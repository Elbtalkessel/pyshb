"""Behaviour tests for the Python code emitter in :mod:`codegen.emit`.

The emitter is pure over a :class:`codegen.schema.CommandSchema`: every function
takes a schema and returns source text, never touching the filesystem. Tests
feed hand-built schemas (and the pinned fixtures via :func:`emit.load_schemas`)
and assert the emitted source, so they run without ``man`` and without any
generation side effects.

Each test pins one rule of the emission contract: frozen-slotted dataclasses,
keyword/builtin field suffixing, arity-to-type mapping, ``arg_join`` rendering,
the build path, and the reproducibility of the committed module.
"""

from typing import Any, cast

import pytest

from codegen import emit
from codegen.schema import (
    CommandSchema,
    ParamArity,
    ParamSchema,
    ParamValueType,
)
from pyshb.builder import CommandBuilder


def _param(
    flag: str,
    *,
    arity: ParamArity = ParamArity.NONE,
    value_type: ParamValueType = ParamValueType.STR,
    arg_join: str | None = None,
    doc: str = "",
) -> ParamSchema:
    """Build one parameter the way the parser leaves it (``python_name`` empty)."""
    return ParamSchema(
        flag=flag,
        arity=arity,
        value_type=value_type,
        arg_join=arg_join,
        doc=doc,
    )


def test_emits_frozen_slots_dataclass() -> None:
    """The generated class is a frozen, slotted dataclass."""
    schema = CommandSchema(name="grep", manpage="grep", summary="match patterns")
    source = emit.emit_class(schema)
    assert "@dataclass(frozen=True, slots=True)" in source
    assert "class grep:" in source


@pytest.mark.parametrize(
    ("flag", "field"),
    [
        ("--in", "in_"),
        ("--from", "from_"),
        ("--type", "type_"),
        ("--id", "id_"),
        ("--format", "format_"),
        ("--exec", "exec_"),
    ],
)
def test_keyword_flag_gets_suffixed_field(flag: str, field: str) -> None:
    """A keyword/builtin flag is suffixed, while ``flag`` keeps its spelling."""
    schema = CommandSchema(
        name="cmd",
        manpage="cmd",
        params=(_param(flag),),
    )
    source = emit.emit_class(schema)
    assert f"{field}: bool = False" in source
    assert f'ParamSpec(flag="{flag}")' in source


def test_bool_flag_emits_false_default() -> None:
    """A no-argument flag is a ``bool`` defaulting to ``False``."""
    schema = CommandSchema(
        name="cmd",
        manpage="cmd",
        params=(_param("--ignore-case"),),
    )
    source = emit.emit_class(schema)
    assert "ignore_case: bool = False" in source


def test_valued_flag_emits_optional_default() -> None:
    """A single-valued string flag is ``str | None = None``."""
    schema = CommandSchema(
        name="cmd",
        manpage="cmd",
        params=(_param("--regexp", arity=ParamArity.ONE),),
    )
    source = emit.emit_class(schema)
    assert "regexp: str | None = None" in source


def test_repeatable_flag_emits_sequence() -> None:
    """A repeatable flag is ``Sequence[str] = ()`` and imports ``Sequence``."""
    schema = CommandSchema(
        name="cmd",
        manpage="cmd",
        params=(_param("--exclude", arity=ParamArity.MANY),),
    )
    class_source = emit.emit_class(schema)
    assert "exclude: Sequence[str] = ()" in class_source

    module_source = emit.emit_module([schema])
    assert "from collections.abc import Mapping, Sequence" in module_source


def test_arg_join_space_emitted() -> None:
    """A space-joined parameter records ``arg_join=\" \"`` in its ``ParamSpec``."""
    schema = CommandSchema(
        name="find",
        manpage="find",
        params=(_param("-type", arity=ParamArity.ONE, arg_join=" "),),
    )
    source = emit.emit_class(schema)
    assert 'ParamSpec(flag="-type", arg_join=" ")' in source


def test_emitted_source_compiles() -> None:
    """The emitted module compiles, and its build path yields a CommandBuilder."""
    schema = CommandSchema(
        name="grep",
        manpage="grep",
        summary="print lines that match patterns",
        params=(
            _param("--ignore-case"),
            _param("--regexp", arity=ParamArity.ONE),
        ),
    )
    source = emit.emit_module([schema])
    namespace: dict[str, object] = {}
    exec(compile(source, "generated.py", "exec"), namespace)  # noqa: S102

    grep = cast(Any, namespace["grep"])
    built = grep(ignore_case=True, regexp="needle").build()
    assert isinstance(built, CommandBuilder)
    assert built.root.to_shell_string() == "grep --ignore-case --regexp=needle"


def test_emitted_source_passes_gates() -> None:
    """The committed module is reproducible, compilable, and importable.

    The full ``ruff check .`` and ``ty check`` gates run at the commit step
    ([[Conventions]]); this test pins the invariants that make them pass — the
    committed file is the byte-for-byte output of the emitter, and that output
    is valid Python that imports and builds.
    """
    emitted = emit.emit_module(emit.load_schemas())
    committed = emit.GENERATED_PATH.read_text()
    assert emitted == committed, "regenerate with `python -m codegen.emit`"

    compile(committed, str(emit.GENERATED_PATH), "exec")

    from pyshb.contrib import generated

    assert isinstance(generated.grep(ignore_case=True).build(), CommandBuilder)
    assert isinstance(generated.find(type_="f").build(), CommandBuilder)
