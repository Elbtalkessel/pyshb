"""Pytest bootstrap: make the dev-time ``codegen`` package importable.

``codegen/`` is a dev tool, not part of the installed ``pyshb`` package, so it
is not on the path uv manages. The tests import ``codegen.schema``; putting the
repo root on ``sys.path`` lets that resolve without shipping ``codegen``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
