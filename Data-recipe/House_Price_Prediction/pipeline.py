"""
Reproducible Ames House Price Prediction Pipeline & SHAP Explainability Module.

Extracts the exact feature engineering, preprocessing, 7-model base estimators,
and Ridge-meta StackingRegressor from `House_Prices_Prediction_using_TFDF.ipynb`
into a deterministic, importable module without changing model behavior.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from catboost import CatBoostRegressor
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, StackingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Lasso, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, median_absolute_error, r2_score
from sklearn.model_selection import KFold, cross_val_predict, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, RobustScaler

PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET_DIR = PROJECT_DIR / "Dataset"
DEFAULT_ARTIFACT_DIR = PROJECT_DIR / "artifacts"
DEFAULT_ARTIFACT_PATH = DEFAULT_ARTIFACT_DIR / "house_price_stacking_pipeline.joblib"

MODEL_VERSION = "1.0.0"
RANDOM_SEED = 42
CV_FOLDS = 5


class AmesFeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Domain-driven feature engineering transformer identical to Section 5
    of `House_Prices_Prediction_using_TFDF.ipynb`.
    """

    CALC_COLS: List[str] = [
        "TotalBsmtSF",
        "1stFlrSF",
        "2ndFlrSF",
        "FullBath",
        "HalfBath",
        "BsmtFullBath",
        "BsmtHalfBath",
        "WoodDeckSF",
        "OpenPorchSF",
        "EnclosedPorch",
        "3SsnPorch",
        "ScreenPorch",
        "PoolArea",
        "YearBuilt",
        "YearRemodAdd",
        "YrSold",
    ]

    ENGINEERED_COLS: List[str] = [
        "TotalSF",
        "TotalBath",
        "TotalPorchSF",
        "HouseAge",
        "RemodAge",
        "IsRemodeled",
        "HasPool",
        "HasGarage",
        "HasBsmt",
    ]

    # Maps each engineered feature to its constituent raw input features for attribution mapping
    ENGINEERED_RAW_PARENTS: Dict[str, List[str]] = {
        "TotalSF": ["TotalBsmtSF", "1stFlrSF", "2ndFlrSF"],
        "TotalBath": ["FullBath", "HalfBath", "BsmtFullBath", "BsmtHalfBath"],
        "TotalPorchSF": ["WoodDeckSF", "OpenPorchSF", "EnclosedPorch", "3SsnPorch", "ScreenPorch"],
        "HouseAge": ["YrSold", "YearBuilt"],
        "RemodAge": ["YrSold", "YearRemodAdd"],
        "IsRemodeled": ["YearRemodAdd", "YearBuilt"],
        "HasPool": ["PoolArea"],
        "HasGarage": ["GarageArea"],
        "HasBsmt": ["TotalBsmtSF"],
    }

    def __init__(self) -> None:
        pass

    def fit(self, X: pd.DataFrame, y: Optional[np.ndarray] = None) -> "AmesFeatureEngineer":
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if not isinstance(X, pd.DataFrame):
            raise TypeError("AmesFeatureEngineer expects a pandas DataFrame input.")
        X_out = X.copy()
        for col in X_out.columns:
            if X_out[col].dtype == object:
                X_out[col] = [np.nan if v is None else v for v in X_out[col]]

        # Fill calculation-critical missing values with 0
        for col in self.CALC_COLS:
            if col in X_out.columns:
                X_out[col] = pd.to_numeric(X_out[col], errors="coerce").fillna(0)

        # 1. Total Living Space Aggregation
        X_out["TotalSF"] = X_out["TotalBsmtSF"] + X_out["1stFlrSF"] + X_out["2ndFlrSF"]

        # 2. Total Bathrooms
        X_out["TotalBath"] = (
            X_out["FullBath"]
            + (0.5 * X_out["HalfBath"])
            + X_out["BsmtFullBath"]
            + (0.5 * X_out["BsmtHalfBath"])
        )

        # 3. Total Porch / Outdoor Entertaining Area
        X_out["TotalPorchSF"] = (
            X_out["WoodDeckSF"]
            + X_out["OpenPorchSF"]
            + X_out["EnclosedPorch"]
            + X_out["3SsnPorch"]
            + X_out["ScreenPorch"]
        )

        # 4. Temporal Features
        X_out["HouseAge"] = X_out["YrSold"] - X_out["YearBuilt"]
        X_out["RemodAge"] = X_out["YrSold"] - X_out["YearRemodAdd"]
        X_out["IsRemodeled"] = (X_out["YearRemodAdd"] != X_out["YearBuilt"]).astype(int)

        # 5. Amenity Presence Flags
        X_out["HasPool"] = (X_out["PoolArea"] > 0).astype(int)
        if "GarageArea" in X_out.columns:
            garage_area = pd.to_numeric(X_out["GarageArea"], errors="coerce").fillna(0)
            X_out["HasGarage"] = (garage_area > 0).astype(int)
        else:
            X_out["HasGarage"] = 0
        X_out["HasBsmt"] = (X_out["TotalBsmtSF"] > 0).astype(int)

        # Cast MSSubClass (dwelling type) to string so it is treated as categorical
        if "MSSubClass" in X_out.columns:
            X_out["MSSubClass"] = (
                pd.to_numeric(X_out["MSSubClass"], errors="coerce")
                .fillna(0)
                .astype(int)
                .astype(str)
            )

        return X_out


def compute_file_sha256(path: Path) -> str:
    """Compute hex SHA-256 digest of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_and_clean_dataset(dataset_dir: Path = DEFAULT_DATASET_DIR) -> Dict[str, Any]:
    """
    Load raw train.csv and test.csv, apply Dean De Cock's documented outlier filter
    ((GrLivArea > 4000) & (SalePrice < 300000)), and return cleaned matrices and metadata.
    """
    dataset_dir = Path(dataset_dir)
    train_path = dataset_dir / "train.csv"
    test_path = dataset_dir / "test.csv"

    if not train_path.exists():
        raise FileNotFoundError(f"Training dataset not found at: {train_path}")
    if not test_path.exists():
        raise FileNotFoundError(f"Test dataset not found at: {test_path}")

    raw_train_df = pd.read_csv(train_path, keep_default_na=True)
    raw_test_df = pd.read_csv(test_path, keep_default_na=True)

    required_train_cols = {"Id", "SalePrice", "GrLivArea", "OverallQual"}
    missing_req = required_train_cols - set(raw_train_df.columns)
    if missing_req:
        raise ValueError(f"train.csv is missing required columns: {sorted(missing_req)}")

    raw_train_rows = len(raw_train_df)

    # Outlier filter from Section 3 of the notebook
    outlier_mask = (raw_train_df["GrLivArea"] > 4000) & (raw_train_df["SalePrice"] < 300000)
    outlier_ids = raw_train_df.loc[outlier_mask, "Id"].astype(int).tolist()
    cleaned_train_df = raw_train_df.drop(raw_train_df[outlier_mask].index).reset_index(drop=True)

    raw_saleprice = cleaned_train_df["SalePrice"].astype(float).copy()
    y_train = np.log1p(raw_saleprice.values)
    train_ids = cleaned_train_df["Id"].astype(int).copy()

    X_train = cleaned_train_df.drop(columns=["Id", "SalePrice"]).copy()
    X_test = raw_test_df.drop(columns=["Id"]).copy()
    test_ids = raw_test_df["Id"].astype(int).copy()

    return {
        "raw_train_df": raw_train_df,
        "cleaned_train_df": cleaned_train_df,
        "raw_test_df": raw_test_df,
        "X_train": X_train,
        "y_train": y_train,
        "raw_saleprice": raw_saleprice,
        "train_ids": train_ids,
        "X_test": X_test,
        "test_ids": test_ids,
        "raw_train_rows": raw_train_rows,
        "cleaned_train_rows": len(cleaned_train_df),
        "outlier_ids": outlier_ids,
        "train_sha256": compute_file_sha256(train_path),
        "test_sha256": compute_file_sha256(test_path),
    }


def identify_feature_types(X_train: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Identify numeric and categorical feature names post-AmesFeatureEngineer."""
    fe = AmesFeatureEngineer()
    sample_eng = fe.fit_transform(X_train)
    numeric_features = sample_eng.select_dtypes(
        include=["int64", "float64", "int32", "float32", "number"]
    ).columns.tolist()
    numeric_set = set(numeric_features)
    categorical_features = [col for col in sample_eng.columns if col not in numeric_set]
    return numeric_features, categorical_features


def build_full_preprocessor(X_train: pd.DataFrame) -> Tuple[Pipeline, List[str], List[str]]:
    """Build the exact front-to-back preprocessing pipeline from Section 7 of the notebook."""
    numeric_features, categorical_features = identify_feature_types(X_train)

    num_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", RobustScaler()),
        ]
    )

    cat_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="constant", fill_value="None")),
            ("ohe", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, numeric_features),
            ("cat", cat_pipeline, categorical_features),
        ]
    )

    full_preprocessor = Pipeline(
        [
            ("feature_engineering", AmesFeatureEngineer()),
            ("preprocessor", preprocessor),
        ]
    )
    return full_preprocessor, numeric_features, categorical_features


def build_base_models() -> Dict[str, Any]:
    """Instantiate the 7 base regression models with the exact notebook hyperparameters."""
    return {
        "Ridge": Ridge(alpha=15.0),
        "Lasso": Lasso(alpha=0.0005, random_state=RANDOM_SEED),
        "ElasticNet": ElasticNet(alpha=0.0005, l1_ratio=0.85, random_state=RANDOM_SEED),
        "GBoost": GradientBoostingRegressor(
            n_estimators=1000,
            learning_rate=0.02,
            max_depth=4,
            max_features="sqrt",
            loss="huber",
            random_state=RANDOM_SEED,
        ),
        "XGBoost": xgb.XGBRegressor(
            n_estimators=1000,
            learning_rate=0.02,
            max_depth=3,
            subsample=0.7,
            colsample_bytree=0.7,
            random_state=RANDOM_SEED,
            n_jobs=-1,
        ),
        "LightGBM": lgb.LGBMRegressor(
            n_estimators=1000,
            learning_rate=0.02,
            num_leaves=15,
            subsample=0.7,
            colsample_bytree=0.7,
            random_state=RANDOM_SEED,
            n_jobs=-1,
            verbose=-1,
        ),
        "CatBoost": CatBoostRegressor(
            iterations=1000,
            learning_rate=0.02,
            depth=4,
            verbose=0,
            random_state=RANDOM_SEED,
        ),
    }


def build_stacking_pipeline(X_train: pd.DataFrame) -> Pipeline:
    """Build the complete preprocessing + StackingRegressor pipeline."""
    full_preprocessor, _, _ = build_full_preprocessor(X_train)
    models = build_base_models()
    estimators = [(name.lower(), model) for name, model in models.items()]

    stacking_model = StackingRegressor(
        estimators=estimators,
        final_estimator=Ridge(alpha=10.0),
        cv=CV_FOLDS,
        n_jobs=-1,
    )

    final_pipeline = Pipeline(
        [
            ("prep", full_preprocessor),
            ("stack", stacking_model),
        ]
    )
    return final_pipeline


def atomic_joblib_dump(obj: Any, target_path: Path) -> None:
    """Write a joblib artifact atomically so incomplete files are never left on disk."""
    target_path = Path(target_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=str(target_path.parent),
        prefix=f".{target_path.name}.",
        suffix=".tmp",
    )
    os.close(fd)
    try:
        joblib.dump(obj, tmp_path, compress=3)
        os.replace(tmp_path, target_path)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def train_and_evaluate_pipeline(dataset_dir: Path = DEFAULT_DATASET_DIR) -> Dict[str, Any]:
    """
    Execute the complete notebook training and 5-fold cross-validation evaluation workflow:
    1. Benchmark each of the 7 base models via 5-fold CV (`KFold(n_splits=5, shuffle=True, random_state=42)`)
       and collect out-of-fold base model predictions.
    2. Compute out-of-fold predictions (`oof_preds_log1p`) and fold-wise RMSLE for the StackingRegressor.
    3. Fit `final_pipeline` on the full cleaned training set `(X_train, y_train)`.
    """
    import warnings

    warnings.filterwarnings("ignore")

    data = load_and_clean_dataset(dataset_dir)
    X_train: pd.DataFrame = data["X_train"]
    y_train: np.ndarray = data["y_train"]

    kf = KFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_SEED)
    full_preprocessor, numeric_features, categorical_features = build_full_preprocessor(X_train)
    base_models = build_base_models()
    model_names = list(base_models.keys())

    n_samples = len(y_train)
    n_models = len(model_names)
    oof_base_preds = np.zeros((n_samples, n_models), dtype=float)
    fold_indices = np.zeros(n_samples, dtype=int)
    per_model_fold_rmsle: Dict[str, List[float]] = {name: [] for name in model_names}

    # Single 5-fold pass across all 7 base models (computes both base CV benchmarks and meta-features)
    splits = list(kf.split(X_train, y_train))
    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        fold_indices[val_idx] = fold_idx
        fold_prep = clone(full_preprocessor)
        Z_tr = fold_prep.fit_transform(X_train.iloc[train_idx], y_train[train_idx])
        Z_val = fold_prep.transform(X_train.iloc[val_idx])
        y_tr = y_train[train_idx]
        y_val = y_train[val_idx]

        for m_idx, name in enumerate(model_names):
            est = clone(base_models[name])
            est.fit(Z_tr, y_tr)
            val_pred = np.asarray(est.predict(Z_val), dtype=float)
            oof_base_preds[val_idx, m_idx] = val_pred
            fold_rmse = float(np.sqrt(mean_squared_error(y_val, val_pred)))
            per_model_fold_rmsle[name].append(fold_rmse)

    base_cv_benchmarks: Dict[str, Dict[str, Any]] = {}
    for name in model_names:
        scores = per_model_fold_rmsle[name]
        base_cv_benchmarks[name] = {
            "meanRmsle": float(np.mean(scores)),
            "stdRmsle": float(np.std(scores)),
            "foldRmsle": [float(v) for v in scores],
        }

    # Compute out-of-fold predictions for the Ridge(alpha=10.0) Stacking meta-learner
    oof_preds_log1p = np.zeros(n_samples, dtype=float)
    stack_fold_rmsle: List[float] = []
    for fold_idx, (train_idx, val_idx) in enumerate(splits):
        meta_est = Ridge(alpha=10.0)
        meta_est.fit(oof_base_preds[train_idx], y_train[train_idx])
        val_stack_pred = np.asarray(meta_est.predict(oof_base_preds[val_idx]), dtype=float)
        oof_preds_log1p[val_idx] = val_stack_pred
        stack_fold_rmsle.append(float(np.sqrt(mean_squared_error(y_train[val_idx], val_stack_pred))))

    # Fit final pipeline on entire cleaned training set
    final_pipeline = build_stacking_pipeline(X_train)
    final_pipeline.fit(X_train, y_train)

    return {
        "model_version": MODEL_VERSION,
        "random_seed": RANDOM_SEED,
        "cv_folds": CV_FOLDS,
        "train_sha256": data["train_sha256"],
        "test_sha256": data["test_sha256"],
        "raw_feature_names": X_train.columns.tolist(),
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "outlier_ids": data["outlier_ids"],
        "pipeline": final_pipeline,
        "base_cv_benchmarks": base_cv_benchmarks,
        "stack_cv_benchmark": {
            "meanRmsle": float(np.mean(stack_fold_rmsle)),
            "stdRmsle": float(np.std(stack_fold_rmsle)),
            "foldRmsle": stack_fold_rmsle,
        },
        "oof_preds_log1p": oof_preds_log1p,
        "oof_fold_indices": fold_indices,
    }


def load_or_train_artifact(
    artifact_path: Path = DEFAULT_ARTIFACT_PATH,
    dataset_dir: Path = DEFAULT_DATASET_DIR,
    allow_train: bool = True,
    force_retrain: bool = False,
) -> Dict[str, Any]:
    """
    Load the pre-serialized model bundle if available and valid; otherwise train
    and serialize it if `allow_train=True`.
    """
    artifact_path = Path(artifact_path)
    dataset_dir = Path(dataset_dir)
    data = load_and_clean_dataset(dataset_dir)

    if artifact_path.exists() and not force_retrain:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            bundle = joblib.load(artifact_path)
        required_keys = {
            "model_version",
            "train_sha256",
            "raw_feature_names",
            "pipeline",
            "oof_preds_log1p",
            "oof_fold_indices",
            "base_cv_benchmarks",
            "stack_cv_benchmark",
        }
        if (
            isinstance(bundle, dict)
            and required_keys.issubset(set(bundle.keys()))
            and bundle["train_sha256"] == data["train_sha256"]
            and bundle["raw_feature_names"] == data["X_train"].columns.tolist()
        ):
            return bundle

    if not allow_train:
        raise FileNotFoundError(
            f"Serialized model artifact not found or out of date at '{artifact_path}'. "
            "Run `python3 Data-recipe/House_Price_Prediction/scripts/export_3d_data.py` "
            "without `--no-train-if-missing` to train and serialize the model artifact."
        )

    bundle = train_and_evaluate_pipeline(dataset_dir)
    atomic_joblib_dump(bundle, artifact_path)
    return bundle


def predict_with_pipeline(
    pipeline: Pipeline,
    X_input: pd.DataFrame,
    raw_feature_names: List[str],
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Validate input columns, enforce original feature order, and return
    (log1p_predictions, usd_predictions).
    """
    if not isinstance(X_input, pd.DataFrame):
        raise TypeError("X_input must be a pandas DataFrame.")

    missing_cols = [c for c in raw_feature_names if c not in X_input.columns]
    if missing_cols:
        raise ValueError(f"Input DataFrame is missing required model features: {missing_cols[:10]}")

    X_ordered = X_input[raw_feature_names].copy()
    for col in X_ordered.columns:
        if X_ordered[col].dtype == object:
            X_ordered[col] = [np.nan if v is None else v for v in X_ordered[col]]
    log_preds = np.asarray(pipeline.predict(X_ordered), dtype=float)
    usd_preds = np.expm1(log_preds)
    return log_preds, usd_preds


def compute_baseline_features(X_train: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute representative baseline values for all 79 raw input features derived
    from the cleaned training dataset:
    - Numerical features: training median (rounded to integer if the column is integer-valued in training data).
    - Categorical features: most frequent non-null category (mode), or 'None' if predominantly missing.
    """
    baseline: Dict[str, Any] = {}
    for col in X_train.columns:
        series = X_train[col]
        if pd.api.types.is_numeric_dtype(series) and col != "MSSubClass":
            non_null = series.dropna()
            med = float(non_null.median()) if len(non_null) > 0 else 0.0
            # Check if all non-null values in training data are integer-valued
            is_int_col = bool(
                pd.api.types.is_integer_dtype(series)
                or (len(non_null) > 0 and np.all(np.isclose(non_null % 1, 0)))
            )
            baseline[col] = int(round(med)) if is_int_col else float(med)
        elif col == "MSSubClass":
            non_null = series.dropna().astype(int)
            mode_val = int(non_null.mode().iloc[0]) if len(non_null) > 0 else 20
            baseline[col] = mode_val
        else:
            # Categorical string feature: if >50% missing (e.g. Alley, PoolQC, Fence, MiscFeature),
            # use None (which the preprocessor imputes as 'None'), else use mode.
            null_frac = float(series.isna().mean())
            non_null = series.dropna().astype(str)
            if null_frac > 0.5 or len(non_null) == 0:
                baseline[col] = None
            else:
                baseline[col] = str(non_null.mode().iloc[0])
    return baseline


def get_preprocessed_feature_groups(
    full_preprocessor: Pipeline,
    numeric_features: List[str],
    categorical_features: List[str],
) -> Tuple[List[str], Dict[str, List[int]]]:
    """
    Map each of the 88 engineered features (44 numeric + 44 categorical) to its
    column indices in the ColumnTransformer's transformed matrix Z.
    """
    col_transformer: ColumnTransformer = full_preprocessor.named_steps["preprocessor"]
    ohe: OneHotEncoder = col_transformer.named_transformers_["cat"].named_steps["ohe"]

    transformed_names: List[str] = []
    feature_to_indices: Dict[str, List[int]] = {}

    idx = 0
    for num_col in numeric_features:
        transformed_names.append(num_col)
        feature_to_indices[num_col] = [idx]
        idx += 1

    for cat_col, categories in zip(categorical_features, ohe.categories_):
        indices: List[int] = []
        for cat_val in categories:
            transformed_names.append(f"{cat_col}_{cat_val}")
            indices.append(idx)
            idx += 1
        feature_to_indices[cat_col] = indices

    return transformed_names, feature_to_indices


def compute_stacking_shap_explanations(
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    X_explain: pd.DataFrame,
    background_size: int = 200,
    additivity_tolerance: float = 1e-5,
) -> List[Dict[str, Any]]:
    """
    Compute exact additive SHAP explanations for the fitted StackingRegressor.

    Mathematical formulation:
    - Let Z = full_preprocessor.transform(X) in R^{N x D}.
    - The StackingRegressor final_estimator is Ridge(alpha=10.0) with weights w_1..w_7 and intercept w_0:
        y_hat_log1p(Z) = w_0 + sum_{k=1}^7 w_k * f_k(Z)
    - For linear base estimators (Ridge, Lasso, ElasticNet), exact linear SHAP values on Z are:
        phi^{(k)}_j(z) = beta^{(k)}_j * (z_j - E[z_j]),  E[f_k(Z)] = f_k(E[Z])
    - For tree base estimators (GBoost, XGBoost, LightGBM, CatBoost), `shap.TreeExplainer`
      (and native XGBoost C++ `pred_contribs=True` TreeSHAP) computes exact TreeSHAP values phi^{(k)}_j(z)
      satisfying sum_j phi^{(k)}_j(z) + E[f_k(Z)] = f_k(z).
    - By linearity of Shapley values, the ensemble SHAP value for preprocessed column j is:
        Phi_j(z) = sum_{k=1}^7 w_k * phi^{(k)}_j(z)
      with ensemble base value:
        base_log1p = w_0 + sum_{k=1}^7 w_k * E[f_k(Z)]
    - By Shapley coalition additivity, summing Phi_j(z) across the one-hot encoded indicator
      columns of each categorical feature yields exact attributions over the 88 engineered features,
      and distributing derived engineered feature attributions equally to their constituent raw
      features yields exact attributions over all 79 raw input features such that:
        base_log1p + sum_{f in 79 raw features} Phi_raw_f(x) == y_hat_log1p(x).
    """
    full_preprocessor: Pipeline = pipeline.named_steps["prep"]
    stacking_model: StackingRegressor = pipeline.named_steps["stack"]
    meta_ridge: Ridge = stacking_model.final_estimator_
    meta_weights: np.ndarray = np.asarray(meta_ridge.coef_, dtype=float)
    meta_intercept: float = float(meta_ridge.intercept_)

    numeric_features, categorical_features = identify_feature_types(X_train)
    _, feature_to_indices = get_preprocessed_feature_groups(
        full_preprocessor, numeric_features, categorical_features
    )

    # Select a deterministic background subsample from X_train
    rng = np.random.default_rng(RANDOM_SEED)
    bg_indices = rng.choice(len(X_train), size=min(background_size, len(X_train)), replace=False)
    bg_indices.sort()
    X_bg = X_train.iloc[bg_indices].copy()

    Z_bg = np.asarray(full_preprocessor.transform(X_bg), dtype=float)
    Z_explain = np.asarray(full_preprocessor.transform(X_explain), dtype=float)
    Z_bg_mean = np.mean(Z_bg, axis=0)

    n_samples, n_transformed = Z_explain.shape
    ensemble_shap_Z = np.zeros((n_samples, n_transformed), dtype=float)
    ensemble_base_log1p = meta_intercept

    for weight, (est_name, fitted_est) in zip(
        meta_weights, zip([name for name, _ in stacking_model.estimators], stacking_model.estimators_)
    ):
        est_preds = np.asarray(fitted_est.predict(Z_explain), dtype=float)
        if hasattr(fitted_est, "coef_"):
            # Exact closed-form linear SHAP for Ridge, Lasso, ElasticNet
            coefs = np.asarray(fitted_est.coef_, dtype=float).reshape(1, -1)
            est_base = float(fitted_est.predict(Z_bg_mean.reshape(1, -1))[0])
            est_shap = (Z_explain - Z_bg_mean.reshape(1, -1)) * coefs
        elif isinstance(fitted_est, xgb.XGBRegressor):
            # Native C++ exact TreeSHAP via XGBoost booster pred_contribs=True
            contribs = np.asarray(
                fitted_est.get_booster().predict(xgb.DMatrix(Z_explain), pred_contribs=True),
                dtype=float,
            )
            est_shap = contribs[:, :-1]
            implied_bases = est_preds - np.sum(est_shap, axis=1)
            if np.max(np.abs(implied_bases - np.mean(implied_bases))) > 1e-4:
                raise AssertionError(
                    f"XGBoost TreeSHAP non-constant base value detected: "
                    f"max_dev={np.max(np.abs(implied_bases - np.mean(implied_bases))):.8e}"
                )
            est_base = float(np.mean(implied_bases))
        else:
            # Exact TreeSHAP for GBoost, LightGBM, CatBoost using shap.TreeExplainer
            explainer = shap.TreeExplainer(fitted_est)
            est_shap = np.asarray(explainer.shap_values(Z_explain, check_additivity=False), dtype=float)
            # Verify that (est_preds - sum(est_shap)) is constant across all samples (exact TreeSHAP additivity)
            implied_bases = est_preds - np.sum(est_shap, axis=1)
            if np.max(np.abs(implied_bases - np.mean(implied_bases))) > 1e-4:
                raise AssertionError(
                    f"TreeSHAP non-constant base value detected for {est_name}: "
                    f"max_dev={np.max(np.abs(implied_bases - np.mean(implied_bases))):.8e}"
                )
            est_base = float(np.mean(implied_bases))

        ensemble_shap_Z += weight * est_shap
        ensemble_base_log1p += weight * est_base

    # Collapse one-hot encoded columns into the 88 engineered features
    engineered_feature_names = numeric_features + categorical_features
    engineered_shap = {
        feat: np.sum(ensemble_shap_Z[:, idxs], axis=1)
        for feat, idxs in feature_to_indices.items()
    }

    # Map the 88 engineered features back to the 79 raw input features preserving exact additivity
    raw_feature_names = X_train.columns.tolist()
    raw_shap_matrix = np.zeros((n_samples, len(raw_feature_names)), dtype=float)
    raw_col_idx = {col: i for i, col in enumerate(raw_feature_names)}

    for feat, vals in engineered_shap.items():
        if feat in raw_col_idx:
            raw_shap_matrix[:, raw_col_idx[feat]] += vals
        elif feat in AmesFeatureEngineer.ENGINEERED_RAW_PARENTS:
            parents = [
                p for p in AmesFeatureEngineer.ENGINEERED_RAW_PARENTS[feat] if p in raw_col_idx
            ]
            share = vals / len(parents)
            for p in parents:
                raw_shap_matrix[:, raw_col_idx[p]] += share
        else:
            raise KeyError(f"Unmapped engineered feature during SHAP attribution: {feat}")

    pred_log1p, pred_usd = predict_with_pipeline(pipeline, X_explain, raw_feature_names)
    base_usd = float(np.expm1(ensemble_base_log1p))

    explanations: List[Dict[str, Any]] = []
    for i in range(n_samples):
        sample_shap_log1p = raw_shap_matrix[i]
        shap_sum_log1p = float(np.sum(sample_shap_log1p))
        reconstructed_log1p = float(ensemble_base_log1p + shap_sum_log1p)
        target_log1p = float(pred_log1p[i])
        target_usd = float(pred_usd[i])
        discrepancy_log1p = abs(reconstructed_log1p - target_log1p)
        verified = bool(discrepancy_log1p <= additivity_tolerance)

        if not verified:
            raise AssertionError(
                f"SHAP additivity check failed for sample {i}: "
                f"reconstructed={reconstructed_log1p:.8f}, predicted={target_log1p:.8f}, "
                f"diff={discrepancy_log1p:.8e} > tol={additivity_tolerance:.8e}"
            )

        # Smooth path-integral scaling factor from log1p space to USD space so
        # baseValueUsd + sum(contributionUsd) == predictedUsd
        delta_log1p = target_log1p - ensemble_base_log1p
        delta_usd = target_usd - base_usd
        usd_scale = (delta_usd / delta_log1p) if abs(delta_log1p) > 1e-12 else float(np.exp(ensemble_base_log1p))

        row_series = X_explain.iloc[i]
        contributions: List[Dict[str, Any]] = []
        for j, col in enumerate(raw_feature_names):
            raw_val = row_series[col]
            if pd.isna(raw_val):
                clean_val: Any = None
            elif isinstance(raw_val, (np.integer, int)):
                clean_val = int(raw_val)
            elif isinstance(raw_val, (np.floating, float)):
                clean_val = int(raw_val) if float(raw_val).is_integer() else float(raw_val)
            else:
                clean_val = str(raw_val)

            c_log = float(sample_shap_log1p[j])
            c_usd = float(c_log * usd_scale)
            contributions.append(
                {
                    "feature": col,
                    "value": clean_val,
                    "shapLog1p": round(c_log, 8),
                    "contributionUsd": round(c_usd, 2),
                }
            )

        top_contributions = sorted(
            contributions, key=lambda item: abs(item["shapLog1p"]), reverse=True
        )[:12]

        explanations.append(
            {
                "explainerType": "ExactStackingExplainer(LinearSHAP[Ridge,Lasso,ElasticNet] + TreeSHAP[GBoost,XGBoost,LightGBM,CatBoost] -> RidgeMeta)",
                "targetScale": "log1p_usd",
                "outputUnit": "USD",
                "backgroundSampleCount": len(X_bg),
                "baseValueLog1p": round(float(ensemble_base_log1p), 8),
                "baseValueUsd": round(base_usd, 2),
                "predictedLog1p": round(target_log1p, 8),
                "predictedUsd": round(target_usd, 2),
                "additivitySumLog1p": round(reconstructed_log1p, 8),
                "additivityDiscrepancyLog1p": float(discrepancy_log1p),
                "additivityTolerance": float(additivity_tolerance),
                "additivityVerified": verified,
                "topContributions": top_contributions,
                "contributions": contributions,
            }
        )

    return explanations
