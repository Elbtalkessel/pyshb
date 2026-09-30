import enum
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class ASTNode(ABC):
    """Base class for all pyshb AST nodes."""

    @property
    @abstractmethod
    def children(self) -> tuple[ASTNode, ...]:
        """Direct child nodes for tree traversal."""
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

    @property
    def children(self) -> tuple[ASTNode, ...]:
        env_words = tuple(val for _, val in self.env)
        return (self.executable, *env_words, *self.args, *self.redirects)


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
