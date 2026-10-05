"""Behaviour tests for the two-tier public export surface.

The package root is a convenience facade, not the API. These tests pin it to
its policy rather than to a hand-maintained list: the exact convenience set,
identity with the owning module, and the absence of everything module-tier.
"""

from types import ModuleType

import pytest

import pyshb
from pyshb import ast, base, builder, compiler, exceptions

#: Exactly the names D012 puts in the convenience tier: the two entry points
#: plus what is unusable without them.
CONVENIENCE_TIER = frozenset(
    {"CommandBuilder", "ParamSpec", "SimpleCommand", "Word", "adhoc"}
)

#: Where each convenience name is declared. A name in the root must also be
#: declared by its module, or the facade has become the only source of truth.
OWNING_MODULE = {
    "CommandBuilder": builder,
    "ParamSpec": builder,
    "adhoc": builder,
    "SimpleCommand": ast,
    "Word": ast,
}


def defined_names(module: ModuleType) -> frozenset[str]:
    """Every public name the module itself defines.

    Filtering on ``__module__`` separates definitions from the stdlib names a
    module imports, which is what makes this usable for ``pyshb.base``: it has
    no ``__all__``, so its own surface cannot be read off one.

    Args:
        module: The module to inspect.

    Returns:
        The public names defined in that module.
    """
    return frozenset(
        name
        for name, obj in vars(module).items()
        if not name.startswith("_") and getattr(obj, "__module__", None) == module.__name__
    )


def test_root_exposes_exactly_the_convenience_set() -> None:
    assert set(pyshb.__all__) == CONVENIENCE_TIER
    assert len(pyshb.__all__) == len(CONVENIENCE_TIER), "__all__ repeats a name"


@pytest.mark.parametrize("name", sorted(CONVENIENCE_TIER))
def test_convenience_name_is_the_object_its_module_defines(name: str) -> None:
    assert getattr(pyshb, name) is getattr(OWNING_MODULE[name], name)


@pytest.mark.parametrize("name", sorted(CONVENIENCE_TIER))
def test_convenience_name_is_declared_by_its_module(name: str) -> None:
    assert name in OWNING_MODULE[name].__all__


@pytest.mark.parametrize("name", sorted(CONVENIENCE_TIER))
def test_convenience_name_needs_no_module_import(name: str) -> None:
    """The facade's whole purpose: this name resolves from the root alone."""
    namespace: dict[str, object] = {}
    exec(f"from pyshb import {name}", namespace)  # noqa: S102
    assert namespace[name] is getattr(pyshb, name)


def test_legacy_base_names_stay_out_of_the_root() -> None:
    """``base.py`` is the pre-AST layer, and it is never public API.

    ``base.Raw`` is a wrapper type while ``Word.raw_word`` is the AST quoting
    escape hatch. Keeping the former out of the root means ``from pyshb import
    Raw`` fails outright instead of silently resolving to the wrong concept.
    """
    assert "Raw" not in pyshb.__all__
    assert not hasattr(pyshb, "Raw")
    assert not defined_names(base) & set(pyshb.__all__)


def test_node_types_and_operators_stay_module_tier() -> None:
    """Only ``SimpleCommand`` and ``Word`` are construction inputs.

    Everything else in the AST is reached *through* the builder, so no user
    needs it to begin a command.
    """
    assert frozenset(ast.__all__) & set(pyshb.__all__) == {"SimpleCommand", "Word"}


def test_exceptions_stay_module_tier() -> None:
    assert not set(exceptions.__all__) & set(pyshb.__all__)


def test_compiler_functions_stay_module_tier() -> None:
    assert not set(compiler.__all__) & set(pyshb.__all__)


#: ``base`` is absent by design: the pre-AST layer has never declared an ``__all__``.
ALL_BEARING_MODULES = [ast, builder, compiler, exceptions]


@pytest.mark.parametrize("module", ALL_BEARING_MODULES)
def test_each_module_keeps_its_own_all(module: ModuleType) -> None:
    assert getattr(module, "__all__", None), f"{module.__name__} lost its __all__"


def test_the_facade_did_not_give_base_an_all() -> None:
    """``base`` stays outside the tier that declares ``__all__``.

    Handing the legacy layer an ``__all__`` would make it look like a peer of
    the modules above, which is the promotion it must not get.
    """
    assert not hasattr(base, "__all__")


def test_a_command_can_be_started_from_the_root_alone() -> None:
    """Both entry points build a command with no second import."""
    from_root = pyshb.adhoc(pyshb.Word.raw_word("$PROG")).args("--opt", "value")

    from_schema = pyshb.CommandBuilder(
        pyshb.SimpleCommand(executable=pyshb.Word.literal("grep")),
        schema={"regexp": pyshb.ParamSpec(flag="--regexp")},
    ).set(regexp="needle")

    assert from_root.root.to_shell_string() == "$PROG --opt value"
    assert from_schema.root.to_shell_string() == "grep --regexp=needle"