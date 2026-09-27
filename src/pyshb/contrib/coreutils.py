from collections.abc import Iterable
from dataclasses import dataclass, field

from pyshb.base import ProgramMeta, ShellCommand


@dataclass
class cd(ShellCommand):
    path: str

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(name="cd")


@dataclass
class grep(ShellCommand):
    file: str = field(default="")
    color: bool = field(default=False, metadata={"flag": "--color"})
    ignore_case: bool = field(default=False, metadata={"flag": "--ignore-case"})
    invert_match: bool = field(default=False, metadata={"flag": "--invert-match"})
    regexp: Iterable[str] = field(default_factory=list, metadata={"flag": "--regexp"})

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(name="grep", arg_join="=")


@dataclass
class find(ShellCommand):
    path: str
    maxdepth: int | None = field(default=None, metadata={"flag": "-maxdepth"})
    type: str | None = field(default=None, metadata={"flag": "-type"})
    name: list[str] | None = field(default=None, metadata={"flag": "-name"})
    or_name: list[str] | None = field(default=None, metadata={"flag": "-or -name"})

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(name="find", arg_join=" ")
