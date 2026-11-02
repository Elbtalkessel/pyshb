# pyshb

Build shell commands in Python without string concatenation.

```python
from pyshb import CommandBuilder, ParamSpec, SimpleCommand, Word

GREP = {
    "ignore_case": ParamSpec("--ignore-case"),
    "line_numbers": ParamSpec("--line-number"),
}

cmd = (
    CommandBuilder(SimpleCommand(executable=Word.literal("grep")), schema=GREP)
    .args("Traceback")
    .set(ignore_case=True, line_numbers=True)
)

cmd.root.to_shell_string()
# grep --ignore-case --line-number Traceback
```

That is the whole interface. Five names are public; everything else is
implementation you should not need.

## Why

Shell commands built by concatenating strings are quoted by luck. `find . -name
*.log` looks right and breaks on any filename with a space in it. Fixing that
means remembering `shlex.quote` at every call site, and forgetting one is a bug
that only shows up on someone else's machine.

`pyshb` holds the command as data until the moment it becomes a string, then
quotes every argument for you. `Word.literal("*.log")` renders as `'*.log'`, so
the glob reaches the shell intact instead of being expanded by your own shell
first.

## Install

```console
$ pip install pyshb
```

Python 3.14+. No runtime dependencies.

## The five public names

| Name | What it is |
| --- | --- |
| `Word` | One argument. `Word.literal(s)` quotes it, `Word.raw_word(s)` passes it through for `$VAR` and globs. |
| `SimpleCommand` | An executable plus its arguments, redirections and `NAME=value` prefixes. |
| `ParamSpec` | One flag: its spelling and how it joins its value, `arg_join="="` or `" "`. |
| `CommandBuilder` | Wraps a command with a flag schema. Every method returns a new builder. |
| `adhoc` | A builder with no schema, for programs the library knows nothing about. |

## Declaring flags

A schema is a plain dict of name to `ParamSpec`. The names are what you call
`.set()` with.

```python
FIND = {
    "type": ParamSpec("-type", arg_join=" "),
    "name": ParamSpec("-name", arg_join=" "),
}

base_find = CommandBuilder(
    SimpleCommand(executable=Word.literal("find")),
    schema=FIND,
).args("/var/log").set(type="f")
```

## Nothing mutates

Every method returns a new builder, so you can branch freely.

```python
error_logs = base_find.set(name="*.error.log")
recent = base_find.set(name="*.log")

base_find.root.to_shell_string()
# find -type f /var/log
```

The original is untouched. If a name is not in the schema, `.set()` raises
`UnknownParameterError` naming what was available — rather than silently emitting
a flag the program does not have.

## Conditional commands

Plain `if` statements work, because the builder is immutable:

```python
name = "*.log"

cmd = base_find
if name:
    cmd = cmd.set(name=name)
```

There is also a `.when()` helper for staying in one chain:

```python
depth = None

cmd = (
    base_find
    .when(name, lambda c: c.set(name=name))
    .when(depth is not None, lambda c: c.args("-maxdepth", str(depth)))
)
```

## Flags with no schema

The shell accepts any flag spelling for any program, so a schema cannot be a
closed set. For programs the library knows nothing about, use `adhoc`:

```python
from pyshb import Word, adhoc

cmd = adhoc("my-custom-tool").args("--unknown-flag", "value")
cmd = adhoc(Word.raw_word("$PROG")).args("--version")
```

## Two ways out

```python
cmd.root.to_shell_string()   # a quoted shell string
```

For `subprocess` you can skip the shell entirely. `to_argv` takes the node and
returns `list[str]`, ready for `shell=False`:

```python
from pyshb import CommandBuilder, SimpleCommand, Word
from pyshb.compiler import to_argv

cmd = CommandBuilder(
    SimpleCommand(executable=Word.literal("ls")), schema={}
).args("/var/log")

argv = to_argv(cmd.root)
# ['ls', '/var/log']

# then: subprocess.run(argv, shell=False)
```

`to_argv` is strict. It raises `UnsupportedCompilationError` unless the result is
a plain command with literal arguments: no pipes, no redirects, no `env` prefix,
and no raw words. A faithful argv list for those would need a shell to evaluate,
so it refuses rather than guessing.

That last condition bites more often than you would expect. Every flag set
through a schema becomes a raw word, so a builder carrying any `arg_join=" "`
parameter cannot be exported:

```python
to_argv(base_find.root)                    # fine: no parameters set
to_argv(base_find.set(name="x").root)      # UnsupportedCompilationError
```

Use `to_shell_string()` for anything with flags.

One thing to know: `dialect` is accepted and ignored. Every dialect renders
identically, and that rendering can use bash-only syntax such as `|&` and `<<<`,
so the output is not strictly POSIX.

## Compositing

Composition is fluent and immutable, like the rest of the builder. Every method
returns a new builder, so a shared prefix is safe to branch from.

```python
from pyshb import adhoc

find = adhoc("find").args("*.py")
grep = adhoc("grep").args("--quiet", "import")
done = adhoc("echo").args("done")

cmd = find.pipe(grep).and_(done)
cmd.root.to_shell_string()
# find '*.py' | grep --quiet import && echo done
```

| Goal | Method | Operator sugar |
| --- | --- | --- |
| pipe stdout | `.pipe(other)` | `\|` |
| pipe stdout and stderr | `.pipe_all(other)` | — |
| run `other` if `self` succeeds | `.and_(other)` | `&` |
| run `other` if `self` fails | `.or_(other)` | `^` |
| run `other` regardless | `.then(other)` | — |
| wrap in a subshell `( ... )` | `.subshell()` | — |
| wrap in a command group `{ ...; }` | `.group()` | — |

Pipelines stay flat: `a.pipe(b).pipe(c)` is one `Pipeline` with three commands
and two operators, not nested pipelines. `Subshell` makes precedence explicit:

```python
# (a && b) | c
cmd = adhoc("a").and_(adhoc("b")).subshell().pipe(adhoc("c"))
```

### Redirection

Redirection methods append to the rightmost command. Earlier redirects are not
replaced:

```python
cmd = (
    adhoc("grep")
    .args("-r", "TODO", ".")
    .redirect_err("/dev/null")
    .redirect_out("todos.txt")
)
cmd.root.to_shell_string()
# grep -r TODO . 2>/dev/null >todos.txt
```

| Goal | Method |
| --- | --- |
| stdout to file | `.redirect_out(path)` |
| append stdout | `.append_out(path)` |
| stderr to file | `.redirect_err(path)` |
| stdout and stderr to file | `.redirect_all(path)` |
| stdin from file | `.redirect_in(path)` |
| here-string | `.here_string(text)` |
| heredoc | `.heredoc(body, delimiter="EOF")` |
| fd duplication (e.g. `2>&1`) | `.redirect(source_fd, to_fd=1)` |

### Operators are sugar

`|`, `&` and `^` delegate to `.pipe()`, `.and_()` and `.or_()`; `>`, `<<` and
`<` delegate to `.redirect_out()`, `.append_out()` and `.redirect_in()`. The
named methods are the contract; operators are there when precedence is obvious.

In Python, `&` binds tighter than `|`; in a shell, `|` binds tighter than `&&`.
That is the opposite direction, so a chain mixing them must use the named
methods or explicit parentheses:

```python
# (find ... | grep ...) && echo done
cmd = (
    adhoc("find").args("*.py") | adhoc("grep").args("--quiet", "import")
) & adhoc("echo").args("done")
```

Note that `<<` maps to `.append_out()`, not to a heredoc; use `.heredoc()` for
`<<`.

## What runs checks today

| Illegal state | Result |
| --- | --- |
| `env` name bash cannot quote (`PATH; echo pwned;`) | `UnsupportedCompilationError` at construction |
| Pipeline operator count does not match its commands | `UnsupportedCompilationError` |
| `to_argv()` on anything but a plain command | `UnsupportedCompilationError` |
| `.set()` with a name not in the schema | `UnknownParameterError` |

All four subclass `PyshbError`. Broader semantic validation is available via
`validate()` (module-tier, `from pyshb.validator import validate`), which walks a
tree and raises a `ValidationError` on the first illegal state. Pipeline
constraints — dangling pipes, empty segments, operator/command mismatches — are
enforced today; conflicting redirect targets and empty subshells remain planned.

## Not ready yet

Typed `coreutils` classes (`ls`, `cat`, `grep` from parsed manpages) are Phase 3
work. Nothing in this README depends on them. The roadmap lives in the project
wiki.

Two pre-AST modules, `pyshb.base` and `pyshb.contrib.coreutils`, still exist as
the original reference for composition ergonomics. They are deprecated and
retained; the fluent methods above are the supported way to compose commands.

## More detail

The README covers the common path. Architecture, the AST node taxonomy,
decisions and the roadmap are in the project wiki at
`gitea.x.home.arpa/python/pyshb/wiki` — reach there when something here does not
answer your question.