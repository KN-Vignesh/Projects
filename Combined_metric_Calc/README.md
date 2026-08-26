# Combined Metric Calculation

## Description

This folder contains tools and a notebook to compute combined evaluation metrics across multiple experiments. Useful when aggregating metrics from cross-validation folds or combining multiple metric types into a single summary score (e.g., weighted F1 + accuracy).

## Requirements

- Python 3.8+
- pandas
- numpy
- scikit-learn

Install via pip:

```bash
pip install pandas numpy scikit-learn
```

## Execution & Usage

1. Place your per-run metric CSV/JSON files into the folder or point the notebook to their location.
2. Open the notebook in this folder:

```bash
jupyter notebook Combined_metric_Calc.ipynb
```

3. Notebook steps:
   - Load per-run metrics into a DataFrame
   - Normalize/align metric names
   - Compute aggregated metrics (mean/std) and combined scores using configurable weights
   - Export summary table and charts

## Example combined metric

CombinedScore = 0.6 * F1_macro + 0.4 * Accuracy

- Weights and metrics used are configurable in the notebook.
