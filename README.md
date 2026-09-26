## Python Shell Command Builder

The library already has several GNU Core Utilities ready,
read more: https://en.wikipedia.org/wiki/GNU_Core_Utilities

```python
from pyshb.contrib import coreutils as s

assert str(
    s.cd("/")
    # Full type and documentation for every argument available!
    & s.grep("./file.txt", ignore_case=True, regexp=("^bar=(.*)", "^baz$"))
    | s.grep(invert_match=True, regexp=(r"\d+",))
    # Append any string.
    + "2>&1"
    # Redirect support.
    > "/dev/null"
    # All operators support plain strings too.
    & "echo 'done!'"
) == "cd / && grep --ignore-case --regexp='^bar=(.*)' --regexp='^baz$' | grep --invert-match --regexp='\d+' 2>&1 > /dev/null && echo 'done!'"
```
