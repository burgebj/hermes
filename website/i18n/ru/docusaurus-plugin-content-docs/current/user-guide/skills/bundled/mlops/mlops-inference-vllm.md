---
title: "Обслуживание LLM vLLM — vLLM: высокопроизводительное обслуживание LLM, OpenAI API, квантизация"
sidebar_label: "Serving Llms Vllm"
description: "vLLM: высокопроизводительное обслуживание LLM, OpenAI API, квантование"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Обслуживание LLM‑ов vLLM

vLLM: высокопроизводительное обслуживание LLM, совместимый с OpenAI API, квантизация.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/mlops/inference/vllm` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `vllm`, `torch`, `transformers` |
| Platforms | linux, macos |
| Tags | `vLLM`, `Inference Serving`, `PagedAttention`, `Continuous Batching`, `High Throughput`, `Production`, `OpenAI API`, `Quantization`, `Tensor Parallelism` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# vLLM — высокопроизводительное обслуживание LLM

## Когда использовать

Используй, когда развертываешь производственные API LLM, оптимизируешь задержку/пропускную способность вывода или обслуживаешь модели с ограниченной видеопамятью. Поддерживает совместимые с OpenAI конечные точки, квантизацию (GPTQ/AWQ/FP8) и тензорный параллелизм.

## Быстрый старт

vLLM достигает в 24 раз выше пропускной способности, чем стандартные transformers, благодаря PagedAttention (блочный KV‑кеш) и непрерывному батчингу (смешивание запросов prefill/decode).

**Установка**:
```bash
pip install vllm
```

**Базовый офлайн‑инференс**:
```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3-8B-Instruct")
sampling = SamplingParams(temperature=0.7, max_tokens=256)

outputs = llm.generate(["Explain quantum computing"], sampling)
print(outputs[0].outputs[0].text)
```

**Сервер, совместимый с OpenAI**:
```bash
vllm serve meta-llama/Llama-3-8B-Instruct

# Query with OpenAI SDK
python -c "
from openai import OpenAI
client = OpenAI(base_url='http://localhost:8000/v1', api_key='EMPTY')
print(client.chat.completions.create(
    model='meta-llama/Llama-3-8B-Instruct',
    messages=[{'role': 'user', 'content': 'Hello!'}]
).choices[0].message.content)
"
```

## Распространённые рабочие процессы

### Рабочий процесс 1: Развёртывание производственного API

Скопируй этот чек‑лист и отслеживай прогресс:

```
Deployment Progress:
- [ ] Step 1: Configure server settings
- [ ] Step 2: Test with limited traffic
- [ ] Step 3: Enable monitoring
- [ ] Step 4: Deploy to production
- [ ] Step 5: Verify performance metrics
```

**Шаг 1: Настройка параметров сервера**

Выбери конфигурацию в зависимости от размера модели:

```bash
# For 7B-13B models on single GPU
vllm serve meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --max-model-len 8192 \
  --port 8000

# For 30B-70B models with tensor parallelism
vllm serve meta-llama/Llama-2-70b-hf \
  --tensor-parallel-size 4 \
  --gpu-memory-utilization 0.9 \
  --quantization awq \
  --port 8000

# For production with caching and metrics
vllm serve meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching \
  --enable-metrics \
  --metrics-port 9090 \
  --port 8000 \
  --host 0.0.0.0
```

**Шаг 2: Тестирование с ограниченным трафиком**

Запусти нагрузочный тест перед продакшеном:

```bash
# Install load testing tool
pip install locust

# Create test_load.py with sample requests
# Run: locust -f test_load.py --host http://localhost:8000
```

Проверь, что TTFT (time to first token) < 500 мс и пропускная способность > 100 запросов/сек.

**Шаг 3: Включение мониторинга**

vLLM экспортирует метрики Prometheus на порт 9090:

```bash
curl http://localhost:9090/metrics | grep vllm
```

Ключевые метрики для наблюдения:
- `vllm:time_to_first_token_seconds` — задержка
- `vllm:num_requests_running` — активные запросы
- `vllm:gpu_cache_usage_perc` — использование KV‑кеша

**Шаг 4: Развёртывание в продакшн**

Используй Docker для согласованного развёртывания:

```bash
# Run vLLM in Docker
docker run --gpus all -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching
```

**Шаг 5: Проверка метрик производительности**

Убедись, что развертывание достигает целей:
- TTFT < 500 мс (для коротких подсказок)
- Пропускная способность > целевое значение запросов/сек
- Использование GPU > 80 %
- В логах нет ошибок OOM

### Рабочий процесс 2: Офлайн‑батч‑инференс

Для обработки больших наборов данных без серверных накладных расходов.

Скопируй этот чек‑лист:

```
Batch Processing:
- [ ] Step 1: Prepare input data
- [ ] Step 2: Configure LLM engine
- [ ] Step 3: Run batch inference
- [ ] Step 4: Process results
```

**Шаг 1: Подготовка входных данных**
```python
# Load prompts from file
prompts = []
with open("prompts.txt") as f:
    prompts = [line.strip() for line in f]

print(f"Loaded {len(prompts)} prompts")
```

**Шаг 2: Настройка движка LLM**
```python
from vllm import LLM, SamplingParams

llm = LLM(
    model="meta-llama/Llama-3-8B-Instruct",
    tensor_parallel_size=2,  # Use 2 GPUs
    gpu_memory_utilization=0.9,
    max_model_len=4096
)

sampling = SamplingParams(
    temperature=0.7,
    top_p=0.95,
    max_tokens=512,
    stop=["</s>", "\n\n"]
)
```

**Шаг 3: Запуск батч‑инференса**
vLLM автоматически группирует запросы для эффективности:
```python
# Process all prompts in one call
outputs = llm.generate(prompts, sampling)

# vLLM handles batching internally
# No need to manually chunk prompts
```

**Шаг 4: Обработка результатов**
```python
# Extract generated text
results = []
for output in outputs:
    prompt = output.prompt
    generated = output.outputs[0].text
    results.append({
        "prompt": prompt,
        "generated": generated,
        "tokens": len(output.outputs[0].token_ids)
    })

# Save to file
import json
with open("results.jsonl", "w") as f:
    for result in results:
        f.write(json.dumps(result) + "\n")

print(f"Processed {len(results)} prompts")
```

### Рабочий процесс 3: Обслуживание квантизированных моделей

Размещай крупные модели при ограниченной видеопамяти.

```
Quantization Setup:
- [ ] Step 1: Choose quantization method
- [ ] Step 2: Find or create quantized model
- [ ] Step 3: Launch with quantization flag
- [ ] Step 4: Verify accuracy
```

**Шаг 1: Выбор метода квантизации**

- **AWQ**: лучший вариант для моделей 70 B, минимальная потеря точности
- **GPTQ**: широкий спектр поддерживаемых моделей, хорошее сжатие
- **FP8**: самая быстрая на GPU H100

**Шаг 2: Поиск или создание квантизированной модели**

Используй предквантизированные модели из HuggingFace:
```bash
# Search for AWQ models
# Example: TheBloke/Llama-2-70B-AWQ
```

**Шаг 3: Запуск с флагом квантизации**
```bash
# Using pre-quantized model
vllm serve TheBloke/Llama-2-70B-AWQ \
  --quantization awq \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95

# Results: 70B model in ~40GB VRAM
```

**Шаг 4: Проверка точности**
Тестируй, что выводы соответствуют ожидаемому качеству:
```python
# Compare quantized vs non-quantized responses
# Verify task-specific performance unchanged
```

## Когда использовать vs альтернативы

**Используй vLLM, когда:**
- Разворачиваешь производственные API LLM (100 + запросов/сек)
- Обслуживаешь совместимые с OpenAI конечные точки
- Имеется ограниченная видеопамять, но нужны крупные модели
- Приложения с несколькими пользователями (чат‑боты, ассистенты)
- Требуется низкая задержка при высокой пропускной способности

**Выбирай альтернативы, когда:**
- **llama.cpp**: инференс на CPU/edge, один пользователь
- **HuggingFace transformers**: исследования, прототипирование, единичные генерации
- **TensorRT-LLM**: только NVIDIA, нужен абсолютный максимум производительности
- **Text-Generation-Inference**: уже в экосистеме HuggingFace

## Распространённые проблемы

**Проблема: Недостаток памяти при загрузке модели**

Снизь потребление памяти:
```bash
vllm serve MODEL \
  --gpu-memory-utilization 0.7 \
  --max-model-len 4096
```

Или используй квантизацию:
```bash
vllm serve MODEL --quantization awq
```

**Проблема: Медленный первый токен (TTFT > 1 сек)**

Включи кэширование префиксов для повторяющихся подсказок:
```bash
vllm serve MODEL --enable-prefix-caching
```

Для длинных подсказок включи префилл по частям:
```bash
vllm serve MODEL --enable-chunked-prefill
```

**Проблема: Ошибка «model not found»**

Используй `--trust-remote-code` для кастомных моделей:
```bash
vllm serve MODEL --trust-remote-code
```

**Проблема: Низкая пропускная способность (<50 запросов/сек)**

Увеличь количество одновременных последовательностей:
```bash
vllm serve MODEL --max-num-seqs 512
```

Проверь использование GPU через `nvidia-smi` — должно быть > 80 %.

**Проблема: Инференс медленнее ожидаемого**

Убедись, что тензорный параллелизм использует количество GPU, являющееся степенью двойки:
```bash
vllm serve MODEL --tensor-parallel-size 4  # Not 3
```

Включи спекулятивную декодировку для ускорения генерации:
```bash
vllm serve MODEL --speculative-model DRAFT_MODEL
```

## Продвинутые темы

**Шаблоны развёртывания сервера**: см. [references/server-deployment.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/vllm/references/server-deployment.md) для конфигураций Docker, Kubernetes и балансировки нагрузки.

**Оптимизация производительности**: см. [references/optimization.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/vllm/references/optimization.md) для настройки PagedAttention, деталей непрерывного батчинга и результатов бенчмарков.

**Руководство по квантизации**: см. [references/quantization.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/vllm/references/quantization.md) для настройки AWQ/GPTQ/FP8, подготовки модели и сравнения точности.

**Устранение неполадок**: см. [references/troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/vllm/references/troubleshooting.md) для подробных сообщений об ошибках, шагов отладки и диагностики производительности.

## Требования к оборудованию

- **Небольшие модели (7 B‑13 B)**: 1 × A10 (24 GB) или A100 (40 GB)
- **Средние модели (30 B‑40 B)**: 2 × A100 (40 GB) с тензорным параллелизмом
- **Большие модели (70 B+)**: 4 × A100 (40 GB) или 2 × A100 (80 GB), используйте AWQ/GPTQ

Поддерживаемые платформы: NVIDIA (основная), AMD ROCm, Intel GPUs, TPUs

## Ресурсы

- Официальная документация: https://docs.vllm.ai
- GitHub: https://github.com/vllm-project/vllm
- Статья: «Efficient Memory Management for Large Language Model Serving with PagedAttention» (SOSP 2023)
- Сообщество: https://discuss.vllm.ai