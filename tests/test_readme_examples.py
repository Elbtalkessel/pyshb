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
