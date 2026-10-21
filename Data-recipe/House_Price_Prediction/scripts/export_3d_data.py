#!/usr/bin/env python3
"""
Reproducible 3D Prediction Surface, Examples, SHAP Explainability & Evaluation Exporter
for the Ames House Price Prediction Stacking Regressor Pipeline.

Usage:
    python3 Data-recipe/House_Price_Prediction/scripts/export_3d_data.py
    python3 scripts/export_3d_data.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, median_absolute_error, r2_score

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_DIR.parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from pipeline import (  # noqa: E402
    AmesFeatureEngineer,
    CV_FOLDS,
    DEFAULT_ARTIFACT_PATH,
    DEFAULT_DATASET_DIR,
    MODEL_VERSION,
    RANDOM_SEED,
    compute_baseline_features,
    compute_file_sha256,
    compute_stacking_shap_explanations,
    get_preprocessed_feature_groups,
    identify_feature_types,
    load_and_clean_dataset,
    load_or_train_artifact,
    predict_with_pipeline,
)
from schema_validator import DEFAULT_SCHEMA_PATH, validate_3d_payload  # noqa: E402

SCHEMA_VERSION = "1.0.0"
GRID_SIZE = 50
DEFAULT_PROJECT_ASSET_PATH = PROJECT_DIR / "assets" / "house_price_3d.json"
DEFAULT_PORTFOLIO_ASSET_PATH = REPO_ROOT / "portfolio" / "assets" / "house_price_3d.json"

ORDINAL_FEATURES = {
    "OverallQual",
    "OverallCond",
    "ExterQual",
    "ExterCond",
    "BsmtQual",
    "BsmtCond",
    "BsmtExposure",
    "BsmtFinType1",
    "BsmtFinType2",
    "HeatingQC",
    "KitchenQual",
    "Functional",
    "FireplaceQu",
    "GarageFinish",
    "GarageQual",
    "GarageCond",
    "PavedDrive",
    "PoolQC",
    "Fence",
}

FEATURE_UNITS: Dict[str, str] = {
    "LotFrontage": "linear_ft",
    "LotArea": "sq_ft",
    "OverallQual": "rating_1_to_10",
    "OverallCond": "rating_1_to_10",
    "YearBuilt": "year",
    "YearRemodAdd": "year",
    "MasVnrArea": "sq_ft",
    "BsmtFinSF1": "sq_ft",
    "BsmtFinSF2": "sq_ft",
    "BsmtUnfSF": "sq_ft",
    "TotalBsmtSF": "sq_ft",
    "1stFlrSF": "sq_ft",
    "2ndFlrSF": "sq_ft",
    "LowQualFinSF": "sq_ft",
    "GrLivArea": "sq_ft",
    "BsmtFullBath": "count",
    "BsmtHalfBath": "count",
    "FullBath": "count",
    "HalfBath": "count",
    "BedroomAbvGr": "count",
    "KitchenAbvGr": "count",
    "TotRmsAbvGrd": "count",
    "Fireplaces": "count",
    "GarageYrBlt": "year",
    "GarageCars": "cars",
    "GarageArea": "sq_ft",
    "WoodDeckSF": "sq_ft",
    "OpenPorchSF": "sq_ft",
    "EnclosedPorch": "sq_ft",
    "3SsnPorch": "sq_ft",
    "ScreenPorch": "sq_ft",
    "PoolArea": "sq_ft",
    "MiscVal": "USD",
    "MoSold": "month_1_to_12",
    "YrSold": "year",
}


def resolve_source_revision(dataset_dir: Path) -> str:
    """Return git commit SHA if available, otherwise a deterministic source+data SHA-256 digest."""
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--short=12", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
            timeout=3,
        )
        sha = proc.stdout.strip()
        if sha:
            return f"git:{sha}"
    except Exception:
        pass

    hasher = hashlib.sha256()
    for path in [
        dataset_dir / "train.csv",
        PROJECT_DIR / "pipeline.py",
        Path(__file__).resolve(),
    ]:
        if path.exists():
            hasher.update(compute_file_sha256(path).encode("utf-8"))
    return f"sha256:{hasher.hexdigest()[:16]}"


def generate_axis_values(
    min_val: float,
    max_val: float,
    size: int = GRID_SIZE,
    as_integer: bool = False,
) -> List[Any]:
    """
    Generate `size` strictly increasing axis coordinates across `[min_val, max_val]`.
    Handles constant or degenerate feature ranges safely without NaN or duplicate collapse.
    """
    if size < 2:
        raise ValueError("Grid axis size must be at least 2.")
    if not np.isfinite(min_val) or not np.isfinite(max_val):
        raise ValueError(f"Non-finite axis bounds: min={min_val}, max={max_val}")

    if max_val < min_val:
        min_val, max_val = max_val, min_val

    if np.isclose(min_val, max_val):
        # Safe fallback for degenerate/constant feature range
        center = float(min_val)
        span = max(abs(center) * 0.1, float(size))
        min_val = center - span / 2.0
        max_val = center + span / 2.0

    raw_grid = np.linspace(float(min_val), float(max_val), size)
    if as_integer:
        # Only round to integers if the range is wide enough to yield `size` unique integers
        rounded = np.round(raw_grid).astype(int)
        if len(np.unique(rounded)) == size:
            return [int(v) for v in rounded]
        # If range is narrower than `size`, step by 1 from int(round(min_val))
        start_int = int(round(min_val))
        return [start_int + i for i in range(size)]

    return [round(float(v), 4) for v in raw_grid]


def build_surface_data(
    pipeline: Any,
    X_train: pd.DataFrame,
    raw_feature_names: List[str],
    grid_size: int = GRID_SIZE,
) -> Dict[str, Any]:
    """
    Generate the 50x50 prediction surface over GrLivArea (X) and OverallQual (Y)
    using the actual fitted model pipeline, with all remaining 77 raw features fixed
    to their training-data baseline values.
    """
    baseline_features = compute_baseline_features(X_train)
    baseline_df = pd.DataFrame([baseline_features])[raw_feature_names]
    base_log1p, base_usd = predict_with_pipeline(pipeline, baseline_df, raw_feature_names)

    x_min = float(X_train["GrLivArea"].min())
    x_max = float(X_train["GrLivArea"].max())
    y_min = float(X_train["OverallQual"].min())
    y_max = float(X_train["OverallQual"].max())

    x_values = generate_axis_values(x_min, x_max, size=grid_size, as_integer=True)
    y_values = generate_axis_values(y_min, y_max, size=grid_size, as_integer=False)

    # Construct the 2,500 grid rows in row-major order:
    # outer loop over y_idx (OverallQual), inner loop over x_idx (GrLivArea)
    total_points = grid_size * grid_size
    grid_rows: List[Dict[str, Any]] = []
    for y_val in y_values:
        for x_val in x_values:
            row = dict(baseline_features)
            row["GrLivArea"] = int(x_val)
            row["OverallQual"] = float(y_val)
            grid_rows.append(row)

    grid_df = pd.DataFrame(grid_rows)[raw_feature_names]
    assert len(grid_df) == total_points

    grid_log1p, grid_usd = predict_with_pipeline(pipeline, grid_df, raw_feature_names)

    z_matrix_log1p: List[List[float]] = []
    z_matrix_usd: List[List[float]] = []
    for r in range(grid_size):
        start = r * grid_size
        end = start + grid_size
        row_log = [round(float(v), 6) for v in grid_log1p[start:end]]
        row_usd = [round(float(v), 2) for v in grid_usd[start:end]]
        z_matrix_log1p.append(row_log)
        z_matrix_usd.append(row_usd)

    return {
        "gridShape": [grid_size, grid_size],
        "matrixOrdering": "row_major_y_outer_x_inner",
        "matrixIndexingConvention": (
            "zMatrixUsd[row_idx][col_idx] corresponds to y = yAxis.values[row_idx] "
            "(OverallQual) and x = xAxis.values[col_idx] (GrLivArea)."
        ),
        "threeJsGeometryMapping": (
            "For a Three.js PlaneGeometry(width, depth, 49, 49), vertex index "
            "k = row_idx * 50 + col_idx maps directly to x = xAxis.values[col_idx], "
            "y_world (elevation) = zMatrixUsd[row_idx][col_idx], and z_world = yAxis.values[row_idx]."
        ),
        "xAxis": {
            "feature": "GrLivArea",
            "label": "Above-Grade Living Area (GrLivArea)",
            "unit": "sq_ft",
            "min": float(x_values[0]),
            "max": float(x_values[-1]),
            "size": grid_size,
            "values": x_values,
        },
        "yAxis": {
            "feature": "OverallQual",
            "label": "Overall Material & Finish Quality (OverallQual)",
            "unit": "rating_1_to_10",
            "min": float(y_values[0]),
            "max": float(y_values[-1]),
            "size": grid_size,
            "validDiscreteRatings": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "values": y_values,
        },
        "zUnit": "USD",
        "zCurrency": "USD",
        "zMinUsd": round(float(np.min(grid_usd)), 2),
        "zMaxUsd": round(float(np.max(grid_usd)), 2),
        "zMatrixUsd": z_matrix_usd,
        "zMatrixLog1p": z_matrix_log1p,
        "baselineFeatures": baseline_features,
        "baselinePredictionUsd": round(float(base_usd[0]), 2),
        "baselinePredictionLog1p": round(float(base_log1p[0]), 6),
    }


def select_representative_examples(
    cleaned_train_df: pd.DataFrame,
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    oof_preds_log1p: np.ndarray,
    oof_fold_indices: np.ndarray,
    pipeline: Any,
    raw_feature_names: List[str],
) -> List[Dict[str, Any]]:
    """
    Select 10 diverse, real observations from the held-out 5-fold OOF evaluation dataset
    spanning the feature space (low/median/high price tiers, small/large living area,
    low/high quality, plus low-error and high-error diagnostic cases) and attach
    genuine SHAP explanations.
    """
    actual_usd = cleaned_train_df["SalePrice"].astype(float).values
    oof_usd = np.expm1(oof_preds_log1p)
    oof_abs_err = np.abs(actual_usd - oof_usd)

    # Select deterministic archetypes across the feature/target space (not cherry-picked by training error)
    candidates: List[Tuple[str, str, str, int]] = []
    used_indices: set[int] = set()

    def pick_index(score_series: pd.Series, code: str, label: str, reason: str) -> None:
        for idx in score_series.index:
            i = int(idx)
            if i not in used_indices:
                used_indices.add(i)
                candidates.append((code, label, reason, i))
                return

    # 1. Starter / Budget Home (10th percentile actual SalePrice)
    q10_price = float(np.percentile(actual_usd, 10))
    pick_index(
        pd.Series(np.abs(actual_usd - q10_price)).sort_values(),
        "ex_01_starter_budget",
        "Starter Budget Home (10th Percentile Price)",
        "Representative entry-level Ames residential property near the 10th percentile of SalePrice.",
    )

    # 2. Typical Median Home (closest to median SalePrice, GrLivArea, and OverallQual=6)
    med_price = float(np.median(actual_usd))
    med_area = float(X_train["GrLivArea"].median())
    median_dist = (
        np.abs(actual_usd - med_price) / med_price
        + np.abs(X_train["GrLivArea"].values - med_area) / med_area
        + np.abs(X_train["OverallQual"].values - 6)
    )
    pick_index(
        pd.Series(median_dist).sort_values(),
        "ex_02_median_typical",
        "Typical Median Ames Home (50th Percentile)",
        "Archetypal mid-market home near the dataset median SalePrice ($163k), GrLivArea, and OverallQual (6).",
    )

    # 3. Family Suburban Home (75th percentile SalePrice, OverallQual=7)
    q75_price = float(np.percentile(actual_usd, 75))
    q75_dist = np.abs(actual_usd - q75_price) + 50000 * (X_train["OverallQual"].values != 7)
    pick_index(
        pd.Series(q75_dist).sort_values(),
        "ex_03_upper_mid_family",
        "Upper-Mid Family Home (75th Percentile Price)",
        "Representative 2-story family home at the 75th percentile of SalePrice with OverallQual=7.",
    )

    # 4. Executive High-Quality Home (90th percentile SalePrice, OverallQual=8)
    q90_price = float(np.percentile(actual_usd, 90))
    q90_dist = np.abs(actual_usd - q90_price) + 50000 * (X_train["OverallQual"].values != 8)
    pick_index(
        pd.Series(q90_dist).sort_values(),
        "ex_04_executive_high_qual",
        "Executive High-Quality Home (90th Percentile Price)",
        "High-grade property at the 90th percentile of SalePrice with OverallQual=8.",
    )

    # 5. Luxury Estate Home (99th percentile SalePrice, OverallQual=10)
    q99_price = float(np.percentile(actual_usd, 99))
    q99_dist = np.abs(actual_usd - q99_price) + 100000 * (X_train["OverallQual"].values < 9)
    pick_index(
        pd.Series(q99_dist).sort_values(),
        "ex_05_luxury_estate",
        "Luxury Custom Estate (99th Percentile Price)",
        "Top-tier luxury home with OverallQual>=9 and expansive living space.",
    )

    # 6. Compact High-Quality Home (small GrLivArea <= 1100 sq ft, high OverallQual >= 7)
    compact_score = X_train["GrLivArea"].values + 10000 * (X_train["OverallQual"].values < 7)
    pick_index(
        pd.Series(compact_score).sort_values(),
        "ex_06_compact_high_grade",
        "Compact High-Grade Home (Small Area, High Quality)",
        "Off-diagonal surface corner case: compact living area combined with high material quality (OverallQual>=7).",
    )

    # 7. Spacious Economy Home (large GrLivArea >= 2200 sq ft, modest OverallQual <= 5)
    spacious_score = -X_train["GrLivArea"].values + 10000 * (X_train["OverallQual"].values > 5)
    pick_index(
        pd.Series(spacious_score).sort_values(),
        "ex_07_spacious_modest_grade",
        "Spacious Modest-Grade Home (Large Area, Average Quality)",
        "Off-diagonal surface corner case: large square footage (>2,200 sq ft) with modest finish quality (OverallQual<=5).",
    )

    # 8. Historic Remodeled Home (built before 1930, remodeled after 1995)
    historic_score = (
        X_train["YearBuilt"].values
        + 10000 * (X_train["YearBuilt"].values > 1930)
        + 10000 * (X_train["YearRemodAdd"].values < 1995)
    )
    pick_index(
        pd.Series(historic_score).sort_values(),
        "ex_08_historic_remodeled",
        "Historic Remodeled Residence (Pre-1930 Build, Modern Remodel)",
        "Demonstrates temporal feature engineering (HouseAge vs RemodAge and IsRemodeled).",
    )

    # 9. Median OOF Error Observation (typical held-out prediction accuracy)
    med_oof_err = float(np.median(oof_abs_err))
    pick_index(
        pd.Series(np.abs(oof_abs_err - med_oof_err)).sort_values(),
        "ex_09_median_oof_error",
        "Median Held-Out Error Benchmark Observation",
        "Observation whose held-out out-of-fold prediction error matches the dataset median absolute error.",
    )

    # 10. High Held-Out Residual Diagnostic Case (95th percentile OOF error)
    q95_oof_err = float(np.percentile(oof_abs_err, 95))
    pick_index(
        pd.Series(np.abs(oof_abs_err - q95_oof_err)).sort_values(),
        "ex_10_high_residual_case",
        "High Held-Out Residual Diagnostic Case (95th Percentile Error)",
        "Included for honest error analysis: held-out observation at the 95th percentile of absolute prediction error.",
    )

    selected_row_indices = [idx for _, _, _, idx in candidates]
    X_examples = X_train.iloc[selected_row_indices].copy().reset_index(drop=True)

    # Pipeline predictions and exact SHAP explanations
    pred_log1p, pred_usd = predict_with_pipeline(pipeline, X_examples, raw_feature_names)
    fe = AmesFeatureEngineer()
    X_examples_eng = fe.fit_transform(X_examples)
    shap_explanations = compute_stacking_shap_explanations(
        pipeline=pipeline,
        X_train=X_train,
        X_explain=X_examples,
    )

    examples_payload: List[Dict[str, Any]] = []
    for k, (code, label, reason, orig_idx) in enumerate(candidates):
        house_id = int(cleaned_train_df.loc[orig_idx, "Id"])
        act_usd = float(actual_usd[orig_idx])
        act_log = float(y_train[orig_idx])
        p_log = float(pred_log1p[k])
        p_usd = float(pred_usd[k])
        o_log = float(oof_preds_log1p[orig_idx])
        o_usd = float(oof_usd[orig_idx])
        fold_id = int(oof_fold_indices[orig_idx])

        raw_row = X_examples.iloc[k]
        raw_feat_dict: Dict[str, Any] = {}
        for col in raw_feature_names:
            val = raw_row[col]
            if pd.isna(val):
                raw_feat_dict[col] = None
            elif isinstance(val, (np.integer, int)):
                raw_feat_dict[col] = int(val)
            elif isinstance(val, (np.floating, float)):
                raw_feat_dict[col] = int(val) if float(val).is_integer() else round(float(val), 4)
            else:
                raw_feat_dict[col] = str(val)

        eng_row = X_examples_eng.iloc[k]
        eng_feat_dict: Dict[str, Any] = {}
        for col in AmesFeatureEngineer.ENGINEERED_COLS:
            val = eng_row[col]
            if isinstance(val, (np.integer, int)):
                eng_feat_dict[col] = int(val)
            elif isinstance(val, (np.floating, float)):
                eng_feat_dict[col] = int(val) if float(val).is_integer() else round(float(val), 4)
            else:
                eng_feat_dict[col] = float(val)

        abs_err_usd = abs(act_usd - p_usd)
        oof_err_usd = abs(act_usd - o_usd)
        rel_err_pct = (abs_err_usd / act_usd) * 100.0

        examples_payload.append(
            {
                "id": f"{code}_house_{house_id}",
                "houseId": house_id,
                "label": label,
                "selectionReason": reason,
                "isRealObservation": True,
                "evaluationSplit": "5_fold_out_of_fold_validation",
                "cvFold": fold_id,
                "actualPriceUsd": round(act_usd, 2),
                "actualPriceLog1p": round(act_log, 6),
                "predictedPriceUsd": round(p_usd, 2),
                "predictedPriceLog1p": round(p_log, 6),
                "oofPredictedPriceUsd": round(o_usd, 2),
                "oofPredictedPriceLog1p": round(o_log, 6),
                "absoluteErrorUsd": round(abs_err_usd, 2),
                "oofAbsoluteErrorUsd": round(oof_err_usd, 2),
                "relativeErrorPct": round(rel_err_pct, 2),
                "surfaceCoordinates": {
                    "xGrLivArea": int(raw_feat_dict["GrLivArea"]),
                    "yOverallQual": int(raw_feat_dict["OverallQual"]),
                    "zActualUsd": round(act_usd, 2),
                    "zPredictedUsd": round(p_usd, 2),
                    "zOofPredictedUsd": round(o_usd, 2),
                },
                "features": raw_feat_dict,
                "engineeredFeatures": eng_feat_dict,
                "explainability": shap_explanations[k],
            }
        )

    return examples_payload


def build_feature_metadata(
    X_train: pd.DataFrame,
    baseline_features: Dict[str, Any],
) -> Dict[str, Any]:
    """Build rich metadata for the 2 surface axes, 9 engineered features, and all 79 raw input features."""
    surface_axes = [
        {
            "axis": "x",
            "name": "GrLivArea",
            "label": "Above-Grade Living Area",
            "unit": "sq_ft",
            "kind": "numerical",
            "isIntegerInDataset": True,
            "min": float(X_train["GrLivArea"].min()),
            "max": float(X_train["GrLivArea"].max()),
            "median": float(X_train["GrLivArea"].median()),
            "mean": round(float(X_train["GrLivArea"].mean()), 2),
            "q05": round(float(X_train["GrLivArea"].quantile(0.05)), 2),
            "q95": round(float(X_train["GrLivArea"].quantile(0.95)), 2),
            "selectionRationale": (
                "Primary continuous spatial feature in the Ames dataset (Pearson r = 0.72 with log1p(SalePrice) "
                "after outlier sanitization; spans 334 to 4,476 sq ft)."
            ),
        },
        {
            "axis": "y",
            "name": "OverallQual",
            "label": "Overall Material & Finish Quality",
            "unit": "rating_1_to_10",
            "kind": "ordinal",
            "isIntegerInDataset": True,
            "min": float(X_train["OverallQual"].min()),
            "max": float(X_train["OverallQual"].max()),
            "median": float(X_train["OverallQual"].median()),
            "mean": round(float(X_train["OverallQual"].mean()), 2),
            "q05": round(float(X_train["OverallQual"].quantile(0.05)), 2),
            "q95": round(float(X_train["OverallQual"].quantile(0.95)), 2),
            "selectionRationale": (
                "Strongest single predictor of log1p(SalePrice) (Pearson r = 0.82), rating overall "
                "material and finish quality on an ordinal scale from 1 (Very Poor) to 10 (Very Excellent)."
            ),
        },
    ]

    engineered_features = [
        {
            "name": "TotalSF",
            "formula": "TotalBsmtSF + 1stFlrSF + 2ndFlrSF",
            "unit": "sq_ft",
            "sourceColumns": ["TotalBsmtSF", "1stFlrSF", "2ndFlrSF"],
        },
        {
            "name": "TotalBath",
            "formula": "FullBath + 0.5 * HalfBath + BsmtFullBath + 0.5 * BsmtHalfBath",
            "unit": "bathrooms",
            "sourceColumns": ["FullBath", "HalfBath", "BsmtFullBath", "BsmtHalfBath"],
        },
        {
            "name": "TotalPorchSF",
            "formula": "WoodDeckSF + OpenPorchSF + EnclosedPorch + 3SsnPorch + ScreenPorch",
            "unit": "sq_ft",
            "sourceColumns": ["WoodDeckSF", "OpenPorchSF", "EnclosedPorch", "3SsnPorch", "ScreenPorch"],
        },
        {
            "name": "HouseAge",
            "formula": "YrSold - YearBuilt",
            "unit": "years",
            "sourceColumns": ["YrSold", "YearBuilt"],
        },
        {
            "name": "RemodAge",
            "formula": "YrSold - YearRemodAdd",
            "unit": "years",
            "sourceColumns": ["YrSold", "YearRemodAdd"],
        },
        {
            "name": "IsRemodeled",
            "formula": "int(YearRemodAdd != YearBuilt)",
            "unit": "binary_flag",
            "sourceColumns": ["YearRemodAdd", "YearBuilt"],
        },
        {
            "name": "HasPool",
            "formula": "int(PoolArea > 0)",
            "unit": "binary_flag",
            "sourceColumns": ["PoolArea"],
        },
        {
            "name": "HasGarage",
            "formula": "int(GarageArea > 0)",
            "unit": "binary_flag",
            "sourceColumns": ["GarageArea"],
        },
        {
            "name": "HasBsmt",
            "formula": "int(TotalBsmtSF > 0)",
            "unit": "binary_flag",
            "sourceColumns": ["TotalBsmtSF"],
        },
    ]

    input_features: List[Dict[str, Any]] = []
    for col in X_train.columns:
        series = X_train[col]
        missing_count = int(series.isna().sum())
        nullable = bool(missing_count > 0)
        unit = FEATURE_UNITS.get(col, "categorical" if not pd.api.types.is_numeric_dtype(series) else "count")

        if pd.api.types.is_numeric_dtype(series) and col != "MSSubClass":
            non_null = series.dropna()
            kind = "ordinal" if col in ORDINAL_FEATURES else "numerical"
            input_features.append(
                {
                    "name": col,
                    "kind": kind,
                    "dtype": str(series.dtype),
                    "unit": unit,
                    "nullable": nullable,
                    "missingCountTrain": missing_count,
                    "baselineValue": baseline_features[col],
                    "min": float(non_null.min()) if len(non_null) > 0 else None,
                    "max": float(non_null.max()) if len(non_null) > 0 else None,
                    "median": float(non_null.median()) if len(non_null) > 0 else None,
                    "categories": None,
                }
            )
        else:
            non_null_str = series.dropna().astype(int).astype(str) if col == "MSSubClass" else series.dropna().astype(str)
            cats = sorted(non_null_str.unique().tolist())
            kind = "ordinal" if col in ORDINAL_FEATURES else "categorical"
            input_features.append(
                {
                    "name": col,
                    "kind": kind,
                    "dtype": "string_categorical",
                    "unit": "category",
                    "nullable": nullable,
                    "missingCountTrain": missing_count,
                    "baselineValue": baseline_features[col],
                    "min": None,
                    "max": None,
                    "median": None,
                    "categories": cats,
                }
            )

    return {
        "surfaceAxes": surface_axes,
        "engineeredFeatures": engineered_features,
        "inputFeatures": input_features,
    }


def build_evaluation_section(
    cleaned_train_df: pd.DataFrame,
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    oof_preds_log1p: np.ndarray,
    oof_fold_indices: np.ndarray,
    stack_cv_benchmark: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Compute held-out 5-fold out-of-fold evaluation metrics (RMSLE, MAE, RMSE, MedianAE, MAPE, R2)
    and export all 1,458 held-out actual-vs-predicted observations.
    """
    actual_usd = cleaned_train_df["SalePrice"].astype(float).values
    pred_oof_usd = np.expm1(oof_preds_log1p)

    overall_rmsle = float(np.sqrt(mean_squared_error(y_train, oof_preds_log1p)))
    mae_usd = float(mean_absolute_error(actual_usd, pred_oof_usd))
    rmse_usd = float(np.sqrt(mean_squared_error(actual_usd, pred_oof_usd)))
    median_ae_usd = float(median_absolute_error(actual_usd, pred_oof_usd))
    mape_pct = float(np.mean(np.abs((actual_usd - pred_oof_usd) / actual_usd)) * 100.0)
    r2_usd = float(r2_score(actual_usd, pred_oof_usd))
    r2_log1p = float(r2_score(y_train, oof_preds_log1p))

    points: List[Dict[str, Any]] = []
    for i in range(len(cleaned_train_df)):
        act_u = float(actual_usd[i])
        prd_u = float(pred_oof_usd[i])
        act_l = float(y_train[i])
        prd_l = float(oof_preds_log1p[i])
        points.append(
            {
                "houseId": int(cleaned_train_df.loc[i, "Id"]),
                "fold": int(oof_fold_indices[i]),
                "actualUsd": round(act_u, 2),
                "predictedOofUsd": round(prd_u, 2),
                "actualLog1p": round(act_l, 6),
                "predictedOofLog1p": round(prd_l, 6),
                "residualLog1p": round(act_l - prd_l, 6),
                "errorUsd": round(prd_u - act_u, 2),
                "grLivArea": int(X_train.loc[i, "GrLivArea"]),
                "overallQual": int(X_train.loc[i, "OverallQual"]),
            }
        )

    return {
        "methodology": (
            "5-Fold Cross-Validation Out-of-Fold (OOF) Evaluation (`KFold(n_splits=5, shuffle=True, random_state=42)`). "
            "Every observation's prediction `predictedOofUsd` is generated strictly by a StackingRegressor "
            "trained on the other 4 folds, preventing any training-set data leakage."
        ),
        "splitType": "5_fold_out_of_fold_cross_validation",
        "cvFolds": CV_FOLDS,
        "randomSeed": RANDOM_SEED,
        "sampleCount": len(cleaned_train_df),
        "targetUnit": "USD",
        "targetCurrency": "USD",
        "metrics": {
            "rmsle": round(overall_rmsle, 6),
            "cvMeanRmsle": round(float(stack_cv_benchmark["meanRmsle"]), 6),
            "cvStdRmsle": round(float(stack_cv_benchmark["stdRmsle"]), 6),
            "maeUsd": round(mae_usd, 2),
            "rmseUsd": round(rmse_usd, 2),
            "medianAeUsd": round(median_ae_usd, 2),
            "mapePct": round(mape_pct, 4),
            "r2Usd": round(r2_usd, 6),
            "r2Log1p": round(r2_log1p, 6),
        },
        "metricDefinitions": {
            "rmsle": "Root Mean Squared Logarithmic Error: sqrt(mean((log1p(actualUsd) - log1p(predictedOofUsd))^2)).",
            "maeUsd": "Mean Absolute Error in USD on held-out out-of-fold predictions: mean(|actualUsd - predictedOofUsd|).",
            "rmseUsd": "Root Mean Squared Error in USD on held-out out-of-fold predictions: sqrt(mean((actualUsd - predictedOofUsd)^2)).",
            "medianAeUsd": "Median Absolute Error in USD on held-out out-of-fold predictions.",
            "mapePct": "Mean Absolute Percentage Error (%) on held-out out-of-fold predictions.",
            "r2Usd": "Coefficient of determination (R^2) in inverted USD price space on held-out OOF predictions.",
            "r2Log1p": "Coefficient of determination (R^2) in log1p(SalePrice) space on held-out OOF predictions.",
        },
        "actualVsPredicted": points,
    }


def generate_3d_export_payload(
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    allow_train: bool = True,
    force_retrain: bool = False,
    generated_at: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Assemble and validate the complete `house_price_3d.json` data structure.
    """
    dataset_dir = Path(dataset_dir)
    artifact_path = Path(artifact_path)

    data = load_and_clean_dataset(dataset_dir)
    bundle = load_or_train_artifact(
        artifact_path=artifact_path,
        dataset_dir=dataset_dir,
        allow_train=allow_train,
        force_retrain=force_retrain,
    )

    pipeline = bundle["pipeline"]
    X_train: pd.DataFrame = data["X_train"]
    y_train: np.ndarray = data["y_train"]
    cleaned_train_df: pd.DataFrame = data["cleaned_train_df"]
    raw_saleprice: pd.Series = data["raw_saleprice"]
    raw_feature_names: List[str] = bundle["raw_feature_names"]

    full_preprocessor = pipeline.named_steps["prep"]
    stacking_model = pipeline.named_steps["stack"]
    meta_ridge = stacking_model.final_estimator_

    transformed_names, _ = get_preprocessed_feature_groups(
        full_preprocessor,
        bundle["numeric_features"],
        bundle["categorical_features"],
    )

    # Model metadata & base estimator weights
    base_estimator_specs = [
        ("ridge", "Ridge", "sklearn.linear_model.Ridge", {"alpha": 15.0}),
        ("lasso", "Lasso", "sklearn.linear_model.Lasso", {"alpha": 0.0005, "random_state": 42}),
        (
            "elasticnet",
            "ElasticNet",
            "sklearn.linear_model.ElasticNet",
            {"alpha": 0.0005, "l1_ratio": 0.85, "random_state": 42},
        ),
        (
            "gboost",
            "GBoost",
            "sklearn.ensemble.GradientBoostingRegressor",
            {
                "n_estimators": 1000,
                "learning_rate": 0.02,
                "max_depth": 4,
                "max_features": "sqrt",
                "loss": "huber",
                "random_state": 42,
            },
        ),
        (
            "xgboost",
            "XGBoost",
            "xgboost.XGBRegressor",
            {
                "n_estimators": 1000,
                "learning_rate": 0.02,
                "max_depth": 3,
                "subsample": 0.7,
                "colsample_bytree": 0.7,
                "random_state": 42,
            },
        ),
        (
            "lightgbm",
            "LightGBM",
            "lightgbm.LGBMRegressor",
            {
                "n_estimators": 1000,
                "learning_rate": 0.02,
                "num_leaves": 15,
                "subsample": 0.7,
                "colsample_bytree": 0.7,
                "random_state": 42,
            },
        ),
        (
            "catboost",
            "CatBoost",
            "catboost.CatBoostRegressor",
            {"iterations": 1000, "learning_rate": 0.02, "depth": 4, "random_state": 42},
        ),
    ]

    meta_coefs = np.asarray(meta_ridge.coef_, dtype=float)
    base_estimators_meta = []
    for idx, (est_id, est_name, est_cls, params) in enumerate(base_estimator_specs):
        base_estimators_meta.append(
            {
                "id": est_id,
                "name": est_name,
                "estimatorClass": est_cls,
                "hyperparameters": params,
                "metaWeight": round(float(meta_coefs[idx]), 6),
            }
        )

    cv_benchmarks_list = []
    for name, b_stats in bundle["base_cv_benchmarks"].items():
        cv_benchmarks_list.append(
            {
                "model": name,
                "meanRmsle": round(float(b_stats["meanRmsle"]), 6),
                "stdRmsle": round(float(b_stats["stdRmsle"]), 6),
                "foldRmsle": [round(float(x), 6) for x in b_stats["foldRmsle"]],
                "isFinalEnsemble": False,
            }
        )
    s_stats = bundle["stack_cv_benchmark"]
    cv_benchmarks_list.append(
        {
            "model": "Stacking Regressor",
            "meanRmsle": round(float(s_stats["meanRmsle"]), 6),
            "stdRmsle": round(float(s_stats["stdRmsle"]), 6),
            "foldRmsle": [round(float(x), 6) for x in s_stats["foldRmsle"]],
            "isFinalEnsemble": True,
        }
    )

    surface_section = build_surface_data(
        pipeline=pipeline,
        X_train=X_train,
        raw_feature_names=raw_feature_names,
        grid_size=GRID_SIZE,
    )

    features_section = build_feature_metadata(
        X_train=X_train,
        baseline_features=surface_section["baselineFeatures"],
    )

    examples_section = select_representative_examples(
        cleaned_train_df=cleaned_train_df,
        X_train=X_train,
        y_train=y_train,
        oof_preds_log1p=bundle["oof_preds_log1p"],
        oof_fold_indices=bundle["oof_fold_indices"],
        pipeline=pipeline,
        raw_feature_names=raw_feature_names,
    )

    evaluation_section = build_evaluation_section(
        cleaned_train_df=cleaned_train_df,
        X_train=X_train,
        y_train=y_train,
        oof_preds_log1p=bundle["oof_preds_log1p"],
        oof_fold_indices=bundle["oof_fold_indices"],
        stack_cv_benchmark=bundle["stack_cv_benchmark"],
    )

    timestamp = generated_at or dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rel_artifact_path = (
        str(artifact_path.relative_to(REPO_ROOT))
        if artifact_path.is_relative_to(REPO_ROOT)
        else str(artifact_path)
    )

    payload: Dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": timestamp,
        "sourceRevision": resolve_source_revision(dataset_dir),
        "model": {
            "name": "Ames Multi-Model Stacking Regressor",
            "version": MODEL_VERSION,
            "architecture": "Pipeline(AmesFeatureEngineer -> ColumnTransformer[RobustScaler, OneHotEncoder] -> StackingRegressor[7 Base Models -> Ridge(alpha=10.0)])",
            "targetVariable": "SalePrice",
            "targetCurrency": "USD",
            "targetUnit": "USD",
            "targetTransformation": "log1p",
            "inverseTransformation": "expm1",
            "randomSeed": RANDOM_SEED,
            "cvFolds": CV_FOLDS,
            "artifactPath": rel_artifact_path,
            "baseEstimators": base_estimators_meta,
            "metaEstimator": {
                "name": "Ridge Meta-Learner",
                "estimatorClass": "sklearn.linear_model.Ridge",
                "alpha": 10.0,
                "interceptLog1p": round(float(meta_ridge.intercept_), 6),
            },
            "cvBenchmarks": cv_benchmarks_list,
        },
        "dataset": {
            "name": "Ames Housing Dataset (Kaggle House Prices: Advanced Regression Techniques)",
            "source": "Data-recipe/House_Price_Prediction/Dataset",
            "trainFile": "Data-recipe/House_Price_Prediction/Dataset/train.csv",
            "testFile": "Data-recipe/House_Price_Prediction/Dataset/test.csv",
            "trainSha256": data["train_sha256"],
            "testSha256": data["test_sha256"],
            "rawTrainRows": data["raw_train_rows"],
            "cleanedTrainRows": data["cleaned_train_rows"],
            "removedOutlierCount": len(data["outlier_ids"]),
            "removedOutlierIds": data["outlier_ids"],
            "outlierFilterRule": "Remove rows where GrLivArea > 4000 sq ft AND SalePrice < $300,000 (Dean De Cock documentation recommendation)",
            "testRows": len(data["X_test"]),
            "rawFeatureCount": len(raw_feature_names),
            "engineeredFeatureCount": len(bundle["numeric_features"]) + len(bundle["categorical_features"]),
            "preprocessedFeatureCount": len(transformed_names),
            "targetSummaryUsd": {
                "min": round(float(raw_saleprice.min()), 2),
                "max": round(float(raw_saleprice.max()), 2),
                "mean": round(float(raw_saleprice.mean()), 2),
                "median": round(float(raw_saleprice.median()), 2),
                "std": round(float(raw_saleprice.std()), 2),
                "q05": round(float(raw_saleprice.quantile(0.05)), 2),
                "q25": round(float(raw_saleprice.quantile(0.25)), 2),
                "q75": round(float(raw_saleprice.quantile(0.75)), 2),
                "q95": round(float(raw_saleprice.quantile(0.95)), 2),
                "unit": "USD",
            },
        },
        "features": features_section,
        "surface": surface_section,
        "examples": examples_section,
        "evaluation": evaluation_section,
    }

    validate_3d_payload(payload, DEFAULT_SCHEMA_PATH)
    return payload


def atomic_write_json(payload: Dict[str, Any], output_path: Path) -> None:
    """
    Write JSON output atomically via temporary file + fsync + os.replace
    so incomplete or corrupted files are never published.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(output_path.parent),
        prefix=f".{output_path.name}.",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, allow_nan=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, output_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export precomputed 3D surface, examples, SHAP attributions, and evaluation JSON for the Ames House Price Prediction model."
    )
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=DEFAULT_DATASET_DIR,
        help="Path to directory containing train.csv and test.csv.",
    )
    parser.add_argument(
        "--artifact-path",
        type=Path,
        default=DEFAULT_ARTIFACT_PATH,
        help="Path to serialized joblib model artifact.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional custom output path for house_price_3d.json. When omitted, writes to both Data-recipe/House_Price_Prediction/assets/house_price_3d.json and portfolio/assets/house_price_3d.json.",
    )
    parser.add_argument(
        "--retrain",
        action="store_true",
        help="Force retraining and re-serializing the model pipeline even if the cached artifact exists.",
    )
    parser.add_argument(
        "--no-train-if-missing",
        action="store_true",
        help="Fail with an error if the serialized model artifact is missing instead of training it.",
    )
    parser.add_argument(
        "--generated-at",
        type=str,
        default=None,
        help="Optional fixed ISO-8601 UTC timestamp for deterministic test comparisons.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    payload = generate_3d_export_payload(
        dataset_dir=args.dataset_dir,
        artifact_path=args.artifact_path,
        allow_train=not args.no_train_if_missing,
        force_retrain=args.retrain,
        generated_at=args.generated_at,
    )

    if args.output is not None:
        targets = [Path(args.output)]
    else:
        targets = [DEFAULT_PROJECT_ASSET_PATH, DEFAULT_PORTFOLIO_ASSET_PATH]

    for target in targets:
        atomic_write_json(payload, target)
        print(f"[OK] Exported validated 3D asset ({target.stat().st_size:,} bytes) -> {target}")

    metrics = payload["evaluation"]["metrics"]
    print(
        f"[SUMMARY] 5-Fold OOF RMSLE={metrics['rmsle']:.4f} "
        f"(CV Mean={metrics['cvMeanRmsle']:.4f} +/- {metrics['cvStdRmsle']:.4f}), "
        f"MAE=${metrics['maeUsd']:,.2f}, RMSE=${metrics['rmseUsd']:,.2f}, R2(log1p)={metrics['r2Log1p']:.4f}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
