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

#: Where each convenience name is defined. The root re-exports these; it does
#: not define them, so each must still resolve to its own module.
OWNING_MODULE = {
    "CommandBuilder": builder,
    "ParamSpec": builder,
    "adhoc": builder,
    "SimpleCommand": ast,
    "Word": ast,
}

#: A representative name from each module tier, to prove that dropping
#: ``__all__`` did not change what those modules expose.
MODULE_TIER_SAMPLE = [
    (ast, "Pipeline"),
    (base, "Raw"),
    (builder, "ParamSpec"),
    (compiler, "to_argv"),
    (exceptions, "PyshbError"),
]


def defined_names(module: ModuleType) -> frozenset[str]:
    """Every public name the module itself defines.

    Filtering on ``__module__`` separates definitions from the names a module
    imports. Since D016 no module below the root declares ``__all__``, so this
    is the only way to read a module's own surface, and the facade-discipline
    tests below all rest on it.

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
def test_convenience_name_is_defined_by_its_own_module(name: str) -> None:
    assert name in defined_names(OWNING_MODULE[name])


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
    assert defined_names(ast) & set(pyshb.__all__) == {"SimpleCommand", "Word"}


def test_exceptions_stay_module_tier() -> None:
    assert not defined_names(exceptions) & set(pyshb.__all__)


def test_compiler_functions_stay_module_tier() -> None:
    assert not defined_names(compiler) & set(pyshb.__all__)


#: ``base`` is in this list on purpose: the legacy layer never declared one either.
ALL_BEARING_MODULES = [ast, base, builder, compiler, exceptions]


@pytest.mark.parametrize("module", ALL_BEARING_MODULES)
def test_only_the_root_declares_an_all(module: ModuleType) -> None:
    """D016: ``__all__`` belongs to the package root alone.

    A per-module list exists only to constrain ``from mod import *``, which pyshb
    neither uses nor expects of its users. Keeping one would be a second place to
    edit per symbol for no reader.
    """
    assert not hasattr(module, "__all__"), f"{module.__name__} declares an __all__"


@pytest.mark.parametrize(("module", "name"), MODULE_TIER_SAMPLE)
def test_module_tier_names_are_still_importable(module: ModuleType, name: str) -> None:
    """Dropping ``__all__`` must not change what a module exposes.

    ``__all__`` never gated a direct import, so this should hold by definition —
    the test exists to catch that assumption breaking. Asserting against the
    module object rather than ``getattr(pyshb, ...)`` keeps it independent of
    whether anything happened to import that module first.
    """
    assert hasattr(module, name)


def test_a_command_can_be_started_from_the_root_alone() -> None:
    """Both entry points build a command with no second import."""
    from_root = pyshb.adhoc(pyshb.Word.raw_word("$PROG")).args("--opt", "value")

    from_schema = pyshb.CommandBuilder(
        pyshb.SimpleCommand(executable=pyshb.Word.literal("grep")),
        schema={"regexp": pyshb.ParamSpec(flag="--regexp")},
    ).set(regexp="needle")

    assert from_root.root.to_shell_string() == "$PROG --opt value"
    assert from_schema.root.to_shell_string() == "grep --regexp=needle"