"""Generated coreutils wrappers — do not edit by hand.

Emitted by :mod:`codegen.emit` from the pinned manpage snapshots in
``tests/fixtures/``. Regenerate with ``python -m codegen.emit``; this file
is the committed output of that run and is never hand-edited.

Each class is a frozen dataclass whose fields are the command's flags.
Build a :class:`pyshb.builder.CommandBuilder` with :meth:`build`.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

from pyshb.ast import SimpleCommand, Word
from pyshb.builder import CommandBuilder, ParamSpec


@dataclass(frozen=True, slots=True)
class grep:
    """print lines that match patterns

    Attributes:
        help_: Output a usage message and exit.
        version: Output the version number of grep and exit.
        extended_regexp: Interpret PATTERNS as extended regular expressions.
        fixed_strings: Interpret PATTERNS as fixed strings, not regular expressions.
        ignore_case: Ignore case distinctions in patterns and input data.
        invert_match: Invert the sense of matching, to select non-matching lines.
        regexp: Use PATTERNS as the patterns.
        file: Obtain patterns from FILE, one per line.
        max_count: Stop reading a file after NUM matching lines.
        color: Surround the matched strings with escape sequences. (assumption: assumed optional value takes one string)
        after_context: Print NUM lines of trailing context after matching lines.
        before_context: Print NUM lines of leading context before matching lines.
    """
    help_: bool = False
    version: bool = False
    extended_regexp: bool = False
    fixed_strings: bool = False
    ignore_case: bool = False
    invert_match: bool = False
    regexp: str | None = None
    file: str | None = None
    max_count: int | None = None
    color: str | None = None
    after_context: int | None = None
    before_context: int | None = None

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
        "extended_regexp": ParamSpec(flag="--extended-regexp"),
        "fixed_strings": ParamSpec(flag="--fixed-strings"),
        "ignore_case": ParamSpec(flag="--ignore-case"),
        "invert_match": ParamSpec(flag="--invert-match"),
        "regexp": ParamSpec(flag="--regexp"),
        "file": ParamSpec(flag="--file"),
        "max_count": ParamSpec(flag="--max-count"),
        "color": ParamSpec(flag="--color"),
        "after_context": ParamSpec(flag="--after-context"),
        "before_context": ParamSpec(flag="--before-context"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("grep")),
            schema=self.schema,
        )
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        if self.extended_regexp:
            builder = builder.set(extended_regexp=True)
        if self.fixed_strings:
            builder = builder.set(fixed_strings=True)
        if self.ignore_case:
            builder = builder.set(ignore_case=True)
        if self.invert_match:
            builder = builder.set(invert_match=True)
        if self.regexp is not None:
            builder = builder.set(regexp=self.regexp)
        if self.file is not None:
            builder = builder.set(file=self.file)
        if self.max_count is not None:
            builder = builder.set(max_count=self.max_count)
        if self.color is not None:
            builder = builder.set(color=self.color)
        if self.after_context is not None:
            builder = builder.set(after_context=self.after_context)
        if self.before_context is not None:
            builder = builder.set(before_context=self.before_context)
        return builder


@dataclass(frozen=True, slots=True)
class find:
    """search for files in a directory hierarchy

    Attributes:
        D: Print diagnostic information.
        help_: Print a summary of the command-line usage of find and exit.
        version: Print the find version number and exit.
        daystart: Measure times from the beginning of today rather than from 24 hours ago.
        regextype: Changes the regular expression syntax understood by -regex and -iregex tests.
        maxdepth: Descend at most levels directories below the starting-points.
        mindepth: Do not apply any tests or actions at levels less than levels.
        amin: File was last accessed less than, more than or exactly n minutes ago.
        name: Base of file name matches shell pattern pattern.
        type_: File is of type c.
        empty: File is empty and is either a regular file or a directory.
    """
    D: str | None = None
    help_: bool = False
    version: bool = False
    daystart: bool = False
    regextype: str | None = None
    maxdepth: str | None = None
    mindepth: str | None = None
    amin: int | None = None
    name: str | None = None
    type_: str | None = None
    empty: bool = False

    schema: ClassVar[Mapping[str, ParamSpec]] = {
        "D": ParamSpec(flag="-D", arg_join=" "),
        "help_": ParamSpec(flag="--help"),
        "version": ParamSpec(flag="--version"),
        "daystart": ParamSpec(flag="-daystart"),
        "regextype": ParamSpec(flag="-regextype", arg_join=" "),
        "maxdepth": ParamSpec(flag="-maxdepth", arg_join=" "),
        "mindepth": ParamSpec(flag="-mindepth", arg_join=" "),
        "amin": ParamSpec(flag="-amin", arg_join=" "),
        "name": ParamSpec(flag="-name", arg_join=" "),
        "type_": ParamSpec(flag="-type", arg_join=" "),
        "empty": ParamSpec(flag="-empty"),
    }

    def build(self) -> CommandBuilder:
        builder = CommandBuilder(
            SimpleCommand(executable=Word.literal("find")),
            schema=self.schema,
        )
        if self.D is not None:
            builder = builder.set(D=self.D)
        if self.help_:
            builder = builder.set(help_=True)
        if self.version:
            builder = builder.set(version=True)
        if self.daystart:
            builder = builder.set(daystart=True)
        if self.regextype is not None:
            builder = builder.set(regextype=self.regextype)
        if self.maxdepth is not None:
            builder = builder.set(maxdepth=self.maxdepth)
        if self.mindepth is not None:
            builder = builder.set(mindepth=self.mindepth)
        if self.amin is not None:
            builder = builder.set(amin=self.amin)
        if self.name is not None:
            builder = builder.set(name=self.name)
        if self.type_ is not None:
            builder = builder.set(type_=self.type_)
        if self.empty:
            builder = builder.set(empty=True)
        return builder
