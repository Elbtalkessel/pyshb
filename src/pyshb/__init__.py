"""The stable, public API of pyshb.

The names in ``__all__`` are the whole of pyshb's public API. Everything else —
the submodules included — is internal, undocumented, and may change or be
removed in any release without it counting as a breaking change.

If a name is not listed here, it is not part of the contract. Please open an
issue before depending on one.
"""

from pyshb.ast import SimpleCommand, Word
from pyshb.builder import CommandBuilder, ParamSpec, adhoc

__all__ = [
    "CommandBuilder",
    "ParamSpec",
    "SimpleCommand",
    "Word",
    "adhoc",
]
