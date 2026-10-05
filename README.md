# pyshb: Python Shell Command Builder

A lean, zero-dependency, typesafe Python library to construct, compose, and validate shell commands.

Inspired by **Django's ORM QuerySet**, `pyshb` enables lazy, immutable, and conditional command construction without string concatenation hazards, paired with automated code generation for Linux core utilities and compile-time/run-time shell validation.

---

## 1. Executive Summary & Design Vision

### 1.1 The Django ORM Metaphor
In Django ORM:
* A `QuerySet` represents a lazy database query.
* Calling `.filter()` or `.exclude()` does not mutate the existing query; it returns a **new, cloned `QuerySet`**.
* Queries can be built conditionally using standard Python control flow (`if condition: qs = qs.filter(...)`).
* Evaluation is deferred until the result is explicitly needed (`list(qs)`, `str(qs)`).
* Complex conditions are composed using expressions (`Q` objects, `F` expressions).

In `pyshb`:
* A `CommandBuilder` wrapping a `SimpleCommand`, or a `Pipeline` node, is an immutable shell construct.
* Adding flags or positional arguments returns a **new, cloned instance**.
* Commands can be built conditionally across branches without side effects.
* Evaluation is deferred until the result is explicitly needed: `node.to_shell_string()` for a quoted shell string, `to_argv(node)` for an argument vector.
* High-level shell features (pipes, redirections, subshells, boolean operators) are composed with mathematical and ergonomic clarity.

### 1.2 Core Pillars
1. **Ergonomics & Conditional Building**: Effortless chaining, branching, and overriding without string concatenation bugs.
2. **Typesafe Coreutils**: Rich, autocompleted, fully-typed dataclasses for standard Linux utilities, generated via automated manpage parsing (Phase 3).
3. **Semantic & Syntax Validation**: Rejecting illegal shell states (e.g., double pipes, dangling redirects, invalid stream mappings, empty subshells) before render (Phase 2).
4. **Lean & Readable**: Standard library only (`dataclasses`, `enum`, `shlex`, `abc`, `collections.abc`), zero external runtime dependencies, minimal abstractions.

---

## 2. Core Architecture & Mental Model

The library is organized into three decoupled layers:

```
┌─────────────────────────────────────────────────────────────┐
│                   1. Fluent Builder Layer                   │
│         (Django-style immutable API: .set(), .args(),        │
│                          .when(), adhoc())                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ builds / clones
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 2. Intermediate AST Layer                   │
│  (Word, SimpleCommand, Redirect, Pipeline, LogicalNode,     │
│                    Subshell, CommandGroup)                   │
└──────────────┬──────────────────────────────┬───────────────┘
               │ validates                    │ argv export
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│    3a. Validation Engine     │ │   3b. Compiler Engine      │
│ (Pre-render syntax & semantic│ │ - Shell string, on the node │
│       rule verification)     │ │   via to_shell_string()     │
│   (planned — see roadmap)    │ │ - Execve argv list[str]    │
│                              │ │   via to_argv(node)         │
└──────────────────────────────┘ └────────────────────────────┘
```

Shell rendering belongs to the AST nodes: every node implements `to_shell_string(dialect)` and renders only itself, delegating to its children. The builder never emits strings, and the compiler never re-parses them.

### 2.1 The Intermediate Representation (AST)
Rather than appending raw strings to a flat list, `pyshb` represents commands as an immutable Abstract Syntax Tree (AST):

* **`Word`**: An atomic argument, either safely quoted or marked `raw` (e.g., for environment variables `$VAR` or glob patterns `*.txt`).
* **`SimpleCommand`**: An executable word, positional arguments, redirections, and `NAME=value` prefixes.
* **`Redirect`**: Operator (`<`, `>`, `>>`, `&>`, `&>>`, `<<<`, `<<`, `<<-`, `<&`, `>&`), file descriptor source (`1`, `2`), and target (a `Word` for a path or string, an `int` for an fd duplicate such as `2>&1`).
* **`Pipeline`**: A sequential chain of commands linked by `|` or `|&`.
* **`LogicalNode`**: Boolean or sequential control flow between two commands: `&&`, `||`, `;`.
* **`Subshell`**: An isolated subshell, `( ... )`.
* **`CommandGroup`**: A group in the current shell context, `{ ...; }`.

---

## 3. Ergonomics & Conditional Command Building

### 3.1 Immutability & Cloning
Every transformation returns a new instance. Existing instances are never mutated:

```python
from pyshb.ast import SimpleCommand, Word
from pyshb.builder import CommandBuilder, ParamSpec

FIND = {
    "type": ParamSpec("-type", arg_join=" "),
    "name": ParamSpec("-name", arg_join=" "),
}

base_find = CommandBuilder(
    SimpleCommand(executable=Word.literal("find")),
    schema=FIND,
).args("/var/log").set(type="f")

# Branching does not alter base_find
error_logs = base_find.set(name="*.error.log")
all_logs = base_find.set(name="*.log")
```

`ParamSpec.arg_join` decides how a value is attached to its flag: `"="`
produces one word (`--regexp=foo`), `" "` produces two (`-type f`).

### 3.2 Conditional Building Patterns

#### Pattern A: Imperative Branching (Django ORM Style)
```python
GREP = {
    "ignore_case": ParamSpec("--ignore-case"),
    "count": ParamSpec("--count"),
    "max_count": ParamSpec("--max-count"),
}
grep_builder = CommandBuilder(
    SimpleCommand(executable=Word.literal("grep")),
    schema=GREP,
)

cmd = grep_builder.args("needle")

if case_insensitive:
    cmd = cmd.set(ignore_case=True)

if count_only:
    cmd = cmd.set(count=True)
elif max_count is not None:
    cmd = cmd.set(max_count=max_count)

if input_file:
    cmd = cmd.args(input_file)
```

#### Pattern B: Declarative `.when()` Helper
To maintain fluent method chains without breaking out into `if` statements:

```python
cmd = (
    grep_builder.args("needle")
    .when(case_insensitive, lambda c: c.set(ignore_case=True))
    .when(count_only, lambda c: c.set(count=True))
    .when(input_file is not None, lambda c: c.args(input_file))
)
```

#### Pattern C: Unsetting and Overriding Options
```python
# False removes a previously set boolean flag; str or int overrides its value
cmd = grep_builder.set(count=False)
```

### 3.3 Dual Output Modes (Shell String vs. Process Vector)
The builder holds the node under `.root`. Both output modes start from it.

1. **Shell String (`cmd.root.to_shell_string()`)**: Every word with `raw=False` is `shlex.quote`d, so the shell cannot reinterpret it. The `dialect` argument is accepted but not honoured: every dialect renders identically, and that rendering can emit bash-only constructs such as `|&` and `<<<`, so it is not strictly POSIX.
2. **Process Argv (`to_argv(cmd.root)`)**: Returns `list[str]` for a `SimpleCommand` with no env prefixes, no redirections, and no raw words. Pass it to `subprocess.Popen(argv, shell=False)` to skip the shell. Anything else raises `UnsupportedCompilationError`, because a faithful argv list would need a shell to evaluate.

### 3.4 The Ad-Hoc Escape Hatch
A schema-backed builder is a **convenience, not a gate**. The shell accepts any flag spelling for any program, so `pyshb` cannot enforce a closed flag set; its job is to make the dynamic path safe and comfortable.

For unmodelled programs or unknown flags, use the `adhoc()` builder, which starts with an empty schema:

```python
from pyshb import Word, adhoc

# Build a command with no known schema
cmd = adhoc("my-custom-tool").args("--unknown-flag", "value")

# Rawness is the escape hatch, and needs no second import
cmd = adhoc(Word.raw_word("$PROG"))
```

`.args(raw=True)` and `Word.raw_word` are the sanctioned dynamic path for passing raw shell expressions (like `$VAR` or globs) through the builder. `to_argv()` rejects a raw word with `UnsupportedCompilationError`, because a raw shell expression requires a shell to evaluate and cannot be safely passed to `execve`.

---

## 4. Composition & Shell Operators

### 4.1 Python Operator Precedence vs. Shell Semantics

> **The Operator Precedence Warning**:
> In Python, bitwise AND (`&`) has higher precedence than bitwise OR (`|`).
> `a | b & c` is parsed in Python as `a | (b & c)`.
> However, in POSIX shell, pipes (`|`) bind tighter than logical AND (`&&`).
> `a | b && c` in shell means `(a | b) && c`.

The fluent surface that will expose composition to callers is `.pipe()`, `.pipe_all()`, `.and_()`, `.or_()`, `.then()`, `.subshell()`, and `.group()`, each returning a new builder. Operator overloading is sugar over those methods, never the only way to express something: `|` for `|`, `&` for `&&`, `^` for `||`, `>` for redirect output, `>>` for append, `<` for redirect input.

That surface is planned work (Phase 1, step 5). Today composition happens at the AST layer, where each construct is a node:

```python
from pyshb.ast import (
    LogicalNode,
    LogicalOp,
    PipeOp,
    Pipeline,
    SimpleCommand,
    Subshell,
    Word,
)

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

Wrapping that logical node in a `Subshell` renders it parenthesised, so a following pipeline applies to the whole group: `(a && b) | c`. A subshell's own redirections render after the closing paren, because inside they would bind to the last command of the body instead of the whole subshell.

### 4.2 Shell Constructs Representable Today
Every construct below is a node in `ast.py`; see §8 for the fluent methods that will build them.

* **Pipelines**: `Pipeline` with `PipeOp.STDOUT` (`|`) or `PipeOp.ALL` (`|&`). `Pipeline.to_shell_string()` raises `UnsupportedCompilationError` when `len(operators) != len(commands) - 1`, rather than silently compiling to a different command.
* **Boolean and sequential flow**: `LogicalNode` with `LogicalOp.AND` (`&&`), `LogicalOp.OR` (`||`), or `LogicalOp.SEQUENCE` (`;`).
* **Grouping**: `Subshell` for `( ... )`, `CommandGroup` for `{ ...; }`.
* **Redirections**: `Redirect` with an operator from `RedirectOp`:
  * `READ` (`<`) — input from a file
  * `WRITE` (`>`) — truncate stdout, or stderr when `source_fd=2`
  * `APPEND` (`>>`) — append stdout
  * `BOTH_WRITE` (`&>`) and `BOTH_APPEND` (`&>>`)
  * `HERE_STRING` (`<<<`) and `HEREDOC` (`<<`) / `HEREDOC_STRIP` (`<<-`)
  * `DUP_IN` (`<&`) and `DUP_OUT` (`>&`) — an `int` target renders `2>&1`

---

## 5. Validation

Two layers reject illegal states. **Construction-time checks** live in the nodes
themselves, so an uncompilable node cannot be built. **Render-time checks** run
when a node is compiled. The general validation pass (`validator.py`) is Phase 2
work; see §8.

### 5.1 Checks That Run Today

| Illegal Shell State | Where | Result |
| :--- | :--- | :--- |
| **`env` name that bash cannot quote** (`"PATH; echo pwned;"`) | `SimpleCommand.__post_init__` | `UnsupportedCompilationError` at construction. Such a name has no correct rendering, so the node must not exist. |
| **Pipeline operator count mismatch** (`3` commands, `1` operator) | `Pipeline.to_shell_string()` | `UnsupportedCompilationError`. The alternative is a silently different command. |
| **Argv export of anything but a plain command** — a pipeline, an `env` prefix, a redirect, or a raw word | `to_argv()` | `UnsupportedCompilationError`. A faithful argv list would need a shell. |
| **Unknown parameter name in `.set()`** | `CommandBuilder.set()` | `UnknownParameterError`, carrying the name and the schema's names. Every name is checked before anything is applied, so one bad name never half-applies. |

### 5.2 Exception Hierarchy

```python
class PyshbError(Exception): ...
class CompilationError(PyshbError): ...
class UnsupportedCompilationError(CompilationError): ...
class UnknownParameterError(PyshbError): ...
```

### 5.3 Planned Checks

The semantic rules below have no implementation yet. Each is illegal shell state
that string concatenation cannot catch, which is why the AST exists. They are
the substance of Phase 2.

| Illegal Shell State | Example |
| :--- | :--- |
| **Dangling pipe** | `.pipe()` with no target |
| **Double pipe** | empty intermediate pipeline segment |
| **Dangling redirection** | `cmd > ""` |
| **Conflicting stdout targets** | `cmd > a.txt > b.txt` |
| **Pipe after stdout redirection** | piping a stdout that is already redirected to a file |
| **Empty subshell** | a subshell with no body |
| **Non-POSIX features under `dialect="posix"`** | `\|&` or `<<<` |

---

## 6. Manpages Parser & Typesafe Codegen (Planned)

Phase 3 covers Linux utilities (GNU coreutils, util-linux, findutils) with fully
typesafe, autocompleted Python classes. None of the pipeline below exists yet;
`codegen/spiderman.py` is a manpage scraper that predates it.

### 6.1 Codegen Pipeline Architecture
The codegen pipeline will operate as follows:

```
┌─────────────────────────────────┐
│     1. Raw Input Sources        │
│ - man -P cat <cmd> (groff/roff) │
│ - <cmd> --help                  │
│ - doclifter / mandoc -T json    │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│    2. Parser & Normalizer       │
│ - Flags: short (-l), long (--all)│
│ - Value types: bool, str, int,  │
│   path, choice/enum, repeated   │
│ - Positional argument arity     │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     3. CommandSchema (IR)       │
│ Normalized intermediate schema  │
└────────────────┬────────────────┘
                 │
                 ▼
┌─────────────────────────────────┐
│     4. Python Code Generator    │
│ - Emits typed dataclasses       │
│ - Docstrings & typing overloads │
│ - Python keyword sanitation     │
└─────────────────────────────────┘
```

### 6.2 Key Challenges & Solutions

#### Challenge 1: Python Keyword Collisions
Shell flags frequently collide with Python reserved keywords (`--in`, `--from`, `--type`, `--id`, `--format`, `--exec`).
* **Solution**: Normalize field names by appending an underscore: `in_`, `from_`, `type_`, `exec_`. The `ParamMeta` retains the exact shell flag string (`flag="--type"`).

#### Challenge 2: Flag Value Arity & Typing
* Flags with no arguments: `bool = False` (`flag="--ignore-case"`).
* Flags with required arguments: `str | None = None` or `int | None = None`.
* Flags that can be repeated: `Sequence[str] = ()` (e.g. `--regexp pattern1 --regexp pattern2`).
* Combined short flags: Support expanded long names or explicit short flags.

#### Challenge 3: Flag Joining Styles
Different utilities use different flag styles:
* GNU style: `--option=value` or `--option value` (`arg_join="="` or `arg_join=" "`).
* Single dash options: `find -name "*.py"` (`arg_join=" "`, `flag="-name"`).
* Short flags with adjacent args: `-I<path>`.
* **Solution**: `ProgramMeta` and `ParamMeta` specify `arg_join` per command and per parameter.

#### Challenge 4: Static Generation vs. Dynamic Metaclasses
* **Design Decision**: generated coreutils will be **pre-generated and committed** into `pyshb/contrib/coreutils.py` (and separate modules for other toolsets), not built at import time.
* **Rationale**: Static code enables instant IDE autocomplete, docstring hover cards, zero import overhead, and 100% compatibility with static type checkers (`ty`, `basedpyright`, `mypy`).

---

## 7. Recommended Repository Layout

```text
pyshb/
├── pyproject.toml
├── src/
│   └── pyshb/
│       ├── __init__.py           # Convenience facade: only what starts a command.
│                                 # Everything else is module-tier — each module's
│                                 # own __all__ is the real surface, and pyshb.base
│                                 # is never re-exported here.
│       ├── ast.py                # Node definitions (Word, SimpleCommand, Redirect,
│       │                         #   Pipeline, LogicalNode, Subshell, CommandGroup)
│       ├── base.py               # Legacy pre-AST implementation (Compose, ShellCommand)
│       ├── builder.py            # CommandBuilder, ParamSpec, adhoc() (Django-style API)
│       ├── compiler.py           # to_argv(node); rendering is on the nodes
│       ├── exceptions.py         # PyshbError, CompilationError,
│       │                         #   UnsupportedCompilationError, UnknownParameterError
│       ├── py.typed
│       └── contrib/
│           ├── __init__.py
│           └── coreutils.py      # cd, grep, find. Legacy, pre-AST; rework is Phase 3–4
├── codegen/
│   ├── __init__.py
│   └── spiderman.py          # Manpage scraper; becomes the structured parser in Phase 3
└── tests/
    ├── test_ast.py           # Node immutability, walk(), rendering
    ├── test_builder.py       # Immutability, cloning, .when(), .set(), .args()
    ├── test_compiler.py      # Quoting, argv export, rejection cases
    ├── test_readme_examples.py
    └── test_shell_features.py
```

---

## 8. Implementation Roadmap

### Phase 1: Core AST & Immutable QuerySet Engine
- [x] Implement AST nodes (`Word`, `Redirect`, `SimpleCommand`, `Pipeline`, `LogicalNode`, `Subshell`, `CommandGroup`).
- [x] Implement `CommandBuilder` with immutable state transformations (`.set()`, `.args()`, `.when()`, `_clone()`).
- [x] Add `adhoc()` for programs outside the `contrib/` schema.
- [x] Implement compiler with robust `shlex` quoting and argv generation.
- [ ] Connect fluent methods (`.pipe()`, `.pipe_all()`, `.and_()`, `.or_()`, `.then()`, `.subshell()`, `.group()`, `.redirect_out()` and the rest of the redirection family).
- [ ] Populate `src/pyshb/__init__.py` with a convenience facade.

### Phase 2: AST Validation Engine
- [ ] Enforce pipeline constraints (no empty segments, no double piping).
- [ ] Enforce stream integrity (no contradictory stdout targets, no piping dead stdout streams).
- [ ] Implement dialect checkers (POSIX vs Bash features like `|&` and `<<<`).
- [ ] Comprehensive validation test suite with descriptive error messages.

### Phase 3: Codegen & Manpage Parser
- [ ] Build normalized `CommandSchema` data structures.
- [ ] Upgrade `codegen/spiderman.py` into a structured parser extracting flags, parameter types, arity, and docstrings.
- [ ] Build Python code emitter formatting clean dataclasses with complete type annotations.

### Phase 4: Full Coreutils Coverage & Documentation
- [ ] Generate and verify GNU Core Utilities (`ls`, `cat`, `grep`, `mkdir`, `cp`, `mv`, `rm`, `chmod`, `sort`, `uniq`, `wc`, etc.).
- [ ] Add integration tests verifying generated commands against actual shell execution.
- [ ] Document public API recipes and Django ORM migration patterns.
