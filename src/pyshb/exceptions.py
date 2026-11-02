from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyshb.ast import ASTNode, Pipeline


class PyshbError(Exception):
    """Base exception for all pyshb errors."""


class CompilationError(PyshbError):
    """Base exception for compilation errors."""


class UnsupportedCompilationError(CompilationError):
    """Raised when an AST node cannot be compiled to the requested target."""


class ValidationError(CompilationError):
    """Raised when an AST node violates a semantic rule.

    Attributes:
        node: The AST node that violates the rule.
        rule: The short name of the violated rule.
    """

    node: ASTNode
    rule: str

    def __init__(self, node: ASTNode, rule: str, detail: str) -> None:
        self.node = node
        self.rule = rule
        super().__init__(f"{rule}: {detail}")


class DanglingPipeError(ValidationError):
    """Raised when a pipeline has fewer than two commands."""

    def __init__(self, node: Pipeline) -> None:
        super().__init__(
            node,
            "dangling pipe",
            f"a pipeline needs at least two commands, got {len(node.commands)}",
        )


class EmptyPipelineError(ValidationError):
    """Raised when a pipeline contains an empty pipeline stage."""

    def __init__(self, node: Pipeline) -> None:
        super().__init__(
            node,
            "empty pipeline segment",
            "a pipeline cannot contain an empty stage between two pipes",
        )


class PipelineOperatorMismatchError(ValidationError):
    """Raised when a pipeline's operators do not match its commands."""

    def __init__(self, node: Pipeline) -> None:
        super().__init__(
            node,
            "pipeline operator mismatch",
            (
                f"pipeline has {len(node.commands)} commands but "
                f"{len(node.operators)} operators; "
                f"expected {len(node.commands) - 1}"
            ),
        )


class ConflictingRedirectError(ValidationError):
    """Raised when a node captures stdout to a file more than once."""

    def __init__(self, node: ASTNode) -> None:
        super().__init__(
            node,
            "conflicting redirect",
            "more than one redirect captures stdout to a file",
        )


class DeadStdoutPipeError(ValidationError):
    """Raised when a non-final pipeline stage redirects its stdout away."""

    def __init__(self, node: Pipeline) -> None:
        super().__init__(
            node,
            "dead stdout pipe",
            "a pipeline stage before the last redirects its stdout away",
        )


class UnknownParameterError(PyshbError):
    """Raised when a parameter name is absent from the builder's schema."""

    param: str
    known: tuple[str, ...]

    def __init__(self, param: str, known: tuple[str, ...]) -> None:
        self.param = param
        self.known = known
        known_text = ", ".join(known) if known else "(none)"
        super().__init__(f"Unknown parameter {param!r}. Known parameters: {known_text}")
