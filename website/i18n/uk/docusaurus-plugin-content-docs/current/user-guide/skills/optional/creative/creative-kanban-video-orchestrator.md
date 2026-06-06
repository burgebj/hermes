---
title: "Kanban Video Orchestrator — Плануй, налаштовуй і контролюй багатоканальний відео‑виробничий конвеєр, підтримуваний Hermes Kanban"
sidebar_label: "Kanban Video Orchestrator"
description: "Плануй, налаштовуй і контролюй багатагентний конвеєр відеовиробництва, підтримуваний Hermes Kanban"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Kanban Video Orchestrator

Плануй, налаштовуй і моніторуй багатоагентний відео‑виробничий конвеєр, підтримуваний Hermes Kanban. Використовуй, коли користувач хоче створити будь‑яке відео — наративний фільм, продуктове/маркетингове, музичне відео, пояснювальне, ASCII/термінальне мистецтво, абстрактний/генеративний цикл, комікс, 3D, реального часу/інсталяція — і робота вимагає розподілу на спеціалізовані профілі (writer, designer, animator, renderer, voice, editor тощо), координовані через kanban‑дошку. Виконує адаптивне дослідження для визначення обсягу завдання, розробляє відповідну команду для запитуваного стилю, генерує скрипт налаштування, який створює Hermes профілі + початкове kanban‑завдання, а потім допомагає моніторити виконання та втручатися, коли завдання застоюються або падають. Маршрутизує сцени до відповідного Hermes інструменту рендерингу / аудіо / дизайну, який підходить кожному біту (`ascii-video`, `manim-video`, `p5js`, `comfyui`, `touchdesigner-mcp`, `blender-mcp`, `pixel-art`, `baoyu-comic`, `claude-design`, `excalidraw`, `songsee`, `heartmula`, …) плюс зовнішні API для TTS, генерації зображень та перетворення зображення у відео за потреби.
## Skill metadata

| | |
|---|---|
| Джерело | Опційно — встановити за допомогою `hermes skills install official/creative/kanban-video-orchestrator` |
| Шлях | `optional-skills/creative/kanban-video-orchestrator` |
| Версія | `1.0.0` |
| Автор | ['SHL0MS', 'alt-glitch'] |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `video`, `kanban`, `multi-agent`, `orchestration`, `production-pipeline` |
| Пов’язані навички | [`kanban-orchestrator`](/docs/user-guide/skills/bundled/devops/devops-kanban-orchestrator), [`kanban-worker`](/docs/user-guide/skills/bundled/devops/devops-kanban-worker), [`ascii-video`](/docs/user-guide/skills/bundled/creative/creative-ascii-video), [`manim-video`](/docs/user-guide/skills/bundled/creative/creative-manim-video), [`p5js`](/docs/user-guide/skills/bundled/creative/creative-p5js), [`comfyui`](/docs/user-guide/skills/bundled/creative/creative-comfyui), [`touchdesigner-mcp`](/docs/user-guide/skills/bundled/creative/creative-touchdesigner-mcp), [`blender-mcp`](/docs/user-guide/skills/optional/creative/creative-blender-mcp), [`pixel-art`](/docs/user-guide/skills/bundled/creative/creative-pixel-art), [`ascii-art`](/docs/user-guide/skills/bundled/creative/creative-ascii-art), [`songwriting-and-ai-music`](/docs/user-guide/skills/bundled/creative/creative-songwriting-and-ai-music), [`heartmula`](/docs/user-guide/skills/bundled/media/media-heartmula), [`songsee`](/docs/user-guide/skills/bundled/media/media-songsee), [`spotify`](/docs/user-guide/skills/bundled/media/media-spotify), [`youtube-content`](/docs/user-guide/skills/bundled/media/media-youtube-content), [`claude-design`](/docs/user-guide/skills/bundled/creative/creative-claude-design), [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw), [`architecture-diagram`](/docs/user-guide/skills/bundled/creative/creative-architecture-diagram), [`concept-diagrams`](/docs/user-guide/skills/optional/creative/creative-concept-diagrams), [`baoyu-comic`](/docs/user-guide/skills/bundled/creative/creative-baoyu-comic), [`baoyu-infographic`](/docs/user-guide/skills/bundled/creative/creative-baoyu-infographic), [`humanizer`](/docs/user-guide/skills/bundled/creative/creative-humanizer), [`gif-search`](/docs/user-guide/skills/bundled/media/media-gif-search), [`meme-generation`](/docs/user-guide/skills/optional/creative/creative-meme-generation) |
:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це інструкції, які агент бачить під час роботи навички.
:::

# Kanban Video Orchestrator

Обгорни будь‑який запит на відео — від 15‑секундного рекламного тизеру до 5‑хвилинного наративного короткометражного фільму, музичного відео чи ASCII‑циклу — у Kanban‑конвеєр Hermes, який розбиває роботу на спеціалізовані профілі агентів.

Ця навичка **не** виконує рендеринг сама. Це мета‑конвеєр, який:

1. **Scopes** запит через цілеспрямоване дослідження
2. **Designs** відповідну команду (які ролі, які інструменти для кожної ролі) згідно зі стилем
3. **Generates** скрипт налаштування, що створює профілі Hermes, робочий простір проєкту та початкове Kanban‑завдання
4. **Hands off** директору‑профілю, який розбиває завдання через Kanban
5. **Monitors** виконання, допомагає втручатися, коли завдання зависають або падають

Фактичний рендеринг відбувається всередині Kanban після його запуску, за допомогою будь‑яких наявних навичок та інструментів, що підходять до сцен — `ascii-video`, `manim-video`, `p5js`, `comfyui`, `touchdesigner-mcp`, `blender-mcp`, `songwriting-and-ai-music`, `heartmula`, зовнішніх API або чистого Python з PIL + ffmpeg.
## Коли НЕ слід використовувати цей skill

- Відео — це один безперервний процедурний проєкт, який не потребує спеціалістів. Просто напиши код безпосередньо.
- Користувач хоче швидке одноразове перетворення (наприклад, «перетвори це mp4 у GIF») — використай `ffmpeg` безпосередньо.
- Результатом є статичне зображення, GIF або лише аудіо‑артефакт — використай відповідний спеціалізований skill (`ascii-art`, `gifs`, `meme-generation`, `songwriting-and-ai-music`).
- Робота чітко підходить під один існуючий skill (наприклад, чисте ASCII‑відео — просто використай `ascii-video`).
## Workflow

```
DISCOVER  →  BRIEF  →  TEAM DESIGN  →  SETUP  →  EXECUTE  →  MONITOR
```

### Крок 1 — Discover (ask the right questions)

Процес виявлення **адаптивний**: запитуй лише те, що дійсно потрібно. Завжди
починай з трьох питань, щоб визначити загальну форму:

- **What is the video?** (однорядковий короткий опис)
- **How long?** (5‑30 с тизер / 30‑90 с коротке відео / 90 с‑3 хв пояснювальне / 3‑10 хв фільм / довше)
- **What aspect ratio + target platform?** (1:1 / 9:16 / 16:9; X, IG, YouTube, internal тощо)

За відповіддю класифікуй категорію стилю. Стиль визначає, які
додаткові питання ставити. **Не став усі питання одразу.** Запитуй 2‑4
одночасно, слухай, потім продовжуй. Роб розумні припущення, коли користувач
натякає відповідь.

Для повних шаблонів intake та банків питань за стилем дивись
**[references/intake.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/intake.md)**.

### Крок 2 — Brief

Коли достатньо інформації, створюй структурований `brief.md` за шаблоном у
`assets/brief.md.tmpl`. Етапи:

1. **Concept** — однорядковий пітч + емоційна північна зірка
2. **Scope** — тривалість, аспект, платформа, дедлайн
3. **Style** — візуальні референси, бренд‑обмеження, тон
4. **Scenes** — розбивка по ударам (тривалість, контент, цільовий інструмент)
5. **Audio** — озвучка / музика / SFX / тиша (за сценами, якщо потрібно)
6. **Deliverables** — формат файлу, роздільна здатність, додаткові варіанти (vertical cut, GIF тощо)

Покажи brief користувачу для підтвердження перед формуванням команди. **Brief — це контракт** — усі подальші завдання посилаються на нього.

### Крок 3 — Team design

Вибери архетипи ролей з бібліотеки, які підходять цьому відео. **Комбінуй, а не
клонуй.** Більшість відео потребують 4‑7 профілів. Директор завжди присутній;
інші підбираються згідно реальних потреб brief‑у.

Для бібліотеки ролей та складів команд за стилем дивись
**[references/role‑archetypes.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/role-archetypes.md)**.

Для відповідності роль → які навички Hermes + toolsets завантажуються, дивись
**[references/tool‑matrix.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/tool-matrix.md)**.

### Крок 4 — Setup

Згенеруй скрипт налаштування (`setup.sh`) і запусти його. Скрипт:

1. Створює робочий простір проєкту (`~/projects/video-pipeline/<slug>/`)
2. Копіює надані активи у `taste/`, `audio/`, `assets/`
3. Створює кожен профіль Hermes через `hermes profile create --clone`
4. Записує `SOUL.md` для кожного профілю (особистість + визначення ролі)
5. Налаштовує YAML профілю (toolsets, always_load skills, cwd)
6. Записує `brief.md`, `TEAM.md` та вміст `taste/`
7. Запускає початкове завдання `hermes kanban create`, призначене директору

Використовуй `scripts/bootstrap_pipeline.py` для генерації `setup.sh` з brief‑у
та JSON‑дизайну команди. Дивись **[references/kanban‑setup.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/kanban-setup.md)**
для структури скрипту, шаблонів конфігурації профілю та критичного правила
«спільний робочий простір».

### Крок 5 — Execute

Запусти `setup.sh`. Потім надай користувачу команди моніторингу:

```bash
hermes kanban watch --tenant <project-tenant>     # live events
hermes kanban list  --tenant <project-tenant>     # board snapshot
hermes dashboard                                   # visual board UI
```

Профіль директора бере на себе подальшу роботу, розбиваючи завдання і
маршрутизуючи їх до спеціалістів через toolset kanban.

### Крок 6 — Monitor and intervene

Будь залучений — kanban працює автономно, але застрягле завдання або поганий
результат потребують людського (або AI) судження.

Шаблони моніторингу: періодично опитуй `kanban list`, перевіряй будь‑яке
завдання у стані RUNNING, яке перевищує очікувану тривалість, за допомогою
`kanban show <id>`, і слідкуй за heartbeat‑ами. Коли вихід робітника не вдається,
стандартні втручання:

1. Коментуй завдання робітника з конкретним фідбеком (`kanban_comment`)
2. Створи повторне завдання, вказавши оригінал як батьківське
3. Скоригуй обсяг brief‑у і дай директору повторно розбити завдання

Для діагностичних шаблонів, рецептів втручання та playbook «завдання застрягло»,
дивись **[references/monitoring.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/monitoring.md)**.
## Посилання: приклади виконання

Шість конкретних конвеєрів, що охоплюють дуже різні стилі відео — наративне відео, продукт/маркетинг, музичне відео, пояснення математики/алгоритмів, ASCII‑відео, інсталяція в реальному часі — демонструють, як один і той самий робочий процес дає дуже різні команди та графи завдань. Дивись **[references/examples.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/examples.md)**.
## Критичні правила

1. **Discovery before action.** Ніколи не починай генерувати бриф або команду без
   запитання хоча б трьох базових питань. Поганий бриф ланцюжиться через
   весь конвеєр.

2. **Match the team to the video.** Не використовуйте один і той же 4‑профільний набір для
   кожного завдання. Музичне відео без профілю *beat‑analysis* не спрацює.
   На‑наративний фільм без профілю *writer* створить несумісні сцени. Дивись `references/role‑archetypes.md`.

3. **One workspace per project.** Усі профілі для даного відео ділять один і той же
   `dir:` workspace. Завдання передають артефакти через спільну файлову систему та структуровані
   handoffs. **Кожен** виклик `kanban_create` передає
   `workspace_kind="dir"` + `workspace_path="<absolute project path>"`.

4. **Tenant every project.** Використовуй tenant, специфічний для проєкту
   (`--tenant <project‑slug>`). Це тримає панель керування в межах проєкту і запобігає
   перехресному змішуванню з іншими активними kanban‑ами.

5. **Respect existing skills.** Коли сцена підходить до існуючого інструменту, відповідний renderer має завантажити цей інструмент через `--skill <name>` у своєму завданні
   або `always_load` у своєму профілі. Не треба повторно виводити те, що інструмент вже надає.

6. **The director never executes.** Навіть маючи повний `kanban + terminal + file` toolset, правила `SOUL.md` директора забороняють йому виконувати
   роботу самостійно. Він лише розкладає та маршрутизує — кожне конкретне завдання
   перетворюється у виклик `hermes kanban create` спеціалісту‑профілю. Інструмент
   `kanban‑orchestrator` детальніше це пояснює.

7. **Don't over-decompose.** 30‑секундне рекламне відео НЕ потребує 20 завдань.
   Став мету створити найменший граф завдань, який все ще добре паралелізується і відкриває
   потрібні ворота людського перегляду.

8. **Verify API keys BEFORE firing.** Зовнішні API (TTS, image‑gen,
   image‑to‑video) потребують ключів у `~/.hermes/.env` або у сховищі секретів користувача.
   Робітник, який стикається з помилкою відсутнього ключа, марно витрачає слот завдання.
   Помічник `check_key` у скрипті налаштування коректно завершує роботу, якщо потрібний ключ відсутній.
## Карта файлів

```
SKILL.md                            ← this file (workflow + rules)
references/
  intake.md                         ← discovery question banks per style
  role-archetypes.md                ← role library (writer, designer, animator, …)
  tool-matrix.md                    ← skill + toolset mapping per role
  kanban-setup.md                   ← setup script structure & profile config
  monitoring.md                     ← watch + intervene patterns
  examples.md                       ← six worked pipelines
assets/
  brief.md.tmpl                     ← brief skeleton
  setup.sh.tmpl                     ← setup script skeleton
  soul.md.tmpl                      ← profile personality skeleton
scripts/
  bootstrap_pipeline.py             ← generate setup.sh from brief + team JSON
  monitor.py                        ← polling + intervention helpers
```