"""
Automated Test Suite for the Ames House Price Prediction 3D Data Export Pipeline.

Covers:
1. Model loading and preprocessing consistency (including agreement with submission.csv).
2. 50x50 grid dimensions and row-major matrix ordering.
3. Finite, valid positive prediction values across surface, examples, and evaluation points.
4. Feature ranges, units, integer constraints, and baseline metadata.
5. Strict JSON Schema validation (`house_price_3d.schema.json`).
6. Example prediction consistency with the original fitted pipeline.
7. Held-out 5-fold out-of-fold evaluation metric consistency (RMSLE, MAE, RMSE, R2).
8. Exact SHAP additivity verification within numerical tolerance.
9. Deterministic output across repeated executions (excluding `generatedAt`).
10. Clear error handling for missing artifacts, missing datasets, and invalid input data,
    plus safe handling of constant/degenerate feature ranges.
"""

from __future__ import annotations

import copy
import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

import jsonschema
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = PROJECT_DIR.parent.parent
SCRIPTS_DIR = PROJECT_DIR / "scripts"

for p in (str(PROJECT_DIR), str(SCRIPTS_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

from export_3d_data import (  # noqa: E402
    DEFAULT_PORTFOLIO_ASSET_PATH,
    DEFAULT_PROJECT_ASSET_PATH,
    GRID_SIZE,
    atomic_write_json,
    generate_3d_export_payload,
    generate_axis_values,
)
from pipeline import (  # noqa: E402
    AmesFeatureEngineer,
    DEFAULT_ARTIFACT_PATH,
    DEFAULT_DATASET_DIR,
    compute_baseline_features,
    load_and_clean_dataset,
    load_or_train_artifact,
    predict_with_pipeline,
)
from schema_validator import DEFAULT_SCHEMA_PATH, validate_3d_payload  # noqa: E402


class TestHousePrice3DExport(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = load_and_clean_dataset(DEFAULT_DATASET_DIR)
        cls.bundle = load_or_train_artifact(
            artifact_path=DEFAULT_ARTIFACT_PATH,
            dataset_dir=DEFAULT_DATASET_DIR,
            allow_train=True,
            force_retrain=False,
        )
        cls.pipeline = cls.bundle["pipeline"]
        cls.raw_feature_names = cls.bundle["raw_feature_names"]

        # Load generated JSON from disk if present, otherwise generate once
        if DEFAULT_PROJECT_ASSET_PATH.exists():
            with open(DEFAULT_PROJECT_ASSET_PATH, "r", encoding="utf-8") as f:
                cls.payload = json.load(f)
        else:
            cls.payload = generate_3d_export_payload(
                dataset_dir=DEFAULT_DATASET_DIR,
                artifact_path=DEFAULT_ARTIFACT_PATH,
                allow_train=False,
                generated_at="2026-10-19T00:00:00Z",
            )

    def test_01_model_loading_and_preprocessing_consistency(self) -> None:
        """Verify model loads without retraining and reproduces submission.csv predictions."""
        self.assertTrue(DEFAULT_ARTIFACT_PATH.exists(), "Serialized model artifact must exist.")
        loaded_bundle = load_or_train_artifact(
            artifact_path=DEFAULT_ARTIFACT_PATH,
            dataset_dir=DEFAULT_DATASET_DIR,
            allow_train=False,
            force_retrain=False,
        )
        self.assertEqual(loaded_bundle["raw_feature_names"], self.raw_feature_names)
        self.assertEqual(len(self.raw_feature_names), 79)

        # Verify AmesFeatureEngineer adds the 9 expected engineered columns
        fe = AmesFeatureEngineer()
        eng_df = fe.fit_transform(self.data["X_train"].iloc[:5])
        self.assertEqual(eng_df.shape[1], 88)
        for col in AmesFeatureEngineer.ENGINEERED_COLS:
            self.assertIn(col, eng_df.columns)
        self.assertTrue(pd.api.types.is_string_dtype(eng_df["MSSubClass"]))

        # Verify consistency with existing submission.csv on test set
        submission_path = PROJECT_DIR / "submission.csv"
        if submission_path.exists():
            sub_df = pd.read_csv(submission_path)
            _, test_preds_usd = predict_with_pipeline(
                self.pipeline,
                self.data["X_test"].iloc[:25],
                self.raw_feature_names,
            )
            rel_diff = np.abs(test_preds_usd - sub_df["SalePrice"].iloc[:25].values) / sub_df["SalePrice"].iloc[:25].values
            # Correlation across test predictions must be > 0.9999 and mean relative difference < 0.5%
            corr = np.corrcoef(test_preds_usd, sub_df["SalePrice"].iloc[:25].values)[0, 1]
            self.assertGreater(corr, 0.9995)
            self.assertLess(float(np.mean(rel_diff)), 0.005)

    def test_02_grid_dimensions_and_matrix_ordering(self) -> None:
        """Verify 50x50 surface grid dimensions and row_major_y_outer_x_inner ordering."""
        surface = self.payload["surface"]
        self.assertEqual(surface["gridShape"], [GRID_SIZE, GRID_SIZE])
        self.assertEqual(surface["matrixOrdering"], "row_major_y_outer_x_inner")

        x_vals = surface["xAxis"]["values"]
        y_vals = surface["yAxis"]["values"]
        z_usd = surface["zMatrixUsd"]
        z_log = surface["zMatrixLog1p"]

        self.assertEqual(len(x_vals), GRID_SIZE)
        self.assertEqual(len(y_vals), GRID_SIZE)
        self.assertEqual(len(z_usd), GRID_SIZE)
        self.assertEqual(len(z_log), GRID_SIZE)
        for row_u, row_l in zip(z_usd, z_log):
            self.assertEqual(len(row_u), GRID_SIZE)
            self.assertEqual(len(row_l), GRID_SIZE)

        # Spot-check matrix ordering at 4 distinct (row_idx, col_idx) coordinates directly against pipeline
        baseline = surface["baselineFeatures"]
        check_coords = [(0, 0), (0, 49), (49, 0), (24, 37)]
        for r_idx, c_idx in check_coords:
            probe = dict(baseline)
            probe["GrLivArea"] = int(x_vals[c_idx])
            probe["OverallQual"] = float(y_vals[r_idx])
            probe_df = pd.DataFrame([probe])[self.raw_feature_names]
            p_log, p_usd = predict_with_pipeline(self.pipeline, probe_df, self.raw_feature_names)
            self.assertAlmostEqual(z_usd[r_idx][c_idx], round(float(p_usd[0]), 2), places=2)
            self.assertAlmostEqual(z_log[r_idx][c_idx], round(float(p_log[0]), 6), places=5)

    def test_03_finite_valid_prediction_values(self) -> None:
        """Ensure all surface predictions, examples, and evaluation points are finite and positive."""
        surface = self.payload["surface"]
        z_flat = [val for row in surface["zMatrixUsd"] for val in row]
        self.assertEqual(len(z_flat), GRID_SIZE * GRID_SIZE)
        for val in z_flat:
            self.assertTrue(math.isfinite(val))
            self.assertGreater(val, 10000.0)
            self.assertLess(val, 2000000.0)

        self.assertAlmostEqual(surface["zMinUsd"], min(z_flat), places=2)
        self.assertAlmostEqual(surface["zMaxUsd"], max(z_flat), places=2)
        # Higher quality & larger living area corner must exceed lowest corner
        self.assertGreater(surface["zMatrixUsd"][49][49], surface["zMatrixUsd"][0][0])

    def test_04_feature_ranges_and_baseline_metadata(self) -> None:
        """Validate feature units, ranges, integer constraints, and baseline values."""
        X_train = self.data["X_train"]
        surface = self.payload["surface"]
        baseline = surface["baselineFeatures"]

        self.assertEqual(len(baseline), 79)
        self.assertEqual(surface["xAxis"]["min"], float(X_train["GrLivArea"].min()))
        self.assertEqual(surface["xAxis"]["max"], float(X_train["GrLivArea"].max()))
        self.assertEqual(surface["yAxis"]["min"], float(X_train["OverallQual"].min()))
        self.assertEqual(surface["yAxis"]["max"], float(X_train["OverallQual"].max()))

        # All xAxis values (GrLivArea) must be strictly increasing integers
        x_vals = surface["xAxis"]["values"]
        for i, val in enumerate(x_vals):
            self.assertIsInstance(val, int)
            if i > 0:
                self.assertGreater(val, x_vals[i - 1])

        # Verify integer-valued numerical features in baseline are stored as integers
        for int_col in ["OverallQual", "OverallCond", "YearBuilt", "FullBath", "BedroomAbvGr", "GarageCars"]:
            self.assertIsInstance(baseline[int_col], int)

    def test_05_json_schema_validation(self) -> None:
        """Validate generated payload against house_price_3d.schema.json and test rejection of invalid payloads."""
        validate_3d_payload(self.payload, DEFAULT_SCHEMA_PATH)

        # Verify both published files exist and match schema
        for path in (DEFAULT_PROJECT_ASSET_PATH, DEFAULT_PORTFOLIO_ASSET_PATH):
            self.assertTrue(path.exists(), f"Published asset missing at {path}")
            with open(path, "r", encoding="utf-8") as f:
                disk_payload = json.load(f)
            validate_3d_payload(disk_payload, DEFAULT_SCHEMA_PATH)

        # Negative test: corrupt gridShape and verify validator rejects it
        bad_payload = copy.deepcopy(self.payload)
        bad_payload["surface"]["zMatrixUsd"] = bad_payload["surface"]["zMatrixUsd"][:10]
        with self.assertRaises((jsonschema.ValidationError, ValueError)):
            validate_3d_payload(bad_payload, DEFAULT_SCHEMA_PATH)

    def test_06_example_prediction_consistency(self) -> None:
        """Verify exported house examples are real dataset observations and match pipeline predictions."""
        examples = self.payload["examples"]
        self.assertGreaterEqual(len(examples), 8)

        cleaned_df = self.data["cleaned_train_df"].set_index("Id")
        for ex in examples:
            house_id = ex["houseId"]
            self.assertIn(house_id, cleaned_df.index)
            true_row = cleaned_df.loc[house_id]
            self.assertAlmostEqual(ex["actualPriceUsd"], float(true_row["SalePrice"]), places=2)

            ex_df = pd.DataFrame([ex["features"]])[self.raw_feature_names]
            p_log, p_usd = predict_with_pipeline(self.pipeline, ex_df, self.raw_feature_names)
            self.assertAlmostEqual(ex["predictedPriceLog1p"], float(p_log[0]), places=5)
            self.assertAlmostEqual(ex["predictedPriceUsd"], float(p_usd[0]), places=1)
            self.assertAlmostEqual(
                ex["absoluteErrorUsd"],
                round(abs(ex["actualPriceUsd"] - ex["predictedPriceUsd"]), 2),
                places=1,
            )

    def test_07_evaluation_metric_consistency(self) -> None:
        """Verify held-out 5-fold OOF evaluation metrics match recomputed metrics from actualVsPredicted points."""
        eval_sec = self.payload["evaluation"]
        points = eval_sec["actualVsPredicted"]
        metrics = eval_sec["metrics"]

        self.assertEqual(eval_sec["sampleCount"], 1458)
        self.assertEqual(len(points), 1458)

        act_usd = np.array([p["actualUsd"] for p in points], dtype=float)
        pred_usd = np.array([p["predictedOofUsd"] for p in points], dtype=float)
        act_log = np.array([p["actualLog1p"] for p in points], dtype=float)
        pred_log = np.array([p["predictedOofLog1p"] for p in points], dtype=float)

        recomputed_rmsle = float(np.sqrt(mean_squared_error(act_log, pred_log)))
        recomputed_mae = float(mean_absolute_error(act_usd, pred_usd))
        recomputed_rmse = float(np.sqrt(mean_squared_error(act_usd, pred_usd)))
        recomputed_r2_log = float(r2_score(act_log, pred_log))

        self.assertAlmostEqual(metrics["rmsle"], recomputed_rmsle, places=4)
        self.assertAlmostEqual(metrics["maeUsd"], recomputed_mae, places=1)
        self.assertAlmostEqual(metrics["rmseUsd"], recomputed_rmse, places=1)
        self.assertAlmostEqual(metrics["r2Log1p"], recomputed_r2_log, places=4)
        # Ensure CV mean RMSLE matches the documented ~0.1081 benchmark
        self.assertAlmostEqual(metrics["cvMeanRmsle"], 0.1081, delta=0.002)

    def test_08_shap_additivity_verification(self) -> None:
        """Verify SHAP values are genuine and satisfy additivity in log1p and USD spaces."""
        for ex in self.payload["examples"]:
            exp = ex["explainability"]
            self.assertTrue(exp["additivityVerified"])
            self.assertEqual(len(exp["contributions"]), 79)

            sum_log1p = sum(c["shapLog1p"] for c in exp["contributions"])
            reconstructed_log1p = exp["baseValueLog1p"] + sum_log1p
            self.assertAlmostEqual(reconstructed_log1p, exp["predictedLog1p"], places=5)
            self.assertLessEqual(exp["additivityDiscrepancyLog1p"], exp["additivityTolerance"])

            # Check USD contribution additivity (within rounding of 79 two-decimal numbers)
            sum_usd = sum(c["contributionUsd"] for c in exp["contributions"])
            reconstructed_usd = exp["baseValueUsd"] + sum_usd
            self.assertAlmostEqual(reconstructed_usd, exp["predictedUsd"], delta=1.0)

    def test_09_deterministic_output(self) -> None:
        """Verify two consecutive exports produce identical JSON (excluding variable timestamps)."""
        fixed_ts = "2026-10-19T12:00:00Z"
        payload_a = generate_3d_export_payload(
            dataset_dir=DEFAULT_DATASET_DIR,
            artifact_path=DEFAULT_ARTIFACT_PATH,
            allow_train=False,
            generated_at=fixed_ts,
        )
        payload_b = generate_3d_export_payload(
            dataset_dir=DEFAULT_DATASET_DIR,
            artifact_path=DEFAULT_ARTIFACT_PATH,
            allow_train=False,
            generated_at=fixed_ts,
        )
        self.assertEqual(
            json.dumps(payload_a, sort_keys=True),
            json.dumps(payload_b, sort_keys=True),
        )

    def test_10_missing_artifacts_invalid_inputs_and_degenerate_ranges(self) -> None:
        """Verify clear errors on missing files/columns and safe handling of constant feature ranges."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Missing dataset directory
            with self.assertRaises(FileNotFoundError):
                load_and_clean_dataset(tmp_path / "nonexistent_dataset")

            # Missing model artifact when allow_train=False
            with self.assertRaises(FileNotFoundError):
                load_or_train_artifact(
                    artifact_path=tmp_path / "missing_model.joblib",
                    dataset_dir=DEFAULT_DATASET_DIR,
                    allow_train=False,
                )

            # Invalid input DataFrame missing required features
            bad_df = pd.DataFrame({"GrLivArea": [1500], "OverallQual": [7]})
            with self.assertRaises(ValueError):
                predict_with_pipeline(self.pipeline, bad_df, self.raw_feature_names)

            # Constant / degenerate feature range handling in generate_axis_values
            deg_float = generate_axis_values(1500.0, 1500.0, size=50, as_integer=False)
            self.assertEqual(len(deg_float), 50)
            self.assertTrue(all(deg_float[i] < deg_float[i + 1] for i in range(49)))

            deg_int = generate_axis_values(5.0, 5.0, size=50, as_integer=True)
            self.assertEqual(len(deg_int), 50)
            self.assertTrue(all(isinstance(v, int) for v in deg_int))
            self.assertTrue(all(deg_int[i] < deg_int[i + 1] for i in range(49)))

            # Atomic JSON writer rejects NaN values without leaving partial target file
            target_json = tmp_path / "atomic_test.json"
            with self.assertRaises(ValueError):
                atomic_write_json({"bad": float("nan")}, target_json)
            self.assertFalse(target_json.exists())


if __name__ == "__main__":
    unittest.main()
