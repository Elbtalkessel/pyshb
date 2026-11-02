import pytest

from pyshb.ast import (
    CommandGroup,
    LogicalNode,
    LogicalOp,
    Pipeline,
    PipeOp,
    Redirect,
    RedirectOp,
    SimpleCommand,
    Subshell,
    Word,
)
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

# ----------------------------------------------------------------------
# Hierarchy
# ----------------------------------------------------------------------


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


# ----------------------------------------------------------------------
# Error message contract
# ----------------------------------------------------------------------


def test_error_messages_name_rule_and_construct():
    """Every message names the rule, the construct, and enough context."""
    cmd = SimpleCommand(executable=Word.literal("cmd"))
    other = SimpleCommand(executable=Word.literal("other"))

    with pytest.raises(DanglingPipeError) as exc:
        validate(Pipeline(commands=(cmd,)))
    assert "dangling pipe" in str(exc.value)
    assert "got 1" in str(exc.value)

    empty = Pipeline(commands=(), operators=())
    pipeline = Pipeline(
        commands=(cmd, empty, other),
        operators=(PipeOp.STDOUT, PipeOp.STDOUT),
    )
    with pytest.raises(EmptyPipelineError) as exc:
        validate(pipeline)
    assert "empty pipeline segment" in str(exc.value)
    assert "stage 2 is empty" in str(exc.value)

    with pytest.raises(PipelineOperatorMismatchError) as exc:
        validate(Pipeline(commands=(cmd, cmd, cmd), operators=(PipeOp.STDOUT,)))
    assert "pipeline operator mismatch" in str(exc.value)
    assert "3 commands" in str(exc.value)

    conflict = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(op=RedirectOp.WRITE, target=Word.literal("a")),
            Redirect(op=RedirectOp.WRITE, target=Word.literal("b")),
        ),
    )
    with pytest.raises(ConflictingRedirectError) as exc:
        validate(conflict)
    assert "conflicting stdout redirect" in str(exc.value)
    assert "command 'cmd'" in str(exc.value)

    dead = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(Redirect(op=RedirectOp.WRITE, target=Word.literal("file")),),
    )
    with pytest.raises(DeadStdoutPipeError) as exc:
        validate(Pipeline(commands=(dead, other), operators=(PipeOp.STDOUT,)))
    assert "dead stdout pipe" in str(exc.value)
    assert "stage 1" in str(exc.value)

    pipe_all = Pipeline(commands=(cmd, other), operators=(PipeOp.ALL,))
    with pytest.raises(NonPosixFeatureError) as exc:
        validate(pipe_all, dialect="posix")
    assert "non-POSIX feature" in str(exc.value)
    assert "|&" in str(exc.value)

    with pytest.raises(UnknownDialectError) as exc:
        validate(cmd, dialect="zsh")
    assert "unknown dialect" in str(exc.value)
    assert "'zsh'" in str(exc.value)


# ----------------------------------------------------------------------
# Pipeline constraints
# ----------------------------------------------------------------------


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


def test_empty_pipeline_nested_in_subshell_raises():
    empty = Pipeline(commands=(), operators=())
    with pytest.raises(DanglingPipeError, match="dangling pipe"):
        validate(Subshell(body=empty))


def test_empty_pipeline_nested_in_group_raises():
    empty = Pipeline(commands=(), operators=())
    with pytest.raises(DanglingPipeError, match="dangling pipe"):
        validate(CommandGroup(body=empty))


# ----------------------------------------------------------------------
# Stream integrity
# ----------------------------------------------------------------------


def test_conflicting_stdout_raises():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(op=RedirectOp.WRITE, target=Word.literal("a")),
            Redirect(op=RedirectOp.WRITE, target=Word.literal("b")),
        ),
    )
    with pytest.raises(ConflictingRedirectError, match="conflicting stdout redirect"):
        validate(cmd)


def test_conflicting_stdout_both_write_raises():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(op=RedirectOp.WRITE, target=Word.literal("a")),
            Redirect(op=RedirectOp.BOTH_WRITE, target=Word.literal("b")),
        ),
    )
    with pytest.raises(ConflictingRedirectError, match="conflicting stdout redirect"):
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


def test_conflicting_redirect_inside_subshell():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(
            Redirect(op=RedirectOp.WRITE, target=Word.literal("a")),
            Redirect(op=RedirectOp.WRITE, target=Word.literal("b")),
        ),
    )
    with pytest.raises(ConflictingRedirectError, match="conflicting stdout redirect"):
        validate(Subshell(body=cmd))


def test_dead_stdout_pipe_inside_subshell():
    first = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(Redirect(op=RedirectOp.WRITE, target=Word.literal("file")),),
    )
    other = SimpleCommand(executable=Word.literal("other"))
    inner = Pipeline(commands=(first, other), operators=(PipeOp.STDOUT,))
    tail = SimpleCommand(executable=Word.literal("tail"))
    tree = Pipeline(commands=(Subshell(body=inner), tail), operators=(PipeOp.STDOUT,))
    with pytest.raises(DeadStdoutPipeError, match="dead stdout pipe"):
        validate(tree)


# ----------------------------------------------------------------------
# Dialect
# ----------------------------------------------------------------------


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


def test_here_string_ok_under_bash():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(Redirect(op=RedirectOp.HERE_STRING, target=Word.literal("x")),),
    )
    assert validate(cmd, dialect="bash") is None


def test_here_string_raises_under_posix():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(Redirect(op=RedirectOp.HERE_STRING, target=Word.literal("x")),),
    )
    with pytest.raises(NonPosixFeatureError, match="non-POSIX feature"):
        validate(cmd, dialect="posix")


def test_both_write_ok_under_bash():
    cmd = SimpleCommand(
        executable=Word.literal("cmd"),
        redirects=(Redirect(op=RedirectOp.BOTH_WRITE, target=Word.literal("out")),),
    )
    assert validate(cmd, dialect="bash") is None


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


def test_non_posix_feature_inside_subshell():
    a = SimpleCommand(executable=Word.literal("a"))
    b = SimpleCommand(executable=Word.literal("b"))
    inner = Pipeline(commands=(a, b), operators=(PipeOp.ALL,))
    with pytest.raises(NonPosixFeatureError, match="non-POSIX feature"):
        validate(Subshell(body=inner), dialect="posix")


# ----------------------------------------------------------------------
# Happy path corpus
# ----------------------------------------------------------------------


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


def test_happy_path_nested_subshell_pipeline_renders():
    a = SimpleCommand(executable=Word.literal("a"))
    b = SimpleCommand(executable=Word.literal("b"))
    c = SimpleCommand(executable=Word.literal("c"))
    sub = Subshell(body=Pipeline(commands=(a, b), operators=(PipeOp.STDOUT,)))
    tree = Pipeline(commands=(sub, c), operators=(PipeOp.STDOUT,))
    assert validate(tree) is None
    assert tree.to_shell_string() == "(a | b) | c"


def test_happy_path_command_group_renders():
    a = SimpleCommand(executable=Word.literal("a"))
    b = SimpleCommand(executable=Word.literal("b"))
    tree = CommandGroup(body=LogicalNode(left=a, op=LogicalOp.AND, right=b))
    assert validate(tree) is None
    assert tree.to_shell_string() == "{ a && b; }"


def test_happy_path_redirects_render():
    cmd = SimpleCommand(
        executable=Word.literal("grep"),
        args=(Word.literal("TODO"),),
        redirects=(
            Redirect(op=RedirectOp.WRITE, target=Word.literal("err"), source_fd=2),
            Redirect(op=RedirectOp.WRITE, target=Word.literal("out")),
        ),
    )
    assert validate(cmd) is None
    assert validate(cmd, dialect="posix") is None
    assert cmd.to_shell_string() == "grep TODO 2>err >out"


def test_happy_path_heredoc_posix_renders():
    cmd = SimpleCommand(
        executable=Word.literal("cat"),
        redirects=(
            Redirect(
                op=RedirectOp.HEREDOC,
                target=Word.literal("EOF"),
                body="line",
            ),
        ),
    )
    assert validate(cmd, dialect="posix") is None
    assert cmd.to_shell_string() == "cat <<EOF\nline\nEOF"


# ----------------------------------------------------------------------
# Immutability & idempotence
# ----------------------------------------------------------------------


def test_validate_is_idempotent():
    a = SimpleCommand(executable=Word.literal("a"))
    b = SimpleCommand(executable=Word.literal("b"))
    tree = Pipeline(commands=(a, b), operators=(PipeOp.STDOUT,))
    assert validate(tree) is None
    assert validate(tree) is None


def test_validate_does_not_mutate_tree():
    a = SimpleCommand(executable=Word.literal("a"))
    b = SimpleCommand(executable=Word.literal("b"))
    tree = Pipeline(commands=(a, b), operators=(PipeOp.STDOUT,))
    before = tree.to_shell_string()
    validate(tree)
    assert tree.to_shell_string() == before


def test_validate_raises_same_error_twice():
    cmd = SimpleCommand(executable=Word.literal("echo"))
    bad = Pipeline(commands=(cmd,))
    with pytest.raises(DanglingPipeError) as first:
        validate(bad)
    with pytest.raises(DanglingPipeError) as second:
        validate(bad)
    assert str(first.value) == str(second.value)
