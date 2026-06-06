---
title: "Оценка Llms Harness — lm-eval-harness: бенчмарк LLM (MMLU, GSM8K и др.)"
sidebar_label: "Evaluating Llms Harness"
description: "lm-eval-harness: бенчмарк LLM (MMLU, GSM8K и др.)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Оценка LLM Harness

lm-eval-harness: бенчмарк LLM (MMLU, GSM8K и др.).

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при активном навыке.
:::

# lm-evaluation-harness — бенчмарк LLM

## Что внутри

Оценивает LLM по более чем 60 академическим бенчмаркам (MMLU, HumanEval, GSM8K, TruthfulQA, HellaSwag). Используется для бенчмаркинга качества модели, сравнения моделей, публикации академических результатов или отслеживания прогресса обучения. Отраслевой стандарт, используемый EleutherAI, HuggingFace и крупными лабораториями. Поддерживает HuggingFace, vLLM, API.

## Быстрый старт

lm-evaluation-harness оценивает LLM по более чем 60 академическим бенчмаркам с использованием стандартизированных подсказок и метрик.

**Установка**:
```bash
pip install lm-eval
```

**Оценить любую модель HuggingFace**:
```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf \
  --tasks mmlu,gsm8k,hellaswag \
  --device cuda:0 \
  --batch_size 8
```

**Посмотреть доступные задачи**:
```bash
lm_eval --tasks list
```

## Распространённые рабочие процессы

### Рабочий процесс 1: Стандартная оценка бенчмарка

Оценка модели по базовым бенчмаркам (MMLU, GSM8K, HumanEval).

Скопируй этот чеклист:

```
Benchmark Evaluation:
- [ ] Step 1: Choose benchmark suite
- [ ] Step 2: Configure model
- [ ] Step 3: Run evaluation
- [ ] Step 4: Analyze results
```

**Шаг 1: Выбери набор бенчмарков**

**Базовые бенчмарки рассуждений**:
- **MMLU** (Massive Multitask Language Understanding) — 57 предметов, множественный выбор
- **GSM8K** — задачи по математике начальной школы
- **HellaSwag** — рассуждения на основе здравого смысла
- **TruthfulQA** — правдивость и фактичность
- **ARC** (AI2 Reasoning Challenge) — вопросы по естественным наукам

**Бенчмарки кода**:
- **HumanEval** — генерация кода Python (164 задачи)
- **MBPP** (Mostly Basic Python Problems) — кодинг на Python

**Стандартный набор** (рекомендовано для релизов моделей):
```bash
--tasks mmlu,gsm8k,hellaswag,truthfulqa,arc_challenge
```

**Шаг 2: Настройка модели**

**Модель HuggingFace**:
```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,dtype=bfloat16 \
  --tasks mmlu \
  --device cuda:0 \
  --batch_size auto  # Auto-detect optimal batch size
```

**Квантованная модель (4‑bit/8‑bit)**:
```bash
lm_eval --model hf \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,load_in_4bit=True \
  --tasks mmlu \
  --device cuda:0
```

**Пользовательская контрольная точка**:
```bash
lm_eval --model hf \
  --model_args pretrained=/path/to/my-model,tokenizer=/path/to/tokenizer \
  --tasks mmlu \
  --device cuda:0
```

**Шаг 3: Запуск оценки**
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

**Шаг 4: Анализ результатов**

Результаты сохранены в `results/llama2-7b-eval.json`:

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

### Рабочий процесс 2: Отслеживание прогресса обучения

Оценка контрольных точек во время обучения.

```
Training Progress Tracking:
- [ ] Step 1: Set up periodic evaluation
- [ ] Step 2: Choose quick benchmarks
- [ ] Step 3: Automate evaluation
- [ ] Step 4: Plot learning curves
```

**Шаг 1: Настройка периодической оценки**

Оценивать каждые N шагов обучения:

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

**Шаг 2: Выбор быстрых бенчмарков**

Быстрые бенчмарки для частой оценки:
- **HellaSwag**: ~10 минут на 1 GPU
- **GSM8K**: ~5 минут
- **PIQA**: ~2 минуты

Избегать для частой оценки (слишком медленно):
- **MMLU**: ~2 часа (57 предметов)
- **HumanEval**: требует выполнения кода

**Шаг 3: Автоматизация оценки**

Интеграция со скриптом обучения:

```python
# In training loop
if step % eval_interval == 0:
    model.save_pretrained(f"checkpoints/step-{step}")

    # Run evaluation
    os.system(f"./eval_checkpoint.sh checkpoints step-{step}")
```

Или использовать callbacks PyTorch Lightning:

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

**Шаг 4: Построение кривых обучения**
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

### Рабочий процесс 3: Сравнение нескольких моделей

Набор бенчмарков для сравнения моделей.

```
Model Comparison:
- [ ] Step 1: Define model list
- [ ] Step 2: Run evaluations
- [ ] Step 3: Generate comparison table
```

**Шаг 1: Определить список моделей**
```bash
# models.txt
meta-llama/Llama-2-7b-hf
meta-llama/Llama-2-13b-hf
mistralai/Mistral-7B-v0.1
microsoft/phi-2
```

**Шаг 2: Запустить оценки**
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

**Шаг 3: Сгенерировать таблицу сравнения**
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

Вывод:
```
| Model                  | MMLU  | GSM8K | HELLASWAG | TRUTHFULQA |
|------------------------|-------|-------|-----------|------------|
| meta-llama/Llama-2-7b  | 0.459 | 0.142 | 0.765     | 0.391      |
| meta-llama/Llama-2-13b | 0.549 | 0.287 | 0.801     | 0.430      |
| mistralai/Mistral-7B   | 0.626 | 0.395 | 0.812     | 0.428      |
| microsoft/phi-2        | 0.560 | 0.613 | 0.682     | 0.447      |
```

### Рабочий процесс 4: Оценка с vLLM (быстрее инференса)

Использовать бэкенд vLLM для оценки в 5‑10 раз быстрее.

```
vLLM Evaluation:
- [ ] Step 1: Install vLLM
- [ ] Step 2: Configure vLLM backend
- [ ] Step 3: Run evaluation
```

**Шаг 1: Установить vLLM**
```bash
pip install vllm
```

**Шаг 2: Настроить бэкенд vLLM**
```bash
lm_eval --model vllm \
  --model_args pretrained=meta-llama/Llama-2-7b-hf,tensor_parallel_size=1,dtype=auto,gpu_memory_utilization=0.8 \
  --tasks mmlu \
  --batch_size auto
```

**Шаг 3: Запустить оценку**

vLLM в 5‑10× быстрее, чем стандартный HuggingFace:

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

## Когда использовать vs альтернативы

**Используй lm-evaluation-harness, когда:**
- Проводишь бенчмарк моделей для академических статей
- Сравниваешь качество моделей по стандартным задачам
- Отслеживаешь прогресс обучения
- Публикуешь стандартизированные метрики (у всех одинаковые подсказки)
- Нужна воспроизводимая оценка

**Используй альтернативы вместо него:**
- **HELM** (Stanford): более широкий спектр оценок (справедливость, эффективность, калибровка)
- **AlpacaEval**: оценка следования инструкциям с судьями‑LLM
- **MT-Bench**: многотуровая разговорная оценка
- **Custom scripts**: оценка, специфичная для домена

## Распространённые проблемы

**Проблема: Оценка слишком медленная**

Использовать бэкенд vLLM:
```bash
lm_eval --model vllm \
  --model_args pretrained=model-name,tensor_parallel_size=2
```

Или уменьшить количество few‑shot примеров:
```bash
--num_fewshot 0  # Instead of 5
```

Или оценить подмножество MMLU:
```bash
--tasks mmlu_stem  # Only STEM subjects
```

**Проблема: Недостаток памяти**

Уменьшить размер батча:
```bash
--batch_size 1  # Or --batch_size auto
```

Использовать квантование:
```bash
--model_args pretrained=model-name,load_in_8bit=True
```

Включить выгрузку на CPU:
```bash
--model_args pretrained=model-name,device_map=auto,offload_folder=offload
```

**Проблема: Результаты отличаются от опубликованных**

Проверить количество few‑shot примеров:
```bash
--num_fewshot 5  # Most papers use 5-shot
```

Проверить точное название задачи:
```bash
--tasks mmlu  # Not mmlu_direct or mmlu_fewshot
```

Убедиться, что модель и токенизатор совпадают:
```bash
--model_args pretrained=model-name,tokenizer=same-model-name
```

**Проблема: HumanEval не выполняет код**

Установить зависимости для выполнения:
```bash
pip install human-eval
```

Включить выполнение кода:
```bash
lm_eval --model hf \
  --model_args pretrained=model-name \
  --tasks humaneval \
  --allow_code_execution  # Required for HumanEval
```

## Продвинутые темы

**Описание бенчмарков**: см. [references/benchmark-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/evaluation/lm-evaluation-harness/references/benchmark-guide.md) для подробного описания всех 60+ задач, что они измеряют и как интерпретировать результаты.

**Пользовательские задачи**: см. [references/custom-tasks.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/evaluation/lm-evaluation-harness/references/custom-tasks.md) для создания оценок, специфичных для домена.

**Оценка API**: см. [references/api-evaluation.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/evaluation/lm-evaluation-harness/references/api-evaluation.md) для оценки моделей OpenAI, Anthropic и других API.

**Стратегии мульти‑GPU**: см. [references/distributed-eval.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/evaluation/lm-evaluation-harness/references/distributed-eval.md) для data parallel и tensor parallel оценки.

## Требования к оборудованию

- **GPU**: NVIDIA (CUDA 11.8+), работает на CPU (очень медленно)
- **VRAM**:
  - модель 7B: 16 GB (bf16) или 8 GB (8‑bit)
  - модель 13B: 28 GB (bf16) или 14 GB (8‑bit)
  - модель 70B: требуется несколько GPU или квантование
- **Время** (модель 7B, один A100):
  - HellaSwag: 10 минут
  - GSM8K: 5 минут
  - MMLU (полный): 2 часа
  - HumanEval: 20 минут

## Ресурсы

- GitHub: https://github.com/EleutherAI/lm-evaluation-harness
- Docs: https://github.com/EleutherAI/lm-evaluation-harness/tree/main/docs
- Библиотека задач: 60+ задач, включая MMLU, GSM8K, HumanEval, TruthfulQA, HellaSwag, ARC, WinoGrande и др.
- Таблица лидеров: https://huggingface.co/spaces/HuggingFaceH4/open_llm_leaderboard (использует этот harness)