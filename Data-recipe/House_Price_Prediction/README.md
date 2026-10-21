# Ames House Price Prediction & Multi-Model Stacking Regressor

Advanced tabular regression pipeline on the Ames Housing dataset featuring custom feature engineering, 5-fold cross-validation benchmarking across 7 algorithms, and a meta-stacking ensemble achieving 0.1081 RMSLE.

## Overview

This project implements an end-to-end regression pipeline designed to predict residential property sale prices. Rather than relying on default model parameters, the pipeline features domain-specific feature engineering (`AmesFeatureEngineer`), skewed target log-transformation, 5-fold cross-validation across seven diverse regression algorithms (Ridge, Lasso, ElasticNet, GradientBoosting, XGBoost, LightGBM, CatBoost), and a meta-level `StackingRegressor` with out-of-fold blending.

## Problem

Property valuation involves complex tabular challenges:
1. **High Cardinality & Interaction:** The Ames dataset contains 79 explanatory variables with extensive multi-collinearity (e.g. square footage across basement, first floor, and second floor).
2. **Target Skewness:** Sale prices are heavily right-skewed, violating ordinary least squares normality assumptions.
3. **Algorithm Divergence:** Linear regularized models and tree-based gradient boosters excel at different sub-distributions of the feature space.

## Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │             Raw Ames Housing Data (79 Features)        │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             AmesFeatureEngineer Pipeline               │
       │       - TotalSquareFeet = GrLivArea + TotalBsmtSF      │
       │       - TotalBathrooms = FullBath + 0.5*HalfBath...    │
       │       - HouseAge & RemodAge at time of sale            │
       │       - log1p Target Transformation for SalePrice      │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │             5-Fold Cross-Validation Benchmarking       │
       │                                                        │
       │  Ridge      Lasso     ElasticNet   GBoost   XGBoost... │
       │ (0.1138)   (0.1118)    (0.1119)   (0.1123)  (0.1139)   │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │         Multi-Level Stacking Regressor (Meta-Model)    │
       │       - Base Estimators: 7 cross-validated models      │
       │       - Final Meta-Estimator: RidgeCV with L2 penalty  │
       │       - Final Ensemble RMSLE: 0.1081                   │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │              Predictions & Submission File             │
       │                 (Inverted expm1 prices)                │
       └────────────────────────────────────────────────────────┘
```

## Technology Stack

- **Languages & Frameworks:** Python, Scikit-learn, CatBoost, XGBoost, LightGBM, NumPy, Pandas, Matplotlib, Seaborn.
- **Dataset:** Kaggle House Prices: Advanced Regression Techniques (1,460 training rows, 1,459 test rows).

## Verified 5-Fold Cross-Validation Benchmark

Models were evaluated using 5-fold cross-validation scored on Root Mean Squared Logarithmic Error (RMSLE):

| Model Algorithm | Mean RMSLE | Standard Deviation | Notes |
| :--- | :--- | :--- | :--- |
| **Ridge Regression** | 0.1138 | 0.0087 | L2 Regularization baseline |
| **Lasso Regression** | 0.1118 | 0.0067 | L1 Regularization with feature selection |
| **ElasticNet** | 0.1119 | 0.0067 | Convex combination of L1 and L2 |
| **Gradient Boosting (GBoost)** | 0.1123 | 0.0082 | Sequential residual boosting |
| **XGBoost** | 0.1139 | 0.0070 | Extreme Gradient Boosting with shrinkage |
| **CatBoost** | 0.1144 | 0.0073 | Categorical-aware symmetric tree boosting |
| **LightGBM** | 0.1205 | 0.0091 | Leaf-wise tree growth gradient boosting |
| **Stacking Regressor (Ensemble)** | **0.1081** | **0.0071** | **Combined 7 base models + RidgeCV meta-learner** |

*Key Takeaway: The multi-level Stacking Regressor outperformed every single individual model, reducing error from 0.1118 (best individual: Lasso) down to 0.1081.*

## Setup & Execution

### Prerequisites
```bash
pip install -r Data-recipe/House_Price_Prediction/requirements.txt
```

### Running the Notebook
```bash
jupyter notebook Data-recipe/House_Price_Prediction/House_Prices_Prediction_using_TFDF.ipynb
```

### Generating the 3D Prediction Surface & Explainability JSON Asset
```bash
# Run from the repository root (loads cached model artifact or trains & serializes on first run)
python3 Data-recipe/House_Price_Prediction/scripts/export_3d_data.py

# Or via the root convenience wrapper:
python3 scripts/export_3d_data.py

# Force full model retraining and artifact re-serialization before exporting:
python3 Data-recipe/House_Price_Prediction/scripts/export_3d_data.py --retrain

# Fail fast if the serialized model artifact is missing (CI/CD verification mode):
python3 Data-recipe/House_Price_Prediction/scripts/export_3d_data.py --no-train-if-missing
```

### Running the Automated Test Suite
```bash
python3 -m unittest Data-recipe/House_Price_Prediction/tests/test_export_3d_data.py -v
# or with pytest:
pytest Data-recipe/House_Price_Prediction/tests/test_export_3d_data.py -v
```

---

## 3D Prediction Surface & Static Portfolio Data Export (`house_price_3d.json`)

To power the interactive 3D prediction surface in the React + TypeScript + Three.js portfolio (`Project-Portfolio`) without requiring a live Python inference backend, this project exports a validated, precomputed static JSON asset (`house_price_3d.json`).

### 1. Model Pipeline & Reproducible Serialization
- **Source Pipeline (`pipeline.py`):** Faithfully encapsulates the exact workflow from `House_Prices_Prediction_using_TFDF.ipynb`:
  1. **Outlier Sanitization:** Removes the 2 documented agricultural anomalies where `GrLivArea > 4000` sq ft and `SalePrice < $300,000` (`Id` 524 and `Id` 1299), yielding `1,458` cleaned training rows across `79` raw input features.
  2. **Target Transformation:** Trains on `y_train = np.log1p(SalePrice)` and inverts predictions via `np.expm1(y_pred)` into `USD ($)`.
  3. **Domain Feature Engineering (`AmesFeatureEngineer`):** Computes 9 derived features (`TotalSF`, `TotalBath`, `TotalPorchSF`, `HouseAge`, `RemodAge`, `IsRemodeled`, `HasPool`, `HasGarage`, `HasBsmt`) and casts `MSSubClass` to categorical string (`88` engineered features total: `44` numeric, `44` categorical).
  4. **Preprocessing (`ColumnTransformer`):** Applies `SimpleImputer(strategy='median')` + `RobustScaler()` to the 44 numerical features, and `SimpleImputer(strategy='constant', fill_value='None')` + `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` to the 44 categorical features (`298` preprocessed columns).
  5. **Stacking Ensemble (`StackingRegressor`):** Combines 7 base estimators (`Ridge`, `Lasso`, `ElasticNet`, `GradientBoostingRegressor`, `XGBoost`, `LightGBM`, `CatBoost`) with a `Ridge(alpha=10.0)` meta-estimator using 5-fold cross-validation (`random_state=42`).
- **Serialized Artifact (`artifacts/house_price_stacking_pipeline.joblib`):** Stores the fitted `final_pipeline`, 5-fold out-of-fold validation predictions, fold assignments, CV benchmark scores, and dataset SHA-256 checksums so subsequent exports and tests load in `<0.5s` without retraining.

### 2. Surface Grid Generation & Three.js Matrix Ordering
- **Selected Surface Axes (`50 × 50` = 2,500 pipeline evaluations):**
  - **X-Axis (`GrLivArea`):** Above-grade living area in square feet (`sq_ft`), spanning the cleaned training range `334` to `4,476` sq ft across 50 strictly increasing integer coordinates (`r = 0.72` with `log1p(SalePrice)`).
  - **Y-Axis (`OverallQual`):** Overall material and finish quality (`rating_1_to_10`), spanning `1.0` to `10.0` across 50 strictly increasing coordinates (`r = 0.82` with `log1p(SalePrice)`), with discrete integer ratings `1..10` documented in `yAxis.validDiscreteRatings`.
- **Baseline Feature Fixing (`surface.baselineFeatures`):** All remaining 77 raw input features are held fixed at representative values derived from the cleaned training dataset:
  - **Numerical & Ordinal Features:** Cleaned training median (preserved as `int` for integer-valued columns, e.g., `YearBuilt = 1973`, `FullBath = 2`, `GarageCars = 2`, `TotalBsmtSF = 991`).
  - **Categorical Features:** Cleaned training mode (e.g., `Neighborhood = "NAmes"`, `MSZoning = "RL"`, `ExterQual = "TA"`), or `null` (imputed as `"None"`) where >50% of training observations have no such amenity (`Alley`, `PoolQC`, `Fence`, `MiscFeature`).
- **Matrix Indexing Convention (`row_major_y_outer_x_inner`):**
  - `zMatrixUsd[row_idx][col_idx]` (and `zMatrixLog1p[row_idx][col_idx]`) stores the genuine pipeline prediction for `OverallQual = yAxis.values[row_idx]` and `GrLivArea = xAxis.values[col_idx]`.
  - For a Three.js `PlaneGeometry(width, depth, 49, 49)`, vertex `k = row_idx * 50 + col_idx` maps directly to `(x = xAxis.values[col_idx], y_elevation = zMatrixUsd[row_idx][col_idx], z = yAxis.values[row_idx])`.
  - Every grid cell is computed by executing `final_pipeline.predict()`—never via post-hoc surface interpolation.

### 3. Representative House Examples, Evaluation Metrics & Exact SHAP Explainability
- **Held-Out Evaluation Split (`evaluation`):**
  - Uses 5-fold cross-validation out-of-fold (`cross_val_predict` with `KFold(n_splits=5, shuffle=True, random_state=42)`) across all `1,458` cleaned observations. Every point in `evaluation.actualVsPredicted` is predicted by a model trained strictly on the other 4 folds.
  - Reports held-out metrics in both logarithmic and USD spaces: `rmsle`, `cvMeanRmsle`, `cvStdRmsle`, `maeUsd`, `rmseUsd`, `medianAeUsd`, `mapePct`, `r2Usd`, and `r2Log1p`.
- **Representative Real Examples (`examples`):**
  - Exports 10 real observations from the dataset spanning the price distribution (10th, 50th, 75th, 90th, 99th percentiles), off-diagonal surface corners (compact high-grade and spacious modest-grade homes), a historic remodeled residence, a median held-out error benchmark, and a 95th-percentile high-residual diagnostic case.
  - Each example records both the full-pipeline prediction (`predictedPriceUsd`) and the held-out out-of-fold prediction (`oofPredictedPriceUsd`) alongside its CV fold index.
- **Exact Additive SHAP Attributions (`examples[*].explainability`):**
  - Exploits the linearity of the `StackingRegressor`'s `Ridge(alpha=10.0)` meta-estimator ($w_0 + \sum_{k=1}^7 w_k f_k(Z)$) to combine exact closed-form LinearSHAP values for `Ridge`, `Lasso`, and `ElasticNet` with exact interventional `shap.TreeExplainer` values for `GBoost`, `XGBoost`, `LightGBM`, and `CatBoost`.
  - One-hot encoded categorical indicator columns are summed back to their parent features by Shapley coalition additivity, and the 9 engineered features' attributions are distributed equally to their constituent raw input columns.
  - **Verified Additivity Identity:** For every exported example, `baseValueLog1p + sum(shapLog1p) == predictedLog1p` holds to machine precision (`< 1e-7`, verified against tolerance `1e-5`). Smooth path-integral scaling also provides dollar attributions (`contributionUsd`) summing to `predictedUsd - baseValueUsd`.

### 4. JSON Schema, Published Asset Paths & Synchronization
- **JSON Schema:** `Data-recipe/House_Price_Prediction/schema/house_price_3d.schema.json` (Draft 2020-12) and runtime validator `Data-recipe/House_Price_Prediction/schema_validator.py`.
- **Published Asset Locations:**
  - Portfolio Asset Path: `portfolio/assets/house_price_3d.json`
  - Project-Local Asset Path: `Data-recipe/House_Price_Prediction/assets/house_price_3d.json`
  - Portfolio Registry: `portfolio/projects.json`
  - Target Raw GitHub URLs (once committed & pushed to `KN-Vignesh/Projects` `main`):
    - `https://raw.githubusercontent.com/KN-Vignesh/Projects/main/portfolio/assets/house_price_3d.json`
    - `https://raw.githubusercontent.com/KN-Vignesh/Projects/main/Data-recipe/House_Price_Prediction/assets/house_price_3d.json`
    - `https://raw.githubusercontent.com/KN-Vignesh/Projects/main/portfolio/projects.json`
- **Limitations of Precomputed Data & Synchronization:**
  - Because the 3D surface varies `GrLivArea` and `OverallQual` while holding the other 77 features at their training baselines, real houses (which differ in neighborhood, basement area, lot size, garage capacity, and build year) naturally sit above or below the baseline surface slice. The exported `examples` include full 79-feature SHAP breakdowns to explain this exact gap between the 2D baseline slice and each real house's multi-dimensional prediction.
  - Whenever `train.csv` or model hyperparameters in `pipeline.py` are updated, run `python3 Data-recipe/House_Price_Prediction/scripts/export_3d_data.py --retrain` followed by `pytest Data-recipe/House_Price_Prediction/tests/test_export_3d_data.py` to atomically regenerate and validate the JSON asset.

## Project Files
- `House_Prices_Prediction_using_TFDF.ipynb`: Executed notebook with complete residual diagnostic plots and benchmarks.
- `pipeline.py`: Reproducible training, serialization, prediction, and exact Stacking SHAP explainability module.
- `schema_validator.py` & `schema/house_price_3d.schema.json`: JSON Schema and numerical invariant validator.
- `scripts/export_3d_data.py`: Deterministic, atomic CLI exporter for `house_price_3d.json`.
- `assets/house_price_3d.json`: Generated 3D surface, examples, SHAP, and evaluation asset.
- `tests/test_export_3d_data.py`: Automated unit and integration test suite.
- `Dataset/train.csv` & `Dataset/test.csv`: Ames Housing raw tabular data.
- `submission.csv`: Final generated predictions formatted for competition evaluation.

## Limitations & Future Work
- **Temporal Stationarity:** Pricing data is historic (2006–2010); modern macroeconomic interest rate shifts would require external indexing.
- **Future Improvements:** Geospatial coordinate enrichment (geocoding neighborhood centroids) and Bayesian hyperparameter optimization (Optuna).

## License
MIT License. Developed by Vignesh K N.

