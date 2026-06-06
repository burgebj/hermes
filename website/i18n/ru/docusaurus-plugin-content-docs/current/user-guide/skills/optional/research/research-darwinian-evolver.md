---
title: "Darwinian Evolver — Эволюция подсказок/regex/SQL/кода с помощью цикла обучения Imbue's evolution loop"
sidebar_label: "Darwinian Evolver"
description: "Развивай подсказки/регекс/SQL/код с помощью цикла обучения Imbue"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Дарвиновский эволвер

Эволюционируй подсказки/регулярные выражения/SQL/код с помощью цикла эволюции Imbue.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/research/darwinian-evolver` |
| Path | `optional-skills/research/darwinian-evolver` |
| Version | `0.1.0` |
| Author | Bihruze (Asahi0x), Hermes Agent |
| License | MIT |
| Platforms | linux, macos |
| Tags | `evolution`, `optimization`, `prompt-engineering`, `research` |
| Related skills | [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv), [`jupyter-live-kernel`](/docs/user-guide/skills/bundled/data-science/data-science-jupyter-live-kernel) |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Дарвиновский эволвер

Запусти [darwinian_evolver](https://github.com/imbue-ai/darwinian_evolver) от Imbue —
LLM‑управляемый эволюционный поисковый цикл — чтобы оптимизировать **подсказку, регулярное выражение, SQL‑запрос или небольшой фрагмент кода** по функции приспособленности.

Статус: тонкая оболочка вокруг оригинального инструмента. Навык устанавливает его, проводит агента через написание определения `Problem` (организм + оценщик + мутатор) и управляет циклом через оригинальный CLI или небольшой кастомный Python‑драйвер.

**Лицензия:** оригинальный инструмент имеет **AGPL‑3.0**. Навык ТОЛЬКО вызывает его через оригинальный CLI или вызов `subprocess`/`uv run` (просто агрегация). Не делай import upstream classes into Hermes itself.

## Когда использовать

- Пользователь говорит «оптимизировать эту подсказку», «эволюционировать регулярное выражение для X», «авто‑улучшить этот код/SQL», «найти лучшую инструкцию».
- У тебя есть оценщик (точное совпадение, процент прохождения regex, юнит‑тест, LLM‑жюри, метрика времени) **и** начальный кандидат (организм). Если оценщика нет, остановись и сначала создай его — это самая сложная часть.
- Стоимость приемлема: типичный запуск требует 50–500 вызовов LLM. На gpt‑4o‑mini это копейки; на Claude Sonnet — несколько долларов.

**Не используй**, если:
- Целевая функция дифференцируема (используй градиентный спуск / DSPy).
- Нужно попробовать только 2–3 варианта — просто напиши их вручную.
- Сигнал приспособленности полностью субъективен и нет измеримого критерия.

## Предварительные требования

- Python ≥ 3.11
- `git`, `uv` (или `pip`)
- Один из: `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY` или `OPENAI_API_KEY`

Навык поставляется с небольшим драйвером `parrot_openrouter.py`, который использует `OPENROUTER_API_KEY` через SDK OpenAI, поэтому любая модель на OpenRouter работает. Сам CLI жёстко привязан к Anthropic и требует `ANTHROPIC_API_KEY`.

## Установка (однократная)

Запусти через инструмент `terminal`:

```bash
mkdir -p ~/.hermes/cache/darwinian-evolver && cd ~/.hermes/cache/darwinian-evolver
[ -d darwinian_evolver ] || git clone --depth 1 https://github.com/imbue-ai/darwinian_evolver.git
cd darwinian_evolver && uv sync
```

Проверь:

```bash
cd ~/.hermes/cache/darwinian-evolver/darwinian_evolver \
  && uv run darwinian_evolver --help | head -5
```

## Быстрый старт — встроенный пример Parrot

Краткий smoke‑test (требуется `ANTHROPIC_API_KEY`):

```bash
cd ~/.hermes/cache/darwinian-evolver/darwinian_evolver
uv run darwinian_evolver parrot \
  --num_iterations 2 \
  --num_parents_per_iteration 2 \
  --mutator_concurrency 2 --evaluator_concurrency 2 \
  --output_dir /tmp/parrot_demo
```

Выводы:
- `/tmp/parrot_demo/snapshots/iteration_N.pkl` — pickled‑популяция за итерацию
- `/tmp/parrot_demo/<jsonl>` — JSON‑лог за итерацию (путь выводится в конце)

Открой `~/.hermes/cache/darwinian-evolver/darwinian_evolver/darwinian_evolver/lineage_visualizer.html` в браузере и загрузите JSON‑лог, чтобы увидеть эволюционное дерево.

## Быстрый старт — драйвер OpenRouter (без ключа Anthropic)

Навык поставляет `scripts/parrot_openrouter.py` — тот же parrot‑проблема, но вызов LLM идёт через OpenRouter, поэтому любой провайдер подходит.

```bash
# From wherever the skill is installed:
SKILL_DIR=~/.hermes/skills/research/darwinian-evolver
DE_DIR=~/.hermes/cache/darwinian-evolver/darwinian_evolver

cd "$DE_DIR" && \
  EVOLVER_MODEL='openai/gpt-4o-mini' \
  uv run --with openai python "$SKILL_DIR/scripts/parrot_openrouter.py" \
    --num_iterations 3 --num_parents_per_iteration 2 \
    --output_dir /tmp/parrot_or
```

Посмотри результат с помощью `scripts/show_snapshot.py`:

```bash
uv run --with openai python "$SKILL_DIR/scripts/show_snapshot.py" \
  /tmp/parrot_or/snapshots/iteration_3.pkl
```

Ожидаемый вывод: 7 эволюционировавших шаблонов подсказок, ранжированных по оценке, лучший — около 0.6–0.8 (начальный `Say {{ phrase }}` получил 0.000).

## Определение кастомной задачи

Навык поставляет `templates/custom_problem_template.py` — скопируй, отредактируй, запусти. Нужно определить три вещи:

1. **`Organism`** — подкласс Pydantic `BaseModel`, хранящий артефакт, который эволюционирует (`prompt_template: str`, `regex_pattern: str`, `sql_query: str`, `code_block: str` и т.д.). Добавь метод `run(*args)`, который его использует.

2. **`Evaluator`** — `.evaluate(organism) -> EvaluationResult(score=..., trainable_failure_cases=[...], holdout_failure_cases=[...], is_viable=True)`.
   - **`score`** в диапазоне `[0, 1]`. Чем выше, тем лучше.
   - **`trainable_failure_cases`** — то, что видит мутатор. Включи достаточно контекста (вход, ожидаемый результат, фактический) для диагностики LLM.
   - **`holdout_failure_cases`** — скрыты от мутатора. Используй их для обнаружения переобучения.
   - **`is_viable=True`**, если организм не полностью сломан (не бросает исключения, не возвращает `None` и т.п.). Организм с нулевой оценкой допускается — он просто будет иметь меньший вес при выборе родителей.

3. **`Mutator`** — `.mutate(organism, failure_cases, learning_log_entries) -> list[Organism]`.
   Обычно: сформировать LLM‑подсказку, включающую текущий организм + случай неудачи + запрос предложить исправление; распарсить ответ LLM; вернуть новый `Organism`. При ошибке парсинга верни `[]` — цикл обработает это.

Затем напиши драйвер‑скрипт, который передаёт `Problem(initial_organism, evaluator, [mutators])` в `EvolveProblemLoop` и итерирует `loop.run(num_iterations=N)` — в качестве примера смотри `scripts/parrot_openrouter.py`.

## Гиперпараметры, которые действительно важны

| flag | default | когда менять |
|---|---|---|
| `--num_iterations` | 5 | увеличь до 10–20, когда доверяешь оценщику |
| `--num_parents_per_iteration` | 4 | снизь до 2 для дешёвой разведки |
| `--mutator_concurrency` | 10 | снизь до 2–4, чтобы избежать ограничений скорости |
| `--evaluator_concurrency` | 10 | то же; оценщик тоже делает запросы к LLM |
| `--batch_size` | 1 | увеличь до 3–5, когда мутатор умеет обрабатывать несколько неудач |
| `--verify_mutations` | off | включи, когда мутатор тратит слишком много ресурсов (>10× экономии на последующих запусках по данным Imbue) |
| `--midpoint_score` | `p75` | оставь как есть, если только оценки не кластеризуются |
| `--sharpness` | 10 | оставь как есть |

## Подводные камни

1. **`Initial organism must be viable`** — ставь `is_viable=True` в `EvaluationResult` даже для начального организма с нулевым баллом. Цикл отбрасывает не‑жизнеспособные организмы, потому что тогда нечего эволюционировать.
2. **Фильтры контента провайдера убивают запуски.** Модели OpenRouter на Azure отклоняют фразы вроде «ignore previous instructions» с HTTP 400. Оберни вызов LLM в `try/except` и верни `f"<LLM_ERROR: {e}>"` — эволвер просто даст этому организму 0 и продолжит.
3. **`loop.run()` — генератор** — вызов ничего не делает, пока не начнёшь итерировать. Используй `for snap in loop.run(num_iterations=N):`.
4. **Снимки — вложенные pickle‑файлы.** `iteration_N.pkl` содержит dict с `population_snapshot` (дальше pickled‑байты). Чтобы распаковать, класс `Organism` должен быть импортируем по тому же dotted‑пути, под которым он был запакован.
5. **Настройки конкурентности агрессивны.** 10/10 быстро достигнут лимитов большинства провайдеров. Начинай с 2/2.
6. **CLI жёстко привязан к Anthropic.** `uv run darwinian_evolver <problem>` ищет `ANTHROPIC_API_KEY` и использует Claude Sonnet. Чтобы работать с другим провайдером, напиши драйвер вроде `parrot_openrouter.py`.
7. **AGPL.** Никогда не делай `from darwinian_evolver import ...` внутри ядра Hermes. Пользовательские драйверы в `~/.hermes/skills/...` находятся на стороне пользователя и допустимы.
8. **Нет пакета PyPI.** `pip install darwinian-evolver` установит не то. Всегда ставь из репозитория GitHub.

## Проверка

После установки + пробного запуска parrot, код возврата 0 считается достаточным:

```bash
DE_DIR=~/.hermes/cache/darwinian-evolver/darwinian_evolver
ls "$DE_DIR/darwinian_evolver/lineage_visualizer.html" >/dev/null && \
cd "$DE_DIR" && uv run darwinian_evolver --help >/dev/null && \
echo "darwinian-evolver: OK"
```

## Ссылки

- [Imbue research post](https://imbue.com/research/2026-02-27-darwinian-evolver/)
- [ARC-AGI-2 results](https://imbue.com/research/2026-02-27-arc-agi-2-evolution/)
- [imbue-ai/darwinian_evolver](https://github.com/imbue-ai/darwinian_evolver) (AGPL‑3.0)
- [Darwin Gödel Machines](https://arxiv.org/abs/2505.22954)
- [PromptBreeder](https://arxiv.org/abs/2309.16797)