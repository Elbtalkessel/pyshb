"""Semantic validation for pyshb AST nodes.

The builder never emits an illegal tree, but the AST is constructible by hand,
so a hand-built node can carry a state that renders to a silently different
command. ``validate()`` walks a tree and raises on the first illegal state it
finds.

It is standalone: it is not wired into ``to_shell_string()`` (which stays pure
rendering) or ``to_argv()``.
"""

from pyshb.ast import (
    ASTNode,
    CommandGroup,
    Pipeline,
    Redirect,
    RedirectOp,
    SimpleCommand,
    Subshell,
)
from pyshb.exceptions import (
    ConflictingRedirectError,
    DanglingPipeError,
    DeadStdoutPipeError,
    EmptyPipelineError,
    PipelineOperatorMismatchError,
)

# Redirect operators that capture stdout into a file.
_STDOUT_CAPTURE_OPS = (
    RedirectOp.WRITE,
    RedirectOp.APPEND,
    RedirectOp.BOTH_WRITE,
    RedirectOp.BOTH_APPEND,
)


def validate(node: ASTNode, dialect: str = "bash") -> None:
    """Validate an AST node, raising on the first illegal state.

    Walks the tree in pre-order and applies the pipeline-constraint and
    stream-integrity rules. Nested pipelines are legal when non-empty and are
    validated recursively.

    Args:
        node: The root AST node to validate.
        dialect: Shell dialect. Accepted but not honoured: dialect validation
            is a later step.

    Returns:
        ``None`` when the tree is valid.

    Raises:
        ValidationError: If any node violates a semantic rule.
    """
    for current in node.walk():
        if isinstance(current, Pipeline):
            _validate_pipeline(current)
        _validate_redirects(current)


def _validate_pipeline(pipeline: Pipeline) -> None:
    """Apply the pipeline-constraint and dead-stdout rules to a pipeline.

    Args:
        pipeline: The pipeline to validate.

    Raises:
        DanglingPipeError: If the pipeline has fewer than two commands.
        EmptyPipelineError: If the pipeline contains an empty pipeline stage.
        PipelineOperatorMismatchError: If the operator count does not match the
            command count.
        DeadStdoutPipeError: If a stage before the last redirects its stdout
            away, so the downstream stage receives nothing.
    """
    commands = pipeline.commands
    if len(commands) < 2:
        raise DanglingPipeError(pipeline)
    if any(isinstance(command, Pipeline) and not command.commands for command in commands):
        raise EmptyPipelineError(pipeline)
    if len(pipeline.operators) != len(commands) - 1:
        raise PipelineOperatorMismatchError(pipeline)
    for stage in commands[:-1]:
        if _redirects_stdout_away(stage):
            raise DeadStdoutPipeError(pipeline)


def _validate_redirects(node: ASTNode) -> None:
    """Reject a node that captures stdout to a file more than once.

    Args:
        node: The node whose redirections to validate.

    Raises:
        ConflictingRedirectError: If the node has more than one redirect that
            captures stdout to a file.
    """
    captures = sum(
        1 for redir in _redirects_of(node) if _captures_stdout_to_file(redir)
    )
    if captures > 1:
        raise ConflictingRedirectError(node)


def _redirects_of(node: ASTNode) -> tuple[Redirect, ...]:
    """Return the redirections bound directly to a node, or an empty tuple."""
    if isinstance(node, (SimpleCommand, Subshell, CommandGroup)):
        return node.redirects
    return ()


def _redirects_stdout_away(node: ASTNode) -> bool:
    """Return whether the node sends stdout somewhere other than downstream.

    A file-capturing redirect to fd 1 does so directly; a ``DUP_OUT`` redirect
    whose source is fd 1 sends stdout onto another descriptor.
    """
    for redir in _redirects_of(node):
        if _captures_stdout_to_file(redir):
            return True
        if redir.op == RedirectOp.DUP_OUT and redir.source_fd in (None, 1):
            return True
    return False


def _captures_stdout_to_file(redir: Redirect) -> bool:
    """Return whether the redirect captures stdout into a file.

    Args:
        redir: The redirect to inspect.

    Returns:
        ``True`` when the redirect is a file-capturing operator targeting fd 1
        (the default ``source_fd`` or an explicit ``source_fd == 1``).
    """
    return redir.source_fd in (None, 1) and redir.op in _STDOUT_CAPTURE_OPS
