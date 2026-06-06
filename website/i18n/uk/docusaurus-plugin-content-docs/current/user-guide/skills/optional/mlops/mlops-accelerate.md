---
title: "Huggingface Accelerate — Найпростіший розподілений API навчання"
sidebar_label: "Huggingface Accelerate"
description: "Найпростіший розподілений API навчання"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Huggingface Accelerate

Найпростіший API розподіленого навчання. 4 рядки коду, щоб додати підтримку розподіленості до будь‑якого скрипту PyTorch. Уніфікований API для DeepSpeed/FSDP/Megatron/DDP. Автоматичне розміщення пристроїв, змішана точність (FP16/BF16/FP8). Інтерактивна конфігурація, одна команда запуску. Стандарт екосистеми HuggingFace.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/accelerate` |
| Path | `optional-skills/mlops/accelerate` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `accelerate`, `torch`, `transformers` |
| Platforms | linux, macos, windows |
| Tags | `Distributed Training`, `HuggingFace`, `Accelerate`, `DeepSpeed`, `FSDP`, `Mixed Precision`, `PyTorch`, `DDP`, `Unified API`, `Simple` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# HuggingFace Accelerate – Уніфіковане розподілене навчання

## Швидкий старт

Accelerate спрощує розподілене навчання до 4 рядків коду.

**Встановлення**:
```bash
pip install accelerate
```

**Конвертація скрипту PyTorch** (4 рядки):
```python
import torch
+ from accelerate import Accelerator

+ accelerator = Accelerator()

  model = torch.nn.Transformer()
  optimizer = torch.optim.Adam(model.parameters())
  dataloader = torch.utils.data.DataLoader(dataset)

+ model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)

  for batch in dataloader:
      optimizer.zero_grad()
      loss = model(batch)
-     loss.backward()
+     accelerator.backward(loss)
      optimizer.step()
```

**Запуск** (одна команда):
```bash
accelerate launch train.py
```

## Типові робочі процеси

### Робочий процес 1: Від одного GPU до багатьох GPU

**Оригінальний скрипт**:
```python
# train.py
import torch

model = torch.nn.Linear(10, 2).to('cuda')
optimizer = torch.optim.Adam(model.parameters())
dataloader = torch.utils.data.DataLoader(dataset, batch_size=32)

for epoch in range(10):
    for batch in dataloader:
        batch = batch.to('cuda')
        optimizer.zero_grad()
        loss = model(batch).mean()
        loss.backward()
        optimizer.step()
```

**З Accelerate** (додано 4 рядки):
```python
# train.py
import torch
from accelerate import Accelerator  # +1

accelerator = Accelerator()  # +2

model = torch.nn.Linear(10, 2)
optimizer = torch.optim.Adam(model.parameters())
dataloader = torch.utils.data.DataLoader(dataset, batch_size=32)

model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)  # +3

for epoch in range(10):
    for batch in dataloader:
        # No .to('cuda') needed - automatic!
        optimizer.zero_grad()
        loss = model(batch).mean()
        accelerator.backward(loss)  # +4
        optimizer.step()
```

**Конфігурація** (інтерактивна):
```bash
accelerate config
```

**Питання**:
- Яка машина? (single/multi GPU/TPU/CPU)
- Скільки машин? (1)
- Змішана точність? (no/fp16/bf16/fp8)
- DeepSpeed? (no/yes)

**Запуск** (працює на будь‑якій конфігурації):
```bash
# Single GPU
accelerate launch train.py

# Multi-GPU (8 GPUs)
accelerate launch --multi_gpu --num_processes 8 train.py

# Multi-node
accelerate launch --multi_gpu --num_processes 16 \
  --num_machines 2 --machine_rank 0 \
  --main_process_ip $MASTER_ADDR \
  train.py
```

### Робочий процес 2: Навчання зі змішаною точністю

**Увімкнути FP16/BF16**:
```python
from accelerate import Accelerator

# FP16 (with gradient scaling)
accelerator = Accelerator(mixed_precision='fp16')

# BF16 (no scaling, more stable)
accelerator = Accelerator(mixed_precision='bf16')

# FP8 (H100+)
accelerator = Accelerator(mixed_precision='fp8')

model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)

# Everything else is automatic!
for batch in dataloader:
    with accelerator.autocast():  # Optional, done automatically
        loss = model(batch)
    accelerator.backward(loss)
```

### Робочий процес 3: Інтеграція DeepSpeed ZeRO

**Увімкнути DeepSpeed ZeRO‑2**:
```python
from accelerate import Accelerator

accelerator = Accelerator(
    mixed_precision='bf16',
    deepspeed_plugin={
        "zero_stage": 2,  # ZeRO-2
        "offload_optimizer": False,
        "gradient_accumulation_steps": 4
    }
)

# Same code as before!
model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)
```

**Або через конфіг**:
```bash
accelerate config
# Select: DeepSpeed → ZeRO-2
```

**deepspeed_config.json**:
```json
{
    "fp16": {"enabled": false},
    "bf16": {"enabled": true},
    "zero_optimization": {
        "stage": 2,
        "offload_optimizer": {"device": "cpu"},
        "allgather_bucket_size": 5e8,
        "reduce_bucket_size": 5e8
    }
}
```

**Запуск**:
```bash
accelerate launch --config_file deepspeed_config.json train.py
```

### Робочий процес 4: FSDP (Fully Sharded Data Parallel)

**Увімкнути FSDP**:
```python
from accelerate import Accelerator, FullyShardedDataParallelPlugin

fsdp_plugin = FullyShardedDataParallelPlugin(
    sharding_strategy="FULL_SHARD",  # ZeRO-3 equivalent
    auto_wrap_policy="TRANSFORMER_AUTO_WRAP",
    cpu_offload=False
)

accelerator = Accelerator(
    mixed_precision='bf16',
    fsdp_plugin=fsdp_plugin
)

model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)
```

**Або через конфіг**:
```bash
accelerate config
# Select: FSDP → Full Shard → No CPU Offload
```

### Робочий процес 5: Накопичення градієнтів

**Накопичувати градієнти**:
```python
from accelerate import Accelerator

accelerator = Accelerator(gradient_accumulation_steps=4)

model, optimizer, dataloader = accelerator.prepare(model, optimizer, dataloader)

for batch in dataloader:
    with accelerator.accumulate(model):  # Handles accumulation
        optimizer.zero_grad()
        loss = model(batch)
        accelerator.backward(loss)
        optimizer.step()
```

**Ефективний розмір пакету**: `batch_size * num_gpus * gradient_accumulation_steps`

## Коли використовувати vs альтернативи

**Використовуй Accelerate, коли**:
- Потрібне найпростіше розподілене навчання
- Потрібен один скрипт для будь‑якого обладнання
- Використовуєш екосистему HuggingFace
- Потрібна гнучкість (DDP/DeepSpeed/FSDP/Megatron)
- Потрібне швидке прототипування

**Ключові переваги**:
- **4 рядки**: мінімальні зміни коду
- **Уніфікований API**: один і той самий код для DDP, DeepSpeed, FSDP, Megatron
- **Автоматично**: розміщення пристроїв, змішана точність, шардинг
- **Інтерактивна конфіг**: без ручного налаштування лаунчера
- **Один запуск**: працює скрізь

**Використовуй альтернативи, коли**:
- **PyTorch Lightning**: потрібні колбеки, високорівневі абстракції
- **Ray Train**: оркестрація багатьох вузлів, налаштування гіперпараметрів
- **DeepSpeed**: прямий контроль API, розширені можливості
- **Raw DDP**: максимальний контроль, мінімальна абстракція

## Типові проблеми

**Проблема: Неправильне розміщення пристрою**

Не переміщуй вручну на пристрій:
```python
# WRONG
batch = batch.to('cuda')

# CORRECT
# Accelerate handles it automatically after prepare()
```

**Проблема: Накопичення градієнтів не працює**

Використай контекстний менеджер:
```python
# CORRECT
with accelerator.accumulate(model):
    optimizer.zero_grad()
    accelerator.backward(loss)
    optimizer.step()
```

**Проблема: Контрольна точка в розподіленому режимі**

Використай методи accelerator:
```python
# Save only on main process
if accelerator.is_main_process:
    accelerator.save_state('checkpoint/')

# Load on all processes
accelerator.load_state('checkpoint/')
```

**Проблема: Різні результати з FSDP**

Переконайся, що використано один і той самий випадковий seed:
```python
from accelerate.utils import set_seed
set_seed(42)
```

## Розширені теми

**Інтеграція Megatron**: Дивись [references/megatron-integration.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/accelerate/references/megatron-integration.md) для налаштувань тензорного, конвеєрного та послідовного паралелізму.

**Кастомні плагіни**: Дивись [references/custom-plugins.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/accelerate/references/custom-plugins.md) для створення власних розподілених плагінів та розширеної конфігурації.

**Тюнінг продуктивності**: Дивись [references/performance.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/accelerate/references/performance.md) для профілювання, оптимізації пам'яті та кращих практик.

## Аппаратні вимоги

- **CPU**: Працює (повільно)
- **Один GPU**: Працює
- **Багато GPU**: DDP (за замовчуванням), DeepSpeed або FSDP
- **Багато вузлів**: DDP, DeepSpeed, FSDP, Megatron
- **TPU**: Підтримується
- **Apple MPS**: Підтримується

**Вимоги до лаунчера**:
- **DDP**: `torch.distributed.run` (вбудовано)
- **DeepSpeed**: `deepspeed` (pip install deepspeed)
- **FSDP**: PyTorch 1.12+ (вбудовано)
- **Megatron**: кастомне налаштування

## Ресурси

- Docs: https://huggingface.co/docs/accelerate
- GitHub: https://github.com/huggingface/accelerate
- Version: 1.11.0+
- Tutorial: "Accelerate your scripts"
- Examples: https://github.com/huggingface/accelerate/tree/main/examples
- Used by: HuggingFace Transformers, TRL, PEFT, all HF libraries