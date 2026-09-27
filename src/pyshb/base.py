import abc
import enum
from abc import ABC
from collections.abc import Generator, Iterable
from dataclasses import dataclass
from typing import Protocol, Self, override

type Serializable = str | float | bool | Iterable[str]


@dataclass(frozen=True)
class ProgramMeta:
    """
    Description of a shell executable.
    """
    # Name of the executable.
    name: str = ""
    # Default joiner for key-value pairs, overridable in ParamMeta.
    arg_join: str = "="


@dataclass
class ParamMeta:
    """
    Description of a parameter of a shell executable.
    """
    # Flag for the parameter to use. None for positional arguments.
    flag: str | None = None
    # Joiner for key-value pairs. Defaults to the ProgramMeta arg_join.
    arg_join: str | None = None


class Operator(enum.StrEnum):
    """
    Supported operators for composing shell commands.
    """
    AND = "&&"
    PIPE = "|"
    ADD = ""
    OUTPUT = ">"
    APPEND = ">>"
    OR = "||"
    THEN = ";"


class Program(Protocol):
    """
    Protocol for use in shell command composition.
    """
    def __str__(self) -> str: ...


class Compose:
    """
    Compose shell commands.
    Builds shell commands using anything that implements the Program protocol,
    or plain strings.
    """

    _chain: list[str | Program | Operator]

    def __init__(self, prog: str | Program):
        self._chain = [prog]

    def pipe(self, other: str | Program, stderr: bool = False) -> Self:
        """
        Pipe (|) operator.
        :param other: Program to pipe to.
        :param stderr: Also pipe stderr.
        """
        op = Operator.PIPE.value
        if stderr:
            op += "&"
        self._chain.extend((op, other))
        return self

    def __or__(self, other: str | Program):
        return self.pipe(other)

    def and_(self, other: str | Program) -> Self:
        """
        AND (&&) operator.
        :param other: Program to run after if the previous command succeeds.
        """
        self._chain.extend((Operator.AND, other))
        return self

    def __and__(self, other: str | Program):
        return self.and_(other)

    def or_(self, other: str | Program) -> Self:
        """
        OR (||) operator.
        :param other: Program to run after if the previous command fails.
        """
        self._chain.extend((Operator.OR, other))
        return self

    def then(self, other: str | Program) -> Self:
        """
        THEN (;) operator.
        :param other: Program to run after regardless of whether the previous command succeeded or failed.
        """
        self._chain.extend((Operator.THEN, other))
        return self

    def output(self, other: str | Program, stderr: bool = False) -> Self:
        """
        Output (or redirect) (>) operator.
        :param other: Redirect to, another program, device, etc.
        :param stderr: Also redirect stderr.
        """
        op = Operator.OUTPUT.value
        if stderr:
            op += "&"
        self._chain.extend((op, other))
        return self

    def __gt__(self, other: str | Program):
        return self.output(other)

    def append(self, other: str | Program, stderr: bool = False) -> Self:
        """
        Append (>>) operator.
        :param other: Output to, another program, device appending content to it.
        :param stderr: Also append stderr.
        """
        op = Operator.APPEND.value
        if stderr:
            op = "&" + op
        self._chain.extend((op, other))
        return self

    def __str__(self) -> str:
        return " ".join(str(arg) for arg in self._chain)


@dataclass
class ShellCommand(ABC):
    @property
    @abc.abstractmethod
    def meta(self) -> ProgramMeta: ...

    def _params(self) -> Generator[tuple[str, ParamMeta]]:
        """
        All program parameters.
        :returns: Value of a parameter and its metadata to build the final key value pair.
        """
        global_meta = self.meta
        for key, value in self.__dataclass_fields__.items():
            meta = ParamMeta(**value.metadata)
            if meta.arg_join is None:
                meta.arg_join = global_meta.arg_join
            value = getattr(self, key)
            yield value, meta

    @staticmethod
    def _to_param(value: str | float, meta: ParamMeta):
        """
        Builds a key value pair from a parameter value and its metadata.
        """
        value = str(value)
        if any(c in value for c in " '\"$*?[]{}()&|;<>\\"):
            value = f"'{value}'"
        if meta.flag is None:
            return value
        return f"{meta.flag}{meta.arg_join}{value}"

    def _to_key_value(self, val: Serializable, meta: ParamMeta) -> Generator[str]:
        if isinstance(val, bool):
            if val:
                assert meta.flag is not None, "For boolean arguments a flag param is required."
                yield meta.flag
        elif isinstance(val, Iterable):
            for item in val:
                yield self._to_param(item, meta)
        else:
            yield self._to_param(val, meta)

    @override
    def __str__(self) -> str:
        meta = self.meta
        args: list[str] = [meta.name]
        for value, meta in self._params():
            args.extend(self._to_key_value(value, meta))
        return " ".join(args)
