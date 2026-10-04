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

    Currently emits a single POSIX-compatible rendering. The `dialect` parameter
    is reserved for future use and does not yet alter output.

    Args:
        node: The AST node to compile.
        dialect: The target shell dialect (default: "bash").

    Returns:
        The compiled shell string.
    """
    if isinstance(node, Word):
        return _render_word(node)
    elif isinstance(node, Redirect):
        source = f"{node.source_fd}" if node.source_fd is not None else ""
        target = str(node.target) if isinstance(node.target, int) else _render_word(node.target)
        return f"{source}{node.op}{target}"
    elif isinstance(node, SimpleCommand):
        parts = []
        for name, val in node.env:
            parts.append(f"{name}={_render_word(val)}")
        parts.append(_render_word(node.executable))
        for arg in node.args:
            parts.append(_render_word(arg))
        for redir in node.redirects:
            parts.append(to_shell_string(redir, dialect))
        return " ".join(parts)
    elif isinstance(node, Pipeline):
        parts = []
        for i, cmd in enumerate(node.commands):
            parts.append(to_shell_string(cmd, dialect))
            if i < len(node.operators):
                parts.append(str(node.operators[i]))
        return " ".join(parts)
    elif isinstance(node, LogicalNode):
        left = to_shell_string(node.left, dialect)
        right = to_shell_string(node.right, dialect)
        return f"{left} {node.op} {right}"
    elif isinstance(node, Subshell):
        body = to_shell_string(node.body, dialect)
        parts = ["(", body]
        for redir in node.redirects:
            parts.append(to_shell_string(redir, dialect))
        parts.append(")")
        return " ".join(parts)
    elif isinstance(node, CommandGroup):
        body = to_shell_string(node.body, dialect)
        parts = ["{", f"{body};"]
        for redir in node.redirects:
            parts.append(to_shell_string(redir, dialect))
        parts.append("}")
        return " ".join(parts)
    else:
        raise UnsupportedCompilationError(f"Unsupported node type: {type(node).__name__}")


def to_argv(node: ASTNode) -> list[str]:
    """Compile an AST node to an argv list.

    Only SimpleCommand nodes without environment variables, redirections, or raw words
    can be compiled to argv. Any other node type or a SimpleCommand with these features
    will raise an UnsupportedCompilationError, because they require a shell to evaluate.

    Note: CommandBuilder._flag_words() marks flag words as raw=True, so a builder with
    any parameter set produces raw words and cannot be passed to to_argv.

    Args:
        node: The AST node to compile.

    Returns:
        A list of strings representing the argv array.

    Raises:
        UnsupportedCompilationError: If the node cannot be represented as argv.
    """
    if not isinstance(node, SimpleCommand):
        raise UnsupportedCompilationError(f"Cannot compile {type(node).__name__} to argv")

    if node.env:
        raise UnsupportedCompilationError("Cannot compile command with environment variables to argv")
    if node.redirects:
        raise UnsupportedCompilationError("Cannot compile command with redirections to argv")

    argv = []
    if node.executable.raw:
        raise UnsupportedCompilationError("Cannot compile raw word to argv")
    argv.append(node.executable.value)

    for arg in node.args:
        if arg.raw:
            raise UnsupportedCompilationError("Cannot compile raw word to argv")
        argv.append(arg.value)

    return argv


__all__ = [
    "to_argv",
    "to_shell_string",
]
