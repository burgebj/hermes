---
title: "Оптимизирует вывод LLM с помощью NVIDIA TensorRT для максимальной пропускной способности и минимальной задержки"
sidebar_label: "Tensorrt Llm"
description: "Оптимизирует вывод LLM с помощью NVIDIA TensorRT для максимальной пропускной способности и минимальной задержки"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Tensorrt Llm

Оптимизирует инференс LLM с помощью NVIDIA TensorRT для максимальной пропускной способности и минимальной задержки. Используется для продакшн‑развёртывания на GPU NVIDIA (A100/H100), когда требуется в 10–100 раз быстрее инференс, чем в PyTorch, или для обслуживания моделей с квантизацией (FP8/INT4), динамической пакетной обработкой и масштабированием на несколько GPU.

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
Следующее — полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# TensorRT-LLM

Открытая библиотека NVIDIA для оптимизации инференса LLM с передовой производительностью на GPU NVIDIA.

## When to use TensorRT-LLM

**Используй TensorRT-LLM, когда:**
- Развёртывание на GPU NVIDIA (A100, H100, GB200)
- Требуется максимальная пропускная способность (24 000+ токенов/сек на Llama 3)
- Необходима низкая задержка для приложений в реальном времени
- Работа с квантизированными моделями (FP8, INT4, FP4)
- Масштабирование на несколько GPU или узлов

**Используй vLLM вместо него, когда:**
- Нужна более простая настройка и API, ориентированное на Python
- Требуется PagedAttention без компиляции TensorRT
- Работаешь с GPU AMD или другим не‑NVIDIA оборудованием

**Используй llama.cpp вместо него, когда:**
- Развёртывание на CPU или Apple Silicon
- Нужен edge‑развёртывание без GPU NVIDIA
- Требуется более простой формат квантизации GGUF

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

```bash
# Start server (automatic model download and compilation)
trtllm-serve meta-llama/Meta-Llama-3-8B \
    --tp_size 4 \              # Tensor parallelism (4 GPUs)
    --max_batch_size 256 \
    --max_num_tokens 4096

# Client request
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3-8B",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

## Key features

### Performance optimizations
- **In-flight batching**: Динамическая пакетная обработка во время генерации
- **Paged KV cache**: Эффективное управление памятью
- **Flash Attention**: Оптимизированные ядра внимания
- **Quantization**: FP8, INT4, FP4 для 2–4× более быстрого инференса
- **CUDA graphs**: Сниженное накладное время запуска ядра

### Parallelism
- **Tensor parallelism (TP)**: Разделение модели между GPU
- **Pipeline parallelism (PP)**: Распределение по слоям
- **Expert parallelism**: Для моделей Mixture-of-Experts
- **Multi-node**: Масштабирование за пределы одной машины

### Advanced features
- **Speculative decoding**: Быстрее генерация с черновыми моделями
- **LoRA serving**: Эффективное развёртывание нескольких адаптеров
- **Disaggregated serving**: Разделение предзаполнения и генерации

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

### Multi-GPU deployment

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

**Meta Llama 3-8B** (GPU H100):
- Throughput: 24 000 токенов/сек
- Latency: ~10 ms за токен
- По сравнению с PyTorch: **100× быстрее**

**Llama 3-70B** (8× A100 80GB):
- Квантизация FP8: в 2 раза быстрее, чем FP16
- Память: снижение на 50 % при FP8

## Supported models

- **LLaMA family**: Llama 2, Llama 3, CodeLlama
- **GPT family**: GPT‑2, GPT‑J, GPT‑NeoX
- **Qwen**: Qwen, Qwen2, QwQ
- **DeepSeek**: DeepSeek‑V2, DeepSeek‑V3
- **Mixtral**: Mixtral‑8x7B, Mixtral‑8x22B
- **Vision**: LLaVA, Phi‑3‑vision
- **100+ models** on HuggingFace

## References

- **[Optimization Guide](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/tensorrt-llm/references/optimization.md)** — квантизация, пакетирование, настройка KV‑кэша
- **[Multi-GPU Setup](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/tensorrt-llm/references/multi-gpu.md)** — Tensor/pipeline parallelism, multi-node
- **[Serving Guide](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/tensorrt-llm/references/serving.md)** — продакшн‑развёртывание, мониторинг, автоскейлинг

## Resources

- **Docs**: https://nvidia.github.io/TensorRT-LLM/
- **GitHub**: https://github.com/NVIDIA/TensorRT-LLM
- **Models**: https://huggingface.co/models?library=tensorrt_llm