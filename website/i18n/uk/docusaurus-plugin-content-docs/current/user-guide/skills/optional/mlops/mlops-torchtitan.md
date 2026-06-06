---
title: "Розподілене попереднє навчання LLM Torchtitan"
sidebar_label: "Distributed Llm Pretraining Torchtitan"
description: "Надає розподілене передтренування LLM у середовищі PyTorch‑native за допомогою torchtitan з 4‑вимірним паралелізмом (FSDP2, TP, PP, CP)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Розподілене попереднє навчання LLM Torchtitan

Надає розподілене попереднє навчання LLM у нативному PyTorch за допомогою torchtitan з 4‑D паралелізмом (FSDP2, TP, PP, CP). Використовуй для попереднього навчання Llama 3.1, DeepSeek V3 або власних моделей у масштабі від 8 до 512+ GPU з Float8, `torch.compile` та розподіленим збереженням контрольних точок.

## Метадані навички

| | |
|---|---|
| Джерело | Optional — install with `hermes skills install official/mlops/torchtitan` |
| Шлях | `optional-skills/mlops/torchtitan` |
| Версія | `1.0.0` |
| Автор | Orchestra Research |
| Ліцензія | MIT |
| Залежності | `torch>=2.6.0`, `torchtitan>=0.2.0`, `torchao>=0.5.0` |
| Платформи | linux, macos |
| Теги | `Model Architecture`, `Distributed Training`, `TorchTitan`, `FSDP2`, `Tensor Parallel`, `Pipeline Parallel`, `Context Parallel`, `Float8`, `Llama`, `Pretraining` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активована. Це те, що агент бачить як інструкції під час роботи навички.
:::

# TorchTitan — нативне розподілене попереднє навчання LLM у PyTorch

## Швидкий старт

TorchTitan — офіційна платформа PyTorch для масштабного попереднього навчання LLM з композиційним 4‑D паралелізмом (FSDP2, TP, PP, CP), забезпечуючи прискорення 65 %+ порівняно з базовими показниками на GPU H100.

**Встановлення**:
```bash
# From PyPI (stable)
pip install torchtitan

# From source (latest features, requires PyTorch nightly)
git clone https://github.com/pytorch/torchtitan
cd torchtitan
pip install -r requirements.txt
```

**Завантаження токенізатора**:
```bash
# Get HF token from https://huggingface.co/settings/tokens
python scripts/download_hf_assets.py --repo_id meta-llama/Llama-3.1-8B --assets tokenizer --hf_token=...
```

**Запуск навчання на 8 GPU**:
```bash
CONFIG_FILE="./torchtitan/models/llama3/train_configs/llama3_8b.toml" ./run_train.sh
```

## Типові робочі процеси

### Робочий процес 1: Попереднє навчання Llama 3.1 8B на одному вузлі

Скопіюй цей чек‑лист:

```
Single Node Pretraining:
- [ ] Step 1: Download tokenizer
- [ ] Step 2: Configure training
- [ ] Step 3: Launch training
- [ ] Step 4: Monitor and checkpoint
```

**Крок 1: Завантажити токенізатор**

```bash
python scripts/download_hf_assets.py \
  --repo_id meta-llama/Llama-3.1-8B \
  --assets tokenizer \
  --hf_token=YOUR_HF_TOKEN
```

**Крок 2: Налаштувати навчання**

Відредагуй або створи TOML‑файл конфігурації:

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

**Крок 3: Запустити навчання**

```bash
# 8 GPUs on single node
CONFIG_FILE="./llama3_8b_custom.toml" ./run_train.sh

# Or explicitly with torchrun
torchrun --nproc_per_node=8 \
  -m torchtitan.train \
  --job.config_file ./llama3_8b_custom.toml
```

**Крок 4: Моніторинг та збереження контрольних точок**

Логи TensorBoard зберігаються у `./outputs/tb/`:
```bash
tensorboard --logdir ./outputs/tb
```

### Робочий процес 2: Багато вузлів з SLURM

```
Multi-Node Training:
- [ ] Step 1: Configure parallelism for scale
- [ ] Step 2: Set up SLURM script
- [ ] Step 3: Submit job
- [ ] Step 4: Resume from checkpoint
```

**Крок 1: Налаштувати паралелізм для масштабу**

Для моделі 70B на 256 GPU (32 вузли):
```toml
[parallelism]
data_parallel_shard_degree = 32  # FSDP across 32 ranks
tensor_parallel_degree = 8        # TP within node
pipeline_parallel_degree = 1      # No PP for 70B
context_parallel_degree = 1       # Increase for long sequences
```

**Крок 2: Створити скрипт SLURM**

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

**Крок 3: Подати задачу**

```bash
sbatch multinode_trainer.slurm
```

**Крок 4: Відновити з контрольної точки**

Навчання автоматично відновлюється, якщо контрольна точка існує у вказаній теці.

### Робочий процес 3: Увімкнути Float8 для H100

Float8 забезпечує прискорення 30‑50 % на GPU H100.

```
Float8 Training:
- [ ] Step 1: Install torchao
- [ ] Step 2: Configure Float8
- [ ] Step 3: Launch with compile
```

**Крок 1: Встановити torchao**

```bash
USE_CPP=0 pip install git+https://github.com/pytorch/ao.git
```

**Крок 2: Налаштувати Float8**

Додай у свій TOML‑конфіг:
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

**Крок 3: Запустити з `torch.compile`**

```bash
CONFIG_FILE="./llama3_8b.toml" ./run_train.sh \
  --model.converters="quantize.linear.float8" \
  --quantize.linear.float8.enable_fsdp_float8_all_gather \
  --compile.enable
```

### Робочий процес 4: 4‑D паралелізм для моделей 405B

```
4D Parallelism (FSDP + TP + PP + CP):
- [ ] Step 1: Create seed checkpoint
- [ ] Step 2: Configure 4D parallelism
- [ ] Step 3: Launch on 512 GPUs
```

**Крок 1: Створити початкову контрольну точку**

Потрібно для узгодженої ініціалізації між етапами PP:
```bash
NGPU=1 CONFIG_FILE=./llama3_405b.toml ./run_train.sh \
  --checkpoint.enable \
  --checkpoint.create_seed_checkpoint \
  --parallelism.data_parallel_shard_degree 1 \
  --parallelism.tensor_parallel_degree 1 \
  --parallelism.pipeline_parallel_degree 1
```

**Крок 2: Налаштувати 4‑D паралелізм**

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

**Крок 3: Запустити на 512 GPU**

```bash
# 64 nodes x 8 GPUs = 512 GPUs
srun torchrun --nnodes=64 --nproc_per_node=8 \
  -m torchtitan.train \
  --job.config_file ./llama3_405b.toml
```

## Коли використовувати TorchTitan vs альтернативи

**Використовуй TorchTitan, коли:**
- Попереднє навчання LLM з нуля (8B до 405B+)
- Потрібне нативне рішення PyTorch без сторонніх залежностей
- Потрібен композиційний 4‑D паралелізм (FSDP2, TP, PP, CP)
- Навчання на H100 з підтримкою Float8
- Потрібні сумісні контрольні точки з torchtune/HuggingFace

**Використовуй альтернативи:**
- **Megatron‑LM**: Максимальна продуктивність для розгортань лише на NVIDIA
- **DeepSpeed**: Ширша екосистема оптимізацій ZeRO, підтримка інференсу
- **Axolotl/TRL**: Тюнінг, а не попереднє навчання
- **LitGPT**: Навчання в освітніх або малих масштабах

## Типові проблеми

**Проблема: Недостатньо пам’яті на великих моделях**

Увімкни activation checkpointing та зменш розмір batch:
```toml
[activation_checkpoint]
mode = "full"  # Instead of "selective"

[training]
local_batch_size = 1
```

Або використай gradient accumulation:
```toml
[training]
local_batch_size = 1
global_batch_size = 32  # Accumulates gradients
```

**Проблема: TP викликає високе споживання пам’яті через async collectives**

Встанови змінну середовища:
```bash
export TORCH_NCCL_AVOID_RECORD_STREAMS=1
```

**Проблема: Float8 не прискорює навчання**

Float8 корисний лише для великих GEMM. Відфільтруй малі шари:
```toml
[quantize.linear.float8]
filter_fqns = ["attention.wk", "attention.wv", "output", "auto_filter_small_kn"]
```

**Проблема: Не вдається завантажити контрольну точку після зміни паралелізму**

Використай можливість resharding у DCP:
```bash
# Convert sharded checkpoint to single file
python -m torch.distributed.checkpoint.format_utils \
  dcp_to_torch checkpoint/step-1000 checkpoint.pt
```

**Проблема: Ініціалізація pipeline parallelism**

Створи спочатку початкову контрольну точку (див. Робочий процес 4, Крок 1).

## Підтримувані моделі

| Модель | Розміри | Статус |
|-------|-------|--------|
| Llama 3.1 | 8B, 70B, 405B | Production |
| Llama 4 | Various | Experimental |
| DeepSeek V3 | 16B, 236B, 671B (MoE) | Experimental |
| GPT‑OSS | 20B, 120B (MoE) | Experimental |
| Qwen 3 | Various | Experimental |
| Flux | Diffusion | Experimental |

## Бенчмарки продуктивності (H100)

| Модель | GPU | Паралелізм | TPS/GPU | Техніки |
|-------|------|-------------|---------|------------|
| Llama 8B | 8 | FSDP | 5,762 | Baseline |
| Llama 8B | 8 | FSDP+compile+FP8 | 8,532 | +48% |
| Llama 70B | 256 | FSDP+TP+AsyncTP | 876 | 2D parallel |
| Llama 405B | 512 | FSDP+TP+PP | 128 | 3D parallel |

## Розширені теми

**Конфігурація FSDP2**: Див. [references/fsdp.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/torchtitan/references/fsdp.md) для детального порівняння FSDP2 vs FSDP1 та еквівалентів ZeRO.

**Навчання Float8**: Див. [references/float8.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/torchtitan/references/float8.md) для рецептів масштабування tensorwise vs rowwise.

**Контрольні точки**: Див. [references/checkpoint.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/torchtitan/references/checkpoint.md) для конвертації у HuggingFace та async checkpointing.

**Додавання власних моделей**: Див. [references/custom-models.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/torchtitan/references/custom-models.md) для протоколу TrainSpec.

## Ресурси

- GitHub: https://github.com/pytorch/torchtitan
- Стаття: https://arxiv.org/abs/2410.06511
- ICLR 2025: https://iclr.cc/virtual/2025/poster/29620
- PyTorch Forum: https://discuss.pytorch.org/c/distributed/torchtitan/44