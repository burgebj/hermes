---
title: "Huggingface Accelerate — Самый простой API распределённого обучения"
sidebar_label: "Huggingface Accelerate"
description: "Самый простой распределённый API обучения"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Huggingface Accelerate

Самый простой API распределённого обучения. 4 строки, чтобы добавить поддержку распределённого режима в любой скрипт PyTorch. Унифицированный API для DeepSpeed/FSDP/Megatron/DDP. Автоматическое размещение устройств, смешанная точность (FP16/BF16/FP8). Интерактивная конфигурация, одна команда запуска. Стандарт экосистемы HuggingFace.

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# HuggingFace Accelerate — Унифицированное распределённое обучение

## Быстрый старт

Accelerate упрощает распределённое обучение до 4 строк кода.

**Установка**:
```bash
pip install accelerate
```

**Преобразование скрипта PyTorch** (4 строки):
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

## Распространённые рабочие процессы

### Рабочий процесс 1: От одного GPU к нескольким GPU

**Исходный скрипт**:
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

**С Accelerate** (добавлено 4 строки):
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

**Конфигурация** (интерактивная):
```bash
accelerate config
```

**Вопросы**:
- Какой тип машины? (single/multi GPU/TPU/CPU)
- Сколько машин? (1)
- Смешанная точность? (no/fp16/bf16/fp8)
- DeepSpeed? (no/yes)

**Запуск** (работает в любой конфигурации):
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

### Рабочий процесс 2: Обучение со смешанной точностью

**Включить FP16/BF16**:
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

### Рабочий процесс 3: Интеграция DeepSpeed ZeRO

**Включить DeepSpeed ZeRO‑2**:
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

**Или через конфиг**:
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

### Рабочий процесс 4: FSDP (Fully Sharded Data Parallel)

**Включить FSDP**:
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

**Или через конфиг**:
```bash
accelerate config
# Select: FSDP → Full Shard → No CPU Offload
```

### Рабочий процесс 5: Накопление градиентов

**Накопление градиентов**:
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

**Эффективный размер пакета**: `batch_size * num_gpus * gradient_accumulation_steps`

## Когда использовать vs альтернативы

**Используй Accelerate, когда**:
- Нужно самое простое распределённое обучение
- Требуется один скрипт для любого оборудования
- Используется экосистема HuggingFace
- Нужна гибкость (DDP/DeepSpeed/FSDP/Megatron)
- Требуется быстрое прототипирование

**Ключевые преимущества**:
- **4 строки**: минимальные изменения кода
- **Унифицированный API**: один и тот же код для DDP, DeepSpeed, FSDP, Megatron
- **Автоматически**: размещение устройств, смешанная точность, шардинг
- **Интерактивная конфигурация**: без ручной настройки лаунчера
- **Один запуск**: работает везде

**Используй альтернативы вместо**:
- **PyTorch Lightning**: нужны callbacks, высокоуровневые абстракции
- **Ray Train**: оркестрация нескольких узлов, настройка гиперпараметров
- **DeepSpeed**: прямой контроль API, продвинутые возможности
- **Raw DDP**: максимальный контроль, минимум абстракций

## Распространённые проблемы

**Проблема: Неправильное размещение устройства**

Не перемещай вручную на устройство:
```python
# WRONG
batch = batch.to('cuda')

# CORRECT
# Accelerate handles it automatically after prepare()
```

**Проблема: Накопление градиентов не работает**

Используй менеджер контекста:
```python
# CORRECT
with accelerator.accumulate(model):
    optimizer.zero_grad()
    accelerator.backward(loss)
    optimizer.step()
```

**Проблема: Контрольные точки в распределённом режиме**

Используй методы accelerator:
```python
# Save only on main process
if accelerator.is_main_process:
    accelerator.save_state('checkpoint/')

# Load on all processes
accelerator.load_state('checkpoint/')
```

**Проблема: Разные результаты с FSDP**

Убедись, что установлен одинаковый seed:
```python
from accelerate.utils import set_seed
set_seed(42)
```

## Продвинутые темы

**Интеграция Megatron**: см. [references/megatron-integration.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/accelerate/references/megatron-integration.md) для настройки тензорного, конвейерного и последовательного параллелизма.

**Пользовательские плагины**: см. [references/custom-plugins.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/accelerate/references/custom-plugins.md) для создания пользовательских распределённых плагинов и продвинутой конфигурации.

**Тонкая настройка производительности**: см. [references/performance.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/accelerate/references/performance.md) для профилирования, оптимизации памяти и лучших практик.

## Требования к оборудованию

- **CPU**: работает (медленно)
- **Один GPU**: работает
- **Множественные GPU**: DDP (по умолчанию), DeepSpeed или FSDP
- **Множественные узлы**: DDP, DeepSpeed, FSDP, Megatron
- **TPU**: поддерживается
- **Apple MPS**: поддерживается

**Требования к лаунчеру**:
- **DDP**: `torch.distributed.run` (встроенный)
- **DeepSpeed**: `deepspeed` (pip install deepspeed)
- **FSDP**: PyTorch 1.12+ (встроенный)
- **Megatron**: пользовательская настройка

## Ресурсы

- Docs: https://huggingface.co/docs/accelerate
- GitHub: https://github.com/huggingface/accelerate
- Version: 1.11.0+
- Tutorial: "Accelerate your scripts"
- Examples: https://github.com/huggingface/accelerate/tree/main/examples
- Used by: HuggingFace Transformers, TRL, PEFT, all HF libraries