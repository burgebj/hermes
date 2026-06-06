---
title: "Simpo Training — простая оптимизация предпочтений для согласования LLM"
sidebar_label: "Simpo Training"
description: "Простая оптимизация предпочтений для выравнивания LLM"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# SimPO Training

Simple Preference Optimization for LLM alignment. Reference‑free alternative to DPO with better performance (+6.4 points on AlpacaEval 2.0). No reference model needed, more efficient than DPO. Use for preference alignment when want simpler, faster training than DPO/PPO.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/simpo` |
| Path | `optional-skills/mlops/simpo` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `torch`, `transformers`, `datasets`, `trl`, `accelerate` |
| Platforms | linux, macos, windows |
| Tags | `Post-Training`, `SimPO`, `Preference Optimization`, `Alignment`, `DPO Alternative`, `Reference-Free`, `LLM Alignment`, `Efficient Training` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# SimPO — Simple Preference Optimization

## Quick start

SimPO — это метод оптимизации предпочтений без использования референс‑модели, который превосходит DPO.

**Installation**:
```bash
# Create environment
conda create -n simpo python=3.10 && conda activate simpo

# Install PyTorch 2.2.2
# Visit: https://pytorch.org/get-started/locally/

# Install alignment-handbook
git clone https://github.com/huggingface/alignment-handbook.git
cd alignment-handbook
python -m pip install .

# Install Flash Attention 2
python -m pip install flash-attn --no-build-isolation
```

**Training** (Mistral 7B):
```bash
ACCELERATE_LOG_LEVEL=info accelerate launch \
  --config_file accelerate_configs/deepspeed_zero3.yaml \
  scripts/run_simpo.py \
  training_configs/mistral-7b-base-simpo.yaml
```

## Common workflows

### Workflow 1: Train from base model (Mistral 7B)

**Config** (`mistral-7b-base-simpo.yaml`):
```yaml
# Model
model_name_or_path: mistralai/Mistral-7B-v0.1
torch_dtype: bfloat16

# Dataset
dataset_mixer:
  HuggingFaceH4/ultrafeedback_binarized: 1.0
dataset_splits:
  - train_prefs
  - test_prefs

# SimPO hyperparameters
beta: 2.0                  # Reward scaling (2.0-10.0)
gamma_beta_ratio: 0.5       # Target margin (0-1)
loss_type: sigmoid          # sigmoid or hinge
sft_weight: 0.0             # Optional SFT regularization

# Training
learning_rate: 5e-7         # Critical: 3e-7 to 1e-6
num_train_epochs: 1
per_device_train_batch_size: 1
gradient_accumulation_steps: 8

# Output
output_dir: ./outputs/mistral-7b-simpo
```

**Launch training**:
```bash
accelerate launch --config_file accelerate_configs/deepspeed_zero3.yaml \
  scripts/run_simpo.py training_configs/mistral-7b-base-simpo.yaml
```

### Workflow 2: Fine‑tune instruct model (Llama 3 8B)

**Config** (`llama3-8b-instruct-simpo.yaml`):
```yaml
model_name_or_path: meta-llama/Meta-Llama-3-8B-Instruct

dataset_mixer:
  argilla/ultrafeedback-binarized-preferences-cleaned: 1.0

beta: 2.5
gamma_beta_ratio: 0.5
learning_rate: 5e-7
sft_weight: 0.1             # Add SFT loss to preserve capabilities

num_train_epochs: 1
per_device_train_batch_size: 2
gradient_accumulation_steps: 4
output_dir: ./outputs/llama3-8b-simpo
```

**Launch**:
```bash
accelerate launch --config_file accelerate_configs/deepspeed_zero3.yaml \
  scripts/run_simpo.py training_configs/llama3-8b-instruct-simpo.yaml
```

### Workflow 3: Reasoning‑intensive tasks (lower LR)

**For math/code tasks**:
```yaml
model_name_or_path: deepseek-ai/deepseek-math-7b-base

dataset_mixer:
  argilla/distilabel-math-preference-dpo: 1.0

beta: 5.0                   # Higher for stronger signal
gamma_beta_ratio: 0.7       # Larger margin
learning_rate: 3e-7         # Lower LR for reasoning
sft_weight: 0.0

num_train_epochs: 1
per_device_train_batch_size: 1
gradient_accumulation_steps: 16
```

## When to use vs alternatives

**Use SimPO when**:
- Нужно более простое обучение, чем у DPO (не требуется референс‑модель);
- Есть данные предпочтений (пары «выбрано/отклонено»);
- Требуется лучшая производительность, чем у DPO;
- Ограничены вычислительные ресурсы;
- Достаточно обучения на одном узле.

**Algorithm selection**:
- **SimPO**: самый простой, лучшая производительность, без референс‑модели;
- **DPO**: нужен базовый референс‑модель, более консервативный;
- **PPO**: максимальный контроль, требуется модель‑награда, сложная настройка;
- **GRPO**: экономичный по памяти RL, без критика.

**Use alternatives instead**:
- **OpenRLHF**: распределённое обучение на нескольких узлах, PPO/GRPO;
- **TRL**: нужен набор методов в одном фреймворке;
- **DPO**: проверенный базовый вариант для сравнения.

## Common issues

**Issue: Loss divergence**
Reduce learning rate:
```yaml
learning_rate: 3e-7  # Reduce from 5e-7
```

Reduce beta:
```yaml
beta: 1.0  # Reduce from 2.0
```

**Issue: Model forgets capabilities**
Add SFT regularization:
```yaml
sft_weight: 0.1  # Add SFT loss component
```

**Issue: Poor preference separation**
Increase beta and margin:
```yaml
beta: 5.0            # Increase from 2.0
gamma_beta_ratio: 0.8  # Increase from 0.5
```

**Issue: OOM during training**
Reduce batch size:
```yaml
per_device_train_batch_size: 1
gradient_accumulation_steps: 16  # Maintain effective batch
```

Enable gradient checkpointing:
```yaml
gradient_checkpointing: true
```

## Advanced topics

**Loss functions**: см. [references/loss-functions.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/simpo/references/loss-functions.md) — сигмоидальная vs hinge‑потери, математические формулировки и рекомендации по использованию.

**Hyperparameter tuning**: см. [references/hyperparameters.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/simpo/references/hyperparameters.md) — подбор beta, gamma, learning rate и рекомендации в зависимости от размера модели.

**Dataset preparation**: см. [references/datasets.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/simpo/references/datasets.md) — форматы данных предпочтений, фильтрация качества и создание собственного набора данных.

## Hardware requirements

- **GPU**: рекомендуется NVIDIA A100/H100
- **VRAM**:
  - модель 7B: 1 × A100 40 GB (DeepSpeed ZeRO‑3)
  - модель 8B: 2 × A100 40 GB
  - модель 70B: 8 × A100 80 GB
- **Single‑node**: достаточно DeepSpeed ZeRO‑3
- **Mixed precision**: рекомендуется BF16

**Memory optimization**:
- DeepSpeed ZeRO‑3 (конфигурация по умолчанию)
- Gradient checkpointing
- Flash Attention 2

## Resources

- Статья: https://arxiv.org/abs/2405.14734 (NeurIPS 2024)
- GitHub: https://github.com/princeton-nlp/SimPO
- Модели: https://huggingface.co/princeton-nlp
- Alignment Handbook: https://github.com/huggingface/alignment-handbook