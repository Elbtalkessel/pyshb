class PyshbError(Exception):
    """Base exception for all pyshb errors."""


class UnknownParameterError(PyshbError):
    """Raised when a parameter name is absent from the builder's schema."""

    param: str
    known: tuple[str, ...]

    def __init__(self, param: str, known: tuple[str, ...]) -> None:
        self.param = param
        self.known = known
        known_text = ", ".join(known) if known else "(none)"
        super().__init__(f"Unknown parameter {param!r}. Known parameters: {known_text}")


__all__ = [
    "PyshbError",
    "UnknownParameterError",
]
