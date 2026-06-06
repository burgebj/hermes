---
title: "Peft Fine Tuning — параметрически‑эффективная донастройка LLM с использованием LoRA, QLoRA и более 25 методов"
sidebar_label: "Peft Fine Tuning"
description: "Параметрически-эффективная донастройка для LLMs с использованием LoRA, QLoRA и более 25 методов"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# PEFT — параметрически эффективная тонкая настройка

Параметрически эффективная тонкая настройка LLM с использованием LoRA, QLoRA и более 25 методов. Применяется при тонкой настройке больших моделей (7 B‑70 B) при ограниченной видеопамяти, когда нужно обучать < 1 % параметров с минимальной потерей точности, либо для обслуживания нескольких адаптеров. Официальная библиотека HuggingFace, интегрированная в экосистему transformers.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/peft` |
| Path | `optional-skills/mlops/peft` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `peft>=0.13.0`, `transformers>=4.45.0`, `torch>=2.0.0`, `bitsandbytes>=0.43.0` |
| Platforms | linux, macos, windows |
| Tags | `Fine-Tuning`, `PEFT`, `LoRA`, `QLoRA`, `Parameter-Efficient`, `Adapters`, `Low-Rank`, `Memory Optimization`, `Multi-Adapter` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда навык активен.
:::

# PEFT (Parameter-Efficient Fine-Tuning)

Тонкая настройка LLM путем обучения < 1 % параметров с помощью LoRA, QLoRA и более 25 методов адаптеров.

## Когда использовать PEFT

**Используй PEFT/LoRA, когда:**
- Тонкая настройка моделей 7 B‑70 B на потребительских GPU (RTX 4090, A100)
- Нужно обучать < 1 % параметров (адаптеры ≈ 6 МБ vs полная модель ≈ 14 ГБ)
- Требуется быстрая итерация с несколькими адаптерами под задачи
- Нужно развернуть несколько вариантов тонкой настройки из одной базовой модели

**Используй QLoRA (PEFT + квантование), когда:**
- Тонкая настройка моделей 70 B на одном GPU с 24 ГБ памяти
- Память является главным ограничением
- Приемлем компромисс ≈ 5 % качества по сравнению с полной настройкой

**Используй полную тонкую настройку вместо PEFT, когда:**
- Обучаешь небольшие модели (< 1 B параметров)
- Требуется максимальное качество и есть бюджет вычислительных ресурсов
- Значительный сдвиг домена требует обновления всех весов

## Быстрый старт

### Установка

```bash
# Basic installation
pip install peft

# With quantization support (recommended)
pip install peft bitsandbytes

# Full stack
pip install peft transformers accelerate bitsandbytes datasets
```

### LoRA‑тонкая настройка (стандартная)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, Trainer
from peft import get_peft_model, LoraConfig, TaskType
from datasets import load_dataset

# Load base model
model_name = "meta-llama/Llama-3.1-8B"
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

# LoRA configuration
lora_config = LoraConfig(
    task_type=TaskType.CAUSAL_LM,
    r=16,                          # Rank (8-64, higher = more capacity)
    lora_alpha=32,                 # Scaling factor (typically 2*r)
    lora_dropout=0.05,             # Dropout for regularization
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],  # Attention layers
    bias="none"                    # Don't train biases
)

# Apply LoRA
model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Output: trainable params: 13,631,488 || all params: 8,043,307,008 || trainable%: 0.17%

# Prepare dataset
dataset = load_dataset("databricks/databricks-dolly-15k", split="train")

def tokenize(example):
    text = f"### Instruction:\n{example['instruction']}\n\n### Response:\n{example['response']}"
    return tokenizer(text, truncation=True, max_length=512, padding="max_length")

tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)

# Training
training_args = TrainingArguments(
    output_dir="./lora-llama",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
    save_strategy="epoch"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized,
    data_collator=lambda data: {"input_ids": torch.stack([f["input_ids"] for f in data]),
                                 "attention_mask": torch.stack([f["attention_mask"] for f in data]),
                                 "labels": torch.stack([f["input_ids"] for f in data])}
)

trainer.train()

# Save adapter only (6MB vs 16GB)
model.save_pretrained("./lora-llama-adapter")
```

### QLoRA‑тонкая настройка (экономия памяти)

```python
from transformers import AutoModelForCausalLM, BitsAndBytesConfig
from peft import get_peft_model, LoraConfig, prepare_model_for_kbit_training

# 4-bit quantization config
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",           # NormalFloat4 (best for LLMs)
    bnb_4bit_compute_dtype="bfloat16",   # Compute in bf16
    bnb_4bit_use_double_quant=True       # Nested quantization
)

# Load quantized model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-70B",
    quantization_config=bnb_config,
    device_map="auto"
)

# Prepare for training (enables gradient checkpointing)
model = prepare_model_for_kbit_training(model)

# LoRA config for QLoRA
lora_config = LoraConfig(
    r=64,                              # Higher rank for 70B
    lora_alpha=128,
    lora_dropout=0.1,
    target_modules=["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    bias="none",
    task_type="CAUSAL_LM"
)

model = get_peft_model(model, lora_config)
# 70B model now fits on single 24GB GPU!
```

## Выбор параметров LoRA

### Rank (r) — ёмкость vs эффективность

| Rank | Обучаемые параметры | Память | Качество | Сценарий |
|------|----------------------|--------|----------|----------|
| 4 | ~3 M | Минимальная | Низкое | Простые задачи, прототипирование |
| **8** | ~7 M | Низкая | Хорошее | **Рекомендуемая отправная точка** |
| **16** | ~14 M | Средняя | Лучше | **Общая тонкая настройка** |
| 32 | ~27 M | Выше | Высокое | Сложные задачи |
| 64 | ~54 M | Высокая | Наивысшее | Адаптация домена, модели 70 B |

### Alpha (lora_alpha) — коэффициент масштабирования

```python
# Rule of thumb: alpha = 2 * rank
LoraConfig(r=16, lora_alpha=32)  # Standard
LoraConfig(r=16, lora_alpha=16)  # Conservative (lower learning rate effect)
LoraConfig(r=16, lora_alpha=64)  # Aggressive (higher learning rate effect)
```

### Целевые модули по архитектуре

```python
# Llama / Mistral / Qwen
target_modules = ["q_proj", "v_proj", "k_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

# GPT-2 / GPT-Neo
target_modules = ["c_attn", "c_proj", "c_fc"]

# Falcon
target_modules = ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"]

# BLOOM
target_modules = ["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"]

# Auto-detect all linear layers
target_modules = "all-linear"  # PEFT 0.6.0+
```

## Загрузка и объединение адаптеров

### Загрузка обученного адаптера

```python
from peft import PeftModel, AutoPeftModelForCausalLM
from transformers import AutoModelForCausalLM

# Option 1: Load with PeftModel
base_model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B")
model = PeftModel.from_pretrained(base_model, "./lora-llama-adapter")

# Option 2: Load directly (recommended)
model = AutoPeftModelForCausalLM.from_pretrained(
    "./lora-llama-adapter",
    device_map="auto"
)
```

### Объединение адаптера с базовой моделью

```python
# Merge for deployment (no adapter overhead)
merged_model = model.merge_and_unload()

# Save merged model
merged_model.save_pretrained("./llama-merged")
tokenizer.save_pretrained("./llama-merged")

# Push to Hub
merged_model.push_to_hub("username/llama-finetuned")
```

### Обслуживание мульти‑адаптеров

```python
from peft import PeftModel

# Load base with first adapter
model = AutoPeftModelForCausalLM.from_pretrained("./adapter-task1")

# Load additional adapters
model.load_adapter("./adapter-task2", adapter_name="task2")
model.load_adapter("./adapter-task3", adapter_name="task3")

# Switch between adapters at runtime
model.set_adapter("task1")  # Use task1 adapter
output1 = model.generate(**inputs)

model.set_adapter("task2")  # Switch to task2
output2 = model.generate(**inputs)

# Disable adapters (use base model)
with model.disable_adapter():
    base_output = model.generate(**inputs)
```

## Сравнение методов PEFT

| Метод | Обучаемый % | Память | Скорость | Оптимально для |
|--------|------------|--------|----------|----------------|
| **LoRA** | 0.1‑1 % | Низкая | Быстрая | Общая тонкая настройка |
| **QLoRA** | 0.1‑1 % | Очень низкая | Средняя | Ограничения памяти |
| AdaLoRA | 0.1‑1 % | Низкая | Средняя | Автоматический выбор ранга |
| IA3 | 0.01 % | Минимальная | Самая быстрая | Few‑shot адаптация |
| Prefix Tuning | 0.1 % | Низкая | Средняя | Управление генерацией |
| Prompt Tuning | 0.001 % | Минимальная | Быстрая | Простая адаптация задачи |
| P‑Tuning v2 | 0.1 % | Низкая | Средняя | NLU‑задачи |

### IA3 (минимальное количество параметров)

```python
from peft import IA3Config

ia3_config = IA3Config(
    target_modules=["q_proj", "v_proj", "k_proj", "down_proj"],
    feedforward_modules=["down_proj"]
)
model = get_peft_model(model, ia3_config)
# Trains only 0.01% of parameters!
```

### Prefix Tuning

```python
from peft import PrefixTuningConfig

prefix_config = PrefixTuningConfig(
    task_type="CAUSAL_LM",
    num_virtual_tokens=20,      # Prepended tokens
    prefix_projection=True       # Use MLP projection
)
model = get_peft_model(model, prefix_config)
```

## Паттерны интеграции

### С TRL (SFTTrainer)

```python
from trl import SFTTrainer, SFTConfig
from peft import LoraConfig

lora_config = LoraConfig(r=16, lora_alpha=32, target_modules="all-linear")

trainer = SFTTrainer(
    model=model,
    args=SFTConfig(output_dir="./output", max_seq_length=512),
    train_dataset=dataset,
    peft_config=lora_config,  # Pass LoRA config directly
)
trainer.train()
```

### С Axolotl (YAML‑конфиг)

```yaml
# axolotl config.yaml
adapter: lora
lora_r: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target_modules:
  - q_proj
  - v_proj
  - k_proj
  - o_proj
lora_target_linear: true  # Target all linear layers
```

### С vLLM (инференс)

```python
from vllm import LLM
from vllm.lora.request import LoRARequest

# Load base model with LoRA support
llm = LLM(model="meta-llama/Llama-3.1-8B", enable_lora=True)

# Serve with adapter
outputs = llm.generate(
    prompts,
    lora_request=LoRARequest("adapter1", 1, "./lora-adapter")
)
```

## Бенчмарки производительности

### Потребление памяти (Llama 3.1 8 B)

| Метод | Память GPU | Обучаемые параметры |
|--------|-----------|---------------------|
| Полная тонкая настройка | 60+ GB | 8 B (100 %) |
| LoRA r=16 | 18 GB | 14 M (0.17 %) |
| QLoRA r=16 | 6 GB | 14 M (0.17 %) |
| IA3 | 16 GB | 800 K (0.01 %) |

### Скорость обучения (A100 80 GB)

| Метод | Токенов/сек | По сравнению с полной тонкой настройкой |
|--------|-------------|-------------------------------------------|
| Полная тонкая настройка | 2 500 | 1× |
| LoRA | 3 200 | 1.3× |
| QLoRA | 2 100 | 0.84× |

### Качество (бенчмарк MMLU)

| Модель | Полная тонкая настройка | LoRA | QLoRA |
|-------|--------------------------|------|-------|
| Llama 2‑7 B | 45.3 | 44.8 | 44.1 |
| Llama 2‑13 B | 54.8 | 54.2 | 53.5 |

## Распространённые проблемы

### CUDA OOM во время обучения

```python
# Solution 1: Enable gradient checkpointing
model.gradient_checkpointing_enable()

# Solution 2: Reduce batch size + increase accumulation
TrainingArguments(
    per_device_train_batch_size=1,
    gradient_accumulation_steps=16
)

# Solution 3: Use QLoRA
from transformers import BitsAndBytesConfig
bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")
```

### Адаптер не применяется

```python
# Verify adapter is active
print(model.active_adapters)  # Should show adapter name

# Check trainable parameters
model.print_trainable_parameters()

# Ensure model in training mode
model.train()
```

### Падение качества

```python
# Increase rank
LoraConfig(r=32, lora_alpha=64)

# Target more modules
target_modules = "all-linear"

# Use more training data and epochs
TrainingArguments(num_train_epochs=5)

# Lower learning rate
TrainingArguments(learning_rate=1e-4)
```

## Лучшие практики

1. **Начинай с r=8‑16**, увеличивай при недостаточном качестве
2. **Используй alpha = 2 × rank** как стартовое значение
3. **Цели слои attention + MLP** для лучшего качества/эффективности
4. **Включи gradient checkpointing** для экономии памяти
5. **Часто сохраняй адаптеры** (маленькие файлы, лёгкий откат)
6. **Оценивай на отложенных данных** перед объединением
7. **Применяй QLoRA для моделей 70 B+** на потребительском железе

## Ссылки

- **[Advanced Usage](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/peft/references/advanced-usage.md)** — DoRA, LoftQ, стабилизация ранга, пользовательские модули
- **[Troubleshooting](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/peft/references/troubleshooting.md)** — Распространённые ошибки, отладка, оптимизация

## Ресурсы

- **GitHub**: https://github.com/huggingface/peft
- **Docs**: https://huggingface.co/docs/peft
- **LoRA Paper**: arXiv:2106.09685
- **QLoRA Paper**: arXiv:2305.14314
- **Models**: https://huggingface.co/models?library=peft