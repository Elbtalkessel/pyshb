"""Python code emitter for the Phase 3 codegen pipeline.

Turns a :class:`codegen.schema.CommandSchema` into the source of a frozen,
slotted dataclass with complete type annotations, committed under
``src/pyshb/contrib/generated.py``. This is the "static over dynamic" decision:
the generated coreutils are source files, so IDE autocomplete, docstring hovers,
zero import overhead and static type checking all work.

The emitter is a dev-time tool, never imported by :mod:`pyshb`, never shipped as
a runtime dependency. Generation is templated: :func:`emit_module` builds a plain
view model from the schema and renders ``module.py.j2`` (Jinja, a codegen-only
dependency). :func:`main` is the only function that touches the filesystem, so
regeneration is deterministic — the committed file is the byte-for-byte output
of ``python -m codegen.emit`` and is never hand-edited.

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

from jinja2 import Environment, FileSystemLoader

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


#: The Jinja environment for ``module.py.j2``. Rendering emits Python source,
#: not HTML, so autoescaping is off. ``quote`` and ``doc`` are the escaping
#: helpers the template uses to build string literals and docstrings.
_ENV = Environment(
    loader=FileSystemLoader(str(Path(__file__).resolve().parent)),
    autoescape=False,
)
_ENV.filters["quote"] = _quoted
_ENV.filters["doc"] = _escape_doc


def _view(schemas: Sequence[CommandSchema]) -> dict[str, object]:
    """Reduce the schemas to the plain view model ``module.py.j2`` renders.

    Args:
        schemas: The command schemas, in emission order.

    Returns:
        A ``{"needs_sequence": bool, "commands": [...]}`` mapping. Each command
        carries ``name``, ``summary``, ``fields`` (annotation/default/doc),
        ``schema_entries`` (name/flag/arg_join) and ``build_params``
        (name/arity/flag/arg_join).
    """
    needs_sequence = False
    commands: list[dict[str, object]] = []
    for schema in schemas:
        fields: list[dict[str, str]] = []
        schema_entries: list[dict[str, str]] = []
        build_params: list[dict[str, str]] = []
        for param in _resolved_params(schema):
            annotation, default = _field_annotation(param)
            join = _effective_arg_join(schema, param)
            if param.arity is ParamArity.MANY:
                needs_sequence = True
            fields.append(
                {
                    "name": param.python_name,
                    "annotation": annotation,
                    "default": default,
                    "doc": param.doc,
                }
            )
            schema_entries.append(
                {"name": param.python_name, "flag": param.flag, "arg_join": join}
            )
            build_params.append(
                {
                    "name": param.python_name,
                    "arity": param.arity.name,
                    "flag": param.flag,
                    "arg_join": join,
                }
            )
        commands.append(
            {
                "name": schema.name,
                "summary": schema.summary,
                "fields": fields,
                "schema_entries": schema_entries,
                "build_params": build_params,
            }
        )
    return {"needs_sequence": needs_sequence, "commands": commands}


def emit_module(schemas: Sequence[CommandSchema]) -> str:
    """Emit the full generated module for ``schemas``.

    Args:
        schemas: The command schemas, in emission order.

    Returns:
        The module source, ending with a trailing newline.
    """
    template = _ENV.get_template("module.py.j2")
    return template.render(**_view(schemas))


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
