---
title: "Тонкая настройка с Trl — TRL: SFT, DPO, PPO, GRPO, моделирование вознаграждения для LLM RLHF"
sidebar_label: "Fine Tuning With Trl"
description: "TRL: SFT, DPO, PPO, GRPO, моделирование вознаграждения для LLM RLHF"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Тонкая настройка с Trl

TRL: SFT, DPO, PPO, GRPO, моделирование наград для LLM RLHF.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/trl-fine-tuning` |
| Path | `optional-skills/mlops/training/trl-fine-tuning` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `trl`, `transformers`, `datasets`, `peft`, `accelerate`, `torch` |
| Platforms | linux, macos, windows |
| Tags | `Post-Training`, `TRL`, `Reinforcement Learning`, `Fine-Tuning`, `SFT`, `DPO`, `PPO`, `GRPO`, `RLHF`, `Preference Alignment`, `HuggingFace` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при работе навыка.
:::

# TRL — Transformer Reinforcement Learning

## Быстрый старт

TRL предоставляет методы постобучения для согласования языковых моделей с человеческими предпочтениями.

**Установка**:
```bash
pip install trl transformers datasets peft accelerate
```

**Супервизированная тонкая настройка** (instruction tuning):
```python
from trl import SFTTrainer

trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B",
    train_dataset=dataset,  # Prompt-completion pairs
)
trainer.train()
```

**DPO** (согласование с предпочтениями):
```python
from trl import DPOTrainer, DPOConfig

config = DPOConfig(output_dir="model-dpo", beta=0.1)
trainer = DPOTrainer(
    model=model,
    args=config,
    train_dataset=preference_dataset,  # chosen/rejected pairs
    processing_class=tokenizer
)
trainer.train()
```

## Распространённые рабочие процессы

### Рабочий процесс 1: Полный конвейер RLHF (SFT → Reward Model → PPO)

Полный конвейер от базовой модели до модели, согласованной с человеком.

Скопируй этот чек‑лист:

```
RLHF Training:
- [ ] Step 1: Supervised fine-tuning (SFT)
- [ ] Step 2: Train reward model
- [ ] Step 3: PPO reinforcement learning
- [ ] Step 4: Evaluate aligned model
```

**Шаг 1: Супервизированная тонкая настройка**

Обучаем базовую модель на данных с инструкциями:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import SFTTrainer, SFTConfig
from datasets import load_dataset

# Load model
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B")

# Load instruction dataset
dataset = load_dataset("trl-lib/Capybara", split="train")

# Configure training
training_args = SFTConfig(
    output_dir="Qwen2.5-0.5B-SFT",
    per_device_train_batch_size=4,
    num_train_epochs=1,
    learning_rate=2e-5,
    logging_steps=10,
    save_strategy="epoch"
)

# Train
trainer = SFTTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer
)
trainer.train()
trainer.save_model()
```

**Шаг 2: Обучение модели наград**

Обучаем модель предсказывать человеческие предпочтения:

```python
from transformers import AutoModelForSequenceClassification
from trl import RewardTrainer, RewardConfig

# Load SFT model as base
model = AutoModelForSequenceClassification.from_pretrained(
    "Qwen2.5-0.5B-SFT",
    num_labels=1  # Single reward score
)
tokenizer = AutoTokenizer.from_pretrained("Qwen2.5-0.5B-SFT")

# Load preference data (chosen/rejected pairs)
dataset = load_dataset("trl-lib/ultrafeedback_binarized", split="train")

# Configure training
training_args = RewardConfig(
    output_dir="Qwen2.5-0.5B-Reward",
    per_device_train_batch_size=2,
    num_train_epochs=1,
    learning_rate=1e-5
)

# Train reward model
trainer = RewardTrainer(
    model=model,
    args=training_args,
    processing_class=tokenizer,
    train_dataset=dataset
)
trainer.train()
trainer.save_model()
```

**Шаг 3: Обучение с подкреплением PPO**

Оптимизируем политику с помощью модели наград:

```bash
python -m trl.scripts.ppo \
    --model_name_or_path Qwen2.5-0.5B-SFT \
    --reward_model_path Qwen2.5-0.5B-Reward \
    --dataset_name trl-internal-testing/descriptiveness-sentiment-trl-style \
    --output_dir Qwen2.5-0.5B-PPO \
    --learning_rate 3e-6 \
    --per_device_train_batch_size 64 \
    --total_episodes 10000
```

**Шаг 4: Оценка**

```python
from transformers import pipeline

# Load aligned model
generator = pipeline("text-generation", model="Qwen2.5-0.5B-PPO")

# Test
prompt = "Explain quantum computing to a 10-year-old"
output = generator(prompt, max_length=200)[0]["generated_text"]
print(output)
```

### Рабочий процесс 2: Простое согласование предпочтений с DPO

Согласуем модель с предпочтениями без модели наград.

Скопируй этот чек‑лист:

```
DPO Training:
- [ ] Step 1: Prepare preference dataset
- [ ] Step 2: Configure DPO
- [ ] Step 3: Train with DPOTrainer
- [ ] Step 4: Evaluate alignment
```

**Шаг 1: Подготовка набора данных предпочтений**

Формат набора данных:
```json
{
  "prompt": "What is the capital of France?",
  "chosen": "The capital of France is Paris.",
  "rejected": "I don't know."
}
```

Загрузка набора данных:
```python
from datasets import load_dataset

dataset = load_dataset("trl-lib/ultrafeedback_binarized", split="train")
# Or load your own
# dataset = load_dataset("json", data_files="preferences.json")
```

**Шаг 2: Конфигурация DPO**

```python
from trl import DPOConfig

config = DPOConfig(
    output_dir="Qwen2.5-0.5B-DPO",
    per_device_train_batch_size=4,
    num_train_epochs=1,
    learning_rate=5e-7,
    beta=0.1,  # KL penalty strength
    max_prompt_length=512,
    max_length=1024,
    logging_steps=10
)
```

**Шаг 3: Обучение с DPOTrainer**

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from trl import DPOTrainer

model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-0.5B-Instruct")

trainer = DPOTrainer(
    model=model,
    args=config,
    train_dataset=dataset,
    processing_class=tokenizer
)

trainer.train()
trainer.save_model()
```

**Альтернатива CLI**:
```bash
trl dpo \
    --model_name_or_path Qwen/Qwen2.5-0.5B-Instruct \
    --dataset_name argilla/Capybara-Preferences \
    --output_dir Qwen2.5-0.5B-DPO \
    --per_device_train_batch_size 4 \
    --learning_rate 5e-7 \
    --beta 0.1
```

### Рабочий процесс 3: Память‑эффективный онлайн‑RL с GRPO

Обучение с подкреплением с минимальным потреблением памяти.

Для подробного руководства по GRPO — проектирование функции награды, критические инсайты обучения (поведение потерь, коллапс режимов, настройка), а также продвинутые много‑этапные шаблоны — см. **[references/grpo-training.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/grpo-training.md)**. Готовый к использованию скрипт обучения находится в **[templates/basic_grpo_training.py](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/templates/basic_grpo_training.py)**.

Скопируй этот чек‑лист:

```
GRPO Training:
- [ ] Step 1: Define reward function
- [ ] Step 2: Configure GRPO
- [ ] Step 3: Train with GRPOTrainer
```

**Шаг 1: Определение функции награды**

```python
def reward_function(completions, **kwargs):
    """
    Compute rewards for completions.

    Args:
        completions: List of generated texts

    Returns:
        List of reward scores (floats)
    """
    rewards = []
    for completion in completions:
        # Example: reward based on length and unique words
        score = len(completion.split())  # Favor longer responses
        score += len(set(completion.lower().split()))  # Reward unique words
        rewards.append(score)
    return rewards
```

Или использовать модель наград:
```python
from transformers import pipeline

reward_model = pipeline("text-classification", model="reward-model-path")

def reward_from_model(completions, prompts, **kwargs):
    # Combine prompt + completion
    full_texts = [p + c for p, c in zip(prompts, completions)]
    # Get reward scores
    results = reward_model(full_texts)
    return [r["score"] for r in results]
```

**Шаг 2: Конфигурация GRPO**

```python
from trl import GRPOConfig

config = GRPOConfig(
    output_dir="Qwen2-GRPO",
    per_device_train_batch_size=4,
    num_train_epochs=1,
    learning_rate=1e-5,
    num_generations=4,  # Generate 4 completions per prompt
    max_new_tokens=128
)
```

**Шаг 3: Обучение с GRPOTrainer**

```python
from datasets import load_dataset
from trl import GRPOTrainer

# Load prompt-only dataset
dataset = load_dataset("trl-lib/tldr", split="train")

trainer = GRPOTrainer(
    model="Qwen/Qwen2-0.5B-Instruct",
    reward_funcs=reward_function,  # Your reward function
    args=config,
    train_dataset=dataset
)

trainer.train()
```

**CLI**:
```bash
trl grpo \
    --model_name_or_path Qwen/Qwen2-0.5B-Instruct \
    --dataset_name trl-lib/tldr \
    --output_dir Qwen2-GRPO \
    --num_generations 4
```

## Когда использовать vs альтернативы

**Используй TRL, когда:**
- Нужно согласовать модель с человеческими предпочтениями
- Есть данные предпочтений (пары выбранных/отклонённых вариантов)
- Требуется обучение с подкреплением (PPO, GRPO)
- Нужно обучать модель наград
- Выполняется RLHF (полный конвейер)

**Выбор метода**:
- **SFT**: Есть пары запрос‑ответ, нужен базовый инструктивный отклик
- **DPO**: Есть предпочтения, нужен простой способ согласования (без модели наград)
- **PPO**: Есть модель наград, нужен максимальный контроль над RL
- **GRPO**: Ограничена память, нужен онлайн‑RL
- **Reward Model**: Строим конвейер RLHF, нужно оценивать генерации

**Используй альтернативы вместо:**
- **HuggingFace Trainer**: Базовая тонкая настройка без RL
- **Axolotl**: Конфигурация обучения в YAML
- **LitGPT**: Образовательный, минимальный набор для тонкой настройки
- **Unsloth**: Быстрое обучение LoRA

## Распространённые проблемы

**Проблема: OOM во время обучения DPO**

Уменьши размер батча и длину последовательности:
```python
config = DPOConfig(
    per_device_train_batch_size=1,  # Reduce from 4
    max_length=512,  # Reduce from 1024
    gradient_accumulation_steps=8  # Maintain effective batch
)
```

Или включи градиентный чекпоинтинг:
```python
model.gradient_checkpointing_enable()
```

**Проблема: Плохое качество согласования**

Настрой параметр beta:
```python
# Higher beta = more conservative (stays closer to reference)
config = DPOConfig(beta=0.5)  # Default 0.1

# Lower beta = more aggressive alignment
config = DPOConfig(beta=0.01)
```

**Проблема: Модель наград не обучается**

Проверь тип функции потерь и скорость обучения:
```python
config = RewardConfig(
    learning_rate=1e-5,  # Try different LR
    num_train_epochs=3  # Train longer
)
```

Убедись, что в наборе данных предпочтений чётко определены победители:
```python
# Verify dataset
print(dataset[0])
# Should have clear chosen > rejected
```

**Проблема: Обучение PPO нестабильно**

Отрегулируй коэффициент KL:
```python
config = PPOConfig(
    kl_coef=0.1,  # Increase from 0.05
    cliprange=0.1  # Reduce from 0.2
)
```

## Продвинутые темы

**Руководство по обучению SFT**: См. [references/sft-training.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/sft-training.md) для форматов наборов данных, шаблонов чатов, стратегий упаковки и обучения на нескольких GPU.

**Варианты DPO**: См. [references/dpo-variants.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/dpo-variants.md) для IPO, cDPO, RPO и других функций потерь DPO с рекомендациями по гиперпараметрам.

**Моделирование наград**: См. [references/reward-modeling.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/reward-modeling.md) для наград за результат vs процесс, функции потерь Bradley‑Terry и оценки модели наград.

**Методы онлайн‑RL**: См. [references/online-rl.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/online-rl.md) для PPO, GRPO, RLOO и OnlineDPO с детальными конфигурациями.

**Глубокий разбор GRPO**: См. [references/grpo-training.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/grpo-training.md) для экспертных шаблонов GRPO — философия проектирования функции награды, инсайты обучения (почему растут потери, обнаружение коллапса режимов), настройка гиперпараметров, много‑этапное обучение и отладка. Готовый шаблон в [templates/basic_grpo_training.py](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/templates/basic_grpo_training.py).

## Требования к оборудованию

- **GPU**: NVIDIA (требуется CUDA)
- **VRAM**: Зависит от модели и метода
  - SFT 7B: 16 GB (с LoRA)
  - DPO 7B: 24 GB (хранит референсную модель)
  - PPO 7B: 40 GB (политика + модель наград)
  - GRPO 7B: 24 GB (более экономный по памяти)
- **Мульти‑GPU**: Поддерживается через `accelerate`
- **Смешанная точность**: Рекомендуется BF16 (A100/H100)

**Оптимизация памяти**:
- Используй LoRA/QLoRA для всех методов
- Включи градиентный чекпоинтинг
- Применяй меньшие размеры батчей с накоплением градиентов

## Ресурсы

- Docs: https://huggingface.co/docs/trl/
- GitHub: https://github.com/huggingface/trl
- Статьи:
  - "Training language models to follow instructions with human feedback" (InstructGPT, 2022)
  - "Direct Preference Optimization: Your Language Model is Secretly a Reward Model" (DPO, 2023)
  - "Group Relative Policy Optimization" (GRPO, 2024)
- Примеры: https://github.com/huggingface/trl/tree/main/examples/scripts