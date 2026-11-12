"""Normalized command schema for the Phase 3 codegen pipeline.

The manpage parser (step 2) populates these structures; the Python code emitter
(step 3) consumes them. They replace the ad-hoc ``FlagTuple`` / ``SubpageTuple``
/ ``ManTuple`` ``NamedTuple``s in :mod:`codegen.spiderman` with a typed,
immutable model of one command and its parameters.

The model splits "how many values" (:class:`ParamArity`) from "what kind"
(:class:`ParamValueType`), because the emitter maps them to different field
types. This module is a dev-time tool: standard library only, never imported by
:mod:`pyshb`, never shipped as a runtime dependency.
"""

import enum
from dataclasses import dataclass


class ParamArity(enum.Enum):
    """How many values a parameter takes."""

    NONE = enum.auto()
    ONE = enum.auto()
    MANY = enum.auto()


class ParamValueType(enum.Enum):
    """What kind of value a parameter takes."""

    STR = enum.auto()
    INT = enum.auto()


@dataclass(frozen=True, slots=True)
class ParamSchema:
    """One parameter of a command, as parsed from a manpage.

    Attributes:
        flag: Exact shell spelling; may be multi-token (e.g. ``"-or -name"``),
            never quoted.
        python_name: Field name for the emitted dataclass; keyword collisions
            are resolved by the emitter.
        arity: How many values the flag takes.
        value_type: What kind of value the flag takes.
        arg_join: How the flag joins its value, ``"="`` or ``" "``; ``None``
            inherits the command default.
        doc: Help text captured from the manpage.
        short: Short form (e.g. ``"-f"``), kept for reference; the field name
            comes from ``python_name``.
    """

    flag: str
    python_name: str = ""
    arity: ParamArity = ParamArity.ONE
    value_type: ParamValueType = ParamValueType.STR
    arg_join: str | None = None
    doc: str = ""
    short: str | None = None

    def __post_init__(self) -> None:
        if not self.flag:
            raise ValueError("ParamSchema.flag must be non-empty")
        if self.arg_join is not None and self.arg_join not in ("=", " "):
            raise ValueError("ParamSchema.arg_join must be '=' or ' '")
        if self.arity is ParamArity.NONE and self.value_type is not ParamValueType.STR:
            raise ValueError(
                "ParamSchema with arity=NONE takes no value; "
                "value_type must be STR"
            )
        if self.python_name and not self.python_name.isidentifier():
            raise ValueError(
                f"ParamSchema.python_name must be a valid identifier, "
                f"got {self.python_name!r}"
            )


@dataclass(frozen=True, slots=True)
class SubcommandSchema:
    """A subcommand of a command, mirroring the old ``SubpageTuple``.

    Carries only what a subpage holds today: its name, manpage and summary.
    No params or nested subcommands.

    Attributes:
        name: Last part of the subcommand, e.g. ``"up"`` for
            ``devenv processes up``.
        manpage: The manpage it is described by, e.g.
            ``"devenv-processes-up"``.
        summary: One-line description.
    """

    name: str
    manpage: str
    summary: str = ""


@dataclass(frozen=True, slots=True)
class CommandSchema:
    """One command and everything the parser captured for it.

    Attributes:
        name: The executable (e.g. ``"grep"``).
        manpage: The manpage it was parsed from.
        arg_join: Command-level default joiner, ``"="`` or ``" "``.
        summary: One-line description for the dataclass docstring.
        params: The command's parameters.
        subcommands: The command's subcommands.
    """

    name: str
    manpage: str
    arg_join: str = "="
    summary: str = ""
    params: tuple[ParamSchema, ...] = ()
    subcommands: tuple[SubcommandSchema, ...] = ()

    def __post_init__(self) -> None:
        if self.arg_join not in ("=", " "):
            raise ValueError("CommandSchema.arg_join must be '=' or ' '")
