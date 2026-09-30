# Titanic Survival Prediction

Foundational supervised machine learning classification pipeline evaluating logistic regression, gradient boosted trees, and random forests on the Titanic passenger survival dataset.

## Overview

This project provides a foundational machine learning workflow traversing exploratory data analysis (EDA), missing value imputation, categorical encoding, feature scaling, and model evaluation across three classification algorithms.

## Key Capabilities

- **Data Cleaning & Imputation:** Handles missing age, cabin, and embarked values through statistical imputations.
- **Categorical Encoding:** One-hot encodes categorical passenger attributes (sex, passenger class, embarkation port).
- **Model Evaluation:** Compares linear, boosted, and bagged estimators on a held-out test split.
- **Submission Output:** Exports final predictions to `submission.csv`.

## Verified Test Accuracy Results

| Model Algorithm | Held-out Test Accuracy | Notes |
| :--- | :--- | :--- |
| **Logistic Regression** | 82.68% | Linear probabilistic baseline |
| **XGBoost Classifier** | 81.56% | Gradient boosted tree classifier |
| **Random Forest Classifier** | **85.47%** | Ensembled bagged decision trees (highest accuracy) |

## Setup & Execution

### Prerequisites
```bash
pip install numpy pandas matplotlib scikit-learn xgboost
```

### Running the Notebook
```bash
jupyter notebook Data-recipe/Titanic_Model/Titanic_model.ipynb
```

## Project Files
- `Titanic_model.ipynb`: Executed notebook with complete EDA and model training steps.
- `Dataset/train.csv` & `Dataset/test.csv`: Passenger datasets.
- `submission.csv`: Exported binary survival predictions.

## Limitations
- Small sample size (891 training records) subject to high variance on single train/test splits; k-fold cross-validation is recommended for future iterations.

## License
MIT License. Developed by Vignesh K N.
