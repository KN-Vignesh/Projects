<div class="vp-project">

<div class="vp-project-header">
  <div class="vp-project-number">PROJECT_001</div>
  <div>TRADITIONAL ML / PRODUCTION API</div>
</div>

# INTELLIGENT CUSTOMER<br>CHURN PREDICTION

## A reproducible customer-risk workflow that turns tabular data into an API-ready prediction system.

<div class="vp-tags">
  <span>PYTHON</span>
  <span>SCIKIT-LEARN</span>
  <span>FASTAPI</span>
  <span>DOCKER</span>
  <span>CLASSIFICATION</span>
</div>

<div class="vp-context">
  <div><small>ROLE IN PORTFOLIO</small><b>TRADITIONAL ML FOUNDATION</b></div>
  <div><small>PROBLEM TYPE</small><b>BINARY CLASSIFICATION</b></div>
  <div><small>SOURCE</small><b>GITHUB REPOSITORY</b></div>
</div>

<div class="vp-log">
  <div class="vp-log-head">SYSTEM THREAD / CHURN_001</div>
  <div class="vp-log-row"><span>DATASET</span><b>TELCO CUSTOMER CHURN</b></div>
  <div class="vp-log-row"><span>PIPELINE</span><b>EDA → PREPROCESSING → MODEL COMPARISON</b></div>
  <div class="vp-log-row"><span>MODELS</span><b>LOGISTIC REGRESSION · RANDOM FOREST · XGBOOST</b></div>
  <div class="vp-log-row"><span>EVALUATION</span><b>ACCURACY · PRECISION · RECALL · F1 · ROC-AUC</b></div>
  <div class="vp-log-row"><span>API</span><b>FASTAPI + OPENAPI DOCS</b></div>
  <div class="vp-log-row"><span>CONTAINER</span><b>DOCKER</b></div>
</div>

## 01 — THE PROBLEM

The system is designed around a practical business question:

**Which customers show a higher risk of leaving the service?**

The project treats churn prediction as a complete engineering workflow rather than only a notebook model. The objective is to make the path from customer data to prediction reproducible and usable through an application interface.

## 02 — WHY THIS APPROACH

A tabular classification task is a useful foundation for production-oriented AI engineering because it exposes the engineering surfaces that remain important even when models become more advanced:

- data quality
- feature preparation
- leakage-safe preprocessing
- train/test separation
- model comparison
- metric selection
- API packaging
- containerization

The repository compares multiple classical models instead of treating a single algorithm as the answer.

## 03 — DATA

The source workflow uses the Telco Customer Churn dataset.

The pipeline is structured around the common tabular preparation steps used throughout the portfolio's ML foundation work:

**missing values → categorical handling → numerical scaling → train/test split → model training → evaluation**

The repository keeps the dataset as an input artifact and generates the model artifact through the training workflow.

## 04 — ARCHITECTURE

<div class="vp-architecture">
  <div class="vp-architecture-head">
    <span>PIPE_001</span>
    <span>END-TO-END ML APPLICATION</span>
  </div>

  <div class="vp-pipeline">
    <div class="vp-pipeline-step"><span>01</span><b>CUSTOMER DATA</b></div>
    <div class="vp-pipeline-step"><span>02</span><b>VALIDATION + PREPROCESSING</b></div>
    <div class="vp-pipeline-step"><span>03</span><b>MODEL COMPARISON</b></div>
    <div class="vp-pipeline-step"><span>04</span><b>FASTAPI</b></div>
    <div class="vp-pipeline-step"><span>05</span><b>WEB UI / DOCKER</b></div>
  </div>
</div>

## 05 — IMPLEMENTATION

The project separates the main engineering responsibilities instead of embedding everything inside a single notebook.

The repository provides a training flow that produces the model artifact, an API layer that exposes prediction behavior, and a lightweight frontend for interacting with the API.

This separation creates a clearer boundary between:

**training code → persisted model → inference service → user interface**

## 06 — MODEL COMPARISON

The current workflow compares:

**Logistic Regression**

A simple and interpretable classification baseline.

**Random Forest**

A nonlinear tree-based ensemble useful for structured feature interactions.

**XGBoost**

A gradient-boosted tree model commonly used for strong tabular classification performance.

The final model should be selected from measured validation behavior rather than from the algorithm name alone.

## 07 — EVALUATION

The repository tracks:

**Accuracy · Precision · Recall · F1 Score · ROC-AUC**

The portfolio intentionally does not present invented benchmark values here. The authoritative results are produced by running the repository's training workflow against the dataset.

This keeps the project page aligned with the actual experiment rather than turning a static portfolio statement into an unsupported performance claim.

## 08 — API / APPLICATION

The inference layer uses FastAPI.

The intended flow is:

**frontend input → HTTP request → FastAPI validation → loaded model → prediction → JSON response**

FastAPI also exposes OpenAPI documentation through `/docs`, which makes the service easier to inspect and integrate.

## 09 — DEPLOYMENT

The project is container-ready through Docker.

The current repository README describes an Azure deployment path; the portfolio treats the container as the portable deployment unit so the same application can be moved to a compatible cloud or free hosting platform without rewriting the core inference service.

## 10 — ENGINEERING DECISIONS

**Keep preprocessing close to the model path.**  
Inference should use the same transformation assumptions as training.

**Compare multiple baselines.**  
A model is a choice supported by evidence, not a default.

**Separate inference from presentation.**  
The API should remain usable independently of the frontend.

**Containerize the application.**  
The environment should be reproducible outside the developer machine.

## 11 — LIMITATIONS

This project is a foundation for production-oriented ML engineering, not a complete production churn platform.

Important follow-up surfaces include:

- dataset drift monitoring
- calibration and threshold selection
- model explainability
- automated tests around inference
- CI/CD
- structured logging
- deployment observability
- retraining strategy

These are the natural next engineering steps rather than claims about functionality already implemented.

## 12 — FUTURE IMPROVEMENTS

**NEXT_001** — Add model explanation with feature-level attribution.

**NEXT_002** — Add evaluation reports that persist experiment metadata.

**NEXT_003** — Add automated API and inference tests.

**NEXT_004** — Add a lightweight production deployment with monitoring.

**NEXT_005** — Connect this system to future retrieval and agent workflows where customer-risk decisions require richer context.

## 13 — RELATED SYSTEMS

<div class="vp-connection-grid">
  <div><small>FOUNDATION ←</small><b>House Price / Titanic</b><p>Earlier tabular ML workflows that establish the supervised learning baseline.</p></div>
  <div><small>YOU ARE HERE</small><b>Customer Churn Prediction</b><p>A production-oriented extension from notebook modeling to API and container boundaries.</p></div>
  <div><small>NEXT LAYER →</small><b>LoRA / QLoRA</b><p>Moves the portfolio from classical ML into generative AI model adaptation.</p></div>
</div>

## 14 — SOURCE CODE

- **Project repository:** [KN-Vignesh / intelligent-customer-churn-prediction](https://github.com/KN-Vignesh/intelligent-customer-churn-prediction)
- **Notebook in portfolio:** [Customer Churn Prediction with ML](https://github.com/KN-Vignesh/Projects/blob/main/Customer_Churn_Prediction_with_ML.ipynb)

> This page is self-contained. The linked repositories provide the executable implementation and supporting artifacts, not required context for understanding the system described here.

</div>
