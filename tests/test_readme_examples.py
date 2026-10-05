"""Pins the target ergonomics, not live behaviour.

Every case here runs against :mod:`pyshb.base` and
:mod:`pyshb.contrib.coreutils`, both deprecated. They are kept precisely
because they are the clearest statement of how composing commands should feel --
operators first, named methods where Python has no operator -- and that surface
is not built yet at the AST layer.

When milestone 1 step 5 lands the fluent composition methods, port these cases
to the new surface rather than deleting them. They are the acceptance criteria
for that step.
"""

from pyshb.base import Compose as _
from pyshb.contrib.coreutils import cd, grep


def test_coreutils_prebuild():
    cmd = (
        _(cd("/"))
        .and_(grep(color=True, ignore_case=True, regexp=("^bar=(.*)", "^baz$")))
        .pipe(grep(invert_match=True, regexp=(r"\d+",)), stderr=True)
        .output("/dev/null")
        .and_("echo 'done!'")
    )
    assert str(cmd) == (
        r"cd / && grep --color --ignore-case --regexp='^bar=(.*)' --regexp='^baz$' "
        r"|& grep --invert-match --regexp='\d+' "
        r"> /dev/null && echo 'done!'"
    )


def test_any_command():
    cmd = (
        _("cd /")
        .and_("grep --ignore-case")
        .pipe("grep --invert-match", stderr=True)
        .output("/dev/null")
        .and_("echo 'done!'")
    )
    assert str(cmd) == (
        r"cd / && grep --ignore-case |& grep --invert-match > /dev/null && echo 'done!'"
    )


def test_any_command_special():
    assert str(
        _("echo 'hello world'")
        | _("grep 'hello'")
        & _("echo 'success!'")
        > _("/dev/null")
    ) == "echo 'hello world' | grep 'hello' && echo 'success!' > /dev/null"


def test_any_command_special_composable():
    cmd = _("echo 'hello world'")
    cmd |= _("grep 'hello'")
    cmd &= _("echo 'success!'")
    assert str(cmd) == "echo 'hello world' | grep 'hello' && echo 'success!'"


def test_prebuild_command_variants():
    assert str(grep("foo")) == "grep foo"
    assert str(grep("foo", color=False, ignore_case=True)) == "grep --ignore-case foo"
    assert str(grep(regexp=("foo", "bar"))) == "grep --regexp=foo --regexp=bar"


def test_prebuild_command_positional_and_keyword_options():
    cmd = _(cd("/tmp")).and_(grep("needle", ignore_case=True))
    assert str(cmd) == "cd /tmp && grep --ignore-case needle"


def test_string_commands_support_all_compositions():
    source = _("printf 'one\\ntwo\\n'")
    filter_cmd = _("grep two")
    assert str(source | filter_cmd) == "printf 'one\\ntwo\\n' | grep two"
    assert str(source & filter_cmd) == "printf 'one\\ntwo\\n' && grep two"
    assert str(source > _("/tmp/out")) == "printf 'one\\ntwo\\n' > /tmp/out"


def test_composable_operators_can_be_chained():
    cmd = _("printf 'hello\\n'") | _("grep hello") & _("wc -l") > _("/tmp/count")
    assert str(cmd) == "printf 'hello\\n' | grep hello && wc -l > /tmp/count"


def test_explicit_methods_compose_with_prebuilt_commands():
    cmd = _(cd("/tmp")).and_(grep(regexp="needle")).pipe("wc -l").output("/tmp/count")
    assert str(cmd) == "cd /tmp && grep --regexp=needle | wc -l > /tmp/count"


def test_stderr_redirection_and_output_redirection():
    cmd = _("my-command").pipe("handle-errors", stderr=True).output("/tmp/log")
    assert str(cmd) == "my-command |& handle-errors > /tmp/log"


def test_multiple_and_pipe_operations_preserve_order():
    cmd = _("prepare").and_("produce").pipe("filter").and_("finish")
    assert str(cmd) == "prepare && produce | filter && finish"


def test_redirection_can_be_composed_after_boolean_operator():
    cmd = _("build").and_("test").output("/dev/null")
    assert str(cmd) == "build && test > /dev/null"
