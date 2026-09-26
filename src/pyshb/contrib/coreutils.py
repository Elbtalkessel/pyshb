from collections.abc import Iterable
from dataclasses import dataclass, field

from pyshb.base import CommandMeta, ShellCommand


@dataclass
class cd(ShellCommand):
    path: str

    @property
    def meta(self) -> CommandMeta:
        return CommandMeta(program="cd")


@dataclass
class grep(ShellCommand):
    file: str = field(default="")
    color: bool = field(default=False, metadata={"param": "--color"})
    ignore_case: bool = field(default=False, metadata={"param": "--ignore-case"})
    invert_match: bool = field(default=False, metadata={"param": "--invert-match"})
    regexp: Iterable[str] = field(
        default_factory=list, metadata={"param": "--regexp", "join": "="}
    )

    @property
    def meta(self) -> CommandMeta:
        return CommandMeta(program="grep")


@dataclass
class find(ShellCommand):
    path: str
    maxdepth: int | None = field(default=None, metadata={"param": "-maxdepth"})
    type: str | None = field(default=None, metadata={"param": "-type"})
    name: list[str] | None = field(default=None, metadata={"param": "-name"})
    or_name: list[str] | None = field(default=None, metadata={"param": "-or -name"})

    @property
    def meta(self) -> CommandMeta:
        return CommandMeta(program="find")
