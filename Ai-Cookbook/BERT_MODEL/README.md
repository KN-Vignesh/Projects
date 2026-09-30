# BERT & Transformer NLP Workflows

Downstream NLP workflows demonstrating Hugging Face Transformers pipelines (classification, summarization, NER, question answering, translation) and dense sentence embeddings via SentenceTransformers.

## Overview

This project provides an operational tour of Transformer architectures applied to standard natural language processing tasks. Implemented via Hugging Face `transformers` and `sentence-transformers`, the notebook demonstrates how pretrained weights are utilized for zero-shot and transfer-learning workflows across 6 downstream NLP modalities.

## Key Capabilities

1. **Sequence Classification:** Binary sentiment analysis evaluating movie reviews and customer support transcripts.
2. **Abstractive Summarization:** Context compression on news editorials using constrained sequence length limits (`max_length=10`).
3. **Named Entity Recognition (NER):** Token-level entity classification identifying organizations (e.g. Apple, Samsung) and contextual mentions.
4. **Extractive Question Answering:** Span-level context extraction locating specific answers (e.g. dates, names) within incoming email text.
5. **Machine Translation:** English-to-French text translation.
6. **Dense Sentence Embeddings:** Generating 384-dimensional semantic dense vectors using `all-MiniLM-L6-v2` for semantic similarity search.

## Technology Stack

- **Libraries:** Hugging Face `transformers` (4.46+), `datasets`, `sentence-transformers`, `torch`, `pandas`.
- **Pretrained Models:** Default Hugging Face pipeline weights and `sentence-transformers/all-MiniLM-L6-v2`.

## Setup & Execution

### Prerequisites
```bash
pip install -q transformers==4.46.3 datasets sentence-transformers torch pandas
```

### Running the Notebook
```bash
jupyter notebook Ai-Cookbook/BERT_MODEL/BERT_MODEL.ipynb
```

## Project Structure
- `BERT_MODEL.ipynb`: Executed notebook containing code cells and pipeline outputs.
- `README.md`: Technical documentation.

## License
MIT License. Developed by Vignesh K N.
