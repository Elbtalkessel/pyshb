import typing
from collections.abc import Callable, Mapping
from dataclasses import KW_ONLY, dataclass, field, replace
from typing import Self

from pyshb.ast import SimpleCommand, Word
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

    The wrapped ``root`` is kept materialised: its ``args`` always equal the
    flag words for ``params`` followed by ``positionals``, so the node stays
    compilable even though flags are tracked separately.

    Attributes:
        root: The command node being built.
        schema: The parameter schema defining known flags. Required, because a
            flag cannot be derived from a parameter name.
        params: The currently set parameter values, in first-set order.
        positionals: The positional arguments added so far. ``None`` means not
            supplied yet, and adopts the root's existing args.
    """

    root: SimpleCommand
    _: KW_ONLY
    schema: Mapping[str, ParamSpec]
    params: Mapping[str, bool | str | int] = field(default_factory=dict)
    positionals: tuple[Word, ...] | None = None

    def __post_init__(self) -> None:
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
            UnknownParameterError: If a name is absent from the schema. Every
                name is validated before anything is applied, so a call with
                one bad name never half-applies.
        """
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

    def _clone(self, **overrides: object) -> Self:
        """Return a new builder with the given fields replaced.

        Every transformation funnels through here, so ``__post_init__`` always
        re-materialises the root's ``args`` as flags-then-positionals and the
        node stays compilable by the compiler step.

        Args:
            **overrides: Builder fields to replace, e.g. ``params``.

        Returns:
            A new builder. ``self`` is never modified.
        """
        root = typing.cast("SimpleCommand", overrides.pop("root", self.root))
        params = typing.cast(
            "Mapping[str, bool | str | int]", overrides.pop("params", self.params)
        )
        positionals = overrides.pop("positionals", self.positionals)
        return replace(
            self, root=root, params=params, positionals=positionals, **overrides
        )


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


__all__ = [
    "CommandBuilder",
    "ParamSpec",
    "adhoc",
]
