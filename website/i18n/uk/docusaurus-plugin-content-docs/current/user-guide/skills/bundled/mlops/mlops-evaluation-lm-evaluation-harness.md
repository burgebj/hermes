---
title: "Оцінка Llms Harness — lm-eval-harness: бенчмарк LLMs (MMLU, GSM8K тощо)"
sidebar_label: "Evaluating Llms Harness"
description: "lm-eval-harness: бенчмарк LLMs (MMLU, GSM8K, тощо)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Оцінка LLMs Harness

lm-eval-harness: бенчмарк LLM (MMLU, GSM8K тощо).

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/mlops/evaluation/lm-evaluation-harness` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `lm-eval`, `transformers`, `vllm` |
| Platforms | linux, macos |
| Tags | `Evaluation`, `LM Evaluation Harness`, `Benchmarking`, `MMLU`, `HumanEval`, `GSM8K`, `EleutherAI`, `Model Quality`, `Academic Benchmarks`, `Industry Standard` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час активної навички.
:::

# lm-evaluation-harness — бенчмарк LLM

## Що всередині

Оцінює LLM за більш ніж 60 академічними бенчмарками (MMLU, HumanEval, GSM8K, TruthfulQA, HellaSwag). Використовуй для бенчмаркінгу якості моделей, порівняння моделей, звітування академічних результатів або відстеження прогресу навчання. Галузевий стандарт, що використовується EleutherAI, HuggingFace та великими лабораторіями. Підтримує HuggingFace, vLLM, API.

## Швидкий старт

lm-evaluation-harness оцінює LLM за більш ніж 60 академічними бенчмарками, використовуючи стандартизовані підказки та метрики.

**Встановлення**:
```bash
pip install lm-eval
```

**Оцінити будь‑яку модель HuggingFace**:
```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag \
  --device cuda:0 \
  --batch_size 8
```

**Переглянути доступні задачі**:
```bash
lm_eval --tasks list
```

## Типові робочі процеси

### Робочий процес 1: Стандартна оцінка бенчмарку

Оцінка моделі за основними бенчмарками (MMLU, GSM8K, HumanEval).

Скопіюй цей чекліст:

```
Benchmark Evaluation:
- [ ] Step 1: Choose benchmark suite
- [ ] Step 2: Configure model
- [ ] Step 3: Run evaluation
- [ ] Step 4: Analyze results
```

**Крок 1: Вибір набору бенчмарків**

**Основні бенчмарки розумових задач**:
- **MMLU** (Massive Multitask Language Understanding) — 57 предметів, множинний вибір
- **GSM8K** — задачі зі шкільної математики
- **HellaSwag** — здоровий глузд
- **TruthfulQA** — правдивість і фактичність
- **ARC** (AI2 Reasoning Challenge) — наукові питання

**Бенчмарки коду**:
- **HumanEval** — генерація коду Python (164 задачі)
- **MBPP** (Mostly Basic Python Problems) — програмування на Python

**Стандартний набір** (рекомендовано для випуску моделей):
```bash
--tasks mmlu,gsm8k,hellaswag,truthfulqa,arc_challenge
```

**Крок 2: Налаштування моделі**

**Модель HuggingFace**:
```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,dtype=bfloat16 \
  --tasks mmlu \
  --device cuda:0 \
  --batch_size auto  # Auto-detect optimal batch size
```

**Квантована модель (4‑bit/8‑bit)**:
```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,load_in_4bit=True \
  --tasks mmlu \
  --device cuda:0
```

**Власна контрольна точка**:
```bash
lm_eval --model hf \
  --model_args pretrained=/path/to/my-model,tokenizer=/path/to/tokenizer \
  --tasks mmlu \
  --device cuda:0
```

**Крок 3: Запуск оцінки**

```bash
# Full MMLU evaluation (57 subjects)
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu \
  --num_fewshot 5 \  # 5-shot evaluation (standard)
  --batch_size 8 \
  --output_path results/ \
  --log_samples  # Save individual predictions

# Multiple benchmarks at once
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag,truthfulqa,arc_challenge \
  --num_fewshot 5 \
  --batch_size 8 \
  --output_path results/llama2-7b-eval.json
```

**Крок 4: Аналіз результатів**

Результати збережено у `results/llama2-7b-eval.json`:

```json
{
  "results": {
    "mmlu": {
      "acc": 0.459,
      "acc_stderr": 0.004
    },
    "gsm8k": {
      "exact_match": 0.142,
      "exact_match_stderr": 0.006
    },
    "hellaswag": {
      "acc_norm": 0.765,
      "acc_norm_stderr": 0.004
    }
  },
  "config": {
    "model": "hf",
    "model_args": "pretrained=meta-llama/Llama-2-7b-hf",
    "num_fewshot": 5
  }
}
```

### Робочий процес 2: Відстеження прогресу навчання

Оцінка контрольних точок під час навчання.

```
Training Progress Tracking:
- [ ] Step 1: Set up periodic evaluation
- [ ] Step 2: Choose quick benchmarks
- [ ] Step 3: Automate evaluation
- [ ] Step 4: Plot learning curves
```

**Крок 1: Налаштування періодичної оцінки**

Оцінювати кожні N кроків навчання:

```bash
#!/bin/bash
# eval_checkpoint.sh

CHECKPOINT_DIR=$1
STEP=$2

lm_eval --model hf \
  --model_args pretrained=$CHECKPOINT_DIR/checkpoint-$STEP \
  --tasks gsm8k,hellaswag \
  --num_fewshot 0 \  # 0-shot for speed
  --batch_size 16 \
  --output_path results/step-$STEP.json
```

**Крок 2: Вибір швидких бенчмарків**

Швидкі бенчмарки для частих оцінок:
- **HellaSwag**: ~10 хвилин на 1 GPU
- **GSM8K**: ~5 хвилин
- **PIQA**: ~2 хвилини

Уникати для частих оцінок (занадто повільно):
- **MMLU**: ~2 години (57 предметів)
- **HumanEval**: потребує виконання коду

**Крок 3: Автоматизація оцінки**

Інтегруй у скрипт навчання:

```python
# In training loop
if step % eval_interval == 0:
    model.save_pretrained(f"checkpoints/step-{step}")

    # Run evaluation
    os.system(f"./eval_checkpoint.sh checkpoints step-{step}")
```

Або використай колбеки PyTorch Lightning:

```python
from pytorch_lightning import Callback

class EvalHarnessCallback(Callback):
    def on_validation_epoch_end(self, trainer, pl_module):
        step = trainer.global_step
        checkpoint_path = f"checkpoints/step-{step}"

        # Save checkpoint
        trainer.save_checkpoint(checkpoint_path)

        # Run lm-eval
        os.system(f"lm_eval --model hf --model_args pretrained={checkpoint_path} ...")
```

**Крок 4: Побудова графіків навчання**

```python
import json
import matplotlib.pyplot as plt

# Load all results
steps = []
mmlu_scores = []

for file in sorted(glob.glob("results/step-*.json")):
    with open(file) as f:
        data = json.load(f)
        step = int(file.split("-")[1].split(".")[0])
        steps.append(step)
        mmlu_scores.append(data["results"]["mmlu"]["acc"])

# Plot
plt.plot(steps, mmlu_scores)
plt.xlabel("Training Step")
plt.ylabel("MMLU Accuracy")
plt.title("Training Progress")
plt.savefig("training_curve.png")
```

### Робочий процес 3: Порівняння кількох моделей

Бенчмарк‑набір для порівняння моделей.

```
Model Comparison:
- [ ] Step 1: Define model list
- [ ] Step 2: Run evaluations
- [ ] Step 3: Generate comparison table
```

**Крок 1: Визначення списку моделей**

```bash
# models.txt
meta-llama/Llama-2-7b-hf
meta-llama/Llama-2-13b-hf
mistralai/Mistral-7B-v0.1
microsoft/phi-2
```

**Крок 2: Запуск оцінок**

```bash
#!/bin/bash
# eval_all_models.sh

TASKS="mmlu,gsm8k,hellaswag,truthfulqa"

while read model; do
    echo "Evaluating $model"

    # Extract model name for output file
    model_name=$(echo $model | sed 's/\//-/g')

    lm_eval --model hf \
      --model_args pretrained=$model,dtype=bfloat16 \
      --tasks $TASKS \
      --num_fewshot 5 \
      --batch_size auto \
      --output_path results/$model_name.json

done < models.txt
```

**Крок 3: Генерація таблиці порівняння**

```python
import json
import pandas as pd

models = [
    "meta-llama-Llama-2-7b-hf",
    "meta-llama-Llama-2-13b-hf",
    "mistralai-Mistral-7B-v0.1",
    "microsoft-phi-2"
]

tasks = ["mmlu", "gsm8k", "hellaswag", "truthfulqa"]

results = []
for model in models:
    with open(f"results/{model}.json") as f:
        data = json.load(f)
        row = {"Model": model.replace("-", "/")}
        for task in tasks:
            # Get primary metric for each task
            metrics = data["results"][task]
            if "acc" in metrics:
                row[task.upper()] = f"{metrics['acc']:.3f}"
            elif "exact_match" in metrics:
                row[task.upper()] = f"{metrics['exact_match']:.3f}"
        results.append(row)

df = pd.DataFrame(results)
print(df.to_markdown(index=False))
```

Вивід:
```
| Model                  | MMLU  | GSM8K | HELLASWAG | TRUTHFULQA |
|------------------------|-------|-------|-----------|------------|
| meta-llama/Llama-2-7b  | 0.459 | 0.142 | 0.765     | 0.391      |
| meta-llama/Llama-2-13b | 0.549 | 0.287 | 0.801     | 0.430      |
| mistralai/Mistral-7B   | 0.626 | 0.395 | 0.812     | 0.428      |
| microsoft/phi-2        | 0.560 | 0.613 | 0.682     | 0.447      |
```

### Робочий процес 4: Оцінка за допомогою vLLM (швидший інференс)

Використовуй бекенд vLLM для 5‑10× швидшої оцінки.

```
vLLM Evaluation:
- [ ] Step 1: Install vLLM
- [ ] Step 2: Configure vLLM backend
- [ ] Step 3: Run evaluation
```

**Крок 1: Встановити vLLM**

```bash
pip install vllm
```

**Крок 2: Налаштувати бекенд vLLM**

```bash
lm_eval --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,tensor_parallel_size=1,dtype=auto,gpu_memory_utilization=0.8 \
  --tasks mmlu \
  --batch_size auto
```

**Крок 3: Запуск оцінки**

vLLM працює в 5‑10× швидше, ніж стандартний HuggingFace:

```bash
# Standard HF: ~2 hours for MMLU on 7B model
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu \
  --batch_size 8

# vLLM: ~15-20 minutes for MMLU on 7B model
lm_eval --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,tensor_parallel_size=2 \
  --tasks mmlu \
  --batch_size auto
```

## Коли використовувати vs альтернативи

**Використовуй lm-evaluation-harness, коли:**
- Бенчмаркуєш моделі для академічних статей
- Порівнюєш якість моделей за стандартними задачами
- Відстежуєш прогрес навчання
- Звітуєш про стандартизовані метрики (всі використовують однакові підказки)
- Потрібна відтворювана оцінка

**Використовуй альтернативи замість:**
- **HELM** (Stanford): ширший спектр оцінки (справедливість, ефективність, калібрування)
- **AlpacaEval**: оцінка слідування інструкціям за допомогою суддів‑LLM
- **MT-Bench**: багатокрокова розмова
- **Custom scripts**: доменно‑специфічна оцінка

## Типові проблеми

**Issue: Evaluation too slow**

Використай бекенд vLLM:
```bash
lm_eval --model vllm \
  --model_args pretrained=model-name,tensor_parallel_size=2
```

Або зменш кількість fewshot‑прикладів:
```bash
--num_fewshot 0  # Instead of 5
```

Або оцінюй підмножину MMLU:
```bash
--tasks mmlu_stem  # Only STEM subjects
```

**Issue: Out of memory**

Зменш batch size:
```bash
--batch_size 1  # Or --batch_size auto
```

Використай квантизацію:
```bash
--model_args pretrained=model-name,load_in_8bit=True
```

Увімкни CPU offloading:
```bash
--model_args pretrained=model-name,device_map=auto,offload_folder=offload
```

**Issue: Different results than reported**

Перевір кількість fewshot:
```bash
--num_fewshot 5  # Most papers use 5-shot
```

Перевір точну назву задачі:
```bash
--tasks mmlu  # Not mmlu_direct or mmlu_fewshot
```

Переконайся, що модель і токенізатор збігаються:
```bash
--model_args pretrained=model-name,tokenizer=same-model-name
```

**Issue: HumanEval not executing code**

Встанови залежності для виконання:
```bash
pip install human-eval
```

Увімкни виконання коду:
```bash
lm_eval --model hf \
  --model_args pretrained=model-name \
  --tasks humaneval \
  --allow_code_execution  # Required for HumanEval
```

## Розширені теми

**Benchmark descriptions**: Дивись [references/benchmark-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/evaluation/lm-evaluation-harness/references/benchmark-guide.md) для докладного опису всіх 60+ задач, що вони вимірюють і як інтерпретувати результати.

**Custom tasks**: Дивись [references/custom-tasks.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/evaluation/lm-evaluation-harness/references/custom-tasks.md) для створення доменно‑специфічних оцінювальних задач.

**API evaluation**: Дивись [references/api-evaluation.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/evaluation/lm-evaluation-harness/references/api-evaluation.md) для оцінки моделей OpenAI, Anthropic та інших API.

**Multi-GPU strategies**: Дивись [references/distributed-eval.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/evaluation/lm-evaluation-harness/references/distributed-eval.md) для data parallel та tensor parallel оцінки.

## Апаратні вимоги

- **GPU**: NVIDIA (CUDA 11.8+), працює на CPU (дуже повільно)
- **VRAM**:
  - 7 B модель: 16 GB (bf16) або 8 GB (8‑bit)
  - 13 B модель: 28 GB (bf16) або 14 GB (8‑bit)
  - 70 B модель: потребує multi‑GPU або квантизації
- **Час** (7 B модель, один A100):
  - HellaSwag: 10 хвилин
  - GSM8K: 5 хвилин
  - MMLU (повний): 2 години
  - HumanEval: 20 хвилин

## Ресурси

- GitHub: https://github.com/EleutherAI/lm-evaluation-harness
- Docs: https://github.com/EleutherAI/lm-evaluation-harness/tree/main/docs
- Task library: 60+ задач, включаючи MMLU, GSM8K, HumanEval, TruthfulQA, HellaSwag, ARC, WinoGrande тощо.
- Leaderboard: https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard (використовує цей harness)