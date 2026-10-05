"""Compiler layer for pyshb AST nodes.

This module provides functions to compile an immutable AST tree into either a shell
string or an argv list. Quoting is the security boundary: words that are not marked
raw are safely quoted so the shell can never reinterpret them.

Shell rendering lives on the nodes themselves (``ASTNode.to_shell_string``); this
module is the published entry point over it, plus the argv export, which is not a
rendering concern and stays here.
"""

from pyshb.ast import ASTNode, SimpleCommand
from pyshb.exceptions import UnsupportedCompilationError


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
        UnsupportedCompilationError: If the node cannot be rendered faithfully.
            Currently raised by ``Pipeline`` when its operator count does not
            match its command count, which would otherwise compile to a
            silently different command.
    """
    return node.to_shell_string(dialect)


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