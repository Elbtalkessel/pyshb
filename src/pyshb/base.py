import abc
import enum
import shlex
from abc import ABC
from collections.abc import Generator, Iterable
from dataclasses import dataclass
from typing import Protocol, Self, override

type Serializable = str | int | float | bool | None | Iterable[str | int | float]


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


@dataclass(frozen=True)
class Raw:
    """A shell fragment that should be emitted without quoting."""

    value: str

    def __str__(self) -> str:
        return self.value


class Operator(enum.StrEnum):
    """
    Supported operators for composing shell commands.
    """
    AND = "&&"
    PIPE = "|"
    ADD = ""
    OUTPUT = ">"
    APPEND = ">>"
    INPUT = "<"
    HERE_STRING = "<<<"
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

    def __or__(self, other: str | Program) -> Self:
        return self._copy().pipe(other)

    def __ior__(self, other: str | Program) -> Self:
        return self.pipe(other)

    def and_(self, other: str | Program) -> Self:
        """
        AND (&&) operator.
        :param other: Program to run after if the previous command succeeds.
        """
        self._chain.extend((Operator.AND, other))
        return self

    def __and__(self, other: str | Program) -> Self:
        return self._copy().and_(other)

    def __iand__(self, other: str | Program) -> Self:
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
        op = "&>" if stderr else Operator.OUTPUT.value
        self._chain.extend((op, self._redirection_target(other)))
        return self

    def __gt__(self, other: str | Program) -> Self:
        return self._copy().output(other)


    def __lt__(self, other: str | Program) -> Self:
        return self._copy().input(other)

    @staticmethod
    def _redirection_target(target: str | Program) -> str | Program:
        if isinstance(target, str):
            return shlex.quote(target)
        return target

    def input(self, other: str | Program) -> Self:
        """Read standard input from a file or shell program fragment."""
        self._chain.extend((Operator.INPUT, self._redirection_target(other)))
        return self

    def here_string(self, value: str) -> Self:
        """Feed one quoted string to the command's standard input."""
        self._chain.extend((Operator.HERE_STRING, shlex.quote(value)))
        return self

    def append(self, other: str | Program, stderr: bool = False) -> Self:
        """
        Append (>>) operator.
        :param other: Output to, another program, device appending content to it.
        :param stderr: Also append stderr.
        """
        op = "&>>" if stderr else Operator.APPEND.value
        self._chain.extend((op, self._redirection_target(other)))
        return self

    def __rshift__(self, other: str | Program) -> Self:
        return self._copy().append(other)

    def __irshift__(self, other: str | Program) -> Self:
        return self.append(other)


    def __add__(self, fragment: str | Program) -> Self:
        return self._copy().add(fragment)

    def __iadd__(self, fragment: str | Program) -> Self:
        return self.add(fragment)

    def add(self, fragment: str | Program) -> Self:
        """Append an unmodified shell fragment, such as ``2>&1``."""
        self._chain.append(fragment)
        return self

    def _copy(self) -> Self:
        result = self.__class__.__new__(self.__class__)
        result._chain = self._chain.copy()
        return result

    def __str__(self) -> str:
        return " ".join(str(arg) for arg in self._chain)


@dataclass
class ShellCommand(ABC):
    @property
    @abc.abstractmethod
    def meta(self) -> ProgramMeta: ...

    def _params(self) -> Generator[tuple[object, ParamMeta]]:
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
    def _to_param(value: object, meta: ParamMeta) -> str:
        """Build a shell-safe argument, optionally prefixed by its flag."""
        if isinstance(value, Raw):
            rendered = value.value
        else:
            rendered = shlex.quote(str(value))
        if meta.flag is None:
            return rendered
        return f"{meta.flag}{meta.arg_join}{rendered}"

    def _to_key_value(self, val: object, meta: ParamMeta) -> Generator[str]:
        if val is None:
            return
        if isinstance(val, bool):
            if val:
                if meta.flag is None:
                    raise ValueError("Boolean arguments require a flag in ParamMeta.")
                yield meta.flag
        elif isinstance(val, (str, Raw)):
            yield self._to_param(val, meta)
        elif isinstance(val, Iterable):
            for item in val:
                yield self._to_param(item, meta)
        else:
            yield self._to_param(val, meta)

    @override
    def __str__(self) -> str:
        meta = self.meta
        args: list[str] = [meta.name]
        params = list(self._params())
        for is_option in (True, False):
            for value, param_meta in params:
                if (param_meta.flag is not None) == is_option:
                    args.extend(self._to_key_value(value, param_meta))
        return " ".join(args)
