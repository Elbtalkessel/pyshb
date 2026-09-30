from dataclasses import FrozenInstanceError

from pyshb.ast import (
    ASTNode,
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


def test_word_creation_and_factories():
    w1 = Word.literal("hello")
    assert w1.value == "hello"
    assert not w1.raw
    assert w1.children == ()

    w2 = Word.raw_word("$VAR")
    assert w2.value == "$VAR"
    assert w2.raw
    assert w2.children == ()


def test_word_immutability():
    w = Word.literal("test")
    try:
        w.__setattr__("value", "changed")
    except (FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError("Expected modification of frozen Word to raise FrozenInstanceError")


def test_redirect_creation_and_children():
    target_word = Word.literal("/tmp/output.log")
    r_file = Redirect(op=RedirectOp.WRITE, target=target_word, source_fd=1)
    assert r_file.children == (target_word,)

    r_dup = Redirect(op=RedirectOp.DUP_OUT, target=1, source_fd=2)
    assert r_dup.children == ()


def test_simple_command_children_and_env():
    cmd_word = Word.literal("grep")
    arg1 = Word.literal("-i")
    arg2 = Word.literal("needle")
    redir = Redirect(op=RedirectOp.READ, target=Word.literal("input.txt"))
    env_val = Word.literal("C")

    cmd = SimpleCommand(
        executable=cmd_word,
        args=(arg1, arg2),
        redirects=(redir,),
        env=(("LC_ALL", env_val),),
    )

    assert cmd.children == (cmd_word, env_val, arg1, arg2, redir)


def test_pipeline_and_logical_nodes():
    c1 = SimpleCommand(executable=Word.literal("cat"))
    c2 = SimpleCommand(executable=Word.literal("grep"))
    c3 = SimpleCommand(executable=Word.literal("wc"))

    pipeline = Pipeline(commands=(c1, c2), operators=(PipeOp.STDOUT,))
    assert pipeline.children == (c1, c2)

    logical = LogicalNode(left=pipeline, op=LogicalOp.AND, right=c3)
    assert logical.children == (pipeline, c3)


def test_subshell_and_command_group():
    cmd = SimpleCommand(executable=Word.literal("echo"))
    redir = Redirect(op=RedirectOp.APPEND, target=Word.literal("out.log"))

    subshell = Subshell(body=cmd, redirects=(redir,))
    assert subshell.children == (cmd, redir)

    group = CommandGroup(body=cmd, redirects=(redir,))
    assert group.children == (cmd, redir)


def test_walk_pre_order_traversal():
    c1 = SimpleCommand(executable=Word.literal("cat"), args=(Word.literal("file.txt"),))
    c2 = SimpleCommand(executable=Word.literal("wc"), args=(Word.literal("-l"),))
    pipe = Pipeline(commands=(c1, c2))
    subshell = Subshell(body=pipe)

    nodes = list(subshell.walk())
    expected = [
        subshell,
        pipe,
        c1,
        c1.executable,
        c1.args[0],
        c2,
        c2.executable,
        c2.args[0],
    ]
    assert nodes == expected


def test_hashable_and_usable_in_sets():
    w1 = Word.literal("test")
    w2 = Word.literal("test")
    assert w1 == w2
    assert hash(w1) == hash(w2)

    s = {w1, w2}
    assert len(s) == 1

    cmd1 = SimpleCommand(executable=w1)
    cmd2 = SimpleCommand(executable=w2)
    assert cmd1 == cmd2
    assert hash(cmd1) == hash(cmd2)


def test_pattern_matching_compatibility():
    node: ASTNode = SimpleCommand(
        executable=Word.literal("grep"),
        args=(Word.literal("-E"), Word.literal("pattern")),
    )

    match node:
        case SimpleCommand(executable=Word(val), args=args):
            assert val == "grep"
            assert len(args) == 2
        case _:
            raise AssertionError("Failed to match SimpleCommand")
