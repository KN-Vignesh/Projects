# RAG Pipeline & DeepEval Evaluation Framework

Retrieval-Augmented Generation (RAG) using LangChain, Google Gemini embeddings, Chroma vector database, and automated synthetic golden dataset evaluation via DeepEval.

## Overview

This project implements an end-to-end Retrieval-Augmented Generation (RAG) system paired with an automated evaluation framework. Grounded in a domain document corpus (`rag_eval_docs.csv`), the architecture indexes text chunks using Google Gemini embeddings (`gemini-embedding-2`) into a persistent Chroma vector database, executes threshold-filtered similarity retrieval, and answers queries via `ChatGoogleGenerativeAI`.

To evaluate system fidelity without relying on manual ground-truth labeling, the project integrates **DeepEval**'s synthetic data engine (`Synthesizer`), programmatically generating evaluation "goldens" (questions and reference answers) directly from source contexts.

## Problem

Building production RAG systems requires solving two interconnected problems:
1. **Retrieval Precision & Noise:** Naive top-$k$ retrieval frequently injects irrelevant context chunks into the prompt, diluting context window quality and triggering hallucinations.
2. **Evaluation Bottlenecks:** Evaluating retrieval and generation quality manually is slow, expensive, and unscalable. Engineering teams need automated, reproducible metrics (Faithfulness, Answer Relevance, Contextual Recall) grounded in synthetic test sets.

## Motivation

Traditional unit tests cannot verify whether an LLM generation faithfully adheres to retrieved context. By combining a LangChain LCEL retrieval pipeline with DeepEval's LLM-as-a-judge synthesizer, this project provides a reproducible template for both running and measuring RAG performance.

## Key Capabilities

- **Google GenAI Embeddings:** Generates semantic vectors using `gemini-embedding-2`.
- **Persistent Vector Store:** Chroma vector database with local disk persistence (`./my_db`).
- **Score-Threshold Retrieval:** Configurable similarity search with hard cutoff (`score_threshold = 0.30`, $k=3$) to prune low-relevance documents.
- **Strict Grounding Prompting:** Enforces strict adherence instructions: *"Answer ONLY from the provided context."*
- **Synthetic Golden Dataset Generation:** Uses DeepEval's `Synthesizer` to extract test cases with expected outputs directly from document contexts.

## Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │             Raw Documents (rag_eval_docs.csv)          │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │              Document Ingestion & Metadata             │
       │       - Extract title, document ID, and context        │
       │       - Wrap into LangChain Document objects           │
       └──────────────┬──────────────────────────┬──────────────┘
                      │                          │
       ┌──────────────┴────────────┐ ┌───────────┴──────────────┐
       │    Vector Store Pipeline  │ │  DeepEval Evaluation Path│
       │   Google GenAI Embeddings │ │   (Synthetic Generation) │
       │     (gemini-embedding-2)  │ │                          │
       │              │            │ │   DeepEval Synthesizer   │
       │              ▼            │ │   (Gemini Model Judge)   │
       │     Chroma Vector DB      │ │            │             │
       │       (./my_db store)     │ │            ▼             │
       │              │            │ │    Golden Dataset Output │
       │              ▼            │ │  (Questions + Reference) │
       │  Similarity Threshold     │ └──────────────────────────┘
       │  (k=3, threshold=0.30)    │
       └──────────────┬────────────┘
                      │
                      ▼
       ┌────────────────────────────────────────────────────────┐
       │              LCEL Generation Pipeline                  │
       │                                                        │
       │   Input Question ─────────────────────────┐            │
       │        │                                  │            │
       │        ▼                                  ▼            │
       │   [Retriever]                      [Passthrough]       │
       │        │ (Context Chunks)                 │            │
       │        └──────────────┬───────────────────┘            │
       │                       ▼                                │
       │              [ChatPromptTemplate]                      │
       │                       ▼                                │
       │            [ChatGoogleGenerativeAI]                    │
       │                       ▼                                │
       │               Grounded Response                        │
       └────────────────────────────────────────────────────────┘
```

## How It Works

1. **Corpus Ingestion:** Document records containing article titles, identifiers, and contextual bodies are converted into structured LangChain `Document` primitives.
2. **Embedding & Vector Storage:** Documents are embedded using `GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")` and indexed in a local Chroma collection (`collection_name="my_db"`).
3. **Threshold-Filtered Retrieval:** The vector store is exposed as a retriever configured with `search_type="similarity_score_threshold"`:
   ```python
   similarity_retriever = chroma_db.as_retriever(
       search_type="similarity_score_threshold",
       search_kwargs={"k": 3, "score_threshold": 0.30}
   )
   ```
4. **LangChain Expression Language (LCEL) Chain:** The question and retrieved context are merged into a strictly constrained prompt:
   ```python
   rag_chain = (
       {"context": similarity_retriever, "question": RunnablePassthrough()}
       | rag_prompt
       | gemini_model
       | StrOutputParser()
   )
   ```
5. **Synthetic Golden Generation:** DeepEval's `Synthesizer(model=deepeval_gemini_model)` evaluates the contexts and automatically generates questions and expected answers for offline benchmarking.

## Technology Stack

### Models
- **Embeddings:** `gemini-embedding-2` via `langchain-google-genai`.
- **Generation LLM:** Google Gemini via `ChatGoogleGenerativeAI`.
- **Evaluation Judge:** `GeminiModel` via DeepEval.

### Frameworks & Libraries
- **LangChain Core & Community (0.3.25):** LCEL runnables, prompt templates, document schemas.
- **LangChain Google GenAI:** Official LangChain integration for Google generative models.
- **ChromaDB (1.0.15) & langchain-chroma (0.2.4):** Local persistent vector database.
- **DeepEval (4.1.3):** Production evaluation framework for LLM and RAG pipelines.
- **Pandas:** Tabular document loading and parsing.

## Engineering Decisions

1. **Why similarity score threshold over standard top-k?**  
   Standard `k=3` always returns 3 documents even if all candidates have low cosine similarity to the query. In a production system, this introduces irrelevant distractors into the prompt. Setting `score_threshold=0.30` ensures the model only receives context chunks with genuine semantic overlap.

2. **Why DeepEval Synthesizer?**  
   Handcrafting evaluation sets is the single largest bottleneck in AI engineering. DeepEval extracts key entities and factual relationships from raw chunks to synthesize realistic user queries and ground-truth answers, enabling repeatable regression testing.

3. **Why persistent Chroma storage?**  
   Persisting vectors to `./my_db` avoids re-computing embeddings on every notebook run, saving API quota and eliminating indexing latency.

## Project Structure

```text
Ai-Cookbook/Combined_metric_Calc/
├── README.md                   # Comprehensive technical documentation
└── Combined_metric_Calc.ipynb  # Executed Jupyter notebook with RAG & DeepEval pipeline
```

## Setup & Execution

### Prerequisites
- Python 3.10+
- Google Gemini API Key (`GOOGLE_API_KEY`)

### Installation
```bash
pip install -q \
  langchain==0.3.25 \
  langchain-google-genai \
  langchain-chroma==0.2.4 \
  chromadb==1.0.15 \
  deepeval==4.1.3 \
  pandas
```

### Configuration
Set your Google API key in your environment:
```bash
export GOOGLE_API_KEY="your-api-key"
```

### Running the Notebook
```bash
jupyter notebook Ai-Cookbook/Combined_metric_Calc/Combined_metric_Calc.ipynb
```

## Example Execution

### User Query
```text
Query: "What is Artificial Intelligence?"
```

### Retrieved Context Chunks
- **Chunk 1 (Score: 0.72):** Definition and foundational branches of AI, including machine learning and neural networks.
- **Chunk 2 (Score: 0.58):** History and symbolic systems vs statistical learning.

### Generated Response
> *"Artificial Intelligence is the branch of computer science dedicated to creating systems capable of performing tasks that typically require human intelligence, such as visual perception, speech recognition, decision-making, and natural language understanding, as detailed in the provided documentation."*

## Limitations

- **Single Document Corpus:** The demonstration uses a specialized dataset (`rag_eval_docs.csv`); multi-modal or unformatted PDF ingestion requires additional unstructured parsers.
- **API Rate Limiting:** Synthetic golden generation makes multiple parallel calls to Gemini; large corpora require batching and exponential backoff.

## Future Improvements

- Hybrid search combining BM25 keyword matching with dense Gemini vector embeddings.
- Cross-encoder reranker stage (e.g. Cohere or BGE reranker) prior to context prompt assembly.
- Automated CI/CD assertion testing using DeepEval's `assert_test()` in GitHub Actions.

## References

- Lewis, P., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.* NeurIPS 2020.
- DeepEval Documentation. *Confident AI: The Open-Source LLM Evaluation Framework.*

## License

MIT License. Developed by Vignesh K N.
