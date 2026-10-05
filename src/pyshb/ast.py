import enum
import shlex
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Self

from pyshb.exceptions import UnsupportedCompilationError


@dataclass(frozen=True, slots=True)
class ASTNode(ABC):
    """Base class for all pyshb AST nodes."""

    @property
    @abstractmethod
    def children(self) -> tuple[ASTNode, ...]:
        """Direct child nodes for tree traversal."""
        ...

    @abstractmethod
    def to_shell_string(self, dialect: str = "bash") -> str:
        """Render this node as a shell command string.

        Args:
            dialect: Shell dialect. Phase 1 emits one POSIX-compatible
                rendering regardless, so this is accepted but not yet honoured.

        Returns:
            The rendered shell fragment.
        """
        ...

    def walk(self) -> Iterator[ASTNode]:
        """Depth-first pre-order traversal of the node and all descendants."""
        yield self
        for child in self.children:
            yield from child.walk()


@dataclass(frozen=True, slots=True)
class Word(ASTNode):
    """An atomic argument or command word.

    Attributes:
        value: The string literal or raw shell expression.
        raw: If True, emitted without quotes (e.g. $VAR, *.txt).
             If False, compiler safely quotes it.
    """

    value: str
    raw: bool = False

    @classmethod
    def literal(cls, value: str) -> Self:
        return cls(value=value, raw=False)

    @classmethod
    def raw_word(cls, value: str) -> Self:
        return cls(value=value, raw=True)

    @property
    def children(self) -> tuple[ASTNode, ...]:
        return ()

    def to_shell_string(self, dialect: str = "bash") -> str:
        """Render this word, quoting it unless it is marked raw.

        Args:
            dialect: Unused; reserved for dialect-specific quoting.

        Returns:
            The word bare when raw, and shell-quoted otherwise.
        """
        if self.raw:
            return self.value
        return shlex.quote(self.value)


class RedirectOp(enum.StrEnum):
    READ = "<"
    WRITE = ">"
    APPEND = ">>"
    BOTH_WRITE = "&>"
    BOTH_APPEND = "&>>"
    HERE_STRING = "<<<"
    HEREDOC = "<<"
    HEREDOC_STRIP = "<<-"
    DUP_IN = "<&"
    DUP_OUT = ">&"


@dataclass(frozen=True, slots=True)
class Redirect(ASTNode):
    """File descriptor redirection.

    Attributes:
        op: Redirection operator (RedirectOp).
        target: Target destination (Word for file/string, int for fd duplicate).
        source_fd: Source file descriptor (e.g. 2 for 2>, None for default).
    """

    op: RedirectOp
    target: Word | int
    source_fd: int | None = None

    @property
    def children(self) -> tuple[ASTNode, ...]:
        if isinstance(self.target, Word):
            return (self.target,)
        return ()

    def to_shell_string(self, dialect: str = "bash") -> str:
        """Render this redirection.

        Args:
            dialect: Passed through to a word target.

        Returns:
            The optional source fd, the operator, and the target.
        """
        source = f"{self.source_fd}" if self.source_fd is not None else ""
        if isinstance(self.target, int):
            target = str(self.target)
        else:
            target = self.target.to_shell_string(dialect)
        return f"{source}{self.op}{target}"


class PipeOp(enum.StrEnum):
    STDOUT = "|"
    ALL = "|&"


class LogicalOp(enum.StrEnum):
    AND = "&&"
    OR = "||"
    SEQUENCE = ";"


type CommandNode = SimpleCommand | Pipeline | LogicalNode | Subshell | CommandGroup


@dataclass(frozen=True, slots=True)
class SimpleCommand(ASTNode):
    """A single executable invocation with arguments and redirections.

    Attributes:
        executable: Executable word or path (e.g. Word.literal("grep")).
        args: Arguments and flags in call order.
        redirects: Redirections bound directly to this command.
        env: Environment variable prefixes (name, value).
    """

    executable: Word
    args: tuple[Word, ...] = ()
    redirects: tuple[Redirect, ...] = ()
    env: tuple[tuple[str, Word], ...] = ()

    def __post_init__(self) -> None:
        """Reject env names that would break out of the assignment.

        Raises:
            UnsupportedCompilationError: If any env name is not a valid
                identifier. Bash cannot quote an assignment name, so a name
                like ``PATH; echo pwned;`` cannot be made safe by quoting and
                would render as shell structure rather than as a name.
        """
        for name, _ in self.env:
            if not (name.isidentifier() and name.isascii()):
                raise UnsupportedCompilationError(
                    f"env name {name!r} is not a valid shell identifier"
                )

    @property
    def children(self) -> tuple[ASTNode, ...]:
        env_words = tuple(val for _, val in self.env)
        return (self.executable, *env_words, *self.args, *self.redirects)

    def to_shell_string(self, dialect: str = "bash") -> str:
        """Render this command as env prefixes, executable, args, and redirects.

        Args:
            dialect: Passed through to every child node.

        Returns:
            The space-joined fragments of this command.
        """
        parts = [
            f"{name}={value.to_shell_string(dialect)}" for name, value in self.env
        ]
        parts.append(self.executable.to_shell_string(dialect))
        parts.extend(arg.to_shell_string(dialect) for arg in self.args)
        parts.extend(redir.to_shell_string(dialect) for redir in self.redirects)
        return " ".join(parts)


@dataclass(frozen=True, slots=True)
class Pipeline(ASTNode):
    """A linear pipeline of commands connected by pipes.

    Attributes:
        commands: Commands in the pipeline (at least 2 commands).
        operators: Connectors between stages (length = len(commands) - 1).
    """

    commands: tuple[CommandNode, ...]
    operators: tuple[PipeOp, ...] = ()

    @property
    def children(self) -> tuple[ASTNode, ...]:
        return self.commands

    def to_shell_string(self, dialect: str = "bash") -> str:
        """Render this pipeline, validating the operator count first.

        Args:
            dialect: Passed through to every command.

        Returns:
            The commands joined by their operators.

        Raises:
            UnsupportedCompilationError: If the number of operators does not
                match the number of commands minus one, which would otherwise
                compile to a silently different command.
        """
        if len(self.operators) != len(self.commands) - 1:
            raise UnsupportedCompilationError(
                f"Pipeline has {len(self.commands)} commands but "
                f"{len(self.operators)} operators; expected "
                f"{len(self.commands) - 1}"
            )
        parts = []
        for index, command in enumerate(self.commands):
            parts.append(command.to_shell_string(dialect))
            if index < len(self.operators):
                parts.append(str(self.operators[index]))
        return " ".join(parts)


@dataclass(frozen=True, slots=True)
class LogicalNode(ASTNode):
    """Boolean control flow or sequential execution between commands.

    Attributes:
        left: Left-hand command operand.
        op: Logical operator (&&, ||, ;).
        right: Right-hand command operand.
    """

    left: CommandNode
    op: LogicalOp
    right: CommandNode

    @property
    def children(self) -> tuple[ASTNode, ...]:
        return (self.left, self.right)

    def to_shell_string(self, dialect: str = "bash") -> str:
        """Render both operands joined by the logical operator.

        Args:
            dialect: Passed through to both operands.

        Returns:
            The rendered ``left op right`` fragment.
        """
        left = self.left.to_shell_string(dialect)
        right = self.right.to_shell_string(dialect)
        return f"{left} {self.op} {right}"


@dataclass(frozen=True, slots=True)
class Subshell(ASTNode):
    """Commands executed in an isolated subshell: `( ... )`.

    Attributes:
        body: The internal command tree.
        redirects: Redirections applied to the whole subshell.
    """

    body: CommandNode
    redirects: tuple[Redirect, ...] = ()

    @property
    def children(self) -> tuple[ASTNode, ...]:
        return (self.body, *self.redirects)

    def to_shell_string(self, dialect: str = "bash") -> str:
        """Render this subshell, keeping redirects outside the parens.

        Args:
            dialect: Passed through to the body and the redirects.

        Returns:
            The parenthesised body followed by its redirections.
        """
        # Redirects must follow the closing paren; inside, they would bind to
        # the body's last command instead of the whole subshell.
        parts = ["(", self.body.to_shell_string(dialect), ")"]
        parts.extend(redir.to_shell_string(dialect) for redir in self.redirects)
        return " ".join(parts)


@dataclass(frozen=True, slots=True)
class CommandGroup(ASTNode):
    """Group of commands executed in current shell context: `{ ...; }`.

    Attributes:
        body: The internal command tree.
        redirects: Redirections applied to the group.
    """

    body: CommandNode
    redirects: tuple[Redirect, ...] = ()

    @property
    def children(self) -> tuple[ASTNode, ...]:
        return (self.body, *self.redirects)

    def to_shell_string(self, dialect: str = "bash") -> str:
        """Render this group as `{ body; }` followed by its redirects.

        Args:
            dialect: Passed through to the body and the redirects.

        Returns:
            The braced body followed by its redirections.
        """
        # `;` must precede `}` and redirects must follow it, or the result is
        # a syntax error.
        body = self.body.to_shell_string(dialect)
        parts = ["{", f"{body};", "}"]
        parts.extend(redir.to_shell_string(dialect) for redir in self.redirects)
        return " ".join(parts)


__all__ = [
    "ASTNode",
    "CommandGroup",
    "CommandNode",
    "LogicalNode",
    "LogicalOp",
    "PipeOp",
    "Pipeline",
    "Redirect",
    "RedirectOp",
    "SimpleCommand",
    "Subshell",
    "Word",
]