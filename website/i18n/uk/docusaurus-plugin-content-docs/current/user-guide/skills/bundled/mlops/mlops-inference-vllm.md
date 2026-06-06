---
title: "Обслуговування LLMs Vllm — vLLM: високопродуктивне обслуговування LLM, OpenAI API, квантування"
sidebar_label: "Serving Llms Vllm"
description: "vLLM: високопродуктивне обслуговування LLM, OpenAI API, квантизація"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Обслуговування LLM‑ів Vllm

vLLM: високопродуктивне обслуговування LLM, OpenAI API, квантування.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# vLLM — високопродуктивне обслуговування LLM

## Коли використовувати

Використовуй, коли розгортаєш LLM‑API у продакшн, оптимізуєш затримку/пропускну здатність інференсу або обслуговуєш моделі з обмеженою пам’яттю GPU. Підтримує OpenAI‑сумісні кінцеві точки, квантування (GPTQ/AWQ/FP8) та тензорний паралелізм.

## Швидкий старт

vLLM забезпечує в 24 рази вищу пропускну здатність, ніж стандартні transformers, завдяки PagedAttention (блоковий KV‑кеш) та безперервному батчінгу (змішування запитів prefill/decode).

**Встановлення**:
```bash
pip install vllm
```

**Базовий офлайн‑інференс**:
```python
from vllm import LLM, SamplingParams

llm = LLM(model="meta-llama/Llama-3-8B-Instruct")
sampling = SamplingParams(temperature=0.7, max_tokens=256)

outputs = llm.generate(["Explain quantum computing"], sampling)
print(outputs[0].outputs[0].text)
```

**Сервер, сумісний з OpenAI**:
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

## Типові робочі процеси

### Робочий процес 1: Розгортання продакшн‑API

Скопіюй цей чек‑ліст і відстежуй прогрес:

```
Deployment Progress:
- [ ] Step 1: Configure server settings
- [ ] Step 2: Test with limited traffic
- [ ] Step 3: Enable monitoring
- [ ] Step 4: Deploy to production
- [ ] Step 5: Verify performance metrics
```

**Крок 1: Налаштування серверних параметрів**

Вибери конфігурацію залежно від розміру моделі:

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

**Крок 2: Тестування з обмеженим навантаженням**

Запусти навантажувальний тест перед продакшн:

```bash
# Install load testing tool
pip install locust

# Create test_load.py with sample requests
# Run: locust -f test_load.py --host http://localhost:8000
```

Перевір, що TTFT (time to first token) < 500 ms і пропускна здатність > 100 req/sec.

**Крок 3: Увімкнення моніторингу**

vLLM експонує метрики Prometheus на порту 9090:

```bash
curl http://localhost:9090/metrics | grep vllm
```

Ключові метрики для моніторингу:
- `vllm:time_to_first_token_seconds` — затримка
- `vllm:num_requests_running` — активні запити
- `vllm:gpu_cache_usage_perc` — використання KV‑кешу

**Крок 4: Розгортання у продакшн**

Використовуй Docker для уніфікованого розгортання:

```bash
# Run vLLM in Docker
docker run --gpus all -p 8000:8000 \
  vllm/vllm-openai:latest \
  --model meta-llama/Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  --enable-prefix-caching
```

**Крок 5: Перевірка продуктивності**

Переконайся, що розгортання відповідає цільовим показникам:
- TTFT < 500 ms (для коротких підказок)
- Пропускна здатність > цільовий req/sec
- Використання GPU > 80 %
- Відсутність OOM‑помилок у логах

### Робочий процес 2: Офлайн‑батч‑інференс

Для обробки великих наборів даних без серверного навантаження.

Скопіюй цей чек‑ліст:

```
Batch Processing:
- [ ] Step 1: Prepare input data
- [ ] Step 2: Configure LLM engine
- [ ] Step 3: Run batch inference
- [ ] Step 4: Process results
```

**Крок 1: Підготовка вхідних даних**
```python
# Load prompts from file
prompts = []
with open("prompts.txt") as f:
    prompts = [line.strip() for line in f]

print(f"Loaded {len(prompts)} prompts")
```

**Крок 2: Налаштування LLM‑двигуна**
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

**Крок 3: Запуск батч‑інференсу**

vLLM автоматично батчить запити для підвищення ефективності:

```python
# Process all prompts in one call
outputs = llm.generate(prompts, sampling)

# vLLM handles batching internally
# No need to manually chunk prompts
```

**Крок 4: Обробка результатів**
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

### Робочий процес 3: Обслуговування квантизованих моделей

Вмісти великі моделі в обмежену пам’ять GPU.

```
Quantization Setup:
- [ ] Step 1: Choose quantization method
- [ ] Step 2: Find or create quantized model
- [ ] Step 3: Launch with quantization flag
- [ ] Step 4: Verify accuracy
```

**Крок 1: Вибір методу квантування**

- **AWQ**: найкраще для моделей 70B, мінімальна втрата точності
- **GPTQ**: широкий спектр підтримуваних моделей, хороша компресія
- **FP8**: найшвидше на GPU H100

**Крок 2: Пошук або створення квантизованої моделі**

Використай попередньо квантизовані моделі з HuggingFace:

```bash
# Search for AWQ models
# Example: TheBloke/Llama-2-70B-AWQ
```

**Крок 3: Запуск з прапорцем квантування**
```bash
# Using pre-quantized model
vllm serve TheBloke/Llama-2-70B-AWQ \
  --quantization awq \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.95

# Results: 70B model in ~40GB VRAM
```

**Крок 4: Перевірка точності**

Перевір, що вихідні дані відповідають очікуваній якості:

```python
# Compare quantized vs non-quantized responses
# Verify task-specific performance unchanged
```

## Коли використовувати vs альтернативи

**Використовуй vLLM, коли:**
- Розгортаєш продакшн‑API LLM (100+ req/sec)
- Обслуговуєш OpenAI‑сумісні кінцеві точки
- Обмежена пам’ять GPU, а потрібні великі моделі
- Багатокористувацькі додатки (чат‑боти, асистенти)
- Потрібна низька затримка при високій пропускній здатності

**Використовуй альтернативи:**
- **llama.cpp**: інференс на CPU/edge, один користувач
- **HuggingFace transformers**: дослідження, прототипування, одноразова генерація
- **TensorRT-LLM**: лише NVIDIA, потрібна абсолютна максимальна продуктивність
- **Text-Generation-Inference**: вже в екосистемі HuggingFace

## Типові проблеми

**Issue: Out of memory during model loading**

Зменш використання пам’яті:
```bash
vllm serve MODEL \
  --gpu-memory-utilization 0.7 \
  --max-model-len 4096
```

Або застосуй квантування:
```bash
vllm serve MODEL --quantization awq
```

**Issue: Slow first token (TTFT > 1 second)**

Увімкни кешування префіксів для повторюваних підказок:
```bash
vllm serve MODEL --enable-prefix-caching
```

Для довгих підказок увімкни chunked prefill:
```bash
vllm serve MODEL --enable-chunked-prefill
```

**Issue: Model not found error**

Використай `--trust-remote-code` для кастомних моделей:
```bash
vllm serve MODEL --trust-remote-code
```

**Issue: Low throughput (<50 req/sec)**

Збільш кількість одночасних послідовностей:
```bash
vllm serve MODEL --max-num-seqs 512
```

Перевір використання GPU за допомогою `nvidia-smi` — має бути >80 %.

**Issue: Inference slower than expected**

Переконайся, що тензорний паралелізм використовує кількість GPU, що є степенем 2:
```bash
vllm serve MODEL --tensor-parallel-size 4  # Not 3
```

Увімкни спекулятивне декодування для швидшої генерації:
```bash
vllm serve MODEL --speculative-model DRAFT_MODEL
```

## Розширені теми

**Server deployment patterns**: Дивись [references/server-deployment.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/vllm/references/server-deployment.md) для конфігурацій Docker, Kubernetes та балансування навантаження.

**Performance optimization**: Дивись [references/optimization.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/vllm/references/optimization.md) для налаштувань PagedAttention, деталей безперервного батчінгу та результатів бенчмарків.

**Quantization guide**: Дивись [references/quantization.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/vllm/references/quantization.md) для налаштувань AWQ/GPTQ/FP8, підготовки моделей та порівняння точності.

**Troubleshooting**: Дивись [references/troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/vllm/references/troubleshooting.md) для докладних повідомлень про помилки, кроків діагностики та оптимізації продуктивності.

## Вимоги до обладнання

- **Малі моделі (7B‑13B)**: 1× A10 (24 GB) або A100 (40 GB)
- **Середні моделі (30B‑40B)**: 2× A100 (40 GB) з тензорним паралелізмом
- **Великі моделі (70B+)**: 4× A100 (40 GB) або 2× A100 (80 GB), використовуйте AWQ/GPTQ

Підтримувані платформи: NVIDIA (основна), AMD ROCm, Intel GPUs, TPUs

## Ресурси

- Official docs: https://docs.vllm.ai
- GitHub: https://github.com/vllm-project/vllm
- Paper: "Efficient Memory Management for Large Language Model Serving with PagedAttention" (SOSP 2023)
- Community: https://discuss.vllm.ai