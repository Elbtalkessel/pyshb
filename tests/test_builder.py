import inspect
from dataclasses import FrozenInstanceError

import pytest

from pyshb.ast import (
    CommandGroup,
    LogicalNode,
    LogicalOp,
    Pipeline,
    PipeOp,
    RedirectOp,
    SimpleCommand,
    Subshell,
    Word,
)
from pyshb.builder import CommandBuilder, ParamSpec, adhoc
from pyshb.exceptions import PyshbError, UnknownParameterError

GREP = {
    "ignore_case": ParamSpec(flag="--ignore-case"),
    "posix": ParamSpec(flag="--posix"),
    "regexp": ParamSpec(flag="--regexp"),
    "maxdepth": ParamSpec(flag="-maxdepth", arg_join=" "),
    "or_name": ParamSpec(flag="-or -name", arg_join=" "),
}


@pytest.fixture
def base() -> CommandBuilder:
    return CommandBuilder(SimpleCommand(executable=Word.literal("grep")), schema=GREP)


def simple_root(builder: CommandBuilder) -> SimpleCommand:
    """Narrow ``builder.root`` to ``SimpleCommand`` after asserting the shape.

    Composition methods replace the root with a compound node, so any test
    that peeks at ``root.args`` or ``root.executable`` must confirm the root
    has not changed. The assertion makes a regression visible here instead
    of as a cryptic ``AttributeError`` later.
    """
    assert isinstance(builder.root, SimpleCommand), builder.root
    return builder.root


def rendered(builder: CommandBuilder) -> tuple[tuple[str, bool], ...]:
    return tuple((word.value, word.raw) for word in simple_root(builder).args)


def values(builder: CommandBuilder) -> tuple[str, ...]:
    return tuple(word.value for word in simple_root(builder).args)


def test_param_spec_default_joiner():
    assert ParamSpec(flag="-c").arg_join == "="
    assert ParamSpec(flag="-maxdepth", arg_join=" ").arg_join == " "


def test_schema_is_required_and_keyword_only():
    parameters = inspect.signature(CommandBuilder).parameters
    assert "schema" in parameters
    assert parameters["schema"].kind is inspect.Parameter.KEYWORD_ONLY


def test_builder_is_frozen(base: CommandBuilder):
    with pytest.raises((FrozenInstanceError, AttributeError)):
        base.__setattr__("params", {})


def test_set_leaves_base_untouched(base: CommandBuilder):
    captured_root = simple_root(base)
    captured_args = captured_root.args
    captured_executable = captured_root.executable
    captured_params = base.params
    captured_positionals = base.positionals

    strict = base.set(ignore_case=True)
    positional = base.args("needle")

    assert base.root is captured_root
    assert simple_root(base).args == captured_args
    assert simple_root(base).executable == captured_executable
    assert base.params == captured_params
    assert base.positionals == captured_positionals
    assert rendered(base) == ()
    assert base is not strict
    assert base is not positional
    assert strict is not positional


def test_branch_independence(base: CommandBuilder):
    strict = base.set(ignore_case=True)
    posix = base.set(posix=True)

    assert rendered(base) == ()
    assert rendered(strict) == (("--ignore-case", True),)
    assert rendered(posix) == (("--posix", True),)
    assert strict.params == {"ignore_case": True}
    assert posix.params == {"posix": True}


def test_set_override_keeps_last_value(base: CommandBuilder):
    result = base.set(regexp="^a$").set(regexp="^b$")
    assert result.params["regexp"] == "^b$"
    assert rendered(result) == (("--regexp=^b$", False),)


def test_set_unknown_param_raises(base: CommandBuilder):
    with pytest.raises(UnknownParameterError) as caught:
        base.set(ignore_case=True, nope=True)

    exc = caught.value
    assert isinstance(exc, PyshbError)
    assert exc.param == "nope"
    assert exc.known == ("ignore_case", "maxdepth", "or_name", "posix", "regexp")
    assert "nope" in str(exc)
    assert rendered(base) == ()


def test_args_ordering_and_accumulation(base: CommandBuilder):
    result = base.args("a").args("b").args("c")

    assert values(result) == ("a", "b", "c")
    assert all(not word.raw for word in simple_root(result).args)
    assert rendered(base) == ()


def test_args_raw_true_produces_raw_words(base: CommandBuilder):
    assert rendered(base.args("$HOME", "*.txt", raw=True)) == (
        ("$HOME", True),
        ("*.txt", True),
    )


def test_args_raw_false_quotes_the_same_arguments(base: CommandBuilder):
    assert rendered(base.args("$HOME", "*.txt", raw=False)) == (
        ("$HOME", False),
        ("*.txt", False),
    )


def test_args_accepts_prebuilt_word_unchanged(base: CommandBuilder):
    prebuilt = Word.literal("needle")
    assert simple_root(base.args(prebuilt)).args[0] is prebuilt
    assert simple_root(base.args(prebuilt, raw=True)).args[0] is prebuilt


def test_when_applies_transform_when_true(base: CommandBuilder):
    applied = base.when(True, lambda c: c.set(ignore_case=True))
    assert rendered(applied) == (("--ignore-case", True),)


def test_when_returns_equal_untouched_builder_when_false(base: CommandBuilder):
    skipped = base.when(False, lambda c: c.set(ignore_case=True))
    assert skipped == base
    assert rendered(skipped) == ()


def test_bool_renders_bare_flag_not_joined_value(base: CommandBuilder):
    # A bool carries no value, so arg_join never applies and the flag is
    # emitted bare. The raw marker is unobservable for a single-token flag --
    # shlex.quote("--posix") is "--posix" -- so it is not load-bearing here.
    # Flags are marked raw uniformly so the multi-token case cannot be
    # special-cased and forgotten; see test_multi_token_flag_stays_raw.
    assert rendered(base.set(posix=True)) == (("--posix", True),)
    assert rendered(base.set(maxdepth=True)) == (("-maxdepth", True),)
    assert rendered(base.set(maxdepth=3)) == (("-maxdepth", True), ("3", False))


def test_equals_joiner_emits_single_joined_word(base: CommandBuilder):
    assert rendered(base.set(regexp="^a b$")) == (("--regexp=^a b$", False),)


def test_space_joiner_emits_separate_words(base: CommandBuilder):
    flag, value = simple_root(base.set(maxdepth=3)).args
    assert (flag.value, flag.raw) == ("-maxdepth", True)
    assert (value.value, value.raw) == ("3", False)


def test_multi_token_flag_stays_raw_and_unsplit(base: CommandBuilder):
    # shlex.quote("-or -name") is "'-or -name'", which collapses two tokens
    # into one argument. This is the case the raw marker actually protects.
    flag, value = simple_root(base.set(or_name="*.log")).args
    assert (flag.value, flag.raw) == ("-or -name", True)
    assert (value.value, value.raw) == ("*.log", False)


def test_false_unsets_previously_set_param(base: CommandBuilder):
    assert rendered(base.set(maxdepth=3).set(maxdepth=False)) == ()
    assert rendered(base.set(posix=True).set(posix=False)) == ()
    assert rendered(base.set(regexp="x").set(regexp=False)) == ()


def test_flags_precede_positionals(base: CommandBuilder):
    result = base.args("needle").set(ignore_case=True)
    assert rendered(result) == (("--ignore-case", True), ("needle", False))


def test_repeated_transformations_do_not_duplicate_args(base: CommandBuilder):
    result = base.args("a").set(ignore_case=True).args("b").set(posix=True)
    assert rendered(result) == (
        ("--ignore-case", True),
        ("--posix", True),
        ("a", False),
        ("b", False),
    )


def test_existing_root_args_adopted_as_positionals():
    root = SimpleCommand(
        executable=Word.literal("grep"),
        args=(Word.literal("pre"),),
    )
    adopted = CommandBuilder(root, schema=GREP)

    assert rendered(adopted) == (("pre", False),)
    assert rendered(adopted.args("post")) == (("pre", False), ("post", False))
    assert values(adopted.set(ignore_case=True)) == ("--ignore-case", "pre")
    assert values(adopted.set(maxdepth=2)) == ("-maxdepth", "2", "pre")


def test_adhoc_string_executable():
    builder = adhoc("grep")
    assert simple_root(builder).executable == Word.literal("grep")


def test_adhoc_word_executable():
    word = Word.raw_word("$PROG")
    builder = adhoc(word)
    executable = simple_root(builder).executable
    assert executable is word
    assert executable.raw is True


def test_adhoc_returns_command_builder():
    builder = adhoc("grep")
    assert isinstance(builder, CommandBuilder)


def test_adhoc_set_raises_unknown_parameter():
    builder = adhoc("grep")
    with pytest.raises(UnknownParameterError) as caught:
        builder.set(flag=True)
    assert str(caught.value).endswith("(none)")


def test_adhoc_args_chaining_preserves_order_and_immutability():
    builder = adhoc("grep")
    result1 = builder.args("a")
    result2 = result1.args("b")

    assert values(builder) == ()
    assert values(result1) == ("a",)
    assert values(result2) == ("a", "b")
    assert builder is not result1
    assert result1 is not result2


def test_adhoc_root_materialisation_invariant():
    builder = adhoc("grep").args("a", "b")
    root = simple_root(builder)
    assert root.args == builder.positionals
    assert values(builder) == ("a", "b")


def test_adhoc_args_raw_flag():
    builder = adhoc("grep").args("a").args("b", raw=True)
    assert rendered(builder) == (("a", False), ("b", True))


def test_pipe_returns_pipeline_node():
    result = adhoc("a").pipe(adhoc("b"))
    assert isinstance(result.root, Pipeline)
    assert len(result.root.commands) == 2
    assert len(result.root.operators) == 1
    assert result.root.operators == (PipeOp.STDOUT,)


def test_pipe_extends_existing_pipeline_flat_not_nested():
    result = adhoc("a").pipe(adhoc("b")).pipe(adhoc("c"))

    assert isinstance(result.root, Pipeline)
    assert len(result.root.commands) == 3
    assert len(result.root.operators) == 2
    assert all(isinstance(cmd, SimpleCommand) for cmd in result.root.commands)
    assert result.root.operators == (PipeOp.STDOUT, PipeOp.STDOUT)


def test_operator_length_invariant_after_pipe_chain():
    result = (
        adhoc("a")
        .pipe(adhoc("b"))
        .pipe(adhoc("c"))
        .pipe(adhoc("d"))
        .pipe(adhoc("e"))
    )
    assert isinstance(result.root, Pipeline)
    assert len(result.root.operators) == len(result.root.commands) - 1


def test_pipe_all_renders_pipeop_all():
    result = adhoc("a").pipe_all(adhoc("b"))
    assert isinstance(result.root, Pipeline)
    assert result.root.operators == (PipeOp.ALL,)


def test_and_builds_logical_node_with_AND():
    result = adhoc("a").and_(adhoc("b"))
    assert isinstance(result.root, LogicalNode)
    assert result.root.op == LogicalOp.AND
    assert isinstance(result.root.left, SimpleCommand)
    assert isinstance(result.root.right, SimpleCommand)


def test_or_builds_logical_node_with_OR():
    result = adhoc("a").or_(adhoc("b"))
    assert isinstance(result.root, LogicalNode)
    assert result.root.op == LogicalOp.OR


def test_then_builds_logical_node_with_sequence():
    result = adhoc("a").then(adhoc("b"))
    assert isinstance(result.root, LogicalNode)
    assert result.root.op == LogicalOp.SEQUENCE


def test_subshell_wraps_root_in_parens():
    inner = adhoc("a").and_(adhoc("b"))
    result = inner.subshell()
    assert isinstance(result.root, Subshell)
    assert isinstance(result.root.body, LogicalNode)
    assert result.root.redirects == ()


def test_group_wraps_root_in_braces():
    inner = adhoc("a").and_(adhoc("b"))
    result = inner.group()
    assert isinstance(result.root, CommandGroup)
    assert isinstance(result.root.body, LogicalNode)


def test_subshell_then_pipe_renders_grouping():
    """README §4.1 case: a && b grouped, then piped.

    The && binds inside the parens, the | outside, so the rendered form is
    exactly ``(a && b) | c`` and not ``a && b | c``.
    """
    cmd = adhoc("a").and_(adhoc("b")).subshell().pipe(adhoc("c"))
    assert cmd.root.to_shell_string() == "(a && b) | c"


def test_group_then_pipe_renders_braced_form():
    cmd = adhoc("a").and_(adhoc("b")).group().then(adhoc("c"))
    assert cmd.root.to_shell_string() == "{ a && b; } ; c"


def test_pipe_accepts_command_node_not_only_builder():
    result = adhoc("a").pipe(SimpleCommand(executable=Word.literal("b")))
    assert isinstance(result.root, Pipeline)
    assert len(result.root.commands) == 2


def test_and_then_pipe_compose_left_to_right():
    cmd = adhoc("a").and_(adhoc("b")).pipe(adhoc("c")).and_(adhoc("d"))
    assert cmd.root.to_shell_string() == "a && b | c && d"


def test_redirect_out_appends_write_redirect():
    cmd = adhoc("echo").redirect_out("file.txt")
    root = simple_root(cmd)
    assert len(root.redirects) == 1
    assert root.redirects[0].op == RedirectOp.WRITE
    assert root.redirects[0].target == Word.literal("file.txt")
    assert root.redirects[0].source_fd is None


def test_redirect_out_then_append_out_accumulate_in_order():
    cmd = adhoc("echo").redirect_out("a").append_out("b")
    root = simple_root(cmd)
    assert len(root.redirects) == 2
    assert root.redirects[0].op == RedirectOp.WRITE
    assert root.redirects[0].target == Word.literal("a")
    assert root.redirects[1].op == RedirectOp.APPEND
    assert root.redirects[1].target == Word.literal("b")


def test_redirect_err_uses_source_fd_two():
    cmd = adhoc("echo").redirect_err("err.log")
    root = simple_root(cmd)
    assert root.redirects[0].op == RedirectOp.WRITE
    assert root.redirects[0].source_fd == 2


def test_redirect_all_uses_both_write():
    cmd = adhoc("echo").redirect_all("both.log")
    root = simple_root(cmd)
    assert root.redirects[0].op == RedirectOp.BOTH_WRITE


def test_redirect_in_uses_read():
    cmd = adhoc("cat").redirect_in("input.txt")
    root = simple_root(cmd)
    assert root.redirects[0].op == RedirectOp.READ


def test_here_string_uses_here_string_op_with_literal_target():
    cmd = adhoc("cat").here_string("two words")
    root = simple_root(cmd)
    assert root.redirects[0].op == RedirectOp.HERE_STRING
    assert root.redirects[0].target == Word.literal("two words")


def test_heredoc_emits_opener_body_and_closer():
    cmd = adhoc("cat").heredoc("hello\nworld")
    rendered = cmd.root.to_shell_string()
    assert rendered == "cat <<EOF\nhello\nworld\nEOF"


def test_heredoc_default_delimiter_is_EOF():
    cmd = adhoc("cat").heredoc("body")
    root = simple_root(cmd)
    assert root.redirects[0].target == Word.literal("EOF")


def test_heredoc_custom_delimiter():
    cmd = adhoc("cat").heredoc("body", delimiter="END")
    assert cmd.root.to_shell_string().endswith("\nEND")


def test_redirect_source_fd_to_other_fd_is_dup_out():
    """The general escape hatch for ``2>&1`` style redirections."""
    cmd = adhoc("echo").redirect(source_fd=2, to_fd=1)
    root = simple_root(cmd)
    assert len(root.redirects) == 1
    assert root.redirects[0].op == RedirectOp.DUP_OUT
    assert root.redirects[0].source_fd == 2
    assert root.redirects[0].target == 1


def test_redirect_source_fd_with_target_is_write_to_fd():
    cmd = adhoc("echo").redirect(source_fd=2, target="err.log")
    root = simple_root(cmd)
    assert root.redirects[0].op == RedirectOp.WRITE
    assert root.redirects[0].source_fd == 2
    assert root.redirects[0].target == Word.literal("err.log")


def test_redirect_requires_exactly_one_of_to_fd_or_target():
    with pytest.raises(ValueError):
        adhoc("echo").redirect(source_fd=2)
    with pytest.raises(ValueError):
        adhoc("echo").redirect(source_fd=2, to_fd=1, target="x")


def test_redirect_on_pipeline_targets_rightmost_command():
    """``a | b > file`` writes b's stdout to file, not a's.

    The redirect is the last token and the pipeline binds left-to-right,
    so the builder threads the redirect into the last command's redirects
    tuple rather than duplicating it across every stage.
    """
    pipeline = adhoc("a").pipe(adhoc("b")).redirect_out("file")
    assert isinstance(pipeline.root, Pipeline)
    last = pipeline.root.commands[-1]
    assert isinstance(last, SimpleCommand)
    assert len(last.redirects) == 1
    assert last.redirects[0].target == Word.literal("file")
    first = pipeline.root.commands[0]
    assert isinstance(first, SimpleCommand)
    assert first.redirects == ()


def test_redirect_on_logical_node_targets_rightmost_command():
    logical = (
        adhoc("a").pipe(adhoc("b")).and_(adhoc("c")).redirect_err("err.log")
    )
    assert isinstance(logical.root, LogicalNode)
    c_node = logical.root.right
    assert isinstance(c_node, SimpleCommand)
    assert len(c_node.redirects) == 1
    assert c_node.redirects[0].op == RedirectOp.WRITE
    assert c_node.redirects[0].source_fd == 2


def test_redirect_on_subshell_targets_subshell_not_inner():
    """``(a && b) > file`` redirects the whole subshell, not just ``b``.

    A redirect after ``)`` binds to the subshell as a whole. Routing it
    inside the parens would render ``(a && b > file)``, which redirects only
    ``b``'s stdout — a silently different command.
    """
    cmd = adhoc("a").and_(adhoc("b")).subshell().redirect_out("file")
    assert isinstance(cmd.root, Subshell)
    assert len(cmd.root.redirects) == 1
    assert cmd.root.redirects[0].target == Word.literal("file")
    inner = cmd.root.body
    assert isinstance(inner, LogicalNode)
    last = inner.right
    assert isinstance(last, SimpleCommand)
    assert last.redirects == ()


def test_redirect_on_group_targets_group_not_inner():
    """``{ a && b; } > file`` redirects the whole group, not just ``b``."""
    cmd = adhoc("a").and_(adhoc("b")).group().redirect_out("file")
    assert isinstance(cmd.root, CommandGroup)
    assert len(cmd.root.redirects) == 1
    assert cmd.root.redirects[0].target == Word.literal("file")
    inner = cmd.root.body
    assert isinstance(inner, LogicalNode)
    last = inner.right
    assert isinstance(last, SimpleCommand)
    assert last.redirects == ()


def test_redirect_on_pipeline_with_subshell_targets_subshell():
    """``a | (b && c) > file`` redirects the subshell, not ``c``."""
    cmd = adhoc("a").pipe(adhoc("b").and_(adhoc("c")).subshell()).redirect_out("file")
    assert isinstance(cmd.root, Pipeline)
    last = cmd.root.commands[-1]
    assert isinstance(last, Subshell)
    assert len(last.redirects) == 1
    assert last.redirects[0].target == Word.literal("file")


def test_args_on_compound_root_raises_type_error():
    pipeline = adhoc("a").pipe(adhoc("b"))
    with pytest.raises(TypeError):
        pipeline.args("x")


def test_set_on_compound_root_raises_type_error():
    """``set()`` on a compound root would silently store params that never
    materialise into any node, so it raises instead."""
    pipeline = adhoc("a").pipe(adhoc("b"))
    with pytest.raises(TypeError):
        pipeline.set(ignore_case=True)


def test_pipe_sugar_equals_pipe_method():
    via_method = adhoc("a").pipe(adhoc("b"))
    via_sugar = adhoc("a") | adhoc("b")
    assert via_method.root == via_sugar.root


def test_and_sugar_equals_and_method():
    via_method = adhoc("a").and_(adhoc("b"))
    via_sugar = adhoc("a") & adhoc("b")
    assert via_method.root == via_sugar.root


def test_or_sugar_equals_or_method():
    via_method = adhoc("a").or_(adhoc("b"))
    via_sugar = adhoc("a") ^ adhoc("b")
    assert via_method.root == via_sugar.root


def test_redirect_out_sugar_equals_method():
    via_method = adhoc("echo").redirect_out("file")
    via_sugar = adhoc("echo") > "file"
    assert simple_root(via_method).redirects == simple_root(via_sugar).redirects


def test_append_out_sugar_equals_method():
    via_method = adhoc("echo").append_out("file")
    via_sugar = adhoc("echo") << "file"
    assert simple_root(via_method).redirects == simple_root(via_sugar).redirects


def test_redirect_in_sugar_equals_method():
    via_method = adhoc("cat").redirect_in("file")
    via_sugar = adhoc("cat") < "file"
    assert simple_root(via_method).redirects == simple_root(via_sugar).redirects


def test_operator_sugar_chains_with_methods():
    cmd = (adhoc("a") | adhoc("b")).pipe(adhoc("c")).and_(adhoc("d"))
    assert cmd.root.to_shell_string() == "a | b | c && d"


def test_operator_sugar_accepts_command_node():
    """The dunders accept a raw ``CommandNode``, not only a builder.

    ``pipe``/``and_``/``or_`` accept ``CommandNode | Self``; the sugar
    delegates to them, so ``builder | SimpleCommand(...)`` must type-check.
    """
    node = SimpleCommand(executable=Word.literal("b"))
    via_pipe = adhoc("a").pipe(node)
    via_or = adhoc("a") | node
    assert via_pipe.root == via_or.root


def test_composition_methods_leave_source_untouched():
    a = adhoc("a")
    b = adhoc("b")
    captured = a.root
    _ = a.pipe(b)
    _ = a.pipe_all(b)
    _ = a.and_(b)
    _ = a.or_(b)
    _ = a.then(b)
    _ = a.subshell()
    _ = a.group()
    assert a.root is captured
    assert isinstance(a.root, SimpleCommand)


def test_redirect_methods_leave_source_untouched():
    a = adhoc("echo")
    captured = simple_root(a)
    _ = a.redirect_out("file")
    _ = a.append_out("log")
    _ = a.redirect_err("err")
    _ = a.redirect_all("both")
    _ = a.redirect_in("in")
    _ = a.here_string("x")
    _ = a.heredoc("body")
    _ = a.redirect(source_fd=2, to_fd=1)
    assert simple_root(a) is captured
    assert captured.redirects == ()


def test_operator_sugar_leaves_source_untouched():
    a = adhoc("a")
    b = adhoc("b")
    captured = a.root
    _ = a | b
    _ = a & b
    _ = a ^ b
    _ = a > "f"
    _ = a << "f"
    _ = a < "f"
    assert a.root is captured
