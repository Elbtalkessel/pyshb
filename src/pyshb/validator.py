"""Semantic validation for pyshb AST nodes.

The builder never emits an illegal tree, but the AST is constructible by hand,
so a hand-built node can carry a state that renders to a silently different
command. ``validate()`` walks a tree and raises on the first illegal state it
finds.

It is standalone: it is not wired into ``to_shell_string()`` (which stays pure
rendering) or ``to_argv()``.
"""

from pyshb.ast import ASTNode, Pipeline
from pyshb.exceptions import (
    DanglingPipeError,
    EmptyPipelineError,
    PipelineOperatorMismatchError,
)


def validate(node: ASTNode, dialect: str = "bash") -> None:
    """Validate an AST node, raising on the first illegal state.

    Walks the tree in pre-order and applies the pipeline-constraint rules.
    Nested pipelines are legal when non-empty and are validated recursively.

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


def _validate_pipeline(pipeline: Pipeline) -> None:
    """Apply the pipeline-constraint rules to a single pipeline.

    Args:
        pipeline: The pipeline to validate.

    Raises:
        DanglingPipeError: If the pipeline has fewer than two commands.
        EmptyPipelineError: If the pipeline contains an empty pipeline stage.
        PipelineOperatorMismatchError: If the operator count does not match the
            command count.
    """
    commands = pipeline.commands
    if len(commands) < 2:
        raise DanglingPipeError(pipeline)
    if any(isinstance(command, Pipeline) and not command.commands for command in commands):
        raise EmptyPipelineError(pipeline)
    if len(pipeline.operators) != len(commands) - 1:
        raise PipelineOperatorMismatchError(pipeline)
