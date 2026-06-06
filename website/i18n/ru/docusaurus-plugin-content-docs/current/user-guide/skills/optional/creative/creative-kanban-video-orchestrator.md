---
title: "Планируй, настраивай и контролируй многoагентный конвейер видеопроизводства, поддерживаемый Hermes Kanban"
sidebar_label: "Kanban Video Orchestrator"
description: "Планируй, настраивай и контролируй многопоточный видеопроизводственный конвейер, поддерживаемый Hermes Kanban"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Оркестратор видеопроизводства Kanban

Планируй, настраивай и контролируй многопрофильный конвейер видеопроизводства, поддерживаемый Hermes Kanban. Используй, когда пользователь хочет создать ЛЮБОЕ видео — художественный фильм, рекламный/продуктовый ролик, музыкальное видео, объяснительное, ASCII/терминальное искусство, абстрактный/генеративный цикл, комикс, 3D, реальное‑время/инсталляцию — и работа требует разбивки на специализированные профили (писатель, дизайнер, аниматор, рендерер, озвучка, монтажёр и т.д.), координируемые через канбан‑доску. Выполняет адаптивное исследование для уточнения брифа, подбирает подходящую команду под запрошенный стиль, генерирует скрипт настройки, который создаёт профили Hermes + начальную задачу канбана, затем помогает отслеживать выполнение и вмешиваться, когда задачи зависают или терпят неудачу. Маршрутизирует сцены к тому Hermes‑рендерингу/аудио/дизайну, который подходит каждому биту (`ascii-video`, `manim-video`, `p5js`, `comfyui`, `touchdesigner-mcp`, `blender-mcp`, `pixel-art`, `baoyu-comic`, `claude-design`, `excalidraw`, `songsee`, `heartmula`, …) плюс внешним API для TTS, генерации изображений и преобразования изображения в видео по мере необходимости.
## Метаданные навыка

| | |
|---|---|
| Источник | Опционально — установить с помощью `hermes skills install official/creative/kanban-video-orchestrator` |
| Путь | `optional-skills/creative/kanban-video-orchestrator` |
| Версия | `1.0.0` |
| Автор | ['SHL0MS', 'alt-glitch'] |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `video`, `kanban`, `multi-agent`, `orchestration`, `production-pipeline` |
| Связанные навыки | [`kanban-orchestrator`](/docs/user-guide/skills/bundled/devops/devops-kanban-orchestrator), [`kanban-worker`](/docs/user-guide/skills/bundled/devops/devops-kanban-worker), [`ascii-video`](/docs/user-guide/skills/bundled/creative/creative-ascii-video), [`manim-video`](/docs/user-guide/skills/bundled/creative/creative-manim-video), [`p5js`](/docs/user-guide/skills/bundled/creative/creative-p5js), [`comfyui`](/docs/user-guide/skills/bundled/creative/creative-comfyui), [`touchdesigner-mcp`](/docs/user-guide/skills/bundled/creative/creative-touchdesigner-mcp), [`blender-mcp`](/docs/user-guide/skills/optional/creative/creative-blender-mcp), [`pixel-art`](/docs/user-guide/skills/bundled/creative/creative-pixel-art), [`ascii-art`](/docs/user-guide/skills/bundled/creative/creative-ascii-art), [`songwriting-and-ai-music`](/docs/user-guide/skills/bundled/creative/creative-songwriting-and-ai-music), [`heartmula`](/docs/user-guide/skills/bundled/media/media-heartmula), [`songsee`](/docs/user-guide/skills/bundled/media/media-songsee), [`spotify`](/docs/user-guide/skills/bundled/media/media-spotify), [`youtube-content`](/docs/user-guide/skills/bundled/media/media-youtube-content), [`claude-design`](/docs/user-guide/skills/bundled/creative/creative-claude-design), [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw), [`architecture-diagram`](/docs/user-guide/skills/bundled/creative/creative-architecture-diagram), [`concept-diagrams`](/docs/user-guide/skills/optional/creative/creative-concept-diagrams), [`baoyu-comic`](/docs/user-guide/skills/bundled/creative/creative-baoyu-comic), [`baoyu-infographic`](/docs/user-guide/skills/bundled/creative/creative-baoyu-infographic), [`humanizer`](/docs/user-guide/skills/bundled/creative/creative-humanizer), [`gif-search`](/docs/user-guide/skills/bundled/media/media-gif-search), [`meme-generation`](/docs/user-guide/skills/optional/creative/creative-meme-generation) |
:::info
Следующий текст — полное определение **skill**, которое Hermes загружает при срабатывании этого **skill**. Это то, что агент видит как инструкции, когда **skill** активен.
:::

# Канбан‑оркестратор видео

Оборачивай любой запрос на видео — от 15‑секундного рекламного ролика продукта до 5‑минутного повествовательного короткометражного фильма, музыкального клипа или ASCII‑цикла — в канбан‑конвейер Hermes, который разбивает работу на специализированные профили агентов.

Этот **skill** **не** выполняет рендеринг сам. Это мета‑конвейер, который:

1. **Определяет границы** запроса через целевое исследование
2. **Разрабатывает** подходящую команду (какие роли, какие инструменты для каждой роли) на основе стиля
3. **Генерирует** скрипт настройки, который создаёт профили Hermes, рабочее пространство проекта и начальную канбан‑задачу
4. **Передаёт** управление профилю директора, который разбивает задачу через канбан
5. **Отслеживает** выполнение, помогает вмешаться, когда задачи задерживаются или завершаются с ошибкой

Фактический рендеринг происходит внутри канбана после его запуска, с использованием любых существующих **skills** + **tools**, подходящих для сцен — `ascii-video`, `manim-video`, `p5js`, `comfyui`, `touchdesigner-mcp`, `blender-mcp`, `songwriting-and-ai-music`, `heartmula`, внешних API или простого Python с PIL + ffmpeg.
## Когда НЕ использовать этот skill

- Видео представляет собой один непрерывный процедурный проект, не требующий специалистов. Просто напиши код напрямую.
- Пользователь хочет быстрое однократное преобразование (например, «конвертировать этот mp4 в GIF») — используй `ffmpeg` напрямую.
- Вывод представляет собой статическое изображение, GIF или только аудио‑артефакт — используй соответствующий специализированный skill (`ascii-art`, `gifs`, `meme-generation`, `songwriting-and-ai-music`).
- Работа полностью вписывается в один существующий skill (например, чисто ASCII‑видео — просто используй `ascii-video`).
## Workflow

```
DISCOVER  →  BRIEF  →  TEAM DESIGN  →  SETUP  →  EXECUTE  →  MONITOR
```

### Шаг 1 — Discover (ask the right questions)

Процесс обнаружения **адаптивный**: спрашивай только то, что действительно нужно. Всегда
начинай с трёх вопросов, чтобы определить общую форму:

- **What is the video?** (краткое описание в одном предложении)
- **How long?** (тизер 5‑30 с / короткое 30‑90 с / объяснительное 90 с‑3 мин / фильм 3‑10 мин / дольше)
- **What aspect ratio + target platform?** (1:1 / 9:16 / 16:9; X, IG, YouTube, внутреннее и т.д.)

По ответу классифицируй категорию стиля. Стиль определяет, какие
дополнительные вопросы задавать. **Не задавай все вопросы сразу.** Спрашивай 2‑4
одновременно, слушай, затем продолжай. Делай разумные предположения, когда пользователь
намекает на ответ.

Для полного набора шаблонов ввода и вопросов по каждому стилю смотри
**[references/intake.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/intake.md)**.

### Шаг 2 — Brief

Как только достаточно информации собрано, создай структурированный `brief.md` по шаблону в
`assets/brief.md.tmpl`. Этапы:

1. **Concept** — однострочное описание + эмоциональная «северная звезда»
2. **Scope** — длительность, соотношение, платформа, дедлайн
3. **Style** — визуальные референсы, ограничения бренда, тон
4. **Scenes** — разбивка по битам (длительность, содержание, целевой инструмент)
5. **Audio** — озвучка / музыка / звуковые эффекты / тишина (по сценам, если нужно)
6. **Deliverables** — формат файла, разрешение, альтернативные варианты (вертикальный вырез, GIF и т.п.)

Покажи бриф пользователю для подтверждения перед проектированием команды. **Бриф —
это контракт** — все последующие задачи ссылаются на него.

### Шаг 3 — Team design

Выбери архетипы ролей из библиотеки, подходящие для этого видео. **Составляй, а не клонируй.** Большинству видео требуется 4‑7 профилей. Директор всегда присутствует; остальные выбираются исходя из реальных требований брифа.

Для библиотеки ролей и составов команд по стилям смотри
**[references/role-archetypes.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/role-archetypes.md)**.

Для сопоставления роль → какие Hermes skills + toolsets она загружает, смотри
**[references/tool-matrix.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/tool-matrix.md)**.

### Шаг 4 — Setup

Сгенерируй скрипт настройки (`setup.sh`) и запусти его. Скрипт:

1. Создаёт рабочее пространство проекта (`~/projects/video-pipeline/<slug>/`)
2. Копирует любые предоставленные ассеты в `taste/`, `audio/`, `assets/`
3. Создаёт каждый Hermes профиль через `hermes profile create --clone`
4. Записывает для каждого профиля `SOUL.md` (личность + определение роли)
5. Конфигурирует профиль YAML (toolsets, always_load skills, cwd)
6. Записывает `brief.md`, `TEAM.md` и содержимое `taste/`
7. Запускает начальную задачу `hermes kanban create`, назначенную директору

Используй `scripts/bootstrap_pipeline.py` для генерации `setup.sh` из брифа + JSON‑описания команды. См. **[references/kanban-setup.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/kanban-setup.md)**
для структуры скрипта, шаблонов конфигураций профилей и критического правила
«общего рабочего пространства».

### Шаг 5 — Execute

Запусти `setup.sh`. Затем предоставь пользователю команды мониторинга:

```bash
hermes kanban watch --tenant <project-tenant>     # live events
hermes kanban list  --tenant <project-tenant>     # board snapshot
hermes dashboard                                   # visual board UI
```

Профиль директора берёт управление от этого момента, разбивая работу и направляя
задачи профильным специалистам через набор инструментов kanban.

### Шаг 6 — Monitor and intervene

Оставайся вовлечённым — kanban работает автономно, но застрявшая задача или плохой результат
требуют человеческого (или AI) суждения.

Шаблоны мониторинга: периодически вызывай `kanban list`, проверяй любую задачу в статусе `RUNNING`,
превышающую ожидаемую длительность с помощью `kanban show <id>`, и следи за heartbeat‑ами. Когда вывод
работника не проходит проверку, стандартные вмешательства таковы:

1. Оставить комментарий к задаче работника с конкретной обратной связью (`kanban_comment`)
2. Создать задачу повторного запуска, указав оригинал как родителя
3. Скорректировать объём брифа и позволить директору пересобрать декомпозицию

Для диагностических шаблонов, рецептов вмешательства и плейбука «задача застряла», смотри
**[references/monitoring.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/monitoring.md)**.
## Ссылка: готовые примеры

Шесть конкретных конвейеров, охватывающих совершенно разные стили видео — нарративный фильм, рекламный/маркетинговый ролик, музыкальное видео, объяснение математики/алгоритма, ASCII‑видео, установка в реальном времени — демонстрируют, как один и тот же рабочий процесс приводит к различным командам и графикам задач. См. **[references/examples.md](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/creative/kanban-video-orchestrator/references/examples.md)**.
## Критические правила

1. **Discovery before action.** Никогда не начинай генерировать бриф или команду без
   задавания как минимум трёх базовых вопросов. Плохой бриф приводит к сбоям
   во всей цепочке обработки.

2. **Match the team to the video.** Не используй одну и ту же настройку из 4‑х профилей
   для каждой задачи. Музыкальное видео без профиля анализа ритма будет
   работать неверно. Нарративный фильм без профиля сценариста даст
   несвязные сцены. См. `references/role-archetypes.md`.

3. **One workspace per project.** Все профили для конкретного видео используют один
   `dir:` рабочий каталог. Задачи передают артефакты через общую файловую систему
   и структурированные передачи. **Каждый** вызов `kanban_create` передаёт
   `workspace_kind="dir"` + `workspace_path="<absolute project path>"`.

4. **Tenant every project.** Используй проектно‑специфичный tenant
   (`--tenant <project-slug>`). Это ограничивает панель управления и предотвращает
   перекрёстное загрязнение с другими активными канбанами.

5. **Respect existing skills.** Когда сцена подходит под существующий skill, соответствующий
   рендерер должен загрузить этот skill через `--skill <name>` в своей задаче
   или `always_load` в своём профиле. Не переопределяй то, что уже предоставляет skill.

6. **The director never executes.** Даже имея полный набор инструментов `kanban + terminal + file`,
   правила `SOUL.md` директора запрещают ему выполнять работу самостоятельно.
   Он только разбивает и маршрутизирует — каждая конкретная задача превращается
   в вызов `hermes kanban create` к профильному специалисту. Об этом подробнее
   говорит skill `kanban-orchestrator`.

7. **Don't over-decompose.** 30‑секундное рекламное видео НЕ требует 20 задач.
   Стремись к минимальному графу задач, который всё ещё хорошо параллелится
   и предоставляет необходимые точки человеческой проверки.

8. **Verify API keys BEFORE firing.** Внешние API (TTS, генерация изображений,
   image‑to‑video) требуют ключи в `~/.hermes/.env` или в секретном хранилище пользователя.
   Работник, получивший ошибку отсутствующего ключа, тратит слот задачи впустую.
   Помощник `check_key` в скрипте установки корректно прерывает процесс,
   если требуемый ключ отсутствует.
## Карта файлов

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