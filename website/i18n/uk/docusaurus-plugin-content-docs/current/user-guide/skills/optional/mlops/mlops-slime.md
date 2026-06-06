---
title: "Slime Rl Training — Надає рекомендації щодо пост‑тренування LLM за допомогою RL, використовуючи slime, фреймворк Megatron+SGLang"
sidebar_label: "Slime Rl Training"
description: "Надає рекомендації щодо пост‑тренування LLM за допомогою RL з використанням slime, фреймворку Megatron+SGLang"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Тренування Slime RL

Надає рекомендації щодо пост‑тренування LLM за допомогою RL, використовуючи slime — фреймворк Megatron+SGLang. Використовуй, коли тренуєш моделі GLM, реалізуєш власні робочі процеси генерації даних або потребуєш тісної інтеграції Megatron‑LM для масштабування RL.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/slime` |
| Path | `optional-skills/mlops/slime` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `sglang-router>=0.2.3`, `ray`, `torch>=2.0.0`, `transformers>=4.40.0` |
| Platforms | linux, macos |
| Tags | `Reinforcement Learning`, `Megatron-LM`, `SGLang`, `GRPO`, `Post-Training`, `GLM` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активована. Це те, що агент бачить як інструкції під час роботи навички.
:::

# slime: фреймворк пост‑тренування LLM для масштабування RL

slime — це фреймворк пост‑тренування LLM від команди THUDM Tsinghua, який живить GLM‑4.5, GLM‑4.6 та GLM‑4.7. Він з’єднує Megatron‑LM для тренування з SGLang для високопродуктивної генерації rollout‑ів.

## Коли використовувати slime

**Обери slime, коли потрібне:**
- Нативне тренування Megatron‑LM з інференсом SGLang
- Кастомні робочі процеси генерації даних з гнучкими буферами даних
- Тренування моделей GLM, Qwen3, DeepSeek V3 або Llama 3
- Дослідницький фреймворк з підтримкою продакшн (Z.ai)

**Розглянь альтернативи, коли:**
- Потрібні функції стабільності корпоративного рівня → використай **miles**
- Хочеш гнучко міняти бекенд → використай **verl**
- Потрібні абстракції, що працюють нативно з PyTorch → використай **torchforge**

## Ключові можливості

- **Тренування**: Megatron‑LM з повною підтримкою паралелізму (TP, PP, DP, SP)
- **Rollout**: генерація високої пропускної здатності на базі SGLang з роутером
- **Буфер даних**: гнучке керування підказками та зберігання зразків
- **Моделі**: GLM‑4.x, Qwen3, DeepSeek V3/R1, Llama 3

## Огляд архітектури

<!-- ascii-guard-ignore -->
```
┌─────────────────────────────────────────────────────────┐
│                    Data Buffer                          │
│ - Prompt initialization and management                  │
│ - Custom data generation and filtering                  │
│ - Rollout sample storage                                │
└─────────────┬───────────────────────────┬───────────────┘
              │                           │
┌─────────────▼───────────┐ ┌─────────────▼───────────────┐
│ Training (Megatron-LM)  │ │ Rollout (SGLang + Router)   │
│ - Actor model training  │ │ - Response generation       │
│ - Critic (optional)     │ │ - Reward/verifier output    │
│ - Weight sync to rollout│ │ - Multi-turn support        │
└─────────────────────────┘ └─────────────────────────────┘
```
<!-- ascii-guard-ignore-end -->

## Встановлення

```bash
# Recommended: Docker
docker pull slimerl/slime:latest
docker run --rm --gpus all --ipc=host --shm-size=16g \
  -it slimerl/slime:latest /bin/bash

# Inside container
cd /root/slime && pip install -e . --no-deps
```

### З вихідного коду

```bash
git clone https://github.com/THUDM/slime.git
cd slime
pip install -r requirements.txt
pip install -e .
```

## Швидкий старт: тренування GRPO

```bash
# Source model configuration
source scripts/models/qwen3-4B.sh

# Launch training
python train.py \
    --actor-num-nodes 1 \
    --actor-num-gpus-per-node 4 \
    --rollout-num-gpus 4 \
    --advantage-estimator grpo \
    --use-kl-loss --kl-loss-coef 0.001 \
    --rollout-batch-size 32 \
    --n-samples-per-prompt 8 \
    --global-batch-size 256 \
    --num-rollout 3000 \
    --prompt-data /path/to/data.jsonl \
    ${MODEL_ARGS[@]} ${CKPT_ARGS[@]}
```

---

## Робочий процес 1: Стандартне тренування GRPO

Використовуй цей процес для тренування моделей розуміння з груповими відносними перевагами.

### Перелік вимог
- [ ] Docker‑окруження або встановлені Megatron‑LM + SGLang
- [ ] Контрольна точка моделі (формат HuggingFace або Megatron)
- [ ] Тренувальні дані у форматі JSONL

### Крок 1: Підготовка даних

```python
# data.jsonl format
{"prompt": "What is 2 + 2?", "label": "4"}
{"prompt": "Solve: 3x = 12", "label": "x = 4"}
```

Або у форматі чату:
```python
{
    "prompt": [
        {"role": "system", "content": "You are a math tutor."},
        {"role": "user", "content": "What is 15 + 27?"}
    ],
    "label": "42"
}
```

### Крок 2: Налаштування моделі

Обери попередньо налаштований скрипт моделі:

```bash
# List available models
ls scripts/models/
# glm4-9B.sh, qwen3-4B.sh, qwen3-30B-A3B.sh, deepseek-v3.sh, llama3-8B.sh, ...

# Source your model
source scripts/models/qwen3-4B.sh
```

### Крок 3: Запуск тренування

```bash
python train.py \
    --actor-num-nodes 1 \
    --actor-num-gpus-per-node 8 \
    --rollout-num-gpus 8 \
    --advantage-estimator grpo \
    --use-kl-loss \
    --kl-loss-coef 0.001 \
    --prompt-data /path/to/train.jsonl \
    --input-key prompt \
    --label-key label \
    --apply-chat-template \
    --rollout-batch-size 32 \
    --n-samples-per-prompt 8 \
    --global-batch-size 256 \
    --num-rollout 3000 \
    --save-interval 100 \
    --eval-interval 50 \
    ${MODEL_ARGS[@]}
```

### Крок 4: Моніторинг тренування
- [ ] Перевір TensorBoard: `tensorboard --logdir outputs/`
- [ ] Переконайся, що криві нагород зростають
- [ ] Слідкуй за використанням GPU на всіх вузлах

---

## Робочий процес 2: Асинхронне тренування

Використовуй async‑режим для підвищення пропускної здатності шляхом перекриття rollout‑у та тренування.

### Коли застосовувати async
- Великі моделі з довгим часом генерації
- Великий простій GPU у синхронному режимі
- Достатньо пам’яті для буферизації

### Запуск асинхронного тренування

```bash
python train_async.py \
    --actor-num-nodes 1 \
    --actor-num-gpus-per-node 8 \
    --rollout-num-gpus 8 \
    --advantage-estimator grpo \
    --async-buffer-size 4 \
    --prompt-data /path/to/train.jsonl \
    ${MODEL_ARGS[@]}
```

### Параметри, специфічні для async

```bash
--async-buffer-size 4        # Number of rollouts to buffer
--update-weights-interval 2  # Sync weights every N rollouts
```

---

## Робочий процес 3: Багатокрокове агентське тренування

Використовуй цей процес для тренування агентів з використанням інструментів або багатокроковим розумінням.

### Вимоги
- [ ] Кастомна функція generate для багатокрокової логіки
- [ ] Інтерфейс інструменту/оточення

### Крок 1: Визначення кастомної функції generate

```python
# custom_generate.py
async def custom_generate(args, samples, evaluation=False):
    """Multi-turn generation with tool calling."""
    for sample in samples:
        conversation = sample.prompt

        for turn in range(args.max_turns):
            # Generate response
            response = await generate_single(conversation)

            # Check for tool call
            tool_call = extract_tool_call(response)
            if tool_call:
                tool_result = execute_tool(tool_call)
                conversation.append({"role": "assistant", "content": response})
                conversation.append({"role": "tool", "content": tool_result})
            else:
                break

        sample.response = response
        sample.reward = compute_reward(sample)

    return samples
```

### Крок 2: Запуск з кастомною функцією

```bash
python train.py \
    --custom-generate-function-path custom_generate.py \
    --max-turns 5 \
    --prompt-data /path/to/agent_data.jsonl \
    ${MODEL_ARGS[@]}
```

Дивись `examples/search-r1/` для повного прикладу багатокрокового пошуку.

---

## Довідка з конфігурації

### Три категорії аргументів

slime використовує три типи аргументів:

**1. Аргументи Megatron** (передаються безпосередньо):
```bash
--tensor-model-parallel-size 2
--pipeline-model-parallel-size 1
--num-layers 32
--hidden-size 4096
```

**2. Аргументи SGLang** (з префіксом `--sglang-`):
```bash
--sglang-mem-fraction-static 0.8
--sglang-context-length 8192
--sglang-log-level INFO
```

**3. Аргументи slime**:
```bash
# Resource allocation
--actor-num-nodes 1
--actor-num-gpus-per-node 8
--rollout-num-gpus 8
--colocate  # Share GPUs between training/inference

# Data
--prompt-data /path/to/data.jsonl
--input-key prompt
--label-key label

# Training loop
--num-rollout 3000
--rollout-batch-size 32
--n-samples-per-prompt 8
--global-batch-size 256

# Algorithm
--advantage-estimator grpo  # or: gspo, ppo, reinforce_plus_plus
--use-kl-loss
--kl-loss-coef 0.001
```

### Ключові обмеження

```
rollout_batch_size × n_samples_per_prompt = global_batch_size × num_steps_per_rollout
```

Приклад: 32 × 8 = 256 × 1

---

## Система буфера даних

Буфер даних slime забезпечує гнучке управління даними:

### Базове джерело даних

```python
class RolloutDataSource:
    def get_samples(self, num_samples):
        """Fetch prompts from dataset."""
        return self.dataset.sample(num_samples)

    def add_samples(self, samples):
        """Called after generation (no-op by default)."""
        pass
```

### Буферизоване джерело даних (Off‑Policy)

```python
class RolloutDataSourceWithBuffer(RolloutDataSource):
    def __init__(self):
        self.buffer = []

    def add_samples(self, samples):
        """Store generated samples for reuse."""
        self.buffer.extend(samples)

    def buffer_filter(self, args, buffer, num_samples):
        """Custom selection logic (prioritized, stratified, etc.)."""
        return select_best(buffer, num_samples)
```

---

## Поширені проблеми та рішення

### Проблема: збій SGLang Engine

**Симптоми**: інференсний движок падає під час тренування

**Рішення**:
```bash
# Enable fault tolerance
--use-fault-tolerance

# Increase memory allocation
--sglang-mem-fraction-static 0.85

# Reduce batch size
--rollout-batch-size 16
```

### Проблема: тайм‑аут синхронізації ваг

**Симптоми**: тренування зависає після rollout

**Рішення**:
```bash
# Increase sync interval
--update-weights-interval 5

# Use colocated mode (no network transfer)
--colocate
```

### Проблема: OOM під час тренування

**Симптоми**: CUDA OOM у зворотному проході

**Рішення**:
```bash
# Enable gradient checkpointing
--recompute-activations

# Reduce micro-batch size
--micro-batch-size 1

# Enable sequence parallelism
--sequence-parallel
```

### Проблема: повільне завантаження даних

**Симптоми**: GPU простоює під час отримання даних

**Рішення**:
```bash
# Increase data workers
--num-data-workers 4

# Use streaming dataset
--streaming-data
```

---

## Підтримувані моделі

| Сімейство моделей | Конфігурації |
|-------------------|--------------|
| GLM | GLM‑4.5, GLM‑4.6, GLM‑4.7, GLM‑Z1-9B |
| Qwen | Qwen3 (4B, 8B, 30B‑A3B), Qwen3‑MoE, Qwen2.5 |
| DeepSeek | V3, V3.1, R1 |
| Llama | Llama 3 (8B, 70B) |
| Інші | Kimi K2, Moonlight‑16B |

Для кожної моделі є попередньо налаштовані скрипти у `scripts/models/`.

---

## Розширені теми

### Режим спільного розміщення

Спільне використання GPU між тренуванням та інференсом для зменшення споживання пам’яті:

```bash
python train.py \
    --colocate \
    --actor-num-gpus-per-node 8 \
    --sglang-mem-fraction-static 0.4 \
    ${MODEL_ARGS[@]}
```

### Кастомна модель нагороди

```python
# custom_rm.py
class CustomRewardModel:
    def __init__(self, model_path):
        self.model = load_model(model_path)

    def compute_reward(self, prompts, responses):
        inputs = self.tokenize(prompts, responses)
        scores = self.model(inputs)
        return scores.tolist()
```

```bash
--custom-rm-path custom_rm.py
```

### Оцінка мульти‑задачності

```bash
--eval-prompt-data aime /path/to/aime.jsonl \
--eval-prompt-data gsm8k /path/to/gsm8k.jsonl \
--n-samples-per-eval-prompt 16
```

---

## Ресурси

- **Документація**: https://thudm.github.io/slime/
- **GitHub**: https://github.com/THUDM/slime
- **Блог**: https://lmsys.org/blog/2025-07-09-slime/
- **Приклади**: Дивись каталог `examples/` для 14+ готових прикладів