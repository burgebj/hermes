---
title: "Oss Forensics — расследование цепочки поставок, восстановление доказательств и судебный анализ репозиториев GitHub"
sidebar_label: "Oss Forensics"
description: "Исследование цепочки поставок, восстановление доказательств и судебный анализ репозиториев GitHub"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# OSS‑Forensics

Исследование цепочки поставок, восстановление доказательств и форензический анализ репозиториев GitHub.
Включает восстановление удалённых коммитов, обнаружение force‑push, извлечение IOC, сбор доказательств из нескольких источников, формирование/валидацию гипотез и структурированную форензическую отчётность.
Вдохновлено системой OSS Forensics от RAPTOR, содержащей более 1800 строк кода.
## Метаданные навыка

| | |
|---|---|
| Источник | Опционально — установить с помощью `hermes skills install official/security/oss-forensics` |
| Путь | `optional-skills/security/oss-forensics` |
| Платформы | linux, macos, windows |
:::info
Следующее — полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Навык OSS Security Forensics

7‑фазный мультиагентный исследовательский фреймворк для изучения атак на цепочки поставок открытого кода.
Адаптировано из системы форензики RAPTOR. Охватывает GitHub Archive, Wayback Machine, GitHub API, локальный анализ git, извлечение IOC, формирование и проверку гипотез, подкреплённые доказательствами, и генерацию финального форензик‑отчёта.

---
## ⚠️ Защита от галлюцинаций

Читайте их перед каждым шагом расследования. Нарушение правил аннулирует отчёт.

1. **Правило «Сначала доказательства»**: Каждое утверждение в любом отчёте, гипотезе или резюме ДОЛЖНО содержать как минимум один идентификатор доказательства (`EV-XXXX`). Утверждения без ссылок запрещены.
2. **ОСТАВАЙСЯ В СВОЁЙ СФЕРЕ**: Каждый суб‑агент (расследователь) имеет единственный источник данных. НЕ смешивай источники. Исследователь GH Archive не запрашивает GitHub API и наоборот. Границы ролей строгие.
3. **Разделение фактов и гипотез**: Помечай все непроверенные выводы как `[HYPOTHESIS]`. Только утверждения, проверенные по оригинальным источникам, могут быть представлены как факты.
4. **Запрещение фабрикации доказательств**: Валидатор гипотез ДОЛЖЕН механически проверять, что каждый указанный идентификатор доказательства действительно существует в хранилище доказательств, прежде чем принять гипотезу.
5. **Требуется доказательство опровержения**: Гипотеза не может быть отклонена без конкретного, подкреплённого доказательствами контраргумента. «Доказательств не найдено» недостаточно для опровержения — это лишь делает гипотезу неопределённой.
6. **Двойная проверка SHA/URL**: Любой SHA коммита, URL или внешний идентификатор, цитируемый как доказательство, должен быть независимо подтверждён минимум из двух источников, прежде чем будет помечен как проверенный.
7. **Правило подозрительного кода**: Никогда не запускай код, найденный в исследуемом репозитории, локально. Анализируй только статически или используй `execute_code` в изолированной среде.
8. **Редактирование секретов**: Любые найденные API‑ключи, токены или учётные данные должны быть замаскированы в финальном отчёте. Сохраняй их только во внутреннем журнале.
## Примеры сценариев

- **Сценарий A: Путаница зависимостей**: Зловредный пакет `internal‑lib‑v2` загружается в NPM с более высокой версией, чем внутренний. Следователь должен отследить, когда пакет был впервые замечен, и обновлял ли какие‑либо `PushEvents` в целевом репозитории `package.json` до этой версии.
- **Сценарий B: Захват мейнтейнера**: Учётная запись долгосрочного контрибьютора используется для отправки бекдорного `.github/workflows/build.yml`. Следователь ищет `PushEvents` от этого пользователя после длительного периода бездействия или с нового IP/местоположения (если это можно определить через BigQuery).
- **Сценарий C: Сокрытие принудительного пуша**: Разработчик случайно коммитит секрет продакшна, затем делает принудительный пуш, чтобы «исправить» его. Следователь использует `git fsck` и GH Archive, чтобы восстановить оригинальный SHA коммита и проверить, что было утекло.

---

> **Конвенция путей**: На протяжении всего этого **skill** `SKILL_DIR` обозначает корень директории установки этого **skill** (папка, содержащая этот `SKILL.md`). Когда **skill** загружается, разрешай `SKILL_DIR` в реальный путь — например, `~/.hermes/skills/security/oss-forensics/` или эквивалент в `optional-skills/`. Все ссылки на скрипты и шаблоны являются относительными к нему.
## Этап 0: Инициализация

1. Создай рабочий каталог расследования:
   ```bash
   mkdir investigation_$(echo "REPO_NAME" | tr '/' '_')
   cd investigation_$(echo "REPO_NAME" | tr '/' '_')
   ```
2. Инициализируй хранилище доказательств:
   ```bash
   python3 SKILL_DIR/scripts/evidence-store.py --store evidence.json list
   ```
3. Скопируй шаблон судебно‑медицинского отчёта:
   ```bash
   cp SKILL_DIR/templates/forensic-report.md ./investigation-report.md
   ```
4. Создай файл `iocs.md` для отслеживания индикаторов компрометации по мере их обнаружения.
5. Зафиксируй время начала расследования, целевой репозиторий и заявленную цель расследования.

---
## Фаза 1: Разбор подсказки и извлечение IOC

**Цель**: Выделить все структурированные цели расследования из запроса пользователя.

**Действия**:
- Разобрать подсказку пользователя и извлечь:
  - Целевой репозиторий (`owner/repo`)
  - Целевых актёров (имена пользователей GitHub, адреса электронной почты)
  - Период интереса (диапазоны дат коммитов, метки времени PR)
  - Предоставленные индикаторы компрометации: SHA коммитов, пути к файлам, имена пакетов, IP‑адреса, домены, API‑ключи/токены, вредоносные URL
  - Любые связанные отчёты поставщиков безопасности или публикации в блогах

**Инструменты**: Только рассуждения или `execute_code` для извлечения регулярными выражениями из больших блоков текста.

**Вывод**: Заполнить `iocs.md` извлечёнными IOC. Каждый IOC должен содержать:
- Тип (из: COMMIT_SHA, FILE_PATH, API_KEY, SECRET, IP_ADDRESS, DOMAIN, PACKAGE_NAME, ACTOR_USERNAME, MALICIOUS_URL, OTHER)
- Значение
- Источник (предоставлен пользователем, выведен)

**Ссылка**: См. [evidence-types.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/evidence-types.md) для таксономии IOC.
## Фаза 2: Параллельный сбор доказательств

Запусти до 5 специализированных под‑агентов‑следователей с помощью `delegate_task` (режим пакетной обработки, максимум 3 одновременно). Каждый следователь имеет **единственный источник данных** и не должен смешивать источники.

> **Заметка оркестратора**: Передай список IOC из Фазы 1 и временное окно расследования в поле `context` каждой делегированной задачи.

---

### Следователь 1: Следователь локального Git

**ГРАНИЦА РОЛИ**: Ты запрашиваешь ТОЛЬКО локальное хранилище Git. Не вызывай внешние API.

**Действия**:
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

**Доказательства для сбора** (добавь через `python3 SKILL_DIR/scripts/evidence-store.py add`):
- Каждый «висячий» SHA коммита → тип: `git`
- Доказательства принудительного push (reflog, показывающий переписывание истории) → тип: `git`
- Неподписанные коммиты от проверенных участников → тип: `git`
- Подозрительные добавления бинарных файлов → тип: `git`

**Ссылка**: См. [recovery-techniques.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/recovery-techniques.md) для доступа к принудительно запушенным коммитам.

---

### Следователь 2: Следователь GitHub API

**ГРАНИЦА РОЛИ**: Ты запрашиваешь ТОЛЬКО REST API GitHub. Не запускай локальные git‑команды.

**Действия**:
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

**Цели перекрестной проверки** (отмечай несоответствия как доказательства):
- PR присутствует в архиве, но отсутствует в API → доказательство удаления
- Участник присутствует в событиях архива, но не в списке contributors → доказательство отзыва прав
- Коммит присутствует в архивных PushEvents, но отсутствует в списке коммитов API → доказательство принудительного push/удаления

**Ссылка**: См. [evidence-types.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/evidence-types.md) для типов событий GitHub.

---

### Следователь 3: Следователь Wayback Machine

**ГРАНИЦА РОЛИ**: Ты запрашиваешь ТОЛЬКО CDX API Wayback Machine. Не используй API GitHub.

**Цель**: Восстановить удалённые страницы GitHub (README, issues, PR, релизы, wiki‑страницы).

**Действия**:
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

**Доказательства для сбора**:
- Архивные снимки удалённых issues/PR с их содержимым
- Исторические версии README, показывающие изменения
- Доказательства наличия контента в архиве, но отсутствия в текущем состоянии GitHub

**Ссылка**: См. [github-archive-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/github-archive-guide.md) для параметров CDX API.

---

### Следователь 4: Следователь GitHub Archive / BigQuery

**ГРАНИЦА РОЛИ**: Ты запрашиваешь ТОЛЬКО GitHub Archive через BigQuery. Это неизменяемый журнал всех публичных событий GitHub.

> **Предварительные требования**: Требуются учётные данные Google Cloud с доступом к BigQuery (`gcloud auth application-default login`). Если недоступно, пропусти этого следователя и отметь это в отчёте.

**Правила оптимизации расходов** (ОБЯЗАТЕЛЬНО):
1. ВСЕГДА запускай `--dry_run` перед каждым запросом для оценки стоимости.
2. Используй `_TABLE_SUFFIX` для фильтрации по диапазону дат и минимизации сканируемых данных.
3. Выбирай ТОЛЬКО необходимые столбцы (`SELECT`).
4. Добавляй `LIMIT`, если только не выполняешь агрегацию.

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

**Доказательства для сбора**:
- События принудительного push (payload.size > 0, payload.distinct_size = 0)
- DeleteEvents для веток/тегов
- WorkflowRunEvents для подозрительной автоматизации CI/CD
- PushEvents, предшествующие «пробелу» в git‑логе (доказательство переписывания)

**Ссылка**: См. [github-archive-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/github-archive-guide.md) для всех 12 типов событий и шаблонов запросов.

---

### Следователь 5: Следователь обогащения IOC

**ГРАНИЦА РОЛИ**: Ты обогащаешь СУЩЕСТВУЮЩИЕ IOC из Фазы 1, используя ТОЛЬКО пассивные публичные источники. Не выполняй никакой код из целевого репозитория.

**Действия**:
- Для каждого SHA коммита: попытаться восстановить через прямой URL GitHub (`github.com/OWNER/REPO/commit/SHA.patch`)
- Для каждого домена/IP: проверять пассивный DNS, WHOIS‑записи (через `web_extract` на публичных WHOIS‑службах)
- Для каждого названия пакета: проверять npm/PyPI на наличие сообщений о вредоносных пакетах
- Для каждого имени пользователя‑актора: проверять профиль GitHub, историю вкладов, возраст аккаунта
- Восстанавливать принудительно запушенные коммиты с помощью трёх методов (см. [recovery-techniques.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/recovery-techniques.md))
## Фаза 3: Консолидация доказательств

После того как все следователи завершат работу:

1. Выполни `python3 SKILL_DIR/scripts/evidence-store.py --store evidence.json list`, чтобы увидеть все собранные доказательства.
2. Для каждого доказательства проверь, что хеш `content_sha256` совпадает с оригинальным источником.
3. Сгруппируй доказательства по:
   - **Timeline**: отсортируй все доказательства с меткой времени хронологически;
   - **Actor**: сгруппируй по GitHub‑нику или электронной почте;
   - **IOC**: привяжи доказательство к соответствующему IOC.
4. Выяви **несоответствия**: элементы, присутствующие в одном источнике, но отсутствующие в другом (индикаторы удаления ключей).
5. Пометь доказательства как `[VERIFIED]` (подтверждено из 2 и более независимых источников) или `[UNVERIFIED]` (только один источник).
## Phase 4: Формирование гипотезы

Гипотеза должна:
- Содержать конкретное утверждение (например, «Actor X принудительно запушил в `BRANCH` в `DATE`, чтобы стереть коммит `SHA`»)
- Ссылаться как минимум на 2 идентификатора доказательств, поддерживающих её (`EV-XXXX`, `EV-YYYY`)
- Указывать, какие доказательства её опровергнут
- Быть помечена `[HYPOTHESIS]` до подтверждения

**Общие шаблоны гипотез** (см. [investigation-templates.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/investigation-templates.md)):
- Compromise maintainer: легитимный аккаунт использован после захвата для внедрения вредоносного кода
- Dependency Confusion: захват имени пакета для перехвата установок
- CI/CD Injection: вредоносные изменения в workflow, запускающие код во время сборок
- Typosquatting: почти идентичное имя пакета, нацеленное на опечатавшихся пользователей
- Credential Leak: токен/ключ случайно закоммичен, затем принудительно запушен для стирания

Для каждой гипотезы запускай под‑агент `delegate_task`, который попытается найти опровергающие доказательства перед подтверждением.
## Фаза 5: Проверка гипотез

Под‑агент‑валидатор ДОЛЖЕН механически проверить:

1. Для каждой гипотезы извлечь все указанные идентификаторы доказательств.
2. Проверить, что каждый идентификатор присутствует в `evidence.json` (критическая ошибка, если какой‑либо идентификатор отсутствует → гипотеза отклоняется как потенциально сфабрикованная).
3. Проверить, что каждый фрагмент доказательства, помеченный `[VERIFIED]`, подтверждён из 2 и более источников.
4. Проверить логическую согласованность: поддерживает ли временная шкала, изображённая доказательствами, гипотезу?
5. Проверить альтернативные объяснения: может ли тот же набор доказательств возникнуть по безвредной причине?

**Результат**:
- `VALIDATED`: все доказательства указаны, проверены, логически согласованы, альтернативных объяснений нет.
- `INCONCLUSIVE`: доказательства поддерживают гипотезу, но существуют альтернативные объяснения или их недостаточно.
- `REJECTED`: отсутствуют идентификаторы доказательств, непроверенные доказательства приведены как факт, обнаружена логическая несогласованность.

Отклонённые гипотезы возвращаются в Фазу 4 для доработки (максимум 3 итерации).
## Фаза 6: Генерация окончательного отчёта

Заполни `investigation-report.md`, используя шаблон из [forensic-report.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/templates/forensic-report.md).

**Обязательные разделы**:
- Исполнительное резюме: однопараграфное заключение (Compromised / Clean / Inconclusive) с указанием уровня уверенности
- Хронология: хронологическая реконструкция всех значимых событий с указанием источников доказательств
- Подтверждённые гипотезы: каждая гипотеза с указанием статуса и поддерживающих идентификаторов доказательств
- Реестр доказательств: таблица всех записей `EV-XXXX` с указанием источника, типа и статуса верификации
- Список IOC: все извлечённые и обогащённые индикаторы компрометации
- Цепочка хранения: как собирались доказательства, из каких источников и с какими временными метками
- Рекомендации: немедленные меры смягчения в случае обнаружения компрометации; рекомендации по мониторингу

**Правила отчёта**:
- Каждый фактический тезис должен иметь как минимум одну ссылку‑цитату `[EV-XXXX]`
- В исполнительном резюме необходимо указать уровень уверенности (High / Medium / Low)
- Все секреты/учётные данные должны быть заменены на `[REDACTED]`
## Фаза 7: Завершение

1. Выполни окончательный подсчёт доказательств: `python3 SKILL_DIR/scripts/evidence-store.py --store evidence.json list`
2. Архивируй полный каталог расследования.
3. Если компрометация подтверждена:
   - Перечисли немедленные меры смягчения (ротация учётных данных, закрепление хешей зависимостей, уведомление затронутых пользователей)
   - Определи затронутые версии и пакеты
   - Учти обязательства по раскрытию информации (если это публичный пакет — согласуй действия с реестром пакетов)
4. Представь окончательный `investigation-report.md` пользователю.

---
## Руководство по этичному использованию

Этот **skill** предназначен для **защитного расследования в области безопасности** — защиты открытого программного обеспечения от атак цепочки поставок. Он не должен использоваться для:

- **Harassment or stalking** участников или **maintainers**
- **Doxing** — сопоставления активности на GitHub с реальными личностями в злонамеренных целях
- **Competitive intelligence** — расследования проприетарных или внутренних репозиториев без разрешения
- **False accusations** — публикации результатов расследования без проверенных доказательств (см. ограничения по предотвращению галлюцинаций)

Расследования должны проводиться согласно принципу **минимального вмешательства**: собирай только те доказательства, которые необходимы для подтверждения или опровержения гипотезы. При публикации результатов следуй практикам ответственного раскрытия и согласуй действия с затронутыми **maintainers** до публичного раскрытия.

Если расследование выявит реальное компрометирование, следуй процессу координированного раскрытия уязвимостей:
1. Сначала уведоми **maintainers** репозитория конфиденциально
2. Предоставь разумное время для исправления (обычно 90 дней)
3. Скоординируй действия с реестрами пакетов (npm, PyPI и др.), если затронуты опубликованные пакеты
4. При необходимости опубликуй CVE

---
## Ограничение скорости API

GitHub REST API применяет ограничения скорости, которые могут прервать крупные расследования, если их не контролировать.

**Авторизованные запросы**: 5 000 / час (требуется переменная окружения `GITHUB_TOKEN` или аутентификация через `gh` CLI)
**Неавторизованные запросы**: 60 / час (непригодны для расследований)

**Рекомендации**:
- Всегда аутентифицируйся: `export GITHUB_TOKEN=ghp_...` или используй `gh` CLI (автоаутентификация)
- Используй условные запросы (`If-None-Match` / `If-Modified-Since` заголовки), чтобы не расходовать квоту на неизменённые данные
- Для постраничных конечных точек получай все страницы последовательно — не параллелизируй запросы к одной и той же конечной точке
- Проверяй заголовок `X-RateLimit-Remaining`; если его значение ниже 100, сделай паузу до временной метки из `X-RateLimit-Reset`
- У BigQuery свои квоты (10 TiB / день бесплатный уровень) — всегда сначала выполняй сухой запуск
- Wayback Machine CDX API: официального ограничения скорости нет, но будь вежлив (не более 1‑2 запросов в секунду)

Если ограничение скорости сработало во время расследования, запиши частичные результаты в хранилище доказательств и укажи ограничение в отчёте.
## Справочные материалы

- [github-archive-guide.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/github-archive-guide.md) — запросы BigQuery, API CDX, 12 типов событий
- [evidence-types.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/evidence-types.md) — таксономия IOC, типы источников доказательств, типы наблюдений
- [recovery-techniques.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/recovery-techniques.md) — восстановление удалённых коммитов, PR и задач
- [investigation-templates.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/references/investigation-templates.md) — готовые шаблоны гипотез для каждого типа атаки
- [evidence-store.py](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/scripts/evidence-store.py) — CLI‑инструмент для управления хранилищем доказательств в формате JSON
- [forensic-report.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/security/oss-forensics/templates/forensic-report.md) — шаблон структурированного отчёта