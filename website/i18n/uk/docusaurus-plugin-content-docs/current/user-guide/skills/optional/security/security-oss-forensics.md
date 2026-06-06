---
title: "Oss Forensics — розслідування ланцюжка постачання, відновлення доказів та судово‑експертний аналіз репозиторіїв GitHub"
sidebar_label: "Oss Forensics"
description: "Розслідування ланцюжка постачання, відновлення доказів та судово‑експертний аналіз репозиторіїв GitHub"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Oss Forensics

Розслідування ланцюжка постачання, відновлення доказів та форензійний аналіз репозиторіїв GitHub.
Охоплює відновлення видалених комітів, виявлення force‑push, вилучення IOC, збір доказів з кількох джерел, формування та перевірку гіпотез і структуровану форензійну звітність.
Натхнено системою OSS Forensics RAPTOR, що містить понад 1800 рядків коду.
## Метадані навички

| | |
|---|---|
| Джерело | Необов’язково — install with `hermes skills install official/security/oss-forensics` |
| Шлях | `optional-skills/security/oss-forensics` |
| Платформи | linux, macos, windows |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Навичка OSS Security Forensics

7‑фазовий багатоагентний фреймворк розслідувань для дослідження атак на ланцюжки постачання відкритого коду.
Адаптовано з системи форензіки RAPTOR. Охоплює GitHub Archive, Wayback Machine, GitHub API, локальний аналіз git, вилучення IOC, формування та валідацію гіпотез на підставі доказів і створення фінального форензічного звіту.

---
## ⚠️ Захисні бар’єри проти галюцинацій

Прочитай їх перед кожним кроком розслідування. Порушення цих правил анулює звіт.

1. **Правило «Доказ спочатку»**: Кожна заява в будь‑якому звіті, гіпотезі чи резюме ПОВИННА містити принаймні один ідентифікатор доказу (`EV-XXXX`). Твердження без посилань заборонені.
2. **ТРИМАЙСЯ СВОЇХ ОБОВ’ЯЗК**: Кожен під‑агент (розслідувач) має єдине джерело даних. НЕ змішуй джерела. Розслідувач GH Archive не запитує GitHub API, і навпаки. Межі ролей жорсткі.
3. **Розмежування фактів і гіпотез**: Позначай усі неперевірені висновки міткою `[HYPOTHESIS]`. Тільки твердження, підтверджені оригінальними джерелами, можуть бути подані як факти.
4. **Не вигадуй доказів**: Валідатор гіпотез ПОВИНЕН механічно перевіряти, що кожен зазначений ідентифікатор доказу дійсно існує у сховищі доказів, перш ніж приймати гіпотезу.
5. **Необхідність доказу для спростування**: Гіпотезу не можна відхилити без конкретного, підкріпленого доказами контраргументу. «Доказів не знайдено» недостатньо для спростування — це лише робить гіпотезу невизначеною.
6. **Подвійна перевірка SHA/URL**: Будь‑який SHA коміту, URL або зовнішній ідентифікатор, зазначений як доказ, має бути незалежно підтверджений принаймні з двох джерел, перш ніж вважатися перевіреним.
7. **Правило підозрілої коду**: Ніколи не запускай код, знайдений у досліджуваному репозиторії, локально. Аналізуй лише статично або використай `execute_code` у пісочниці.
8. **Редагування секретів**: Будь‑які API‑ключі, токени чи облікові дані, виявлені під час розслідування, мають бути замасковані у фінальному звіті. Внутрішньо їх зберігай лише в логах.
## Приклади сценаріїв

- **Сценарій A: Dependency Confusion**: Шкідливий пакет `internal-lib-v2` завантажується в NPM з вищою версією, ніж внутрішня. Досліднику потрібно відстежити, коли цей пакет був вперше помічений і чи оновив якийсь PushEvent у цільовому репозиторії `package.json` до цієї версії.
- **Сценарій B: Maintainer Takeover**: Обліковий запис довгострокового учасника використовується для пуша файлу `.github/workflows/build.yml` з бекдором. Дослідник шукає PushEvents від цього користувача після тривалого періоду неактивності або з нової IP‑адреси/локації (за можливості визначити через BigQuery).
- **Сценарій C: Force‑Push Hide**: Розробник випадково комітить секрет продакшн, потім виконує force‑push, щоб «виправити» його. Дослідник використовує `git fsck` і GH Archive, щоб відновити оригінальний SHA коміту і перевірити, що саме було витекло.

---

> **Конвенція шляху**: Протягом цього skill `SKILL_DIR` посилається на кореневу директорію встановлення цього skill (тека, що містить цей `SKILL.md`). Коли skill завантажується, розв’язуйте `SKILL_DIR` у фактичний шлях — напр., `~/.hermes/skills/security/oss-forensics/` або еквівалент у `optional-skills/`. Усі посилання на скрипти та шаблони є відносними до нього.
## Фаза 0: Ініціалізація

1. Створи робочий каталог розслідування:
   ```bash
   mkdir investigation_$(echo "REPO_NAME" | tr '/' '_')
   cd investigation_$(echo "REPO_NAME" | tr '/' '_')
   ```
2. Ініціалізуй сховище доказів:
   ```bash
   python3 SKILL_DIR/scripts/evidence-store.py --store evidence.json list
   ```
3. Скопіюй шаблон форензічного звіту:
   ```bash
   cp SKILL_DIR/templates/forensic-report.md ./investigation-report.md
   ```
4. Створи файл `iocs.md` для відстеження індикаторів компрометації у процесі їх виявлення.
5. Запиши час початку розслідування, цільовий репозиторій та заявлену мету розслідування.

---
## Фаза 1: Аналіз запиту та витягнення IOC

**Мета**: Витягнути всі структуровані цілі розслідування з запиту користувача.

**Дії**:
- Проаналізувати запит користувача та витягнути:
  - Цільовий репозиторій (`owner/repo`)
  - Цільові актори (GitHub‑імена, електронні адреси)
  - Часове вікно інтересу (діапазони дат комітів, часові мітки PR)
  - Надані індикатори компрометації: SHA комітів, шляхи файлів, назви пакетів, IP‑адреси, домени, API‑ключі/токени, шкідливі URL‑и
  - Будь‑які пов’язані звіти безпеки від постачальників або публікації в блогах

**Інструменти**: Лише розумові процеси, або `execute_code` для застосування регулярних виразів до великих блоків тексту.

**Вихід**: Заповнити `iocs.md` витягнутими IOC. Кожен IOC має містити:
- Тип (з: COMMIT_SHA, FILE_PATH, API_KEY, SECRET, IP_ADDRESS, DOMAIN, PACKAGE_NAME, ACTOR_USERNAME, MALICIOUS_URL, OTHER)
- Значення
- Джерело (надано користувачем, виведено)

**Посилання**: Дивись [evidence-types.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/evidence-types.md) для таксономії IOC.
## Phase 2: Parallel Evidence Collection

Запусти до 5 спеціалізованих під‑агентів‑розслідувачів за допомогою `delegate_task` (batch mode, максимум 3 одночасно). Кожен розслідувач має **єдине джерело даних** і не повинен змішувати їх.

> **Примітка оркестратора**: Передай список IOC з Phase 1 та часове вікно розслідування у полі `context` кожного делегованого завдання.

---

### Investigator 1: Local Git Investigator

**ROLE BOUNDARY**: Запитуй лише **LOCAL GIT REPOSITORY**. Не викликай зовнішні API.

**Actions**:
```bash
# Clone repository
git clone https://github.com/OWNER/REPO.git target_repo && cd target_repo

# Full commit log with stats
git log --all --full-history --stat --format="%H|%ae|%an|%ai|%s" > ../git_log.txt

# Detect force-push evidence (orphaned/dangling commits)
git fsck --lost-found --unreachable 2>&1 | grep commit > ../dangling_commits.txt

# Check reflog for rewritten history
git reflog --all > ../reflog.txt

# List ALL branches including deleted remote refs
git branch -a -v > ../branches.txt

# Find suspicious large binary additions
git log --all --diff-filter=A --name-only --format="%H %ai" -- "*.so" "*.dll" "*.exe" "*.bin" > ../binary_additions.txt

# Check for GPG signature anomalies
git log --show-signature --format="%H %ai %aN" > ../signature_check.txt 2>&1
```

**Evidence to collect** (додай за допомогою `python3 SKILL_DIR/scripts/evidence-store.py add`):
- Кожен «висілий» SHA коміту → type: `git`
- Докази force‑push (reflog, що показує перепис історії) → type: `git`
- Непідписані коміти від перевірених контрибуторів → type: `git`
- Підозрілі додавання бінарних файлів → type: `git`

**Reference**: Див. [recovery-techniques.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/recovery-techniques.md) щодо отримання force‑pushed комітів.

---

### Investigator 2: GitHub API Investigator

**ROLE BOUNDARY**: Запитуй лише **GITHUB REST API**. Не виконуй git‑команди локально.

**Actions**:
```bash
# Commits (paginated)
curl -s "https://api.github.com/repos/OWNER/REPO/commits?per_page=100" > api_commits.json

# Pull Requests including closed/deleted
curl -s "https://api.github.com/repos/OWNER/REPO/pulls?state=all&per_page=100" > api_prs.json

# Issues
curl -s "https://api.github.com/repos/OWNER/REPO/issues?state=all&per_page=100" > api_issues.json

# Contributors and collaborator changes
curl -s "https://api.github.com/repos/OWNER/REPO/contributors" > api_contributors.json

# Repository events (last 300)
curl -s "https://api.github.com/repos/OWNER/REPO/events?per_page=100" > api_events.json

# Check specific suspicious commit SHA details
curl -s "https://api.github.com/repos/OWNER/REPO/git/commits/SHA" > commit_detail.json

# Releases
curl -s "https://api.github.com/repos/OWNER/REPO/releases?per_page=100" > api_releases.json

# Check if a specific commit exists (force-pushed commits may 404 on commits/ but succeed on git/commits/)
curl -s "https://api.github.com/repos/OWNER/REPO/commits/SHA" | jq .sha
```

**Cross‑reference targets** (позначай розбіжності як доказ):
- PR є в архіві, але відсутній в API → доказ видалення
- Контрибутор є в архівних подіях, але не в списку contributors → доказ відкликання прав
- Коміт є в архівних PushEvents, але не в списку комітів API → доказ force‑push/видалення

**Reference**: Див. [evidence-types.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/evidence-types.md) щодо типів подій GH.

---

### Investigator 3: Wayback Machine Investigator

**ROLE BOUNDARY**: Запитуй лише **WAYBACK MACHINE CDX API**. Не використовуйте GitHub API.

**Goal**: Відновити видалені сторінки GitHub (README, issues, PR, releases, wiki‑сторінки).

**Actions**:
```bash
# Search for archived snapshots of the repo main page
curl -s "https://web.archive.org/cdx/search/cdx?url=github.com/OWNER/REPO&output=json&limit=100&from=YYYYMMDD&to=YYYYMMDD" > wayback_main.json

# Search for a specific deleted issue
curl -s "https://web.archive.org/cdx/search/cdx?url=github.com/OWNER/REPO/issues/NUM&output=json&limit=50" > wayback_issue_NUM.json

# Search for a specific deleted PR
curl -s "https://web.archive.org/cdx/search/cdx?url=github.com/OWNER/REPO/pull/NUM&output=json&limit=50" > wayback_pr_NUM.json

# Fetch the best snapshot of a page
# Use the Wayback Machine URL: https://web.archive.org/web/TIMESTAMP/ORIGINAL_URL
# Example: https://web.archive.org/web/20240101000000*/github.com/OWNER/REPO

# Advanced: Search for deleted releases/tags
curl -s "https://web.archive.org/cdx/search/cdx?url=github.com/OWNER/REPO/releases/tag/*&output=json" > wayback_tags.json

# Advanced: Search for historical wiki changes
curl -s "https://web.archive.org/cdx/search/cdx?url=github.com/OWNER/REPO/wiki/*&output=json" > wayback_wiki.json
```

**Evidence to collect**:
- Заархівовані знімки видалених issues/PR разом із їх вмістом
- Історичні версії README, що показують зміни
- Докази того, що контент є в архіві, а в поточному стані GitHub його немає

**Reference**: Див. [github-archive-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/github-archive-guide.md) щодо параметрів CDX API.

---

### Investigator 4: GH Archive / BigQuery Investigator

**ROLE BOUNDARY**: Запитуй лише **GITHUB ARCHIVE** через **BIGQUERY**. Це захищений від підробки журнал усіх публічних подій GitHub.

> **Prerequisites**: Потрібні облікові дані Google Cloud з доступом до BigQuery (`gcloud auth application-default login`). Якщо їх немає, пропусти цього розслідувача і зазнач це у звіті.

**Cost Optimization Rules** (ОБОВ’ЯЗКОВО):
1. Завжди виконуй `--dry_run` перед кожним запитом, щоб оцінити вартість.
2. Використовуй `_TABLE_SUFFIX` для фільтрації за діапазоном дат і мінімізації сканованих даних.
3. SELECT лише потрібні стовпці.
4. Додавай LIMIT, якщо не виконуєш агрегування.

```bash
# Template: safe BigQuery query for PushEvents to OWNER/REPO
bq query --use_legacy_sql=false --dry_run "
SELECT created_at, actor.login, payload.commits, payload.before, payload.head,
       payload.size, payload.distinct_size
FROM \`githubarchive.month.*\`
WHERE _TABLE_SUFFIX BETWEEN 'YYYYMM' AND 'YYYYMM'
  AND type = 'PushEvent'
  AND repo.name = 'OWNER/REPO'
LIMIT 1000
"
# If cost is acceptable, re-run without --dry_run

# Detect force-pushes: zero-distinct_size PushEvents mean commits were force-erased
# payload.distinct_size = 0 AND payload.size > 0 → force push indicator

# Check for deleted branch events
bq query --use_legacy_sql=false "
SELECT created_at, actor.login, payload.ref, payload.ref_type
FROM \`githubarchive.month.*\`
WHERE _TABLE_SUFFIX BETWEEN 'YYYYMM' AND 'YYYYMM'
  AND type = 'DeleteEvent'
  AND repo.name = 'OWNER/REPO'
LIMIT 200
"
```

**Evidence to collect**:
- Події force‑push (payload.size > 0, payload.distinct_size = 0)
- DeleteEvents для гілок/тегів
- WorkflowRunEvents, що вказують на підозрілу CI/CD‑автоматизацію
- PushEvents, що передують «проміжку» в git‑логах (доказ перепису)

**Reference**: Див. [github-archive-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/github-archive-guide.md) щодо 12 типів подій і шаблонів запитів.

---

### Investigator 5: IOC Enrichment Investigator

**ROLE BOUNDARY**: Збагачуй **EXISTING IOCs** з Phase 1, використовуючи лише пасивні публічні джерела. Не виконуй жодного коду з цільового репозиторію.

**Actions**:
- Для кожного SHA коміту: спробуй відновити його за прямим URL GitHub (`github.com/OWNER/REPO/commit/SHA.patch`)
- Для кожного домену/IP: перевір пасивний DNS, WHOIS (через `web_extract` на публічних WHOIS‑сервісах)
- Для кожного назви пакету: перевір npm/PyPI на наявність шкідливих пакетів
- Для кожного імені користувача‑актору: перевір профіль GitHub, історію внесків, вік акаунту
- Віднови force‑pushed коміти за допомогою 3 методів (див. [recovery-techniques.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/recovery-techniques.md))
## Phase 3: Консолідація доказів

Після завершення роботи всіх розслідувачів:

1. Запусти `python3 SKILL_DIR/scripts/evidence-store.py --store evidence.json list`, щоб переглянути всі зібрані докази.
2. Для кожного доказу перевір, чи збігається хеш `content_sha256` з оригінальним джерелом.
3. Групуй докази за:
   - **Timeline**: сортуй усі докази з мітками часу хронологічно;
   - **Actor**: групуй за GitHub‑handle або електронною поштою;
   - **IOC**: пов’язуй докази з відповідним IOC.
4. Визнач **невідповідності**: елементи, які присутні в одному джерелі, але відсутні в іншому (індикатори видалення ключа).
5. Познач докази як `[VERIFIED]` (підтверджено з 2+ незалежних джерел) або `[UNVERIFIED]` (лише одне джерело).
## Phase 4: Формування гіпотези

Гіпотеза повинна:
- Формулювати конкретне твердження (наприклад, «Actor X force‑pushed to `BRANCH` on `DATE` to erase commit `SHA`»)
- Посилатися принаймні на 2 ідентифікатори доказів, які її підтримують (`EV-XXXX`, `EV-YYYY`)
- Визначати, які докази її спростують
- Мати мітку `[HYPOTHESIS]` до моменту валідації

**Типові шаблони гіпотез** (див. [investigation-templates.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/investigation-templates.md)):
- Компрометація супроводжувача: легітимний обліковий запис використано після захоплення для ін’єкції шкідливого коду
- Dependency Confusion: зайняття назви пакету з метою перехоплення інсталяцій
- CI/CD Injection: шкідливі зміни у workflow, що виконуються під час збірок
- Typosquatting: майже ідентична назва пакету, спрямована на користувачів‑опечатників
- Credential Leak: токен/ключ випадково закомічено, а потім force‑pushed для стирання

Для кожної гіпотези створюй під‑агент `delegate_task`, який спробує знайти спростовуючі докази перед підтвердженням.
## Фаза 5: Перевірка гіпотез

Підагент‑валідатор ПОВИНЕН механічно перевіряти:

1. Для кожної гіпотези витягнути всі зазначені ідентифікатори доказів.
2. Перевірити, чи існує кожен ідентифікатор у `evidence.json` (жорстка помилка, якщо будь‑який ідентифікатор відсутній → гіпотеза відхилена як потенційно сфабрикована).
3. Перевірити, чи кожен доказ з міткою `[VERIFIED]` підтверджений 2‑ма і більше джерелами.
4. Перевірити логічну послідовність: чи підтримує хронологія, зображена в доказах, гіпотезу?
5. Перевірити альтернативні пояснення: чи може той самий шаблон доказів виникнути внаслідок безпечної причини?

**Вихід**:
- `VALIDATED`: Усі докази зазначені, підтверджені, логічно послідовні, немає правдоподібних альтернативних пояснень.
- `INCONCLUSIVE`: Докази підтримують гіпотезу, але існують альтернативні пояснення або доказів недостатньо.
- `REJECTED`: Відсутні ідентифікатори доказів, непідтверджені докази зазначені як факти, виявлена логічна несумісність.

Відхилені гіпотези повертаються у Фазу 4 для уточнення (максимум 3 ітерації).
## Фаза 6: Генерація фінального звіту

Заповни `investigation-report.md`, використовуючи шаблон у [forensic-report.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/templates/forensic-report.md).

**Обов’язкові розділи**:
- **Executive Summary**: один абзац‑висновок (Compromised / Clean / Inconclusive) з рівнем впевненості
- **Timeline**: хронологічна реконструкція всіх значущих подій з посиланнями на докази
- **Validated Hypotheses**: кожна гіпотеза з статусом та ідентифікаторами підтримуючих доказів
- **Evidence Registry**: таблиця всіх записів `EV-XXXX` з джерелом, типом та статусом верифікації
- **IOC List**: усі витягнуті та збагачені індикатори компрометації
- **Chain of Custody**: як збирали докази, з яких джерел і в який час
- **Recommendations**: негайні заходи щодо пом’якшення, якщо виявлено компрометацію; рекомендації щодо моніторингу

**Правила складання звіту**:
- Кожне фактичне твердження має мати принаймні одне посилання `[EV-XXXX]`
- У розділі **Executive Summary** потрібно вказати рівень впевненості (High / Medium / Low)
- Усі секрети/облікові дані мають бути замасковані як `[REDACTED]`
## Phase 7: Completion

1. Запусти підрахунок остаточних доказів: `python3 SKILL_DIR/scripts/evidence-store.py --store evidence.json list`
2. Заархівуй повний каталог розслідування.
3. Якщо компрометація підтверджена:
   - Перерахуйте негайні заходи пом’якшення (повернути облікові дані, зафіксувати хеші залежностей, повідомити постраждалих користувачів)
   - Визначте уражені версії/пакети
   - Зафіксуйте зобов’язання щодо розкриття (якщо це публічний пакет: координуй дії з реєстром пакунків)
4. Представте фінальний `investigation-report.md` користувачеві.

---
## Керівництво з етичного використання

Цей інструмент призначений для **захисного розслідування безпеки** — захисту відкритого програмного забезпечення від атак ланцюжка постачання. Не слід його використовувати для:

- **Домагань або стеження** за учасниками чи підтримувачами
- **Doxing** — зіставлення активності на GitHub з реальними особами з метою шкоди
- **Конкурентна розвідка** — розслідування пропрієтарних або внутрішніх репозиторіїв без дозволу
- **Помилкові звинувачення** — публікація результатів розслідування без підтверджених доказів (див. захисні механізми проти галюцинацій)

Розслідування слід проводити за принципом **мінімального втручання**: збирати лише ті докази, які необхідні для підтвердження або спростування гіпотези. При публікації результатів дотримуйся практик відповідального розкриття та координуй дії з зацікавленими підтримувачами перед публічним розголошенням.

Якщо розслідування виявляє реальну компрометацію, дотримуйся процесу координованого розкриття вразливостей:
1. Спочатку повідомити підтримувачів репозиторію приватно
2. Надати розумний термін для виправлення (зазвичай 90 днів)
3. Координувати дії з реєстрами пакетів (npm, PyPI тощо), якщо постраждали опубліковані пакети
4. За потреби створити CVE

---
## Обмеження швидкості запитів API

GitHub REST API застосовує обмеження швидкості запитів, які можуть перервати великі розслідування, якщо їх не контролювати.

**Автентифіковані запити**: 5 000/година (вимагає змінної середовища `GITHUB_TOKEN` або автентифікації `gh` CLI)
**Неавтентифіковані запити**: 60/година (непридатні для розслідувань)

**Кращі практики**:
- Завжди автентифікуйся: `export GITHUB_TOKEN=ghp_...` або використай `gh` CLI (автоматична автентифікація)
- Використовуй умовні запити (`If-None-Match` / `If-Modified-Since` заголовки), щоб не споживати квоту на незмінені дані
- Для пагінованих кінцевих точок (endpoints) отримуй усі сторінки послідовно — не паралелізуй запити до однієї й тієї ж кінцевої точки
- Перевіряй заголовок `X-RateLimit-Remaining`; якщо залишилося менше 100, зачекай до часу, вказаного в `X-RateLimit-Reset`
- BigQuery має власні квоти (10 TiB/день безкоштовний рівень) — спочатку завжди виконуй dry‑run
- Wayback Machine CDX API: офіційного обмеження швидкості немає, але будь ввічливим (максимум 1‑2 запити/сек)

Якщо обмеження швидкості спрацювало під час розслідування, зафіксуй часткові результати у сховищі доказів і зазнач обмеження у звіті.

---
- [github-archive-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/github-archive-guide.md) — BigQuery‑запити, CDX API, 12 типів подій
- [evidence-types.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/evidence-types.md) — таксономія IOC, типи джерел доказів, типи спостережень
- [recovery-techniques.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/recovery-techniques.md) — відновлення видалених комітів, PR, issue
- [investigation-templates.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/investigation-templates.md) — готові шаблони гіпотез за типом атаки
- [evidence-store.py](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/scripts/evidence-store.py) — CLI‑інструмент для керування JSON‑сховищем доказів
- [forensic-report.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/templates/forensic-report.md) — шаблон структурованого звіту