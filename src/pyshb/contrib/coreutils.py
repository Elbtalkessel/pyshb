"""Deprecated. The pre-AST coreutils, kept as a flag-rendering reference.

Superseded by the AST builder plus a schema dict. Phase 3 generates these from
manpages ([[Decisions]] D017); until then these three classes are the only
worked example of per-program flag rendering, which is why they stay.

Note the two shapes side by side: ``grep`` uses ``arg_join="="`` and ``find``
uses ``arg_join=" "``, so ``--regexp=foo`` versus ``-type f``. The AST layer
reproduces that with ``ParamSpec("-name", arg_join=" ")`` instead.

Built on :mod:`pyshb.base`, which is itself deprecated.
"""

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
    file: str | None = field(default=None)
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
