import pytest

from pyshb.ast import Pipeline, PipeOp, SimpleCommand, Word
from pyshb.exceptions import (
    CompilationError,
    DanglingPipeError,
    EmptyPipelineError,
    PipelineOperatorMismatchError,
    PyshbError,
    ValidationError,
)
from pyshb.validator import validate


def test_validate_accepts_flat_pipeline():
    cat = SimpleCommand(executable=Word.literal("cat"))
    wc = SimpleCommand(executable=Word.literal("wc"))
    pipeline = Pipeline(commands=(cat, wc), operators=(PipeOp.STDOUT,))
    assert validate(pipeline) is None


def test_validate_accepts_simple_command():
    cmd = SimpleCommand(executable=Word.literal("echo"), args=(Word.literal("hi"),))
    assert validate(cmd) is None


def test_validate_returns_none_on_valid_tree():
    """A nested non-empty pipeline is legal and validated recursively."""
    cat = SimpleCommand(executable=Word.literal("cat"))
    grep = SimpleCommand(executable=Word.literal("grep"))
    wc = SimpleCommand(executable=Word.literal("wc"))
    inner = Pipeline(commands=(cat, grep), operators=(PipeOp.STDOUT,))
    outer = Pipeline(commands=(inner, wc), operators=(PipeOp.STDOUT,))
    assert validate(outer) is None


def test_dangling_pipe_raises():
    cmd = SimpleCommand(executable=Word.literal("echo"))
    with pytest.raises(DanglingPipeError, match="dangling pipe"):
        validate(Pipeline(commands=(cmd,)))
    with pytest.raises(DanglingPipeError, match="dangling pipe"):
        validate(Pipeline(commands=()))


def test_empty_pipeline_segment_raises():
    head = SimpleCommand(executable=Word.literal("echo"))
    tail = SimpleCommand(executable=Word.literal("wc"))
    empty = Pipeline(commands=(), operators=())
    pipeline = Pipeline(
        commands=(head, empty, tail),
        operators=(PipeOp.STDOUT, PipeOp.STDOUT),
    )
    with pytest.raises(EmptyPipelineError, match="empty pipeline segment"):
        validate(pipeline)


def test_operator_command_mismatch_raises():
    cmd = SimpleCommand(executable=Word.literal("echo"))
    pipeline = Pipeline(
        commands=(cmd, cmd, cmd),
        operators=(PipeOp.STDOUT,),
    )
    with pytest.raises(PipelineOperatorMismatchError, match="operator mismatch"):
        validate(pipeline)


def test_validation_error_subclasses_compilation_error():
    assert issubclass(ValidationError, CompilationError)
    assert issubclass(ValidationError, PyshbError)
    assert issubclass(DanglingPipeError, ValidationError)
    assert issubclass(EmptyPipelineError, ValidationError)
    assert issubclass(PipelineOperatorMismatchError, ValidationError)
