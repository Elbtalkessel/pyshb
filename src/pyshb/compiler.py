"""Compiler layer for pyshb AST nodes.

Shell rendering is **not** here. Every node renders itself through
``ASTNode.to_shell_string(dialect)``, so a command is rendered by calling that
method on the node you already hold — there is no wrapper to route through.
Quoting remains the security boundary: a ``Word`` with ``raw=False`` is
``shlex.quote``d, so the shell can never reinterpret it.

What stays here is the argv export. It is not a rendering concern — most nodes
cannot produce an argv list at all, since they need a shell to evaluate — so it
lives with the one node type that can, rather than on ``ASTNode``.
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
]