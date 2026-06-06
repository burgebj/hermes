---
title: "Тонке налаштування за допомогою Trl — TRL: SFT, DPO, PPO, GRPO, моделювання винагороди для LLM RLHF"
sidebar_label: "Fine Tuning With Trl"
description: "TRL: SFT, DPO, PPO, GRPO, моделювання винагороди для LLM RLHF"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Тонке налаштування за допомогою TRL

TRL: SFT, DPO, PPO, GRPO, reward modeling for LLM RLHF.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# TRL — Transformer Reinforcement Learning

## Швидкий старт

TRL надає методи післятренування для вирівнювання мовних моделей з людськими уподобаннями.

**Встановлення**:
```bash
pip install trl transformers datasets peft accelerate
```

**Супервізоване тонке налаштування** (instruction tuning):
```python
from trl import SFTTrainer

trainer = SFTTrainer(
    model="Qwen/Qwen2.5-0.5B",
    train_dataset=dataset,  # Prompt-completion pairs
)
trainer.train()
```

**DPO** (align with preferences):
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

## Типові робочі процеси

### Робочий процес 1: Повний конвеєр RLHF (SFT → модель винагороди → PPO)

Повний конвеєр від базової моделі до моделі, вирівняної з людьми.

Скопіюй цей чек‑лист:

```
RLHF Training:
- [ ] Step 1: Supervised fine-tuning (SFT)
- [ ] Step 2: Train reward model
- [ ] Step 3: PPO reinforcement learning
- [ ] Step 4: Evaluate aligned model
```

**Крок 1: Супервізоване тонке налаштування**

Тренуй базову модель на даних інструкцій:

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

**Крок 2: Тренування моделі винагороди**

Навчи модель передбачати людські уподобання:

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

**Крок 3: PPO reinforcement learning**

Оптимізуй політику за допомогою моделі винагороди:

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

**Крок 4: Оцінка**

```python
from transformers import pipeline

# Load aligned model
generator = pipeline("text-generation", model="Qwen2.5-0.5B-PPO")

# Test
prompt = "Explain quantum computing to a 10-year-old"
output = generator(prompt, max_length=200)[0]["generated_text"]
print(output)
```

### Робочий процес 2: Просте вирівнювання уподобань за допомогою DPO

Вирівняй модель з уподобаннями без моделі винагороди.

Скопіюй цей чек‑лист:

```
DPO Training:
- [ ] Step 1: Prepare preference dataset
- [ ] Step 2: Configure DPO
- [ ] Step 3: Train with DPOTrainer
- [ ] Step 4: Evaluate alignment
```

**Крок 1: Підготувати датасет уподобань**

Формат датасету:
```json
{
  "prompt": "What is the capital of France?",
  "chosen": "The capital of France is Paris.",
  "rejected": "I don't know."
}
```

Завантажити датасет:
```python
from datasets import load_dataset

dataset = load_dataset("trl-lib/ultrafeedback_binarized", split="train")
# Or load your own
# dataset = load_dataset("json", data_files="preferences.json")
```

**Крок 2: Налаштувати DPO**

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

**Крок 3: Тренування з DPOTrainer**

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

### Робочий процес 3: Ефективний за пам’яттю онлайн‑RL з GRPO

Тренуй з підкріплювальним навчанням, використовуючи мінімальну пам’ять.

Для докладного керівництва по GRPO — дизайн функції винагороди, критичні інсайти під час тренування (поведінка втрат, колапс режиму, налаштування) та розширені багатоступеневі патерни — дивись **[references/grpo-training.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/grpo-training.md)**. Готовий до продакшну скрипт тренування знаходиться у **[templates/basic_grpo_training.py](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/templates/basic_grpo_training.py)**.

Скопіюй цей чек‑лист:

```
GRPO Training:
- [ ] Step 1: Define reward function
- [ ] Step 2: Configure GRPO
- [ ] Step 3: Train with GRPOTrainer
```

**Крок 1: Визначити функцію винагороди**

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

Або використати модель винагороди:
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

**Крок 2: Налаштувати GRPO**

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

**Крок 3: Тренування з GRPOTrainer**

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

## Коли використовувати vs альтернативи

**Використовуй TRL, коли:**
- Потрібно вирівняти модель з людськими уподобаннями
- Є дані уподобань (пари обраних/відхилених)
- Хочеш застосовувати підкріплювальне навчання (PPO, GRPO)
- Потрібно тренувати модель винагороди
- Проводиш RLHF (повний конвеєр)

**Вибір методу**:
- **SFT**: Є пари prompt‑completion, потрібне базове слідування інструкціям
- **DPO**: Є уподобання, потрібне просте вирівнювання (модель винагороди не потрібна)
- **PPO**: Є модель винагороди, потрібен максимальний контроль над RL
- **GRPO**: Обмежена пам’ять, потрібне онлайн‑RL
- **Модель винагороди**: Будуєш конвеєр RLHF, треба оцінювати генерації

**Використовуй альтернативи замість:**
- **HuggingFace Trainer**: Базове тонке налаштування без RL
- **Axolotl**: YAML‑базована конфігурація тренування
- **LitGPT**: Навчальний, мінімальне тонке налаштування
- **Unsloth**: Швидке LoRA‑тренування

## Типові проблеми

**Проблема: OOM під час DPO‑тренування**

Зменш розмір batch та довжину послідовності:
```python
config = DPOConfig(
    per_device_train_batch_size=1,  # Reduce from 4
    max_length=512,  # Reduce from 1024
    gradient_accumulation_steps=8  # Maintain effective batch
)
```

Або використай gradient checkpointing:
```python
model.gradient_checkpointing_enable()
```

**Проблема: Погана якість вирівнювання**

Налаштуй параметр beta:
```python
# Higher beta = more conservative (stays closer to reference)
config = DPOConfig(beta=0.5)  # Default 0.1

# Lower beta = more aggressive alignment
config = DPOConfig(beta=0.01)
```

**Проблема: Модель винагороди не навчається**

Перевір тип втрати та швидкість навчання:
```python
config = RewardConfig(
    learning_rate=1e-5,  # Try different LR
    num_train_epochs=3  # Train longer
)
```

Переконайся, що у датасеті уподобань чітко визначені переможці:
```python
# Verify dataset
print(dataset[0])
# Should have clear chosen > rejected
```

**Проблема: PPO‑тренування нестабільне**

Відкоригуй KL‑коефіцієнт:
```python
config = PPOConfig(
    kl_coef=0.1,  # Increase from 0.05
    cliprange=0.1  # Reduce from 0.2
)
```

## Розширені теми

**Посібник з SFT‑тренування**: Дивись [references/sft-training.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/sft-training.md) для форматів датасетів, шаблонів чатів, стратегій пакування та мульти‑GPU тренування.

**Варіанти DPO**: Дивись [references/dpo-variants.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/dpo-variants.md) для IPO, cDPO, RPO та інших функцій втрат DPO з рекомендованими гіперпараметрами.

**Reward modeling**: Дивись [references/reward-modeling.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/reward-modeling.md) для винагород за результат vs процес, Bradley‑Terry loss та оцінки моделі винагороди.

**Методи онлайн‑RL**: Дивись [references/online-rl.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/online-rl.md) для PPO, GRPO, RLOO та OnlineDPO з детальними конфігураціями.

**Глибоке занурення в GRPO**: Дивись [references/grpo-training.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/references/grpo-training.md) для експертних патернів GRPO — філософія дизайну функції винагороди, інсайти під час тренування (чому втрати зростають, виявлення колапсу режиму), налаштування гіперпараметрів, багатоступеневе тренування та усунення проблем. Готовий шаблон у [templates/basic_grpo_training.py](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/training/trl-fine-tuning/templates/basic_grpo_training.py).

## Апаратурні вимоги

- **GPU**: NVIDIA (потрібен CUDA)
- **VRAM**: Залежить від моделі та методу
  - SFT 7B: 16 GB (з LoRA)
  - DPO 7B: 24 GB (зберігає reference model)
  - PPO 7B: 40 GB (policy + модель винагороди)
  - GRPO 7B: 24 GB (ефективніше за пам’яттю)
- **Multi‑GPU**: Підтримується через `accelerate`
- **Mixed precision**: Рекомендовано BF16 (A100/H100)

**Оптимізація пам’яті**:
- Використовуй LoRA/QLoRA для всіх методів
- Увімкни gradient checkpointing
- Використовуй менші batch size з gradient accumulation

## Ресурси

- Docs: https://huggingface.co/docs/trl/
- GitHub: https://github.com/huggingface/trl
- Papers:
  - "Training language models to follow instructions with human feedback" (InstructGPT, 2022)
  - "Direct Preference Optimization: Your Language Model is Secretly a Reward Model" (DPO, 2023)
  - "Group Relative Policy Optimization" (GRPO, 2024)
- Examples: https://github.com/huggingface/trl/tree/main/examples/scripts