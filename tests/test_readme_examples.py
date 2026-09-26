from pyshb.contrib.coreutils import cd, grep


def test_coreutils_prebuild():
    cmd = (
        cd("/")
        & grep(color=True, ignore_case=True, regexp=("^bar=(.*)", "^baz$"))
        | grep(invert_match=True, regexp=(r"\d+",))
        + "2>&1"
        > "/dev/null"
    ) & "echo 'done!'"
    assert str(cmd) == (
        r"cd / && grep --color --ignore-case --regexp='^bar=(.*)' --regexp='^baz$' "
        r"| grep --invert-match --regexp='\d+' 2>&1 "
        r"> /dev/null && echo 'done!'"
    )
