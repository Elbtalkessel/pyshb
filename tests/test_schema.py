"""Behaviour tests for the normalized :mod:`codegen.schema` model.

These pin the invariants the emitter relies on: the model is immutable, splits
arity from value type, and refuses to construct a schema the emitter could not
render into valid Python. Cover the failure mode, not just the happy path.
"""

from dataclasses import FrozenInstanceError

import pytest

from codegen.schema import (
    CommandSchema,
    ParamArity,
    ParamSchema,
    ParamValueType,
    SubcommandSchema,
)


def test_param_schema_immutability() -> None:
    param = ParamSchema(flag="--ignore-case")
    with pytest.raises(FrozenInstanceError):
        param.__setattr__("flag", "--other")


def test_command_schema_equality_and_hash() -> None:
    a = CommandSchema(name="grep", manpage="grep(1)")
    b = CommandSchema(name="grep", manpage="grep(1)")
    assert a == b
    assert hash(a) == hash(b)
    assert len({a, b}) == 1


def test_flag_rejects_empty() -> None:
    with pytest.raises(ValueError, match="flag"):
        ParamSchema(flag="")


def test_arg_join_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="arg_join"):
        ParamSchema(flag="--opt", arg_join=":")


def test_command_arg_join_rejects_unknown_value() -> None:
    with pytest.raises(ValueError, match="arg_join"):
        CommandSchema(name="grep", manpage="grep(1)", arg_join=":")


def test_no_arg_param_has_no_value_type() -> None:
    param = ParamSchema(flag="-v", arity=ParamArity.NONE)
    assert param.value_type is ParamValueType.STR


def test_none_arity_rejects_int_value_type() -> None:
    with pytest.raises(ValueError, match="value_type"):
        ParamSchema(
            flag="-v",
            arity=ParamArity.NONE,
            value_type=ParamValueType.INT,
        )


@pytest.mark.parametrize(
    "name",
    ["1bad", "bad-name", "has space", "with.dots", "with/slash"],
)
def test_python_name_must_be_identifier(name: str) -> None:
    with pytest.raises(ValueError, match="identifier"):
        ParamSchema(flag="--opt", python_name=name)


@pytest.mark.parametrize("name", ["ok", "_ok", "in_", "from_", "class", "exec_"])
def test_python_name_accepts_identifiers(name: str) -> None:
    """Keywords are valid identifiers; the emitter resolves their collisions."""
    assert ParamSchema(flag="--opt", python_name=name).python_name == name


def test_parameter_inherits_command_arg_join_when_none() -> None:
    """A parameter without ``arg_join`` keeps ``None``, the "inherit" marker.

    The emitter falls back to ``CommandSchema.arg_join`` at emit time. The
    schema must not eagerly resolve it, so the parameter's ``None`` survives
    next to a command default of ``" "``.
    """
    command = CommandSchema(
        name="find",
        manpage="find(1)",
        arg_join=" ",
        params=(ParamSchema(flag="-name"),),
    )
    param = command.params[0]
    assert param.arg_join is None
    effective = param.arg_join if param.arg_join is not None else command.arg_join
    assert effective == " "


def test_subcommand_schema_is_a_flat_subpage() -> None:
    sub = SubcommandSchema(
        name="up",
        manpage="devenv-processes-up",
        summary="Start a process",
    )
    assert sub.name == "up"
    assert sub.manpage == "devenv-processes-up"
    assert sub.summary == "Start a process"
