---
sidebar_position: 3
title: "FAQ та усунення проблем"
description: "Часті запитання та рішення поширених проблем з Hermes Agent"
---

# FAQ та вирішення проблем

Швидкі відповіді та виправлення найпоширеніших питань і проблем.

---
## Часті запитання

### Які провайдери LLM працюють з Hermes?

Hermes Agent працює з будь‑яким API, сумісним з OpenAI. Підтримувані провайдери включають:

- **[OpenRouter](https://openrouter.ai/)** — доступ до сотень моделей через один API‑ключ (рекомендовано для гнучкості)
- **[Nous Portal](/integrations/nous-portal)** — шлюз підписки Nous Research — 300+ моделей плюс веб/зображення/TTS/браузер через один OAuth‑логін (рекомендовано для новачків)
- **OpenAI** — GPT‑5.4, GPT‑5‑codex, GPT‑4.1, GPT‑4o тощо
- **Anthropic** — моделі Claude (прямий API, OAuth via `hermes auth add anthropic`, OpenRouter або будь‑який сумісний проксі)
- **Google** — моделі Gemini (прямий API via `gemini` provider, OAuth‑провайдер `google-gemini-cli`, OpenRouter або сумісний проксі)
- **z.ai / ZhipuAI** — моделі GLM
- **Kimi / Moonshot AI** — моделі Kimi
- **MiniMax** — глобальні та китайські кінцеві точки
- **Локальні моделі** — через [Ollama](https://ollama.com/), [vLLM](https://docs.vllm.ai/), [llama.cpp](https://github.com/ggerganov/llama.cpp), [SGLang](https://github.com/sgl-project/sglang) або будь‑який сервер, сумісний з OpenAI

Вкажи свого провайдера за допомогою `hermes model` або відредагувавши `~/.hermes/.env`. Дивись довідку [Environment Variables](./environment-variables.md) для всіх ключів провайдерів.

### Чи працює це на Windows?

**Не нативно.** Hermes Agent потребує Unix‑подібного середовища. На Windows встанови [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install) і запускай Hermes всередині нього. Стандартна команда встановлення працює без проблем у WSL2:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

### Я запускаю Hermes у WSL2. Який найкращий спосіб керувати моїм звичайним Chrome у Windows?

Віддавай перевагу мосту MCP над `/browser connect`.

**Рекомендований шаблон**

- запускати Hermes всередині WSL2
- продовжувати користуватись звичайним підписаним Chrome у Windows
- додати `chrome-devtools-mcp` як сервер MCP через `cmd.exe` або `powershell.exe`
- дозволити Hermes використовувати отримані інструменти браузера MCP

Це надійніше, ніж намагатися змусити транспорт браузера ядра Hermes підключитись безпосередньо через межу WSL2/Windows.

Дивись:

- [Use MCP with Hermes](../guides/use-mcp-with-hermes.md#wsl2-bridge-hermes-in-wsl-to-windows-chrome)
- [Browser Automation](../user-guide/features/browser.md#wsl2--windows-chrome-prefer-mcp-over-browser-connect)

### Чи працює це на Android / Termux?

Так — Hermes має перевірений шлях встановлення для Termux на Android‑телефонах.

**Швидке встановлення**

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

Для повного опису кроків, підтримуваних додатків та поточних обмежень дивись [Termux guide](../getting-started/termux.md).

**Важливе зауваження:** повний екстра `.[all]` наразі недоступний на Android, бо екстра `voice` залежить від `faster-whisper` → `ctranslate2`, а `ctranslate2` не публікує Android‑колеса. Використовуй перевірений екстра `.[termux]`.

### Чи надсилаються мої дані кудись?

API‑виклики надсилаються **лише до провайдера LLM, який ти налаштував** (наприклад, OpenRouter, твій локальний Ollama‑сервер). Hermes Agent не збирає телеметрію, дані використання чи аналітику. Твої розмови, пам'ять і навички зберігаються локально у `~/.hermes/`.

### Чи можу я використовувати його офлайн / з локальними моделями?

Так. Запусти `hermes model`, вибери **Custom endpoint** і введи URL твого сервера:

```bash
hermes model
# Select: Custom endpoint (enter URL manually)
# API base URL: http://localhost:11434/v1
# API key: ollama
# Model name: qwen3.5:27b
# Context length: 64000   ← Hermes minimum; set this to match your server's actual context window
```

Або налаштуй це безпосередньо у `config.yaml`:

```yaml
model:
  default: qwen3.5:27b
  provider: custom
  base_url: http://localhost:11434/v1
```

Hermes зберігає кінцеву точку, провайдера та базовий URL у `config.yaml`, тому вони зберігаються після перезапуску. Якщо на твоєму локальному сервері завантажена лише одна модель, `/model custom` автоматично її визначить. Також можна встановити `provider: custom` у `config.yaml` — це справжній провайдер, а не псевдонім.

Працює з Ollama, vLLM, сервером llama.cpp, SGLang, LocalAI та іншими. Дивись [Configuration guide](../user-guide/configuration.md) для деталей.

:::tip Ollama users
Якщо ти встановив власний `num_ctx` в Ollama (наприклад, `ollama run --num_ctx 64000`), обов’язково встанови відповідну довжину контексту в Hermes — `/api/show` Ollama повертає *максимальний* контекст моделі, а не фактичний `num_ctx`, який ти налаштував.
:::

:::tip Timeouts with local models
Hermes автоматично визначає локальні кінцеві точки і пом’якшує тайм‑аути потоків (тайм‑аут читання підвищено з 120 s до 1800 s, виявлення «застарілих» потоків вимкнено). Якщо ти все ж стикаєшся з тайм‑аутами при дуже великих контекстах, встанови `HERMES_STREAM_READ_TIMEOUT=1800` у своєму `.env`. Дивись [Local LLM guide](../guides/local-llm-on-mac.md#timeouts) для деталей.
:::

### Скільки це коштує?

Сам Hermes Agent **безкоштовний і з відкритим кодом** (ліцензія MIT). Ти платиш лише за використання API LLM у обраного провайдера. Локальні моделі повністю безкоштовні.

### Чи можуть кілька людей користуватись одним інстансом?

Так. [Messaging gateway](../user-guide/messaging/index.md) дозволяє кільком користувачам взаємодіяти з одним інстансом Hermes Agent через Telegram, Discord, Slack, WhatsApp або Home Assistant. Доступ контролюється білим списком (конкретні ID користувачів) та паруванням DM (перший, хто написав, отримує доступ).

### У чому різниця між пам'яттю та навичками?

- **Пам'ять** зберігає **факти** — те, що агент знає про тебе, твої проєкти та уподобання. Пам'ять автоматично витягується за релевантністю.
- **Навички** зберігають **процедури** — покрокові інструкції, як щось робити. Навички викликаються, коли агент стикається зі схожим завданням.

Обидва типи зберігаються між сесіями. Дивись [Memory](../user-guide/features/memory.md) та [Skills](../user-guide/features/skills.md) для деталей.

### Чи можу я використовувати його у своєму Python‑проєкті?

Так. Імпортуй клас `AIAgent` і використай Hermes програмно:

```python
from run_agent import AIAgent

agent = AIAgent(model="anthropic/claude-opus-4.7")
response = agent.chat("Explain quantum computing briefly")
```

Дивись [Python Library guide](../user-guide/features/code-execution.md) для повного опису API.
## Усунення проблем
### Проблеми з встановленням

#### `hermes: command not found` після встановлення

**Причина:** Твоя оболонка не перезавантажила оновлений `PATH`.

**Рішення:**
```bash
# Reload your shell profile
source ~/.bashrc    # bash
source ~/.zshrc     # zsh

# Or start a new terminal session
```

Якщо це все ще не працює, перевір місце встановлення:
```bash
which hermes
ls ~/.local/bin/hermes
```

:::tip
Інсталятор додає `~/.local/bin` до твого `PATH`. Якщо ти користуєшся нестандартною конфігурацією оболонки, додай `export PATH="$HOME/.local/bin:$PATH"` вручну.
:::

#### Версія Python занадто стара

**Причина:** Hermes вимагає Python 3.11 або новішого.

**Рішення:**
```bash
python3 --version   # Check current version

# Install a newer Python
sudo apt install python3.12   # Ubuntu/Debian
brew install python@3.12      # macOS
```

Інсталятор обробляє це автоматично — якщо ти бачиш цю помилку під час ручного встановлення, спочатку онови Python.

#### У терміналі `node: command not found` (або `nvm`, `pyenv`, `asdf`, …)

**Причина:** Hermes створює знімок середовища для сесії, запускаючи `bash -l` один раз під час старту. Bash‑login‑shell читає `/etc/profile`, `~/.bash_profile` та `~/.profile`, але **не підключає `~/.bashrc`** — тому інструменти, які встановлюються там (`nvm`, `asdf`, `pyenv`, `cargo`, кастомні експорти `PATH`), залишаються невидимими для знімка. Це найчастіше трапляється, коли Hermes працює під systemd або в мінімальній оболонці, де нічого не завантажено з інтерактивного профілю оболонки.

**Рішення:** Hermes автоматично підключає `~/.bashrc` за замовчуванням. Якщо цього недостатньо — наприклад, ти користувач zsh, у якого `PATH` визначено у `~/.zshrc`, або ініціалізуєш `nvm` з окремого файлу — вкажи додаткові файли для підключення у `~/.hermes/config.yaml`:

```yaml
terminal:
  shell_init_files:
    - ~/.zshrc                     # zsh users: pulls zsh-managed PATH into the bash snapshot
    - ~/.nvm/nvm.sh                # direct nvm init (works regardless of shell)
    - /etc/profile.d/cargo.sh      # system-wide rc files
  # When this list is set, the default ~/.bashrc auto-source is NOT added —
  # include it explicitly if you want both:
  #   - ~/.bashrc
  #   - ~/.zshrc
```

Відсутні файли пропускаються без повідомлення. Підключення відбувається в bash, тому файли, що залежать лише від синтаксису zsh, можуть викликати помилки — якщо це проблема, підключай лише частину, що встановлює `PATH` (наприклад, `nvm.sh`), а не весь rc‑файл.

Щоб вимкнути автоматичне підключення (тільки строгі правила login‑shell):

```yaml
terminal:
  auto_source_bashrc: false
```

#### `uv: command not found`

**Причина:** Менеджер пакетів `uv` не встановлений або не знаходиться в `PATH`.

**Рішення:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

#### Помилки «Permission denied» під час встановлення

**Причина:** Недостатньо прав для запису у каталог встановлення.

**Рішення:**
```bash
# Don't use sudo with the installer — it installs to ~/.local/bin
# If you previously installed with sudo, clean up:
sudo rm /usr/local/bin/hermes
# Then re-run the standard installer
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

---
### Проблеми з провайдером та моделлю

#### `/model` показує лише одного провайдера / неможливо переключити провайдери

**Причина:** `/model` (всередині сесії чату) може переключатися лише між провайдерами, які **вже налаштовані**. Якщо ти налаштував лише OpenRouter, то саме його `/model` і показуватиме.

**Рішення:** Вийди з поточної сесії та використай `hermes model` у терміналі, щоб додати нових провайдерів:

```bash
# Exit the Hermes chat session first (Ctrl+C or /quit)

# Run the full provider setup wizard
hermes model

# This lets you: add providers, run OAuth, enter API keys, configure endpoints
```

Після додавання нового провайдера за допомогою `hermes model` запусти нову сесію чату — `/model` тепер покаже всіх налаштованих провайдерів.

:::tip Швидка довідка
| Хочеш… | Використай |
|-----------|-----|
| Додати нового провайдера | `hermes model` (з терміналу) |
| Ввести/змінити API‑ключі | `hermes model` (з терміналу) |
| Перемкнути модель під час сесії | `/model <name>` (всередині сесії) |
| Перемкнутись на інший налаштований провайдер | `/model provider:model` (всередині сесії) |
:::

#### API‑ключ не працює

**Причина:** Ключ відсутній, прострочений, неправильно встановлений або належить іншому провайдеру.

**Рішення:**
```bash
# Check your configuration
hermes config show

# Re-configure your provider
hermes model

# Or set directly
hermes config set OPENROUTER_API_KEY sk-or-v1-xxxxxxxxxxxx
```

:::warning
Переконайся, що ключ відповідає провайдеру. Ключ OpenAI не працюватиме з OpenRouter і навпаки. Перевір `~/.hermes/.env` на наявність конфліктних записів.
:::

#### Модель недоступна / модель не знайдена

**Причина:** Ідентифікатор моделі неправильний або недоступний у твого провайдера.

**Рішення:**
```bash
# List available models for your provider
hermes model

# Set a valid model
hermes config set HERMES_MODEL anthropic/claude-opus-4.7

# Or specify per-session
hermes chat --model openrouter/meta-llama/llama-3.1-70b-instruct
```

#### Обмеження швидкості (помилки 429)

**Причина:** Перевищено ліміти швидкості твого провайдера.

**Рішення:** Зачекай трохи і спробуй ще раз. Для тривалого використання розглянь:
- Оновлення плану провайдера
- Перехід на іншу модель або провайдера
- Використання `hermes chat --provider <alternative>` для маршрутизації до іншого бекенду

#### Перевищено довжину контексту

**Причина:** Розмова стала занадто довгою для вікна контексту моделі, або Hermes визначив неправильну довжину контексту для твоєї моделі.

**Рішення:**
```bash
# Compress the current session
/compress

# Or start a fresh session
hermes chat

# Use a model with a larger context window
hermes chat --model openrouter/google/gemini-3-flash-preview
```

Якщо це сталося під час першої довгої розмови, Hermes міг визначити неправильну довжину контексту для твоєї моделі. Перевір, що було визначено:

Подивися рядок запуску CLI — там показана виявлена довжина контексту (наприклад, `📊 Context limit: 128000 tokens`). Також можна перевірити за допомогою `/usage` під час сесії.

Щоб виправити визначення контексту, встанови його явно:

```yaml
# In ~/.hermes/config.yaml
model:
  default: your-model-name
  context_length: 131072  # your model's actual context window
```

Або для кастомних кінцевих точок додай його per‑model:

```yaml
custom_providers:
  - name: "My Server"
    base_url: "http://localhost:11434/v1"
    models:
      qwen3.5:27b:
        context_length: 64000
```

Дивись [Виявлення довжини контексту](../integrations/providers.md#context-length-detection) для того, як працює авто‑виявлення та всі варіанти перевизначення.
### Проблеми з терміналом

#### Команда заблокована як небезпечна

**Причина:** Hermes виявив потенційно руйнівну команду (наприклад, `rm -rf`, `DROP TABLE`). Це функція безпеки.

**Рішення:** Коли з’явиться запит, переглянь команду та введи `y`, щоб схвалити її. Також можна:
- Попросити агента використати безпечніший варіант
- Переглянути повний список небезпечних шаблонів у [документації безпеки](../user-guide/security.md)

:::tip
Це працює так, як задумано — Hermes ніколи не виконує руйнівні команди без підтвердження. Запит на схвалення показує точно те, що буде виконано.
:::

#### `sudo` не працює через шлюз повідомлень

**Причина:** Шлюз повідомлень працює без інтерактивного терміналу, тому `sudo` не може запросити пароль.

**Рішення:**
- Уникай `sudo` в обміні повідомленнями — попроси агента знайти альтернативи
- Якщо потрібно використати `sudo`, налаштуй безпарольний `sudo` для конкретних команд у `/etc/sudoers`
- Або перейди до інтерфейсу терміналу для адміністративних завдань: `hermes chat`

#### Docker‑бекенд не підключається

**Причина:** Демон Docker не запущений або у користувача немає прав.

**Рішення:**
```bash
# Check Docker is running
docker info

# Add your user to the docker group
sudo usermod -aG docker $USER
newgrp docker

# Verify
docker run hello-world
```

---
### Проблеми з обміном повідомленнями

#### Бот не відповідає на повідомлення

**Причина:** Бот не запущений, не авторизований або твій користувач не включений у білий список.

**Рішення:**
```bash
# Check if the gateway is running
hermes gateway status

# Start the gateway
hermes gateway start

# Check logs for errors
cat ~/.hermes/logs/gateway.log | tail -50
```

#### Повідомлення не доставляються

**Причина:** Проблеми з мережею, токен бота прострочений або неправильна конфігурація вебхука платформи.

**Рішення:**
- Перевір, чи дійсний токен бота, за допомогою `hermes gateway setup`
- Переглянь логи шлюзу: `cat ~/.hermes/logs/gateway.log | tail -50`
- Для платформ, що працюють через вебхук (Slack, WhatsApp), переконайся, що твій сервер публічно доступний

#### Невизначеність білого списку — хто може спілкуватися з ботом?

**Причина:** Режим авторизації визначає, хто отримує доступ.

**Рішення:**

| Режим | Як це працює |
|------|--------------|
| **Allowlist** | Тільки ID користувачів, зазначені в конфігурації, можуть взаємодіяти |
| **DM pairing** | Перший користувач, який написав у DM, отримує виключний доступ |
| **Open** | Будь‑хто може взаємодіяти (не рекомендовано для продакшн) |

Налаштуй у `~/.hermes/config.yaml` у розділі налаштувань твого шлюзу. Дивись [документацію з обміну повідомленнями](../user-guide/messaging/index.md).

#### Шлюз не запускається

**Причина:** Відсутні залежності, конфлікти портів або неправильна конфігурація токенів.

**Рішення:**
```bash
# Install core messaging gateway dependencies
pip install "hermes-agent[messaging]"  # Telegram, Discord, Slack, and shared gateway deps

# Check for port conflicts
lsof -i :8080

# Verify configuration
hermes config show
```

#### WSL: Шлюз постійно розривається або `hermes gateway start` не працює

**Причина:** Підтримка systemd у WSL ненадійна. Багато інсталяцій WSL2 не мають увімкненого systemd, і навіть коли увімкнено, служби можуть не виживати після перезапуску WSL або сплячого режиму Windows.

**Рішення:** Використовуй режим foreground замість сервісу systemd:

```bash
# Option 1: Direct foreground (simplest)
hermes gateway run

# Option 2: Persistent via tmux (survives terminal close)
tmux new -s hermes 'hermes gateway run'
# Reattach later: tmux attach -t hermes

# Option 3: Background via nohup
nohup hermes gateway run > ~/.hermes/logs/gateway.log 2>&1 &
```

Якщо все ж хочеш спробувати systemd, переконайся, що він увімкнений:

1. Відкрий `/etc/wsl.conf` (створи, якщо його немає)
2. Додай:
      ```ini
   [boot]
   systemd=true
   ```
3. У PowerShell: `wsl --shutdown`
4. Знову відкрий термінал WSL
5. Перевір: `systemctl is-system-running` має вивести `running` або `degraded`

:::tip Автозапуск при завантаженні Windows
Для надійного автозапуску використай Планувальник завдань Windows, щоб запускати WSL + шлюз під час входу:
1. Створи завдання, яке виконує `wsl -d Ubuntu -- bash -lc 'hermes gateway run'`
2. Встанови тригер на вхід користувача
:::

#### macOS: Node.js / ffmpeg / інші інструменти не знайдено шлюзом

**Причина:** Служби launchd успадковують мінімальний `PATH` (`/usr/bin:/bin:/usr/sbin:/sbin`), який не включає Homebrew, nvm, cargo чи інші каталоги інструментів, встановлених користувачем. Це часто ламає місток WhatsApp (`node not found`) або транскрипцію голосу (`ffmpeg not found`).

**Рішення:** Шлюз захоплює твій `PATH` оболонки, коли ти виконуєш `hermes gateway install`. Якщо ти встановив інструменти після налаштування шлюзу, повторно запусти інсталяцію, щоб захопити оновлений `PATH`:

```bash
hermes gateway install    # Re-snapshots your current PATH
hermes gateway start      # Detects the updated plist and reloads
```

Можеш перевірити, чи `plist` має правильний `PATH`:

```bash
/usr/libexec/PlistBuddy -c "Print :EnvironmentVariables:PATH" \
  ~/Library/LaunchAgents/ai.hermes.gateway.plist
```

---
### Проблеми продуктивності

#### Повільні відповіді

**Причина:** Велика модель, віддалений сервер API або важкий системний запит із багатьма інструментами.

**Рішення:**
- Спробуй швидшу/меншу модель: `hermes chat --model openrouter/meta-llama/llama-3.1-8b-instruct`
- Зменш активні набори інструментів: `hermes chat -t "terminal"`
- Перевір затримку мережі до провайдера
- Для локальних моделей переконайся, що маєш достатньо GPU VRAM

#### Велика витрата токенів

**Причина:** Довгі розмови, багатослівні системні запити або багато викликів інструментів, що накопичують контекст.

**Рішення:**
```bash
# Compress the conversation to reduce tokens
/compress

# Check session token usage
/usage
```

:::tip
Регулярно використовуй `/compress` під час довгих сесій. Він підсумовує історію розмови та значно зменшує витрату токенів, зберігаючи контекст.
:::

#### Сесія стає надто довгою

**Причина:** Тривалі розмови накопичують повідомлення та виводи інструментів, наближаючись до меж контексту.

**Рішення:**
```bash
# Compress current session (preserves key context)
/compress

# Start a new session with a reference to the old one
hermes chat

# Resume a specific session later if needed
hermes chat --continue
```

---
### Проблеми MCP

#### Сервер MCP не підключається

**Причина:** Не знайдено бінарний файл сервера, неправильний шлях до команди або відсутнє середовище виконання.

**Рішення:**
```bash
# Ensure MCP dependencies are installed (already included in standard install)
cd ~/.hermes/hermes-agent && uv pip install -e ".[mcp]"

# For npm-based servers, ensure Node.js is available
node --version
npx --version

# Test the server manually
npx -y @modelcontextprotocol/server-filesystem /tmp
```

Перевірте ваш файл `~/.hermes/config.yaml` з налаштуваннями MCP:
```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/docs"]
```

#### Інструменти не відображаються з сервера MCP

**Причина:** Сервер запущено, але виявлення інструментів не вдалося, інструменти були відфільтровані конфігурацією або сервер не підтримує можливість MCP, яку ви очікували.

**Рішення:**
- Перевірте журнали gateway/agent на помилки підключення MCP
- Переконайтеся, що сервер відповідає на метод RPC `tools/list`
- Перегляньте налаштування `tools.include`, `tools.exclude`, `tools.resources`, `tools.prompts` або `enabled` для цього сервера
- Пам’ятайте, що інструменти ресурсів/промптів реєструються лише коли сесія фактично підтримує ці можливості
- Використайте `/reload-mcp` після зміни конфігурації

```bash
# Verify MCP servers are configured
hermes config show | grep -A 12 mcp_servers

# Restart Hermes or reload MCP after config changes
hermes chat
```

Дивіться також:
- [MCP (Model Context Protocol)](/user-guide/features/mcp)
- [Використання MCP з Hermes](/guides/use-mcp-with-hermes)
- [Посилання на конфігурацію MCP](/reference/mcp-config-reference)

#### Помилки тайм‑ауту MCP

**Причина:** Сервер MCP занадто довго відповідає або впав під час виконання.

**Рішення:**
- Збільшіть тайм‑аут у конфігурації вашого сервера MCP, якщо це підтримується
- Перевірте, чи процес сервера MCP все ще працює
- Для віддалених HTTP‑серверів MCP перевірте мережеве з’єднання

:::warning
Якщо сервер MCP падає під час запиту, Hermes повідомить про тайм‑аут. Перевірте журнали самого сервера (а не лише журнали Hermes), щоб діагностувати причину.
:::
## Профілі

### Чим профілі відрізняються від простого встановлення `HERMES_HOME`?

Профілі – це керований шар поверх `HERMES_HOME`. Ти *можеш* вручну встановлювати `HERMES_HOME=/some/path` перед кожною командою, але профілі виконують всю «трубопровідну» роботу за тебе: створюють структуру каталогів, генерують shell‑аліаси (`hermes-work`), відстежують активний профіль у `~/.hermes/active_profile` і автоматично синхронізують оновлення навичок між усіма профілями. Вони також інтегруються з автодоповненням, тож тобі не треба запам’ятовувати шляхи.

### Чи можуть два профілі використовувати один і той же токен бота?

Ні. Кожна платформа обміну повідомленнями (Telegram, Discord тощо) вимагає виключного доступу до токену бота. Якщо два профілі спробують одночасно використовувати один токен, другий шлюз не зможе підключитися. Створи окремий бот для кожного профілю — для Telegram звертайся до [@BotFather](https://t.me/BotFather), щоб створити додаткові боти.

### Чи діляться профілі пам’яттю або сесіями?

Ні. Кожен профіль має власне сховище пам’яті, базу даних сесій і каталог навичок. Вони повністю ізольовані. Якщо хочеш створити новий профіль з існуючими пам’яттями та сесіями, використай `hermes profile create newname --clone-all`, щоб скопіювати все з поточного профілю.

### Що відбувається, коли я запускаю `hermes update`?

`hermes update` завантажує останній код і переустановлює залежності **один раз** (не для кожного профілю). Потім він автоматично синхронізує оновлені навички до всіх профілів. Тобі потрібно запускати `hermes update` лише один раз — він охоплює всі профілі на машині.

### Скільки профілів я можу запустити?

Жорсткого обмеження немає. Кожен профіль – це просто каталог у `~/.hermes/profiles/`. Практичне обмеження залежить від вільного місця на диску та кількості одночасних шлюзів, які може обробляти твоя система (кожен шлюз – це легковаговий процес Python). Запуск десятків профілів цілком прийнятний; кожен неактивний профіль не споживає ресурси.
## Робочі процеси та шаблони

### Використання різних моделей для різних завдань (багатомодельні робочі процеси)

**Сценарій:** Ти використовуєш GPT‑5.4 як основну модель, але Gemini або Grok краще пишуть контент для соцмереж. Ручне перемикання моделей щораз — нудно.

**Рішення: Конфігурація делегування.** Hermes може автоматично направляти підагенти до іншої моделі. Встанови це у `~/.hermes/config.yaml`:

```yaml
delegation:
  model: "google/gemini-3-flash-preview"   # subagents use this model
  provider: "openrouter"                    # provider for subagents
```

Тепер, коли ти скажеш Hermes «напиши мені Twitter‑тред про X», і він створить підагент `delegate_task`, цей підагент працюватиме на Gemini замість твоєї основної моделі. Твоя головна розмова залишиться на GPT‑5.4.

Ти також можеш явно вказати в запиті: *«Делегуй завдання написати пости для соцмереж про наш запуск продукту. Використай свого підагента для фактичного написання.»* Агент використає `delegate_task`, який автоматично підхопить конфігурацію делегування.

Для одноразових перемикань моделей без делегування використай `/model` у CLI:

```bash
/model google/gemini-3-flash-preview    # switch for this session
# ... write your content ...
/model openai/gpt-5.4                   # switch back
```

Дивись [Subagent Delegation](../user-guide/features/delegation.md) для докладнішої інформації про те, як працює делегування.

### Запуск кількох агентів на одному номері WhatsApp (прив’язка per‑chat)

**Сценарій:** У OpenClaw у тебе було кілька незалежних агентів, прив’язаних до конкретних чатів WhatsApp — один для групи сімейного списку покупок, інший для приватного чату. Чи може Hermes це зробити?

**Поточне обмеження:** Кожен профіль Hermes потребує свій власний номер/сесію WhatsApp. Не можна прив’язати кілька профілів до різних чатів на одному номері — шлюз WhatsApp (Baileys) використовує одну автентифіковану сесію на номер.

**Обхідні шляхи:**

1. **Використовуй один профіль зі зміною персональності.** Створи різні файли контексту `AGENTS.md` або використай команду `/personality`, щоб змінювати поведінку per‑chat. Агент бачить, у якому чаті він знаходиться, і може адаптуватися.

2. **Використовуй cron‑задачі для спеціалізованих функцій.** Для трекера списку покупок налаштуй cron‑задачу, яка моніторить конкретний чат і керує списком — окремий агент не потрібен.

3. **Використовуй окремі номери.** Якщо потрібні справді незалежні агенти, підключи кожному профілю свій номер WhatsApp. Віртуальні номери, наприклад Google Voice, підходять.

4. **Використовуй Telegram або Discord.** Ці платформи природніше підтримують прив’язку per‑chat — кожна група Telegram або канал Discord отримує свою сесію, і ти можеш запускати кілька токенів ботів (по одному на профіль) в одному обліковому записі.

Дивись [Profiles](../user-guide/profiles.md) та [WhatsApp setup](../user-guide/messaging/whatsapp.md) для докладніших відомостей.

### Керування тим, що відображається в Telegram (приховування логів і міркувань)

**Сценарій:** У Telegram ти бачиш логи виконання шлюзу, міркування Hermes та деталі викликів інструментів замість лише фінального результату.

**Рішення:** Параметр `display.tool_progress` у `config.yaml` визначає, скільки активності інструментів показувати:

```yaml
display:
  tool_progress: "off"   # options: off, new, all, verbose
```

- **`off`** — лише фінальна відповідь. Без викликів інструментів, без міркувань, без логів.
- **`new`** — показує нові виклики інструментів у міру їх появи (короткі однорядкові повідомлення).
- **`all`** — показує всю активність інструментів, включно з результатами.
- **`verbose`** — повний детальний вивід, включно з аргументами інструментів та їх виводом.

Для месенджер‑платформ зазвичай підходять `off` або `new`. Після редагування `config.yaml` перезапусти шлюз, щоб зміни набули сили.

Ти також можеш перемикати це per‑session командою `/verbose` (за умови, що вона ввімкнена):

```yaml
display:
  tool_progress_command: true   # enables /verbose in the gateway
```

### Керування навичками в Telegram (обмеження на slash‑команди)

**Сценарій:** У Telegram є ліміт у 100 slash‑команд, і твої навички вже підходять до цього ліміту. Ти хочеш вимкнути непотрібні навички, але налаштування `hermes skills config` не працюють.

**Рішення:** Використай `hermes skills config` для вимкнення навичок per‑platform. Це записує зміни у `config.yaml`:

```yaml
skills:
  disabled: []                    # globally disabled skills
  platform_disabled:
    telegram: [skill-a, skill-b]  # disabled only on telegram
```

Після зміни **перезапусти шлюз** (`hermes gateway restart` або вбий процес і запусти заново). Меню команд Telegram‑бота перебудується під час старту.

:::tip
Навички з дуже довгими описами обрізаються до 40 символів у меню Telegram, щоб вкластися у розмір payload. Якщо навички не з’являються, можливо, проблема у загальному розмірі payload, а не у ліміті 100 команд — вимкнення невикористовуваних навичок допомагає в обох випадках.
:::

### Спільні сесії в темі (кілька користувачів, одна розмова)

**Сценарій:** У Telegram або Discord є тема, де кілька людей згадують бота. Ти хочеш, щоб усі згадки в цій темі входили до однієї спільної розмови, а не створювали окремі сесії per‑user.

**Поточна поведінка:** Hermes створює сесії, ключовані за ID користувача на більшості платформ, тому кожна особа має власний контекст розмови. Це задумано для приватності та ізоляції контексту.

**Обхідні шляхи:**

1. **Використовуй Slack.** Сесії в Slack ключуються за темою, а не за користувачем. Кілька користувачів в одній темі ділять одну розмову — саме те, що тобі потрібно. Це найприродніше рішення.

2. **Використовуй груповий чат з одним «оператором».** Якщо одна особа виступає як «оператор», який передає питання, сесія залишається єдиною. Інші можуть лише читати.

3. **Використовуй канал Discord.** Сесії в Discord ключуються за каналом, тому всі користувачі в одному каналі ділять контекст. Створи окремий канал для спільної розмови.

### Експорт Hermes на інший комп’ютер

**Сценарій:** Ти створив навички, cron‑задачі та пам’ять на одному комп’ютері і хочеш перенести все на новий Linux‑сервер.

**Рішення:**

1. Встанови Hermes Agent на новому комп’ютері:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
   ```

2. На **джерельному комп’ютері** створи повний бекап:
   ```bash
   hermes backup
   ```
   Це створить zip‑архів усього каталогу `~/.hermes/` — конфіг, API‑ключі, пам’ять, навички, сесії та профілі — і збереже його у домашньому каталозі як `~/hermes-backup-<timestamp>.zip`.

3. Скопіюй zip‑файл на новий комп’ютер і імпортуй його:
   ```bash
   # On the source machine
   scp ~/hermes-backup-<timestamp>.zip newmachine:~/

   # On the new machine
   hermes import ~/hermes-backup-<timestamp>.zip
   ```

4. На новому комп’ютері запусти `hermes setup`, щоб перевірити, чи працюють API‑ключі та конфігурація провайдера.

### Перенесення окремого профілю на інший комп’ютер

**Сценарій:** Ти хочеш перемістити або поділитися лише одним конкретним профілем — а не усією інсталяцією.

```bash
# On the source machine
hermes profile export work ./work-backup.tar.gz

# Copy the file to the target machine, then:
hermes profile import ./work-backup.tar.gz work
```

Імпортований профіль міститиме всю конфігурацію, пам’ять, сесії та навички з експорту. Можливо, доведеться оновити шляхи або повторно автентифікуватися у провайдерів, якщо новий комп’ютер має інше середовище.

### `hermes backup` vs `hermes profile export`

| Feature | `hermes backup` | `hermes profile export` |
| :--- | :--- | :--- |
| **Use Case** | **Full machine migration** | **Porting/sharing a specific profile** |
| **Scope** | Global (entire `~/.hermes` directory) | Local (single profile directory) |
| **Includes** | All profiles, global config, API keys, sessions | Single profile: SOUL.md, memories, sessions, skills |
| **Credentials** | **Included** (`.env` and `auth.json`) | **Excluded** (stripped for safe sharing) |
| **Format** | `.zip` | `.tar.gz` |

**Manual fallback (rsync):** Якщо ти віддаєш перевагу копіюванню файлів безпосередньо, виключи репозиторій коду:
```bash
rsync -av --exclude='hermes-agent' ~/.hermes/ newmachine:~/.hermes/
```

:::tip
`hermes backup` створює консистентний знімок навіть під час активної роботи Hermes. Відновлений архів не містить машинних файлів виконання, таких як `gateway.pid` і `cron.pid`.
:::

### Permission denied при перезавантаженні shell після інсталяції

**Сценарій:** Після запуску інсталятору Hermes команда `source ~/.zshrc` повертає помилку «permission denied».

**Причина:** Зазвичай це трапляється, коли у `~/.zshrc` (або `~/.bashrc`) неправильні права доступу, або інсталятор не зміг записати файл коректно. Це не проблема Hermes, а проблема прав доступу до конфігурації shell.

**Рішення:**
```bash
# Check permissions
ls -la ~/.zshrc

# Fix if needed (should be -rw-r--r-- or 644)
chmod 644 ~/.zshrc

# Then reload
source ~/.zshrc

# Or just open a new terminal window — it picks up PATH changes automatically
```

Якщо інсталятор додав рядок PATH, але права неправильні, можеш додати його вручну:
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

### Error 400 при першому запуску агента

**Сценарій:** Налаштування пройшли успішно, але перша спроба чату завершується HTTP 400.

**Причина:** Зазвичай це невідповідність назви моделі — вказана модель не існує у провайдера, або API‑ключ не має до неї доступу.

**Рішення:**
```bash
# Check what model and provider are configured
hermes config show | head -20

# Re-run model selection
hermes model

# Or test with a known-good model
hermes chat -q "hello" --model anthropic/claude-opus-4.7
```

Якщо ти користуєшся OpenRouter, переконайся, що у твого API‑ключа є кредити. 400‑ка від OpenRouter часто означає, що модель потребує платного плану або в ідентифікаторі моделі є помилка.
## Still Stuck?

Якщо твою проблему тут не розглянуто:

1. **Пошукай існуючі питання:** [GitHub Issues](https://github.com/NousResearch/hermes-agent/issues)
2. **Запитай у спільноти:** [Nous Research Discord](https://discord.gg/nousresearch)
3. **Подай звіт про помилку:** вкажи свою ОС, версію Python (`python3 --version`), версію Hermes (`hermes --version`) та повне повідомлення про помилку