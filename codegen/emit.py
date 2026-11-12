"""Python code emitter for the Phase 3 codegen pipeline.

Turns a :class:`codegen.schema.CommandSchema` into the source of a frozen,
slotted dataclass with complete type annotations, committed under
``src/pyshb/contrib/generated.py``. This is the "static over dynamic" decision:
the generated coreutils are source files, so IDE autocomplete, docstring hovers,
zero import overhead and static type checking all work.

The emitter is a dev-time tool: standard library only, never imported by
:mod:`pyshb`, never shipped as a runtime dependency. Every function below is
pure over the schema; only :func:`main` touches the filesystem (reading pinned
manpage snapshots and writing the generated module), so regeneration is
deterministic — the committed file is the byte-for-byte output of this module
and is never hand-edited.

Emission rules ([[Architecture]] "Phase 3 codegen pipeline"):

1. **Field naming.** A flag spelling becomes a field name by stripping leading
   dashes and turning ``-`` into ``_``. A name that would shadow a Python
   keyword or builtin is suffixed with ``_`` (``--in`` -> ``in_``,
   ``--type`` -> ``type_``), while :attr:`ParamSchema.flag` keeps the exact
   shell spelling. ``keyword.iskeyword`` catches keywords; the builtin check
   catches names like ``type``, ``id``, ``format`` and ``exec`` that are legal
   identifiers but reserved words in practice.
2. **Arity to type.** No-argument flags are ``bool = False``; single-valued
   flags are ``str | None = None`` or ``int | None = None``; repeatable flags
   are ``Sequence[str] = ()``.
3. **arg_join.** Each parameter resolves its joiner — the parameter's own
   ``arg_join`` or, when ``None``, the command default — and the generated
   :class:`pyshb.builder.ParamSpec` records it so ``--opt=value`` renders
   differently from ``--opt value``.
4. **Integration.** Each dataclass carries a :attr:`schema` class attribute
   (``Mapping[str, ParamSpec]``) and a :meth:`build` method that materialises a
   :class:`pyshb.builder.CommandBuilder`, so
   ``grep(ignore_case=True).build()`` is a usable command. Generated classes
   are module-tier and do not enter the root ``__all__``.
"""

import builtins
import keyword
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path

from codegen.schema import (
    CommandSchema,
    ParamArity,
    ParamSchema,
    ParamValueType,
)
from codegen.spiderman import parse_manpage

#: Repo root, from which the fixture snapshots and the generated module are
#: resolved. ``codegen/`` is one directory below the root.
REPO_ROOT = Path(__file__).resolve().parents[1]

#: The pinned manpage snapshots the generated module is emitted from. Each pair
#: is ``(command, fixture)``; the fixture is a captured ``man <command>`` subset
#: under ``tests/fixtures/``. Adding a coreutil means capturing its manpage and
#: appending one pair here.
COREUTILS: tuple[tuple[str, str], ...] = (
    ("grep", "grep.txt"),
    ("find", "find.txt"),
)

#: Where the committed generated module lives.
GENERATED_PATH = REPO_ROOT / "src" / "pyshb" / "contrib" / "generated.py"

#: Names a field must not shadow. ``dir(builtins)`` is deterministic at runtime,
#: so the set is stable across regeneration.
_BUILTIN_NAMES = frozenset(dir(builtins))


def python_name(flag: str) -> str:
    """Derive a dataclass field name from a flag spelling.

    Args:
        flag: The exact shell spelling (e.g. ``"--ignore-case"``, ``"-type"``).

    Returns:
        The field name, with keyword/builtin collisions suffixed with ``_``.
    """
    name = flag.lstrip("-").replace("-", "_")
    if keyword.iskeyword(name) or name in _BUILTIN_NAMES:
        name += "_"
    return name


def _field_annotation(param: ParamSchema) -> tuple[str, str]:
    """Return the ``(annotation, default)`` pair for one parameter.

    Args:
        param: The resolved parameter.

    Returns:
        The type annotation text and its default value text.
    """
    match param.arity:
        case ParamArity.NONE:
            return "bool", "False"
        case ParamArity.MANY:
            return "Sequence[str]", "()"
        case ParamArity.ONE:
            if param.value_type is ParamValueType.INT:
                return "int | None", "None"
            return "str | None", "None"


def _effective_arg_join(schema: CommandSchema, param: ParamSchema) -> str:
    """Resolve a parameter's joiner, falling back to the command default."""
    return param.arg_join if param.arg_join is not None else schema.arg_join


def _quoted(value: str) -> str:
    """Return ``value`` as a double-quoted Python string literal."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _escape_doc(text: str) -> str:
    """Escape ``text`` for safe embedding in a triple-quoted docstring."""
    return text.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')


def _resolved_params(schema: CommandSchema) -> tuple[ParamSchema, ...]:
    """Return the schema's parameters with ``python_name`` populated.

    ``ParamSchema`` is frozen, so the name is materialised with
    :func:`dataclasses.replace` rather than by mutation. Duplicate field names
    would produce an uncompilable dataclass, so they raise here.

    Args:
        schema: The command schema.

    Returns:
        The parameters in schema order, each carrying its field name.
    """
    resolved: list[ParamSchema] = []
    seen: set[str] = set()
    for param in schema.params:
        name = python_name(param.flag)
        if name in seen:
            raise ValueError(
                f"{schema.name}: flags {param.flag!r} and another collapse to "
                f"the same field name {name!r}"
            )
        seen.add(name)
        resolved.append(replace(param, python_name=name))
    return tuple(resolved)


def _emit_class_docstring(
    summary: str, attrs: Sequence[tuple[str, str]]
) -> list[str]:
    """Emit the Google-style class docstring, indented for the class body.

    Args:
        summary: The one-line command summary.
        attrs: ``(field_name, doc)`` pairs for the ``Attributes:`` block.

    Returns:
        The docstring source lines including the triple-quote delimiters, each
        already indented by four spaces.
    """
    summary_line = _escape_doc(summary) or "A generated command wrapper."
    lines = ['    """' + summary_line, ""]
    lines.append("    Attributes:")
    for name, doc in attrs:
        if doc:
            lines.append(f"        {name}: {_escape_doc(doc)}")
        else:
            lines.append(f"        {name}")
    lines.append('    """')
    return lines


def _emit_build_lines(param: ParamSchema, join: str) -> list[str]:
    """Emit the ``build`` method body for one parameter.

    Booleans and single-valued flags go through ``set()``, which validates
    against the schema; repeatable flags go through ``args()`` because ``set()``
    stores one value per name and cannot accumulate a sequence.

    Args:
        param: The resolved parameter.
        join: The resolved ``arg_join``.

    Returns:
        The indented source lines applying this parameter to the builder.
    """
    name = param.python_name
    match param.arity:
        case ParamArity.NONE:
            return [
                f"        if self.{name}:",
                f"            builder = builder.set({name}=True)",
            ]
        case ParamArity.ONE:
            return [
                f"        if self.{name} is not None:",
                f"            builder = builder.set({name}=self.{name})",
            ]
        case ParamArity.MANY:
            if join == "=":
                return [
                    f"        for value in self.{name}:",
                    f"            builder = builder.args({_quoted(param.flag + '=')} + value)",
                ]
            return [
                f"        for value in self.{name}:",
                f"            builder = builder.args({_quoted(param.flag)}, value)",
            ]


def emit_class(schema: CommandSchema) -> str:
    """Emit the source of one frozen dataclass for ``schema``.

    The result is a self-contained class definition (decorator, class, fields,
    schema, build method) but does not carry its own imports; combine classes
    with :func:`emit_module` to get a compilable module.

    Args:
        schema: The command schema.

    Returns:
        The class source, without a trailing newline.
    """
    resolved = _resolved_params(schema)
    lines: list[str] = ["@dataclass(frozen=True, slots=True)", f"class {schema.name}:"]
    lines.extend(
        _emit_class_docstring(
            schema.summary, [(p.python_name, p.doc) for p in resolved]
        )
    )

    for param in resolved:
        annotation, default = _field_annotation(param)
        lines.append(f"    {param.python_name}: {annotation} = {default}")

    lines.append("")
    lines.append("    schema: ClassVar[Mapping[str, ParamSpec]] = {")
    for param in resolved:
        join = _effective_arg_join(schema, param)
        spec = (
            f"ParamSpec(flag={_quoted(param.flag)}, arg_join=\" \")"
            if join == " "
            else f"ParamSpec(flag={_quoted(param.flag)})"
        )
        lines.append(f"        {_quoted(param.python_name)}: {spec},")
    lines.append("    }")

    lines.append("")
    lines.append("    def build(self) -> CommandBuilder:")
    lines.append("        builder = CommandBuilder(")
    lines.append(
        f"            SimpleCommand(executable=Word.literal({_quoted(schema.name)})),"
    )
    lines.append("            schema=self.schema,")
    lines.append("        )")
    for param in resolved:
        lines.extend(_emit_build_lines(param, _effective_arg_join(schema, param)))
    lines.append("        return builder")

    return "\n".join(lines)


def emit_module(schemas: Sequence[CommandSchema]) -> str:
    """Emit the full generated module for ``schemas``.

    Args:
        schemas: The command schemas, in emission order.

    Returns:
        The module source, ending with a trailing newline.
    """
    needs_sequence = any(
        param.arity is ParamArity.MANY for schema in schemas for param in schema.params
    )
    lines = [
        '"""Generated coreutils wrappers — do not edit by hand.',
        "",
        "Emitted by :mod:`codegen.emit` from the pinned manpage snapshots in",
        "``tests/fixtures/``. Regenerate with ``python -m codegen.emit``; this file",
        "is the committed output of that run and is never hand-edited.",
        "",
        "Each class is a frozen dataclass whose fields are the command's flags.",
        "Build a :class:`pyshb.builder.CommandBuilder` with :meth:`build`.",
        '"""',
        "",
    ]
    abc_imports = ["Mapping"]
    if needs_sequence:
        abc_imports.append("Sequence")
    lines.append(f"from collections.abc import {', '.join(abc_imports)}")
    lines.append("from dataclasses import dataclass")
    lines.append("from typing import ClassVar")
    lines.append("")
    lines.append("from pyshb.ast import SimpleCommand, Word")
    lines.append("from pyshb.builder import CommandBuilder, ParamSpec")
    lines.append("")
    lines.append("")
    for index, schema in enumerate(schemas):
        if index:
            lines.append("")
            lines.append("")
        lines.append(emit_class(schema))
    return "\n".join(lines) + "\n"


def _read_fixture(path: Path) -> list[str]:
    """Read a fixture the way :func:`codegen.spiderman.fetch_manual_lines` returns it."""
    return [line for line in path.read_text().splitlines() if line.strip()]


def load_schemas() -> list[CommandSchema]:
    """Parse the pinned manpage snapshots into command schemas.

    Returns:
        One :class:`CommandSchema` per entry in :data:`COREUTILS`, in order.
    """
    schemas: list[CommandSchema] = []
    for command, fixture in COREUTILS:
        lines = _read_fixture(REPO_ROOT / "tests" / "fixtures" / fixture)
        schemas.append(parse_manpage(command, command, lines))
    return schemas


def main() -> None:
    """Re-run parser -> schema -> emitter and write the generated module.

    Reads the pinned snapshots, parses them, emits the module source, and
    writes it to :data:`GENERATED_PATH`. This is the only entry point that
    touches the filesystem, and the only way the committed file should change.
    """
    schemas = load_schemas()
    source = emit_module(schemas)
    GENERATED_PATH.write_text(source)


if __name__ == "__main__":
    main()
