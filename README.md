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
* A `Command` or `Pipeline` represents an immutable, lazy shell construct.
* Adding flags, positional arguments, or redirects returns a **new, cloned command instance**.
* Shell scripts and commands can be composed conditionally across branches without side effects.
* Evaluation to a quoted shell string (`str(cmd)`) or an argument vector (`list(cmd)`) is deferred until execution or compilation.
* High-level shell features (pipes, redirections, subshells, boolean operators) are composed with mathematical and ergonomic clarity.

### 1.2 Core Pillars
1. **Ergonomics & Conditional Building**: Effortless chaining, branching, and overriding without string concatenation bugs.
2. **Typesafe Coreutils**: Rich, autocompleted, fully-typed dataclasses for standard Linux utilities, generated via automated manpage parsing.
3. **Semantic & Syntax Validation**: Making illegal shell states impossible (e.g., double pipes, dangling redirects, invalid stream mappings, empty subshells).
4. **Lean & Readable**: Standard library only (`dataclasses`, `enum`, `typing`, `shlex`, `abc`, `pathlib`), zero external runtime dependencies, minimal abstractions.

---

## 2. Core Architecture & Mental Model

The library is organized into three decoupled layers:

```
┌─────────────────────────────────────────────────────────────┐
│                   1. Fluent Builder Layer                   │
│   (Django-style immutable API: .set(), .when(), .pipe())     │
└──────────────────────────────┬──────────────────────────────┘
                               │ builds / clones
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 2. Intermediate AST Layer                   │
│   (CommandNode, PipelineNode, LogicalNode, RedirectNode)    │
└──────────────┬──────────────────────────────┬───────────────┘
               │ validates                    │ compiles
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│    3a. Validation Engine     │ │   3b. Compiler Engine      │
│ (Pre-render syntax & semantic│ │ - Shell string (shlex)     │
│       rule verification)     │ │ - Execve argv list[str]    │
└──────────────────────────────┘ └────────────────────────────┘
```

### 2.1 The Intermediate Representation (AST)
Rather than appending raw strings to a flat list, `pyshb` represents commands as an immutable Abstract Syntax Tree (AST):

* **`Word`**: An atomic argument, either safely quoted or marked `Raw` (e.g., for environment variables `$VAR` or glob patterns `*.txt`).
* **`SimpleCommand`**: An executable name, flag mappings, and positional arguments.
* **`Redirect`**: Direction (`<`, `>`, `>>`, `&>`, `&>>`, `<<<`), file descriptor source (`1`, `2`), and target (file path or file descriptor `&1`).
* **`Pipeline`**: A sequential chain of commands linked by `|` or `|&`.
* **`CompoundCommand`**: Subshell `( ... )`, grouping `{ ...; }`, or control logic (`&&`, `||`, `;`).

---

## 3. Ergonomics & Conditional Command Building

### 3.1 Immutability & Cloning
Every transformation returns a new instance. Existing instances are never mutated:

```python
base_find = coreutils.find("/var/log").type("f")

# Branching does not alter base_find
error_logs = base_find.name("*.error.log")
all_logs = base_find.name("*.log")
```

### 3.2 Conditional Building Patterns

#### Pattern A: Imperative Branching (Django ORM Style)
```python
cmd = coreutils.grep("needle")

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
    coreutils.grep("needle")
    .when(case_insensitive, lambda c: c.set(ignore_case=True))
    .when(count_only, lambda c: c.set(count=True))
    .when(input_file is not None, lambda c: c.args(input_file))
)
```

#### Pattern C: Unsetting and Overriding Options
```python
# Unset a previously defined flag or reset positional arguments
cmd = coreutils.ls("-la").set(all=False)
```

### 3.3 Dual Output Modes (Shell String vs. Process Vector)
1. **Shell String (`str(cmd)`)**: Fully quoted and escaped for passing to `bash -c`, SSH, or script output.
2. **Process Argv (`cmd.to_argv()`)**: Returns `list[str]` for simple single commands to pass directly to `subprocess.Popen(args, shell=False)` without shell overhead or shell injection risks.
   *(Raises a validation error if called on pipelines or compound commands that require a shell parser).*

### 3.4 The Ad-Hoc Escape Hatch
The typed `contrib/` layer is a **convenience, not a gate**. The shell accepts any flag spelling for any program, so `pyshb` cannot enforce a closed flag set; its job is to make the dynamic path safe and comfortable.

For unmodelled programs or unknown flags, use the `adhoc()` builder:

```python
from pyshb.builder import adhoc

# Build a command with no known schema
cmd = adhoc("my-custom-tool").args("--unknown-flag", "value")
```

`.args(raw=True)` and `Word.raw_word` are the sanctioned dynamic path for passing raw shell expressions (like `$VAR` or globs) through the builder. Note that a raw word will be rejected by the upcoming `to_argv()` compiler (see issue #4), because raw shell expressions require a shell parser to evaluate and cannot be safely passed directly to `execve`.

---

## 4. Composition & Shell Operators

### 4.1 Python Operator Precedence vs. Shell Semantics

> **The Operator Precedence Warning**:
> In Python, bitwise AND (`&`) has higher precedence than bitwise OR (`|`).
> `a | b & c` is parsed in Python as `a | (b & c)`.
> However, in POSIX shell, pipes (`|`) bind tighter than logical AND (`&&`).
> `a | b && c` in shell means `(a | b) && c`.

To prevent subtle precedence bugs, `pyshb` supports two design principles:
1. **Fluent Methods as First-Class Interface**: `.pipe()`, `.and_()`, `.or_()`, `.then()` are the unambiguous, canonical way to compose.
2. **Explicit Operator Overloading**:
   * `|`: Standard pipe (`|`)
   * `&`: Logical AND (`&&`) (overloaded for command chaining, matching user intuition in shell builders)
   * `^`: Logical OR (`||`) (or `.or_()`)
   * `>`: Redirect output (`>`)
   * `>>`: Append output (`>>`)
   * `<`: Redirect input (`<`)
3. **Subshells for Grouping**: `sh.subshell(cmd1 & cmd2).pipe(cmd3)` cleanly renders `(cmd1 && cmd2) | cmd3`.

### 4.2 Supported Shell Constructs
* **Pipelines**: Standard stdout pipe (`|`), stdout+stderr pipe (`|&`).
* **Redirections**:
  * Truncate stdout: `cmd > file` or `cmd.redirect_out("file")`
  * Append stdout: `cmd >> file` or `cmd.append_out("file")`
  * Redirect stderr: `cmd.redirect_err("file")`
  * Redirect both: `cmd.redirect_all("file")`
  * Redirect fd to fd: `cmd.redirect(2, to_fd=1)` (renders `2>&1`)
  * Input from file: `cmd < file` or `cmd.redirect_in("file")`
  * Here-string: `cmd.here_string("hello")` (renders `cmd <<< 'hello'`)
  * Heredoc: `cmd.heredoc("data...", delimiter="EOF")`

---

## 5. Validation System (Preventing Illegal Shell States)

Validation occurs at two stages: **Construction Time** (fast type checks) and **AST Verification Time** (before string compilation or execution).

### 5.1 Rules & Constraints

| Illegal Shell State | Example of Invalid Usage | `pyshb` Solution / Exception |
| :--- | :--- | :--- |
| **Dangling Pipe** | `cmd.pipe()` without target | Signature requires `target: CommandLike`. |
| **Double Pipe** | `cmd1.pipe("").pipe(cmd2)` | `InvalidPipelineError`: Empty intermediate pipeline segment. |
| **Dangling Redirection** | `cmd > ""` or `cmd.redirect_out("")` | `RedirectionError`: Target cannot be empty or null. |
| **Conflicting Stdout Targets** | `cmd > "a.txt" > "b.txt"` | `RedirectionConflictError`: Cannot redirect stdout to multiple destinations without `tee`. |
| **Pipe After Stdout Redirection** | `(cmd > file).pipe(cmd2)` | `InvalidStreamWiringError`: stdout was redirected to file; piping stdout is contradictory. |
| **Invalid Subshell / Block** | `sh.subshell()` with no commands | `EmptyCompoundCommandError`: Subshells must contain at least one command. |
| **Argv Export on Compound Command** | `(cmd1 | cmd2).to_argv()` | `UnsupportedCompilationError`: Pipelines require shell interpretation. |
| **Non-POSIX Features in POSIX Mode**| `\|&` or `<<<` with `dialect="posix"` | `DialectCompatibilityError`: Feature requires Bash/Zsh dialect. |

### 5.2 Exception Hierarchy
```python
class PyshbError(Exception): """Base exception for all pyshb errors."""

class ValidationError(PyshbError): """Base exception for invalid shell semantics."""
class InvalidPipelineError(ValidationError): ...
class RedirectionError(ValidationError): ...
class RedirectionConflictError(RedirectionError): ...
class InvalidStreamWiringError(ValidationError): ...
class DialectCompatibilityError(ValidationError): ...
```

---

## 6. Manpages Parser & Typesafe Codegen

The second major milestone is covering Linux utilities (GNU coreutils, util-linux, findutils) with fully typesafe, autocompleted Python classes.

### 6.1 Codegen Pipeline Architecture
The codegen pipeline operates as follows:

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
* **Design Decision**: All coreutils are **pre-generated and committed** into `pyshb/contrib/coreutils.py` (and separate modules for other toolsets).
* **Rationale**: Static code enables instant IDE autocomplete, docstring hover cards, zero import overhead, and 100% compatibility with static type checkers (`ty`, `basedpyright`, `mypy`).

---

## 7. Recommended Repository Layout

```text
pyshb/
├── pyproject.toml
├── src/
│   └── pyshb/
│       ├── __init__.py           # Public exports (Command, Raw, sh, subshell)
│       ├── ast.py                # Node definitions (Word, SimpleCommand, Pipeline, Redirect)
│       ├── builder.py            # Fluent CommandBuilder & PipelineBuilder (Django-style API)
│       ├── compiler.py           # to_argv(node) — rendering is on the nodes: node.to_shell_string()
│       ├── validator.py          # AST validation rules and error checks
│       ├── exceptions.py         # Structured exception hierarchy
│       ├── py.typed
│       └── contrib/              # Generated high-level typesafe commands
│           ├── __init__.py
│           ├── coreutils.py      # ls, cp, mv, rm, cat, grep, find, etc.
│           └── posix.py          # POSIX builtins (cd, test, echo, etc.)
├── codegen/
│   ├── __init__.py
│   ├── schema.py             # CommandSchema, OptionSchema, ArgSchema
│   ├── parsers/
│   │   ├── help_parser.py    # Robust parser for `<cmd> --help`
│   │   └── man_parser.py     # Parser for roff/man pages
│   └── emitter.py            # Jinja2 / AST generator producing contrib/*.py
└── tests/
    ├── test_builder.py       # Immutability, cloning, .when(), .set()
    ├── test_compiler.py      # Quoting, escapes, dialects
    ├── test_validation.py    # Double pipe, dangling redirect, conflict checks
    ├── test_coreutils.py     # Typed commands validation
    └── test_codegen.py       # Manpage parsing regression tests
```

---

## 8. Implementation Roadmap

### Phase 1: Core AST & Immutable QuerySet Engine
- [ ] Implement AST nodes (`Word`, `SimpleCommand`, `Redirect`, `Pipeline`, `Subshell`).
- [ ] Implement `CommandBuilder` with immutable state transformations (`.set()`, `.args()`, `.when()`, `_clone()`).
- [ ] Implement compiler with robust `shlex` quoting and argv generation.
- [ ] Connect fluent methods (`.pipe()`, `.and_()`, `.or_()`, `.redirect_out()`).

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
