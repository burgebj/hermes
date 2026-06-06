---
title: "Написание исследовательских статей — Пиши ML‑статьи для NeurIPS/ICML/ICLR: design→submit"
sidebar_label: "Research Paper Writing"
description: "Пиши ML‑статьи для NeurIPS/ICML/ICLR: дизайн→подача"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Написание исследовательских статей

Пиши ML‑статьи для NeurIPS/ICML/ICLR: от разработки до подачи.
## Метаданные навыка

| | |
|---|---|
| Источник | Bundled (installed by default) |
| Путь | `skills/research/research-paper-writing` |
| Версия | `1.1.0` |
| Автор | Orchestra Research |
| Лицензия | MIT |
| Зависимости | `semanticscholar`, `arxiv`, `habanero`, `requests`, `scipy`, `numpy`, `matplotlib`, `SciencePlots` |
| Платформы | linux, macos |
| Теги | `Research`, `Paper Writing`, `Experiments`, `ML`, `AI`, `NeurIPS`, `ICML`, `ICLR`, `ACL`, `AAAI`, `COLM`, `LaTeX`, `Citations`, `Statistical Analysis` |
| Связанные навыки | [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv), `ml-paper-writing`, [`subagent-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-subagent-driven-development), [`plan`](/docs/user-guide/skills/bundled/software-development/software-development-plan) |
:::info
Следующее — полное определение навыка, которое Hermes загружает, когда этот навык активируется. Это то, что агент видит как инструкции, когда навык активен.
:::

# Конвейер написания исследовательской статьи

Сквозной конвейер для создания готовых к публикации статей по машинному обучению/искусственному интеллекту, ориентированных на **NeurIPS, ICML, ICLR, ACL, AAAI и COLM**. Этот навык охватывает весь жизненный цикл исследования: проектирование эксперимента, выполнение, мониторинг, анализ, написание статьи, рецензирование, исправление и подачу.

Это **не линейный конвейер** — это итеративный цикл. Результаты вызывают новые эксперименты. Рецензии вызывают новый анализ. Агент должен обрабатывать эти циклы обратной связи.

<!-- ascii-guard-ignore -->
<!-- ascii-guard-ignore -->
```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH PAPER PIPELINE                  │
│                                                             │
│  Phase 0: Project Setup ──► Phase 1: Literature Review      │
│       │                          │                          │
│       ▼                          ▼                          │
│  Phase 2: Experiment     Phase 5: Paper Drafting ◄──┐      │
│       Design                     │                   │      │
│       │                          ▼                   │      │
│       ▼                    Phase 6: Self-Review      │      │
│  Phase 3: Execution &           & Revision ──────────┘      │
│       Monitoring                 │                          │
│       │                          ▼                          │
│       ▼                    Phase 7: Submission               │
│  Phase 4: Analysis ─────► (feeds back to Phase 2 or 5)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```
<!-- ascii-guard-ignore-end -->
<!-- ascii-guard-ignore-end -->

---
## Когда использовать этот навык

Используй этот навык, когда:
- **Начинаешь новую исследовательскую статью** на основе существующей кодовой базы или идеи
- **Разрабатываешь и проводишь эксперименты** для подтверждения заявлений статьи
- **Пишешь или редактируешь** любой раздел исследовательской статьи
- **Готовишься к подаче** в конкретную конференцию или воркшоп
- **Отвечаешь на рецензии** с дополнительными экспериментами или правками
- **Конвертируешь** статью между форматами конференций
- **Пишешь неэмпирические статьи** — теоретические, обзорные, бенчмарк‑ или позиционные (см. [Paper Types Beyond Empirical ML](#paper-types-beyond-empirical-ml))
- **Разрабатываешь человеческие оценки** для исследований в области NLP, HCI или alignment
- **Готовишь постприёмные материалы** — постеры, доклады, релизы кода
## Основная философия

1. **Будь проактивным.** Предоставляй готовые черновики, а не вопросы. Учёные заняты — создай что‑то конкретное, на что они могут отреагировать, а затем дорабатывай.
2. **Никогда не выдумывай ссылки.** У AI‑сгенерированных ссылок ошибка около 40 %. Всегда получай их программно. Помечай непроверяемые ссылки как `[CITATION NEEDED]`.
3. **Статья — это история, а не набор экспериментов.** Каждая статья должна иметь один чёткий вклад, сформулированный в одном предложении. Если не можешь этого сделать, статья ещё не готова.
4. **Эксперименты служат утверждениям.** Каждый эксперимент обязан явно указывать, какое утверждение он поддерживает. Никогда не проводи эксперименты, не связанные с повествованием статьи.
5. **Коммить часто и рано.** Каждый завершённый набор экспериментов, каждое обновление черновика — делай commit с описательными сообщениями. Журнал Git — это история экспериментов.

### Проактивность и сотрудничество

**По умолчанию: будь проактивным. Сначала черновик, потом вопрос к черновику.**

| Уровень уверенности | Действие |
|----------------------|----------|
| **Высокий** (чёткий репозиторий, очевидный вклад) | Написать полный черновик, доставить, доработать по обратной связи |
| **Средний** (некоторая неоднозначность) | Написать черновик с пометками о неопределённостях, продолжать |
| **Низкий** (существенные неизвестные) | Задать 1‑2 целевых вопроса через `clarify`, затем написать черновик |

| Section | Draft Autonomously? | Flag With Draft |
|---------|---------------------|-----------------|
| Abstract | Yes | «Вклад сформулирован как X — при необходимости скорректировать» |
| Introduction | Yes | «Подчёркнута проблема Y — исправить, если неверно» |
| Methods | Yes | «Включены детали A, B, C — добавить недостающие части» |
| Experiments | Yes | «Выделены результаты 1, 2, 3 — при необходимости переупорядочить» |
| Related Work | Yes | «Цитированы работы X, Y, Z — добавить любые пропущенные» |

**Блокировать ввод только когда**: целевое издание неясно, есть несколько противоречивых формулировок, результаты выглядят неполными, явный запрос сначала просмотреть.
## Phase 0: Настройка проекта

**Goal**: Создать рабочее пространство, понять существующую работу, определить вклад.

### Step 0.1: Исследование репозитория

```bash
# Understand project structure
ls -la
find . -name "*.py" | head -30
find . -name "*.md" -o -name "*.txt" | xargs grep -l -i "result\|conclusion\|finding"
```

Ищи:
- `README.md` — обзор проекта и основные утверждения
- `results/`, `outputs/`, `experiments/` — существующие результаты
- `configs/` — настройки экспериментов
- `.bib` файлы — существующие ссылки
- Черновики документов или заметки

### Step 0.2: Организация рабочего пространства

Установи единообразную структуру рабочего пространства:

```
workspace/
  paper/               # LaTeX source, figures, compiled PDFs
  experiments/         # Experiment runner scripts
  code/                # Core method implementation
  results/             # Raw experiment results (auto-generated)
  tasks/               # Task/benchmark definitions
  human_eval/          # Human evaluation materials (if needed)
```

### Step 0.3: Настройка системы контроля версий

```bash
git init  # if not already
git remote add origin <repo-url>
git checkout -b paper-draft  # or main
```

**Git discipline**: Каждый завершённый пакет экспериментов коммитится с описательным сообщением. Пример:
```
Add Monte Carlo constrained results (5 runs, Sonnet 4.6, policy memo task)
Add Haiku baseline comparison: autoreason vs refinement baselines at cheap model tier
```

### Step 0.4: Определение вклада

Прежде чем писать, сформулируй:
- **The What**: Что именно вносит эта статья?
- **The Why**: Какие доказательства это подтверждают?
- **The So What**: Почему это важно для читателей?

> Предложи учёному: «Исходя из моего понимания, основной вклад состоит в: [одно предложение]. Ключевые результаты показывают [Y]. Это та формулировка, которую ты хочешь?»

### Step 0.5: Создание списка задач

Используй инструмент `todo` для создания структурированного плана проекта:

```
Research Paper TODO:
- [ ] Define one-sentence contribution
- [ ] Literature review (related work + baselines)
- [ ] Design core experiments
- [ ] Run experiments
- [ ] Analyze results
- [ ] Write first draft
- [ ] Self-review (simulate reviewers)
- [ ] Revise based on review
- [ ] Submission prep
```

Обновляй его на протяжении всего проекта. Он служит постоянным состоянием между сессиями.

### Step 0.6: Оценка вычислительного бюджета

Перед запуском экспериментов оцени общие затраты и время:

```
Compute Budget Checklist:
- [ ] API costs: (model price per token) × (estimated tokens per run) × (number of runs)
- [ ] GPU hours: (time per experiment) × (number of experiments) × (number of seeds)
- [ ] Human evaluation costs: (annotators) × (hours) × (hourly rate)
- [ ] Total budget ceiling and contingency (add 30-50% for reruns)
```

Отслеживай фактические расходы по мере выполнения экспериментов:
```python
# Simple cost tracker pattern
import json, os
from datetime import datetime

COST_LOG = "results/cost_log.jsonl"

def log_cost(experiment: str, model: str, input_tokens: int, output_tokens: int, cost_usd: float):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "experiment": experiment,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": cost_usd,
    }
    with open(COST_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
```

**Когда бюджет ограничен**: Запусти пилотные эксперименты (1‑2 seed, подмножество задач) перед полными прогонками. Для отладки пайплайнов используй более дешёвые модели, затем переключись на целевые модели для финальных запусков.

### Step 0.7: Координация нескольких авторов

У большинства статей 3‑10 авторов. Установи рабочие процессы заранее:

| Workflow | Tool | When to Use |
|----------|------|-------------|
| **Overleaf** | Browser-based | Несколько авторов редактируют одновременно, без опыта git |
| **Git + LaTeX** | `git` с `.gitignore` для вспомогательных файлов | Технические команды, нужна ревью по веткам |
| **Overleaf + Git sync** | Overleaf premium | Лучшее из обоих — живое совместное редактирование с историей версий |

**Ответственность за разделы**: Назначь каждому разделу одного основного автора. Остальные могут комментировать, но не редактировать напрямую. Это предотвращает конфликты слияния и несоответствие стиля.

```
Author Coordination Checklist:
- [ ] Agree on section ownership (who writes what)
- [ ] Set up shared workspace (Overleaf or git repo)
- [ ] Establish notation conventions (before anyone writes)
- [ ] Schedule internal review rounds (not just at the end)
- [ ] Designate one person for final formatting pass
- [ ] Agree on figure style (colors, fonts, sizes) before creating figures
```

**LaTeX‑конвенции, которые следует согласовать заранее**:
- макрос `\method{}` для единообразного названия методов
- стиль цитирования: использование `\citet{}` vs `\citep{}`
- математическая нотация: нижний регистр жирный для векторов, верхний регистр жирный для матриц и т.д.
- британское vs американское написание
## Phase 1: Обзор литературы

**Цель**: Найти смежные работы, определить базовые линии, собрать цитаты.

### Step 1.1: Identify Seed Papers

Start from papers already referenced in the codebase:

```bash
# Via terminal:
grep -r "arxiv\|doi\|cite" --include="*.md" --include="*.bib" --include="*.py"
find . -name "*.bib"
```

### Step 1.2: Search for Related Work

**Load the `arxiv` skill** for structured paper discovery: `skill_view("arxiv")`. It provides arXiv REST API search, Semantic Scholar citation graphs, author profiles, and BibTeX generation.

Use `web_search` for broad discovery, `web_extract` for fetching specific papers:

```
# Via web_search:
web_search("[main technique] + [application domain] site:arxiv.org")
web_search("[baseline method] comparison ICML NeurIPS 2024")

# Via web_extract (for specific papers):
web_extract("https://arxiv.org/abs/2303.17651")
```

Additional search queries to try:

```
Search queries:
- "[main technique] + [application domain]"
- "[baseline method] comparison"
- "[problem name] state-of-the-art"
- Author names from existing citations
```

**Recommended**: Install **Exa MCP** for real‑time academic search:
```bash
claude mcp add exa -- npx -y mcp-remote "https://mcp.exa.ai/mcp"
```

### Step 1.2b: Deepen the Search (Breadth‑First, Then Depth)

A flat search (one round of queries) typically misses important related work. Use an iterative **breadth‑then‑depth** pattern inspired by deep research pipelines:

```
Iterative Literature Search:

Round 1 (Breadth): 4-6 parallel queries covering different angles
  - "[method] + [domain]"
  - "[problem name] state-of-the-art 2024 2025"
  - "[baseline method] comparison"
  - "[alternative approach] vs [your approach]"
  → Collect papers, extract key concepts and terminology

Round 2 (Depth): Generate follow-up queries from Round 1 learnings
  - New terminology discovered in Round 1 papers
  - Papers cited by the most relevant Round 1 results
  - Contradictory findings that need investigation
  → Collect papers, identify remaining gaps

Round 3 (Targeted): Fill specific gaps
  - Missing baselines identified in Rounds 1-2
  - Concurrent work (last 6 months, same problem)
  - Key negative results or failed approaches
  → Stop when new queries return mostly papers you've already seen
```

**When to stop**: If a round returns > 80 % papers already in your collection, the search is saturated. Typically 2‑3 rounds suffice. For survey papers, expect 4‑5 rounds.

**For agent‑based workflows**: Delegate each round's queries in parallel via `delegate_task`. Collect results, deduplicate, then generate the next round's queries from the combined learnings.

### Step 1.3: Verify Every Citation

**NEVER generate BibTeX from memory. ALWAYS fetch programmatically.**

For each citation, follow the mandatory 5‑step process:

```
Citation Verification (MANDATORY per citation):
1. SEARCH → Query Semantic Scholar or Exa MCP with specific keywords
2. VERIFY → Confirm paper exists in 2+ sources (Semantic Scholar + arXiv/CrossRef)
3. RETRIEVE → Get BibTeX via DOI content negotiation (programmatically, not from memory)
4. VALIDATE → Confirm the claim you're citing actually appears in the paper
5. ADD → Add verified BibTeX to bibliography
If ANY step fails → mark as [CITATION NEEDED], inform scientist
```

```python
# Fetch BibTeX via DOI
import requests

def doi_to_bibtex(doi: str) -> str:
    response = requests.get(
        f"https://doi.org/{doi}",
        headers={"Accept": "application/x-bibtex"}
    )
    response.raise_for_status()
    return response.text
```

If you cannot verify a citation:

```latex
\cite{PLACEHOLDER_author2024_verify_this}  % TODO: Verify this citation exists
```

**Always tell the scientist**: “I’ve marked [X] citations as placeholders that need verification.”

See [references/citation-workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/citation-workflow.md) for complete API documentation and the full `CitationManager` class.

### Step 1.4: Organize Related Work

Group papers by methodology, not paper‑by‑paper:

**Good**: “One line of work uses X’s assumption [refs] whereas we use Y’s assumption because…”
**Bad**: “Smith et al. introduced X. Jones et al. introduced Y. We combine both.”

---
## Фаза 2: Проектирование экспериментов

**Goal**: Спроектировать эксперименты, которые напрямую поддерживают утверждения статьи. Каждый эксперимент должен отвечать на конкретный вопрос.

### Step 2.1: Сопоставление утверждений и экспериментов

Создай явное сопоставление:

| Утверждение | Эксперимент | Ожидаемое доказательство |
|------------|-------------|--------------------------|
| «Our method outperforms baselines» | Main comparison (Table 1) | Win rate, statistical significance |
| «Effect is larger for weaker models» | Model scaling study | Monotonic improvement curve |
| «Convergence requires scope constraints» | Constrained vs unconstrained | Convergence rate comparison |

**Rule**: Если эксперимент не сопоставлен с утверждением, не проводи его.

### Step 2.2: Проектирование baseline‑ов

Сильные baseline‑ы — то, что отличает принятые статьи от отклонённых. Рецензенты спросят: «Сравнивали ли они с X?»

Стандартные категории baseline‑ов:
- **Naive baseline**: Самый простой возможный подход
- **Strong baseline**: Лучший известный существующий метод
- **Ablation baselines**: Твой метод без одного компонента
- **Compute‑matched baselines**: Тот же бюджет вычислений, но другое распределение

### Step 2.3: Определение протокола оценки

Перед запуском чего‑либо укажи:
- **Metrics**: Что измеряешь, символы направления (выше / ниже — лучше)
- **Aggregation**: Как объединять результаты по запускам/задачам
- **Statistical tests**: Какие тесты установят значимость
- **Sample sizes**: Сколько запусков/проблем/задач

### Step 2.4: Написание скриптов экспериментов

Следуй этим шаблонам из успешных исследовательских пайплайнов:

**Incremental saving** — сохраняй результаты после каждого шага для восстановления после сбоя:
```python
# Save after each problem/task
result_path = f"results/{task}/{strategy}/result.json"
if os.path.exists(result_path):
    continue  # Skip already-completed work
# ... run experiment ...
with open(result_path, 'w') as f:
    json.dump(result, f, indent=2)
```

**Artifact preservation** — сохраняй все промежуточные выводы:
```
results/<experiment>/
  <task>/
    <strategy>/
      final_output.md          # Final result
      history.json             # Full trajectory
      pass_01/                 # Per-iteration artifacts
        version_a.md
        version_b.md
        critic.md
```

**Separation of concerns** — держи генерацию, оценку и визуализацию раздельно:
```
run_experiment.py              # Core experiment runner
run_baselines.py               # Baseline comparison
run_comparison_judge.py        # Blind evaluation
analyze_results.py             # Statistical analysis
make_charts.py                 # Visualization
```

См. [references/experiment-patterns.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/experiment-patterns.md) для полного набора шаблонов дизайна, мониторинга cron и восстановления после ошибок.

### Step 2.5: Проектирование human evaluation (при необходимости)

Многие статьи в области NLP, HCI и alignment требуют human evaluation как основного или дополнительного доказательства. Спроектируй её до запуска автоматических экспериментов — human eval часто требует больше времени (одобрение IRB, набор аннотаторов).

**Когда нужна human evaluation:**
- Automated metrics не отражают то, что тебя интересует (fluency, helpfulness, safety)
- Твой вклад касается качеств, воспринимаемых человеком (readability, preference, trust)
- Рецензенты на конференциях NLP (ACL, EMNLP) ожидают её для задач генерации

**Ключевые решения дизайна:**

| Decision | Options | Guidance |
|----------|---------|-----------|
| **Annotator type** | Expert, crowdworker, end‑user | Выбирай в соответствии с тем, что требуют твои claims |
| **Scale** | Likert (1‑5), pairwise comparison, ranking | Pairwise более надёжно, чем Likert, для выводов LLM |
| **Sample size** | Per annotator and total items | Проведи power‑analysis или минимум 100 items, 3 + аннотатора |
| **Agreement metric** | Cohen's kappa, Krippendorff's alpha, ICC | Krippendorff's alpha для >2 аннотаторов; также укажи raw agreement |
| **Platform** | Prolific, MTurk, internal team | Prolific — качество; MTurk — масштаб; internal — доменно‑специфическая экспертиза |

**Annotation guideline checklist:**
```
- [ ] Clear task description with examples (good AND bad)
- [ ] Decision criteria for ambiguous cases
- [ ] At least 2 worked examples per category
- [ ] Attention checks / gold standard items (10-15% of total)
- [ ] Qualification task or screening round
- [ ] Estimated time per item and fair compensation (>= local minimum wage)
- [ ] IRB/ethics review if required by your institution
```

**Требования к отчётности** (рецензенты проверяют всё перечисленное):
- Количество аннотаторов и их квалификация
- Межаннотаторское согласие с указанием конкретной метрики и значения
- Детали компенсации (сумма, ориентировочная почасовая ставка)
- Описание или скриншот интерфейса аннотирования (приложение)
- Общее время аннотирования

См. [references/human-evaluation.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/human-evaluation.md) для полного руководства, включая статистические тесты для данных human eval, шаблоны контроля качества краудсорсинга и рекомендации по IRB.
## Phase 3: Выполнение экспериментов и мониторинг

**Goal**: Запускать эксперименты надёжно, отслеживать прогресс, восстанавливаться после сбоев.

### Step 3.1: Запуск экспериментов

Используй `nohup` для длительно работающих экспериментов:

```bash
nohup python run_experiment.py --config config.yaml > logs/experiment_01.log 2>&1 &
echo $!  # Record the PID
```

**Параллельное выполнение**: Запускай независимые эксперименты одновременно, но учитывай ограничения скорости API. 4 и более одновременных экспериментов на одном и том же API замедлят каждый из них.

### Step 3.2: Настройка мониторинга (шаблон Cron)

Для длительно работающих экспериментов настрой периодические проверки статуса. Шаблон команды cron должен выглядеть так:

```
Monitor Prompt Template:
1. Check if process is still running: ps aux | grep <pattern>
2. Read last 30 lines of log: tail -30 <logfile>
3. Check for completed results: ls <result_dir>
4. If results exist, read and report: cat <result_file>
5. If all done, commit: git add -A && git commit -m "<descriptive message>" && git push
6. Report in structured format (tables with key metrics)
7. Answer the key analytical question for this experiment
```

**Тихий режим**: Если с последней проверки ничего не изменилось, отвечай `[SILENT]`, чтобы подавить уведомление пользователю. Сообщай только при появлении новых данных.

### Step 3.3: Обработка сбоев

Распространённые типы сбоев и способы восстановления:

| Failure | Detection | Recovery |
|---------|-----------|----------|
| API rate limit / credit exhaustion | Ошибки 402/429 в логах | Подожди, затем запусти заново (скрипты пропускают уже выполненную работу) |
| Process crash | PID исчез, неполные результаты | Перезапусти с последней контрольной точки |
| Timeout on hard problems | Процесс завис, нет прогресса в логах | Убей процесс и пропусти, отметь в результатах |
| Wrong model ID | Ошибки, связанные с именем модели | Исправь ID и запусти заново |

**Ключ**: Скрипты всегда должны проверять наличие уже полученных результатов и пропускать выполненную работу. Это делает повторные запуски безопасными и эффективными.

### Step 3.4: Коммит завершённых результатов

После завершения каждой партии экспериментов:

```bash
git add -A
git commit -m "Add <experiment name>: <key finding in 1 line>"
git push
```

### Step 3.5: Ведение журнала экспериментов

Git‑коммиты фиксируют, что произошло, но не **дерево исследований** — решения о том, что пробовать дальше, исходя из полученных знаний. Веди структурированный журнал экспериментов, который фиксирует это дерево:

```json
// experiment_journal.jsonl — append one entry per experiment attempt
{
  "id": "exp_003",
  "parent": "exp_001",
  "timestamp": "2025-05-10T14:30:00Z",
  "hypothesis": "Adding scope constraints will fix convergence failure from exp_001",
  "plan": "Re-run autoreason with max_tokens=2000 and fixed structure template",
  "config": {"model": "haiku", "strategy": "autoreason", "max_tokens": 2000},
  "status": "completed",
  "result_path": "results/exp_003/",
  "key_metrics": {"win_rate": 0.85, "convergence_rounds": 3},
  "analysis": "Scope constraints fixed convergence. Win rate jumped from 0.42 to 0.85.",
  "next_steps": ["Try same constraints on Sonnet", "Test without structure template"],
  "figures": ["figures/exp003_convergence.pdf"]
}
```

**Зачем журнал, а не только git?** Git отслеживает изменения файлов. Журнал фиксирует рассуждения: почему ты попробовал X, что ты узнал и как это влияет на следующий эксперимент. При написании статьи это дерево бесценно для раздела Methods («мы наблюдали X, что мотивировало Y») и для честного отчёта о неудачах.

**Выбор лучшего пути**: Когда журнал показывает разветвлённое дерево (exp_001 → exp_002a, exp_002b, exp_003), определи путь, который лучше всего поддерживает выводы статьи. Документируй ветки‑тупики в приложении как абляции или отрицательные результаты.

**Снимок кода для каждого эксперимента**: Скопируй скрипт эксперимента после каждого запуска:
```bash
cp experiment.py results/exp_003/experiment_snapshot.py
```
Это обеспечивает точное воспроизведение даже после последующих изменений кода.
## Фаза 4: Анализ результатов

**Goal**: Выделить выводы, посчитать статистику, определить историю.

### Step 4.1: Сбор результатов

Напиши скрипты анализа, которые:
1. Загружают все файлы результатов из партии
2. Вычисляют метрики по задачам и агрегированные метрики
3. Генерируют сводные таблицы

```python
# Standard analysis pattern
import json, os
from pathlib import Path

results = {}
for result_file in Path("results/").rglob("result.json"):
    data = json.loads(result_file.read_text())
    strategy = result_file.parent.name
    task = result_file.parent.parent.name
    results.setdefault(strategy, {})[task] = data

# Compute aggregate metrics
for strategy, tasks in results.items():
    scores = [t["score"] for t in tasks.values()]
    print(f"{strategy}: mean={np.mean(scores):.1f}, std={np.std(scores):.1f}")
```

### Step 4.2: Статистическая значимость

Всегда вычисляй:
- **Error bars**: стандартное отклонение или стандартная ошибка — укажи, что именно
- **Confidence intervals**: 95 % CI для ключевых результатов
- **Pairwise tests**: тест МакНемара для сравнения двух методов
- **Effect sizes**: d или h Коэна для практической значимости

См. [references/experiment-patterns.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/experiment-patterns.md) для полной реализации теста МакНемара, бутстрэп‑CI и h Коэна.

### Step 4.3: Определение истории

После анализа явно ответь на:
1. **Какой главный вывод?** Сформулируй в одном предложении.
2. **Что тебя удивило?** Неожиданные результаты часто делают лучшие статьи.
3. **Что провалилось?** Неудачные эксперименты могут быть самыми информативными. Честный отчёт о провалах усиливает статью.
4. **Какие последующие эксперименты нужны?** Результаты часто вызывают новые вопросы.

#### Обработка отрицательных или нулевых результатов

Когда гипотеза оказалась неверной или результаты неоднозначны, у тебя есть три варианта:

| Situation | Action | Venue Fit |
|-----------|--------|-----------|
| Гипотеза неверна, но **почему** информативно | Сформировать статью вокруг анализа причин | NeurIPS, ICML (если анализ строгий) |
| Метод не превосходит базовые линии, но **выявляет что‑то новое** | Переформулировать вклад как понимание/анализ | ICLR (ценит понимание), workshop‑papers |
| Чистый отрицательный результат по популярному утверждению | Оформить его — сообществу это нужно знать | NeurIPS Datasets & Benchmarks, TMLR, workshops |
| Результаты неоднозначны, нет чёткой истории | Переориентироваться — провести другие эксперименты или изменить фокус | Не заставлять писать статью, если её нет |

**Как написать статью с отрицательными результатами:**
- Начни с того, что сообщество считает и почему важно это проверить
- Описывай строгую методологию (должна быть безупречной — рецензенты будут проверять её тщательнее)
- Представь нулевой результат ясно, с статистическими доказательствами
- Проанализируй **почему** ожидаемый результат не получился
- Обсуди последствия для области

**Конференции, открыто принимающие отрицательные результаты**: NeurIPS (трек Datasets & Benchmarks), TMLR, ML Reproducibility Challenge, воркшопы на крупных конференциях. Некоторые воркшопы специально запрашивают отрицательные результаты.

### Step 4.4: Создание фигур и таблиц

**Figures**:
- Используй векторную графику (PDF) для всех графиков: `plt.savefig('fig.pdf')`
- Палитры, безопасные для дальтоников (Okabe‑Ito или Paul Tol)
- Самодостаточные подписи — читатель должен понять без основного текста
- Без заголовка внутри фигуры — подпись выполняет эту функцию

**Tables**:
- Используй LaTeX‑пакет `booktabs`
- Жирным выделяй лучшее значение по каждой метрике
- Добавляй символы направления (выше / ниже — лучше)
- Единая точность десятичных знаков

```latex
\usepackage{booktabs}
\begin{tabular}{lcc}
\toprule
Method & Accuracy $\uparrow$ & Latency $\downarrow$ \\
\midrule
Baseline & 85.2 & 45ms \\
\textbf{Ours} & \textbf{92.1} & 38ms \\
\bottomrule
\end{tabular}
```

### Step 4.5: Решить: больше экспериментов или писать?

| Situation | Action |
|-----------|--------|
| Основные утверждения подтверждены, результаты значимы | Перейти к Phase 5 (написание) |
| Результаты неоднозначны, нужны дополнительные данные | Вернуться к Phase 2 (дизайн) |
| Неожиданное открытие подразумевает новое направление | Вернуться к Phase 2 (дизайн) |
| Не хватает одной абляции, которую спросят рецензенты | Провести её, затем Phase 5 |
| Все эксперименты проведены, но некоторые провалились | Зафиксировать провалы, перейти к Phase 5 |

### Step 4.6: Написать журнал экспериментов (мост к написанию)

Перед переходом к написанию статьи создай структурированный журнал экспериментов, который связывает результаты с текстом. Это единственная самая важная связующая ткань между экспериментами и написанием — без неё агенту‑писателю придётся заново выводить историю из сырых файлов результатов.

**Создай `experiment_log.md`** со следующей структурой:

```markdown
# Experiment Log

## Contribution (one sentence)
[The paper's main claim]

## Experiments Run

### Experiment 1: [Name]
- **Claim tested**: [Which paper claim this supports]
- **Setup**: [Model, dataset, config, number of runs]
- **Key result**: [One sentence with the number]
- **Result files**: results/exp1/final_info.json
- **Figures generated**: figures/exp1_comparison.pdf
- **Surprising findings**: [Anything unexpected]

### Experiment 2: [Name]
...

## Figures
| Filename | Description | Which section it belongs in |
|----------|-------------|---------------------------|
| figures/main_comparison.pdf | Bar chart comparing all methods on benchmark X | Results, Figure 2 |
| figures/ablation.pdf | Ablation removing components A, B, C | Results, Figure 3 |
...

## Failed Experiments (document for honesty)
- [What was tried, why it failed, what it tells us]

## Open Questions
- [Anything the results raised that the paper should address]
```

**Почему это важно**: При подготовке черновика агент (или делегированный суб‑агент) может загрузить `experiment_log.md` вместе с LaTeX‑шаблоном и создать первый черновик, основанный на реальных результатах. Без этого моста агенту‑писателю придётся парсить сырые JSON/CSV файлы и выводить историю — частый источник галлюцинаций или неверных цифр.

**Git‑дисциплина**: Закоммить этот журнал вместе с результатами, которые он описывает.
## Итеративное уточнение: выбор стратегии

Любой вывод в этом конвейере — черновики статей, скрипты экспериментов, анализ — может быть итеративно уточнён. Исследование **autoreason** предоставляет эмпирические доказательства того, когда каждая стратегия уточнения работает, а когда терпит неудачу. Используй этот раздел, чтобы выбрать правильный подход.

### Быстрая таблица решений

| Твоя ситуация | Стратегия | Почему |
|---------------|----------|--------|
| Модель среднего уровня + ограниченная задача | **Autoreason** | Идеальное соотношение. Разрыв между генерацией и оценкой самый широкий. Базовые модели активно уничтожают слабые выводы. |
| Модель среднего уровня + открытая задача | **Autoreason** с добавленными ограничениями области | Добавь фиксированные факты, структуру или результат, чтобы ограничить пространство улучшений. |
| Модель передового уровня + ограниченная задача | **Autoreason** | Выигрывает 2/3 ограниченных задач даже у передовых моделей. |
| Модель передового уровня + неограниченная задача | **Critique-and-revise** или **single pass** | Autoreason применяется последним. Модель достаточно хорошо самокритична. |
| Конкретная техническая задача (проектирование системы) | **Critique-and-revise** | Прямой цикл «найти‑и‑исправить» более эффективен. |
| Задача заполнения шаблона (одна правильная структура) | **single pass** или **conservative** | Минимальное пространство решений. Итерация не добавляет ценности. |
| Код с тестами | **Autoreason (code variant)** | Структурированный анализ *почему* он не прошёл перед исправлением. Коэффициент восстановления 62 % против 43 %. |
| Очень слабая модель (класс Llama 8B) | **single pass** | Модель слишком слаба для разнообразных кандидатов. Инвестируй в качество генерации. |

### Разрыв между генерацией и оценкой

**Ключевой вывод**: ценность **autoreason** зависит от разрыва между способностью модели генерировать и её способностью самокритично оценивать.

<!-- ascii-guard-ignore -->
```
Model Tier        │ Generation │ Self-Eval │ Gap    │ Autoreason Value
──────────────────┼────────────┼───────────┼────────┼─────────────────
Weak (Llama 8B)   │ Poor       │ Poor      │ Small  │ None — can't generate diverse candidates
Mid (Haiku 3.5)   │ Decent     │ Poor      │ LARGE  │ MAXIMUM — 42/42 perfect Borda
Mid (Gemini Flash)│ Decent     │ Moderate  │ Large  │ High — wins 2/3
Strong (Sonnet 4) │ Good       │ Decent    │ Medium │ Moderate — wins 3/5
Frontier (S4.6)   │ Excellent  │ Good      │ Small  │ Only with constraints
```
<!-- ascii-guard-ignore-end -->

Этот разрыв структурный, а не временный. По мере снижения стоимости сегодняшняя передовая модель становится завтрашней моделью среднего уровня. Идеальное соотношение смещается, но никогда не исчезает.

### Цикл Autoreason (резюме)

Каждый проход генерирует три кандидата от новых, изолированных агентов:

1. **Critic** → находит проблемы в текущем A (без исправлений)
2. **Author B** → исправляет A на основе критики
3. **Synthesizer** → объединяет A и B (случайные метки)
4. **Judge Panel** → 3 слепых судьи CoT ранжируют A, B, AB по системе Борда
5. **Convergence** → A выигрывает k=2 последовательных прохода → завершено

**Ключевые параметры**
- сходимость k=2 (k=1 — преждевременно, k=3 — слишком дорого, без прироста качества)
- судьи CoT всегда (3 × быстрее сходимость)
- температура 0.8 у авторов, 0.3 у судей
- консервативный разрыв: при равенстве выигрывает текущий кандидат
- каждая роль — новый агент без общего контекста

### Применение к черновикам статей

При уточнении самой статьи через **autoreason**:
- **Предоставь критикам истинные данные**: реальные экспериментальные данные, JSON‑результаты, статистические выводы. Без этого модели будут галлюцинировать вымышленные абляционные исследования и поддельные доверительные интервалы.
- **Используй минимум 3 работающих судьи**: сломанный парсер судьи не добавляет шум — он полностью разрушает равновесие.
- **Ограничь область правок**: «Устранить эти конкретные недостатки», а не «улучшить статью».

### Режимы отказов

| Отказ | Обнаружение | Исправление |
|-------|--------------|-------------|
| Нет сходимости (A никогда не выигрывает) | A выигрывает < 15 % за 20+ проходов | Добавь ограничения области задачи |
| Дрейф синтеза | Объём текста растёт без границ | Ограничь структуру и результат |
| Деградация ниже **single pass** | Базовые модели получают более высокий балл, чем итеративный вывод | Перейди к **single pass**; модель может быть слишком слабой |
| Переобучение (код) | Высокий проход публичных тестов, низкий — приватных | Используй структурный анализ, а не только обратную связь от тестов |
| Сломанные судьи | Ошибки парсинга уменьшают панель ниже 3 | Исправь парсер перед продолжением |

См. [references/autoreason-methodology.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/autoreason-methodology.md) для полного набора подсказок, деталей оценки по Борду, руководства по выбору модели, шаблонов ограничения области и справки по бюджету вычислений.
## Phase 5: Paper Drafting

**Goal**: Write a complete, publication‑ready paper.

### Управление контекстом для крупных проектов

Проект статьи с более чем 50 файлами экспериментов, несколькими каталогами результатов и обширными заметками по литературе легко может превысить окно контекста агента. Управляй этим проактивно:

**Что загружать в контекст для каждой задачи написания:**

| Задача написания | Загружать в контекст | Не загружать |
|------------------|----------------------|--------------|
| Написание Introduction | `experiment_log.md`, формулировка вклада, 5‑10 самых релевантных аннотаций статей | Сырые JSON‑результаты, полные скрипты экспериментов, все заметки по литературе |
| Написание Methods | Конфиги экспериментов, псевдокод, описание архитектуры | Сырые логи, результаты других экспериментов |
| Написание Results | `experiment_log.md`, таблицы‑резюме результатов, список фигур | Полные скрипты анализа, промежуточные данные |
| Написание Related Work | Организованные заметки‑цитаты (вывод Step 1.4), файл `.bib` | Файлы экспериментов, сырые PDF |
| Revision pass | Полный черновик статьи, конкретные замечания рецензентов | Всё остальное |

**Принципы:**
- **`experiment_log.md` — основной мост контекста** — он суммирует всё, что нужно для написания, без загрузки сырых файлов (см. Step 4.6).
- **Загружай контекст только одного раздела за раз** при делегировании. Под‑агент, пишущий Methods, не нуждается в заметках по литературному обзору.
- **Суммируй, а не включай сырые файлы.** Для JSON‑результата в 200 строк загрузи 10‑строчную таблицу‑резюме. Для статьи в 50 страниц загрузите 5‑предложный абстракт + вашу 2‑строчную заметку о её релевантности.
- **Для очень больших проектов**: создай каталог `context/` с предварительно сжатыми резюме:
  ```
  context/
    contribution.md          # 1 sentence
    experiment_summary.md    # Key results table (from experiment_log.md)
    literature_map.md        # Organized citation notes
    figure_inventory.md      # List of figures with descriptions
  ```

### Принцип нарратива

**Самый критичный инсайт**: твоя статья — не набор экспериментов, а история с одной чёткой идеей, подкреплённой доказательствами.

Каждая успешная ML‑статья опирается на то, что Нил Нанда называет «нарративом»: короткая, строгая, доказательная техническая история с выводом, который интересует читателя.

**Три столпа (должны быть кристально ясны к концу Introduction):**

| Столп | Описание | Проверка |
|-------|----------|----------|
| **The What** | 1‑3 конкретных новых утверждения | Можно ли сформулировать их в одном предложении? |
| **The Why** | Строгие эмпирические доказательства | Отличаются ли эксперименты твою гипотезу от альтернатив? |
| **The So What** | Почему это важно читателю | Связано ли это с известной проблемой сообщества? |

**Если ты не можешь сформулировать свой вклад в одном предложении, статьи ещё нет.**

### Источники, лежащие в основе рекомендаций

Этот навык синтезирует писательскую философию исследователей, активно публикующихся в топ‑конференциях. Слой писательской философии изначально был собран [Orchestra Research](https://github.com/orchestra-research) как skill `ml-paper-writing`.

| Источник | Ключевой вклад | Ссылка |
|----------|----------------|--------|
| **Neel Nanda** (Google DeepMind) | Принцип нарратива, рамка What/Why/So What | [How to Write ML Papers](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) |
| **Sebastian Farquhar** (DeepMind) | Формула абстракта в 5 предложений | [How to Write ML Papers](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/) |
| **Gopen & Swan** | 7 принципов ожиданий читателя | [Science of Scientific Writing](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf) |
| **Zachary Lipton** | Выбор слов, устранение «hedging» | [Heuristics for Scientific Writing](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/) |
| **Jacob Steinhardt** (UC Berkeley) | Точность, согласованность терминологии | [Writing Tips](https://bounded-regret.ghost.io/) |
| **Ethan Perez** (Anthropic) | Микро‑уровневые советы по ясности | [Easy Paper Writing Tips](https://ethanperez.net/easy-paper-writing-tips/) |
| **Andrej Karpathy** | Фокус на едином вкладе | Разные лекции |

**Для более глубокого изучения см.:**
- [references/writing-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/writing-guide.md) — полные объяснения с примерами
- [references/sources.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/sources.md) — полная библиография

### Распределение времени

Выделяй примерно **одинаковое время** на каждый из пунктов:
1. Абстракт
2. Введение
3. Фигуры
4. Всё остальное вместе

**Почему?** Большинство рецензентов формируют мнение, ещё не дойдя до раздела Methods. Читатель проходит статью так: заголовок → абстракт → введение → фигуры → (возможно) остальное.

### Рабочий процесс написания

```
Paper Writing Checklist:
- [ ] Step 1: Define the one-sentence contribution
- [ ] Step 2: Draft Figure 1 (core idea or most compelling result)
- [ ] Step 3: Draft abstract (5-sentence formula)
- [ ] Step 4: Draft introduction (1-1.5 pages max)
- [ ] Step 5: Draft methods
- [ ] Step 6: Draft experiments & results
- [ ] Step 7: Draft related work
- [ ] Step 8: Draft conclusion & discussion
- [ ] Step 9: Draft limitations (REQUIRED by all venues)
- [ ] Step 10: Plan appendix (proofs, extra experiments, details)
- [ ] Step 11: Complete paper checklist
- [ ] Step 12: Final review
```

### Двухпроходный паттерн уточнения

При написании с помощью AI‑агента используй **двухпроходный** подход (проверено в пайплайне AI‑Scientist от SakanaAI):

**Pass 1 — Писать + сразу уточнять в рамках раздела:**
Для каждого раздела создай полный черновик, затем сразу же уточни его, оставаясь в том же контексте. Так ловятся локальные проблемы (ясность, связность, полнота), пока раздел ещё «свежий».

**Pass 2 — Глобальное уточнение с полным контекстом статьи:**
После того как все разделы написаны, пройди каждый из них, учитывая полную статью. Это выявит межразделовые проблемы: избыточность, несогласованность терминов, нарушение нарративного потока и пробелы, когда один раздел обещает то, чего другой не доставляет.

```
Second-pass refinement prompt (per section):
"Review the [SECTION] in the context of the complete paper.
- Does it fit with the rest of the paper? Are there redundancies with other sections?
- Is terminology consistent with Introduction and Methods?
- Can anything be cut without weakening the message?
- Does the narrative flow from the previous section and into the next?
Make minimal, targeted edits. Do not rewrite from scratch."
```

### Чек‑лист ошибок LaTeX

Прикладывай этот чек‑лист к каждому запросу уточнения. Это самые частые ошибки, когда LLM генерируют LaTeX:

```
LaTeX Quality Checklist (verify after every edit):
- [ ] No unenclosed math symbols ($ signs balanced)
- [ ] Only reference figures/tables that exist (\ref matches \label)
- [ ] No fabricated citations (\cite matches entries in .bib)
- [ ] Every \begin{env} has matching \end{env} (especially figure, table, algorithm)
- [ ] No HTML contamination (</end{figure}> instead of \end{figure})
- [ ] No unescaped underscores outside math mode (use \_ in text)
- [ ] No duplicate \label definitions
- [ ] No duplicate section headers
- [ ] Numbers in text match actual experimental results
- [ ] All figures have captions and labels
- [ ] No overly long lines that cause overfull hbox warnings
```

### Шаг 5.0: Заголовок

Заголовок — самый просматриваемый элемент статьи. Он определяет, кликнет ли кто‑то дальше к абстракту.

**Хорошие заголовки**:
- Формулируют вклад или находку: «Autoreason: When Iterative LLM Refinement Works and Why It Fails»
- Выделяют неожиданную результативность: «Scaling Data‑Constrained Language Models» (подразумевается, что это возможно)
- Указывают название метода + его назначение: «DPO: Direct Preference Optimization of Language Models»

**Плохие заголовки**:
- Слишком общие: «An Approach to Improving Language Model Outputs»
- Слишком длинные: более ~15 слов
- Только жаргон: «Asymptotic Convergence of Iterative Stochastic Policy Refinement» (для кого?)

**Правила**:
- Если у тебя есть название метода, включи его (для цитируемости).
- Добавь 1‑2 ключевых слова, по которым рецензенты будут искать.
- Избегай двоеточий, если обе части не несут смысловой нагрузки.
- Проверь: узнает ли рецензент по заголовку область и вклад без чтения статьи?

### Шаг 5.1: Абстракт (формула в 5 предложений)

От Себастьяна Фаркуара (DeepMind):

```
1. What you achieved: "We introduce...", "We prove...", "We demonstrate..."
2. Why this is hard and important
3. How you do it (with specialist keywords for discoverability)
4. What evidence you have
5. Your most remarkable number/result
```

**Удали** шаблонные вводные типа «Large language models have achieved remarkable success…».

### Шаг 5.2: Figure 1

Figure 1 — вторая по важности вещь после абстракта. Сформируй её до написания Introduction — это заставит уточнить ядро идеи.

| Тип Figure 1 | Когда использовать | Пример |
|-------------|-------------------|--------|
| **Диаграмма метода** | Новый архитектурный подход или пайплайн | TikZ‑flowchart твоей системы |
| **Тизер результатов** | Один убедительный результат раскрывает всю историю | Бар‑чарт «Our vs. baselines» с чётким разрывом |
| **Иллюстрация проблемы** | Проблема неинтуитивна | До/после, показывающее исправляемый сбой |
| **Концептуальная диаграмма** | Абстрактный вклад нуждается в визуальном обосновании | 2×2‑матрица свойств метода |

**Правила**: Figure 1 должна быть понятна без чтения текста. Описание в подписи должно полностью передавать суть. Цвет используй осознанно — не просто для украшения.

### Шаг 5.3: Introduction (макс 1‑1.5 стр.)

Обязательно:
- Чёткое формулирование проблемы
- Краткий обзор подхода
- 2‑4 пункта вклада (по 1‑2 строки каждый, в двухколоночном формате)
- Методы должны начинаться к странице 2‑3

### Шаг 5.4: Methods

Обеспечь возможность воспроизведения:
- Концептуальный план или псевдокод
- Полный список гиперпараметров
- Достаточно деталей архитектуры для воспроизводства
- Представь окончательные дизайнерские решения; абляции вынеси в Experiments

### Шаг 5.5: Experiments & Results

Для каждого эксперимента явно укажи:
- **Какой тезис он поддерживает**
- Как он связывается с главным вкладом
- Что наблюдать: «синяя линия показывает X, что демонстрирует Y»

Требования:
- Ошибки с указанием метода (std dev vs std error)
- Диапазоны гиперпараметров, использованные в поиске
- Описание вычислительной инфраструктуры (тип GPU, суммарные часы)
- Способы установки seed’ов

### Шаг 5.6: Related Work

Организуй методологически, а не по отдельным статьям. Цитируй обильно — рецензенты часто являются авторами релевантных работ.

### Шаг 5.7: Limitations (ОБЯЗАТЕЛЬНО)

Все крупные конференции требуют этот раздел. Честность помогает:
- Рецензенты проинструктированы не штрафовать за откровенное признание ограничений
- Предвосхищаешь критику, указывая слабости заранее
- Объясни, почему ограничения не подрывают основные выводы

### Шаг 5.8: Conclusion & Discussion

**Conclusion** (обязательно, 0.5‑1 стр.):
- Переформулируй вклад в одном предложении (другими словами, чем в абстракте)
- Кратко суммируй ключевые находки (2‑3 предложения, без списка)
- Последствия: что это значит для области?
- Будущее: 2‑3 конкретных шага (не «мы оставляем X на будущее»)

**Discussion** (по желанию, иногда объединяется с Conclusion):
- Широкие последствия за пределами непосредственных результатов
- Связи с другими подполями
- Честная оценка, когда метод работает, а когда нет
- Практические соображения по внедрению

**Не вводи** новые результаты или утверждения в Conclusion.

### Шаг 5.9: Стратегия Appendix

Appendix’ы не ограничены по объёму на всех крупных конференциях и критически важны для воспроизводимости. Структура:

| Раздел Appendix | Что помещать |
|-----------------|--------------|
| **Proofs & Derivations** | Полные доказательства, слишком длинные для основного текста. В тексте можно писать «доказательство в Appendix A». |
| **Additional Experiments** | Абляции, кривые масштабирования, разбивка по датасетам, чувствительность к гиперпараметрам |
| **Implementation Details** | Полные таблицы гиперпараметров, детали обучения, спецификации железа, seed’ы |
| **Dataset Documentation** | Процесс сбора данных, инструкции по аннотации, лицензии, предобработка |
| **Prompts & Templates** | Точные подсказки, использованные в LLM‑методах, шаблоны оценки |
| **Human Evaluation** | Скриншоты интерфейса аннотации, инструкции для аннотаторов, детали IRB |
| **Additional Figures** | Разбивки по задачам, визуализации траекторий, примеры провальных кейсов |

**Правила**:
- Основная статья должна быть самодостаточной — рецензенты не обязаны читать Appendix.
- Критически важные доказательства не помещай только в Appendix.
- Делай кросс‑ссылки: «Полные результаты в Table 5 (Appendix B)», а не просто «см. Appendix».
- Используй команду `\appendix`, затем `\section{A: Proofs}` и т.д.

### Управление страницами

Если превышаешь лимит:

| Стратегия сокращения | Сокращает | Риск |
|----------------------|-----------|------|
| Перенести доказательства в Appendix | 0.5‑2 стр. | Низкий — стандартная практика |
| Сократить Related Work | 0.5‑1 стр. | Средний — могут пропустить важные ссылки |
| Объединить таблицы с подфигурами | 0.25‑0.5 стр. | Низкий — часто улучшает читаемость |
| Использовать `\vspace{-Xpt}` умеренно | 0.1‑0.3 стр. | Низкий, если незаметно; высокий, если явно |
| Убрать качественные примеры | 0.5‑1 стр. | Средний — рецензенты любят примеры |
| Уменьшить размеры фигур | 0.25‑0.5 стр. | Высокий — фигуры должны оставаться разборчивыми |

**Не делай**: уменьшать размер шрифта, менять поля, удалять обязательные разделы (Limitations, Broader Impact) или использовать `\small`/`\footnotesize` для основного текста.

### Шаг 5.10: Ethics & Broader Impact Statement

Большинство конференций сейчас требуют или настоятельно советуют включать этический/влияющий на общество раздел. Это не шаблон — рецензенты читают его и могут отклонить работу за этические проблемы.

**Что включать:**

| Компонент | Содержание | Требуется на |
|-----------|-------------|--------------|
| **Positive societal impact** | Как работа приносит пользу обществу | NeurIPS, ICML |
| **Potential negative impact** | Риски злоупотребления, двойного использования, режимы отказа | NeurIPS, ICML |
| **Fairness & bias** | Есть ли известные предвзятости в методе/данных? | Все конференции (неявно) |
| **Environmental impact** | Углеродный след вычислений при крупном обучении | ICML, всё чаще NeurIPS |
| **Privacy** | Используются ли персональные данные или их обработка? | ACL, NeurIPS |
| **LLM disclosure** | Был ли ИИ использован при написании или экспериментах? | ICLR (обязательно), ACL |

**Как писать заявление:**

```latex
\section*{Broader Impact Statement}
% NeurIPS/ICML: after conclusion, does not count toward page limit

% 1. Positive applications (1-2 sentences)
This work enables [specific application] which may benefit [specific group].

% 2. Risks and mitigations (1-3 sentences, be specific)
[Method/model] could potentially be misused for [specific risk]. We mitigate
this by [specific mitigation, e.g., releasing only model weights above size X,
including safety filters, documenting failure modes].

% 3. Limitations of impact claims (1 sentence)
Our evaluation is limited to [specific domain]; broader deployment would
require [specific additional work].
```

**Типичные ошибки:**
- «Мы не видим негативных последствий» — почти никогда не правдиво, рецензенты скептически относятся.
- Неопределённые формулировки: «это может быть использовано неправильно» без уточнения как.
- Игнорирование вычислительных затрат при масштабных экспериментах.
- Забвение раскрыть использование LLM там, где это требуется.

**Углеродный след вычислений** (для тяжёлых обучающих работ):

```python
# Estimate using ML CO2 Impact tool methodology
gpu_hours = 1000  # total GPU hours
gpu_tdp_watts = 400  # e.g., A100 = 400W
pue = 1.1  # Power Usage Effectiveness (data center overhead)
carbon_intensity = 0.429  # kg CO2/kWh (US average; varies by region)

energy_kwh = (gpu_hours * gpu_tdp_watts * pue) / 1000
carbon_kg = energy_kwh * carbon_intensity
print(f"Energy: {energy_kwh:.0f} kWh, Carbon: {carbon_kg:.0f} kg CO2eq")
```

### Шаг 5.11: Datasheets & Model Cards (при необходимости)

Если статья представляет **новый датасет** или **выдаёт модель**, включи структурированную документацию. Рецензенты всё чаще её требуют, а трек NeurIPS Datasets & Benchmarks делает её обязательной.

**Datasheets for Datasets** (Gebru et al., 2021) — размести в Appendix:

```
Dataset Documentation (Appendix):
- Motivation: Why was this dataset created? What task does it support?
- Composition: What are the instances? How many? What data types?
- Collection: How was data collected? What was the source?
- Preprocessing: What cleaning/filtering was applied?
- Distribution: How is the dataset distributed? Under what license?
- Maintenance: Who maintains it? How to report issues?
- Ethical considerations: Contains personal data? Consent obtained?
  Potential for harm? Known biases?
```

**Model Cards** (Mitchell et al., 2019) — размести в Appendix для релизов моделей:

```
Model Card (Appendix):
- Model details: Architecture, training data, training procedure
- Intended use: Primary use cases, out-of-scope uses
- Metrics: Evaluation metrics and results on benchmarks
- Ethical considerations: Known biases, fairness evaluations
- Limitations: Known failure modes, domains where model underperforms
```

### Стиль написания

**Ясность на уровне предложения (7 принципов Gopen & Swan):**

| Принцип | Правило |
|---------|---------|
| Близость подлежащего и сказуемого | Держи их рядом |
| Позиция ударения | Делай акцент в конце предложения |
| Позиция темы | Сначала контекст, затем новая информация |
| Сначала известное, потом новое | Переходи от привычного к новому |
| Один блок — одна функция | Каждый абзац несёт одну мысль |
| Действие в глаголе | Используй глаголы, а не номинализации |
| Контекст перед новым | Сначала задавай сцену, потом представляй новизну |

**Выбор слов (Lipton, Steinhardt):**
- Будь конкретен: «accuracy», а не «performance».
- Убирай «hedging»: убирай «may», если только не действительно неуверен.
- Сохраняй согласованность терминологии.
- Избегай «incremental vocabulary»: «develop», а не «combine».

Полный гайд с примерами: см. [references/writing-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/writing-guide.md)

### Использование LaTeX‑шаблонов

**Всегда сначала копируй весь каталог шаблона, а потом работай внутри него.**

```
Template Setup Checklist:
- [ ] Step 1: Copy entire template directory to new project
- [ ] Step 2: Verify template compiles as-is (before any changes)
- [ ] Step 3: Read the template's example content to understand structure
- [ ] Step 4: Replace example content section by section
- [ ] Step 5: Use template macros (check preamble for \newcommand definitions)
- [ ] Step 6: Clean up template artifacts only at the end
```

**Шаг 1: Скопировать полный шаблон**

```bash
cp -r templates/neurips2025/ ~/papers/my-paper/
cd ~/papers/my-paper/
ls -la  # Should see: main.tex, neurips.sty, Makefile, etc.
```

Копируй **весь** каталог, а не только файл `.tex`. Шаблоны включают файлы стилей (`.sty`), стили библиографии (`.bst`), примерный контент и Make‑файлы.

**Шаг 2: Убедиться, что шаблон компилируется**

Перед любыми изменениями:
```bash
latexmk -pdf main.tex
# Or manual: pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

Если оригинальный шаблон не компилируется, исправь это в первую очередь (чаще всего не хватает пакетов — ставь их через `tlmgr install <package>`).

**Шаг 3: Сохранять контент шаблона как справку**

Не удаляй примерный контент сразу. Закомментируй его и используй как образец форматирования:
```latex
% Template example (keep for reference):
% \begin{figure}[t]
%   \centering
%   \includegraphics[width=0.8\linewidth]{example-image}
%   \caption{Template shows caption style}
% \end{figure}

% Your actual figure:
\begin{figure}[t]
  \centering
  \includegraphics[width=0.8\linewidth]{your-figure.pdf}
  \caption{Your caption following the same style.}
\end{figure}
```

**Шаг 4: Заменять содержимое по секциям**

Последовательно: title/authors → abstract → introduction → methods → experiments → related work → conclusion → references → appendix. Компилируй после каждой секции.

**Шаг 5: Пользоваться макросами шаблона**

```latex
\newcommand{\method}{YourMethodName}  % Consistent method naming
\newcommand{\eg}{e.g.,\xspace}        % Proper abbreviations
\newcommand{\ie}{i.e.,\xspace}
```

### Подводные камни шаблонов

| Проблема | Что происходит | Как решить |
|----------|----------------|------------|
| Копирование только `.tex` | Отсутствуют `.sty`, не компилируется | Копировать весь каталог |
| Правка `.sty` файлов | Нарушает формат конференции | Никогда не менять файлы стилей |
| Добавление произвольных пакетов | Конфликты, ломает шаблон | Добавляй только при необходимости |
| Удаление контента шаблона слишком рано | Потеря справки по форматированию | Оставляй как комментарии до завершения |
| Редко компилировать | Ошибки накапливаются | Компилируй после каждой секции |
| Растровые PNG для фигур | Размыто в печати | Всегда используй векторный PDF (`savefig('fig.pdf')`) |

### Быстрая справка по шаблонам

| Конференция | Главный файл | Файл стиля | Лимит страниц |
|------------|--------------|------------|----------------|
| NeurIPS 2025 | `main.tex` | `neurips.sty` | 9 стр. |
| ICML 2026 | `example_paper.tex` | `icml2026.sty` | 8 стр. |
| ICLR 2026 | `iclr2026_conference.tex` | `iclr2026_conference.sty` | 9 стр. |
| ACL 2025 | `acl_latex.tex` | `acl.sty` | 8 стр. (long) |
| AAAI 2026 | `aaai2026-unified-template.tex` | `aaai2026.sty` | 7 стр. |
| COLM 2025 | `colm2025_conference.tex` | `colm2025_conference.sty` | 9 стр. |

**Общее:** двойное слепое рецензирование, ссылки не учитываются в лимите, appendix — неограничен, LaTeX обязателен.

Шаблоны находятся в каталоге `templates/`. См. [templates/README.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/templates/README.md) для настройки компиляции (VS Code, CLI, Overleaf, другие IDE).

### Таблицы и фигуры

**Таблицы** — используй пакет `booktabs` для профессионального вида:

```latex
\usepackage{booktabs}
\begin{tabular}{lcc}
\toprule
Method & Accuracy $\uparrow$ & Latency $\downarrow$ \\
\midrule
Baseline & 85.2 & 45ms \\
\textbf{Ours} & \textbf{92.1} & 38ms \\
\bottomrule
\end{tabular}
```

Правила:
- Жирным выделяй лучшее значение по метрике
- Добавляй символы направления ($\uparrow$ — выше лучше, $\downarrow$ — ниже лучше)
- Выравнивай числовые колонки по правому краю
- Сохраняй одинаковую точность десятичных знаков

**Фигуры**:
- **Векторная графика** (PDF, EPS) для всех графиков и схем — `plt.savefig('fig.pdf')`
- **Растровая** (PNG 600 DPI) только для фотографий
- **Палитры, безопасные для дальтоников** (Okabe‑Ito или Paul Tol)
- Проверяй **читаемость в градациях серого** (≈8 % мужчин имеют дефицит цветового зрения)
- **Без заголовка внутри фигуры** — подпись выполняет эту функцию
- **Самодостаточные подписи** — читатель должен понять без основного текста

### Переподача на другую конференцию

Для конвертации между площадками см. Phase 7 (Submission Preparation) — там описан полный workflow конверсии, таблица изменения лимитов страниц и рекомендации после отказа.

### Профессиональный LaTeX‑преамбул

Добавь эти пакеты в любую статью для профессионального качества. Они совместимы со всеми крупными стилями конференций:

```latex
% --- Professional Packages (add after conference style file) ---

% Typography
\usepackage{microtype}              % Microtypographic improvements (protrusion, expansion)
                                     % Makes text noticeably more polished — always include

% Tables
\usepackage{booktabs}               % Professional table rules (\toprule, \midrule, \bottomrule)
\usepackage{siunitx}                % Consistent number formatting, decimal alignment
                                     % Usage: \num{12345} → 12,345; \SI{3.5}{GHz} → 3.5 GHz
                                     % Table alignment: S column type for decimal-aligned numbers

% Figures
\usepackage{graphicx}               % Include graphics (\includegraphics)
\usepackage{subcaption}             % Subfigures with (a), (b), (c) labels
                                     % Usage: \begin{subfigure}{0.48\textwidth} ... \end{subfigure}

% Diagrams and Algorithms
\usepackage{tikz}                   % Programmable vector diagrams
\usetikzlibrary{arrows.meta, positioning, shapes.geometric, calc, fit, backgrounds}
\usepackage[ruled,vlined]{algorithm2e}  % Professional pseudocode
                                     % Alternative: \usepackage{algorithmicx} if template bundles it

% Cross-references
\usepackage{cleveref}               % Smart references: \cref{fig:x} → "Figure 1"
                                     % MUST be loaded AFTER hyperref
                                     % Handles: figures, tables, sections, equations, algorithms

% Math (usually included by conference .sty, but verify)
\usepackage{amsmath,amssymb}        % AMS math environments and symbols
\usepackage{mathtools}              % Extends amsmath (dcases, coloneqq, etc.)

% Colors (for figures and diagrams)
\usepackage{xcolor}                 % Color management
% Okabe-Ito colorblind-safe palette:
\definecolor{okblue}{HTML}{0072B2}
\definecolor{okorange}{HTML}{E69F00}
\definecolor{okgreen}{HTML}{009E73}
\definecolor{okred}{HTML}{D55E00}
\definecolor{okpurple}{HTML}{CC79A7}
\definecolor{okcyan}{HTML}{56B4E9}
\definecolor{okyellow}{HTML}{F0E442}
```

**Заметки:**
- `microtype` — самый эффективный пакет для визуального качества; всегда включай.
- `siunitx` — упрощает выравнивание десятичных чисел в таблицах через тип столбца `S`.
- `cleveref` должен загружаться **после** `hyperref`. Большинство `.sty` файлов уже включают `hyperref`, поэтому ставь `cleveref` последним.
- Проверь, не загружает ли шаблон уже какие‑то из этих пакетов (особенно `algorithm`, `amsmath`, `graphicx`). Не дублируй их.

### Выравнивание таблиц с `siunitx`

`siunitx` делает таблицы с большим количеством чисел гораздо читабельнее:

```latex
\begin{tabular}{l S[table-format=2.1] S[table-format=2.1] S[table-format=2.1]}
\toprule
Method & {Accuracy $\uparrow$} & {F1 $\uparrow$} & {Latency (ms) $\downarrow$} \\
\midrule
Baseline         & 85.2  & 83.7  & 45.3 \\
Ablation (no X)  & 87.1  & 85.4  & 42.1 \\
\textbf{Ours}    & \textbf{92.1} & \textbf{90.8} & \textbf{38.7} \\
\bottomrule
\end{tabular}
```

Тип столбца `S` автоматически выравнивает по десятичной точке. Заголовки в `{}` экранируют выравнивание.

### Подфигуры

Стандартный шаблон для фигур рядом:

```latex
\begin{figure}[t]
  \centering
  \begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{fig_results_a.pdf}
    \caption{Results on Dataset A.}
    \label{fig:results-a}
  \end{subfigure}
  \hfill
  \begin{subfigure}[b]{0.48\textwidth}
    \centering
    \includegraphics[width=\textwidth]{fig_results_b.pdf}
    \caption{Results on Dataset B.}
    \label{fig:results-b}
  \end{subfigure}
  \caption{Comparison of our method across two datasets. (a) shows the scaling
  behavior and (b) shows the ablation results. Both use 5 random seeds.}
  \label{fig:results}
\end{figure}
```

Используй `\cref{fig:results}` → «Figure 1», `\cref{fig:results-a}` → «Figure 1a».

### Псевдокод с `algorithm2e`

```latex
\begin{algorithm}[t]
\caption{Iterative Refinement with Judge Panel}
\label{alg:method}
\KwIn{Task $T$, model $M$, judges $J_1 \ldots J_n$, convergence threshold $k$}
\KwOut{Final output $A^*$}
$A \gets M(T)$ \tcp*{Initial generation}
$\text{streak} \gets 0$\;
\While{$\text{streak} < k$}{
  $C \gets \text{Critic}(A, T)$ \tcp*{Identify weaknesses}
  $B \gets M(T, C)$ \tcp*{Revised version addressing critique}
  $AB \gets \text{Synthesize}(A, B)$ \tcp*{Merge best elements}
  \ForEach{judge $J_i$}{
    $\text{rank}_i \gets J_i(\text{shuffle}(A, B, AB))$ \tcp*{Blind ranking}
  }
  $\text{winner} \gets \text{BordaCount}(\text{ranks})$\;
  \eIf{$\text{winner} = A$}{
    $\text{streak} \gets \text{streak} + 1$\;
  }{
    $A \gets \text{winner}$; $\text{streak} \gets 0$\;
  }
}
\Return{$A$}\;
\end{algorithm}
```

### Шаблоны диаграмм TikZ

TikZ — стандарт для методических диаграмм в ML‑статьях. Часто используемые шаблоны:

**Pipeline/Flow Diagram** (самый распространённый):

```latex
\begin{figure}[t]
\centering
\begin{tikzpicture}[
  node distance=1.8cm,
  box/.style={rectangle, draw, rounded corners, minimum height=1cm, 
              minimum width=2cm, align=center, font=\small},
  arrow/.style={-{Stealth[length=3mm]}, thick},
]
  \node[box, fill=okcyan!20] (input) {Input\\$x$};
  \node[box, fill=okblue!20, right of=input] (encoder) {Encoder\\$f_\theta$};
  \node[box, fill=okgreen!20, right of=encoder] (latent) {Latent\\$z$};
  \node[box, fill=okorange!20, right of=latent] (decoder) {Decoder\\$g_\phi$};
  \node[box, fill=okred!20, right of=decoder] (output) {Output\\$\hat{x}$};
  
  \draw[arrow] (input) -- (encoder);
  \draw[arrow] (encoder) -- (latent);
  \draw[arrow] (latent) -- (decoder);
  \draw[arrow] (decoder) -- (output);
\end{tikzpicture}
\caption{Architecture overview. The encoder maps input $x$ to latent 
representation $z$, which the decoder reconstructs.}
\label{fig:architecture}
\end{figure}
```

**Comparison/Matrix Diagram** (для вариантов метода):

```latex
\begin{tikzpicture}[
  cell/.style={rectangle, draw, minimum width=2.5cm, minimum height=1cm, 
               align=center, font=\small},
  header/.style={cell, fill=gray!20, font=\small\bfseries},
]
  % Headers
  \node[header] at (0, 0) {Method};
  \node[header] at (3, 0) {Converges?};
  \node[header] at (6, 0) {Quality?};
  % Rows
  \node[cell] at (0, -1) {Single Pass};
  \node[cell, fill=okgreen!15] at (3, -1) {N/A};
  \node[cell, fill=okorange!15] at (6, -1) {Baseline};
  \node[cell] at (0, -2) {Critique+Revise};
  \node[cell, fill=okred!15] at (3, -2) {No};
  \node[cell, fill=okred!15] at (6, -2) {Degrades};
  \node[cell] at (0, -3) {Ours};
  \node[cell, fill=okgreen!15] at (3, -3) {Yes ($k$=2)};
  \node[cell, fill=okgreen!15] at (6, -3) {Improves};
\end{tikzpicture}
```

**Iterative Loop Diagram** (для методов с обратной связью):

```latex
\begin{tikzpicture}[
  node distance=2cm,
  box/.style={rectangle, draw, rounded corners, minimum height=0.8cm, 
              minimum width=1.8cm, align=center, font=\small},
  arrow/.style={-{Stealth[length=3mm]}, thick},
  label/.style={font=\scriptsize, midway, above},
]
  \node[box, fill=okblue!20] (gen) {Generator};
  \node[box, fill=okred!20, right=2.5cm of gen] (critic) {Critic};
  \node[box, fill=okgreen!20, below=1.5cm of $(gen)!0.5!(critic)$] (judge) {Judge Panel};
  
  \draw[arrow] (gen) -- node[label] {output $A$} (critic);
  \draw[arrow] (critic) -- node[label, right] {critique $C$} (judge);
  \draw[arrow] (judge) -| node[label, left, pos=0.3] {winner} (gen);
\end{tikzpicture}
```

### `latexdiff` для отслеживания правок

Необходим для rebuttal — генерирует PDF с пометками изменений между версиями:

```bash
# Install
# macOS: brew install latexdiff (or comes with TeX Live)
# Linux: sudo apt install latexdiff

# Generate diff
latexdiff paper_v1.tex paper_v2.tex > paper_diff.tex
pdflatex paper_diff.tex

# For multi-file projects (with \input{} or \include{})
latexdiff --flatten paper_v1.tex paper_v2.tex > paper_diff.tex
```

Полученный PDF показывает удаления красным зачёркнутым шрифтом и добавления синим — стандартный формат для приложений к rebuttal.

### SciencePlots для matplotlib

Установи и используй для публикационных графиков:

```bash
pip install SciencePlots
```

```python
import matplotlib.pyplot as plt
import scienceplots  # registers styles

# Use science style (IEEE-like, clean)
with plt.style.context(['science', 'no-latex']):
    fig, ax = plt.subplots(figsize=(3.5, 2.5))  # Single-column width
    ax.plot(x, y, label='Ours', color='#0072B2')
    ax.plot(x, y2, label='Baseline', color='#D55E00', linestyle='--')
    ax.set_xlabel('Training Steps')
    ax.set_ylabel('Accuracy')
    ax.legend()
    fig.savefig('paper/fig_results.pdf', bbox_inches='tight')

# Available styles: 'science', 'ieee', 'nature', 'science+ieee'
# Add 'no-latex' if LaTeX is not installed on the machine generating plots
```

**Стандартные размеры фигур** (двухколоночный формат):
- Одна колонка: `figsize=(3.5, 2.5)` — помещается в одну колонку
- Две колонки: `figsize=(7.0, 3.0)` — охватывает обе колонки
- Квадрат: `figsize=(3.5, 3.5)` — для тепловых карт, матриц ошибок
## Этап 6: Само‑оценка и исправление

**Цель**: Смоделировать процесс рецензирования перед отправкой. Выявить слабые места заранее.

### Шаг 6.1: Симуляция рецензий (паттерн «ансамбль»)

Сгенерировать рецензии с разных точек зрения. Ключевой вывод из автоматизированных исследовательских конвейеров (в частности AI‑Scientist от SakanaAI): **ансамблевое рецензирование с мета‑рецензентом даёт гораздо более калиброванную обратную связь, чем один проход**.

**Шаг 1: Сгенерировать N независимых рецензий** (N = 3‑5)
Использовать разные модели или настройки `temperature`. Каждый рецензент видит только статью, без других рецензий. **По умолчанию — негативный уклон** — у LLM известна положительная предвзятость в оценке.

```
You are an expert reviewer for [VENUE]. You are critical and thorough.
If a paper has weaknesses or you are unsure about a claim, flag it clearly
and reflect that in your scores. Do not give the benefit of the doubt.

Review this paper according to the official reviewer guidelines. Evaluate:

1. Soundness (are claims well-supported? are baselines fair and strong?)
2. Clarity (is the paper well-written? could an expert reproduce it?)
3. Significance (does this matter to the community?)
4. Originality (new insights, not just incremental combination?)

Provide your review as structured JSON:
{
  "summary": "2-3 sentence summary",
  "strengths": ["strength 1", "strength 2", ...],
  "weaknesses": ["weakness 1 (most critical)", "weakness 2", ...],
  "questions": ["question for authors 1", ...],
  "missing_references": ["paper that should be cited", ...],
  "soundness": 1-4,
  "presentation": 1-4,
  "contribution": 1-4,
  "overall": 1-10,
  "confidence": 1-5
}
```

**Шаг 2: Мета‑рецензия (агрегация Area Chair)**
Передать все N рецензий мета‑рецензенту:

```
You are an Area Chair at [VENUE]. You have received [N] independent reviews
of a paper. Your job is to:

1. Identify consensus strengths and weaknesses across reviewers
2. Resolve disagreements by examining the paper directly
3. Produce a meta-review that represents the aggregate judgment
4. Use AVERAGED numerical scores across all reviews

Be conservative: if reviewers disagree on whether a weakness is serious,
treat it as serious until the authors address it.

Reviews:
[review_1]
[review_2]
...
```

**Шаг 3: Цикл рефлексии** (по желанию, 2‑3 раунда)
Каждый рецензент может уточнить свою рецензию после просмотра мета‑рецензии. Использовать ранний терминальный сигнал: если рецензент отвечает «I am done» (без изменений), прекращать итерацию.

**Выбор модели для рецензирования**: Рецензировать лучше всего самой сильной доступной моделью, даже если статья писалась более дешёвой. Модель‑рецензент должна выбираться независимо от модели‑писателя.

**Калибровка few‑shot**: При возможности добавить 1‑2 реальных опубликованных рецензии из целевого конференц‑зала в качестве примеров. Это существенно улучшает калибровку оценок. См. [references/reviewer‑guidelines.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/reviewer-guidelines.md) для примеров рецензий.

### Шаг 6.1b: Визуальный проход рецензии (VLM)

Только текстовая рецензия упускает целый класс проблем: качество фигур, макет, визуальная согласованность. Если есть доступ к модели с возможностями зрения, запусти отдельный **визуальный обзор** скомпилированного PDF:

```
You are reviewing the visual presentation of this research paper PDF.
Check for:
1. Figure quality: Are plots readable? Labels legible? Colors distinguishable?
2. Figure-caption alignment: Does each caption accurately describe its figure?
3. Layout issues: Orphaned section headers, awkward page breaks, figures far from their references
4. Table formatting: Aligned columns, consistent decimal precision, bold for best results
5. Visual consistency: Same color scheme across all figures, consistent font sizes
6. Grayscale readability: Would the figures be understandable if printed in B&W?

For each issue, specify the page number and exact location.
```

Это выявляет проблемы, которые текстовый обзор не поймает: график с нечитаемыми подписями осей, фигура, расположенная на 3‑й странице от первого упоминания, несоответствующая цветовая палитра между Figure 2 и Figure 5, или таблица, явно шире колонки.

### Шаг 6.1c: Проход проверки утверждений

После симулированных рецензий выполнить отдельный проход проверки. Это ловит фактические ошибки, которые могут ускользнуть от рецензентов:

```
Claim Verification Protocol:
1. Extract every factual claim from the paper (numbers, comparisons, trends)
2. For each claim, trace it to the specific experiment/result that supports it
3. Verify the number in the paper matches the actual result file
4. Flag any claim without a traceable source as [VERIFY]
```

Для агентных рабочих процессов: делегировать проверку **свежему суб‑агенту**, который получает только текст статьи и сырые файлы результатов. Свежий контекст предотвращает подтверждающую предвзятость — проверяющий не «помнит», какими должны быть результаты.

### Шаг 6.2: Приоритизация обратной связи

После сбора рецензий классифицировать:

| Приоритет | Действие |
|-----------|----------|
| **Критический** (технический дефект, отсутствие базовой линии) | Обязательно исправить. Может потребовать новых экспериментов → возврат к Этапу 2 |
| **Высокий** (проблема ясности, отсутствие абляции) | Следует исправить в этой версии |
| **Средний** (незначительные стилистические проблемы, дополнительные эксперименты) | Исправить, если есть время |
| **Низкий** (стилевые предпочтения, отдалённые предложения) | Отметить для будущей работы |

### Шаг 6.3: Цикл исправлений

Для каждой критической/высокой проблемы:
1. Определить конкретный раздел(ы), затронутый(ые)
2. Составить план исправления
3. Проверить, что исправление не нарушает другие утверждения
4. Обновить статью
5. Перепроверить в соответствии с замечанием рецензента

### Шаг 6.4: Написание ответа (rebuttal)

При ответе на реальные рецензии (после подачи) ответы — отдельный навык, отличающийся от исправлений:

**Формат**: По пунктам. Для каждого замечания рецензента:
```
> R1-W1: "The paper lacks comparison with Method X."

We thank the reviewer for this suggestion. We have added a comparison with 
Method X in Table 3 (revised). Our method outperforms X by 3.2pp on [metric] 
(p<0.05). We note that X requires 2x our compute budget.
```

**Правила**:
- Ответить на каждое замечание — рецензенты замечают, если что‑то пропущено
- Начинать с самых сильных ответов
- Быть лаконичным и прямым — рецензенты читают десятки ответов
- Включать новые результаты, если они были получены в период ответа
- Никогда не быть оборонительным или пренебрежительным, даже к слабой критике
- Использовать `latexdiff` для создания помечённого PDF с изменениями (см. раздел «Professional LaTeX Tooling»)
- Благодарить рецензентов за конкретные, практические замечания (а не за общую похвалу)

**Что НЕ делать**: «Мы с уважением не согласны» без доказательств. «Это выходит за рамки» без объяснения. Игнорировать слабость, отвечая только на сильные стороны.

### Шаг 6.5: Отслеживание эволюции статьи

Сохранять снимки состояния на ключевых этапах:
```
paper/
  paper.tex                    # Current working version
  paper_v1_first_draft.tex     # First complete draft
  paper_v2_post_review.tex     # After simulated review
  paper_v3_pre_submission.tex  # Final before submission
  paper_v4_camera_ready.tex    # Post-acceptance final
```

---
## Phase 7: Подготовка к отправке

**Goal**: Финальные проверки, форматирование и отправка.

### Step 7.1: Чеклист конференции

У каждой площадки есть обязательные чеклисты. Заполняй их внимательно — неполные чеклисты могут привести к отклонению на этапе desk‑review.

См. [references/checklists.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/checklists.md) для:
- 16‑пунктового чеклиста статей NeurIPS
- Broader Impact + reproducibility ICML
- Политика раскрытия LLM ICLR
- Обязательный раздел Limitations ACL
- Универсальный чеклист перед отправкой

### Step 7.2: Чеклист анонимизации

Double‑blind review подразумевает, что рецензенты не знают, кто написал статью. Проверь **ВСЁ** из следующего списка:

```
Anonymization Checklist:
- [ ] No author names or affiliations anywhere in the PDF
- [ ] No acknowledgments section (add after acceptance)
- [ ] Self-citations written in third person: "Smith et al. [1] showed..." not "We previously showed [1]..."
- [ ] No GitHub/GitLab URLs pointing to your personal repos
- [ ] Use Anonymous GitHub (https://anonymous.4open.science/) for code links
- [ ] No institutional logos or identifiers in figures
- [ ] No file metadata containing author names (check PDF properties)
- [ ] No "our previous work" or "in our earlier paper" phrasing
- [ ] Dataset names don't reveal institution (rename if needed)
- [ ] Supplementary materials don't contain identifying information
```

**Типичные ошибки**: сообщения коммитов Git, видимые в дополнительном коде; фигурки с водяными знаками от институциональных инструментов; благодарности, оставшиеся из предыдущего черновика; preprint на arXiv, опубликованный до периода анонимности.

### Step 7.3: Проверка форматирования

```
Pre-Submission Format Check:
- [ ] Page limit respected (excluding references and appendix)
- [ ] All figures are vector (PDF) or high-res raster (600 DPI PNG)
- [ ] All figures readable in grayscale
- [ ] All tables use booktabs
- [ ] References compile correctly (no "?" in citations)
- [ ] No overfull hboxes in critical areas
- [ ] Appendix clearly labeled and separated
- [ ] Required sections present (limitations, broader impact, etc.)
```

### Step 7.4: Предварительная проверка компиляции

Запусти эти автоматические проверки **до** попытки `pdflatex`. Выявление ошибок на этом этапе быстрее, чем отладка вывода компилятора.

```bash
# 1. Lint with chktex (catches common LaTeX mistakes)
# Suppress noisy warnings: -n2 (sentence end), -n24 (parens), -n13 (intersentence), -n1 (command terminated)
chktex main.tex -q -n2 -n24 -n13 -n1

# 2. Verify all citations exist in .bib
# Extract \cite{...} from .tex, check each against .bib
python3 -c "
import re
tex = open('main.tex').read()
bib = open('references.bib').read()
cites = set(re.findall(r'\\\\cite[tp]?{([^}]+)}', tex))
for cite_group in cites:
    for cite in cite_group.split(','):
        cite = cite.strip()
        if cite and cite not in bib:
            print(f'WARNING: \\\\cite{{{cite}}} not found in references.bib')
"

# 3. Verify all referenced figures exist on disk
python3 -c "
import re, os
tex = open('main.tex').read()
figs = re.findall(r'\\\\includegraphics(?:\[.*?\])?{([^}]+)}', tex)
for fig in figs:
    if not os.path.exists(fig):
        print(f'WARNING: Figure file not found: {fig}')
"

# 4. Check for duplicate \label definitions
python3 -c "
import re
from collections import Counter
tex = open('main.tex').read()
labels = re.findall(r'\\\\label{([^}]+)}', tex)
dupes = {k: v for k, v in Counter(labels).items() if v > 1}
for label, count in dupes.items():
    print(f'WARNING: Duplicate label: {label} (appears {count} times)')
"
```

Исправь все предупреждения перед продолжением. Для агентных рабочих процессов: передай вывод `chktex` обратно агенту с инструкциями выполнить минимальные исправления.

### Step 7.5: Финальная компиляция

```bash
# Clean build
rm -f *.aux *.bbl *.blg *.log *.out *.pdf
latexmk -pdf main.tex

# Or manual (triple pdflatex + bibtex for cross-references)
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex

# Verify output exists and has content
ls -la main.pdf
```

**Если компиляция не удалась**: проанализируй файл `.log` и найди первую ошибку. Типичные исправления:
- «Undefined control sequence» → отсутствует пакет или опечатка в названии команды
- «Missing $ inserted» → математический символ вне математического режима
- «File not found» → неверный путь к фигурке или отсутствует файл `.sty`
- «Citation undefined» → отсутствует запись в `.bib` или не запущен `bibtex`

### Step 7.6: Требования конкретных конференций

| Venue | Special Requirements |
|-------|---------------------|
| **NeurIPS** | Чеклист статьи в приложении, lay summary, если принята |
| **ICML** | Broader Impact Statement (после заключения, не считается в лимит) |
| **ICLR** | Требуется раскрытие LLM, соглашение о взаимном рецензировании |
| **ACL** | Обязательный раздел Limitations, чеклист Responsible NLP |
| **AAAI** | Строгий style‑file — без каких‑либо модификаций |
| **COLM** | Оформить вклад для сообщества языковых моделей |

### Step 7.7: Переподача и конверсия формата

При переходе между площадками **никогда не копируй LaTeX‑преамбулу из одного шаблона в другой**:

```bash
# 1. Start fresh with target template
cp -r templates/icml2026/ new_submission/

# 2. Copy ONLY content sections (not preamble)
#    - Abstract text, section content, figures, tables, bib entries

# 3. Adjust for page limits
# 4. Add venue-specific required sections
# 5. Update references
```

| From → To | Page Change | Key Adjustments |
|-----------|-------------|-----------------|
| NeurIPS → ICML | 9 → 8 | Убрать 1 страницу, добавить Broader Impact |
| ICML → ICLR | 8 → 9 | Расширить эксперименты, добавить раскрытие LLM |
| NeurIPS → ACL | 9 → 8 | Перестроить под конвенции NLP, добавить Limitations |
| ICLR → AAAI | 9 → 7 | Сильные сокращения, строгая стилистика |
| Any → COLM | varies → 9 | Переформатировать под фокус на языковые модели |

При сокращении страниц: переноси доказательства в приложение, сокращай Related Work, объединяй таблицы, используй subfigures.
При расширении: добавляй абляции, расширяй раздел Limitations, включай дополнительные baselines, добавляй качественные примеры.

**После отклонения**: учти замечания рецензентов в новой версии, но не включай раздел «changes» и не ссылайся на предыдущую отправку (слепой рецензент).

### Step 7.8: Подготовка camera‑ready (после принятия)

После принятия подготовь финальную camera‑ready версию:

```
Camera-Ready Checklist:
- [ ] De-anonymize: add author names, affiliations, email addresses
- [ ] Add Acknowledgments section (funding, compute grants, helpful reviewers)
- [ ] Add public code/data URL (real GitHub, not anonymous)
- [ ] Address any mandatory revisions from meta-reviewer
- [ ] Switch template to camera-ready mode (if applicable — e.g., AAAI \anon → \camera)
- [ ] Add copyright notice if required by venue
- [ ] Update any "anonymous" placeholders in text
- [ ] Verify final PDF compiles cleanly
- [ ] Check page limit for camera-ready (sometimes differs from submission)
- [ ] Upload supplementary materials (code, data, appendix) to venue portal
```

### Step 7.9: Стратегия arXiv & preprint

Размещение на arXiv — обычная практика в ML, но имеет важные нюансы по таймингу и анонимности.

**Дерево решений по таймингу:**

| Situation | Recommendation |
|-----------|----------------|
| Отправка в double‑blind venue (NeurIPS, ICML, ACL) | Публикуй в arXiv **после** дедлайна подачи, а не раньше. Публикация до этого может нарушать политику анонимности, хотя степень её применения варьируется. |
| Отправка в ICLR | ICLR явно разрешает размещение на arXiv до подачи. Но не указывай имена авторов в самой подаче. |
| Статья уже на arXiv, подаёшь в новую площадку | Приемлемо почти во всех конференциях. НЕ обновляй версию arXiv во время рецензирования, если изменения ссылаются на отзывы. |
| Workshop paper | arXiv допустим в любое время — воркшопы обычно не double‑blind. |
| Хочешь закрепить приоритет | Публикуй сразу, если есть риск «скоупинга», но учитывай компромисс с анонимностью. |

**Выбор категории arXiv** (ML/AI статьи):

| Category | Code | Best For |
|----------|------|----------|
| Machine Learning | `cs.LG` | Общие методы ML |
| Computation and Language | `cs.CL` | NLP, языковые модели |
| Artificial Intelligence | `cs.AI` | Рассуждения, планирование, агенты |
| Computer Vision | `cs.CV` | Визуальные модели |
| Information Retrieval | `cs.IR` | Поиск, рекомендации |

Укажи основную + 1‑2 кросс‑листинговые категории. Больше категорий — больше видимости, но кросс‑листинг делай только при реальной релевантности.

**Стратегия версионирования:**
- **v1**: Первичная подача (соответствует конференц‑submission)
- **v2**: После принятия с исправлениями camera‑ready (добавь «accepted at [Venue]» в аннотацию)
- Не публикуй v2 в период рецензирования с изменениями, явно отвечающими на отзывы

```bash
# Check if your paper's title is already taken on arXiv
# (before choosing a title)
pip install arxiv
python -c "
import arxiv
results = list(arxiv.Search(query='ti:\"Your Exact Title\"', max_results=5).results())
print(f'Found {len(results)} matches')
for r in results: print(f'  {r.title} ({r.published.year})')
"
```

### Step 7.10: Пакетирование исследовательского кода

Публикация чистого, запускаемого кода значительно повышает количество цитирований и доверие рецензентов. Пакетируй код вместе с camera‑ready подачей.

**Структура репозитория:**

```
your-method/
  README.md              # Setup, usage, reproduction instructions
  requirements.txt       # Or environment.yml for conda
  setup.py               # For pip-installable packages
  LICENSE                # MIT or Apache 2.0 recommended for research
  configs/               # Experiment configurations
  src/                   # Core method implementation
  scripts/               # Training, evaluation, analysis scripts
    train.py
    evaluate.py
    reproduce_table1.sh  # One script per main result
  data/                  # Small data or download scripts
    download_data.sh
  results/               # Expected outputs for verification
```

**Шаблон README для исследовательского кода:**

```markdown
# [Paper Title]

Official implementation of "[Paper Title]" (Venue Year).

## Setup
[Exact commands to set up environment]

## Reproduction
To reproduce Table 1: `bash scripts/reproduce_table1.sh`
To reproduce Figure 2: `python scripts/make_figure2.py`

## Citation
[BibTeX entry]
```

**Чеклист перед релизом:**
```
- [ ] Code runs from a clean clone (test on fresh machine or Docker)
- [ ] All dependencies pinned to specific versions
- [ ] No hardcoded absolute paths
- [ ] No API keys, credentials, or personal data in repo
- [ ] README covers setup, reproduction, and citation
- [ ] LICENSE file present (MIT or Apache 2.0 for max reuse)
- [ ] Results are reproducible within expected variance
- [ ] .gitignore excludes data files, checkpoints, logs
```

**Анонимный код для подачи** (до принятия):
```bash
# Use Anonymous GitHub for double-blind review
# https://anonymous.4open.science/
# Upload your repo → get an anonymous URL → put in paper
```
## Phase 8: Post-Acceptance Deliverables

**Goal**: Maximize the impact of your accepted paper through presentation materials and community engagement.

### Step 8.1: Conference Poster

Most conferences require a poster session. Poster design principles:

| Element | Guideline |
|---------|-----------|
| **Size** | Check venue requirements (typically 24"x36" or A0 portrait/landscape) |
| **Content** | Title, authors, 1‑sentence contribution, method figure, 2‑3 key results, conclusion |
| **Flow** | Top‑left to bottom‑right (Z‑pattern) or columnar |
| **Text** | Title readable at 3 m, body at 1 m. No full paragraphs — bullet points only. |
| **Figures** | Reuse paper figures at higher resolution. Enlarge key result. |

**Tools**: LaTeX (`beamerposter` package), PowerPoint/Keynote, Figma, Canva.

**Production**: Order 2 + weeks before the conference. Fabric posters are lighter for travel. Many conferences now support virtual/digital posters too.

### Step 8.2: Conference Talk / Spotlight

If awarded an oral or spotlight presentation:

| Talk Type | Duration | Content |
|-----------|----------|---------|
| **Spotlight** | 5 min | Problem, approach, one key result. Rehearse to exactly 5 minutes. |
| **Oral** | 15‑20 min | Full story: problem, approach, key results, ablations, limitations. |
| **Workshop talk** | 10‑15 min | Adapt based on workshop audience — may need more background. |

**Slide design rules:**
- One idea per slide
- Minimize text — speak the details, don’t project them
- Animate key figures to build understanding step‑by‑step
- Include a “takeaway” slide at the end (single‑sentence contribution)
- Prepare backup slides for anticipated questions

### Step 8.3: Blog Post / Social Media

An accessible summary significantly increases impact:

- **Twitter/X thread**: 5‑8 tweets. Lead with the result, not the method. Include Figure 1 and key‑result figure.
- **Blog post**: 800‑1500 words. Written for ML practitioners, not reviewers. Skip formalism, emphasize intuition and practical implications.
- **Project page**: HTML page with abstract, figures, demo, code link, BibTeX. Use GitHub Pages.

**Timing**: Post within 1‑2 days of paper appearing in the proceedings or on arXiv camera‑ready.
## Workshop и короткие статьи

Статьи для воркшопов и короткие статьи (например, короткие статьи ACL, статьи Findings) проходят одинаковый процесс подачи, но имеют разные ограничения и ожидания.

### Статьи для воркшопов

| Свойство | Воркшоп | Основная конференция |
|----------|----------|----------------------|
| **Ограничение по страницам** | 4‑6 страниц (обычно) | 7‑9 страниц |
| **Требования к обзору** | Ниже планка полноты | Должна быть полной и тщательной |
| **Процесс рецензирования** | Обычно single‑blind или лёгкий обзор | Double‑blind, строгий |
| **Что ценится** | Интересные идеи, предварительные результаты, позиционные статьи | Полная эмпирическая история с сильными базовыми моделями |
| **arXiv** | Публикация в любое время | Время публикации имеет значение (см. стратегию arXiv) |
| **Порог вклада** | Новое направление, интересный отрицательный результат, работа в процессе | Значительный прорыв с убедительными доказательствами |

**Когда стоит выбирать воркшоп:**
- Идея на ранней стадии, для которой нужен фидбэк перед полной статьёй
- Отрицательный результат, не требующий 8 + страниц
- Позиционная статья или мнение по актуальной теме
- Репликационное исследование или отчёт о воспроизводимости

### Короткие статьи ACL и Findings

У конференций ACL есть отдельные типы подач:

| Тип | Страниц | Что ожидается |
|------|---------|----------------|
| **Long paper** | 8 | Полное исследование, сильные базовые модели, абляции |
| **Short paper** | 4 | Сфокусированный вклад: один чёткий пункт, подкреплённый доказательствами |
| **Findings** | 8 | Качественная работа, чуть не попавшая в основную конференцию |

**Стратегия для короткой статьи**: выбрать ОДНО утверждение и тщательно его обосновать. Не пытайся уместить материал длинной статьи в 4 страницы — напиши отдельную, более сфокусированную работу.
## Типы статей, выходящие за рамки эмпирического ML

Основной конвейер выше ориентирован на эмпирические статьи по ML. Другие типы статей требуют иной структуры и стандартов доказательств. См. [references/paper-types.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/paper-types.md) для подробных рекомендаций по каждому типу.

### Теоретические статьи

**Структура**: Introduction → Preliminaries (definitions, notation) → Main Results (theorems) → Proof Sketches → Discussion → Full Proofs (appendix)

**Ключевые отличия от эмпирических статей:**
- Вклад — теорема, граница или результат невозможности, а не экспериментальные цифры
- Раздел *Methods* заменён на «Preliminaries» и «Main Results»
- Доказательства являются доказательством, а не экспериментами (хотя эмпирическая проверка теории приветствуется)
- Краткие доказательства в основном тексте, полные доказательства в приложении — стандартная практика
- Экспериментальный раздел необязателен, но усиливает статью, если подтверждает теоретические предсказания

**Принципы написания доказательств:**
- Формально формулируй теоремы, делая все предположения явными
- Дай интуицию перед формальным доказательством («Ключевая идея…»)
- Краткие доказательства должны передавать основную идею на 0,5–1 странице
- Используй окружения `\begin{proof}...\end{proof}`
- Нумеруй предположения и ссылайся на них в теоремах: «При предположениях 1‑3, …»

### Обзорные / учебные статьи

**Структура**: Introduction → Taxonomy / Organization → Detailed Coverage → Open Problems → Conclusion

**Ключевые отличия:**
- Вклад — организация, синтез и выявление открытых проблем, а не новые методы
- Должна быть всесторонней в рамках выбранного охвата (рецензенты проверят отсутствие ссылок)
- Требуется чёткая таксономия или организационная структура
- Ценность заключается в связях между работами, которые отдельные статьи не делают
- Лучшие площадки: TMLR (survey track), JMLR, Foundations and Trends in ML, ACM Computing Surveys

### Статьи о бенчмарках

**Структура**: Introduction → Task Definition → Dataset Construction → Baseline Evaluation → Analysis → Intended Use & Limitations

**Ключевые отличия:**
- Вклад — сам бенчмарк — он должен заполнять реальный пробел в оценке
- Документация набора данных обязательна, а не опциональна (см. Datasheets, Step 5.11)
- Нужно показать, что бенчмарк сложен (базовые модели не достигают насыщения)
- Нужно продемонстрировать, что бенчмарк измеряет то, что заявлено (конструктная валидность)
- Лучшие площадки: NeurIPS Datasets & Benchmarks track, ACL (resource papers), LREC‑COLING

### Позиционные статьи

**Структура**: Introduction → Background → Thesis / Argument → Supporting Evidence → Counterarguments → Implications

**Ключевые отличия:**
- Вклад — аргумент, а не результат
- Необходимо серьёзно учитывать контраргументы
- Доказательства могут быть эмпирическими, теоретическими или логическим анализом
- Лучшие площадки: ICML (position track), воркшопы, TMLR
## Интеграция Hermes Agent

Этот навык предназначен для агента Hermes. Он использует инструменты Hermes, делегирование, планирование и память для полного жизненного цикла исследования.

### Связанные навыки

Сочетай этот навык с другими навыками Hermes для конкретных фаз:

| Навык | Когда использовать | Как загрузить |
|-------|--------------------|---------------|
| **arxiv** | Фаза 1 (Обзор литературы): поиск по arXiv, генерация BibTeX, поиск связанных статей через Semantic Scholar | `skill_view("arxiv")` |
| **subagent-driven-development** | Фаза 5 (Написание черновика): параллельное написание разделов с двухэтапным рецензированием (соответствие спецификации, затем качество) | `skill_view("subagent-driven-development")` |
| **plan** | Фаза 0 (Подготовка): создание структурированных планов перед выполнением. Записывается в `.hermes/plans/` | `skill_view("plan")` |
| **qmd** | Фаза 1 (Литература): поиск по локальным базам знаний (заметки, транскрипты, документы) с гибридным поиском BM25 + vector | Install: `skill_manage("install", "qmd")` |
| **diagramming** | Фазы 4‑5: создание фигур и архитектурных диаграмм на основе Excalidraw | `skill_view("diagramming")` |
| **data-science** | Фаза 4 (Анализ): живое ядро Jupyter для интерактивного анализа и визуализации | `skill_view("data-science")` |

**Этот навык заменяет `ml-paper-writing`** — он содержит весь контент `ml-paper-writing` плюс полный конвейер экспериментов/анализа и методологию автодоказательства.

### Справочник инструментов Hermes

| Инструмент | Использование в этом конвейере |
|------------|---------------------------------|
| **`terminal`** | Компиляция LaTeX (`latexmk -pdf`), операции git, запуск экспериментов (`nohup python run.py &`), проверка процессов |
| **`process`** | Управление фоновыми экспериментами: `process("start", ...)`, `process("poll", pid)`, `process("log", pid)`, `process("kill", pid)` |
| **`execute_code`** | Запуск Python для проверки цитат, статистического анализа, агрегации данных. Имеет доступ к инструментам через RPC. |
| **`read_file`** / **`write_file`** / **`patch`** | Редактирование статьи, скриптов экспериментов, файлов результатов. `patch` используется для целевых правок больших `.tex`‑файлов. |
| **`web_search`** | Поиск литературы: `web_search("transformer attention mechanism 2024")` |
| **`web_extract`** | Получение содержимого статьи, проверка цитат: `web_extract("https://arxiv.org/abs/2303.17651")` |
| **`delegate_task`** | **Параллельное написание разделов** — создание изолированных субагентов для каждого раздела. Также для одновременной проверки цитат. |
| **`todo`** | Основной трекер состояния между сессиями. Обновляется после каждой смены фазы. |
| **`memory`** | Сохранение ключевых решений между сессиями: формулировка вклада, выбор места публикации, отзывы рецензентов. |
| **`cronjob`** | Планирование мониторинга экспериментов, обратного отсчёта дедлайнов, автоматических проверок arXiv. |
| **`clarify`** | Задавать пользователю целевые вопросы при блокировке (выбор места публикации, формулировка вклада). |
| **`send_message`** | Уведомлять пользователя, когда эксперименты завершены или черновики готовы, даже если пользователь не находится в чате. |

### Шаблоны использования инструментов

**Мониторинг экспериментов** (самый распространённый):
```
terminal("ps aux | grep <pattern>")
→ terminal("tail -30 <logfile>")
→ terminal("ls results/")
→ execute_code("analyze results JSON, compute metrics")
→ terminal("git add -A && git commit -m '<descriptive message>' && git push")
→ send_message("Experiment complete: <summary>")
```

**Параллельное написание разделов** (с делегированием):
```
delegate_task("Draft the Methods section based on these experiment scripts and configs. 
  Include: pseudocode, all hyperparameters, architectural details sufficient for 
  reproduction. Write in LaTeX using the neurips2025 template conventions.")

delegate_task("Draft the Related Work section. Use web_search and web_extract to 
  find papers. Verify every citation via Semantic Scholar. Group by methodology.")

delegate_task("Draft the Experiments section. Read all result files in results/. 
  State which claim each experiment supports. Include error bars and significance.")
```

Каждый делегат работает как **новый субагент** без общего контекста — предоставляй всю необходимую информацию в подсказке. Собирай выводы и интегрируй их.

**Проверка цитат** (с `execute_code`):
```python
# In execute_code:
from semanticscholar import SemanticScholar
import requests

sch = SemanticScholar()
results = sch.search_paper("attention mechanism transformers", limit=5)
for paper in results:
    doi = paper.externalIds.get('DOI', 'N/A')
    if doi != 'N/A':
        bibtex = requests.get(f"https://doi.org/{doi}", 
                              headers={"Accept": "application/x-bibtex"}).text
        print(bibtex)
```

### Управление состоянием с помощью `memory` и `todo`

**Инструмент `memory`** — сохраняет ключевые решения (ограничение ≈ 2200 символов для `MEMORY.md`):
```
memory("add", "Paper: autoreason. Venue: NeurIPS 2025 (9 pages). 
  Contribution: structured refinement works when generation-evaluation gap is wide.
  Key results: Haiku 42/42, Sonnet 3/5, S4.6 constrained 2/3.
  Status: Phase 5 — drafting Methods section.")
```

Обновляй память после крупных решений или переходов фаз. Она сохраняется между сессиями.

**Инструмент `todo`** — отслеживает детальный прогресс:
```
todo("add", "Design constrained task experiments for Sonnet 4.6")
todo("add", "Run Haiku baseline comparison")
todo("add", "Draft Methods section")
todo("update", id=3, status="in_progress")
todo("update", id=1, status="completed")
```

**Протокол запуска сессии:**
```
1. todo("list")                           # Check current task list
2. memory("read")                         # Recall key decisions
3. terminal("git log --oneline -10")      # Check recent commits
4. terminal("ps aux | grep python")       # Check running experiments
5. terminal("ls results/ | tail -20")     # Check for new results
6. Report status to user, ask for direction
```

### Мониторинг с `cronjob`

Используй инструмент `cronjob` для планового контроля экспериментов:
```
cronjob("create", {
  "schedule": "*/30 * * * *",  # Every 30 minutes
  "prompt": "Check experiment status:
    1. ps aux | grep run_experiment
    2. tail -30 logs/experiment_haiku.log
    3. ls results/haiku_baselines/
    4. If complete: read results, compute Borda scores, 
       git add -A && git commit -m 'Add Haiku results' && git push
    5. Report: table of results, key finding, next step
    6. If nothing changed: respond with [SILENT]"
})
```

**Протокол `[SILENT]`**: когда с последней проверки ничего не изменилось, отвечай ровно `[SILENT]`. Это подавляет доставку уведомления пользователю. Сообщай только при реальных изменениях, которые стоит знать.

**Отслеживание дедлайнов:**
```
cronjob("create", {
  "schedule": "0 9 * * *",  # Daily at 9am
  "prompt": "NeurIPS 2025 deadline: May 22. Today is {date}. 
    Days remaining: {compute}. 
    Check todo list — are we on track? 
    If <7 days: warn user about remaining tasks."
})
```

### Шаблоны коммуникации

**Когда уведомлять пользователя** (через `send_message` или прямой ответ):
- Завершён пакет экспериментов (с таблицей результатов)
- Неожиданное открытие или ошибка, требующая решения
- Раздел черновика готов к рецензии
- Приближается дедлайн с незавершёнными задачами

**Когда НЕ уведомлять:**
- Эксперимент всё ещё работает, новых результатов нет → `[SILENT]`
- Рутинный мониторинг без изменений → `[SILENT]`
- Промежуточные шаги, не требующие внимания

**Формат отчёта** — всегда включай структурированные данные:
```
## Experiment: <name>
Status: Complete / Running / Failed

| Task | Method A | Method B | Method C |
|------|---------|---------|---------|
| Task 1 | 85.2 | 82.1 | **89.4** |

Key finding: <one sentence>
Next step: <what happens next>
```

### Точки принятия решений, требующие ввода от человека

Используй `clarify` для целевых вопросов, когда действительно заблокирован:

| Решение | Когда спрашивать |
|--------|-------------------|
| Целевое место публикации | Перед началом работы над статьёй (влияет на ограничения по объёму, формулировку) |
| Формулировка вклада | Когда существует несколько валидных формулировок |
| Приоритет экспериментов | Когда список `todo` содержит больше экспериментов, чем времени |
| Готовность к сдаче | Перед окончательной отправкой |

**Не спрашивай** (будь проактивен, принимай решение, отмечай):
- Выбор слов, порядок разделов
- Какие конкретные результаты выделять
- Полноту цитат (делай черновик с тем, что найдено, отмечай пробелы)
## Критерии оценки рецензентов

Понимание того, на что обращают внимание рецензенты, помогает сосредоточить усилия:

| Критерий | Что проверяется |
|-----------|-------------------|
| **Quality** | Техническая обоснованность, хорошо подтверждённые утверждения, справедливые базовые сравнения |
| **Clarity** | Ясность изложения, воспроизводимость экспертами, единообразное обозначение |
| **Significance** | Влияние на сообщество, продвижение понимания |
| **Originality** | Новые инсайты (не требует нового метода) |

**Оценивание (шкала NeurIPS из 6 баллов):**
- 6: Strong Accept — прорывной, безупречный
- 5: Accept — технически солидный, высокий вклад
- 4: Borderline Accept — солидный, ограниченная оценка
- 3: Borderline Reject — недостатки перевешивают
- 2: Reject — технические недостатки
- 1: Strong Reject — известные результаты или этические проблемы

См. [references/reviewer-guidelines.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/reviewer-guidelines.md) для подробных рекомендаций, типовых проблем и стратегий ответа.
## Общие проблемы и решения

| Проблема | Решение |
|-------|----------|
| Аннотация слишком общая | Удали первое предложение, если оно могло бы предшествовать любой работе по **ML**. Начни с конкретного вклада. |
| Введение превышает 1,5 страницы | Раздели фон на раздел **Related Work**. Выдели вклад в начале в виде пунктов. |
| В экспериментах нет явных утверждений | Добавь перед каждым экспериментом фразу: «Этот эксперимент проверяет, что **[конкретное утверждение]**…». |
| Рецензенты считают статью трудной для восприятия | Добавь навигацию, используй единообразную терминологию, сделай подписи к рисункам самодостаточными. |
| Отсутствует статистическая значимость | Добавь полосы ошибок, указание количества запусков, статистические тесты и доверительные интервалы. |
| Расширение объёма экспериментов | Каждый эксперимент должен соответствовать конкретному утверждению. Удали эксперименты, которые этому не соответствуют. |
| Статья отклонена, требуется повторная подача | См. **Conference Resubmission** в Phase 7. Устрани замечания рецензентов, не ссылаясь на их отзывы. |
| Отсутствует заявление о более широком воздействии | См. Step 5.10. Большинство конференций требуют такой раздел. Формулировка «Отрицательных воздействий нет» почти никогда не выглядит правдоподобно. |
| Критика слабой человеческой оценки | См. Step 2.5 и [references/human-evaluation.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/human-evaluation.md). Укажи метрики согласия, детали аннотаторов и их компенсацию. |
| Рецензенты ставят вопросы о воспроизводимости | Выпусти код (Step 7.9), задокументируй все гиперпараметры, включи семена и детали вычислительных ресурсов. |
| Теоретическая статья лишена интуиции | Добавь наброски доказательств с объяснениями простым языком перед формальными доказательствами. См. [references/paper-types.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/paper-types.md). |
| Результаты отрицательные/нуль | См. Phase 4.3 о работе с отрицательными результатами. Рассмотри воркшопы, **TMLR** или переоформление в виде анализа. |
## Справочные документы

| Документ | Содержание |
|----------|------------|
| [references/writing-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/writing-guide.md) | Принципы Gopen & Swan, микро‑советы Perez, выбор слов Lipton, точность Steinhardt, дизайн фигур |
| [references/citation-workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/citation-workflow.md) | API цитирования, код Python, класс `CitationManager`, управление BibTeX |
| [references/checklists.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/checklists.md) | Чек‑лист из 16 пунктов NeurIPS, требования ICML, ICLR, ACL, универсальный чек‑лист перед подачей |
| [references/reviewer-guidelines.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/reviewer-guidelines.md) | Критерии оценки, шкала, типичные замечания, шаблон реплики |
| [references/sources.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/sources.md) | Полная библиография всех руководств по написанию, требований конференций, API |
| [references/experiment-patterns.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/experiment-patterns.md) | Шаблоны проектирования экспериментов, протоколы оценки, мониторинг, восстановление после ошибок |
| [references/autoreason-methodology.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/autoreason-methodology.md) | Цикл Autoreason, выбор стратегии, руководство по модели, подсказки, ограничения области, оценка по методу Борда |
| [references/human-evaluation.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/human-evaluation.md) | Дизайн человеческой оценки, рекомендации по аннотации, метрики согласия, контроль качества краудсорсинга, рекомендации по IRB |
| [references/paper-types.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/paper-types.md) | Теоретические статьи (написание доказательств, структура теорем), обзорные статьи, статьи‑бенчмарки, позиционные статьи |

### Шаблоны LaTeX

Шаблоны в `templates/` для: **NeurIPS 2025**, **ICML 2026**, **ICLR 2026**, **ACL**, **AAAI 2026**, **COLM 2025**.

Смотрите [templates/README.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/templates/README.md) для инструкций по компиляции.

### Ключевые внешние источники

**Философия написания:**
- [Neel Nanda: How to Write ML Papers](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers)
- [Sebastian Farquhar: How to Write ML Papers](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/)
- [Gopen & Swan: Science of Scientific Writing](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf)
- [Lipton: Heuristics for Scientific Writing](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/)
- [Perez: Easy Paper Writing Tips](https://ethanperez.net/easy-paper-writing-tips/)

**API:** [Semantic Scholar](https://api.semanticscholar.org/api-docs/) | [CrossRef](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | [arXiv](https://info.arxiv.org/help/api/basics.html)

**Конференции:** [NeurIPS](https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles) | [ICML](https://icml.cc/Conferences/2025/AuthorInstructions) | [ICLR](https://iclr.cc/Conferences/2026/AuthorGuide) | [ACL](https://github.com/acl-org/acl-style-files)