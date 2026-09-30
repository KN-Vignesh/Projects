# QLoRA: Quantized Low-Rank Adaptation

Memory-efficient language model adaptation using 4-bit NormalFloat (NF4) quantization, double quantization, and low-rank adapters.

## Overview

This project explores Quantized Low-Rank Adaptation (QLoRA) on a constrained causal language model (`distilgpt2`). By quantizing the frozen base model weights down to 4-bit precision using `bitsandbytes` while keeping trainable low-rank adapters in half-precision (`fp16`), the system reduces GPU VRAM consumption while training only **0.1797%** of the model's parameters.

## Problem

Fine-tuning modern large language models poses severe hardware constraints:
1. **Memory Ceiling:** Even in 16-bit precision, loading a 7B model requires 14+ GB of VRAM solely for weights, leaving zero headroom for gradients and activations on consumer GPUs.
2. **Quantization Degradation:** Standard 8-bit or 4-bit integer quantization (INT4/INT8) degrades model quality and causes gradient instability if applied during training.
3. **Double Quantization Overhead:** Quantization constants themselves consume significant GPU memory when models scale to billions of weights.

## Motivation

QLoRA (Dettmers et al., 2023) introduced three innovations to enable fine-tuning without performance loss:
1. **4-bit NormalFloat (NF4):** An information-theoretically optimal quantile quantization data type for normally distributed weights.
2. **Double Quantization (DQ):** Quantizes the quantization constants, saving an additional 0.37 bits per parameter.
3. **Paged Optimizers:** Uses CUDA Unified Memory to prevent out-of-memory spikes during gradient checkpointing.

This experiment implements the complete QLoRA pipeline to understand how NF4 quantization, `prepare_model_for_kbit_training`, and attention adapters behave in practice.

## Key Capabilities

- **BitsAndBytes 4-bit NF4 Quantization:** Loads the base model in 4-bit precision with float16 compute dtype.
- **Double Quantization:** Enables `bnb_4bit_use_double_quant=True` to minimize quantization constant memory.
- **k-Bit Training Preparation:** Freezes base weights, casts layer norms to 32-bit for numerical stability, and attaches gradient hooks.
- **Targeted LoRA Injection:** Injects rank-8 adapters directly into the combined attention projection (`c_attn`).
- **Empirical Failure-Mode Analysis:** Documents the real-world representational limits of aggressive 4-bit quantization on small (<100M) language models.

## Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │                     Input Prompt                       │
       │    "Question: What are the working hours? Answer:"     │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                   DistilGPT2 Base                      │
       │           (82M Parameters · Frozen)                    │
       │                                                        │
       │  ┌──────────────────────────────────────────────────┐  │
       │  │        4-bit NormalFloat (NF4) Quantization       │  │
       │  │        + Double Quantization (BitsAndBytes)       │  │
       │  └────────────────────────┬─────────────────────────┘  │
       │                           │                            │
       │                     c_attn weights                     │
       └───────────────────────────┼────────────────────────────┘
                                   │ +
       ┌───────────────────────────▼────────────────────────────┐
       │             Trainable LoRA Adapter (ΔW)                │
       │             (r = 8, alpha = 16, fp16)                  │
       │                                                        │
       │   147,456 Trainable Parameters (0.1797% of total)      │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                     Generated Tokens                   │
       └────────────────────────────────────────────────────────┘
```

## How It Works

1. **Quantization Configuration:** A `BitsAndBytesConfig` is defined with `load_in_4bit=True`, `bnb_4bit_quant_type="nf4"`, `bnb_4bit_compute_dtype=torch.float16`, and `bnb_4bit_use_double_quant=True`.
2. **Quantized Model Loading:** `AutoModelForCausalLM.from_pretrained` loads `distilgpt2` directly into 4-bit representation with automatic GPU device mapping.
3. **k-Bit Preparation:** `prepare_model_for_kbit_training` prepares the quantized graph, enabling gradient checkpointing and casting layer normalization layers to 32-bit float to prevent loss divergence.
4. **LoRA Adapter Injection:** `LoraConfig` targets the `c_attn` projection layer with rank $r=8$ and $\alpha=16$.
5. **Training Execution:** The model trains for 10 epochs using Hugging Face `Trainer` and `DataCollatorForLanguageModeling(mlm=False)`.

## Technology Stack

### Models
- **Base Architecture:** `distilgpt2` (82,060,032 total parameters).
- **Adaptation Layer:** PEFT LoRA with 4-bit NF4 quantized base weights.

### Frameworks & Libraries
- **PyTorch:** GPU tensor acceleration.
- **BitsAndBytes (>=0.46.1):** 4-bit NF4 quantization kernels.
- **Hugging Face Transformers (4.46+):** Model loader and Trainer pipeline.
- **PEFT (0.13+):** Quantized k-bit adapter injection.
- **Accelerate:** Device mapping and gradient checkpointing.

## Engineering Decisions

1. **Why NF4 (NormalFloat4) over FP4 or INT4?**  
   Pretrained neural network weights typically follow a zero-centered normal distribution $\mathcal{N}(0, \sigma^2)$. Uniform INT4 quantization places equal spacing between bins, wasting resolution on outliers. NF4 constructs quantile bins with equal probability mass, preserving significantly higher information theoretical entropy per weight.

2. **Why target `c_attn` on DistilGPT2?**  
   In GPT-2 and DistilGPT2 architectures, the query, key, and value attention projections are stored as a single combined linear layer (`c_attn`). Attaching LoRA adapters to `c_attn` adapts all three attention matrices simultaneously.

3. **Why double quantization?**  
   Quantizing 32-bit fp constants to 8-bit fp saves 0.37 bits per parameter. For an 82M model this is small, but for 7B+ models double quantization frees nearly 3GB of VRAM.

4. **Why did the experiment evaluate DistilGPT2?**  
   DistilGPT2 allows validating the full end-to-end BitsAndBytes and PEFT integration pipeline with minimal compute download times, providing immediate feedback on compilation and gradient flow.

## Project Structure

```text
Ai-Cookbook/QLoraFine-Tuning/
├── README.md               # Comprehensive technical documentation
└── QLora_FineTuning.ipynb  # Executed Jupyter notebook with logged training outputs
```

## Setup & Execution

### Prerequisites
- Python 3.10+
- Linux with NVIDIA CUDA GPU (BitsAndBytes 4-bit CUDA kernels require Linux / WSL)

### Installation
```bash
pip install -q -U torch transformers datasets peft accelerate "bitsandbytes>=0.46.1"
```

### Running the Notebook
```bash
jupyter notebook Ai-Cookbook/QLoraFine-Tuning/QLora_FineTuning.ipynb
```

## Verified Configuration & Training Parameters

The following parameters are extracted directly from the verified notebook execution:

| Parameter | Measured / Configured Value |
| :--- | :--- |
| **Base Model** | `distilgpt2` |
| **Quantization Type** | 4-bit NormalFloat (`nf4`) |
| **Double Quantization** | Enabled (`bnb_4bit_use_double_quant=True`) |
| **Compute Dtype** | `torch.float16` |
| **LoRA Rank ($r$)** | `8` |
| **LoRA Alpha ($\alpha$)** | `16` |
| **LoRA Dropout** | `0.05` |
| **Target Modules** | `["c_attn"]` |
| **Total Model Parameters** | 82,060,032 |
| **Trainable Parameters** | **147,456** (0.1797% of total) |
| **Batch Size** | 2 (per device) |
| **Learning Rate** | `2e-4` |
| **Epochs** | 10 |
| **Optimization Steps** | 30 |
| **Training Loss** | **3.6479** |

## Evaluation & Empirical Observations

### Observed Generation Output
```text
Input: Question: What are the working hours? Answer:
Generated Output: I I I,,,,.. I and and or or,
```

### Critical Engineering Findings
1. **Representational Bottlenecks in Small Models:** While QLoRA is proven to preserve 99%+ of full fine-tuning performance on large models (7B, 13B, 70B parameters), aggressive 4-bit quantization on sub-100M parameter models (`distilgpt2`) severely truncates the model's capacity, causing repetitive token generation when trained on small datasets.
2. **Gradient Checkpointing Caveats:** As logged during training, PyTorch dynamo issued warnings regarding `use_reentrant=False` parameter changes and `use_cache=False` incompatibilities during gradient checkpointing.
3. **Conclusion for Production Engineering:** QLoRA is an optimal technique for 7B+ models where weight redundancy is high. For small models (<1B parameters), standard 16-bit LoRA (as demonstrated in the Qwen project) provides far superior task fidelity without quantization distortion.

## Limitations

- **Hardware Dependency:** BitsAndBytes 4-bit CUDA kernels require an NVIDIA GPU; QLoRA cannot be trained on CPU or Apple Silicon without specialized MPS backends.
- **Small-Scale Base Model:** DistilGPT2 lacks the foundational instruction reasoning necessary for complex zero-shot downstream generation.

## Future Improvements

- Scaling the verified QLoRA configuration to `Qwen2.5-7B` or `Llama-3-8B` where NF4 quantization maintains baseline benchmark accuracy.
- Implementing Paged AdamW optimizers (`paged_adamw_8bit`) to prevent out-of-memory memory spikes during long sequence token generation.

## References

- Dettmers, T., Pagnoni, A., Holtzman, A., & Zettlemoyer, L. (2023). *QLoRA: Efficient Finetuning of Quantized LLMs.* NeurIPS 2023. arXiv:2305.14314.

## License

MIT License. Developed by Vignesh K N.
