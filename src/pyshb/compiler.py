"""Compiler layer for pyshb AST nodes.

This module provides functions to compile an immutable AST tree into either a shell
string or an argv list. Quoting is the security boundary: words that are not marked
raw are safely quoted so the shell can never reinterpret them.
"""

import shlex

from pyshb.ast import (
    ASTNode,
    CommandGroup,
    LogicalNode,
    Pipeline,
    Redirect,
    SimpleCommand,
    Subshell,
    Word,
)
from pyshb.exceptions import UnsupportedCompilationError


def _render_word(word: Word) -> str:
    if word.raw:
        return word.value
    return shlex.quote(word.value)


def to_shell_string(node: ASTNode, dialect: str = "bash") -> str:
    """Compile an AST node to a shell string.

    Phase 1 emits a single POSIX-compatible rendering. ``dialect`` is part of
    the published signature but does not yet alter output; it is reserved for
    a later phase rather than validated here.

    Args:
        node: The AST node to compile.
        dialect: The intended shell dialect.

    Returns:
        The compiled shell string.

    Raises:
        UnsupportedCompilationError: If a ``Pipeline`` carries a number of
            operators that does not match its commands, which would otherwise
            compile to a silently different command.
    """
    if isinstance(node, Word):
        return _render_word(node)
    if isinstance(node, Redirect):
        source = f"{node.source_fd}" if node.source_fd is not None else ""
        if isinstance(node.target, int):
            target = str(node.target)
        else:
            target = _render_word(node.target)
        return f"{source}{node.op}{target}"
    if isinstance(node, SimpleCommand):
        parts = []
        for name, val in node.env:
            parts.append(f"{name}={_render_word(val)}")
        parts.append(_render_word(node.executable))
        for arg in node.args:
            parts.append(_render_word(arg))
        for redir in node.redirects:
            parts.append(to_shell_string(redir, dialect))
        return " ".join(parts)
    if isinstance(node, Pipeline):
        if len(node.operators) != len(node.commands) - 1:
            raise UnsupportedCompilationError(
                f"Pipeline has {len(node.commands)} commands but "
                f"{len(node.operators)} operators; expected "
                f"{len(node.commands) - 1}"
            )
        parts = []
        for index, cmd in enumerate(node.commands):
            parts.append(to_shell_string(cmd, dialect))
            if index < len(node.operators):
                parts.append(str(node.operators[index]))
        return " ".join(parts)
    if isinstance(node, LogicalNode):
        left = to_shell_string(node.left, dialect)
        right = to_shell_string(node.right, dialect)
        return f"{left} {node.op} {right}"
    if isinstance(node, Subshell):
        body = to_shell_string(node.body, dialect)
        parts = ["(", body]
        for redir in node.redirects:
            parts.append(to_shell_string(redir, dialect))
        parts.append(")")
        return " ".join(parts)
    if isinstance(node, CommandGroup):
        body = to_shell_string(node.body, dialect)
        parts = ["{", f"{body};"]
        for redir in node.redirects:
            parts.append(to_shell_string(redir, dialect))
        parts.append("}")
        return " ".join(parts)
    raise UnsupportedCompilationError(
        f"Unsupported node type: {type(node).__name__}"
    )


def to_argv(node: ASTNode) -> list[str]:
    """Compile an AST node to an argv list.

    Only ``SimpleCommand`` nodes without environment variables, redirections
    or raw words can be compiled to argv. Anything else raises, because a
    faithful argv list would require a shell to evaluate.

    Args:
        node: The AST node to compile.

    Returns:
        The executable followed by its arguments, as plain strings.

    Raises:
        UnsupportedCompilationError: If the node cannot be represented as an
            argv list without a shell. That includes every compound node, and
            any ``env`` or redirect, which argv cannot carry.

    Note:
        ``CommandBuilder`` flags are marked ``raw=True`` so that a multi-token
        flag such as ``-or -name`` is not folded into one quoted argument.
        Raw words have no meaning in argv, so a builder with any parameter set
        raises here; argv callers should pass positionals via ``.args()``.
    """
    if not isinstance(node, SimpleCommand):
        raise UnsupportedCompilationError(
            f"Cannot compile {type(node).__name__} to argv"
        )
    if node.env:
        raise UnsupportedCompilationError(
            "Cannot compile a command with env assignments to argv"
        )
    if node.redirects:
        raise UnsupportedCompilationError(
            "Cannot compile a command with redirections to argv"
        )
    if node.executable.raw:
        raise UnsupportedCompilationError("Cannot compile a raw word to argv")

    argv = [node.executable.value]
    for arg in node.args:
        if arg.raw:
            raise UnsupportedCompilationError("Cannot compile a raw word to argv")
        argv.append(arg.value)
    return argv


__all__ = [
    "to_argv",
    "to_shell_string",
]
