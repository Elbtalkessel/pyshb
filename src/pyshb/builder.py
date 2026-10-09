from collections.abc import Callable, Mapping
from dataclasses import KW_ONLY, dataclass, field, replace
from typing import Self

from pyshb.ast import (
    CommandGroup,
    CommandNode,
    LogicalNode,
    LogicalOp,
    Pipeline,
    PipeOp,
    Redirect,
    RedirectOp,
    SimpleCommand,
    Subshell,
    Word,
)
from pyshb.exceptions import UnknownParameterError


@dataclass(frozen=True, slots=True)
class ParamSpec:
    """Schema entry describing one parameter a command accepts.

    Attributes:
        flag: The exact shell flag spelling, which may be more than one
            token (e.g. ``-maxdepth``, ``-or -name``). Never quoted.
        arg_join: The joiner placed between ``flag`` and a value. ``"="``
            produces a single joined word (``--regexp=foo``); ``" "``
            produces two separate words (``-maxdepth 3``).
    """

    flag: str
    arg_join: str = "="


@dataclass(frozen=True, slots=True)
class CommandBuilder:
    """Immutable builder for a shell command.

    Every transformation returns a new builder; nothing mutates. Evaluation to
    a shell string or an argv list belongs to the compiler step and is
    deliberately absent here.

    For a ``SimpleCommand`` root, the wrapped ``root`` is kept materialised:
    its ``args`` always equal the flag words for ``params`` followed by
    ``positionals``, so the node stays compilable even though flags are
    tracked separately. A compound root (``Pipeline``, ``LogicalNode``,
    ``Subshell``, ``CommandGroup``) has no schema, so ``schema``, ``params``
    and ``positionals`` are unused and left at their defaults.

    Attributes:
        root: The command node being built. Composition and redirection methods
            replace it with a compound node when invoked.
        schema: The parameter schema defining known flags. Required for
            ``SimpleCommand`` roots; ignored otherwise. Keyword-only because a
            flag cannot be derived from a parameter name.
        params: The currently set parameter values, in first-set order.
            Empty for compound roots.
        positionals: The positional arguments added so far. ``None`` means
            not supplied yet and adopts the root's existing args. Empty for
            compound roots.
    """

    root: CommandNode
    _: KW_ONLY
    schema: Mapping[str, ParamSpec] = field(default_factory=dict)
    params: Mapping[str, bool | str | int] = field(default_factory=dict)
    positionals: tuple[Word, ...] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.root, SimpleCommand):
            # A pipeline, logical node, subshell or group has no flags or
            # positionals to materialise; leave schema, params and
            # positionals at their defaults and return.
            return
        positionals = self.root.args if self.positionals is None else self.positionals
        object.__setattr__(self, "positionals", positionals)
        args = (*self._flag_words(), *positionals)
        object.__setattr__(self, "root", replace(self.root, args=args))

    def _flag_words(self) -> tuple[Word, ...]:
        """Render the currently set parameters into shell words.

        ``bool`` is tested before ``int`` because ``bool`` subclasses ``int``;
        the reverse order would render ``True`` as ``--flag=1``. A boolean has
        no value, so ``arg_join`` never applies to it.

        Flags are marked raw uniformly. For a single-token flag this is
        unobservable — ``shlex.quote("--posix")`` is ``--posix`` — but
        ``shlex.quote("-or -name")`` is ``"'-or -name'"``, which folds two
        tokens into one argument. Marking every flag raw means the multi-token
        case cannot be special-cased and forgotten.
        """
        words: list[Word] = []
        for name, value in self.params.items():
            spec = self.schema[name]
            if isinstance(value, bool):
                if value:
                    words.append(Word.raw_word(spec.flag))
            elif isinstance(value, int | str):
                rendered = str(value)
                if spec.arg_join == "=":
                    words.append(Word.literal(f"{spec.flag}={rendered}"))
                else:
                    words.append(Word.raw_word(spec.flag))
                    words.append(Word.literal(rendered))
        return tuple(words)

    def set(self, **params: bool | str | int) -> Self:
        """Set, override or unset named parameters.

        Args:
            **params: Parameter names from the schema. ``True`` emits the bare
                flag, ``False`` removes a previously set flag, and ``str`` or
                ``int`` emits the value joined per the spec's ``arg_join``.

        Returns:
            A new builder. ``self`` is never modified.

        Raises:
            TypeError: If the root is not a ``SimpleCommand``. A compound root
                has no schema to validate against, so ``set()`` would silently
                store params that never materialise into any node.
            UnknownParameterError: If a name is absent from the schema. Every
                name is validated before anything is applied, so a call with
                one bad name never half-applies.
        """
        if not isinstance(self.root, SimpleCommand):
            raise TypeError(
                "set() requires a SimpleCommand root; use composition "
                "methods to build or extend a compound node"
            )
        for name in params:
            if name not in self.schema:
                raise UnknownParameterError(name, tuple(sorted(self.schema)))
        new_params = {**self.params, **params}
        return self._clone(params=new_params)

    def args(self, *values: str | Word, raw: bool = False) -> Self:
        """Append positional arguments in call order.

        Args:
            *values: Words to append. Strings become ``Word.literal`` unless
                ``raw`` is true, in which case they become ``Word.raw_word``.
                An existing ``Word`` passes through untouched.
            raw: Emit the string values without quoting, for globs and
                variable references.

        Returns:
            A new builder. ``self`` is never modified.
        """
        if not isinstance(self.root, SimpleCommand):
            raise TypeError(
                "args() requires a SimpleCommand root; use composition "
                "methods to build or extend a compound node"
            )
        words: list[Word] = []
        for value in values:
            if isinstance(value, Word):
                words.append(value)
            elif raw:
                words.append(Word.raw_word(value))
            else:
                words.append(Word.literal(value))
        return self._clone(positionals=(*(self.positionals or ()), *words))

    def when(self, condition: bool, fn: Callable[[Self], Self]) -> Self:
        """Apply a transform only when a condition holds.

        Lets callers stay in a fluent chain instead of breaking into ``if``.

        Args:
            condition: Truthiness test deciding whether to apply ``fn``.
            fn: Transform receiving this builder and returning a new one.

        Returns:
            ``fn(self)`` when ``condition`` is truthy, otherwise ``self``.
            Returning ``self`` is deliberate: nothing changed, so cloning
            would only allocate.
        """
        if condition:
            return fn(self)
        return self

    # ------------------------------------------------------------------
    # Composition
    # ------------------------------------------------------------------

    def pipe(self, other: CommandNode | Self) -> Self:
        """Pipe ``self`` into ``other``, extending any existing pipeline.

        If ``self`` is already a ``Pipeline``, ``other`` is appended as the
        final stage and a single ``|`` joins it to the previous tail, so
        ``a.pipe(b).pipe(c)`` is one flat ``Pipeline`` with three commands and
        two operators rather than nested pipelines.

        Args:
            other: Command node or builder to receive ``self``'s stdout.

        Returns:
            A new builder whose root is the resulting ``Pipeline``.
        """
        other_node = _unwrap(other)
        new_root = self._extend_pipeline(other_node, PipeOp.STDOUT)
        return self._clone(root=new_root)

    def pipe_all(self, other: CommandNode | Self) -> Self:
        """Pipe ``self`` into ``other`` with ``|&`` so stderr travels too.

        Same shape rule as ``pipe``, just the operator changes.

        Args:
            other: Command node or builder to receive ``self``'s stdout and
                stderr.

        Returns:
            A new builder whose root is the resulting ``Pipeline``.
        """
        other_node = _unwrap(other)
        new_root = self._extend_pipeline(other_node, PipeOp.ALL)
        return self._clone(root=new_root)

    def and_(self, other: CommandNode | Self) -> Self:
        """Run ``other`` after ``self`` if ``self`` succeeds (``&&``).

        Args:
            other: Command node or builder to run on success.

        Returns:
            A new builder whose root is ``self && other``.
        """
        return self._clone(
            root=LogicalNode(left=self.root, op=LogicalOp.AND, right=_unwrap(other))
        )

    def or_(self, other: CommandNode | Self) -> Self:
        """Run ``other`` after ``self`` if ``self`` fails (``||``).

        Args:
            other: Command node or builder to run on failure.

        Returns:
            A new builder whose root is ``self || other``.
        """
        return self._clone(
            root=LogicalNode(left=self.root, op=LogicalOp.OR, right=_unwrap(other))
        )

    def then(self, other: CommandNode | Self) -> Self:
        """Run ``other`` after ``self`` regardless of exit status (``;``).

        Args:
            other: Command node or builder to run unconditionally.

        Returns:
            A new builder whose root is ``self ; other``.
        """
        return self._clone(
            root=LogicalNode(
                left=self.root, op=LogicalOp.SEQUENCE, right=_unwrap(other)
            )
        )

    def subshell(self) -> Self:
        """Wrap ``self`` in a subshell ``( ... )``.

        A subshell isolates variable assignments and side effects, so
        ``sh.subshell(a.and_(b)).pipe(c)`` renders ``(a && b) | c``: the
        ``&&`` is evaluated inside the parens, the pipe outside them.

        Returns:
            A new builder whose root is a ``Subshell`` over ``self.root``.
        """
        return self._clone(root=Subshell(body=self.root, redirects=()))

    def group(self) -> Self:
        """Wrap ``self`` in a command group ``{ ...; }``.

        Unlike ``subshell``, a group runs in the current shell, so
        assignments leak out and exits affect the caller.

        Returns:
            A new builder whose root is a ``CommandGroup`` over ``self.root``.
        """
        return self._clone(root=CommandGroup(body=self.root, redirects=()))

    # ------------------------------------------------------------------
    # Redirection
    # ------------------------------------------------------------------

    def redirect_out(self, target: str | Word) -> Self:
        """Redirect stdout to ``target`` (``>``). Appends, never replaces.

        Args:
            target: File path or shell fragment to write to.

        Returns:
            A new builder with one more ``WRITE`` redirect on the rightmost
            ``SimpleCommand``.
        """
        return self._add_redirect(
            Redirect(op=RedirectOp.WRITE, target=_to_word(target))
        )

    def append_out(self, target: str | Word) -> Self:
        """Append stdout to ``target`` (``>>``).

        Args:
            target: File path or shell fragment to append to.

        Returns:
            A new builder with one more ``APPEND`` redirect on the rightmost
            ``SimpleCommand``.
        """
        return self._add_redirect(
            Redirect(op=RedirectOp.APPEND, target=_to_word(target))
        )

    def redirect_err(self, target: str | Word) -> Self:
        """Redirect stderr to ``target`` (``2>``).

        Args:
            target: File path or shell fragment to write stderr to.

        Returns:
            A new builder with one more ``WRITE`` redirect with
            ``source_fd=2``.
        """
        return self._add_redirect(
            Redirect(
                op=RedirectOp.WRITE,
                target=_to_word(target),
                source_fd=2,
            )
        )

    def redirect_all(self, target: str | Word) -> Self:
        """Redirect both stdout and stderr to ``target`` (``&>``).

        Args:
            target: File path or shell fragment to write to.

        Returns:
            A new builder with one more ``BOTH_WRITE`` redirect.
        """
        return self._add_redirect(
            Redirect(op=RedirectOp.BOTH_WRITE, target=_to_word(target))
        )

    def redirect_in(self, target: str | Word) -> Self:
        """Redirect stdin from ``target`` (``<``).

        Args:
            target: File path or shell fragment to read from.

        Returns:
            A new builder with one more ``READ`` redirect.
        """
        return self._add_redirect(
            Redirect(op=RedirectOp.READ, target=_to_word(target))
        )

    def here_string(self, text: str) -> Self:
        """Feed ``text`` to stdin as a quoted here-string (``<<<``).

        Args:
            text: The string to feed, wrapped in a literal word.

        Returns:
            A new builder with one more ``HERE_STRING`` redirect.
        """
        return self._add_redirect(
            Redirect(op=RedirectOp.HERE_STRING, target=_to_word(text))
        )

    def heredoc(self, body: str, delimiter: str = "EOF") -> Self:
        """Feed ``body`` to stdin as a heredoc (``<<``).

        Args:
            body: The lines of input, placed verbatim between the
                delimiter pair.
            delimiter: The closing marker. Defaults to ``EOF``.

        Returns:
            A new builder with one more ``HEREDOC`` redirect carrying the
            body.
        """
        return self._add_redirect(
            Redirect(
                op=RedirectOp.HEREDOC,
                target=Word.literal(delimiter),
                body=body,
            )
        )

    def redirect(
        self,
        source_fd: int,
        to_fd: int | None = None,
        target: str | Word | None = None,
    ) -> Self:
        """Escape hatch for fd-level redirections like ``2>&1`` or ``2>file``.

        Exactly one of ``to_fd`` or ``target`` must be supplied. ``to_fd``
        produces a ``DUP_OUT`` redirect (``>&``); ``target`` produces a
        ``WRITE`` redirect bound to ``source_fd``.

        Args:
            source_fd: File descriptor to redirect from (e.g. ``2`` for
                stderr).
            to_fd: Destination fd to duplicate to (e.g. ``1`` for stdout).
            target: File path to redirect to.

        Returns:
            A new builder with the resulting redirect on the rightmost
            ``SimpleCommand``.

        Raises:
            ValueError: If neither or both of ``to_fd`` and ``target`` are
                supplied.
        """
        if (to_fd is None) == (target is None):
            raise ValueError(
                "redirect() requires exactly one of to_fd or target"
            )
        if to_fd is not None:
            redirect = Redirect(
                op=RedirectOp.DUP_OUT, target=to_fd, source_fd=source_fd
            )
        else:
            assert target is not None  # narrowed by the == check above
            redirect = Redirect(
                op=RedirectOp.WRITE,
                target=_to_word(target),
                source_fd=source_fd,
            )
        return self._add_redirect(redirect)

    # ------------------------------------------------------------------
    # Operator sugar
    # ------------------------------------------------------------------

    def __or__(self, other: CommandNode | Self) -> Self:
        """``a | b`` is sugar for ``a.pipe(b)``."""
        return self.pipe(other)

    def __and__(self, other: CommandNode | Self) -> Self:
        """``a & b`` is sugar for ``a.and_(b)``.

        Note Python's ``&`` binds tighter than ``|``, which is the inverse
        of the shell's ``&&`` versus ``|``. Chains mixing the two must use
        the named methods to make the precedence explicit.
        """
        return self.and_(other)

    def __xor__(self, other: CommandNode | Self) -> Self:
        """``a ^ b`` is sugar for ``a.or_(b)``.

        The shell has no ``^`` operator, so this is purely an ``or_`` alias
        exposed for ergonomics.
        """
        return self.or_(other)

    def __gt__(self, target: str | Word) -> Self:
        """``a > path`` is sugar for ``a.redirect_out(path)``."""
        return self.redirect_out(target)

    def __lshift__(self, target: str | Word) -> Self:
        """``a << path`` is sugar for ``a.append_out(path)``."""
        return self.append_out(target)

    def __lt__(self, target: str | Word) -> Self:
        """``a < path`` is sugar for ``a.redirect_in(path)``."""
        return self.redirect_in(target)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _extend_pipeline(
        self, other_node: CommandNode, operator: PipeOp
    ) -> CommandNode:
        """Append ``other_node`` to ``self.root``'s pipeline, or start one.
        The operator count always matches ``len(commands) - 1`` after.
        """
        match self.root:
            case Pipeline(commands=cmds, operators=ops):
                return Pipeline(
                    commands=(*cmds, other_node),
                    operators=(*ops, operator),
                )
        return Pipeline(commands=(self.root, other_node), operators=(operator,))

    def _add_redirect(self, redirect: Redirect) -> Self:
        """Append ``redirect`` to the rightmost redirect target in ``self.root``.

        A ``SimpleCommand``, ``Subshell`` or ``CommandGroup`` root takes the
        redirect directly on its own ``redirects`` tuple. A ``Pipeline`` or
        ``LogicalNode`` root rebuilds the tree so the redirect lands on its
        rightmost child — which may itself be a ``Subshell`` or
        ``CommandGroup`` that accepts the redirect on its own ``redirects``
        tuple rather than descending into its body.
        """
        if isinstance(self.root, SimpleCommand | Subshell | CommandGroup):
            return self._clone(
                root=replace(self.root, redirects=(*self.root.redirects, redirect))
            )
        leaf = _rightmost(self.root)
        new_leaf = replace(leaf, redirects=(*leaf.redirects, redirect))
        return self._clone(root=_replace_rightmost(self.root, new_leaf))

    def _clone(self, **overrides: object) -> Self:
        """Return a new builder with the given fields replaced.

        Every transformation funnels through here, so ``__post_init__`` always
        re-materialises a ``SimpleCommand`` root's ``args`` as flags-then-
        positionals and the node stays compilable by the compiler step.

        Args:
            **overrides: Builder fields to replace, e.g. ``params`` or ``root``.

        Returns:
            A new builder. ``self`` is never modified.
        """
        return replace(self, **overrides)


def adhoc(executable: str | Word) -> CommandBuilder:
    """A builder for a program with no known flags. Use ``.args()``.

    Args:
        executable: The program name or path. A string is wrapped as a
            literal word; a ``Word`` passes through untouched.

    Returns:
        A new builder with an empty schema.
    """
    if isinstance(executable, str):
        executable = Word.literal(executable)
    return CommandBuilder(SimpleCommand(executable=executable), schema={})


# ----------------------------------------------------------------------
# Module-private tree helpers
# ----------------------------------------------------------------------


def _to_word(value: str | Word) -> Word:
    """Coerce a target into a ``Word``. Strings become ``Word.literal``."""
    if isinstance(value, Word):
        return value
    return Word.literal(value)


def _unwrap(node: CommandNode | CommandBuilder) -> CommandNode:
    """Return ``node``'s root if it is a builder, otherwise ``node`` itself."""
    if isinstance(node, CommandBuilder):
        return node.root
    return node


def _rightmost(node: CommandNode) -> SimpleCommand | Subshell | CommandGroup:
    """The rightmost redirect target in a command tree.

    A pipeline or logical node delegates to its last component. A subshell
    or group is itself a redirect target — a redirect after ``)`` or ``}``
    binds to the whole compound, not to its inner rightmost command.
    """
    match node:
        case SimpleCommand():
            return node
        case Subshell():
            return node
        case CommandGroup():
            return node
        case Pipeline(commands=cmds):
            return _rightmost(cmds[-1])
        case LogicalNode(right=right):
            return _rightmost(right)


def _replace_rightmost(
    node: CommandNode, leaf: SimpleCommand | Subshell | CommandGroup
) -> CommandNode:
    """Return a copy of ``node`` whose rightmost redirect target is ``leaf``.

    Used by ``_add_redirect`` to thread a new redirect through a compound
    tree without disturbing its left side or operators. A subshell or group
    is replaced wholesale — its own ``redirects`` tuple is the target.
    """
    match node:
        case SimpleCommand():
            return leaf
        case Subshell():
            return leaf
        case CommandGroup():
            return leaf
        case Pipeline(commands=cmds, operators=ops):
            return Pipeline(
                commands=(*cmds[:-1], _replace_rightmost(cmds[-1], leaf)),
                operators=ops,
            )
        case LogicalNode(left=left, op=op, right=right):
            return LogicalNode(left=left, op=op, right=_replace_rightmost(right, leaf))