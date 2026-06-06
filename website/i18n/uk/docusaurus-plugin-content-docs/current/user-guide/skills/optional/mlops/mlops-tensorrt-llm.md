---
title: "Tensorrt Llm — Оптимізує інференс LLM за допомогою NVIDIA TensorRT для максимальної пропускної здатності та найнижчої затримки"
sidebar_label: "Tensorrt Llm"
description: "Оптимізує інференс LLM за допомогою NVIDIA TensorRT для максимальної пропускної здатності та найнижчої затримки"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Tensorrt Llm

Оптимізує інференс LLM за допомогою NVIDIA TensorRT для максимальної пропускної здатності та найнижчої затримки. Використовуй для продакшн‑розгортання на NVIDIA GPU (A100/H100), коли потрібен інференс у 10‑100 раз швидший, ніж у PyTorch, або для обслуговування моделей з квантуванням (FP8/INT4), динамічним батчингом у польоті та масштабуванням на кілька GPU.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/tensorrt-llm` |
| Path | `optional-skills/mlops/tensorrt-llm` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `tensorrt-llm`, `torch` |
| Platforms | linux, macos |
| Tags | `Inference Serving`, `TensorRT-LLM`, `NVIDIA`, `Inference Optimization`, `High Throughput`, `Low Latency`, `Production`, `FP8`, `INT4`, `In-Flight Batching`, `Multi-GPU` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# TensorRT-LLM

Open‑source бібліотека NVIDIA для оптимізації інференсу LLM з передовою продуктивністю на NVIDIA GPU.

## Коли використовувати TensorRT-LLM

**Використовуй TensorRT-LLM, коли:**
- Розгортаєш на NVIDIA GPU (A100, H100, GB200)
- Потрібна максимальна пропускна здатність (24 000+ токенів/сек на Llama 3)
- Необхідна низька затримка для реального часу
- Працюєш з квантизованими моделями (FP8, INT4, FP4)
- Потрібне масштабування на кілька GPU або вузлів

**Використовуй vLLM, коли:**
- Потрібне простіше налаштування та Python‑first API
- Хочеш PagedAttention без компіляції TensorRT
- Працюєш з AMD GPU або іншим не‑NVIDIA обладнанням

**Використовуй llama.cpp, коли:**
- Розгортаєш на CPU або Apple Silicon
- Потрібне edge‑розгортання без NVIDIA GPU
- Хочеш простіший формат квантування GGUF

## Quick start

### Installation

```bash
# Docker (recommended)
docker pull nvidia/tensorrt_llm:latest

# pip install
pip install tensorrt_llm==1.2.0rc3

# Requires CUDA 13.0.0, TensorRT 10.13.2, Python 3.10-3.12
```

### Basic inference

```python
from tensorrt_llm import LLM, SamplingParams

# Initialize model
llm = LLM(model="meta-llama/Meta-Llama-3-8B")

# Configure sampling
sampling_params = SamplingParams(
    max_tokens=100,
    temperature=0.7,
    top_p=0.9
)

# Generate
prompts = ["Explain quantum computing"]
outputs = llm.generate(prompts, sampling_params)

for output in outputs:
    print(output.text)
```

### Serving with trtllm-serve

⟟HOLD_2⟧

## Key features

### Performance optimizations
- **In‑flight batching**: Динамічний батчинг під час генерації
- **Paged KV cache**: Ефективне управління пам’яттю
- **Flash Attention**: Оптимізовані ядра attention
- **Quantization**: FP8, INT4, FP4 для 2‑4× швидшого інференсу
- **CUDA graphs**: Зменшення накладних витрат запуску ядер

### Parallelism
- **Tensor parallelism (TP)**: Розподіл моделі між GPU
- **Pipeline parallelism (PP)**: Розподіл за шарами
- **Expert parallelism**: Для моделей Mixture‑of‑Experts
- **Multi‑node**: Масштабування за межі одного комп’ютера

### Advanced features
- **Speculative decoding**: Швидша генерація за рахунок чернеткових моделей
- **LoRA serving**: Ефективне розгортання кількох адаптерів
- **Disaggregated serving**: Окреме передзаповнення та генерація

## Common patterns

### Quantized model (FP8)

```python
from tensorrt_llm import LLM

# Load FP8 quantized model (2× faster, 50% memory)
llm = LLM(
    model="meta-llama/Meta-Llama-3-70B",
    dtype="fp8",
    max_num_tokens=8192
)

# Inference same as before
outputs = llm.generate(["Summarize this article..."])
```

### Multi‑GPU deployment

```python
# Tensor parallelism across 8 GPUs
llm = LLM(
    model="meta-llama/Meta-Llama-3-405B",
    tensor_parallel_size=8,
    dtype="fp8"
)
```

### Batch inference

```python
# Process 100 prompts efficiently
prompts = [f"Question {i}: ..." for i in range(100)]

outputs = llm.generate(
    prompts,
    sampling_params=SamplingParams(max_tokens=200)
)

# Automatic in-flight batching for maximum throughput
```

## Performance benchmarks

**Meta Llama 3‑8B** (GPU H100):
- Пропускна здатність: 24 000 токенів/сек
- Затримка: ~10 ms за токен
- Порівняно з PyTorch: **100× швидше**

**Llama 3‑70B** (8 × A100 80 GB):
- Квантування FP8: 2 × швидше, ніж FP16
- Пам’ять: зменшення на 50 % завдяки FP8

## Supported models

- **LLaMA family**: Llama 2, Llama 3, CodeLlama
- **GPT family**: GPT‑2, GPT‑J, GPT‑NeoX
- **Qwen**: Qwen, Qwen2, QwQ
- **DeepSeek**: DeepSeek‑V2, DeepSeek‑V3
- **Mixtral**: Mixtral‑8x7B, Mixtral‑8x22B
- **Vision**: LLaVA, Phi‑3‑vision
- **100+ models** on HuggingFace

## References

- **[Optimization Guide](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/tensorrt-llm/references/optimization.md)** – квантування, батчинг, налаштування KV‑кешу
- **[Multi‑GPU Setup](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/tensorrt-llm/references/multi-gpu.md)** – Tensor/ pipeline parallelism, multi‑node
- **[Serving Guide](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/tensorrt-llm/references/serving.md)** – продакшн‑розгортання, моніторинг, автоскейлінг

## Resources

- **Docs**: https://nvidia.github.io/TensorRT-LLM/
- **GitHub**: https://github.com/NVIDIA/TensorRT-LLM
- **Models**: https://huggingface.co/models?library=tensorrt_llm