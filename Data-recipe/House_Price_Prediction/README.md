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
pip install numpy pandas scikit-learn xgboost lightgbm catboost matplotlib seaborn
```

### Running the Notebook
```bash
jupyter notebook Data-recipe/House_Price_Prediction/House_Prices_Prediction_using_TFDF.ipynb
```

## Project Files
- `House_Prices_Prediction_using_TFDF.ipynb`: Executed notebook with complete residual diagnostic plots and benchmarks.
- `Dataset/train.csv` & `Dataset/test.csv`: Ames Housing raw tabular data.
- `submission.csv`: Final generated predictions formatted for competition evaluation.

## Limitations & Future Work
- **Temporal Stationarity:** Pricing data is historic (2006–2010); modern macroeconomic interest rate shifts would require external indexing.
- **Future Improvements:** Geospatial coordinate enrichment (geocoding neighborhood centroids) and Bayesian hyperparameter optimization (Optuna).

## License
MIT License. Developed by Vignesh K N.
