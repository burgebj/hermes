---
title: "Slime Rl Training — Предоставляет руководство по постобучению LLM с использованием RL и slime, фреймворка Megatron+SGLang"
sidebar_label: "Slime Rl Training"
description: "Предоставляет рекомендации по постобучению LLM с использованием RL и slime, фреймворка Megatron+SGLang"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Обучение Slime RL

Предоставляет руководство по постобучению LLM с помощью RL, используя slime — фреймворк Megatron+SGLang. Используй при обучении моделей GLM, реализации пользовательских рабочих процессов генерации данных или необходимости тесной интеграции Megatron-LM для масштабирования RL.

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# slime: фреймворк постобучения LLM для масштабирования RL

slime — это фреймворк постобучения LLM от команды THUDM Tsinghua, использующийся в GLM‑4.5, GLM‑4.6 и GLM‑4.7. Он соединяет Megatron‑LM для обучения с SGLang для высокопроизводительной генерации роллаутов.

## Когда использовать slime

**Выбирай slime, когда нужно:**
- Нативное обучение Megatron‑LM с инференсом SGLang
- Пользовательские рабочие процессы генерации данных с гибкими буферами данных
- Обучение моделей GLM, Qwen3, DeepSeek V3 или Llama 3
- Исследовательский фреймворк с поддержкой продакшн (Z.ai)

**Рассмотри альтернативы, когда:**
- Требуются функции стабильности корпоративного уровня → используй **miles**
- Нужна гибкая замена бекенда → используй **verl**
- Требуются абстракции, родные PyTorch → используй **torchforge**

## Ключевые возможности

- **Обучение**: Megatron‑LM с полной поддержкой параллелизма (TP, PP, DP, SP)
- **Роллаут**: генерация с высокой пропускной способностью на основе SGLang с роутером
- **Буфер данных**: гибкое управление подсказками и хранение образцов
- **Модели**: GLM‑4.x, Qwen3, DeepSeek V3/R1, Llama 3

## Обзор архитектуры

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

## Установка

```bash
# Recommended: Docker
docker pull slimerl/slime:latest
docker run --rm --gpus all --ipc=host --shm-size=16g \
  -it slimerl/slime:latest /bin/bash

# Inside container
cd /root/slime && pip install -e . --no-deps
```

### Из исходного кода

```bash
git clone https://github.com/THUDM/slime.git
cd slime
pip install -r requirements.txt
pip install -e .
```

## Быстрый старт: обучение GRPO

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

## Рабочий процесс 1: Стандартное обучение GRPO

Используй этот рабочий процесс для обучения моделей рассуждения с групповыми относительными преимуществами.

### Список проверок перед началом
- [ ] Docker‑окружение или установленный Megatron‑LM + SGLang
- [ ] Контрольная точка модели (формат HuggingFace или Megatron)
- [ ] Обучающие данные в формате JSONL

### Шаг 1: Подготовка данных

```python
# data.jsonl format
{"prompt": "What is 2 + 2?", "label": "4"}
{"prompt": "Solve: 3x = 12", "label": "x = 4"}
```

Или в формате чата:
```python
{
    "prompt": [
        {"role": "system", "content": "You are a math tutor."},
        {"role": "user", "content": "What is 15 + 27?"}
    ],
    "label": "42"
}
```

### Шаг 2: Настройка модели

Выбери преднастроенный скрипт модели:

```bash
# List available models
ls scripts/models/
# glm4-9B.sh, qwen3-4B.sh, qwen3-30B-A3B.sh, deepseek-v3.sh, llama3-8B.sh, ...

# Source your model
source scripts/models/qwen3-4B.sh
```

### Шаг 3: Запуск обучения

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

### Шаг 4: Мониторинг обучения
- [ ] Проверить TensorBoard: `tensorboard --logdir outputs/`
- [ ] Убедиться, что кривые награды растут
- [ ] Следить за загрузкой GPU на всех узлах

---

## Рабочий процесс 2: Асинхронное обучение

Используй асинхронный режим для повышения пропускной способности за счёт наложения роллаутов и обучения.

### Когда использовать асинхронный режим
- Большие модели с длительным временем генерации
- Высокий простой GPU в синхронном режиме
- Достаточно памяти для буферизации

### Запуск асинхронного обучения

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

### Параметры, специфичные для async

```bash
--async-buffer-size 4        # Number of rollouts to buffer
--update-weights-interval 2  # Sync weights every N rollouts
```

---

## Рабочий процесс 3: Многошаговое агентное обучение

Используй этот рабочий процесс для обучения агентов с использованием инструментов или многошагового рассуждения.

### Предварительные требования
- [ ] Пользовательская функция генерации для многошаговой логики
- [ ] Интерфейс инструмента/окружения

### Шаг 1: Определение пользовательской функции генерации

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

### Шаг 2: Запуск с пользовательской функцией

```bash
python train.py \
    --custom-generate-function-path custom_generate.py \
    --max-turns 5 \
    --prompt-data /path/to/agent_data.jsonl \
    ${MODEL_ARGS[@]}
```

См. `examples/search-r1/` для полного примера многошагового поиска.

---

## Справочник конфигураций

### Три категории аргументов

slime использует три типа аргументов:

**1. Аргументы Megatron** (передаются напрямую):
```bash
--tensor-model-parallel-size 2
--pipeline-model-parallel-size 1
--num-layers 32
--hidden-size 4096
```

**2. Аргументы SGLang** (с префиксом `--sglang-`):
```bash
--sglang-mem-fraction-static 0.8
--sglang-context-length 8192
--sglang-log-level INFO
```

**3. Аргументы slime**:
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

### Ключевые ограничения

```
rollout_batch_size × n_samples_per_prompt = global_batch_size × num_steps_per_rollout
```

Пример: 32 × 8 = 256 × 1

---

## Система буфера данных

Буфер данных slime обеспечивает гибкое управление данными:

### Базовый источник данных

```python
class RolloutDataSource:
    def get_samples(self, num_samples):
        """Fetch prompts from dataset."""
        return self.dataset.sample(num_samples)

    def add_samples(self, samples):
        """Called after generation (no-op by default)."""
        pass
```

### Буферизованный источник данных (Off‑Policy)

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

## Распространённые проблемы и решения

### Проблема: сбой движка SGLang

**Симптомы**: Движок инференса падает в середине обучения

**Решения**:
```bash
# Enable fault tolerance
--use-fault-tolerance

# Increase memory allocation
--sglang-mem-fraction-static 0.85

# Reduce batch size
--rollout-batch-size 16
```

### Проблема: таймаут синхронизации весов

**Симптомы**: Обучение зависает после роллаута

**Решения**:
```bash
# Increase sync interval
--update-weights-interval 5

# Use colocated mode (no network transfer)
--colocate
```

### Проблема: OOM во время обучения

**Симптомы**: CUDA OOM в обратном проходе

**Решения**:
```bash
# Enable gradient checkpointing
--recompute-activations

# Reduce micro-batch size
--micro-batch-size 1

# Enable sequence parallelism
--sequence-parallel
```

### Проблема: медленная загрузка данных

**Симптомы**: GPU простаивает во время получения данных

**Решения**:
```bash
# Increase data workers
--num-data-workers 4

# Use streaming dataset
--streaming-data
```

---

## Поддерживаемые модели

| Семейство моделей | Конфигурации |
|-------------------|--------------|
| GLM | GLM‑4.5, GLM‑4.6, GLM‑4.7, GLM‑Z1‑9B |
| Qwen | Qwen3 (4B, 8B, 30B‑A3B), Qwen3‑MoE, Qwen2.5 |
| DeepSeek | V3, V3.1, R1 |
| Llama | Llama 3 (8B, 70B) |
| Другие | Kimi K2, Moonlight‑16B |

Для каждой модели есть преднастроенные скрипты в `scripts/models/`.

---

## Продвинутые темы

### Режим совместного размещения

Совместное использование GPU между обучением и инференсом для снижения потребления памяти:

```bash
python train.py \
    --colocate \
    --actor-num-gpus-per-node 8 \
    --sglang-mem-fraction-static 0.4 \
    ${MODEL_ARGS[@]}
```

### Пользовательская модель награды

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

### Мультизадачная оценка

```bash
--eval-prompt-data aime /path/to/aime.jsonl \
--eval-prompt-data gsm8k /path/to/gsm8k.jsonl \
--n-samples-per-eval-prompt 16
```

---

## Ресурсы

- **Документация**: https://thudm.github.io/slime/
- **GitHub**: https://github.com/THUDM/slime
- **Блог**: https://lmsys.org/blog/2025-07-09-slime/
- **Примеры**: См. каталог `examples/` для более чем 14 готовых примеров