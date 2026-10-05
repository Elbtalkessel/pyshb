"""Convenience facade for pyshb: the names needed to *begin* a command.

Every public name lives in exactly one of two tiers.

* **Convenience** — ``from pyshb import X``. The handful of names a library user
  needs to start building a command, gathered here so the common case needs one
  import.
* **Module** — ``from pyshb.<module> import X``. Everything else: the AST node
  types, the operator enums, the compiler functions, and the exceptions. Each
  module keeps its own ``__all__``, and that is the authoritative surface for
  it.

The root set does not grow automatically. A name belongs here only when a user
cannot begin a command without it; anything reached *after* a command exists is
module-tier, because the builder returns builders and the nodes are already
reachable through them. See ``Decisions`` D012.

The legacy pre-AST layer in ``pyshb.base`` stays out of the root entirely, so
``from pyshb import Raw`` does not resolve and cannot be mistaken for the AST
quoting escape hatch, which is ``Word.raw_word``.
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
