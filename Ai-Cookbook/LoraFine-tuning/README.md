# Qwen / LoRA Parameter-Efficient Fine-Tuning

Parameter-efficient fine-tuning of Qwen2.5-0.5B-Instruct using low-rank adaptation (LoRA) for structured domain response generation.

## Overview

This project demonstrates parameter-efficient fine-tuning (PEFT) on an open-weight language model (`Qwen/Qwen2.5-0.5B-Instruct`). By freezing the 495-million-parameter base model and injecting trainable rank decomposition matrices into the multi-head attention projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`), the model is taught a rigid enterprise HR response protocol while training only **0.2184%** of total parameters.

## Problem

Full parameter fine-tuning of modern language models poses serious engineering hurdles:
1. **Excessive VRAM Footprint:** Storing optimizer states (e.g. AdamW requires 8 bytes per parameter in fp32), gradients, and activations for billions of weights requires multi-GPU clusters.
2. **Catastrophic Forgetting:** Overwriting all base weights on a small specialized dataset causes the model to lose general reasoning and instruction-following abilities.
3. **Storage & Deployment Overhead:** Saving a full checkpoint per specialized task requires gigabytes of disk and complicates serving multi-tenant models.

## Motivation

LoRA (Low-Rank Adaptation) addresses these issues by freezing the pretrained weight matrix $W_0 \in \mathbb{R}^{d \times k}$ and parameterizing the weight update $\Delta W$ as the product of two low-rank matrices:
$$\Delta W = B \cdot A$$
where $B \in \mathbb{R}^{d \times r}$ and $A \in \mathbb{R}^{r \times k}$, with rank $r \ll \min(d, k)$. During training, only $A$ and $B$ receive gradient updates, reducing the memory required for optimizer states and producing compact adapter artifacts that can be swapped dynamically at inference.

## Key Capabilities

- **Targeted Attention Projection Adaptation:** Targets query (`q_proj`), key (`k_proj`), value (`v_proj`), and output (`o_proj`) projections for maximum adaptation capacity with minimal rank.
- **Micro-Artifact Generation:** Generates lightweight adapter weights without altering the underlying base model files.
- **Strict Format Adherence:** Transforms verbose conversational replies into strict enterprise outputs (`HR_RESPONSE: <response>`).
- **Before-and-After Inference Verification:** Side-by-side evaluation verifying that the base model adheres to the domain schema post-adaptation.

## Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │                Input Employee Prompt                   │
       │    "Employee: I need leave tomorrow. Response:"        │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │              Qwen2.5-0.5B-Instruct Base                │
       │          (Frozen Weights W_0 - 494M params)            │
       │                                                        │
       │   q_proj         k_proj         v_proj         o_proj  │
       │     │              │              │              │     │
       │     ▼              ▼              ▼              ▼     │
       │  [Frozen]       [Frozen]       [Frozen]       [Frozen] │
       └─────┼──────────────┼──────────────┼──────────────┼─────┘
             │ +            │ +            │ +            │ +
       ┌─────▼──────────────▼──────────────▼──────────────▼─────┐
       │             Trainable LoRA Adapters (ΔW)               │
       │                  (r = 8, alpha = 16)                   │
       │     │              │              │              │     │
       │   [ B·A ]        [ B·A ]        [ B·A ]        [ B·A ] │
       │ (1.08M Trainable Parameters · 0.2184% of total)        │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                 Supervised Loss / Output               │
       │  "HR_RESPONSE: Please submit your leave request..."    │
       └────────────────────────────────────────────────────────┘
```

## How It Works

1. **Base Model Loading:** `Qwen/Qwen2.5-0.5B-Instruct` is loaded in half-precision (`torch.float16`) to minimize baseline memory overhead.
2. **Prompt Template Formatting:** Samples are formatted using chat templates with explicit instruction and role boundaries:
   ```text
   ### Instruction:
   Respond to the employee using exactly this format:
   HR_RESPONSE: <your response>
   ### Employee:
   <query>
   ### Response:
   HR_RESPONSE: <target text>
   ```
3. **LoRA Injection:** `LoraConfig` from Hugging Face `peft` attaches low-rank adapters to `q_proj`, `k_proj`, `v_proj`, and `o_proj`.
4. **Supervised Fine-Tuning (SFT):** The model is trained using Hugging Face `Trainer` with `DataCollatorForLanguageModeling(mlm=False)` for 15 epochs.
5. **Inference & Verification:** Test prompts are passed through `model.generate()` to verify strict syntax adherence.

## Technology Stack

### Models
- **Base Model:** `Qwen/Qwen2.5-0.5B-Instruct` (495,114,112 total parameters).
- **Adapter Type:** Low-Rank Adaptation (LoRA) via PEFT.

### Frameworks & Libraries
- **PyTorch:** Underlying tensor computation and GPU acceleration.
- **Hugging Face Transformers (4.46+):** Model architecture, tokenizer, and `Trainer` abstraction.
- **PEFT (0.13+):** Parameter-efficient fine-tuning matrix injection.
- **Datasets:** Tokenized dataset mapping and batch collation.
- **Accelerate:** Efficient memory management and mixed-precision execution.

## Engineering Decisions

1. **Why Qwen2.5-0.5B-Instruct?**  
   The 0.5B parameter variant provides modern architectural design (RoPE, SwiGLU, RMSNorm) and instruction-following capability while being small enough to train on a single consumer GPU or free Google Colab T4 tier without out-of-memory errors.

2. **Why adapt all four attention projections (`q_proj`, `k_proj`, `v_proj`, `o_proj`)?**  
   Early LoRA implementations often adapted only query and value matrices ($W_q, W_v$). Recent research (e.g. QLoRA paper by Dettmers et al.) demonstrated that adapting all attention projections with a smaller rank ($r=8$) yields higher expressive capacity and faster loss convergence than adapting only $W_q, W_v$ with larger rank ($r=16$).

3. **Why rank $r = 8$ and alpha $\alpha = 16$?**  
   The scaling factor is $\frac{\alpha}{r} = \frac{16}{8} = 2.0$. A scaling factor of 2 provides a stable gradient update balance that allows the model to learn the strict output prefix without destabilizing general vocabulary representations.

4. **Why float16 precision?**  
   `torch.float16` reduces base model memory from ~2.0 GB (in fp32) to ~1.0 GB, leaving ample headroom for activation caching during backpropagation.

## Project Structure

```text
Ai-Cookbook/LoraFine-tuning/
├── README.md                     # Comprehensive technical documentation
└── LORA_WITH_QWENN_MODEL.ipynb   # Executed Jupyter notebook with logged outputs
```

## Setup & Execution

### Prerequisites
- Python 3.10+
- CUDA-capable GPU (Google Colab T4, NVIDIA RTX 3060+, or cloud instance with >= 6GB VRAM)

### Installation
```bash
pip install -q -U torch transformers datasets peft accelerate
```

### Running the Notebook
Open and run `LORA_WITH_QWENN_MODEL.ipynb` in Jupyter Notebook, VS Code, or Google Colab:
```bash
jupyter notebook Ai-Cookbook/LoraFine-tuning/LORA_WITH_QWENN_MODEL.ipynb
```

## Verified Configuration & Training Parameters

The following parameters are extracted directly from the verified notebook execution:

| Parameter | Measured / Configured Value |
| :--- | :--- |
| **Base Model** | `Qwen/Qwen2.5-0.5B-Instruct` |
| **Precision** | `torch.float16` |
| **LoRA Rank ($r$)** | `8` |
| **LoRA Alpha ($\alpha$)** | `16` |
| **LoRA Dropout** | `0.05` |
| **Target Modules** | `["q_proj", "k_proj", "v_proj", "o_proj"]` |
| **Total Model Parameters** | 495,114,112 |
| **Trainable Parameters** | **1,081,344** (0.2184% of total) |
| **Batch Size** | 1 (per device) |
| **Learning Rate** | `2e-4` |
| **Epochs** | 15 |
| **Optimization Steps** | 75 |
| **Training Runtime** | 18.06 seconds |
| **Final Training Loss** | **0.7089** |

## Evaluation & Results

### Qualitative Verification (Before vs. After Adaptation)

The model was tested with identical employee inquiries before and after adapter training:

#### Test Prompt 1
```text
Respond to the employee using exactly this format:
HR_RESPONSE: <your response>
Employee: I need leave tomorrow.
Response:
```

- **Before LoRA (Base Model Output):**
  > *"Employee: I understand that you need some time off tomorrow. Please let me know if there is anything specific you would like to discuss or if you have any questions before we proceed."*  
  *(Failed: Failed the requested prefix schema; produced generic conversational reply).*

- **After LoRA (Adapted Model Output):**
  > **`HR_RESPONSE: Please submit your leave request through the HR portal.`**  
  *(Success: Follows exact required prefix and tone).*

#### Test Prompt 2
```text
Respond to the employee using exactly this format:
HR_RESPONSE: <your response>
Employee: Can I work from home?
Response:
```

- **After LoRA (Adapted Model Output):**
  > **`HR_RESPONSE: Employees can work from home two days per week.`**  
  *(Success: Correct domain resolution and strict formatting).*

## Limitations

- **Dataset Scale:** The experiment serves as an architectural demonstration of schema-constrained adaptation using a small 5-sample training set; larger production use cases require hundreds of diverse policy queries.
- **In-Memory Adaptation Only:** The notebook demonstrates PEFT parameter optimization but does not export merged safetensors or serve the model via an inference endpoint (e.g. vLLM).
- **Base Model Hallucinations:** On queries outside the narrow training samples, the small 0.5B base model may still generate generic responses if prompting is ambiguous.

## Future Improvements

- Merging adapter weights back into base model (`model.merge_and_unload()`) for zero-overhead inference serving.
- Exporting to GGUF format for edge deployment with `llama.cpp`.
- Adding automated schema validation (e.g. regex matching test suite) to measure format compliance rate across a 100-sample test set.

## References

- Hu, E. J., et al. (2021). *LoRA: Low-Rank Adaptation of Large Language Models.* arXiv:2106.09685.
- Qwen Team. (2024). *Qwen2.5: A Party of Foundation Models.* Alibaba Cloud.

## License

MIT License. Developed by Vignesh K N.
