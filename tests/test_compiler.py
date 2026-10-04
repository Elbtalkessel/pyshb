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


def test_quoting_round_trip() -> None:
    """Quoting round-trip: values containing spaces, single quotes, $, *, and newlines survive shlex.split."""
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


def test_raw_pass_through() -> None:
    """Raw pass-through: Word.raw_word("$HOME") appears unquoted; Word.literal("$HOME") appears quoted."""
    raw = Word.raw_word("$HOME")
    assert to_shell_string(raw) == "$HOME"

    literal = Word.literal("$HOME")
    assert to_shell_string(literal) == "'$HOME'"


def test_empty_literal_renders_as_empty_quotes() -> None:
    """Empty literal renders as ''."""
    empty = Word.literal("")
    assert to_shell_string(empty) == "''"


def test_redirect_rendering() -> None:
    """Every RedirectOp renders the expected string, including the source_fd prefix form and an int target."""
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


def test_node_rendering_shapes() -> None:
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

    sub_redir = Subshell(body=cmd1, redirects=(Redirect(op=RedirectOp.WRITE, target=Word.literal("out")),))
    assert to_shell_string(sub_redir) == "( echo hi >out )"

    # CommandGroup
    grp = CommandGroup(body=cmd1)
    assert to_shell_string(grp) == "{ echo hi; }"

    grp_redir = CommandGroup(body=cmd1, redirects=(Redirect(op=RedirectOp.WRITE, target=Word.literal("out")),))
    assert to_shell_string(grp_redir) == "{ echo hi; >out }"


def test_to_argv_happy_path() -> None:
    """to_argv happy path on a SimpleCommand."""
    cmd = SimpleCommand(executable=Word.literal("echo"), args=(Word.literal("hello"), Word.literal("world")))
    assert to_argv(cmd) == ["echo", "hello", "world"]


def test_to_argv_raises_on_compound_nodes() -> None:
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


def test_to_argv_raises_on_raw_words() -> None:
    """A raw word is rejected, not passed through."""
    cmd = SimpleCommand(executable=Word.literal("echo"), args=(Word.raw_word("$HOME"),))
    with pytest.raises(UnsupportedCompilationError, match="Cannot compile raw word to argv"):
        to_argv(cmd)

    cmd2 = SimpleCommand(executable=Word.raw_word("echo"))
    with pytest.raises(UnsupportedCompilationError, match="Cannot compile raw word to argv"):
        to_argv(cmd2)


def test_to_argv_raises_on_env_and_redirects() -> None:
    """to_argv raises UnsupportedCompilationError if a SimpleCommand carries a non-empty env or redirects."""
    cmd_env = SimpleCommand(
        executable=Word.literal("echo"),
        env=(("VAR", Word.literal("val")),),
    )
    with pytest.raises(UnsupportedCompilationError, match="Cannot compile command with environment variables to argv"):
        to_argv(cmd_env)

    cmd_redir = SimpleCommand(
        executable=Word.literal("echo"),
        redirects=(Redirect(op=RedirectOp.WRITE, target=Word.literal("out")),),
    )
    with pytest.raises(UnsupportedCompilationError, match="Cannot compile command with redirections to argv"):
        to_argv(cmd_redir)


def test_word_literal_escape_works() -> None:
    """The Word.literal escape actually works: a Word.literal containing $HOME or * compiles to argv unchanged."""
    cmd = SimpleCommand(executable=Word.literal("echo"), args=(Word.literal("$HOME"), Word.literal("*")))
    assert to_argv(cmd) == ["echo", "$HOME", "*"]


def test_round_trip_property() -> None:
    """Round-trip property: for a set of generated SimpleCommands that have no raw words, no env, and no redirects,
    shlex.split(to_shell_string(cmd)) == to_argv(cmd).
    """
    cmds = [
        SimpleCommand(executable=Word.literal("echo")),
        SimpleCommand(executable=Word.literal("echo"), args=(Word.literal("hello"),)),
        SimpleCommand(executable=Word.literal("echo"), args=(Word.literal("hello world"),)),
        SimpleCommand(executable=Word.literal("echo"), args=(Word.literal("$HOME"), Word.literal("*"))),
        SimpleCommand(executable=Word.literal("grep"), args=(Word.literal("-v"), Word.literal("foo bar"))),
    ]

    for cmd in cmds:
        assert shlex.split(to_shell_string(cmd)) == to_argv(cmd)


def test_builder_flag_words_interaction() -> None:
    """CommandBuilder._flag_words() marks every flag word raw=True, so a builder with any parameter set
    produces raw words and therefore cannot be passed to to_argv.
    """
    # We simulate the builder's output by creating a SimpleCommand with a raw word flag.
    cmd = SimpleCommand(executable=Word.literal("ls"), args=(Word.raw_word("-l"), Word.literal("dir")))
    with pytest.raises(UnsupportedCompilationError, match="Cannot compile raw word to argv"):
        to_argv(cmd)
