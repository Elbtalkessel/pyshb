import pytest

from pyshb.ast import Pipeline, PipeOp, Redirect, RedirectOp, SimpleCommand, Word
from pyshb.exceptions import (
    CompilationError,
    ConflictingRedirectError,
    DanglingPipeError,
    DeadStdoutPipeError,
    EmptyPipelineError,
    NonPosixFeatureError,
    PipelineOperatorMismatchError,
    PyshbError,
    UnknownDialectError,
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
    assert issubclass(ConflictingRedirectError, ValidationError)
    assert issubclass(DeadStdoutPipeError, ValidationError)
    assert issubclass(NonPosixFeatureError, ValidationError)
    assert issubclass(UnknownDialectError, ValidationError)


def test_conflicting_stdout_raises():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(op=RedirectOp.WRITE, target=Word.literal("a")),
            Redirect(op=RedirectOp.WRITE, target=Word.literal("b")),
        ),
    )
    with pytest.raises(ConflictingRedirectError, match="conflicting redirect"):
        validate(cmd)


def test_conflicting_stdout_both_write_raises():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(op=RedirectOp.WRITE, target=Word.literal("a")),
            Redirect(op=RedirectOp.BOTH_WRITE, target=Word.literal("b")),
        ),
    )
    with pytest.raises(ConflictingRedirectError, match="conflicting redirect"):
        validate(cmd)


def test_stderr_and_stdout_redirect_not_conflicting():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(op=RedirectOp.WRITE, target=Word.literal("err"), source_fd=2),
            Redirect(op=RedirectOp.WRITE, target=Word.literal("out")),
        ),
    )
    assert validate(cmd) is None


def test_pipe_after_stdout_redirect_raises():
    first = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(Redirect(op=RedirectOp.WRITE, target=Word.literal("file")),),
    )
    other = SimpleCommand(executable=Word.literal("other"))
    pipeline = Pipeline(commands=(first, other), operators=(PipeOp.STDOUT,))
    with pytest.raises(DeadStdoutPipeError, match="dead stdout pipe"):
        validate(pipeline)


def test_pipe_after_stderr_redirect_ok():
    first = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(op=RedirectOp.WRITE, target=Word.literal("err"), source_fd=2),
        ),
    )
    other = SimpleCommand(executable=Word.literal("other"))
    pipeline = Pipeline(commands=(first, other), operators=(PipeOp.STDOUT,))
    assert validate(pipeline) is None


def test_pipe_after_dup_merge_ok():
    first = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(Redirect(op=RedirectOp.DUP_OUT, target=1, source_fd=2),),
    )
    other = SimpleCommand(executable=Word.literal("other"))
    pipeline = Pipeline(commands=(first, other), operators=(PipeOp.STDOUT,))
    assert validate(pipeline) is None


def test_last_stage_may_redirect_stdout():
    a = SimpleCommand(executable=Word.literal("a"))
    b = SimpleCommand(
        executable=Word.literal("b"),
        redirects=(Redirect(op=RedirectOp.WRITE, target=Word.literal("out")),),
    )
    pipeline = Pipeline(commands=(a, b), operators=(PipeOp.STDOUT,))
    assert validate(pipeline) is None


def test_pipe_all_ok_under_bash():
    a = SimpleCommand(executable=Word.literal("a"))
    b = SimpleCommand(executable=Word.literal("b"))
    pipeline = Pipeline(commands=(a, b), operators=(PipeOp.ALL,))
    assert validate(pipeline, dialect="bash") is None


def test_pipe_all_raises_under_posix():
    a = SimpleCommand(executable=Word.literal("a"))
    b = SimpleCommand(executable=Word.literal("b"))
    pipeline = Pipeline(commands=(a, b), operators=(PipeOp.ALL,))
    with pytest.raises(NonPosixFeatureError, match="non-POSIX feature"):
        validate(pipeline, dialect="posix")


def test_here_string_raises_under_posix():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(Redirect(op=RedirectOp.HERE_STRING, target=Word.literal("x")),),
    )
    with pytest.raises(NonPosixFeatureError, match="non-POSIX feature"):
        validate(cmd, dialect="posix")


def test_both_write_raises_under_posix():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(Redirect(op=RedirectOp.BOTH_WRITE, target=Word.literal("out")),),
    )
    with pytest.raises(NonPosixFeatureError, match="non-POSIX feature"):
        validate(cmd, dialect="posix")


def test_both_append_raises_under_posix():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(op=RedirectOp.BOTH_APPEND, target=Word.literal("out")),
        ),
    )
    with pytest.raises(NonPosixFeatureError, match="non-POSIX feature"):
        validate(cmd, dialect="posix")


def test_heredoc_ok_under_posix():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(
                op=RedirectOp.HEREDOC,
                target=Word.literal("EOF"),
                body="line",
            ),
        ),
    )
    assert validate(cmd, dialect="posix") is None


def test_heredoc_strip_ok_under_posix():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(
                op=RedirectOp.HEREDOC_STRIP,
                target=Word.literal("EOF"),
                body="line",
            ),
        ),
    )
    assert validate(cmd, dialect="posix") is None


def test_unknown_dialect_raises():
    cmd = SimpleCommand(executable=Word.literal("echo"))
    with pytest.raises(UnknownDialectError, match="unknown dialect"):
        validate(cmd, dialect="zsh")


def test_default_dialect_is_bash():
    a = SimpleCommand(executable=Word.literal("a"))
    b = SimpleCommand(executable=Word.literal("b"))
    pipeline = Pipeline(commands=(a, b), operators=(PipeOp.ALL,))
    assert validate(pipeline) is None
