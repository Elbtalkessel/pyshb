"""Behaviour tests for the structured manpage parser in :mod:`codegen.spiderman`.

The parser is pure over a ``Sequence[str]`` of lines: every parsing function
takes manpage lines directly and never shells out to ``man``. Tests feed it
captured fixtures (``tests/fixtures/*.txt``) and hand-built line lists, so they
run without ``man`` installed.

Each test pins one rule of the schema contract: boolean flags map to
``arity=NONE``, valued flags to ``arity=ONE`` with ``INT``/``STR`` decided by
the placeholder, repeatable/multi-value flags to ``arity=MANY``, ``--opt=value``
versus ``--opt value`` to ``arg_join``, the NAME line to ``summary``, and
subcommand references to ``subcommands``.
"""

from pathlib import Path

import pytest

from codegen import spiderman
from codegen.schema import ParamArity, ParamValueType

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[str]:
    """Read a fixture the way :func:`spiderman.fetch_manual_lines` returns it."""
    return [
        line for line in (FIXTURES / name).read_text().splitlines() if line.strip()
    ]


def _single_flag(lines: list[str]) -> spiderman.ParamSchema:
    """Parse ``lines`` and return the single flag they describe."""
    params = list(spiderman.parse_flags(lines))
    assert len(params) == 1, f"expected one flag, got {params!r}"
    return params[0]


def test_parse_bool_flag() -> None:
    """A no-argument flag is ``arity=NONE`` and keeps its long spelling."""
    param = _single_flag(
        ["     -i, --ignore-case", "            Ignore case distinctions."]
    )
    assert param.flag == "--ignore-case"
    assert param.short == "-i"
    assert param.arity is ParamArity.NONE
    assert param.value_type is ParamValueType.STR


def test_parse_valued_flag_str() -> None:
    """A ``--flag=VALUE`` string flag is ``ONE``/``STR`` with ``arg_join="="``."""
    param = _single_flag(
        ["     -e PATTERNS, --regexp=PATTERNS", "            Use PATTERNS as the patterns."]
    )
    assert param.flag == "--regexp"
    assert param.short == "-e"
    assert param.arity is ParamArity.ONE
    assert param.value_type is ParamValueType.STR
    assert param.arg_join == "="


def test_parse_valued_flag_int() -> None:
    """A numeric placeholder (``NUM``) is ``ONE``/``INT``."""
    param = _single_flag(
        ["     -m NUM, --max-count=NUM", "            Stop reading a file after NUM lines."]
    )
    assert param.flag == "--max-count"
    assert param.arity is ParamArity.ONE
    assert param.value_type is ParamValueType.INT


def test_parse_repeatable_flag() -> None:
    """A ``...`` hint is ``arity=MANY``."""
    param = _single_flag(
        ["     --exclude=GLOB...", "            Skip files whose base name matches GLOB."]
    )
    assert param.flag == "--exclude"
    assert param.arity is ParamArity.MANY


def test_parse_arg_join_space() -> None:
    """A find-style ``-type f`` joins its value with a space."""
    param = _single_flag(["     -type f", "            File is of type f."])
    assert param.flag == "-type"
    assert param.arg_join == " "
    assert param.arity is ParamArity.ONE
    assert param.value_type is ParamValueType.STR


def test_parse_summary_from_name_section() -> None:
    """The NAME one-liner becomes ``CommandSchema.summary``."""
    lines = [
        "NAME",
        "     grep - print lines that match patterns",
        "SYNOPSIS",
        "     grep [OPTION]... PATTERNS [FILE]...",
    ]
    assert spiderman.parse_summary(lines) == "print lines that match patterns"


def test_parse_functions_accept_lines_without_subprocess(monkeypatch: pytest.MonkeyPatch) -> None:
    """Pure parsers never shell out, even when given nothing but lines."""
    def no_subprocess(*args: object, **kwargs: object) -> None:
        raise AssertionError("parser must not run `man`")

    monkeypatch.setattr(spiderman.subprocess, "run", no_subprocess)

    lines = [
        "NAME",
        "     grep - print lines that match patterns",
        "OPTIONS",
        "     -i, --ignore-case",
        "            Ignore case distinctions.",
    ]
    params = list(spiderman.parse_flags(lines))
    assert len(params) == 1
    assert spiderman.parse_summary(lines) == "print lines that match patterns"
    schema = spiderman.parse_manpage("grep", "grep", lines)
    assert schema.params[0].flag == "--ignore-case"


def test_parse_subcommands() -> None:
    """A manpage listing subcommand pages populates ``subcommands``."""
    lines = [
        "SUBCOMMANDS",
        "     devenv-init(1)",
        "            Scaffold devenv.yaml, devenv.nix, and .gitignore.",
        "     devenv-processes-up(1)",
        "            Start the processes defined in devenv.nix.",
    ]
    subs = list(spiderman.parse_subcommands("devenv", lines))
    assert [(s.name, s.manpage) for s in subs] == [
        ("init", "devenv-init"),
        ("up", "devenv-processes-up"),
    ]
    assert subs[0].summary == "Scaffold devenv.yaml, devenv.nix, and .gitignore."


def test_parse_manpage_from_grep_fixture() -> None:
    """End-to-end over the captured ``man grep`` subset."""
    schema = spiderman.parse_manpage("grep", "grep", _load("grep.txt"))
    assert schema.name == "grep"
    assert schema.summary == "print lines that match patterns"
    by_flag = {param.flag: param for param in schema.params}
    assert by_flag["--ignore-case"].arity is ParamArity.NONE
    assert by_flag["--regexp"].value_type is ParamValueType.STR
    assert by_flag["--max-count"].value_type is ParamValueType.INT
    assert by_flag["--color"].doc.endswith("assumed optional value takes one string)")


def test_parse_manpage_from_find_fixture() -> None:
    """End-to-end over the captured ``man find`` subset."""
    schema = spiderman.parse_manpage("find", "find", _load("find.txt"))
    assert schema.summary == "search for files in a directory hierarchy"
    by_flag = {param.flag: param for param in schema.params}
    assert by_flag["-type"].arg_join == " "
    assert by_flag["-type"].arity is ParamArity.ONE
    assert by_flag["-amin"].value_type is ParamValueType.INT
    assert by_flag["-empty"].arity is ParamArity.NONE


def test_parse_manpage_from_devenv_fixture() -> None:
    """End-to-end over the captured ``man devenv`` subset: space-join, multi-value, subcommands."""
    schema = spiderman.parse_manpage("devenv", "devenv", _load("devenv.txt"))
    assert schema.summary.startswith("Fast, Declarative")
    by_flag = {param.flag: param for param in schema.params}
    assert by_flag["--user-config"].arg_join == " "
    assert by_flag["--override-input"].arity is ParamArity.MANY
    assert [sub.manpage for sub in schema.subcommands] == [
        "devenv-init",
        "devenv-shell",
        "devenv-up",
        "devenv-processes",
        "devenv-processes-up",
        "devenv-processes-down",
        "devenv-version",
    ]
