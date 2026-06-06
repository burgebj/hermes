---
title: "Obliteratus — OBLITERATUS: устранять отказы LLM (разница в средних)"
sidebar_label: "Obliteratus"
description: "OBLITERATUS: уничтожать отказы LLM (разница в средних)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Облитератус

OBLITERATUS: уничтожать отказы LLM (diff‑in‑means).
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/mlops/inference/obliteratus` |
| Версия | `2.0.0` |
| Автор | Hermes Agent |
| Лицензия | MIT |
| Зависимости | `obliteratus`, `torch`, `transformers`, `bitsandbytes`, `accelerate`, `safetensors` |
| Платформы | linux, macos |
| Теги | `Abliteration`, `Uncensoring`, `Refusal-Removal`, `LLM`, `Weight-Projection`, `SVD`, `Mechanistic-Interpretability`, `HuggingFace`, `Model-Surgery` |
| Связанные навыки | `vllm`, `gguf`, [`huggingface-tokenizers`](/docs/user-guide/skills/optional/mlops/mlops-huggingface-tokenizers) |
:::info
Следующее — полное определение **skill**, которое Hermes загружает, когда этот **skill** вызывается. Это то, что агент видит как инструкции, когда **skill** активен.
:::

# OBLITERATUS Skill
## Что внутри

9 методов CLI, 28 модулей анализа, 116 предустановок моделей в 5 уровнях вычислений, оценка турнира и рекомендации, основанные на телеметрии.

Удаление поведения отказа (guardrails) из LLM с открытыми весами без переобучения или дообучения. Использует техники механистической интерпретируемости — включая diff-in-means, SVD, whitened SVD, LEACE concept erasure, SAE decomposition, Bayesian kernel projection и другие — для выявления и хирургического удаления направлений отказа из весов модели при сохранении способностей рассуждения.

**Предупреждение о лицензии:** OBLITERATUS распространяется под AGPL‑3.0. НИКОГДА не импортируй его как библиотеку Python. Всегда вызывай через CLI (`obliteratus` command) или subprocess. Это сохраняет чистоту лицензии MIT Hermes Agent.
## Видео‑руководство

Пошаговое руководство по использованию OBLITERATUS агентом Hermes для уничтожения Gemma:
https://www.youtube.com/watch?v=8fG9BrNTeHs ("OBLITERATUS: An AI Agent Removed Gemma 4's Safety Guardrails")

Полезно, когда пользователь хочет получить визуальное представление о полном рабочем процессе перед тем, как запускать его самостоятельно.
## Когда использовать этот skill

Триггер, когда пользователь:

- Хочет «расцензурировать» или «обезвредить» LLM
- Спрашивает о снятии отказов/ограничений модели
- Желает создать нецензурированную версию Llama, Qwen, Mistral и т.п.
- Упоминает «удаление отказов», «обезвреживание», «проекция весов»
- Хочет проанализировать, как работает механизм отказа модели
- Ссылается на OBLITERATUS, abliterator или направления отказов
## Шаг 1: Установка

Проверь, установлен ли уже:
```bash
obliteratus --version 2>/dev/null && echo "INSTALLED" || echo "NOT INSTALLED"
```

Если не установлен, клонируй и установи из GitHub:
```bash
git clone https://github.com/elder-plinius/OBLITERATUS.git
cd OBLITERATUS
pip install -e .
# For Gradio web UI support:
# pip install -e ".[spaces]"
```

**ВАЖНО:** Подтверди у пользователя перед установкой. Это загрузит ~5‑10 ГБ зависимостей (PyTorch, Transformers, bitsandbytes и др.).
## Шаг 2: Проверка оборудования

Прежде чем что‑либо делать, проверь, какой GPU доступен:
```bash
python3 -c "
import torch
if torch.cuda.is_available():
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f'GPU: {gpu}')
    print(f'VRAM: {vram:.1f} GB')
    if vram < 4: print('TIER: tiny (models under 1B)')
    elif vram < 8: print('TIER: small (models 1-4B)')
    elif vram < 16: print('TIER: medium (models 4-9B with 4bit quant)')
    elif vram < 32: print('TIER: large (models 8-32B with 4bit quant)')
    else: print('TIER: frontier (models 32B+)')
else:
    print('NO GPU - only tiny models (under 1B) on CPU')
"
```

### Требования к VRAM (при 4‑битной квантизации)

| VRAM      | Максимальный размер модели | Примеры моделей                              |
|:----------|:---------------------------|:--------------------------------------------|
| только CPU | ~1 млрд параметров          | GPT-2, TinyLlama, SmolLM                    |
| 4‑8 ГБ    | ~4 млрд параметров          | Qwen2.5-1.5B, Phi-3.5 mini, Llama 3.2 3B   |
| 8‑16 ГБ   | ~9 млрд параметров          | Llama 3.1 8B, Mistral 7B, Gemma 2 9B       |
| 24 ГБ     | ~32 млрд параметров         | Qwen3-32B, Llama 3.1 70B (tight), Command‑R |
| 48 ГБ+    | ~72 млрд+ параметров        | Qwen2.5-72B, DeepSeek‑R1                    |
| Multi‑GPU | 200 млрд+ параметров        | Llama 3.1 405B, DeepSeek‑V3 (685B MoE)      |
## Шаг 3: Обзор доступных моделей и получение рекомендаций

```bash
# Browse models by compute tier
obliteratus models --tier medium

# Get architecture info for a specific model
obliteratus info <model_name>

# Get telemetry-driven recommendation for best method & params
obliteratus recommend <model_name>
obliteratus recommend <model_name> --insights  # global cross-architecture rankings
```
## Шаг 4: Выбор метода

### Руководство по выбору метода
**По умолчанию / рекомендуется для большинства случаев: `advanced`.** Он использует многовекторный SVD с проекцией, сохраняющей норму, и хорошо протестирован.

| Ситуация                           | Рекомендуемый метод | Почему                                   |
|:----------------------------------|:--------------------|:------------------------------------------|
| По умолчанию / большинство моделей | `advanced`          | Многовекторный SVD, сохраняет норму, надёжный |
| Быстрый тест / прототипирование   | `basic`             | Быстро, просто, достаточно для оценки    |
| Плотная модель (Llama, Mistral)   | `advanced`          | Многовекторный, сохраняет норму           |
| MoE‑модель (DeepSeek, Mixtral)    | `nuclear`           | Экспертно‑гранулированный, справляется со сложностью MoE |
| Модель рассуждения (R1 distills)  | `surgical`          | Учитывает цепочку рассуждений (CoT), сохраняет её |
| Упорные отказы продолжаются       | `aggressive`        | Отбеленный SVD + хирургия головы + jailbreak |
| Нужно обратимое изменение         | Использовать вектор управления (см. раздел Analysis) |
| Максимальное качество, время не важно | `optimized`         | Байесовский поиск лучших параметров      |
| Экспериментальное автоопределение  | `informed`          | Автоопределяет тип выравнивания — экспериментально, может не всегда превосходить `advanced` |

### 9 CLI‑методов
- **basic** — Одно направление отказа через diff-in-means. Быстро (~5‑10 мин для 8B).
- **advanced** (DEFAULT, RECOMMENDED) — Несколько направлений SVD, проекция, сохраняющая норму, 2 прохода уточнения. Средняя скорость (~10‑20 мин).
- **aggressive** — Отбеленный SVD + jailbreak‑контрастивный + хирургия attention‑головы. Более высокий риск повреждения связности.
- **spectral_cascade** — DCT‑разложение в частотной области. Исследовательский/новый подход.
- **informed** — Выполняет анализ **DURING** абляции для автонастройки. Экспериментально — медленнее и менее предсказуемо, чем `advanced`.
- **surgical** — SAE‑фичи + маскирование нейронов + хирургия головы + per‑expert. Очень медленно (~1‑2 ч). Лучший вариант для моделей рассуждения.
- **optimized** — Байесовский поиск гиперпараметров (Optuna TPE). Самый длительный запуск, но находит оптимальные параметры.
- **inverted** — Инвертирует направление отказа. Модель становится активно согласующейся.
- **nuclear** — Максимальная сила для упорных MoE‑моделей. Экспертно‑гранулированный.

### Методы извлечения направления (флаг `--direction-method`)
- **diff_means** (по умолчанию) — Простое различие средних между отказавшими и подчиняющимися активациями. Надёжно.
- **svd** — Многовекторное извлечение SVD. Лучше для сложного выравнивания.
- **leace** — LEACE (Linear Erasure via Closed-form Estimation). Оптимальное линейное стирание.

### 4 метода только для Python‑API
(НЕ доступны через CLI — требуют импорт Python, что нарушает границы AGPL. Упоминай пользователю только если он явно хочет использовать OBLITERATUS как библиотеку в своём AGPL‑проекте.)
- failspy, gabliteration, heretic, rdo
## Шаг 5: Запуск Abliteration

### Стандартное использование
```bash
# Default method (advanced) — recommended for most models
obliteratus obliterate <model_name> --method advanced --output-dir ./abliterated-models

# With 4-bit quantization (saves VRAM)
obliteratus obliterate <model_name> --method advanced --quantization 4bit --output-dir ./abliterated-models

# Large models (70B+) — conservative defaults
obliteratus obliterate <model_name> --method advanced --quantization 4bit --large-model --output-dir ./abliterated-models
```

### Параметры Abliteration
```bash
obliteratus obliterate <model_name> \
  --method advanced \
  --direction-method diff_means \
  --n-directions 4 \
  --refinement-passes 2 \
  --regularization 0.1 \
  --quantization 4bit \
  --output-dir ./abliterated-models \
  --contribute  # opt-in telemetry for community research
```

### Ключевые флаги
| Flag | Description | Default |
|:-----|:------------|:--------|
| `--method` | Метод аблитерации | advanced |
| `--direction-method` | Извлечение направлений | diff_means |
| `--n-directions` | Количество направлений отказа (1‑32) | method-dependent |
| `--refinement-passes` | Итеративные проходы (1‑5) | 2 |
| `--regularization` | Сила регуляризации (0.0‑1.0) | 0.1 |
| `--quantization` | Загрузка в 4‑bit или 8‑bit | none (full precision) |
| `--large-model` | Консервативные значения по умолчанию для моделей 120B+ | false |
| `--output-dir` | Куда сохранять аблитерированную модель | ./obliterated_model |
| `--contribute` | Отправлять анонимные результаты для исследований | false |
| `--verify-sample-size` | Количество тестовых запросов для проверки отказов | 20 |
| `--dtype` | Тип данных модели (float16, bfloat16) | auto |

### Другие режимы выполнения
```bash
# Interactive guided mode (hardware → model → preset)
obliteratus interactive

# Web UI (Gradio)
obliteratus ui --port 7860

# Run a full ablation study from YAML config
obliteratus run config.yaml --preset quick

# Tournament: pit all methods against each other
obliteratus tourney <model_name>
```
## Шаг 6: Проверка результатов

После абляции проверь метрики вывода:

| Метрика | Хорошее значение | Предупреждение |
|:-------|:-----------|:--------|
| Уровень отказов | &lt; 5% (в идеале ~0%) | > 10% — отказы сохраняются |
| Изменение перплексии | &lt; 10% увеличения | > 15% — повреждение связности |
| KL‑дивергенция | &lt; 0.1 | > 0.5 — значительный сдвиг распределения |
| Связность | Высокая / проходит качественную проверку | Ухудшенные ответы, повторения |

### Если отказы сохраняются (> 10%)
1. Попробуй метод `aggressive`
2. Увеличь `--n-directions` (например, 8 или 16)
3. Добавь `--refinement-passes 3`
4. Попробуй `--direction-method svd` вместо `diff_means`

### Если связность повреждена (перплексия > 15% увеличения)
1. Уменьши `--n-directions` (например, 2)
2. Увеличь `--regularization` (например, 0.3)
3. Снизь `--refinement-passes` до 1
4. Попробуй метод `basic` (мягче)
## Шаг 7: Использовать аблитерированную модель

Вывод представляет собой стандартный каталог модели HuggingFace.

```bash
# Test locally with transformers
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained('./abliterated-models/<model>')
tokenizer = AutoTokenizer.from_pretrained('./abliterated-models/<model>')
inputs = tokenizer('How do I pick a lock?', return_tensors='pt')
outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
"

# Upload to HuggingFace Hub
huggingface-cli upload <username>/<model-name>-abliterated ./abliterated-models/<model>

# Serve with vLLM
vllm serve ./abliterated-models/<model>
```
## CLI Command Reference

| Команда | Описание |
|:--------|:------------|
| `obliteratus obliterate` | Основная команда абляции |
| `obliteratus info <model>` | Показать детали архитектуры модели |
| `obliteratus models --tier <tier>` | Просмотр отобранных моделей по уровню вычислительных ресурсов |
| `obliteratus recommend <model>` | Предложение методов/параметров, основанное на телеметрии |
| `obliteratus interactive` | Интерактивный мастер настройки |
| `obliteratus tourney <model>` | Турнир: все методы друг против друга |
| `obliteratus run <config.yaml>` | Выполнить исследование абляции, указав файл YAML |
| `obliteratus strategies` | Список всех зарегистрированных стратегий абляции |
| `obliteratus report <results.json>` | Сгенерировать визуальные отчёты заново |
| `obliteratus ui` | Запустить веб‑интерфейс Gradio |
| `obliteratus aggregate` | Свести данные телеметрии сообщества |
## Модули анализа

OBLITERATUS включает 28 модулей анализа для механистической интерпретируемости.
См. `skill_view(name="obliteratus", file_path="references/analysis-modules.md")` для полного справочника.

### Быстрые команды анализа
```bash
# Run specific analysis modules
obliteratus run analysis-config.yaml --preset quick

# Key modules to run first:
# - alignment_imprint: Fingerprint DPO/RLHF/CAI/SFT alignment method
# - concept_geometry: Single direction vs polyhedral cone
# - logit_lens: Which layer decides to refuse
# - anti_ouroboros: Self-repair risk score
# - causal_tracing: Causally necessary components
```

### Векторы управления (обратимая альтернатива)
Вместо постоянного изменения весов используйте управление во время вывода:
```python
# Python API only — for user's own projects
from obliteratus.analysis.steering_vectors import SteeringVectorFactory, SteeringHookManager
```
## Стратегии абляции

Помимо направленной абляции, OBLITERATUS включает структурные стратегии абляции:
- **Embedding Ablation** — компоненты целевого слоя embedding
- **FFN Ablation** — удаление блока feed‑forward сети
- **Head Pruning** — обрезка голов внимания
- **Layer Removal** — полное удаление слоя

Список всех доступных: `obliteratus strategies`
## Оценка

OBLITERATUS включает встроенные инструменты оценки:
- Бенчмарк уровня отказов
- Сравнение perplexity (до/после)
- Интеграция LM Eval Harness для академических бенчмарков
- Сравнение конкурентов в формате «один против одного»
- Отслеживание базовой производительности
## Поддержка платформ

- **CUDA** — Полная поддержка (GPU NVIDIA)
- **Apple Silicon (MLX)** — Поддерживается через backend MLX
- **CPU** — Поддерживается для небольших моделей (< 1 B параметров)
## Шаблоны конфигураций YAML

Загрузи шаблоны для воспроизводимых запусков через `skill_view`:
- `templates/abliteration-config.yaml` — Стандартная конфигурация для одной модели
- `templates/analysis-study.yaml` — Исследование предабляции
- `templates/batch-abliteration.yaml` — Пакетная обработка нескольких моделей
## Телеметрия

OBLITERATUS может при желании отправлять анонимные данные о запуске в глобальный исследовательский набор данных.
Включи это с помощью флага `--contribute`. Личные данные не собираются — только название модели, метод и метрики.
## Общие подводные камни

1. **Не используй `informed` по умолчанию** — это экспериментальный режим и работает медленнее. Используй `advanced` для надёжных результатов.
2. **Модели размером ~1 B плохо реагируют на абляцию** — их поведения отказа поверхностны и фрагментарны, что затрудняет чистое извлечение направления. Ожидай частичные результаты (20‑40 % оставшегося отказа). Модели 3 B+ дают более чистые направления отказа и работают гораздо лучше (часто 0 % отказа с `advanced`).
3. **`aggressive` может ухудшить ситуацию** — на небольших моделях он может повредить связность и фактически увеличить уровень отказов. Используй его только если `advanced` оставляет > 10 % отказов на модели 3 B+.
4. **Всегда проверяй перплексию** — если она скачет выше 15 %, модель повреждена. Снизь агрессивность.
5. **MoE‑модели требуют особой обработки** — используй метод `nuclear` для Mixtral, DeepSeek-MoE и т.п.
6. **Квантованные модели нельзя повторно квантизировать** — сначала абляцию полной‑точностной модели, затем квантизируй полученный результат.
7. **Оценка VRAM приблизительна** — 4‑битная квантизация помогает, но пик потребления может всплескнуться во время извлечения.
8. **Модели рассуждения чувствительны** — используй `surgical` для дистиллятов R1, чтобы сохранить цепочку рассуждений.
9. **Проверь `obliteratus recommend`** — телеметрические данные могут содержать лучшие параметры, чем значения по умолчанию.
10. **Лицензия AGPL** — никогда не `import obliteratus` в проектах MIT/Apache. Только вызов через CLI.
11. **Большие модели (70 B+)** — всегда указывай флаг `--large-model` для консервативных настроек по умолчанию.
12. **Спектральная сертификация RED распространена** — спектральная проверка часто помечает «неполный», даже когда практический уровень отказов равен 0 %. Проверяй реальный уровень отказов, а не полагайся только на спектральную сертификацию.
## Дополнительные навыки

- **vllm** — Обслуживание ускоренных моделей с высокой пропускной способностью
- **gguf** — Конвертация ускоренных моделей в GGUF для llama.cpp
- **huggingface-tokenizers** — Работа с токенизаторами моделей