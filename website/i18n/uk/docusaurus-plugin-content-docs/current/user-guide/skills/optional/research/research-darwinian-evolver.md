---
title: "Darwinian Evolver — Еволюціонуй підказки/regex/SQL/код за допомогою циклу еволюції Imbue's."
sidebar_label: "Darwinian Evolver"
description: "Розвивай підказки/regex/SQL/код за допомогою циклу навчання Imbue's."
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Дарвінівський еволвер

Еволюція підказок/regex/SQL/коду за допомогою циклу еволюції Imbue.

## Метадані навички

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

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Дарвінівський еволвер

Запусти [darwinian_evolver](https://github.com/imbue-ai/darwinian_evolver) від Imbue — LLM‑керований еволюційний пошуковий цикл — щоб оптимізувати **підказку, regex, SQL‑запит або невеликий фрагмент коду** за функцією придатності.

Статус: тонка обгортка навколо upstream‑інструменту. Навичка встановлює його, проводить агента через написання визначення `Problem` (організм + оцінювач + мутатор) і керує циклом через upstream‑CLI або невеликий кастомний Python‑драйвер.

**License:** upstream‑інструмент має **AGPL‑3.0**. Навичка ТІЛЬКИ викликає його через upstream‑CLI або виклик `subprocess`/`uv run` (проста агрегація). Не роби
import upstream classes into Hermes itself.

## Коли використовувати

- Користувач каже «оптимізуй цю підказку», «еволюціонуй regex для X», «авто‑покращи цей код/SQL», «знайди кращу інструкцію».
- У тебе є скорер (точний збіг, проходження regex, юніт‑тест, LLM‑judge, метрика часу) **і** стартовий кандидат (організм). Якщо скорера немає, спочатку його визначи — це складна частина.
- Вартість прийнятна: типова сесія — 50–500 викликів LLM. На gpt‑4o‑mini це копійки; на Claude Sonnet може коштувати кілька доларів.

Не використовуйте, коли:
- Ціль оптимізації диференційована (використовуй градієнтний спуск / DSPy).
- Потрібно лише 2–3 варіанти — просто напиши їх вручну.
- Сигнал придатності суто суб’єктивний без вимірюваного критерію.

## Передумови

- Python ≥ 3.11
- `git`, `uv` (або `pip`)
- Один із: `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY` або `OPENAI_API_KEY`

Навичка постачає невеликий драйвер `parrot_openrouter.py`, який використовує `OPENROUTER_API_KEY` через OpenAI SDK, тому будь‑яка модель на OpenRouter працює. Сам CLI жорстко прив’язаний до Anthropic і потребує `ANTHROPIC_API_KEY`.

## Встановлення (одноразове)

Запусти через інструмент `terminal`:

```bash
mkdir -p ~/.hermes/cache/darwinian-evolver && cd ~/.hermes/cache/darwinian-evolver
[ -d darwinian_evolver ] || git clone --depth 1 https://github.com/imbue-ai/darwinian_evolver.git
cd darwinian_evolver && uv sync
```

Перевірка:

```bash
cd ~/.hermes/cache/darwinian-evolver/darwinian_evolver \
  && uv run darwinian_evolver --help | head -5
```

## Швидкий старт — вбудований приклад Parrot

Малий smoke‑test (потрібен `ANTHROPIC_API_KEY`):

```bash
cd ~/.hermes/cache/darwinian-evolver/darwinian_evolver
uv run darwinian_evolver parrot \
  --num_iterations 2 \
  --num_parents_per_iteration 2 \
  --mutator_concurrency 2 --evaluator_concurrency 2 \
  --output_dir /tmp/parrot_demo
```

Вивід:
- `/tmp/parrot_demo/snapshots/iteration_N.pkl` — pickle‑популяція за ітерацію
- `/tmp/parrot_demo/<jsonl>` — JSON‑лог за ітерацію (шлях виводиться в кінці)

Відкрий `~/.hermes/cache/darwinian-evolver/darwinian_evolver/darwinian_evolver/lineage_visualizer.html` у браузері і завантаж JSON‑лог, щоб побачити еволюційне дерево.

## Швидкий старт — драйвер OpenRouter (без ключа Anthropic)

Навичка постачає `scripts/parrot_openrouter.py` — той самий parrot‑проект, але виклик LLM проходить через OpenRouter, тому підходить будь‑який провайдер.

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

Переглянь результат за допомогою `scripts/show_snapshot.py`:

```bash
uv run --with openai python "$SKILL_DIR/scripts/show_snapshot.py" \
  /tmp/parrot_or/snapshots/iteration_3.pkl
```

Очікуваний вивід: 7 еволюційних шаблонів підказок, ранжованих за балом; найкращий розташовується в діапазоні 0.6–0.8 (насіння `Say {{ phrase }}` отримало 0.000).

## Визначення кастомної проблеми

Навичка постачає `templates/custom_problem_template.py` — скопіюй, відредагуй, запусти. Три речі, які треба визначити:

1. **`Organism`** — підклас Pydantic `BaseModel`, що містить артефакт, який еволюціонує (`prompt_template: str`, `regex_pattern: str`, `sql_query: str`, `code_block: str` тощо). Додай метод `run(*args)`, який його виконує.

2. **`Evaluator`** — `.evaluate(organism) -> EvaluationResult(score=..., trainable_failure_cases=[...], holdout_failure_cases=[...], is_viable=True)`.
   - **`score`** у діапазоні `[0, 1]`. Вище — краще.
   - **`trainable_failure_cases`** — те, що бачить мутатор. Додай достатньо контексту (вхід, очікуване, фактичне) для діагностики LLM.
   - **`holdout_failure_cases`** — приховані від мутатора. Використовуй їх для виявлення переобучення.
   - **`is_viable=True`** якщо організм не зламаний (не піднімає виключення, не повертає `None` тощо). Організм з 0‑балом теж підходить — його просто зменшують у ваговому відборі батьків.

3. **`Mutator`** — `.mutate(organism, failure_cases, learning_log_entries) -> list[Organism]`.
   Зазвичай: формуєш LLM‑підказку, що включає поточний організм + випадок помилки + запит на пропозицію виправлення; парсиш відповідь LLM; повертаєш новий `Organism`. Поверни `[]` при помилці парсингу — цикл це обробить.

Потім напиши драйвер‑скрипт, який підключає `Problem(initial_organism, evaluator, [mutators])` до `EvolveProblemLoop` і ітерує `loop.run(num_iterations=N)`. Референсом є `scripts/parrot_openrouter.py`.

## Гіперпараметри, які дійсно мають значення

| flag | default | коли змінювати |
|---|---|---|
| `--num_iterations` | 5 | підвищити до 10–20, коли оцінювач довірений |
| `--num_parents_per_iteration` | 4 | зменшити до 2 для дешевого дослідження |
| `--mutator_concurrency` | 10 | зменшити до 2–4, щоб уникнути лімітів |
| `--evaluator_concurrency` | 10 | те саме; оцінювач теж навантажує LLM |
| `--batch_size` | 1 | підняти до 3–5, коли мутатор обробляє кілька помилок |
| `--verify_mutations` | off | увімкнути, коли мутатор витрачає зайві ресурси (>10× економії на пізніших запусках за Imbue) |
| `--midpoint_score` | `p75` | залишити, якщо лише балами не скупчуються |
| `--sharpness` | 10 | залишити |

## Підводні камені

1. **`Initial organism must be viable`** — встанови `is_viable=True` у своєму `EvaluationResult` навіть для 0‑балового насіння. Цикл відхиляє не‑життєздатні організми, бо без них немає чого еволюціонувати.
2. **Фільтри провайдера вбивають запуски.** Моделі OpenRouter на Azure відхиляють фрази типу «ignore previous instructions» з HTTP 400. Обгорни виклик LLM у `try/except` і поверни `f"<LLM_ERROR: {e}>"` — еволвер просто поставить 0 і продовжить.
3. **`loop.run()` — генератор** — виклик сам по собі нічого не робить, доки не ітеруєш. Використовуй `for snap in loop.run(num_iterations=N):`.
4. **Снапшоти — вкладені pickle‑файли.** `iteration_N.pkl` містить dict з `population_snapshot` (ще один pickle‑байт). Для розпакування потрібен клас `Organism`, імпортований за тим же dotted‑шляхом, що був під час серіалізації.
5. **Конкурентність за замовчуванням агресивна.** 10/10 швидко вдарить ліміти у більшості провайдерів. Починай з 2/2.
6. **CLI жорстко прив’язаний до Anthropic.** `uv run darwinian_evolver <problem>` шукає `ANTHROPIC_API_KEY` і використовує Claude Sonnet. Щоб працювати з іншим провайдером, напиши драйвер типу `parrot_openrouter.py`.
7. **AGPL.** Ніколи не імпортуй `from darwinian_evolver import ...` у ядро Hermes. Кастомні драйвери в `~/.hermes/skills/...` — це користувацька сторона і дозволено.
8. **Немає PyPI‑пакету.** `pip install darwinian-evolver` встановить інший пакет. Завжди інсталюй з репозиторію GitHub.

## Верифікація

Після встановлення + запуску parrot, код виходу 0 вважається достатнім:

```bash
DE_DIR=~/.hermes/cache/darwinian-evolver/darwinian_evolver
ls "$DE_DIR/darwinian_evolver/lineage_visualizer.html" >/dev/null && \
cd "$DE_DIR" && uv run darwinian_evolver --help >/dev/null && \
echo "darwinian-evolver: OK"
```

## Посилання

- [Imbue research post](https://imbue.com/research/2026-02-27-darwinian-evolver/)
- [ARC-AGI-2 results](https://imbue.com/research/2026-02-27-arc-agi-2-evolution/)
- [imbue-ai/darwinian_evolver](https://github.com/imbue-ai/darwinian_evolver) (AGPL-3.0)
- [Darwin Gödel Machines](https://arxiv.org/abs/2505.22954)
- [PromptBreeder](https://arxiv.org/abs/2309.16797)