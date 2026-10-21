"""
Runtime JSON Schema and numerical invariant validator for `house_price_3d.json`.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict

import jsonschema

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_SCHEMA_PATH = PROJECT_DIR / "schema" / "house_price_3d.schema.json"


def _assert_no_non_finite_numbers(obj: Any, path: str = "$") -> None:
    """Recursively ensure no NaN or Infinity values exist anywhere in the payload."""
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError(f"Non-finite float value {obj!r} found at {path}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            _assert_no_non_finite_numbers(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _assert_no_non_finite_numbers(item, f"{path}[{idx}]")


def load_schema(schema_path: Path = DEFAULT_SCHEMA_PATH) -> Dict[str, Any]:
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"JSON Schema not found at: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_3d_payload(
    payload: Dict[str, Any],
    schema_path: Path = DEFAULT_SCHEMA_PATH,
) -> None:
    """
    Validate `payload` against the Draft 2020-12 JSON Schema AND verify strict
    numerical and geometric invariants required by the React/Three.js frontend.
    """
    _assert_no_non_finite_numbers(payload)
    schema = load_schema(schema_path)
    jsonschema.validate(instance=payload, schema=schema)

    surface = payload["surface"]
    x_vals = surface["xAxis"]["values"]
    y_vals = surface["yAxis"]["values"]
    z_usd = surface["zMatrixUsd"]

    if len(x_vals) != 50 or len(y_vals) != 50:
        raise ValueError("Surface axes must each contain exactly 50 values.")
    if any(x_vals[i] >= x_vals[i + 1] for i in range(len(x_vals) - 1)):
        raise ValueError("xAxis.values must be strictly increasing.")
    if any(y_vals[i] >= y_vals[i + 1] for i in range(len(y_vals) - 1)):
        raise ValueError("yAxis.values must be strictly increasing.")
    if len(z_usd) != 50 or any(len(row) != 50 for row in z_usd):
        raise ValueError("zMatrixUsd must be a 50x50 matrix.")

    # Verify SHAP additivity on every example
    for ex in payload["examples"]:
        exp = ex["explainability"]
        contrib_sum = sum(item["shapLog1p"] for item in exp["contributions"])
        reconstructed = exp["baseValueLog1p"] + contrib_sum
        diff = abs(reconstructed - exp["predictedLog1p"])
        if diff > exp["additivityTolerance"] + 1e-5:
            raise ValueError(
                f"SHAP additivity failed in payload for {ex['id']}: "
                f"diff={diff:.8e} > tol={exp['additivityTolerance']}"
            )
