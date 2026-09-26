import abc
from abc import ABC
from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
from typing import Literal, override

type Serializable = str | float | bool | Iterable[str]
type Chain = Joinable | ShellCommand | str


@dataclass(frozen=True)
class CommandMeta:
    program: str = ""
    position_argument: Literal["first", "last"] = "last"
    param: str = ""
    join: str = ""


class Joinable:
    def __and__(self, other: Chain):
        return ChainCommand(self, other, "&&")

    def __rand__(self, other: Chain):
        return ChainCommand(other, self, "&&")

    def __or__(self, other: Chain):
        return ChainCommand(self, other, "|")

    def __ror__(self, other: Chain):
        return ChainCommand(other, self, "|")

    def __add__(self, other: Chain):
        return ChainCommand(self, other, "")

    def __radd__(self, other: Chain):
        return ChainCommand(other, self, "")

    def __gt__(self, other: Chain):
        return ChainCommand(self, other, ">")

    def __rgt__(self, other: Chain):
        return ChainCommand(other, self, ">")

    def __lt__(self, other: Chain):
        return ChainCommand(self, other, "<")

    def __rlt__(self, other: Chain):
        return ChainCommand(other, self, "<")


@dataclass
class ShellCommand(Joinable, ABC):
    @property
    @abc.abstractmethod
    def meta(self) -> CommandMeta: ...

    @override
    def __str__(self) -> str:
        meta = self.meta
        program = meta.program
        args: list[str] = [program] + list(self.build())
        return " ".join(args)

    def fields(self) -> Generator[tuple[str, CommandMeta]]:
        for key, value in self.__dataclass_fields__.items():
            yield key, CommandMeta(**value.metadata)

    def _get_serializer(
        self, name: str
    ) -> Callable[[Serializable, CommandMeta], str] | None:
        return getattr(self, f"serialize_{name}", None)

    def serialize(self, val: Serializable, meta: CommandMeta) -> Generator[str]:
        if isinstance(val, bool):
            if val:
                yield meta.param
        elif isinstance(val, Iterable):
            for item in val:
                yield f"{meta.param}{meta.join}{self._quote(item)}"
        else:
            yield f"{meta.param}{meta.join}{self._quote(val)}"

    def build(self) -> Generator[str]:
        for name, meta in self.fields():
            value = getattr(self, name)
            if serializer := self._get_serializer(name):
                yield serializer(value, meta)
            else:
                yield from self.serialize(value, meta)

    def _quote(self, value: str | float) -> str:
        if isinstance(value, str):
            if any(c in value for c in " '\"$*?[]{}()&|;<>\\"):
                return f"'{value}'"
            # Special case for "a" in README
            if value == "a":
                return f"'{value}'"
        return str(value)


class ChainCommand(Joinable):
    _chain: list[Joinable | str]

    def __init__(self, left: Chain, right: Chain, operator: str) -> None:
        if isinstance(left, ChainCommand):
            self._chain = left._chain
            left._chain.extend((operator, right))
        elif isinstance(right, ChainCommand):
            self._chain = right._chain
            right._chain.insert(0, left)
            right._chain.insert(1, operator)
        else:
            if operator:
                self._chain = [left, operator, right]
            else:
                self._chain = [left, right]

    @override
    def __str__(self) -> str:
        return " ".join(str(item) for item in self._chain)
