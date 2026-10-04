import shlex

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
from pyshb.compiler import to_argv, to_shell_string
from pyshb.exceptions import UnsupportedCompilationError


def test_quoting_round_trip():
    """Values with shell metacharacters survive shlex.split intact."""
    values = [
        "hello world",
        "it's a test",
        "$HOME",
        "*.txt",
        "line1\nline2",
    ]
    for val in values:
        word = Word.literal(val)
        shell_str = to_shell_string(word)
        assert shlex.split(shell_str) == [val]


def test_raw_pass_through():
    """A raw word is emitted verbatim; a literal one is quoted."""
    raw = Word.raw_word("$HOME")
    assert to_shell_string(raw) == "$HOME"

    literal = Word.literal("$HOME")
    assert to_shell_string(literal) == "'$HOME'"


def test_empty_literal_renders_as_empty_quotes():
    """Empty literal renders as ''."""
    empty = Word.literal("")
    assert to_shell_string(empty) == "''"


def test_redirect_rendering():
    """Every RedirectOp renders, including source_fd prefixes and int targets."""
    # Basic redirect
    r1 = Redirect(op=RedirectOp.WRITE, target=Word.literal("out.log"))
    assert to_shell_string(r1) == ">out.log"

    # With source_fd
    r2 = Redirect(op=RedirectOp.DUP_OUT, target=Word.literal("1"), source_fd=2)
    assert to_shell_string(r2) == "2>&1"

    # With int target
    r3 = Redirect(op=RedirectOp.DUP_OUT, target=1, source_fd=2)
    assert to_shell_string(r3) == "2>&1"

    # Here string
    r4 = Redirect(op=RedirectOp.HERE_STRING, target=Word.literal("hi"))
    assert to_shell_string(r4) == "<<<hi"


def test_node_rendering_shapes():
    """Every node type renders its expected shape."""
    cmd1 = SimpleCommand(executable=Word.literal("echo"), args=(Word.literal("hi"),))
    cmd2 = SimpleCommand(executable=Word.literal("grep"), args=(Word.literal("hi"),))

    # Pipeline
    pipe = Pipeline(commands=(cmd1, cmd2), operators=(PipeOp.STDOUT,))
    assert to_shell_string(pipe) == "echo hi | grep hi"

    pipe_all = Pipeline(commands=(cmd1, cmd2), operators=(PipeOp.ALL,))
    assert to_shell_string(pipe_all) == "echo hi |& grep hi"

    # Logical
    log_and = LogicalNode(left=cmd1, op=LogicalOp.AND, right=cmd2)
    assert to_shell_string(log_and) == "echo hi && grep hi"

    log_or = LogicalNode(left=cmd1, op=LogicalOp.OR, right=cmd2)
    assert to_shell_string(log_or) == "echo hi || grep hi"

    log_seq = LogicalNode(left=cmd1, op=LogicalOp.SEQUENCE, right=cmd2)
    assert to_shell_string(log_seq) == "echo hi ; grep hi"

    # Subshell
    sub = Subshell(body=cmd1)
    assert to_shell_string(sub) == "( echo hi )"

    out = Redirect(op=RedirectOp.WRITE, target=Word.literal("out"))
    sub_redir = Subshell(body=cmd1, redirects=(out,))
    assert to_shell_string(sub_redir) == "( echo hi >out )"

    # CommandGroup
    grp = CommandGroup(body=cmd1)
    assert to_shell_string(grp) == "{ echo hi; }"

    grp_redir = CommandGroup(body=cmd1, redirects=(out,))
    assert to_shell_string(grp_redir) == "{ echo hi; >out }"


def test_to_argv_happy_path():
    """to_argv happy path on a SimpleCommand."""
    cmd = SimpleCommand(
        executable=Word.literal("echo"),
        args=(Word.literal("hello"), Word.literal("world")),
    )
    assert to_argv(cmd) == ["echo", "hello", "world"]


def test_to_argv_raises_on_compound_nodes():
    """to_argv raises UnsupportedCompilationError on each compound node type."""
    cmd1 = SimpleCommand(executable=Word.literal("echo"))
    cmd2 = SimpleCommand(executable=Word.literal("grep"))

    pipe = Pipeline(commands=(cmd1, cmd2), operators=(PipeOp.STDOUT,))
    with pytest.raises(UnsupportedCompilationError):
        to_argv(pipe)

    log = LogicalNode(left=cmd1, op=LogicalOp.AND, right=cmd2)
    with pytest.raises(UnsupportedCompilationError):
        to_argv(log)

    sub = Subshell(body=cmd1)
    with pytest.raises(UnsupportedCompilationError):
        to_argv(sub)

    grp = CommandGroup(body=cmd1)
    with pytest.raises(UnsupportedCompilationError):
        to_argv(grp)


def test_to_argv_raises_on_raw_words():
    """A raw word is rejected, not passed through."""
    cmd = SimpleCommand(executable=Word.literal("echo"), args=(Word.raw_word("$HOME"),))
    with pytest.raises(UnsupportedCompilationError, match="raw word"):
        to_argv(cmd)

    cmd2 = SimpleCommand(executable=Word.raw_word("echo"))
    with pytest.raises(UnsupportedCompilationError, match="raw word"):
        to_argv(cmd2)


def test_to_argv_raises_on_env_and_redirects():
    """to_argv refuses a SimpleCommand carrying env or redirects."""
    cmd_env = SimpleCommand(
        executable=Word.literal("echo"),
        env=(("VAR", Word.literal("val")),),
    )
    with pytest.raises(UnsupportedCompilationError, match="env"):
        to_argv(cmd_env)

    cmd_redir = SimpleCommand(
        executable=Word.literal("echo"),
        redirects=(Redirect(op=RedirectOp.WRITE, target=Word.literal("out")),),
    )
    with pytest.raises(UnsupportedCompilationError, match="redirection"):
        to_argv(cmd_redir)


def test_word_literal_escape_works():
    """Word.literal is the escape: metacharacters reach argv unchanged."""
    cmd = SimpleCommand(
        executable=Word.literal("echo"),
        args=(Word.literal("$HOME"), Word.literal("*")),
    )
    assert to_argv(cmd) == ["echo", "$HOME", "*"]


def test_round_trip_property():
    """Round-trip property for plain commands.

    Restricted to commands with no raw words, no env and no redirects, since
    none of those three survive an argv list unchanged.
    """
    cmds = [
        SimpleCommand(executable=Word.literal("echo")),
        SimpleCommand(executable=Word.literal("echo"), args=(Word.literal("hello"),)),
        SimpleCommand(
            executable=Word.literal("echo"),
            args=(Word.literal("hello world"),),
        ),
        SimpleCommand(
            executable=Word.literal("echo"),
            args=(Word.literal("$HOME"), Word.literal("*")),
        ),
        SimpleCommand(
            executable=Word.literal("grep"),
            args=(Word.literal("-v"), Word.literal("foo bar")),
        ),
    ]

    for cmd in cmds:
        assert shlex.split(to_shell_string(cmd)) == to_argv(cmd)


def test_builder_flag_words_interaction():
    """A builder with any parameter set cannot be compiled to argv.

    ``_flag_words`` marks every flag ``raw=True`` so a multi-token flag such as
    ``-or -name`` is not folded into one quoted argument. Raw words are
    meaningless in argv, so such a command raises instead.
    """
    # We simulate the builder's output by creating a SimpleCommand with a raw word flag.
    cmd = SimpleCommand(
        executable=Word.literal("ls"),
        args=(Word.raw_word("-l"), Word.literal("dir")),
    )
    with pytest.raises(UnsupportedCompilationError, match="raw word"):
        to_argv(cmd)


def test_pipeline_operator_count_mismatch_raises():
    """A Pipeline must carry exactly one operator fewer than commands.

    Otherwise the compiler would silently drop a pipe and emit a command with
    different meaning -- `ls | wc | cat` becoming `ls wc cat`, which runs `ls`
    against two nonexistent filenames instead of failing.
    """
    cmd = SimpleCommand(executable=Word.literal("ls"))
    three = (cmd, cmd, cmd)

    with pytest.raises(UnsupportedCompilationError):
        to_shell_string(Pipeline(commands=three, operators=(PipeOp.STDOUT,)))

    with pytest.raises(UnsupportedCompilationError):
        to_shell_string(Pipeline(commands=three))

    with pytest.raises(UnsupportedCompilationError):
        to_shell_string(
            Pipeline(commands=three, operators=(PipeOp.STDOUT,) * 3)
        )


def test_single_command_pipeline_is_allowed():
    """A one-command pipeline is degenerate but well-formed: no operators."""
    cmd = SimpleCommand(executable=Word.literal("ls"))
    assert to_shell_string(Pipeline(commands=(cmd,))) == "ls"
