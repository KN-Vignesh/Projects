# AI & Machine Learning Engineering Projects

A collection of AI systems, multi-agent workflows, model adaptation experiments, and machine learning pipelines developed by Vignesh K N.

> **Engineering Principle:** Build with software discipline, evaluate with reproducible evidence, and govern probabilistic model outputs with deterministic decision rules.

---

## Technical Reviewer Guide

If you are evaluating this repository for the first time, start with the **Tier A Showcase Projects**:

1. **[VERO (Full-Stack PR Review Engine)](VERO/README.md):** Evidence-based pull request analysis combining GitHub diff parsing, in-process SonarQube static rules, TypeSafe Jev structured inference, and an auditable 5-policy decision engine. *(Interactive React 19 app + Express API)*.
2. **[Shiny Agents (Multi-Agent Architectures)](Shiny-Agents/README.md):** Side-by-side comparison of CrewAI (hierarchical roles), OpenAI Agents SDK (event loop + safety guardrails), and LangGraph (cyclical graph with code review feedback loops) on Gemini.
3. **[Qwen / LoRA Adaptation](Ai-Cookbook/LoraFine-tuning/README.md):** Parameter-efficient fine-tuning on `Qwen2.5-0.5B-Instruct` adapting only 0.2184% of parameters for strict enterprise schema formatting.
4. **[QLoRA 4-bit Quantization](Ai-Cookbook/QLoraFine-Tuning/README.md):** 4-bit NF4 quantized adaptation with double quantization on constrained models, documenting memory vs representational capacity trade-offs.
5. **[RAG Pipeline & DeepEval](Ai-Cookbook/Combined_metric_Calc/README.md):** Retrieval-Augmented Generation with Chroma, Gemini embeddings, and programmatic synthetic golden evaluation via DeepEval.

---

## Project Directory

### Tier A — Showcase Projects

| Project | Domain | Architecture / Tech | Key Evidence / Highlights | Links |
| :--- | :--- | :--- | :--- | :--- |
| **VERO** | AI Code Intelligence | React 19 · Express · SonarQube Rules · TypeSafe Jev · Policy Engine | Evaluated on 120 PRs; reduced false-positive security alerts from 22.8% to 4.6% via dual-engine corroboration. | [README](VERO/README.md) · [Live Demo](/vero/) |
| **Shiny Agents** | Multi-Agent Systems | Python · FastAPI · CrewAI · OpenAI Agents SDK · LangGraph · Gemini | Closed-loop review cycles (capped at 2 revisions); pre-execution safety guardrail tripwire; 24h SQLite trial limiter. | [README](Shiny-Agents/README.md) |
| **Qwen / LoRA** | Parameter-Efficient LLM | PyTorch · Transformers · PEFT · Qwen2.5-0.5B-Instruct | Trained 1.08M / 495M parameters (0.2184%); loss decreased from initial to 0.7089; verified before/after format adherence. | [README](Ai-Cookbook/LoraFine-tuning/README.md) · [Notebook](Ai-Cookbook/LoraFine-tuning/LORA_WITH_QWENN_MODEL.ipynb) |
| **QLoRA Adaptation** | Memory-Efficient LLM | PyTorch · BitsAndBytes · 4-bit NF4 · Double Quantization · PEFT | Trained 147K / 82M parameters (0.1797%); documented representational bottlenecks on sub-100M parameter models. | [README](Ai-Cookbook/QLoraFine-Tuning/README.md) · [Notebook](Ai-Cookbook/QLoraFine-Tuning/QLora_FineTuning.ipynb) |
| **RAG & DeepEval** | Retrieval & AI Evaluation | LangChain 0.3 · Chroma · Gemini Embeddings · DeepEval 4.1 | Similarity score threshold cutoff ($k=3$, score $\ge 0.30$); automated synthetic golden dataset extraction. | [README](Ai-Cookbook/Combined_metric_Calc/README.md) · [Notebook](Ai-Cookbook/Combined_metric_Calc/Combined_metric_Calc.ipynb) |

---

### Tier B — Supporting Projects (Breadth & Foundations)

| Project | Focus | Methods & Models | Results | Links |
| :--- | :--- | :--- | :--- | :--- |
| **Customer Churn Prediction** | Tabular ML & Serving | Scikit-learn, SMOTE oversampling, 5-fold CV, FastAPI, Docker | Random Forest (84.0% CV acc) vs Decision Tree (79.0% CV acc). Serialized model. | [Doc](projects/customer-churn.md) · [Notebook](Customer_Churn_Prediction_with_ML.ipynb) |
| **House Price Regression** | Feature Engineering & Stacking | Ames dataset, AmesFeatureEngineer, CatBoost, XGBoost, LightGBM, RidgeCV | Stacking ensemble achieved 0.1081 RMSLE, outperforming all 7 base models. | [README](Data-recipe/House_Price_Prediction/README.md) · [Notebook](Data-recipe/House_Price_Prediction/House_Prices_Prediction_using_TFDF.ipynb) |
| **Titanic Survival** | Supervised Classification | Data cleaning, imputation, categorical encoding, scikit-learn | Random Forest (85.47%) vs Logistic Regression (82.68%) vs XGBoost (81.56%). | [README](Data-recipe/Titanic_Model/README.md) · [Notebook](Data-recipe/Titanic_Model/Titanic_model.ipynb) |
| **BERT NLP Workflows** | Transformer Pipelines | Hugging Face Transformers, sentence-transformers (`all-MiniLM-L6-v2`) | Implemented classification, summarization, NER, extractive QA, and translation. | [README](Ai-Cookbook/BERT_MODEL/README.md) · [Notebook](Ai-Cookbook/BERT_MODEL/BERT_MODEL.ipynb) |

---

### Tier C — Experiments & Archive

| Project | Focus | Description | Links |
| :--- | :--- | :--- | :--- |
| **CNN Fundamentals** | Computer Vision Preprocessing | 4D tensor reshaping, pixel normalization ($0-255 \to 0-1$), and one-hot encoding for MNIST classification in TensorFlow Keras. | [README](Ai-Cookbook/CNN-Fundamentals/README.md) · [Notebook](Ai-Cookbook/CNN-Fundamentals/CNN_Fundamental_Preprocessing.ipynb) |

---

## Technology Map

```text
Languages:
  Python (3.10+) · TypeScript · JavaScript · SQL · Bash

Generative AI & LLMs:
  Google Gemini (gemini-2.5-flash, gemini-embedding-2) · Qwen2.5 · DistilGPT2

Agent Architectures & Orchestration:
  CrewAI · OpenAI Agents SDK · LangGraph · LangChain LCEL · Input Guardrails

Parameter-Efficient Fine-Tuning (PEFT):
  LoRA · QLoRA · 4-bit NormalFloat (NF4) · Double Quantization · BitsAndBytes

Machine Learning & Deep Learning:
  PyTorch · TensorFlow / Keras · Scikit-learn · CatBoost · XGBoost · LightGBM

Vector Databases & Evaluation:
  ChromaDB · DeepEval · Shannon Entropy Calibration · SonarQube Clean Code Gate

Serving & Web Infrastructure:
  FastAPI · Express · React 19 · Vite 8 · Tailwind CSS · Docker · Uvicorn
```

---

## Repository Structure

```text
Projects/
├── README.md                          # Repository index and technical reviewer guide
├── package.json                       # Root workspace and testing scripts
├── .env.example                       # Root environment variable template
├── _sidebar.md                        # Documentation sidebar navigation
├── _navbar.md                         # Documentation header navigation
├── index.html                         # Docsify single-page documentation shell
│
├── VERO/                              # Tier A: Flagship PR Code Analysis Platform
│   ├── README.md                      # Comprehensive VERO documentation
│   ├── server.ts                      # Express API and Vite integration
│   ├── package.json                   # React 19 + TypeScript dependencies
│   ├── src/                           # Client components & server engines
│   │   ├── server/decisionEngine.ts   # 5-policy deterministic gatekeeper
│   │   ├── server/sonarEngine.ts      # 28+ static Clean Code rules
│   │   ├── server/jevEngine.ts        # TypeSafe Jev probabilistic inference
│   │   └── server/evaluationData.ts   # 120 PR benchmark comparisons
│   └── tests/engines.test.ts          # Automated unit test suite
│
├── Shiny-Agents/                      # Tier A: Multi-Agent Comparative Framework
│   ├── README.md                      # Comparative framework documentation
│   ├── requirements.txt               # Agent SDK dependencies
│   ├── .env.example                   # Gemini configuration template
│   ├── 01_crewai/                     # Level 1: Role-based crew
│   ├── 02_agents_sdk/                 # Level 2: Tool loop + safety guardrail
│   ├── 03_langgraph/                  # Level 3: Stateful cyclical review graph
│   ├── app/server.py                  # FastAPI gateway with 24h SQLite trial limiter
│   └── tests/test_server_contracts.py # Automated agent routing & trial tests
│
├── Ai-Cookbook/                       # Deep Learning, NLP & LLM Cookbook
│   ├── LoraFine-tuning/               # Tier A: Qwen2.5-0.5B LoRA adaptation
│   ├── QLoraFine-Tuning/              # Tier A: 4-bit NF4 QLoRA on DistilGPT2
│   ├── Combined_metric_Calc/          # Tier A: RAG Pipeline & DeepEval
│   ├── BERT_MODEL/                    # Tier B: Downstream Transformer workflows
│   └── CNN-Fundamentals/              # Tier C: MNIST image tensor preprocessing
│
├── Data-recipe/                       # Classical Machine Learning Pipelines
│   ├── House_Price_Prediction/        # Tier B: Stacking ensemble regression (RMSLE 0.1081)
│   └── Titanic_Model/                 # Tier B: Passenger survival classification
│
├── projects/
│   └── customer-churn.md              # Tier B: Telecom churn classification with FastAPI
│
└── Customer_Churn_Prediction_with_ML.ipynb # Churn EDA, SMOTE & 5-fold CV notebook
```

---

## Reproducibility & Automated Testing

All flagship engines include executable test suites to verify reproducibility:

### 1. VERO Engine Tests (Static Scanner, Jev Inference & Decision Policies)
```bash
npm install
npm test
```
*Executes `VERO/tests/engines.test.ts` across URL parsing, OWASP static vulnerability scanning, Jev entropy calculation, and 5-policy gate enforcement.*

### 2. Shiny Agents Contracts & Rate-Limiter Tests
```bash
python -m unittest Shiny-Agents/tests/test_server_contracts.py
```
*Validates SQLite 24-hour rate limiting, thread memory context formatting, and agent script integrity.*

### 3. Notebook Reproducibility
- All Jupyter notebooks contain pre-computed outputs from verified training runs.
- GPU-dependent training notebooks (`LoraFine-tuning`, `QLoraFine-Tuning`) run in Google Colab (free T4 GPU) or any CUDA-enabled environment.

---

## Contact & Links

- **Engineer:** Vignesh K N
- **GitHub:** [https://github.com/KN-Vignesh](https://github.com/KN-Vignesh)
- **LinkedIn:** [https://www.linkedin.com/in/vignesh-k-n/](https://www.linkedin.com/in/vignesh-k-n/)
