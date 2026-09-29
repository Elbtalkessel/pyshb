from dataclasses import dataclass, field

from pyshb.base import Compose as _
from pyshb.base import ProgramMeta, Raw, ShellCommand


@dataclass
class sample(ShellCommand):
    value: str | Raw = ""
    enabled: bool = field(default=False, metadata={"flag": "--enabled"})
    optional: str | None = field(default=None, metadata={"flag": "--optional"})
    values: tuple[str, ...] = field(default_factory=tuple, metadata={"flag": "--value"})

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta("sample")


def test_scalar_strings_and_optional_values_are_serialized_as_single_arguments():
    assert str(sample("a b", enabled=True, values=("one", "two words"))) == (
        "sample --enabled --value=one --value='two words' 'a b'"
    )


def test_shell_arguments_are_quoted_and_raw_values_are_explicit():
    assert str(sample("it's; safe")) == "sample 'it'\"'\"'s; safe'"
    assert str(sample(Raw("$HOME"))) == "sample $HOME"


def test_composition_operators_do_not_mutate_their_left_operand():
    source = _("printf 'hello\\n'")
    assert str(source | "grep hello") == "printf 'hello\\n' | grep hello"
    assert str(source & "grep hello") == "printf 'hello\\n' && grep hello"
    assert str(source > "/tmp/file name") == "printf 'hello\\n' > '/tmp/file name'"
    assert str(source) == "printf 'hello\\n'"


def test_in_place_and_fluent_composition_remain_mutable():
    command = _("prepare")
    command |= "run"
    command &= "finish"
    assert str(command) == "prepare | run && finish"

    assert str(_("test").or_("recover").then("always")) == "test || recover ; always"


def test_redirections_and_raw_fragments():
    assert str(_("cat") < "/tmp/input file") == "cat < '/tmp/input file'"
    assert str(_("echo value") >> "/tmp/log file") == "echo value >> '/tmp/log file'"
    assert (
        str(_("echo value").append("/tmp/log", stderr=True))
        == "echo value &>> /tmp/log"
    )
    assert str(_("cat").here_string("two words")) == "cat <<< 'two words'"
    assert str(_("echo value") + "2>&1") == "echo value 2>&1"
