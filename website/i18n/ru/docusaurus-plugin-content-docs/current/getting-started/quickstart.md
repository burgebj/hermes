---
sidebar_position: 1
title: "Быстрый старт"
description: "Твой первый разговор с Hermes Agent — от установки до общения менее чем за 5 минут"
---
# Быстрый старт

Это руководство проведёт тебя от нуля до работающего Hermes, готового к реальному использованию. Установи, выбери провайдера, проверь рабочий чат и точно знаешь, что делать, когда что‑то ломается.

## Предпочитаешь смотреть?

**Onchain AI Garage** собрал мастер‑класс по установке, настройке и базовым командам — хороший помощник к этой странице, если ты предпочитаешь следовать видео. Подробнее смотри плейлист [Hermes Agent Tutorials & Use Cases](https://www.youtube.com/channel/UCqB1bhMwGsW-yefBxYwFCCg).

<div style={{position: 'relative', paddingBottom: '56.25%', height: 0, overflow: 'hidden', maxWidth: '100%', marginBottom: '1.5rem'}}>
  <iframe
    style={{position: 'absolute', top: 0, left: 0, width: '100%', height: '100%'}}
    src="https://www.youtube-nocookie.com/embed/R3YOGfTBcQg"
    title="Hermes Agent Masterclass: Installation, Setup, Basic Commands"
    frameBorder="0"
    allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
    allowFullScreen
  ></iframe>
</div>

## Для кого это

- Для новичков, которым нужен самый короткий путь к рабочей установке
- При смене провайдера, чтобы не терять время на ошибки конфигурации
- Для настройки Hermes для команды, бота или постоянно работающего рабочего потока
- Если уже «установилось, но ничего не делает»

## Самый быстрый путь

Выбери строку, соответствующую твоей цели:

| Цель | Сначала сделай | Затем сделай |
|---|---|---|
| Просто хочу, чтобы Hermes работал на моём компьютере | `hermes setup` | Запусти реальный чат и проверь, что он отвечает |
| Я уже знаю своего провайдера | `hermes model` | Сохрани конфиг, затем начни чат |
| Хочу бота или постоянно работающую настройку | `hermes gateway setup` после того, как CLI работает | Подключи Telegram, Discord, Slack или другую платформу |
| Хочу локальную или саморазмещённую модель | `hermes model` → custom endpoint | Проверь endpoint, имя модели и длину контекста |
| Нужен мульти‑провайдерный запасной вариант | `hermes model` сначала | Добавляй роутинг и запасной (fallback) только после того, как базовый чат заработает |

**Практический совет:** если Hermes не может завершить обычный чат, пока не добавляй новые функции. Сначала добейся чистого разговора, затем добавляй gateway, cron, skills, голос или роутинг.

---

## 1. Установить Hermes Agent

**Вариант A — pip (самый простой):**

```bash
pip install hermes-agent
hermes postinstall     # optional: installs Node.js, browser, ripgrep, ffmpeg + runs setup
```

Релизы PyPI отслеживают версии с тегами (мажор/минор), а не каждый коммит в `main`. Для самых свежих функций используй вариант B.

**Вариант B — git‑инсталлер (отслеживает ветку main):**

```bash
# Linux / macOS / WSL2 / Android (Termux)
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

:::tip Android / Termux
Если устанавливаешь на телефон, смотри специальный [Termux guide](./termux.md) — проверенный ручной путь, поддерживаемые extras и текущие ограничения Android.
:::

:::tip Windows Users
Сначала установи [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install), затем запусти команду выше в терминале WSL2.
:::

После завершения перезагрузи оболочку:

```bash
source ~/.bashrc   # or source ~/.zshrc
```

Подробные варианты установки, предварительные требования и отладка описаны в [Installation guide](./installation.md).

## 2. Выбрать провайдера

Самый важный шаг настройки. Используй `hermes model`, чтобы интерактивно пройти выбор:

```bash
hermes model
```

:::tip Самый простой путь: Nous Portal
Одна подписка покрывает 300+ моделей плюс [Tool Gateway](../user-guide/features/tool-gateway.md) (веб‑поиск, генерация изображений, TTS, облачный браузер). На свежей установке:

```bash
hermes setup --portal
```

Это выполнит вход, установит Nous как провайдера и включит Tool Gateway одной командой.
:::

Хорошие варианты по умолчанию:

| Провайдер | Что это | Как настроить |
|----------|-----------|---------------|
| **Nous Portal** | Подписка, zero‑config | OAuth‑вход через `hermes model` |
| **OpenAI Codex** | ChatGPT OAuth, использует модели Codex | Авторизация device‑code через `hermes model` |
| **Anthropic** | Модели Claude напрямую — план Max + дополнительные кредиты (OAuth) или API‑ключ для pay‑per‑token | `hermes model` → OAuth‑вход (нужен Max + кредиты) или Anthropic API‑key |
| **OpenRouter** | Мульти‑провайдерный роутинг по множеству моделей | Введи свой API‑key |
| **Z.AI** | Модели GLM / Zhipu‑hosted | Установи `GLM_API_KEY` / `ZAI_API_KEY` (принимает также `Z_AI_API_KEY`) |
| **Kimi / Moonshot** | Модели кодинга и чата от Moonshot | Установи `KIMI_API_KEY` (или `KIMI_CODING_API_KEY` для кодинга) |
| **Kimi / Moonshot China** | Эндпоинт Moonshot в Китае | Установи `KIMI_CN_API_KEY` |
| **Arcee AI** | Модели Trinity | Установи `ARCEEAI_API_KEY` |
| **GMI Cloud** | Прямой API мульти‑моделей | Установи `GMI_API_KEY` |
| **MiniMax (OAuth)** | Frontier‑модель MiniMax через браузерный OAuth — API‑key не нужен (имя модели в `hermes_cli/models.py` может меняться) | `hermes model` → MiniMax (OAuth) |
| **MiniMax** | Международный эндпоинт MiniMax | Установи `MINIMAX_API_KEY` |
| **MiniMax China** | Китайский эндпоинт MiniMax | Установи `MINIMAX_CN_API_KEY` |
| **Alibaba Cloud** | Модели Qwen через DashScope | Установи `DASHSCOPE_API_KEY` (план Qwen Coding также принимает `ALIBABA_CODING_PLAN_API_KEY`) |
| **Hugging Face** | 20+ открытых моделей через унифицированный роутер (Qwen, DeepSeek, Kimi и др.) | Установи `HF_TOKEN` |
| **AWS Bedrock** | Claude, Nova, Llama, DeepSeek через нативный Converse API | IAM‑роль или `aws configure` ([руководство](../guides/aws-bedrock.md)) |
| **Azure Foundry** | Модели, размещённые в Azure AI Foundry | Установи `AZURE_FOUNDRY_API_KEY` + `AZURE_FOUNDRY_BASE_URL` |
| **Google AI Studio** | Модели Gemini через прямой API | Установи `GOOGLE_API_KEY` / `GEMINI_API_KEY` |
| **Google Gemini (OAuth)** | Gemini через OAuth‑flow `google-gemini-cli` — ключ не нужен | `hermes model` → Google Gemini (OAuth) |
| **xAI** | Модели Grok через прямой API | Установи `XAI_API_KEY` |
| **xAI Grok OAuth** | Подписка SuperGrok / Premium+ — ключ не нужен | `hermes model` → xAI Grok OAuth |
| **NovitaAI** | Мульти‑модельный API‑gateway | Установи `NOVITA_API_KEY` |
| **StepFun** | Модели Step Plan | Установи `STEPFUN_API_KEY` |
| **Xiaomi MiMo** | Модели от Xiaomi | Установи `XIAOMI_API_KEY` |
| **Tencent TokenHub** | Модели от Tencent | Установи `TOKENHUB_API_KEY` |
| **Ollama Cloud** | Управляемые модели Ollama | Установи `OLLAMA_API_KEY` |
| **LM Studio** | Локальное приложение, предоставляющее OpenAI‑совместимый API | Установи `LM_API_KEY` (и `LM_BASE_URL`, если не по умолчанию) |
| **Qwen OAuth** | Браузерный OAuth Qwen Portal — ключ не нужен | `hermes model` → Qwen OAuth |
| **Kilo Code** | Модели KiloCode‑hosted | Установи `KILOCODE_API_KEY` |
| **OpenCode Zen** | Платный доступ к отобранным моделям | Установи `OPENCODE_ZEN_API_KEY` |
| **OpenCode Go** | Подписка $10/мес на открытые модели | Установи `OPENCODE_GO_API_KEY` |
| **DeepSeek** | Прямой доступ к DeepSeek API | Установи `DEEPSEEK_API_KEY` |
| **NVIDIA NIM** | Модели Nemotron через build.nvidia.com или локальный NIM | Установи `NVIDIA_API_KEY` (опционально `NVIDIA_BASE_URL`) |
| **GitHub Copilot** | Подписка GitHub Copilot (GPT‑5.x, Claude, Gemini и др.) | OAuth через `hermes model`, или `COPILOT_GITHUB_TOKEN` / `GH_TOKEN` |
| **GitHub Copilot ACP** | Бэкенд‑агент Copilot ACP (запускает локальный `copilot` CLI) | `hermes model` (требуется `copilot` CLI + `copilot login`) |
| **Custom Endpoint** | VLLM, SGLang, Ollama или любой OpenAI‑совместимый API | Установи базовый URL + API‑key |

Для большинства новых пользователей: выбери провайдера, оставь значения по умолчанию, если только не знаешь, зачем их менять. Полный каталог провайдеров с переменными окружения и шагами настройки находится на странице [Providers](../integrations/providers.md).

:::caution Minimum context: 64K tokens
Hermes Agent требует модель с минимум **64 000 токенов** контекста. Модели с меньшими окнами не могут поддерживать достаточную рабочую память для многошаговых вызовов инструментов и будут отклонены при старте. Большинство hosted‑моделей (Claude, GPT, Gemini, Qwen, DeepSeek) легко удовлетворяют этому требованию. Если ты запускаешь локальную модель, установи её размер контекста минимум в 64K (например, `--ctx-size 65536` для llama.cpp или `-c 65536` для Ollama).
:::

:::tip
Провайдера можно менять в любой момент с помощью `hermes model` — нет привязки. Полный список поддерживаемых провайдеров и детали настройки смотри в [AI Providers](../integrations/providers.md).
:::

### Как хранятся настройки

Hermes разделяет секреты и обычные конфиги:

- **Секреты и токены** → `~/.hermes/.env`
- **Несекретные настройки** → `~/.hermes/config.yaml`

Самый простой способ задать значения правильно — через CLI:

```bash
hermes config set model anthropic/claude-opus-4.6
hermes config set terminal.backend docker
hermes config set OPENROUTER_API_KEY sk-or-...
```

Правильное значение автоматически попадает в нужный файл.

## 3. Запусти первый чат

```bash
hermes            # classic CLI
hermes --tui      # modern TUI (recommended)
```

Ты увидишь приветственный баннер с моделью, доступными инструментами и skills. Используй запрос, который конкретен и легко проверяется:

:::tip Выбери интерфейс
Hermes поставляется с двумя терминальными интерфейсами: классическим CLI `prompt_toolkit` и новым [TUI](../user-guide/tui.md) с модальными оверлеями, выбором мышью и неблокирующим вводом. Оба используют одни и те же сессии, слеш‑команды и конфиги — попробуй каждый с `hermes` vs `hermes --tui`.
:::

```
Summarize this repo in 5 bullets and tell me what the main entrypoint is.
```

```
Check my current directory and tell me what looks like the main project file.
```

```
Help me set up a clean GitHub PR workflow for this codebase.
```

**Как выглядит успех:**

- Баннер показывает выбранную модель/провайдера
- Hermes отвечает без ошибок
- При необходимости использует инструмент (терминал, чтение файла, веб‑поиск)
- Разговор продолжается более одного хода

Если всё так, ты прошёл самую сложную часть.

## 4. Проверить работу сессий

Перед тем как идти дальше, убедись, что возобновление работает:

```bash
hermes --continue    # Resume the most recent session
hermes -c            # Short form
```

Это должно вернуть тебя к только что завершённой сессии. Если нет, проверь, в том ли профиле ты находишься и действительно ли сессия была сохранена. Это важно позже, когда будешь переключаться между разными настройками или машинами.

## 5. Попробовать ключевые функции

### Использовать терминал

```
❯ What's my disk usage? Show the top 5 largest directories.
```

Агент выполняет терминальные команды от твоего имени и показывает результаты.

### Слеш‑команды

Нажми `/`, чтобы увидеть автодополнение со всеми командами:

| Команда | Что делает |
|---------|------------|
| `/help` | Показать все доступные команды |
| `/tools` | Список доступных инструментов |
| `/model` | Переключить модели интерактивно |
| `/personality pirate` | Попробовать забавную личность |
| `/save` | Сохранить разговор |

### Многострочный ввод

Нажми `Alt+Enter`, `Ctrl+J` или `Shift+Enter`, чтобы добавить новую строку. `Shift+Enter` требует терминала, который отправляет его как отдельную последовательность (по умолчанию Kitty / foot / WezTerm / Ghostty; iTerm2 / Alacritty / VS Code terminal работают после включения протокола клавиатуры Kitty). `Alt+Enter` и `Ctrl+J` работают во всех терминалах.

### Прервать агента

Если агент работает слишком долго, введи новое сообщение и нажми Enter — текущая задача будет прервана и агент перейдёт к новым инструкциям. Также работает `Ctrl+C`.

## 6. Добавить следующий слой

Только после того, как базовый чат заработает. Выбирай, что нужно:

### Бот или общий помощник

```bash
hermes gateway setup    # Interactive platform configuration
```

Подключи [Telegram](/user-guide/messaging/telegram), [Discord](/user-guide/messaging/discord), [Slack](/user-guide/messaging/slack), [WhatsApp](/user-guide/messaging/whatsapp), [Signal](/user-guide/messaging/signal), [Email](/user-guide/messaging/email), [Home Assistant](/user-guide/messaging/homeassistant) или [Microsoft Teams](/user-guide/messaging/teams).

### Автоматизация и инструменты

- `hermes tools` — настроить доступ к инструментам для каждой платформы
- `hermes skills` — просмотреть и установить переиспользуемые workflows
- Cron — только после того, как бот или CLI стабилизируются

### Песочница терминала

Для безопасности запускай агента в Docker‑контейнере или на удалённом сервере:

```bash
hermes config set terminal.backend docker    # Docker isolation
hermes config set terminal.backend ssh       # Remote server
```

### Голосовой режим

```bash
# From the Hermes install directory (the curl installer placed it at
# ~/.hermes/hermes-agent on Linux/macOS or %LOCALAPPDATA%\hermes\hermes-agent on Windows):
cd ~/.hermes/hermes-agent
uv pip install -e ".[voice]"
# Includes faster-whisper for free local speech-to-text
```

Затем в CLI: `/voice on`. Нажми `Ctrl+B` для записи. См. [Voice Mode](../user-guide/features/voice-mode.md).

### Skills

```bash
hermes skills search kubernetes
hermes skills install openai/skills/k8s
```

Или используй `/skills` внутри чат‑сессии.

### MCP‑серверы

```yaml
# Add to ~/.hermes/config.yaml
mcp_servers:
  github:
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxx"
```

### Интеграция редактора (ACP)

Поддержка ACP поставляется с экстрами `[all]`, поэтому curl‑инсталлятор уже включает её. Просто запусти:

```bash
hermes acp
```

(Если устанавливали без `[all]`, сначала выполните `cd ~/.hermes/hermes-agent && uv pip install -e ".[acp]"`.)

См. [ACP Editor Integration](../user-guide/features/acp.md).

---

## Частые причины сбоев

Это проблемы, которые отнимают больше всего времени:

| Симптом | Вероятная причина | Как исправить |
|---|---|---|
| Hermes открывается, но отдает пустые или сломанные ответы | Ошибка аутентификации провайдера или неверный выбор модели | Запусти `hermes model` снова и проверь провайдера, модель и аутентификацию |
| Пользовательский endpoint «работает», но возвращает мусор | Неправильный базовый URL, имя модели или он не совместим с OpenAI | Сначала проверь endpoint в отдельном клиенте |
| Gateway стартует, но никто не может ему писать | Токен бота, whitelist или настройка платформы неполные | Повтори `hermes gateway setup` и проверь `hermes gateway status` |
| `hermes --continue` не находит старую сессию | Сменили профиль или сессия не была сохранена | Проверь `hermes sessions list` и убедись, что в нужном профиле |
| Модель недоступна или странное fallback‑поведение | Роутинг провайдера или настройки fallback слишком агрессивны | Отключи роутинг, пока базовый провайдер не стабилен |
| `hermes doctor` сигнализирует проблемы конфигурации | Значения в конфиге отсутствуют или устарели | Исправь конфиг, протестируй простой чат перед добавлением функций |

## Инструменты восстановления

Когда что‑то идёт не так, действуй в таком порядке:

1. `hermes doctor`
2. `hermes model`
3. `hermes setup`
4. `hermes sessions list`
5. `hermes --continue`
6. `hermes gateway status`

Эта последовательность быстро вернёт тебя из «сломанных вибраций» в известное состояние.

---

## Быстрая справка

| Команда | Описание |
|---------|----------|
| `hermes` | Начать чат |
| `hermes model` | Выбрать LLM‑провайдера и модель |
| `hermes tools` | Настроить, какие инструменты включены для каждой платформы |
| `hermes setup` | Полный мастер установки (настраивает всё сразу) |
| `hermes doctor` | Диагностировать проблемы |
| `hermes update` | Обновить до последней версии |
| `hermes gateway` | Запустить шлюз обмена сообщениями |
| `hermes --continue` | Возобновить последнюю сессию |

## Следующие шаги

- **[CLI Guide](../user-guide/cli.md)** — освоить терминальный интерфейс
- **[Configuration](../user-guide/configuration.md)** — кастомизировать установку
- **[Messaging Gateway](../user-guide/messaging/index.md)** — подключить Telegram, Discord, Slack, WhatsApp, Signal, Email, Home Assistant, Teams и др.
- **[Tools & Toolsets](../user-guide/features/tools.md)** — исследовать доступные возможности
- **[AI Providers](../integrations/providers.md)** — полный список провайдеров и детали настройки
- **[Skills System](../user-guide/features/skills.md)** — переиспользуемые workflows и знания
- **[Tips & Best Practices](../guides/tips.md)** — советы продвинутым пользователям