---
title: "Распределённое предобучение LLM Torchtitan"
sidebar_label: "Distributed Llm Pretraining Torchtitan"
description: "Обеспечивает нативное распределённое предобучение LLM в PyTorch с использованием torchtitan и 4‑мерного параллелизма (FSDP2, TP, PP, CP)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Распределённое предобучение LLM с Torchtitan

Обеспечивает распределённое предобучение LLM на PyTorch‑нативном уровне с использованием torchtitan и 4‑мерного параллелизма (FSDP2, TP, PP, CP). Используй для предобучения Llama 3.1, DeepSeek V3 или кастомных моделей в масштабе от 8 до 512+ GPU с Float8, torch.compile и распределённым сохранением контрольных точек.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/torchtitan` |
| Path | `optional-skills/mlops/torchtitan` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `torch>=2.6.0`, `torchtitan>=0.2.0`, `torchao>=0.5.0` |
| Platforms | linux, macos |
| Tags | `Model Architecture`, `Distributed Training`, `TorchTitan`, `FSDP2`, `Tensor Parallel`, `Pipeline Parallel`, `Context Parallel`, `Float8`, `Llama`, `Pretraining` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# TorchTitan — PyTorch‑нативное распределённое предобучение LLM

## Быстрый старт

TorchTitan — официальная платформа PyTorch для масштабного предобучения LLM с компонуемым 4‑мерным параллелизмом (FSDP2, TP, PP, CP), обеспечивающая ускорение более 65 % по сравнению с базовыми решениями на GPU H100.

**Установка**:
```bash
# From PyPI (stable)
pip install torchtitan

# From source (latest features, requires PyTorch nightly)
git clone https://github.com/pytorch/torchtitan
cd torchtitan
pip install -r requirements.txt
```

**Скачивание токенизатора**:
```bash
# Get HF token from https://huggingface.co/settings/tokens
python scripts/download_hf_assets.py --repo_id meta-llama/Llama-3.1-8B --assets tokenizer --hf_token=...
```

**Запуск обучения на 8 GPU**:
```bash
CONFIG_FILE="./torchtitan/models/llama3/train_configs/llama3_8b.toml" ./run_train.sh
```

## Типовые рабочие процессы

### Рабочий процесс 1: Предобучение Llama 3.1 8B на одном узле

Скопируй этот чек‑лист:

```
Single Node Pretraining:
- [ ] Step 1: Download tokenizer
- [ ] Step 2: Configure training
- [ ] Step 3: Launch training
- [ ] Step 4: Monitor and checkpoint
```

**Шаг 1: Скачивание токенизатора**

```bash
python scripts/download_hf_assets.py \
  --repo_id meta-llama/Llama-3.1-8B \
  --assets tokenizer \
  --hf_token=YOUR_HF_TOKEN
```

**Шаг 2: Настройка обучения**

Отредактируй или создай TOML‑конфиг:

```toml
# llama3_8b_custom.toml
[job]
dump_folder = "./outputs"
description = "Llama 3.1 8B training"

[model]
name = "llama3"
flavor = "8B"
hf_assets_path = "./assets/hf/Llama-3.1-8B"

[optimizer]
name = "AdamW"
lr = 3e-4

[lr_scheduler]
warmup_steps = 200

[training]
local_batch_size = 2
seq_len = 8192
max_norm = 1.0
steps = 1000
dataset = "c4"

[parallelism]
data_parallel_shard_degree = -1  # Use all GPUs for FSDP

[activation_checkpoint]
mode = "selective"
selective_ac_option = "op"

[checkpoint]
enable = true
folder = "checkpoint"
interval = 500
```

**Шаг 3: Запуск обучения**

```bash
# 8 GPUs on single node
CONFIG_FILE="./llama3_8b_custom.toml" ./run_train.sh

# Or explicitly with torchrun
torchrun --nproc_per_node=8 \
  -m torchtitan.train \
  --job.config_file ./llama3_8b_custom.toml
```

**Шаг 4: Мониторинг и контрольные точки**

Логи TensorBoard сохраняются в `./outputs/tb/`:
```bash
tensorboard --logdir ./outputs/tb
```

### Рабочий процесс 2: Мульти‑узловое обучение с SLURM

```
Multi-Node Training:
- [ ] Step 1: Configure parallelism for scale
- [ ] Step 2: Set up SLURM script
- [ ] Step 3: Submit job
- [ ] Step 4: Resume from checkpoint
```

**Шаг 1: Настройка параллелизма для масштаба**

Для модели 70 B на 256 GPU (32 узла):
```toml
[parallelism]
data_parallel_shard_degree = 32  # FSDP across 32 ranks
tensor_parallel_degree = 8        # TP within node
pipeline_parallel_degree = 1      # No PP for 70B
context_parallel_degree = 1       # Increase for long sequences
```

**Шаг 2: Создание SLURM‑скрипта**

```bash
#!/bin/bash
#SBATCH --job-name=llama70b
#SBATCH --nodes=32
#SBATCH --ntasks-per-node=8
#SBATCH --gpus-per-node=8

srun torchrun \
  --nnodes=32 \
  --nproc_per_node=8 \
  --rdzv_backend=c10d \
  --rdzv_endpoint=$MASTER_ADDR:$MASTER_PORT \
  -m torchtitan.train \
  --job.config_file ./llama3_70b.toml
```

**Шаг 3: Отправка задания**

```bash
sbatch multinode_trainer.slurm
```

**Шаг 4: Возобновление из контрольной точки**

Обучение автоматически возобновляется, если в настроенной папке есть контрольная точка.

### Рабочий процесс 3: Включение Float8‑обучения для H100

Float8 даёт ускорение 30‑50 % на GPU H100.

```
Float8 Training:
- [ ] Step 1: Install torchao
- [ ] Step 2: Configure Float8
- [ ] Step 3: Launch with compile
```

**Шаг 1: Установка torchao**

```bash
USE_CPP=0 pip install git+https://github.com/pytorch/ao.git
```

**Шаг 2: Настройка Float8**

Добавь в свой TOML‑конфиг:
```toml
[model]
converters = ["quantize.linear.float8"]

[quantize.linear.float8]
enable_fsdp_float8_all_gather = true
precompute_float8_dynamic_scale_for_fsdp = true
filter_fqns = ["output"]  # Exclude output layer

[compile]
enable = true
components = ["model", "loss"]
```

**Шаг 3: Запуск с компиляцией**

```bash
CONFIG_FILE="./llama3_8b.toml" ./run_train.sh \
  --model.converters="quantize.linear.float8" \
  --quantize.linear.float8.enable_fsdp_float8_all_gather \
  --compile.enable
```

### Рабочий процесс 4: 4‑мерный параллелизм для моделей 405 B

```
4D Parallelism (FSDP + TP + PP + CP):
- [ ] Step 1: Create seed checkpoint
- [ ] Step 2: Configure 4D parallelism
- [ ] Step 3: Launch on 512 GPUs
```

**Шаг 1: Создание seed‑контрольной точки**

Требуется для согласованной инициализации на всех этапах PP:
```bash
NGPU=1 CONFIG_FILE=./llama3_405b.toml ./run_train.sh \
  --checkpoint.enable \
  --checkpoint.create_seed_checkpoint \
  --parallelism.data_parallel_shard_degree 1 \
  --parallelism.tensor_parallel_degree 1 \
  --parallelism.pipeline_parallel_degree 1
```

**Шаг 2: Настройка 4‑мерного параллелизма**

```toml
[parallelism]
data_parallel_shard_degree = 8   # FSDP
tensor_parallel_degree = 8       # TP within node
pipeline_parallel_degree = 8     # PP across nodes
context_parallel_degree = 1      # CP for long sequences

[training]
local_batch_size = 32
seq_len = 8192
```

**Шаг 3: Запуск на 512 GPU**

```bash
# 64 nodes x 8 GPUs = 512 GPUs
srun torchrun --nnodes=64 --nproc_per_node=8 \
  -m torchtitan.train \
  --job.config_file ./llama3_405b.toml
```

## Когда использовать TorchTitan vs альтернативы

**Используй TorchTitan, когда:**
- Предобучаешь LLM с нуля (от 8 B до 405 B+)
- Нужно решение полностью на PyTorch без сторонних зависимостей
- Требуется компонуемый 4‑мерный параллелизм (FSDP2, TP, PP, CP)
- Обучаешься на H100 с поддержкой Float8
- Хочешь совместимые контрольные точки с torchtune/HuggingFace

**Выбирай альтернативы, когда:**
- **Megatron‑LM**: максимальная производительность для чисто NVIDIA‑ориентированных развертываний
- **DeepSpeed**: широкая экосистема оптимизаций ZeRO, поддержка инференса
- **Axolotl/TRL**: тонкая настройка, а не предобучение
- **LitGPT**: образовательные цели, небольшие масштабы обучения

## Распространённые проблемы

**Проблема: Out of memory на больших моделях**

Включи checkpointing активаций и уменьшите размер батча:
```toml
[activation_checkpoint]
mode = "full"  # Instead of "selective"

[training]
local_batch_size = 1
```

Или используй накопление градиентов:
```toml
[training]
local_batch_size = 1
global_batch_size = 32  # Accumulates gradients
```

**Проблема: TP вызывает высокий расход памяти из‑за async collectives**

Установи переменную окружения:
```bash
export TORCH_NCCL_AVOID_RECORD_STREAMS=1
```

**Проблема: Float8‑обучение не ускоряется**

Float8 выгоден только для больших GEMM‑операций. Отфильтруй небольшие слои:
```toml
[quantize.linear.float8]
filter_fqns = ["attention.wk", "attention.wv", "output", "auto_filter_small_kn"]
```

**Проблема: Ошибка загрузки контрольной точки после изменения параллелизма**

Используй возможность пересборки (resharding) DCP:
```bash
# Convert sharded checkpoint to single file
python -m torch.distributed.checkpoint.format_utils \
  dcp_to_torch checkpoint/step-1000 checkpoint.pt
```

**Проблема: Инициализация pipeline parallelism**

Сначала создай seed‑контрольную точку (см. рабочий процесс 4, шаг 1).

## Поддерживаемые модели

| Model | Sizes | Status |
|-------|-------|--------|
| Llama 3.1 | 8B, 70B, 405B | Production |
| Llama 4 | Various | Experimental |
| DeepSeek V3 | 16B, 236B, 671B (MoE) | Experimental |
| GPT-OSS | 20B, 120B (MoE) | Experimental |
| Qwen 3 | Various | Experimental |
| Flux | Diffusion | Experimental |

## Показатели производительности (H100)

| Model | GPUs | Parallelism | TPS/GPU | Techniques |
|-------|------|-------------|---------|------------|
| Llama 8B | 8 | FSDP | 5,762 | Baseline |
| Llama 8B | 8 | FSDP+compile+FP8 | 8,532 | +48% |
| Llama 70B | 256 | FSDP+TP+AsyncTP | 876 | 2D parallel |
| Llama 405B | 512 | FSDP+TP+PP | 128 | 3D parallel |

## Продвинутые темы

**Конфигурация FSDP2**: См. [references/fsdp.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/torchtitan/references/fsdp.md) для подробного сравнения FSDP2 и FSDP1 и эквивалентов ZeRO.

**Обучение Float8**: См. [references/float8.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/torchtitan/references/float8.md) для рецептов масштабирования tensorwise vs rowwise.

**Контрольные точки**: См. [references/checkpoint.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/torchtitan/references/checkpoint.md) для конвертации в HuggingFace и асинхронного сохранения.

**Добавление кастомных моделей**: См. [references/custom-models.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/torchtitan/references/custom-models.md) для протокола TrainSpec.

## Ресурсы

- GitHub: https://github.com/pytorch/torchtitan
- Статья: https://arxiv.org/abs/2410.06511
- ICLR 2025: https://iclr.cc/virtual/2025/poster/29620
- Форум PyTorch: https://discuss.pytorch.org/c/distributed/torchtitan/44