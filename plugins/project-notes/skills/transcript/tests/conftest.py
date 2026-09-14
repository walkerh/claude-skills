"""Make the skill's scripts importable.

The scripts are `uv run` files invoked directly, which puts their own
directory on sys.path; that is also what makes their plain sibling import
resolve. Tests have to reproduce that by hand.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
