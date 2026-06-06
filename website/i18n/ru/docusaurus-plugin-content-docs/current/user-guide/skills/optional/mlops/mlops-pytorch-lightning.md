---
title: "Pytorch Lightning"
sidebar_label: "Pytorch Lightning"
description: "Высокоуровневый фреймворк PyTorch с классом Trainer, автоматическим распределённым обучением (DDP/FSDP/DeepSpeed), системой callbacks и минимальным шаблонным кодом"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Pytorch Lightning

Высокоуровневый фреймворк PyTorch с классом **Trainer**, автоматическим распределённым обучением (DDP/FSDP/DeepSpeed), системой **callbacks** и минимальным boilerplate. Масштабируется от ноутбука до суперкомпьютера без изменения кода. Используй, когда нужен чистый цикл обучения с встроенными лучшими практиками.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/pytorch-lightning` |
| Path | `optional-skills/mlops/pytorch-lightning` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `lightning`, `torch`, `transformers` |
| Platforms | linux, macos, windows |
| Tags | `PyTorch Lightning`, `Training Framework`, `Distributed Training`, `DDP`, `FSDP`, `DeepSpeed`, `High-Level API`, `Callbacks`, `Best Practices`, `Scalable` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# PyTorch Lightning — высокоуровневый фреймворк для обучения

## Quick start

PyTorch Lightning упорядочивает код PyTorch, устраняя boilerplate при сохранении гибкости.

**Installation**:
```bash
pip install lightning
```

**Convert PyTorch to Lightning** (3 шага):
```python
import lightning as L
import torch
from torch import nn
from torch.utils.data import DataLoader, Dataset

# Step 1: Define LightningModule (organize your PyTorch code)
class LitModel(L.LightningModule):
    def __init__(self, hidden_size=128):
        super().__init__()
        self.model = nn.Sequential(
            nn.Linear(28 * 28, hidden_size),
            nn.ReLU(),
            nn.Linear(hidden_size, 10)
        )

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.model(x)
        loss = nn.functional.cross_entropy(y_hat, y)
        self.log('train_loss', loss)  # Auto-logged to TensorBoard
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3)

# Step 2: Create data
train_loader = DataLoader(train_dataset, batch_size=32)

# Step 3: Train with Trainer (handles everything else!)
trainer = L.Trainer(max_epochs=10, accelerator='gpu', devices=2)
model = LitModel()
trainer.fit(model, train_loader)
```

**Вот и всё!** Trainer управляет:
- переключением между GPU/TPU/CPU
- распределённым обучением (DDP, FSDP, DeepSpeed)
- смешанной точностью (FP16, BF16)
- аккумуляцией градиентов
- контрольными точками
- логированием
- индикаторами прогресса

## Common workflows

### Workflow 1: From PyTorch to Lightning

**Исходный код PyTorch**:
```python
model = MyModel()
optimizer = torch.optim.Adam(model.parameters())
model.to('cuda')

for epoch in range(max_epochs):
    for batch in train_loader:
        batch = batch.to('cuda')
        optimizer.zero_grad()
        loss = model(batch)
        loss.backward()
        optimizer.step()
```

**Версия на Lightning**:
```python
class LitModel(L.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = MyModel()

    def training_step(self, batch, batch_idx):
        loss = self.model(batch)  # No .to('cuda') needed!
        return loss

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters())

# Train
trainer = L.Trainer(max_epochs=10, accelerator='gpu')
trainer.fit(LitModel(), train_loader)
```

**Плюсы**: 40+ строк → 15 строк, без управления устройствами, автоматическое распределение

### Workflow 2: Validation and testing

```python
class LitModel(L.LightningModule):
    def __init__(self):
        super().__init__()
        self.model = MyModel()

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.model(x)
        loss = nn.functional.cross_entropy(y_hat, y)
        self.log('train_loss', loss)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.model(x)
        val_loss = nn.functional.cross_entropy(y_hat, y)
        acc = (y_hat.argmax(dim=1) == y).float().mean()
        self.log('val_loss', val_loss)
        self.log('val_acc', acc)

    def test_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.model(x)
        test_loss = nn.functional.cross_entropy(y_hat, y)
        self.log('test_loss', test_loss)

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3)

# Train with validation
trainer = L.Trainer(max_epochs=10)
trainer.fit(model, train_loader, val_loader)

# Test
trainer.test(model, test_loader)
```

**Автоматические возможности**:
- валидация запускается каждый эпох по умолчанию
- метрики записываются в TensorBoard
- контрольная точка лучшей модели сохраняется по `val_loss`

### Workflow 3: Distributed training (DDP)

```python
# Same code as single GPU!
model = LitModel()

# 8 GPUs with DDP (automatic!)
trainer = L.Trainer(
    accelerator='gpu',
    devices=8,
    strategy='ddp'  # Or 'fsdp', 'deepspeed'
)

trainer.fit(model, train_loader)
```

**Запуск**:
```bash
# Single command, Lightning handles the rest
python train.py
```

**Никаких изменений не требуется**:
- автоматическое распределение данных
- синхронизация градиентов
- поддержка нескольких узлов (достаточно задать `num_nodes=2`)

### Workflow 4: Callbacks for monitoring

```python
from lightning.pytorch.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor

# Create callbacks
checkpoint = ModelCheckpoint(
    monitor='val_loss',
    mode='min',
    save_top_k=3,
    filename='model-{epoch:02d}-{val_loss:.2f}'
)

early_stop = EarlyStopping(
    monitor='val_loss',
    patience=5,
    mode='min'
)

lr_monitor = LearningRateMonitor(logging_interval='epoch')

# Add to Trainer
trainer = L.Trainer(
    max_epochs=100,
    callbacks=[checkpoint, early_stop, lr_monitor]
)

trainer.fit(model, train_loader, val_loader)
```

**Результат**:
- автоматическое сохранение лучших 3 моделей
- ранняя остановка, если улучшения нет более 5 эпох
- запись скорости обучения в TensorBoard

### Workflow 5: Learning rate scheduling

```python
class LitModel(L.LightningModule):
    # ... (training_step, etc.)

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)

        # Cosine annealing
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer,
            T_max=100,
            eta_min=1e-5
        )

        return {
            'optimizer': optimizer,
            'lr_scheduler': {
                'scheduler': scheduler,
                'interval': 'epoch',  # Update per epoch
                'frequency': 1
            }
        }

# Learning rate auto-logged!
trainer = L.Trainer(max_epochs=100)
trainer.fit(model, train_loader)
```

## When to use vs alternatives

**Используй PyTorch Lightning, когда**:
- нужен чистый, структурированный код
- требуются готовые к продакшену циклы обучения
- требуется переключение между одиночным GPU, несколькими GPU, TPU
- нужны встроенные callbacks и логирование
- важна командная работа (единый стандарт структуры)

**Ключевые преимущества**:
- **Организованность**: отделяет исследовательский код от инженерного
- **Автоматизация**: DDP, FSDP, DeepSpeed — одной строкой
- **Callbacks**: модульные расширения обучения
- **Воспроизводимость**: меньше boilerplate → меньше багов
- **Проверено**: более 1 М скачиваний в месяц, battle‑tested

**Альтернативы**:
- **Accelerate**: минимальные изменения в существующем коде, больше гибкости
- **Ray Train**: оркестрация на нескольких узлах, гиперпараметрический поиск
- **Raw PyTorch**: максимальный контроль, обучение основам
- **Keras**: экосистема TensorFlow

## Common issues

**Issue: Loss not decreasing**

Проверь данные и конфигурацию модели:
```python
# Add to training_step
def training_step(self, batch, batch_idx):
    if batch_idx == 0:
        print(f"Batch shape: {batch[0].shape}")
        print(f"Labels: {batch[1]}")
    loss = ...
    return loss
```

**Issue: Out of memory**

Уменьши размер батча или включи аккумуляцию градиентов:
```python
trainer = L.Trainer(
    accumulate_grad_batches=4,  # Effective batch = batch_size × 4
    precision='bf16'  # Or 'fp16', reduces memory 50%
)
```

**Issue: Validation not running**

Убедись, что передаёшь `val_loader`:
```python
# WRONG
trainer.fit(model, train_loader)

# CORRECT
trainer.fit(model, train_loader, val_loader)
```

**Issue: DDP spawns multiple processes unexpectedly**

Lightning автоматически определяет GPU. Явно укажи устройства:
```python
# Test on CPU first
trainer = L.Trainer(accelerator='cpu', devices=1)

# Then GPU
trainer = L.Trainer(accelerator='gpu', devices=1)
```

## Advanced topics

**Callbacks**: см. [references/callbacks.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/pytorch-lightning/references/callbacks.md) — EarlyStopping, ModelCheckpoint, пользовательские callbacks и хуки.

**Distributed strategies**: см. [references/distributed.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/pytorch-lightning/references/distributed.md) — DDP, FSDP, интеграция DeepSpeed ZeRO, настройка мульти‑узлов.

**Hyperparameter tuning**: см. [references/hyperparameter-tuning.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/pytorch-lightning/references/hyperparameter-tuning.md) — интеграция с Optuna, Ray Tune и WandB sweeps.

## Hardware requirements

- **CPU**: работает (удобно для отладки)
- **Single GPU**: работает
- **Multi‑GPU**: DDP (по умолчанию), FSDP или DeepSpeed
- **Multi‑node**: DDP, FSDP, DeepSpeed
- **TPU**: поддерживается (8 ядер)
- **Apple MPS**: поддерживается

**Опции точности**:
- FP32 (по умолчанию)
- FP16 (V100, более старые GPU)
- BF16 (A100/H100, рекомендуется)
- FP8 (H100)

## Resources

- Docs: https://lightning.ai/docs/pytorch/stable/
- GitHub: https://github.com/Lightning-AI/pytorch-lightning ⭐ 29 000+
- Version: 2.5.5+
- Examples: https://github.com/Lightning-AI/pytorch-lightning/tree/master/examples
- Discord: https://discord.gg/lightning-ai
- Used by: победители Kaggle, исследовательские лаборатории, продакшен‑команды