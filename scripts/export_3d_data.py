#!/usr/bin/env python3
"""
Root CLI entrypoint wrapper for `Data-recipe/House_Price_Prediction/scripts/export_3d_data.py`.

Allows executing `python3 scripts/export_3d_data.py` directly from the repository root.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROJECT_SCRIPTS_DIR = REPO_ROOT / "Data-recipe" / "House_Price_Prediction" / "scripts"
PROJECT_DIR = REPO_ROOT / "Data-recipe" / "House_Price_Prediction"

for p in (str(PROJECT_SCRIPTS_DIR), str(PROJECT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from export_3d_data import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
