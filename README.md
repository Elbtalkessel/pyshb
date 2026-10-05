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

Pipe and boolean operators are not built yet; the fluent methods `.pipe()`,
`.and_()` and `.or_()` are on the roadmap. Today you compose at the node level:

```python
from pyshb.ast import LogicalNode, LogicalOp, Pipeline, PipeOp, SimpleCommand, Word

find = SimpleCommand(executable=Word.literal("find"), args=(Word.literal("*.py"),))
grep = SimpleCommand(
    executable=Word.literal("grep"),
    args=(Word.literal("--quiet"), Word.literal("import")),
)

# find '*.py' |& grep --quiet import && echo done
LogicalNode(
    left=Pipeline(commands=(find, grep), operators=(PipeOp.ALL,)),
    op=LogicalOp.AND,
    right=SimpleCommand(executable=Word.literal("echo"), args=(Word.literal("done"),)),
).to_shell_string()
```

Mind the precedence difference: in Python `&` binds tighter than `|`, in a shell
`&&` binds tighter than `|`. `a | b & c` is not the same command either way.

## What runs checks today

| Illegal state | Result |
| --- | --- |
| `env` name bash cannot quote (`PATH; echo pwned;`) | `UnsupportedCompilationError` at construction |
| Pipeline operator count does not match its commands | `UnsupportedCompilationError` |
| `to_argv()` on anything but a plain command | `UnsupportedCompilationError` |
| `.set()` with a name not in the schema | `UnknownParameterError` |

All four subclass `PyshbError`. Broader semantic validation — dangling pipes,
conflicting redirect targets, empty subshells — is planned and not implemented.

## Not ready yet

Typed `coreutils` classes (`ls`, `cat`, `grep` from parsed manpages) are Phase 3
work. Nothing in this README depends on them. The roadmap lives in the project
wiki.

Two pre-AST modules exist as a reference for the composition ergonomics we want
(operators where Python has them, named methods where it does not):
`pyshb.base` and `pyshb.contrib.coreutils`. They are deprecated; the AST layer
will grow fluent methods to match them (milestone 1 step 5).

## More detail

The README covers the common path. Architecture, the AST node taxonomy,
decisions and the roadmap are in the project wiki at
`gitea.x.home.arpa/python/pyshb/wiki` — reach there when something here does not
answer your question.