"""Argv export for pyshb AST nodes.

Most nodes cannot produce an argv list, because they need a shell to evaluate.
This module exports the one that can: ``to_argv()`` takes a node and returns
plain strings for ``subprocess`` with ``shell=False``.
"""

from pyshb.ast import ASTNode, SimpleCommand
from pyshb.exceptions import UnsupportedCompilationError


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
        ``CommandBuilder._flag_words()`` emits bare boolean flags and the flag
        half of a space-joined pair as ``raw=True``, because a multi-token flag
        such as ``-or -name`` would otherwise be folded into one quoted
        argument. Raw words have no meaning in argv, so such a builder raises
        here. A value joined with ``=`` is one literal ``--flag=value`` word and
        survives; positionals added with ``.args()`` are literal too.
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