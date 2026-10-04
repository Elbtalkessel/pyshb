import inspect
from dataclasses import FrozenInstanceError

from pyshb.ast import SimpleCommand, Word
from pyshb.builder import CommandBuilder, ParamSpec
from pyshb.exceptions import PyshbError, UnknownParameterError

GREP = {
    "ignore_case": ParamSpec(flag="--ignore-case"),
    "posix": ParamSpec(flag="--posix"),
    "regexp": ParamSpec(flag="--regexp"),
    "maxdepth": ParamSpec(flag="-maxdepth", arg_join=" "),
    "or_name": ParamSpec(flag="-or -name", arg_join=" "),
}


def make_base() -> CommandBuilder:
    return CommandBuilder(SimpleCommand(executable=Word.literal("grep")), schema=GREP)


def rendered(builder: CommandBuilder) -> tuple[tuple[str, bool], ...]:
    return tuple((word.value, word.raw) for word in builder.root.args)


def values(builder: CommandBuilder) -> tuple[str, ...]:
    return tuple(word.value for word in builder.root.args)


def test_param_spec_default_joiner():
    assert ParamSpec(flag="-c").arg_join == "="
    assert ParamSpec(flag="-maxdepth", arg_join=" ").arg_join == " "


def test_schema_is_required_and_keyword_only():
    parameters = inspect.signature(CommandBuilder).parameters
    assert "schema" in parameters
    assert parameters["schema"].kind is inspect.Parameter.KEYWORD_ONLY
    assert parameters["schema"].default is inspect.Parameter.empty


def test_builder_is_frozen():
    base = make_base()
    try:
        base.__setattr__("params", {})
    except (FrozenInstanceError, AttributeError):
        pass
    else:
        raise AssertionError("Expected mutation of a frozen builder to raise")


def test_set_leaves_base_untouched():
    base = make_base()
    captured_root = base.root
    captured_args = base.root.args
    captured_executable = base.root.executable
    captured_params = base.params
    captured_positionals = base.positionals

    strict = base.set(ignore_case=True)
    positional = base.args("needle")

    assert base.root is captured_root
    assert base.root.args == captured_args
    assert base.root.executable == captured_executable
    assert base.params == captured_params
    assert base.positionals == captured_positionals
    assert rendered(base) == ()
    assert base is not strict
    assert base is not positional
    assert strict is not positional


def test_branch_independence():
    base = make_base()
    strict = base.set(ignore_case=True)
    posix = base.set(posix=True)

    assert rendered(base) == ()
    assert rendered(strict) == (("--ignore-case", True),)
    assert rendered(posix) == (("--posix", True),)
    assert strict.params == {"ignore_case": True}
    assert posix.params == {"posix": True}


def test_set_override_keeps_last_value():
    result = make_base().set(regexp="^a$").set(regexp="^b$")
    assert result.params["regexp"] == "^b$"
    assert rendered(result) == (("--regexp=^b$", False),)


def test_set_unknown_param_raises():
    base = make_base()
    try:
        base.set(ignore_case=True, nope=True)
    except UnknownParameterError as exc:
        assert isinstance(exc, PyshbError)
        assert exc.param == "nope"
        assert exc.known == (
            "ignore_case",
            "maxdepth",
            "or_name",
            "posix",
            "regexp",
        )
        assert "nope" in str(exc)
    else:
        raise AssertionError("Expected UnknownParameterError for unknown param")
    assert rendered(base) == ()


def test_args_ordering_and_accumulation():
    base = make_base()
    result = base.args("a").args("b").args("c")

    assert values(result) == ("a", "b", "c")
    assert all(not word.raw for word in result.root.args)
    assert rendered(base) == ()


def test_args_raw_true_produces_raw_words():
    result = make_base().args("$HOME", raw=True)
    assert rendered(result) == (("$HOME", True),)


def test_args_accepts_prebuilt_word_unchanged():
    prebuilt = Word.literal("needle")
    assert make_base().args(prebuilt).root.args[0] is prebuilt
    assert make_base().args(prebuilt, raw=True).root.args[0] is prebuilt


def test_when_applies_transform_when_true():
    base = make_base()
    applied = base.when(True, lambda c: c.set(ignore_case=True))
    assert rendered(applied) == (("--ignore-case", True),)


def test_when_returns_equal_untouched_builder_when_false():
    base = make_base()
    skipped = base.when(False, lambda c: c.set(ignore_case=True))
    assert skipped == base
    assert rendered(skipped) == ()


def test_bool_renders_bare_flag_not_joined_value():
    base = make_base()
    assert rendered(base.set(posix=True)) == (("--posix", True),)
    assert rendered(base.set(maxdepth=True)) == (("-maxdepth", True),)
    assert rendered(base.set(maxdepth=3)) == (("-maxdepth", True), ("3", False))


def test_equals_joiner_emits_single_joined_word():
    assert rendered(make_base().set(regexp="^a b$")) == (("--regexp=^a b$", False),)


def test_space_joiner_emits_separate_words():
    flag, value = make_base().set(maxdepth=3).root.args
    assert (flag.value, flag.raw) == ("-maxdepth", True)
    assert (value.value, value.raw) == ("3", False)


def test_multi_token_flag_stays_raw_and_unsplit():
    flag, value = make_base().set(or_name="*.log").root.args
    assert (flag.value, flag.raw) == ("-or -name", True)
    assert (value.value, value.raw) == ("*.log", False)


def test_false_unsets_previously_set_param():
    base = make_base()
    assert rendered(base.set(maxdepth=3).set(maxdepth=False)) == ()
    assert rendered(base.set(posix=True).set(posix=False)) == ()
    assert rendered(base.set(regexp="x").set(regexp=False)) == ()


def test_flags_precede_positionals():
    result = make_base().args("needle").set(ignore_case=True)
    assert rendered(result) == (("--ignore-case", True), ("needle", False))


def test_repeated_transformations_do_not_duplicate_args():
    result = make_base().args("a").set(ignore_case=True).args("b").set(posix=True)
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
