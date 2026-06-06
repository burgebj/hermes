---
title: "Написання наукових статей — Пиши ML‑статті для NeurIPS/ICML/ICLR: дизайн→подання"
sidebar_label: "Research Paper Writing"
description: "Пиши ML статті для NeurIPS/ICML/ICLR: дизайн→подання"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Написання наукових статей

Пиши статті з ML для NeurIPS, ICML, ICLR: design→submit.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлено за замовчуванням) |
| Шлях | `skills/research/research-paper-writing` |
| Версія | `1.1.0` |
| Автор | Orchestra Research |
| Ліцензія | MIT |
| Залежності | `semanticscholar`, `arxiv`, `habanero`, `requests`, `scipy`, `numpy`, `matplotlib`, `SciencePlots` |
| Платформи | linux, macos |
| Теги | `Research`, `Paper Writing`, `Experiments`, `ML`, `AI`, `NeurIPS`, `ICML`, `ICLR`, `ACL`, `AAAI`, `COLM`, `LaTeX`, `Citations`, `Statistical Analysis` |
| Пов’язані навички | [`arxiv`](/docs/user-guide/skills/bundled/research/research-arxiv), `ml-paper-writing`, [`subagent-driven-development`](/docs/user-guide/skills/bundled/software-development/software-development-subagent-driven-development), [`plan`](/docs/user-guide/skills/bundled/software-development/software-development-plan) |
:::info
Нижче наведено повне визначення навички, яке Hermes завантажує під час її активації. Це інструкції, які бачить агент, коли навичка активна.
:::

# Пайплайн написання наукових статей

Сквозний конвеєр для створення готових до публікації досліджень у галузі ML/AI, орієнтованих на **NeurIPS, ICML, ICLR, ACL, AAAI та COLM**. Ця навичка охоплює весь життєвий цикл дослідження: проєктування експерименту, його виконання, моніторинг, аналіз, написання статті, рецензування, редагування та подання.

Це **не лінійний конвеєр** — це ітеративний цикл. Результати ініціюють нові експерименти. Рецензії ініціюють новий аналіз. Агент має обробляти ці цикли зворотного зв’язку.

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
## Коли використовувати цей skill

Використовуй цей skill, коли:
- **Починаєш нову дослідницьку статтю** з існуючої кодової бази або ідеї
- **Проектуєш та проводиш експерименти** для підтримки тверджень статті
- **Пишеш або редагуєш** будь‑який розділ дослідницької статті
- **Готуєшся до подачі** на конкретну конференцію чи воркшоп
- **Відповідаєш на рецензії** додатковими експериментами або правками
- **Перетворюєш** статтю між форматами конференцій
- **Пишеш неемпіричні статті** — теоретичні, оглядові, бенчмарк‑ або позиційні (див. [Paper Types Beyond Empirical ML](#paper-types-beyond-empirical-ml))
- **Проектуєш людські оцінювання** для NLP, HCI або досліджень вирівнювання
- **Готуєш пост‑акцептні deliverables** — постери, доповіді, випуск коду
## Core Philosophy

1. **Будь проактивним.** Доставляй готові чернетки, а не питання. Вчені зайняті — створюй щось конкретне, на що вони можуть реагувати, а потім ітеративно вдосконалюй.
2. **Ніколи не вигадуй посилань.** AI‑згенеровані посилання мають ~40 % помилок. Завжди отримуй їх програмно. Познач неперевірені посилання як `[CITATION NEEDED]`.
3. **Папір — це історія, а не збірка експериментів.** Кожна стаття потребує одного чіткого внеску, сформульованого в одному реченні. Якщо не вдається це зробити, стаття ще не готова.
4. **Експерименти слугують твердженням.** Кожен експеримент має явно вказувати, яке твердження він підтримує. Не проводь експерименти, які не пов’язані з наративом статті.
5. **Комітити рано, комітити часто.** Кожна завершена партія експериментів, кожне оновлення чернетки статті — коміт з описовим повідомленням. Git‑лог — це історія експерименту.

### Proactivity and Collaboration

**Default: Будь проактивним. Спочатку чернетка, потім питання щодо чернетки.**

| Confidence Level | Action |
|-------------------|--------|
| **High** (clear repo, obvious contribution) | Write full draft, deliver, iterate on feedback |
| **Medium** (some ambiguity) | Write draft with flagged uncertainties, continue |
| **Low** (major unknowns) | Ask 1‑2 targeted questions via `clarify`, then draft |

| Section | Draft Autonomously? | Flag With Draft |
|---------|---------------------|-----------------|
| Abstract | Yes | "Framed contribution as X — adjust if needed" |
| Introduction | Yes | "Emphasized problem Y — correct if wrong" |
| Methods | Yes | "Included details A, B, C — add missing pieces" |
| Experiments | Yes | "Highlighted results 1, 2, 3 — reorder if needed" |
| Related Work | Yes | "Cited papers X, Y, Z — add any I missed" |

**Block for input only when**: target venue unclear, multiple contradictory framings, results seem incomplete, explicit request to review first.
## Phase 0: Налаштування проєкту

**Мета**: Встановити робоче середовище, зрозуміти існуючу роботу, визначити внесок.

### Крок 0.1: Дослідження репозиторію

```bash
# Understand project structure
ls -la
find . -name "*.py" | head -30
find . -name "*.md" -o -name "*.txt" | xargs grep -l -i "result\|conclusion\|finding"
```

Шукай:
- `README.md` — огляд проєкту та заяви
- `results/`, `outputs/`, `experiments/` — наявні результати
- `configs/` — налаштування експериментів
- `.bib` файли — існуючі посилання
- чернетки документів або нотатки

### Крок 0.2: Організація робочого простору

Встанови послідовну структуру робочого простору:

```
workspace/
  paper/               # LaTeX source, figures, compiled PDFs
  experiments/         # Experiment runner scripts
  code/                # Core method implementation
  results/             # Raw experiment results (auto-generated)
  tasks/               # Task/benchmark definitions
  human_eval/          # Human evaluation materials (if needed)
```

### Крок 0.3: Налаштування системи контролю версій

```bash
git init  # if not already
git remote add origin <repo-url>
git checkout -b paper-draft  # or main
```

**Git discipline**: Кожна завершена партія експериментів комітиться з описовим повідомленням. Приклад:
```
Add Monte Carlo constrained results (5 runs, Sonnet 4.6, policy memo task)
Add Haiku baseline comparison: autoreason vs refinement baselines at cheap model tier
```

### Крок 0.4: Визначення внеску

Перш ніж писати, сформулюй:
- **The What**: Яка єдина річ, яку цей документ вносить?
- **The Why**: Які докази це підтверджують?
- **The So What**: Чому це важливо для читачів?

> Запропонуй вченому: «На підставі мого розуміння головний внесок полягає в: [одне речення]. Ключові результати показують [Y]. Чи це те формулювання, яке ти хочеш?»

### Крок 0.5: Створення списку TODO

Використай інструмент `todo` для створення структурованого плану проєкту:

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

Оновлюй його протягом усього проєкту. Це слугує постійним станом між сесіями.

### Крок 0.6: Оцінка бюджету обчислень

Перед запуском експериментів оцінити загальну вартість і час:

```
Compute Budget Checklist:
- [ ] API costs: (model price per token) × (estimated tokens per run) × (number of runs)
- [ ] GPU hours: (time per experiment) × (number of experiments) × (number of seeds)
- [ ] Human evaluation costs: (annotators) × (hours) × (hourly rate)
- [ ] Total budget ceiling and contingency (add 30-50% for reruns)
```

Відстежуй фактичні витрати під час виконання експериментів:
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

**Коли бюджет обмежений**: Запусти пілотні експерименти (1‑2 seeds, підмножина завдань) перед повними переборами. Використовуй дешевші моделі для налагодження конвеєрів, а потім переходи до цільових моделей для фінальних запусків.

### Крок 0.7: Координація між авторами

Більшість статей мають 3‑10 авторів. Встанови робочі процеси заздалегідь:

| Workflow | Tool | When to Use |
|----------|------|-------------|
| **Overleaf** | Browser-based | Кілька авторів редагують одночасно, без досвіду git |
| **Git + LaTeX** | `git` з `.gitignore` для допоміжних файлів | Технічні команди, потрібен огляд на гілках |
| **Overleaf + Git sync** | Overleaf premium | Найкраще з обох — живе співробітництво з історією змін |

**Володіння розділом**: Признач кожному розділу одного головного автора. Інші можуть коментувати, але не редагувати безпосередньо. Це запобігає конфліктам злиття та розбіжностям у стилі.

```
Author Coordination Checklist:
- [ ] Agree on section ownership (who writes what)
- [ ] Set up shared workspace (Overleaf or git repo)
- [ ] Establish notation conventions (before anyone writes)
- [ ] Schedule internal review rounds (not just at the end)
- [ ] Designate one person for final formatting pass
- [ ] Agree on figure style (colors, fonts, sizes) before creating figures
```

**Конвенції LaTeX, які треба узгодити заздалегідь**:
- макрос `\method{}` для уніфікованого найменування методів
- стиль цитувань: використання `\citet{}` vs `\citep{}`
- математична нотація: нижній регістр жирний для векторів, верхній регістр жирний для матриць тощо
- британська vs американська орфографія

---
## Phase 1: Огляд літератури

**Мета**: Знайти пов’язану роботу, визначити базові підходи, зібрати посилання.

### Крок 1.1: Визначити насіннєві статті

Почни з статей, вже згаданих у кодовій базі:

```bash
# Via terminal:
grep -r "arxiv\|doi\|cite" --include="*.md" --include="*.bib" --include="*.py"
find . -name "*.bib"
```

### Крок 1.2: Пошук пов’язаної роботи

**Завантаж `arxiv` skill** для структурованого пошуку статей: `skill_view("arxiv")`. Він надає пошук через REST API arXiv, графи цитувань Semantic Scholar, профілі авторів та генерацію BibTeX.

Використовуй `web_search` для широкого пошуку, `web_extract` для отримання конкретних статей:

```
# Via web_search:
web_search("[main technique] + [application domain] site:arxiv.org")
web_search("[baseline method] comparison ICML NeurIPS 2024")

# Via web_extract (for specific papers):
web_extract("https://arxiv.org/abs/2303.17651")
```

Додаткові запити для пошуку:

```
Search queries:
- "[main technique] + [application domain]"
- "[baseline method] comparison"
- "[problem name] state-of-the-art"
- Author names from existing citations
```

**Рекомендовано**: Встановити **Exa MCP** для реального часу академічного пошуку:
```bash
claude mcp add exa -- npx -y mcp-remote "https://mcp.exa.ai/mcp"
```

### Крок 1.2b: Поглибити пошук (ширина‑перш‑потім‑глибина)

Плоский пошук (один раунд запитів) зазвичай пропускає важливу пов’язану роботу. Використовуй ітеративний шаблон **ширина‑перш‑потім‑глибина**, натхненний глибокими дослідницькими конвеєрами:

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

**Коли зупинятись**: Якщо раунд повертає >80 % статей, вже присутніх у твоїй колекції, пошук насичений. Зазвичай достатньо 2‑3 раундів. Для оглядових статей очікуй 4‑5 раундів.

**Для агентних робочих процесів**: Делегуй запити кожного раунду паралельно через `delegate_task`. Збери результати, видали дублікати, потім сформуй запити наступного раунду на основі об’єднаних висновків.

### Крок 1.3: Перевірити кожне посилання

**НІКОЛИ не генеруй BibTeX з пам’яті. ЗАВЖДИ отримуй його програмно.**

Для кожного посилання дотримуйся обов’язкового 5‑крокового процесу:

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

Якщо не вдається перевірити посилання:

```latex
\cite{PLACEHOLDER_author2024_verify_this}  % TODO: Verify this citation exists
```

**Завжди повідомляй вченому**: «Я позначив [X] посилань як заповнювачі, які потребують перевірки.»

Дивись [references/citation-workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/citation-workflow.md) для повної документації API та класу `CitationManager`.

### Крок 1.4: Організувати пов’язану роботу

Групуй статті за методологією, а не поодиноко:

**Добре**: «Один ряд робіт використовує припущення X [refs], тоді як ми використовуємо припущення Y, тому що…»

**Погано**: «Сміт і ін. представили X. Джонс і ін. представили Y. Ми поєднуємо обидва.»

---
## Phase 2: Дизайн експерименту

**Goal**: Спроектувати експерименти, які безпосередньо підтримують твердження статті. Кожен експеримент має відповідати на конкретне питання.

### Крок 2.1: Відображення тверджень на експерименти

Create an explicit mapping:

| Claim | Experiment | Expected Evidence |
|-------|-----------|-------------------|
| "Our method outperforms baselines" | Main comparison (Table 1) | Win rate, statistical significance |
| "Effect is larger for weaker models" | Model scaling study | Monotonic improvement curve |
| "Convergence requires scope constraints" | Constrained vs unconstrained | Convergence rate comparison |

**Правило**: Якщо експеримент не співпадає з жодним твердженням, не проводь його.

### Крок 2.2: Дизайн базових ліній

Strong baselines – це те, що розрізняє прийняті статті від відхилених. Рецензенти запитають: «Чи порівнювали вони з X?»

Standard baseline categories:
- **Naive baseline**: Найпростіший можливий підхід
- **Strong baseline**: Найкращий відомий існуючий метод
- **Ablation baselines**: Твій метод без одного компонента
- **Compute-matched baselines**: Та ж обчислювальна потужність, інше розподілення

### Крок 2.3: Визначення протоколу оцінки

Before running anything, specify:
- **Metrics**: Що вимірюєш, символи напрямку (вища/нижча краще)
- **Aggregation**: Як результати комбінуються між запусками/завданнями
- **Statistical tests**: Які тести встановлюватимуть значущість
- **Sample sizes**: Скільки запусків/проблем/завдань

### Крок 2.4: Написання скриптів експерименту

Follow these patterns from successful research pipelines:

**Incremental saving** — save results after each step for crash recovery:
```python
# Save after each problem/task
result_path = f"results/{task}/{strategy}/result.json"
if os.path.exists(result_path):
    continue  # Skip already-completed work
# ... run experiment ...
with open(result_path, 'w') as f:
    json.dump(result, f, indent=2)
```

**Artifact preservation** — save all intermediate outputs:
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

**Separation of concerns** — keep generation, evaluation, and visualization separate:
```
run_experiment.py              # Core experiment runner
run_baselines.py               # Baseline comparison
run_comparison_judge.py        # Blind evaluation
analyze_results.py             # Statistical analysis
make_charts.py                 # Visualization
```

See [references/experiment-patterns.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/experiment-patterns.md) for complete design patterns, cron monitoring, and error recovery.

### Крок 2.5: Дизайн людської оцінки (за потреби)

Many NLP, HCI, and alignment papers require human evaluation as primary or complementary evidence. Design this before running automated experiments — human eval often has longer lead times (IRB approval, annotator recruitment).

**When human evaluation is needed:**
- Automated metrics don’t capture what you care about (fluency, helpfulness, safety)
- Your contribution is about human‑facing qualities (readability, preference, trust)
- Reviewers at NLP venues (ACL, EMNLP) expect it for generation tasks

**Key design decisions:**

| Decision | Options | Guidance |
|----------|---------|----------|
| **Annotator type** | Expert, crowdworker, end‑user | Match to what your claims require |
| **Scale** | Likert (1‑5), pairwise comparison, ranking | Pairwise is more reliable than Likert for LLM outputs |
| **Sample size** | Per annotator and total items | Power analysis or minimum 100 items, 3+ annotators |
| **Agreement metric** | Cohen's kappa, Krippendorff's alpha, ICC | Krippendorff's alpha for >2 annotators; report raw agreement too |
| **Platform** | Prolific, MTurk, internal team | Prolific for quality; MTurk for scale; internal for domain expertise |

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

**Reporting requirements** (reviewers check all of these):
- Number of annotators and their qualifications
- Inter‑annotator agreement with specific metric and value
- Compensation details (amount, estimated hourly rate)
- Annotation interface description or screenshot (appendix)
- Total annotation time

See [references/human-evaluation.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/human-evaluation.md) for complete guide including statistical tests for human eval data, crowdsourcing quality control patterns, and IRB guidance.
## Фаза 3: Виконання експериментів та моніторинг

**Мета**: Запускати експерименти надійно, стежити за прогресом, відновлюватися після збоїв.

### Step 3.1: Запуск експериментів

Використовуй `nohup` для довготривалих експериментів:

```bash
nohup python run_experiment.py --config config.yaml > logs/experiment_01.log 2>&1 &
echo $!  # Record the PID
```

**Паралельне виконання**: Запускай незалежні експерименти одночасно, але май на увазі обмеження швидкості API. 4+ одночасних експериментів на одному API сповільнять кожен з них.

### Step 3.2: Налаштування моніторингу (шаблон Cron)

Для довготривалих експериментів налаштуй періодичні перевірки статусу. Шаблон cron має виглядати так:

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

**Тихий режим**: Якщо з останньої перевірки нічого не змінилося, відповідай `[SILENT]`, щоб придушити сповіщення користувачеві. Повідомляй лише коли є новини.

### Step 3.3: Обробка збоїв

Типові режими збоїв та відновлення:

| Failure | Detection | Recovery |
|---------|-----------|----------|
| API rate limit / credit exhaustion | 402/429 errors in logs | Wait, then re-run (scripts skip completed work) |
| Process crash | PID gone, incomplete results | Re-run from last checkpoint |
| Timeout on hard problems | Process stuck, no log progress | Kill and skip, note in results |
| Wrong model ID | Errors referencing model name | Fix ID and re-run |

**Ключ**: Скрипти мають завжди перевіряти наявність існуючих результатів і пропускати вже виконану роботу. Це робить повторні запуски безпечними та ефективними.

### Step 3.4: Коміт завершених результатів

Після завершення кожної партії експериментів:

```bash
git add -A
git commit -m "Add <experiment name>: <key finding in 1 line>"
git push
```

### Step 3.5: Ведення журналу експериментів

Git‑коміти фіксують, що сталося, але не **дерево експериментів** — рішення, що пробувати далі на основі отриманих знань. Веди структурований журнал експериментів, який захоплює це дерево:

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

**Навіщо журнал, а не лише git?** Git фіксує зміни файлів. Журнал фіксує міркування: чому ти спробував X, що ти дізнався і що це означає для наступного експерименту. При написанні статті це дерево безцінне для розділу Methods («ми спостерігали X, що спонукало до Y») і для чесного звіту про невдачі.

**Вибір найкращого шляху**: Коли журнал показує розгалужене дерево (exp_001 → exp_002a, exp_002b, exp_003), визначай шлях, який найкраще підтримує твердження статті. Документуй мертві гілки у додатку як абляції або негативні результати.

**Знімок коду для кожного експерименту**: Скопіюй скрипт експерименту після кожного запуску:
```bash
cp experiment.py results/exp_003/experiment_snapshot.py
```
Це забезпечує точну відтворюваність навіть після подальших змін коду.
## Phase 4: Аналіз результатів

**Goal**: Витягнути висновки, обчислити статистику, визначити історію.

### Step 4.1: Агрегування результатів

Напиши скрипти аналізу, які:
1. Завантажують усі файли результатів з пакету
2. Обчислюють метрики за завданням та агреговані метрики
3. Генерують підсумкові таблиці

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

### Step 4.2: Статистична значимість

Завжди обчислюй:
- **Error bars**: стандартне відхилення або стандартна помилка, вкажи, яке саме
- **Confidence intervals**: 95 % CI для ключових результатів
- **Pairwise tests**: тест МакНемара для порівняння двох методів
- **Effect sizes**: d або h Коуена для практичної значимості

Дивись [references/experiment-patterns.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/experiment-patterns.md) для повних реалізацій тесту МакНемара, бутстреп‑CI та h Коуена.

### Step 4.3: Визначення історії

Після аналізу явно відповідай:
1. **What is the main finding?** State it in one sentence.
2. **What surprised you?** Неочікувані результати часто роблять найкращі статті.
3. **What failed?** Невдалі експерименти можуть бути найінформативнішими. Чесна звітність про провали зміцнює статтю.
4. **What follow‑up experiments are needed?** Результати часто піднімають нові питання.

#### Обробка негативних або нульових результатів

Коли твоя гіпотеза виявилась хибною або результати неоднозначні, у тебе є три варіанти:

| Situation | Action | Venue Fit |
|-----------|--------|-----------|
| Гіпотеза неправильна, але **чому** інформативно | Сформулюй статтю навколо аналізу причин | NeurIPS, ICML (якщо аналіз строгий) |
| Метод не перевершує базові, але **розкриває щось нове** | Переформулюй внесок як розуміння/аналіз | ICLR (цінує розуміння), workshop papers |
| Чистий негативний результат щодо популярної заяви | Напиши про це — галузі треба знати | NeurIPS Datasets & Benchmarks, TMLR, workshops |
| Результати неоднозначні, історії немає | Переорієнтуйся — проведи інші експерименти або змінюй фокус | Не змушуй писати статтю, якої немає |

**Як написати статтю про негативні результати:**
- Почни з того, у що вірить спільнота, і чому це важливо перевірити
- Описуй строгий метод (повинен бути бездоганним — рецензенти будуть суворіші)
- Представляй нульовий результат чітко зі статистичними доказами
- Проаналізуй **чому** очікуваний результат не отримано
- Обговори наслідки для галузі

**Вендори, які явно вітають негативні результати**: NeurIPS (Tracks Datasets & Benchmarks), TMLR, ML Reproducibility Challenge, workshops на великих конференціях. Деякі воркшопи спеціально запрошують негативні результати.

### Step 4.4: Створення фігур та таблиць

**Фігури**:
- Використовуй векторну графіку (PDF) для всіх графіків: `plt.savefig('fig.pdf')`
- Палітри, безпечні для дальтоніків (Okabe‑Ito або Paul Tol)
- Самодостатні підписи — читач має розуміти без основного тексту
- Не став заголовок у фігуру — функцію виконує підпис

**Таблиці**:
- Використовуй LaTeX‑пакет `booktabs`
- Виділяй жирним найкраще значення за метрикою
- Додавай символи напрямку (вища/нижча — краще)
- Послідовна десяткова точність

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

### Step 4.5: Вирішити: Більше експериментів чи писати?

| Situation | Action |
|-----------|--------|
| Основні твердження підтверджені, результати значимі | Перейти до Phase 5 (writing) |
| Результати неоднозначні, треба більше даних | Повернутись до Phase 2 (design) |
| Неочікуване відкриття натякає новий напрямок | Повернутись до Phase 2 (design) |
| Відсутня одна абляція, яку запитають рецензенти | Провести її, потім Phase 5 |
| Всі експерименти завершені, але деякі провалились | Зафіксувати провали, перейти до Phase 5 |

### Step 4.6: Написати журнал експерименту (міст між експериментом і написанням)

Перед переходом до написання статті створити структурований журнал експерименту, який з’єднує результати з прозою. Це найважливіший зв’язок між експериментами та написанням — без нього агенту‑писанню доведеться заново виводити історію з сирих файлів результатів.

**Створи `experiment_log.md`** зі такою структурою:

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

**Чому це важливо**: При підготовці чернетки агент (або делегований під‑агент) може завантажити `experiment_log.md` разом із шаблоном LaTeX і створити перший чернетковий варіант, підкріплений реальними результатами. Без цього мосту агенту‑писанню доведеться парсити сирі JSON/CSV файли і виводити історію — часте джерело галюцинацій або помилкових цифр.

**Git‑дисципліна**: Комітни цей журнал разом з результатами, які він описує.
## Ітеративне уточнення: вибір стратегії

Будь‑який результат у цьому конвеєрі — чернетки статей, скрипти експериментів, аналіз — може бути ітеративно уточнений. Дослідження **Autoreason** надає емпіричні докази того, коли кожна стратегія уточнення працює, а коли ні. Використай цей розділ, щоб обрати правильний підхід.

### Швидка таблиця рішень

| Твоя ситуація | Стратегія | Чому |
|---------------|----------|------|
| Середньорівнева модель + обмежене завдання | **Autoreason** | Ідеальне поєднання. Проміжок між генерацією та оцінкою найширший. Базові лінії активно руйнують слабкі виходи моделі. |
| Середньорівнева модель + відкрите завдання | **Autoreason** з доданими обмеженнями області | Додай фіксовані факти, структуру або результат, щоб обмежити простір покращень. |
| Фронт‑рід модель + обмежене завдання | **Autoreason** | Перемагає у 2/3 обмежених завдань навіть у фронт‑рід. |
| Фронт‑рід модель + необмежене завдання | **Critique-and-revise** або **single pass** | **Autoreason** використовується останнім. Модель самостійно оцінює достатньо добре. |
| Конкретне технічне завдання (системний дизайн) | **Critique-and-revise** | Прямий цикл «знайди‑і‑виправ» ефективніший. |
| Завдання заповнення шаблону (одна правильна структура) | **single pass** або **conservative** | Мінімальний простір рішень. Ітерація не додає цінності. |
| Код з тест‑кейсами | **Autoreason (code variant)** | Структурований аналіз *чому* він не спрацював перед виправленням. Рівень відновлення 62 % проти 43 %. |
| Дуже слабка модель (клас Llama 8B) | **single pass** | Модель занадто слабка для різноманітних кандидатів. Інвестуй у якість генерації. |

### Проміжок між генерацією та оцінкою

**Ключове розуміння**: цінність **Autoreason** залежить від розриву між здатністю моделі генерувати та її здатністю самостійно оцінювати.

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

Цей розрив є структурним, а не тимчасовим. По мірі зниження вартості, сьогоднішній фронт‑рід стає завтрашнім середньорівневим. Ідеальне поєднання зміщується, але ніколи не зникає.

### Цикл **Autoreason** (резюме)

Кожен прохід створює три кандидати від нових, ізольованих агентів:

1. **Critic** → знаходить проблеми в поточному A (без виправлень)
2. **Author B** → виправляє A на основі критики
3. **Synthesizer** → об’єднує A і B (випадкові мітки)
4. **Judge Panel** → 3 сліпих CoT судді ранжують A, B, AB за методом Борда
5. **Convergence** → A виграє k=2 послідовних проходи → завершено

**Ключові параметри:**
- k=2 — збіжність (k=1 — передчасно, k=3 — занадто дорого, без підвищення якості)
- CoT судді завжди (3 × швидша збіжність)
- Температура 0.8 у авторів, 0.3 у суддів
- Консервативний розв’язок у нічиїх: поточний виграє
- Кожна роль — новий агент без спільного контексту

### Застосування до чернеток статей

При уточненні самої статті за допомогою **Autoreason**:
- **Надай критикові правдиві дані**: реальні експериментальні дані, JSON‑результати, статистичні виходи. Без цього моделі вигадують фіктивні абляційні дослідження та фальшиві інтервали довіри.
- **Використовуй мінімум 3 робочих суддів**: поломаний парсер судді не додає шум — він повністю руйнує рівновагу.
- **Обмежуй область правки**: «Виправити ці конкретні недоліки», а не «покращити статтю».

### Режими відмов

| Відмова | Виявлення | Виправлення |
|--------|-----------|------------|
| Немає збіжності (A ніколи не виграє) | A виграє <15 % за 20+ проходів | Додай обмеження області до завдання |
| Дрейф синтезу | Кількість слів зростає без меж | Обмеж структуру та результат |
| Падіння якості нижче **single pass** | Базові лінії отримують вищі бали, ніж ітеративний вихід | Перейди на **single pass**; модель може бути занадто слабкою |
| Перепідгонка (код) | Високий прохід у public‑test, низький у private‑test | Використовуй структурований аналіз, а не лише зворотний зв’язок тесту |
| Поломлені судді | Помилки парсингу зменшують панель до <3 | Виправ парсер перед продовженням |

Дивись [references/autoreason-methodology.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/autoreason-methodology.md) для повних підказок, деталей підрахунку Борда, рекомендацій щодо вибору моделі, шаблонів обмежень області та орієнтирів бюджету обчислень.
## Фаза 5: Підготовка статті

**Мета**: Написати повну, готову до публікації статтю.
### Управління контекстом для великих проєктів

Проєкт статті з 50+ файлів експериментів, кількома каталогами результатів та обширними нотатками літератури легко може перевищити вікно контексту агента. Керуйте цим проактивно:

**Що завантажувати в контекст для кожного завдання написання:**

| Завдання написання | Завантажити в контекст | Не завантажувати |
|--------------------|------------------------|-------------------|
| Написання вступу | `experiment_log.md`, заява про внесок, 5‑10 найрелевантніших анотацій статей | Сирі JSON‑файли результатів, повні скрипти експериментів, усі нотатки літератури |
| Написання методів | Конфігурації експериментів, псевдокод, опис архітектури | Сирі логи, результати інших експериментів |
| Написання результатів | `experiment_log.md`, таблиці підсумків результатів, список рисунків | Повні скрипти аналізу, проміжні дані |
| Написання розділу «Пов’язана робота» | Організовані нотатки про цитування (вихід Step 1.4), файл `.bib` | Файли експериментів, сирі PDF |
| Перегляд ревізії | Повна чернетка статті, конкретні зауваження рецензентів | Все інше |

**Принципи:**
- **`experiment_log.md` — основний місток контексту** — він підсумовує все, що потрібно для написання, без завантаження сирих файлів даних (див. Step 4.6).
- **Завантажуй контекст лише однієї секції за раз**, коли делегуєш. Під‑агент, який пише розділ Methods, не потребує нотаток літературного огляду.
- **Стислий підсумок, а не сирі файли.** Для JSON‑файлу результату у 200 рядків завантажуй таблицю підсумку у 10 рядків. Для статті у 50 сторінок завантажуй анотацію у 5 речень + твою 2‑рядкову нотатку про її релевантність.
- **Для дуже великих проєктів**: створюй каталог `context/` з попередньо стиснутими підсумками:
  ```
  context/
    contribution.md          # 1 sentence
    experiment_summary.md    # Key results table (from experiment_log.md)
    literature_map.md        # Organized citation notes
    figure_inventory.md      # List of figures with descriptions
  ```
### Принцип наративу

**Найважливіший інсайт**: Твоя стаття — це не збірка експериментів, а історія з одним чітким внеском, підкріпленим доказами.

Кожна успішна ML‑стаття зосереджена навколо того, що Ніл Нанда називає «наративом»: коротка, строгa, доказова технічна історія з висновком, який важливий для читачів.

**Три стовпи (повинні бути кристально зрозумілими до кінця вступу):**

| Стовп | Опис | Перевірка |
|--------|------|-----------|
| **Що** | 1‑3 конкретних нових твердження | Чи можеш ти сформулювати їх в одному реченні? |
| **Навіщо** | Строге емпіричне підтвердження | Чи відрізняють експерименти твою гіпотезу від альтернатив? |
| **То‑що** | Чому це важливо для читачів | Чи пов’язано це з визнаною проблемою спільноти? |

**Якщо ти не можеш сформулювати свій внесок в одному реченні, у тебе ще немає статті.**
### Джерела, що стоять за цим керівництвом

Ця **навичка** синтезує філософію написання від дослідників, які широко публікувалися у провідних виданнях. Шар філософії написання спочатку був зібраний [Orchestra Research](https://github.com/orchestra-research) як навичка `ml-paper-writing`.

| Джерело | Ключовий внесок | Посилання |
|--------|-----------------|-----------|
| **Neel Nanda** (Google DeepMind) | Принцип наративу, фреймворк What/Why/So What | [How to Write ML Papers](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers) |
| **Sebastian Farquhar** (DeepMind) | Формула 5‑речевого абстракту | [How to Write ML Papers](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/) |
| **Gopen & Swan** | 7 принципів очікувань читача | [Science of Scientific Writing](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf) |
| **Zachary Lipton** | Вибір слів, усунення хеджування | [Heuristics for Scientific Writing](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/) |
| **Jacob Steinhardt** (UC Berkeley) | Точність, послідовна термінологія | [Writing Tips](https://bounded-regret.ghost.io/) |
| **Ethan Perez** (Anthropic) | Поради щодо мікрорівня ясності | [Easy Paper Writing Tips](https://ethanperez.net/easy-paper-writing-tips/) |
| **Andrej Karpathy** | Фокус на єдиному внеску | Різні лекції |

**Для глибшого занурення в будь‑який з цих матеріалів, дивись:**
- [references/writing-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/writing-guide.md) — Повні пояснення з прикладами
- [references/sources.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/sources.md) — Повна бібліографія
### Розподіл часу

Приділяй приблизно **однакову кількість часу** кожному з:
1. Анотації
2. Вступу
3. Рисунків
4. Усьому іншому разом

**Чому?** Більшість рецензентів формують оцінку ще до того, як дійдуть до розділу «Методи». Читачі сприймають твою статтю так: назва → анотація → вступ → рисунки → можливо решта.
### Процес написання

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
### Two-Pass Refinement Pattern

Коли ти створюєш документ за допомогою AI‑агента, використай **двохпрохідний** підхід (перевірений у pipeline SakanaAI's AI‑Scientist):

**Pass 1 — Write + immediate refine per section:**
Для кожного розділу спочатку напиши повний чернетковий варіант, а потім одразу ж уточни його в тому ж контексті. Це дозволяє виявити локальні проблеми (ясність, логічність, повноту), доки розділ ще свіжий.

**Pass 2 — Global refinement with full-paper context:**
Після того, як усі розділи написані, повернись до кожного з них, маючи на увазі повний документ. Це допомагає виявити проблеми між розділами: надмірну повторюваність, несумісність термінології, порушення наративного потоку та прогалини, коли один розділ обіцяє те, чого інший не виконує.

```
Second-pass refinement prompt (per section):
"Review the [SECTION] in the context of the complete paper.
- Does it fit with the rest of the paper? Are there redundancies with other sections?
- Is terminology consistent with Introduction and Methods?
- Can anything be cut without weakening the message?
- Does the narrative flow from the previous section and into the next?
Make minimal, targeted edits. Do not rewrite from scratch."
```
### Перелік помилок LaTeX

Додай цей чек‑лист до кожного запиту уточнення. Це найчастіші помилки, які виникають, коли LLM‑и пишуть LaTeX:

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
### Крок 5.0: Заголовок

Заголовок – це найчастіше читаємий елемент статті. Він визначає, чи хтось перейде до анотації.

**Хороші заголовки**
- Вказують на внесок або результат: «Autoreason: When Iterative LLM Refinement Works and Why It Fails»
- Підкреслюють несподіваний результат: «Scaling Data-Constrained Language Models» (має на увазі, що це можливо)
- Назва методу + його функція: «DPO: Direct Preference Optimization of Language Models»

**Погані заголовки**
- Надто загальні: «An Approach to Improving Language Model Outputs»
- Надто довгі: будь‑що понад ~15 слів
- Тільки жаргон: «Asymptotic Convergence of Iterative Stochastic Policy Refinement» (для кого це?)

**Правила**
- Додай назву свого методу, якщо вона є (для цитованості)
- Додай 1‑2 ключові слова, які шукають рецензенти
- Уникай двокрапок, якщо обидві частини не несуть змісту
- Перевірка: чи зможе рецензент зрозуміти галузь і внесок лише за заголовком?
### Крок 5.1. Абстракт (формула з 5 речень)

Від Себастіана Фаркуара (DeepMind):

```
1. What you achieved: "We introduce...", "We prove...", "We demonstrate..."
2. Why this is hard and important
3. How you do it (with specialist keywords for discoverability)
4. What evidence you have
5. Your most remarkable number/result
```

**Видали** типові вступи типу «Великі мовні моделі досягли визначних успіхів…».
### Крок 5.2: Рисунок 1

Рисунок 1 – це друга річ, яку більшість читачів переглядає (після анотації). Підготуй його перед написанням вступу — це змушує уточнити основну ідею.

| Тип рисунка | Коли використовувати | Приклад |
|-------------|----------------------|---------|
| **Діаграма методу** | Нова архітектура або pipeline | TikZ‑flowchart, що показує твою систему |
| **Тізер результатів** | Один вражаючий результат розповідає всю історію | Стовпчиковий графік: «Наші vs базові» з чітким розривом |
| **Ілюстрація проблеми** | Проблема неінтуїтивна | До/після, що демонструє режим збою, який ти виправляєш |
| **Концептуальна діаграма** | Абстрактний внесок потребує візуального підкріплення | 2 × 2 матриця властивостей методу |

**Правила**: Рисунок 1 має бути зрозумілим без читання будь‑якого тексту. Підпис під рисунком сам по собі має передавати основну ідею. Використовуй колір цілеспрямовано — не просто для оздоблення.
### Крок 5.3: Вступ (не більше 1‑1,5 сторінки)

Повинен містити:
- Чітке формулювання проблеми
- Короткий огляд підходу
- Список внесків у 2‑4 пунктах (не більше 1‑2 рядків кожен у двостовпчиковому форматі)
- Методи мають починатися на сторінці 2‑3
### Крок 5.4: Методи

Забезпечити можливість повторної реалізації:
- Концептуальний план або псевдокод
- Усі гіперпараметри, зазначені
- Архітектурні деталі, достатні для відтворення
- Представити остаточні рішення дизайну; абляції розміщуються у розділі **Експерименти**
### Крок 5.5: Експерименти та результати

Для кожного експерименту чітко вкажи:
- **Яке твердження він підтримує**
- Як він пов’язаний з основним внеском
- Що спостерігати: «синя лінія показує X, що демонструє Y»

Вимоги:
- Смуги помилок з методологією (стандартне відхилення vs стандартна помилка)
- Діапазони пошуку гіперпараметрів
- Обчислювальна інфраструктура (тип GPU, загальна кількість годин роботи)
- Методи встановлення seed
### Крок 5.6: Пов’язана робота

Організовуй за методологією, а не стаття за статтею. Цитуй щедро — рецензенти, ймовірно, є авторами відповідних статей.
### Крок 5.7: Обмеження (ОБОВʼЯЗКОВО)

Усі великі конференції вимагають це. Чесність допомагає:
- Рецензентам інструктовано не карати за чесне визнання обмежень
- Попередити критику, спочатку виявивши слабкі місця
- Пояснити, чому обмеження не підривають основні твердження
### Крок 5.8. Висновок та обговорення

**Висновок** (обов’язково, 0,5–1 сторінка):
- Перефразуй внесок у одному реченні (відмінним від формулювання в анотації)
- Підсумуй ключові результати (2–3 речення, без списку)
- Наслідки: що це означає для галузі?
- Майбутня робота: 2–3 конкретних наступних кроки (не розпливчасті «ми залишаємо X на майбутнє»)

**Обговорення** (за бажанням, іноді поєднується з висновком):
- Ширші наслідки поза межами безпосередніх результатів
- Зв’язки з іншими підгалузями
- Чесна оцінка, коли метод працює, а коли ні
- Практичні міркування щодо впровадження

**Не** вводь нові результати або твердження у висновку.
### Крок 5.9: Стратегія додатків

Додатки необмежені на всіх основних майданчиках і є важливими для відтворюваності. Структура:

| Розділ додатку | Що розміщувати |
|-----------------|----------------|
| **Докази та виведення** | Повні докази, які занадто довгі для основного тексту. У основному тексті можна зазначити теореми з «доказ у Додатку A». |
| **Додаткові експерименти** | Абляції, криві масштабування, розбивки за набором даних, чутливість гіперпараметрів |
| **Деталі реалізації** | Повні таблиці гіперпараметрів, деталі навчання, специфікації обладнання, випадкові зерна |
| **Документація набору даних** | Процес збору даних, інструкції з анотації, ліцензування, попередня обробка |
| **Промпти та шаблони** | Точні промпти, які використовувалися (для методів на основі LLM), шаблони оцінювання |
| **Оцінка людьми** | Скриншоти інтерфейсу анотації, інструкції, дані IRB |
| **Додаткові фігури** | Розбивки за завданням, візуалізації траєкторій, приклади випадків провалу |

**Правила**:
- Основна стаття має бути самодостатньою — рецензенти не зобов’язані читати додатки
- Ніколи не розміщуй критичні докази лише в додатку
- Перехресне посилання: «Повні результати в Таблиці 5 (Додаток B)», а не просто «див. додаток»
- Використовуй команду `\appendix`, потім `\section{A: Докази}` тощо.
### Управління обсягом сторінки

Коли перевищено ліміт сторінок:

| Стратегія скорочення | Заощаджує | Ризик |
|----------------------|-----------|-------|
| Перемістити докази в додаток | 0.5‑2 сторінки | Низький — стандартна практика |
| Скоротити розділ «Пов’язана робота» | 0.5‑1 сторінка | Середній — може бути пропущено ключові посилання |
| Об’єднати таблиці з підрисунками | 0.25‑0.5 сторінки | Низький — часто покращує читабельність |
| Використовувати `\vspace{-Xpt}` помірно | 0.1‑0.3 сторінки | Низький, якщо непомітно; високий, якщо помітно |
| Видалити якісні приклади | 0.5‑1 сторінка | Середній — рецензенти цінують приклади |
| Зменшити розмір рисунків | 0.25‑0.5 сторінки | Високий — рисунки мають залишатися читабельними |

**Не роби**: зменшувати розмір шрифту, змінювати поля, видаляти обов’язкові розділи (обмеження, ширший вплив) або використовувати `\small`/`\footnotesize` для основного тексту.
### Крок 5.10: Заява про етику та ширший вплив

Більшість конференцій тепер вимагає або настійно радить надати заяву про етику/ширший вплив. Це не шаблон — рецензенти читають її і можуть позначити етичні проблеми, які призведуть до відхилення на етапі подання.

**Що включити:**

| Компонент | Зміст | Вимагає |
|-----------|-------|--------|
| **Позитивний суспільний вплив** | Як ваша робота приносить користь суспільству | NeurIPS, ICML |
| **Потенційний негативний вплив** | Ризики зловживання, проблеми подвійного використання, режими відмови | NeurIPS, ICML |
| **Справедливість та упередженість** | Чи має ваш метод/дані відомі упередження? | Всі конференції (неявно) |
| **Екологічний вплив** | Вуглецевий слід обчислень для масштабного навчання | ICML, все більше NeurIPS |
| **Конфіденційність** | Чи використовує ваша робота або дозволяє обробку персональних даних? | ACL, NeurIPS |
| **Розкриття використання LLM** | Чи було використано ШІ при написанні чи експериментах? | ICLR (обов’язково), ACL |

**Написання заяви:**

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

**Типові помилки:**
- Написати «ми не передбачаємо жодних негативних впливів» (майже ніколи не відповідає дійсності — рецензенти не довіряють цьому)
- Бути розпливчастим: «це може бути використано зловмисно» без уточнення як
- Ігнорувати витрати обчислень для масштабних проєктів
- Забути розкрити використання LLM на конференціях, які це вимагають

**Вуглецевий слід обчислень** (для статей з інтенсивним навчанням):
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
### Крок 5.11: Datasheets & Model Cards (за потреби)

Якщо у твоїй статті представлено **новий набір даних** або **випущено модель**, додай структуровану документацію. Рецензенти все частіше очікують це, а трек NeurIPS Datasets & Benchmarks вимагає це.

**Datasheets for Datasets** (Gebru et al., 2021) — додай у додаток:

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

**Model Cards** (Mitchell et al., 2019) — додай у додаток для випуску моделі:

```
Model Card (Appendix):
- Model details: Architecture, training data, training procedure
- Intended use: Primary use cases, out-of-scope uses
- Metrics: Evaluation metrics and results on benchmarks
- Ethical considerations: Known biases, fairness evaluations
- Limitations: Known failure modes, domains where model underperforms
```
### Стиль написання

**Чіткість на рівні речень (7 принципів Gopen & Swan):**

| Принцип | Правило |
|-----------|------|
| Близькість підмета і присудка | Тримай підмет і дієслово поруч |
| Позиція наголосу | Розміщуй наголос у кінці речення |
| Позиція теми | Спочатку подавай контекст, потім нову інформацію |
| Старе перед новим | Знайома інформація → незнайома інформація |
| Одна одиниця, одна функція | Кожен абзац висловлює одну думку |
| Дія у дієслові | Використовуй дієслова, а не іменники |
| Контекст перед новим | Підготуй сцену перед представленням нового |

**Вибір слів (Lipton, Steinhardt):**
- Будь конкретним: «точність», а не «продуктивність»
- Усунь невизначеність: прибери «може», якщо не є дійсно невизначеним
- Послідовна термінологія протягом усього тексту
- Уникай зайвих синонімів: «розробляти», а не «поєднувати»

**Повний посібник з написання з прикладами**: Дивись [references/writing-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/writing-guide.md)
### Використання шаблонів LaTeX

**Завжди спочатку копіюй весь каталог шаблону, а потім працюй у ньому.**

```
Template Setup Checklist:
- [ ] Step 1: Copy entire template directory to new project
- [ ] Step 2: Verify template compiles as-is (before any changes)
- [ ] Step 3: Read the template's example content to understand structure
- [ ] Step 4: Replace example content section by section
- [ ] Step 5: Use template macros (check preamble for \newcommand definitions)
- [ ] Step 6: Clean up template artifacts only at the end
```

**Крок 1: Скопіюй повний шаблон**

```bash
cp -r templates/neurips2025/ ~/papers/my-paper/
cd ~/papers/my-paper/
ls -la  # Should see: main.tex, neurips.sty, Makefile, etc.
```

Скопіюй **весь** каталог, а не лише файл `.tex`. Шаблони містять файли стилів (`.sty`), стилі бібліографії (`.bst`), зразковий вміст і `Makefile`‑и.

**Крок 2: Переконайся, що шаблон компілюється спочатку**

Перш ніж вносити будь‑які зміни:
```bash
latexmk -pdf main.tex
# Or manual: pdflatex main.tex && bibtex main && pdflatex main.tex && pdflatex main.tex
```

Якщо незмінений шаблон не компілюється, виправ це спочатку (зазвичай бракує пакетів TeX — встанови їх за допомогою `tlmgr install <package>`).

**Крок 3: Залишай вміст шаблону як довідковий**

Не видаляй одразу зразковий вміст. Закоментуй його і використай як довідку щодо форматування:
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

**Крок 4: Замінюй вміст розділ за розділом**

Працюй послідовно: заголовок/автори → анотація → вступ → методи → експерименти → пов’язані роботи → висновки → література → додаток. Компілюй після кожного розділу.

**Крок 5: Використовуй макроси шаблону**

```latex
\newcommand{\method}{YourMethodName}  % Consistent method naming
\newcommand{\eg}{e.g.,\xspace}        % Proper abbreviations
\newcommand{\ie}{i.e.,\xspace}
```
### Підводні камені шаблону

| Підводний камінь | Проблема | Рішення |
|------------------|----------|----------|
| Копіювання лише файлу `.tex` | Відсутній файл `.sty`, не вдається компіляція | Скопіюй весь каталог |
| Зміна файлів `.sty` | Порушує форматування конференції | Ніколи не редагуй файли стилю |
| Додавання випадкових пакетів | Конфлікти, руйнує шаблон | Додавай лише за потреби |
| Видалення вмісту шаблону занадто рано | Втрачаєш орієнтир щодо форматування | Тримай його як коментарі, доки не завершиш |
| Не компілюєш часто | Помилки накопичуються | Компілюй після кожного розділу |
| Растрові PNG для рисунків | Розмиття в статті | Завжди використовуй векторний PDF через `savefig('fig.pdf')` |
### Швидка довідка щодо шаблонів

| Conference | Main File | Style File | Page Limit |
|------------|-----------|------------|------------|
| NeurIPS 2025 | `main.tex` | `neurips.sty` | 9 pages |
| ICML 2026 | `example_paper.tex` | `icml2026.sty` | 8 pages |
| ICLR 2026 | `iclr2026_conference.tex` | `iclr2026_conference.sty` | 9 pages |
| ACL 2025 | `acl_latex.tex` | `acl.sty` | 8 pages (long) |
| AAAI 2026 | `aaai2026-unified-template.tex` | `aaai2026.sty` | 7 pages |
| COLM 2025 | `colm2025_conference.tex` | `colm2025_conference.sty` | 9 pages |

**Універсальний**: Double‑blind, посилання не враховуються, додатки без обмежень, LaTeX обов’язковий.

Шаблони розташовані у каталозі `templates/`. Дивись [templates/README.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/templates/README.md) для налаштувань компіляції (VS Code, CLI, Overleaf, інші IDE).
### Таблиці та рисунки

**Таблиці** — використовуйте `booktabs` для професійного форматування:

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
- Виділяйте жирним найкраще значення за метрикою
- Додавайте символи напрямку ($\uparrow$ вищий — краще, $\downarrow$ нижчий — краще)
- Вирівнюйте числові стовпці праворуч
- Забезпечуйте однакову кількість знаків після коми

**Рисунки**:
- **Векторна графіка** (PDF, EPS) для всіх графіків і діаграм — `plt.savefig('fig.pdf')`
- **Растрова** (PNG, 600 DPI) лише для фотографій
- **Палітри, безпечні для дальтоніків** (Okabe‑Ito або Paul Tol)
- Перевіряйте **читабельність у відтінках сірого** (8 % чоловіків мають порушення кольорового зору)
- **Без заголовка всередині рисунка** — функцію виконує підпис
- **Самодостатні підписи** — читач має зрозуміти їх без основного тексту
### Повторна подача на конференцію

Для конвертації між майданчиками дивись Phase 7 (Submission Preparation) — вона охоплює повний процес конвертації, таблицю змін сторінок та рекомендації після відхилення.
### Професійний LaTeX преамбул

Додай ці пакети до будь‑якої статті для професійної якості. Вони сумісні з усіма основними стилями конференцій:

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

**Примітки:**
- `microtype` — це найбільш впливовий пакет для візуальної якості. Він коригує інтервали між символами на субпіксельному рівні. Завжди підключай його.
- `siunitx` забезпечує вирівнювання десяткових у таблицях за допомогою типу стовпця `S` — усуває ручне розставлення пробілів.
- `cleveref` треба завантажувати **після** `hyperref`. Більшість конференц‑шаблонів `.sty` підключають `hyperref`, тому розмісти `cleveref` останнім.
- Перевір, чи шаблон конференції вже підключає якийсь із цих пакетів (особливо `algorithm`, `amsmath`, `graphicx`). Не підключай їх двічі.
### Вирівнювання таблиць siunitx

`siunitx` робить таблиці, насичені числами, значно більш читабельними:

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

Тип стовпця `S` автоматично вирівнює за десятковою крапкою. Заголовки в `{}` екранують вирівнювання.
### Підфігури

Стандартний шаблон для розміщення фігур поруч:

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

Використовуй `\cref{fig:results}` → «Figure 1», `\cref{fig:results-a}` → «Figure 1a».
### Псевдокод за допомогою algorithm2e

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
### Шаблони діаграм TikZ

TikZ — стандарт для діаграм методів у статтях з ML. Поширені шаблони:

**Діаграма конвеєра/потоку** (найчастіше у статтях з ML):

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

**Діаграма порівняння/матриці** (для показу варіантів методу):

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

**Діаграма ітеративного циклу** (для методів із зворотним зв’язком):

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
### latexdiff for Revision Tracking

Необхідний для оскаржень — генерує розмічений PDF, що показує зміни між версіями:

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

Це створює PDF, у якому видалення позначені червоним перекресленням, а додавання — синім — стандартний формат для додатків до оскарження.
### SciencePlots для matplotlib

Встанови та використай для створення графіків публікаційної якості:

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

**Стандартні розміри фігур** (формат у два стовпці):
- Один стовпець: `figsize=(3.5, 2.5)` — вміщується в один стовпець
- Два стовпці: `figsize=(7.0, 3.0)` — охоплює обидва стовпці
- Квадрат: `figsize=(3.5, 3.5)` — для теплових карт, матриць плутанини

---
## Phase 6: Само‑оцінка та ревізія

**Мета**: Імітувати процес рецензування перед подачею. Виявляти слабкі місця заздалегідь.

### Крок 6.1: Імітація рецензій (Ensemble Pattern)

Генеруй рецензії з кількох перспектив. Ключовий висновок з автоматизованих дослідницьких конвеєрів (зокрема AI‑Scientist від SakanaAI): **ансамбль‑рецензування з мета‑рецензентом дає набагато більш калібровану зворотну звязок, ніж один прохід**.

**Крок 1: Згенерувати N незалежних рецензій** (N=3‑5)

Використовуй різні моделі або налаштування температури. Кожен рецензент бачить лише статтю, без інших рецензій. **За замовчуванням – негативний ухил** – LLM мають добре задокументований позитивний ухил у оцінці.

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

**Крок 2: Мета‑рецензія (агрегація Area Chair)**

Передай усі N рецензії мета‑рецензенту:

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

**Крок 3: Цикл рефлексії** (необов’язково, 2‑3 раунди)

Кожен рецензент може уточнити свою рецензію після ознайомлення з мета‑рецензією. Використай сенсор завершення: якщо рецензент відповідає «I am done» (без змін), зупини ітерації.

**Вибір моделі для рецензування**: Рецензування найкраще виконувати найсильнішою доступною моделлю, навіть якщо статтю писав менш потужний варіант. Модель‑рецензент має обиратись незалежно від моделі‑писача.

**Калібрування few‑shot**: Якщо є, включи 1‑2 реальні опубліковані рецензії з цільового конференційного збірника як приклади. Це значно підвищує точність оцінки. Дивись [references/reviewer‑guidelines.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/reviewer-guidelines.md) для прикладів рецензій.

### Крок 6.1b: Візуальний прохід рецензії (VLM)

Текстове рецензування пропускає цілий клас проблем: якість рисунків, розмітка, візуальна узгодженість. Якщо маєш доступ до моделі, що розуміє зображення, запусти окремий **візуальний огляд** зкомпільованого PDF:

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

Так виявляються проблеми, які текстовий аналіз не помітить: графік з нечіткими підписами осей, рисунок, розташований на 3‑й сторінці після першого посилання, несумісна кольорова палітра між Figure 2 та Figure 5, або таблиця, явно ширша за колонку.

### Крок 6.1c: Перевірка тверджень

Після імітованих рецензій запусти окремий прохід перевірки. Це виявляє фактичні помилки, які рецензенти можуть пропустити:

```
Claim Verification Protocol:
1. Extract every factual claim from the paper (numbers, comparisons, trends)
2. For each claim, trace it to the specific experiment/result that supports it
3. Verify the number in the paper matches the actual result file
4. Flag any claim without a traceable source as [VERIFY]
```

Для агентних робочих процесів: делегуй перевірку **свіжому під‑агенту**, який отримує лише текст статті та сирі результати. Свіжий контекст запобігає упередженості підтвердження — верифікатор не «пам’ятає», які результати мали бути.

### Крок 6.2: Пріоритезація зворотного зв’язку

Після збору рецензій категоризуй:

| Пріоритет | Дія |
|----------|--------|
| **Критичний** (технічна помилка, відсутня базова лінія) | Потрібно виправити. Може знадобитися новий експеримент → повернутись до Phase 2 |
| **Високий** (проблема зрозумілості, відсутня абляція) | Слід виправити в цій ревізії |
| **Середній** (небажані дрібні помилки, додаткові експерименти) | Виправити, якщо є час |
| **Низький** (стильові уподобання, сторонні пропозиції) | Зафіксувати для майбутньої роботи |

### Крок 6.3: Цикл ревізії

Для кожного критичного/високого питання:
1. Визначити конкретний розділ(и), що постраждав(и)
2. Скласти виправлення
3. Перевірити, що виправлення не руйнує інші твердження
4. Оновити статтю
5. Переперевірити проти зауважень рецензента

### Крок 6.4: Написання відповіді (Rebuttal)

Коли відповідаєш на реальні рецензії (після подачі), відповіді – це окремий навик від ревізії:

**Формат**: По‑пунктово. Для кожного зауваження рецензента:
```
> R1-W1: "The paper lacks comparison with Method X."

We thank the reviewer for this suggestion. We have added a comparison with 
Method X in Table 3 (revised). Our method outperforms X by 3.2pp on [metric] 
(p<0.05). We note that X requires 2x our compute budget.
```

**Правила**:
- Відповідай на кожне зауваження — рецензенти помічають, якщо щось пропущено
- Починай з найсильніших відповідей
- Будь лаконічним і прямим — рецензенти читають десятки відповідей
- Додай нові результати, якщо провів експерименти під час періоду відповіді
- Ніколи не будь оборонним або зневажливим, навіть щодо слабких критик
- Використовуй `latexdiff` для генерації PDF з позначеними змінами (дивись розділ Professional LaTeX Tooling)
- Подякуй рецензентам за конкретні, дієві зауваження (а не за загальну похвалу)

**Чого НЕ робити**: «We respectfully disagree» без доказів. «This is out of scope» без пояснення. Ігнорувати слабкість, відповідаючи лише на сильні сторони.

### Крок 6.5: Відстеження еволюції статті

Зберігай знімки на ключових етапах:
```
paper/
  paper.tex                    # Current working version
  paper_v1_first_draft.tex     # First complete draft
  paper_v2_post_review.tex     # After simulated review
  paper_v3_pre_submission.tex  # Final before submission
  paper_v4_camera_ready.tex    # Post-acceptance final
```
## Phase 7: Підготовка до подачі

**Goal**: Останні перевірки, форматування та подача.

### Step 7.1: Конференційний чек‑лист

Кожне місце проведення має обов’язкові чек‑лісти. Заповнюй їх ретельно — неповний чек‑ліст може призвести до відхилення на етапі desk review.

Дивись [references/checklists.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/checklists.md) для:
- 16‑пунктового чек‑ліста NeurIPS
- Більш широкого впливу + відтворюваності ICML
- Політики розкриття LLM ICLR
- Обов’язкового розділу про обмеження ACL
- Універсального чек‑ліста перед подачею

### Step 7.2: Чек‑лист анонімізації

Подвійне сліпе рецензування означає, що рецензенти не повинні знати, хто написав статтю. Перевір **усі** наступні пункти:

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

**Типові помилки**: повідомлення комітів Git, видимі у додатковому коді, водяні знаки на рисунках від інституційних інструментів, подяки, залишені з попереднього чернетки, arXiv‑препринт, розміщений до періоду анонімності.

### Step 7.3: Перевірка форматування

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

### Step 7.4: Перевірка перед компіляцією

Запусти ці автоматичні перевірки **перед** спробою `pdflatex`. Виявлення помилок на цьому етапі швидше, ніж налагодження виводу компілятора.

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

Виправ будь‑які попередження перед продовженням. Для робочих процесів, заснованих на агенті: передай вивід `chktex` агенту з інструкцією виконати мінімальні виправлення.

### Step 7.5: Остання компіляція

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

**Якщо компіляція не вдається**: проаналізуй файл `.log` і знайди першу помилку. Типові виправлення:
- “Undefined control sequence” → відсутній пакет або помилка в назві команди
- “Missing $ inserted” → математичний символ поза математичним режимом
- “File not found” → неправильний шлях до рисунка або відсутній `.sty` файл
- “Citation undefined” → відсутній запис у `.bib` або не запущено `bibtex`

### Step 7.6: Специфічні вимоги конференцій

| Venue | Special Requirements |
|-------|---------------------|
| **NeurIPS** | Чек‑лист статті в додатку, lay summary, якщо прийнято |
| **ICML** | Розділ “Broader Impact” (після висновку, не враховується в ліміті) |
| **ICLR** | Потрібне розкриття LLM, угода про взаємний рецензентський процес |
| **ACL** | Обов’язковий розділ “Limitations”, чек‑лист Responsible NLP |
| **AAAI** | Жорсткий style‑file — без жодних змін |
| **COLM** | Формулювання внеску для спільноти мовних моделей |

### Step 7.7: Переподача та конвертація формату

При переході між конференціями **ніколи не копіюй LaTeX‑преамбули між шаблонами**:

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
| NeurIPS → ICML | 9 → 8 | Відрізати 1 сторінку, додати “Broader Impact” |
| ICML → ICLR | 8 → 9 | Розширити експерименти, додати розкриття LLM |
| NeurIPS → ACL | 9 → 8 | Переструктурувати під NLP‑конвенції, додати “Limitations” |
| ICLR → AAAI | 9 → 7 | Значне скорочення, суворе дотримання стилю |
| Any → COLM | varies → 9 | Переформулювати внесок під фокус мовних моделей |

При скороченні сторінок: перемісти докази в додаток, скоротити розділ “Related Work”, об’єднати таблиці, використати subfigures.
При розширенні: додати абляції, розширити розділ “Limitations”, включити додаткові базові моделі, додати якісні приклади.

**Після відхилення**: врахуй зауваження рецензентів у новій версії, але не додавай розділ “changes” і не посилайся на попередню подачу (слепий процес).

### Step 7.8: Підготовка camera‑ready (після прийняття)

Після прийняття підготуй фінальну camera‑ready версію:

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

### Step 7.9: Стратегія arXiv та препринтів

Розміщення в arXiv — стандартна практика в ML, проте має важливі часові та анонімні аспекти.

**Дерево рішень щодо часу:**

| Situation | Recommendation |
|-----------|-----------------|
| Подання в конференцію з подвійним сліпим рецензуванням (NeurIPS, ICML, ACL) | Розмісти в arXiv **після** дедлайну подачі, а не раніше. Публікація до цього може технічно порушити політику анонімності, хоча її застосування різниться. |
| Подання в ICLR | ICLR явно дозволяє розміщення в arXiv до подачі. Проте не вказуй імена авторів у самій подачі. |
| Стаття вже є в arXiv, подача в нову конференцію | Дозволено в більшості конференцій. НЕ оновлюй версію arXiv під час рецензування, якщо зміни посилаються на відгуки. |
| Робоча стаття (workshop) | arXiv підходить у будь‑який час — воркшопи зазвичай не сліпі. |
| Прагнеш закріпити пріоритет | Розмісти негайно, якщо існує ризик «скоупінгу», — але прийми компроміс анонімності. |

**Вибір категорії arXiv** (ML/AI статті):

| Category | Code | Best For |
|----------|------|----------|
| Machine Learning | `cs.LG` | Загальні методи ML |
| Computation and Language | `cs.CL` | NLP, мовні моделі |
| Artificial Intelligence | `cs.AI` | Розуміння, планування, агенти |
| Computer Vision | `cs.CV` | Візуальні моделі |
| Information Retrieval | `cs.IR` | Пошук, рекомендації |

Наведи основну + 1‑2 крос‑лістовані категорії. Більше категорій — більше видимості, але крос‑лістуй лише, якщо це дійсно релевантно.

**Стратегія версій:**
- **v1**: Початкова подача (відповідає конференційному варіанту)
- **v2**: Після прийняття з виправленнями camera‑ready (додай “accepted at [Venue]” в анотацію)
- Не розміщуй v2 під час рецензування, якщо зміни явно відповідають на відгуки рецензентів

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

### Step 7.10: Пакування дослідницького коду

Публікація чистого, запускаємого коду значно підвищує кількість цитувань та довіру рецензентів. Пакуй код разом з camera‑ready подачею.

**Структура репозиторію:**

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

**Шаблон README для дослідницького коду:**

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

**Чек‑лист перед релізом:**
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

**Анонімний код для подачі** (до прийняття):
```bash
# Use Anonymous GitHub for double-blind review
# https://anonymous.4open.science/
# Upload your repo → get an anonymous URL → put in paper
```
## Phase 8: Post-Acceptance Deliverables

**Goal**: Максимізувати вплив твоєї прийнятої статті за допомогою презентаційних матеріалів та взаємодії з спільнотою.

### Step 8.1: Conference Poster

Більшість конференцій вимагають постерну сесію. Принципи дизайну постеру:

| Element | Guideline |
|---------|-----------|
| **Size** | Перевір вимоги локації (зазвичай 24"x36" або A0 у портреті/ландшафті) |
| **Content** | Назва, автори, 1‑речення про внесок, схема методу, 2‑3 ключові результати, висновок |
| **Flow** | Зліва‑вгорі → справа‑внизу (Z‑патерн) або колонковий |
| **Text** | Назва читається з 3 м, основний текст – з 1 м. Не використовуйте довгі абзаци – лише маркери. |
| **Figures** | Використай фігури зі статті у вищій роздільній здатності. Збільш ключовий результат. |

**Tools**: LaTeX (`beamerposter` package), PowerPoint/Keynote, Figma, Canva.

**Production**: Замовляй за 2+ тижні до конференції. Тканинні постери легші для транспортування. Багато конференцій вже підтримують віртуальні/цифрові постери.

### Step 8.2: Conference Talk / Spotlight

Якщо отримав усну або spotlight‑презентацію:

| Talk Type | Duration | Content |
|-----------|----------|---------|
| **Spotlight** | 5 хв | Проблема, підхід, один ключовий результат. Репетируй точно 5 хв. |
| **Oral** | 15‑20 хв | Повна історія: проблема, підхід, ключові результати, абляції, обмеження. |
| **Workshop talk** | 10‑15 хв | Адаптуй під аудиторію воркшопу – можливо, треба більше бекграунду. |

**Slide design rules:**
- Одна ідея на слайд
- Мінімізуй текст – розповідай деталі усно, не проєктуючи їх
- Анімуй ключові фігури, поступово будуючи розуміння
- Додай слайд «takeaway» в кінці (одне речення про внесок)
- Підготуй резервні слайди для передбачуваних питань

### Step 8.3: Blog Post / Social Media

Доступний підсумок значно підвищує вплив:

- **Twitter/X thread**: 5‑8 твітів. Спочатку покажи результат, а не метод. Додай Figure 1 та фігуру з ключовим результатом.
- **Blog post**: 800‑1500 слів. Пишеться для ML‑практиків, а не для рецензентів. Прибери формалізм, підкресли інтуїцію та практичні наслідки.
- **Project page**: HTML‑сторінка з анотацією, фігурами, демо, посиланням на код, BibTeX. Використовуй GitHub Pages.

**Timing**: Опублікуй протягом 1‑2 днів після появи статті в збірнику або arXiv camera‑ready.
## Workshop & Short Papers

Workshop‑папери та короткі статті (наприклад, ACL short papers, Findings papers) проходять один і той самий процес, проте мають різні обмеження та очікування.

### Workshop Papers

| Властивість | Workshop | Основна конференція |
|------------|----------|----------------------|
| **Ліміт сторінок** | 4‑6 сторінок (зазвичай) | 7‑9 сторінок |
| **Стандарт рецензії** | Нижчий поріг завершеності | Має бути повним, ретельним |
| **Процес рецензії** | Зазвичай single‑blind або легка рецензія | Double‑blind, сувора |
| **Що цінується** | Цікаві ідеї, попередні результати, позиційні статті | Повна емпірична історія зі сильними базовими моделями |
| **arXiv** | Публікація у будь‑який час | Час має значення (див. стратегію arXiv) |
| **Бар’єр внеску** | Новий напрямок, цікава негативна результативність, робота в процесі | Значний прорив з переконливими доказами |

**Коли варто орієнтуватися на workshop:**
- Ідея на ранній стадії, яку хочеш отримати зворотний зв’язок перед повною статтею
- Негативний результат, який не виправдовує 8+ сторінок
- Позиційна стаття або думка щодо актуальної теми
- Реплікаційне дослідження або звіт про відтворюваність

### ACL Short Papers & Findings

У ACL існують різні типи подань:

| Тип | Сторінок | Що очікується |
|-----|----------|----------------|
| **Long paper** | 8 | Повне дослідження, сильні базові моделі, абляції |
| **Short paper** | 4 | Сфокусований внесок: один чіткий пункт з доказами |
| **Findings** | 8 | Якісна робота, що лише не зовсім підходить для основної конференції |

**Стратегія для короткої статті**: вибери ОДНУ гіпотезу і ретельно її підкріпи. Не намагайся втиснути довгу статтю в 4 сторінки — напиши іншу, більш сфокусовану роботу.
## Типи статей, що виходять за межі емпіричного ML

Основний pipeline, описаний вище, орієнтований на емпіричні статті ML. Інші типи статей вимагають різних структур і стандартів доказовості. Дивись [references/paper-types.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/paper-types.md) для докладних рекомендацій щодо кожного типу.

### Теоретичні статті

**Структура**: Вступ → Попередні положення (визначення, нотація) → Основні результати (теореми) → Нотатки доведень → Обговорення → Повні доведення (додаток)

**Ключові відмінності від емпіричних статей:**
- Внесок – це теорема, межа або результат неможливості — не експериментальні цифри
- Розділ «Методи» замінюється на «Попередні положення» та «Основні результати»
- Докази є доказовою базою, а не експериментами (хоча емпірична валідація теорії вітається)
- Нотатки доведень у основному тексті, повні доведення в додатку – стандартна практика
- Розділ «Експериментальний» є необов’язковим, але підсилює статтю, якщо він підтверджує теоретичні передбачення

**Принципи написання доказів:**
- Формально формулюй теореми, вказуючи всі припущення явно
- Надати інтуїцію перед формальним доказом («Ключове розуміння полягає в…»)
- Нотатки доведень мають передати основну ідею на 0,5–1 сторінці
- Використовуй середовища `\begin{proof}...\end{proof}`
- Нумеруй припущення і посилайся на них у теоремах: «За припущеннями 1‑3, …»

### Оглядові / навчальні статті

**Структура**: Вступ → Таксономія / Організація → Детальне охоплення → Відкриті проблеми → Висновок

**Ключові відмінності:**
- Внесок – це організація, синтез і виявлення відкритих проблем, а не нові методи
- Має бути всебічним у межах теми (рецензенти перевірятимуть відсутність важливих посилань)
- Потрібна чітка таксономія або організаційна рамка
- Цінність полягає у зв’язках між роботами, які окремі статті не роблять
- Найкращі майданчики: TMLR (track оглядів), JMLR, Foundations and Trends in ML, ACM Computing Surveys

### Статті про бенчмарки

**Структура**: Вступ → Визначення завдання → Створення набору даних → Оцінка базових моделей → Аналіз → Передбачуване використання та обмеження

**Ключові відмінності:**
- Внесок – сам бенчмарк, який має заповнювати реальну прогалину в оцінюванні
- Документація набору даних є обов’язковою, а не опційною (див. Datasheets, крок 5.11)
- Потрібно продемонструвати, що бенчмарк складний (базові моделі не досягають його меж)
- Потрібно показати, що бенчмарк вимірює саме те, що заявлено (конструктна валідність)
- Найкращі майданчики: NeurIPS Datasets & Benchmarks track, ACL (resource papers), LREC‑COLING

### Позиційні статті

**Структура**: Вступ → Фон → Тезис / Аргумент → Підтримуючі докази → Контраргументи → Наслідки

**Ключові відмінності:**
- Внесок – аргумент, а не результат
- Потрібно серйозно працювати з контраргументами
- Докази можуть бути емпіричними, теоретичними або логічними аналізами
- Найкращі майданчики: ICML (track позицій), воркшопи, TMLR
## Hermes Agent Integration

Цей **skill** розроблений для агента Hermes. Він використовує інструменти Hermes, делегування, планування та **memory** для повного життєвого циклу дослідження.

### Пов’язані skills

Скомпонуй цей **skill** з іншими **skills** Hermes для конкретних фаз:

| Skill | Коли використовувати | Як завантажити |
|-------|----------------------|----------------|
| **arxiv** | Фаза 1 (Огляд літератури): пошук в arXiv, генерація BibTeX, пошук пов’язаних статей через Semantic Scholar | `skill_view("arxiv")` |
| **subagent-driven-development** | Фаза 5 (Написання чернетки): паралельне написання розділів з 2‑етапним рецензуванням (відповідність специфікації, потім якість) | `skill_view("subagent-driven-development")` |
| **plan** | Фаза 0 (Налаштування): створення структурованих планів перед виконанням. Записує у `.hermes/plans/` | `skill_view("plan")` |
| **qmd** | Фаза 1 (Література): пошук у локальних базах знань (нотатки, транскрипти, документи) за допомогою гібридного пошуку BM25+vector | Install: `skill_manage("install", "qmd")` |
| **diagramming** | Фази 4‑5: створення фігур та діаграм архітектури на базі Excalidraw | `skill_view("diagramming")` |
| **data-science** | Фаза 4 (Аналіз): живе ядро Jupyter для інтерактивного аналізу та візуалізації | `skill_view("data-science")` |

**Цей skill замінює `ml-paper-writing`** — він містить весь вміст `ml-paper-writing` плюс повний конвеєр експерименту/аналізу та методологію автодоказу.

### Довідник інструментів Hermes

| Tool | Використання в цьому конвеєрі |
|------|--------------------------------|
| **`terminal`** | Компіляція LaTeX (`latexmk -pdf`), операції git, запуск експериментів (`nohup python run.py &`), перевірка процесів |
| **`process`** | Управління фоновими експериментами: `process("start", ...)`, `process("poll", pid)`, `process("log", pid)`, `process("kill", pid)` |
| **`execute_code`** | Запуск Python для перевірки цитат, статистичного аналізу, агрегації даних. Має доступ до інструменту через RPC. |
| **`read_file`** / **`write_file`** / **`patch`** | Редагування статті, скриптів експериментів, файлів результатів. Використовуй `patch` для цільових правок великих `.tex`‑файлів. |
| **`web_search`** | Пошук літератури: `web_search("transformer attention mechanism 2024")` |
| **`web_extract`** | Отримання вмісту статті, перевірка цитат: `web_extract("https://arxiv.org/abs/2303.17651")` |
| **`delegate_task`** | **Паралельне написання розділів** — створює ізольовані **subagents** для кожного розділу. Також використовується для одночасної перевірки цитат. |
| **`todo`** | Основний трекер стану між сесіями. Оновлюється після кожного переходу фази. |
| **`memory`** | Зберігає ключові рішення між сесіями: формулювання внеску, вибір журналу, відгуки рецензентів. |
| **`cronjob`** | Планування моніторингу експериментів, відліку дедлайнів, автоматичних перевірок arXiv. |
| **`clarify`** | Задає користувачеві цільові питання, коли блоковано (вибір журналу, формулювання внеску). |
| **`send_message`** | Сповіщає користувача, коли експерименти завершені або чернетки готові, навіть якщо користувач не в чаті. |

### Шаблони використання інструментів

**Моніторинг експериментів** (найчастіше):
```
terminal("ps aux | grep <pattern>")
→ terminal("tail -30 <logfile>")
→ terminal("ls results/")
→ execute_code("analyze results JSON, compute metrics")
→ terminal("git add -A && git commit -m '<descriptive message>' && git push")
→ send_message("Experiment complete: <summary>")
```

**Паралельне написання розділів** (за допомогою делегування):
```
delegate_task("Draft the Methods section based on these experiment scripts and configs. 
  Include: pseudocode, all hyperparameters, architectural details sufficient for 
  reproduction. Write in LaTeX using the neurips2025 template conventions.")

delegate_task("Draft the Related Work section. Use web_search and web_extract to 
  find papers. Verify every citation via Semantic Scholar. Group by methodology.")

delegate_task("Draft the Experiments section. Read all result files in results/. 
  State which claim each experiment supports. Include error bars and significance.")
```

Кожен делегат працює як **новий subagent** без спільного контексту — передай всю необхідну інформацію у підказці. Збери вихідні дані та інтегруй їх.

**Перевірка цитат** (за допомогою `execute_code`):
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

### Управління станом за допомогою `memory` та `todo`

**Інструмент `memory`** — зберігає ключові рішення (обмежено ≈ 2200 символів для `MEMORY.md`):
```
memory("add", "Paper: autoreason. Venue: NeurIPS 2025 (9 pages). 
  Contribution: structured refinement works when generation-evaluation gap is wide.
  Key results: Haiku 42/42, Sonnet 3/5, S4.6 constrained 2/3.
  Status: Phase 5 — drafting Methods section.")
```

Оновлюй **memory** після важливих рішень або переходів фаз. Це зберігається між сесіями.

**Інструмент `todo`** — відстежує детальний прогрес:
```
todo("add", "Design constrained task experiments for Sonnet 4.6")
todo("add", "Run Haiku baseline comparison")
todo("add", "Draft Methods section")
todo("update", id=3, status="in_progress")
todo("update", id=1, status="completed")
```

**Протокол запуску сесії:**
```
1. todo("list")                           # Check current task list
2. memory("read")                         # Recall key decisions
3. terminal("git log --oneline -10")      # Check recent commits
4. terminal("ps aux | grep python")       # Check running experiments
5. terminal("ls results/ | tail -20")     # Check for new results
6. Report status to user, ask for direction
```

### Моніторинг за допомогою `cronjob`

Використовуй інструмент `cronjob` для планування періодичних перевірок експериментів:
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

**Протокол `[SILENT]`**: коли з останньої перевірки нічого не змінилося, відповідай точно `[SILENT]`. Це придушує надсилання сповіщень користувачеві. Повідомляй лише про реальні зміни, які варто знати.

**Відстеження дедлайнів:**
```
cronjob("create", {
  "schedule": "0 9 * * *",  # Daily at 9am
  "prompt": "NeurIPS 2025 deadline: May 22. Today is {date}. 
    Days remaining: {compute}. 
    Check todo list — are we on track? 
    If <7 days: warn user about remaining tasks."
})
```

### Шаблони комунікації

**Коли сповіщати користувача** (через `send_message` або пряму відповідь):
- Завершено пакет експериментів (з таблицею результатів)
- Неочікуване відкриття або помилка, що потребує рішення
- Розділ чернетки готовий до рецензії
- Наближається дедлайн з незавершеними завданнями

**Коли НЕ сповіщати:**
- Експеримент ще виконується, нових результатів немає → `[SILENT]`
- Рутинний моніторинг без змін → `[SILENT]`
- Проміжні кроки, які не потребують уваги

**Формат звіту** — завжди включай структуровані дані:
```
## Experiment: <name>
Status: Complete / Running / Failed

| Task | Method A | Method B | Method C |
|------|---------|---------|---------|
| Task 1 | 85.2 | 82.1 | **89.4** |

Key finding: <one sentence>
Next step: <what happens next>
```

### Точки прийняття рішень, що вимагають людського вводу

Використовуй `clarify` для цільових питань, коли дійсно заблоковано:

| Рішення | Коли запитувати |
|----------|----------------|
| Цільовий журнал | Перед початком написання статті (впливає на обмеження сторінок, формулювання) |
| Формулювання внеску | Коли існує кілька валідних варіантів |
| Пріоритет експериментів | Коли список `todo` містить більше експериментів, ніж часу |
| Готовність до подачі | Перед остаточною подачею |

**Не запитуй про** (будь проактивним, приймай рішення, позначай це):
- Вибір слів, порядок розділів
- Які саме результати підкреслити
- Повноту цитат (створи чернетку з тим, що знайдено, познач недоліки)
## Критерії оцінки рецензентом

Розуміння того, що шукають рецензенти, допомагає зосередити зусилля:

| Критерій | Що вони перевіряють |
|-----------|----------------------|
| **Quality** | Якість: технічна обґрунтованість, добре підкріплені твердження, справедливі базові лінії |
| **Clarity** | Зрозумілість: чітке викладення, можливість відтворення експертами, послідовна нотація |
| **Significance** | Значимість: вплив на спільноту, просування розуміння |
| **Originality** | Оригінальність: нові інсайти (не обов’язково новий метод) |

**Оцінювання (шкала NeurIPS, 6 балів):**
- 6: Strong Accept — видатний, бездоганний
- 5: Accept — технічно якісний, високий вплив
- 4: Borderline Accept — якісний, обмежена оцінка
- 3: Borderline Reject — недоліки переважають
- 2: Reject — технічні недоліки
- 1: Strong Reject — відомі результати або етичні проблеми

Дивись [references/reviewer-guidelines.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/reviewer-guidelines.md) для докладних вказівок, типових зауважень та стратегій відповіді.
## Поширені проблеми та рішення

| Проблема | Рішення |
|-------|----------|
| Абстракт занадто загальний | Видали перше речення, якщо воно може бути застосоване до будь‑якої статті з ML. Почни з конкретного внеску. |
| Вступ перевищує 1,5 сторінки | Поділи фон на розділ «Пов’язані роботи». Перенеси основні пункти внеску на початок. |
| Експерименти не містять явних тверджень | Додай: «Цей експеримент перевіряє, чи [конкретне твердження]…» перед кожним з них. |
| Рецензенти вважають статтю важкою для сприйняття | Додай сигнальні маркери, використай послідовну термінологію, зроби підписи до рисунків самодостатніми. |
| Відсутня статистична значущість | Додай смуги помилок, кількість запусків, статистичні тести, довірчі інтервали. |
| Розширення сфери експериментів | Кожен експеримент має відповідати конкретному твердженню. Прибери експерименти, які не відповідають. |
| Статтю відхилено, потрібно повторно подати | Дивись «Conference Resubmission» у Phase 7. Врахуй зауваження рецензентів без посилань на їхні відгуки. |
| Відсутня заява про ширший вплив | Дивись Step 5.10. Більшість конференцій вимагає її. «Немає негативних впливів» майже ніколи не є достовірним. |
| Оцінка людиною вважається слабкою | Дивись Step 2.5 та [references/human-evaluation.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/human-evaluation.md). Наведи метрики згоди, деталі анотаторів, компенсацію. |
| Рецензенти ставлять під сумнів відтворюваність | Опублікуй код (Step 7.9), задокументуй усі гіперпараметри, включи seeds та деталі обчислень. |
| Теоретична стаття не має інтуїції | Додай ескізи доказів з поясненнями простими словами перед формальними доказами. Дивись [references/paper-types.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/paper-types.md). |
| Результати негативні/нульові | Дивись Phase 4.3 щодо роботи з негативними результатами. Розглянь воркшопи, TMLR або переоформлення як аналіз. |
## Довідкові документи

| Документ | Вміст |
|----------|----------|
| [references/writing-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/writing-guide.md) | Gopen & Swan – 7 принципів, мікро‑поради Perez, вибір слів Lipton, точність Steinhardt, дизайн рисунків |
| [references/citation-workflow.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/citation-workflow.md) | Citation APIs, Python‑код, клас `CitationManager`, управління BibTeX |
| [references/checklists.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/checklists.md) | 16‑пунктовий чек‑лист NeurIPS, вимоги ICML, ICLR, ACL, універсальний чек‑лист перед подачею |
| [references/reviewer-guidelines.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/reviewer-guidelines.md) | Критерії оцінки, система балів, типові зауваження, шаблон відповіді |
| [references/sources.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/sources.md) | Повна бібліографія всіх посібників з написання, вимоги конференцій, API |
| [references/experiment-patterns.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/experiment-patterns.md) | Шаблони дизайну експериментів, протоколи оцінки, моніторинг, відновлення після помилок |
| [references/autoreason-methodology.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/autoreason-methodology.md) | Autoreason loop, вибір стратегії, керівництво моделлю, підказки, обмеження області, оцінка Борда |
| [references/human-evaluation.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/human-evaluation.md) | Дизайн людської оцінки, інструкції для анотації, метрики узгодженості, контроль якості краудсорсингу, рекомендації IRB |
| [references/paper-types.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/references/paper-types.md) | Теоретичні статті (написання доказів, структура теорем), оглядові статті, статті‑бенчмарки, позиційні статті |

### Шаблони LaTeX

Шаблони у `templates/` для: **NeurIPS 2025**, **ICML 2026**, **ICLR 2026**, **ACL**, **AAAI 2026**, **COLM 2025**.

Дивись [templates/README.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/research/research-paper-writing/templates/README.md) для інструкцій зі збірки.

### Ключові зовнішні джерела

**Філософія написання:**
- [Neel Nanda: How to Write ML Papers](https://www.alignmentforum.org/posts/eJGptPbbFPZGLpjsp/highly-opinionated-advice-on-how-to-write-ml-papers)
- [Sebastian Farquhar: How to Write ML Papers](https://sebastianfarquhar.com/on-research/2024/11/04/how_to_write_ml_papers/)
- [Gopen & Swan: Science of Scientific Writing](https://cseweb.ucsd.edu/~swanson/papers/science-of-writing.pdf)
- [Lipton: Heuristics for Scientific Writing](https://www.approximatelycorrect.com/2018/01/29/heuristics-technical-scientific-writing-machine-learning-perspective/)
- [Perez: Easy Paper Writing Tips](https://ethanperez.net/easy-paper-writing-tips/)

**API:** [Semantic Scholar](https://api.semanticscholar.org/api-docs/) | [CrossRef](https://www.crossref.org/documentation/retrieve-metadata/rest-api/) | [arXiv](https://info.arxiv.org/help/api/basics.html)

**Конференції:** [NeurIPS](https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles) | [ICML](https://icml.cc/Conferences/2025/AuthorInstructions) | [ICLR](https://iclr.cc/Conferences/2026/AuthorGuide) | [ACL](https://github.com/acl-org/acl-style-files)