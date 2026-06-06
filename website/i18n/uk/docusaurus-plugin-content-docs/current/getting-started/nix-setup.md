---
sidebar_position: 3
title: "Налаштування Nix та NixOS"
description: "Встанови та розгорни Hermes Agent за допомогою Nix — від швидкого `nix run` до повністю декларативного модуля NixOS у режимі контейнера"
---

# Налаштування Nix і NixOS

Hermes Agent постачається з Nix‑flake, що має три рівні інтеграції:

| Level | Who it's for | What you get |
|-------|-------------|--------------|
| **`nix run` / `nix profile install`** | Будь‑який користувач Nix (macOS, Linux) | Попередньо зібраний бінарник зі всіма залежностями — далі використовуй стандартний CLI‑workflow |
| **NixOS module (native)** | Деплойменти серверів NixOS | Декларативна конфігурація, жорстко налаштована systemd‑служба, керовані секрети |
| **NixOS module (container)** | Агентам, яким потрібна самонавчальна модифікація | Все вищезазначене, плюс постійний контейнер Ubuntu, у якому агент може виконувати `apt`/`pip`/`npm install` |

:::info What’s different from the standard install
Інсталятор `curl | bash` сам керує Python, Node та їхніми залежностями. Nix‑flake замінює все це — кожна Python‑залежність є Nix‑деривацією, зібраною за допомогою [uv2nix](https://github.com/pyproject-nix/uv2nix), а інструменти виконання (Node.js, git, ripgrep, ffmpeg) включені у PATH бінарника. Немає runtime‑pip, немає активації venv, немає `npm install`.

**Для користувачів, які не користуються NixOS**, це лише змінює крок інсталяції. Все, що йде після (`hermes setup`, `hermes gateway install`, редагування конфігурації), працює так само, як і при стандартній інсталяції.

**Для користувачів NixOS‑модуля** весь життєвий цикл інший: конфігурація живе у `configuration.nix`, секрети проходять через sops-nix/agenix, служба — це unit systemd, а команди CLI‑конфігурації блокуються. Ти керуєш Hermes Agent так само, як будь‑якою іншою службою NixOS.
:::
## Вимоги

- **Nix з увімкненими flakes** — рекомендовано [Determinate Nix](https://install.determinate.systems) (за замовчуванням flakes увімкнено)
- **API‑ключі** для сервісів, якими ти плануєш користуватися (принаймні: ключ OpenRouter або Anthropic)
## Quick Start (будь‑який користувач Nix)

Не потрібно клонувати репозиторій. Nix завантажує, збирає та запускає все:

```bash
# Run directly (builds on first use, cached after)
nix run github:NousResearch/hermes-agent -- setup
nix run github:NousResearch/hermes-agent -- chat

# Or install persistently
nix profile install github:NousResearch/hermes-agent
hermes setup
hermes chat
```

Після `nix profile install` у твоєму `PATH` з’являться `hermes`, `hermes-agent` і `hermes-acp`. Далі процес роботи ідентичний [стандартному встановленню](./installation.md) — `hermes setup` проведе тебе через вибір провайдера, `hermes gateway install` налаштує службу launchd (macOS) або користувацьку службу systemd, а конфігурація зберігається в `~/.hermes/`.

:::warning Платформи обміну повідомленнями (Discord, Telegram, Slack)
Пакет за замовчуванням не містить бібліотек платформ обміну повідомленнями — їх перенесено до встановлення за запитом, що не працює в середовищі Nix лише для читання. Якщо плануєш підключати агент до Discord, Telegram або Slack, встанови варіант `messaging`:

```bash
nix profile install github:NousResearch/hermes-agent#messaging
```

Для всіх додаткових опцій (голос, усі провайдери, усі платформи):

```bash
nix profile install github:NousResearch/hermes-agent#full
```

Варіант `full` додає до замикання приблизно 700 МБ. Якщо потрібні лише платформи обміну повідомленнями, `#messaging` додає лише ~33 МБ.
:::

<details>
<summary><strong>Збірка з локального клонування</strong></summary>

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
nix build
./result/bin/hermes setup
```

</details>

---
## NixOS Module

Flake експортує `nixosModules.default` — повний модуль сервісу NixOS, який декларативно керує створенням користувачів, каталогами, генерацією конфігурації, секретами, документами та життєвим циклом сервісу.

:::note
Цей модуль вимагає NixOS. Для систем, які не є NixOS (macOS, інші дистрибутиви Linux), використай `nix profile install` та стандартний CLI‑workflow, описаний вище.
:::

### Add the Flake Input

```nix
# /etc/nixos/flake.nix (or your system flake)
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    hermes-agent.url = "github:NousResearch/hermes-agent";
  };

  outputs = { nixpkgs, hermes-agent, ... }: {
    nixosConfigurations.your-host = nixpkgs.lib.nixosSystem {
      system = "x86_64-linux";
      modules = [
        hermes-agent.nixosModules.default
        ./configuration.nix
      ];
    };
  };
}
```

### Minimal Configuration

```nix
# configuration.nix
{ config, ... }: {
  services.hermes-agent = {
    enable = true;
    settings.model.default = "anthropic/claude-sonnet-4";
    environmentFiles = [ config.sops.secrets."hermes-env".path ];
    addToSystemPackages = true;
  };
}
```

Ось і все. `nixos-rebuild switch` створює користувача `hermes`, генерує `config.yaml`, підключає секрети та запускає шлюз — довготривалий сервіс, який з’єднує агента з платформами обміну повідомленнями (Telegram, Discord тощо) і слухає вхідні повідомлення.

:::warning Secrets are required
Рядок `environmentFiles`, наведений вище, передбачає, що у вас налаштовано [sops-nix](https://github.com/Mic92/sops-nix) або [agenix](https://github.com/ryantm/agenix). Файл має містити принаймні один ключ провайдера LLM (наприклад, `OPENROUTER_API_KEY=sk-or-...`). Дивись розділ [Secrets Management](#secrets-management) для повної інструкції. Якщо у вас ще немає менеджера секретів, можна використати простий файл як стартову точку — лише переконайся, що він не доступний для читання всім:

```bash
echo "OPENROUTER_API_KEY=sk-or-your-key" | sudo install -m 0600 -o hermes /dev/stdin /var/lib/hermes/env
```

```nix
services.hermes-agent.environmentFiles = [ "/var/lib/hermes/env" ];
```
:::

:::tip addToSystemPackages
Встановлення `addToSystemPackages = true` робить два: додає CLI `hermes` у системний PATH **і** встановлює `HERMES_HOME` глобально, щоб інтерактивний CLI ділився станом (сесії, інструменти, cron) з сервісом шлюзу. Без цього запуск `hermes` у твоїй оболонці створює окремий каталог `~/.hermes/`.
:::

### Container-aware CLI

:::info
Коли `container.enable = true` і `addToSystemPackages = true`, **кожна** команда `hermes` на хості автоматично маршрутизується у керований контейнер. Це означає, що твоя інтерактивна CLI‑сесія працює в тому ж середовищі, що й сервіс шлюзу — з доступом до всіх пакетів і інструментів, встановлених у контейнері.

- Маршрутизація прозора: `hermes chat`, `hermes sessions list`, `hermes version` тощо виконуються всередині контейнера
- Усі прапорці CLI передаються без змін
- Якщо контейнер не запущений, CLI кілька разів повторює спробу (5 с з індикатором для інтерактивного використання, 10 с без індикатора для скриптів), після чого завершується з чіткою помилкою — без тихого запасного варіанту
- Для розробників, які працюють над кодом hermes, встанови `HERMES_DEV=1`, щоб обійти маршрутизацію в контейнер і запустити локальну копію безпосередньо

Встанови `container.hostUsers`, щоб створити символічне посилання `~/.hermes` на каталог стану сервісу, так що CLI на хості і контейнер ділять сесії, конфіг та пам’ять:

```nix
services.hermes-agent = {
  container.enable = true;
  container.hostUsers = [ "your-username" ];
  addToSystemPackages = true;
};
```

Користувачі, зазначені в `hostUsers`, автоматично додаються до групи `hermes` для доступу до файлів.

**Podman‑користувачі:** Сервіс NixOS запускає контейнер від імені root. Користувачі Docker отримують доступ через сокет групи `docker`, але у Podman‑контейнерів, що працюють у режимі rootful, потрібен sudo. Надій права без пароля для вашого runtime контейнера:

```nix
security.sudo.extraRules = [{
  users = [ "your-username" ];
  commands = [{
    command = "/run/current-system/sw/bin/podman";
    options = [ "NOPASSWD" ];
  }];
}];
```

CLI автоматично визначає, коли потрібен sudo, і використовує його прозоро. Без цього доведеться вручну запускати `sudo hermes chat`.
:::

### Verify It Works

Після `nixos-rebuild switch` перевір, що сервіс працює:

```bash
# Check service status
systemctl status hermes-agent

# Watch logs (Ctrl+C to stop)
journalctl -u hermes-agent -f

# If addToSystemPackages is true, test the CLI
hermes version
hermes config       # shows the generated config
```

### Choosing a Deployment Mode

Модуль підтримує два режими, керовані параметром `container.enable`:

| | **Native** (за замовчуванням) | **Container** |
|---|---|---|
| Як запускається | Захищений systemd‑сервіс на хості | Постійний контейнер Ubuntu з прив’язкою `/nix/store` |
| Безпека | `NoNewPrivileges`, `ProtectSystem=strict`, `PrivateTmp` | Ізоляція контейнера, працює як непривілейований користувач всередині |
| Агент може самостійно встановлювати пакети | Ні — лише інструменти, доступні у PATH Nix | Так — встановлення `apt`, `pip`, `npm` зберігаються між перезапусками |
| Поверхня конфігурації | Та сама | Та сама |
| Коли обирати | Стандартні розгортання, максимальна безпека, відтворюваність | Агент потребує встановлення пакетів під час роботи, змінне середовище, експериментальні інструменти |

Щоб увімкнути режим контейнера, додай один рядок:

```nix
{
  services.hermes-agent = {
    enable = true;
    container.enable = true;
    # ... rest of config is identical
  };
}
```

:::info
Режим контейнера автоматично вмикає `virtualisation.docker.enable` через `mkDefault`. Якщо ти використовуєш Podman, встанови `container.backend = "podman"` і `virtualisation.docker.enable = false`.
:::

---
## Конфігурація

### Декларативні налаштування

Опція `settings` приймає довільний **attrset**, який рендериться як `config.yaml`. Вона підтримує глибоке злиття між кількома визначеннями модулів (за допомогою `lib.recursiveUpdate`), тому ти можеш розбити конфігурацію на файли:

```nix
# base.nix
services.hermes-agent.settings = {
  model.default = "anthropic/claude-sonnet-4";
  toolsets = [ "all" ];
  terminal = { backend = "local"; timeout = 180; };
};

# personality.nix
services.hermes-agent.settings = {
  display = { compact = false; personality = "kawaii"; };
  memory = { memory_enabled = true; user_profile_enabled = true; };
};
```

Обидва набори глибоко зливаються під час оцінки. Ключі, оголошені в Nix, завжди переважають над ключами у вже існуючому `config.yaml` на диску, але **додані користувачем ключі, які Nix не змінює, зберігаються**. Це означає, що якщо агент або ручне редагування додає ключі типу `skills.disabled` або `streaming.enabled`, вони залишаються після `nixos-rebuild switch`.

:::note Іменування моделей
`settings.model.default` використовує ідентифікатор моделі, який очікує твій провайдер. У [OpenRouter](https://openrouter.ai) (за замовчуванням) вони виглядають так: `"anthropic/claude-sonnet-4"` або `"google/gemini-3-flash"`. Якщо ти використовуєш провайдера безпосередньо (Anthropic, OpenAI), встанови `settings.model.base_url`, щоб вказати їх API, і використай їхні власні ідентифікатори моделей (наприклад, `"claude-sonnet-4-20250514"`). Коли `base_url` не задано, Hermes за замовчуванням використовує OpenRouter.
:::

:::tip Як знайти доступні ключі конфігурації
Запусти `nix build .#configKeys && cat result`, щоб побачити кожен листовий ключ конфігурації, витягнутий з `DEFAULT_CONFIG` у Python. Ти можеш вставити свій існуючий `config.yaml` у атрибутний набір `settings` — структура відповідає 1:1.
:::

<details>
<summary><strong>Повний приклад: усі часто налаштовані параметри</strong></summary>

```nix
{ config, ... }: {
  services.hermes-agent = {
    enable = true;
    container.enable = true;

    # ── Model ──────────────────────────────────────────────────────────
    settings = {
      model = {
        base_url = "https://openrouter.ai/api/v1";
        default = "anthropic/claude-opus-4.6";
      };
      toolsets = [ "all" ];
      max_turns = 100;
      terminal = { backend = "local"; cwd = "."; timeout = 180; };
      compression = {
        enabled = true;
        threshold = 0.85;
        summary_model = "google/gemini-3-flash-preview";
      };
      memory = { memory_enabled = true; user_profile_enabled = true; };
      display = { compact = false; personality = "kawaii"; };
      agent = { max_turns = 60; verbose = false; };
    };

    # ── Secrets ────────────────────────────────────────────────────────
    environmentFiles = [ config.sops.secrets."hermes-env".path ];

    # ── Documents ──────────────────────────────────────────────────────
    documents = {
      "USER.md" = ./documents/USER.md;
    };

    # ── MCP Servers ────────────────────────────────────────────────────
    mcpServers.filesystem = {
      command = "npx";
      args = [ "-y" "@modelcontextprotocol/server-filesystem" "/data/workspace" ];
    };

    # ── Container options ──────────────────────────────────────────────
    container = {
      image = "ubuntu:24.04";
      backend = "docker";
      hostUsers = [ "your-username" ];
      extraVolumes = [ "/home/user/projects:/projects:rw" ];
      extraOptions = [ "--gpus" "all" ];
    };

    # ── Service tuning ─────────────────────────────────────────────────
    addToSystemPackages = true;
    extraArgs = [ "--verbose" ];
    restart = "always";
    restartSec = 5;
  };
}
```

</details>

### Escape Hatch: Bring Your Own Config

Якщо ти хочеш керувати `config.yaml` повністю поза Nix, використай `configFile`:

```nix
services.hermes-agent.configFile = /etc/hermes/config.yaml;
```

Це повністю обходить `settings` — без злиття, без генерації. Файл копіюється «як є» до `$HERMES_HOME/config.yaml` під час кожної активації.

### Шпаргалка налаштувань

Швидка довідка щодо найпоширеніших речей, які користувачі Nix хочуть налаштувати:

| Я хочу... | Опція | Приклад |
|---|---|---|
| Змінити модель LLM | `settings.model.default` | `"anthropic/claude-sonnet-4"` |
| Використати інший endpoint провайдера | `settings.model.base_url` | `"https://openrouter.ai/api/v1"` |
| Додати API‑ключі | `environmentFiles` | `[ config.sops.secrets."hermes-env".path ]` |
| Надати агенту особистість | `${services.hermes-agent.stateDir}/.hermes/SOUL.md` | керувати файлом безпосередньо |
| Додати сервери інструментів MCP | `mcpServers.<name>` | Див. [MCP Servers](#mcp-servers) |
| Увімкнути Discord/Telegram/Slack | `extraDependencyGroups` | `[ "messaging" ]` |
| Підключити директорії хоста до контейнера | `container.extraVolumes` | `[ "/data:/data:rw" ]` |
| Надати контейнеру доступ до GPU | `container.extraOptions` | `[ "--gpus" "all" ]` |
| Використати Podman замість Docker | `container.backend` | `"podman"` |
| Поділитися станом між CLI хоста та контейнером | `container.hostUsers` | `[ "sidbin" ]` |
| Додати додаткові інструменти для агента | `extraPackages` | `[ pkgs.pandoc pkgs.imagemagick ]` |
| Використати власний базовий образ | `container.image` | `"ubuntu:24.04"` |
| Перезаписати пакет hermes | `package` | `inputs.hermes-agent.packages.${system}.default.override { ... }` |
| Змінити директорію стану | `stateDir` | `"/opt/hermes"` |
| Встановити робочу директорію агента | `workingDirectory` | `"/home/user/projects"` |

---
## Управління секретами

:::danger Ніколи не розміщуй API‑ключі у `settings` або `environment`
Значення у виразах Nix потрапляють у `/nix/store`, який доступний для читання всім. Завжди використовуйте `environmentFiles` разом із менеджером секретів.
:::

Як `environment` (незасекречені змінні), так і `environmentFiles` (файли секретів) об’єднуються у `$HERMES_HOME/.env` під час активації (`nixos-rebuild switch`). Hermes читає цей файл при кожному запуску, тому зміни набувають чинності після `systemctl restart hermes-agent` — без потреби у повторному створенні контейнера.

### sops-nix

```nix
{
  sops = {
    defaultSopsFile = ./secrets/hermes.yaml;
    age.keyFile = "/home/user/.config/sops/age/keys.txt";
    secrets."hermes-env" = { format = "yaml"; };
  };

  services.hermes-agent.environmentFiles = [
    config.sops.secrets."hermes-env".path
  ];
}
```

Файл секретів містить пари «ключ‑значення»:

```yaml
# secrets/hermes.yaml (encrypted with sops)
hermes-env: |
    OPENROUTER_API_KEY=sk-or-...
    TELEGRAM_BOT_TOKEN=123456:ABC...
    ANTHROPIC_API_KEY=sk-ant-...
```

### agenix

```nix
{
  age.secrets.hermes-env.file = ./secrets/hermes-env.age;

  services.hermes-agent.environmentFiles = [
    config.age.secrets.hermes-env.path
  ];
}
```

### OAuth / Auth Seeding

Для платформ, які вимагають OAuth (наприклад, Discord), використовуйте `authFile` для заповнення облікових даних під час першого розгортання:

```nix
{
  services.hermes-agent = {
    authFile = config.sops.secrets."hermes/auth.json".path;
    # authFileForceOverwrite = true;  # overwrite on every activation
  };
}
```

Файл копіюється лише якщо `auth.json` ще не існує (за винятком випадку, коли `authFileForceOverwrite = true`). Оновлення токенів OAuth під час виконання записуються у каталог стану та зберігаються між перебудовами.
## Документи

Опція `documents` встановлює файли у робочий каталог агента ( `workingDirectory`, який агент читає як свою робочу область). Hermes шукає певні імена файлів за конвенцією:

- **`USER.md`** — контекст про користувача, з яким взаємодіє агент.
- Будь‑які інші файли, які ти розміщуєш тут, будуть видимі агенту як файли робочої області.

Файл ідентифікації агента окремий: Hermes завантажує свій основний `SOUL.md` з `$HERMES_HOME/SOUL.md`, який у модулі NixOS знаходиться за шляхом `${services.hermes-agent.stateDir}/.hermes/SOUL.md`. Розміщення `SOUL.md` у `documents` лише створює файл робочої області і не замінить головний файл персонажа.

```nix
{
  services.hermes-agent.documents = {
    "USER.md" = ./documents/USER.md;  # path reference, copied from Nix store
  };
}
```

Значення можуть бути рядками в інлайн‑форматі або посиланнями на шляхи. Файли встановлюються при кожному `nixos-rebuild switch`.
## MCP Servers

Опція `mcpServers` декларативно налаштовує сервери [MCP (Model Context Protocol)](https://modelcontextprotocol.io). Кожен сервер використовує транспорт **stdio** (локальна команда) або **HTTP** (віддалений URL).

### Stdio Transport (Local Servers)

```nix
{
  services.hermes-agent.mcpServers = {
    filesystem = {
      command = "npx";
      args = [ "-y" "@modelcontextprotocol/server-filesystem" "/data/workspace" ];
    };
    github = {
      command = "npx";
      args = [ "-y" "@modelcontextprotocol/server-github" ];
      env.GITHUB_PERSONAL_ACCESS_TOKEN = "\${GITHUB_TOKEN}"; # resolved from .env
    };
  };
}
```

:::tip
Змінні середовища у значеннях `env` розв’язуються з `$HERMES_HOME/.env` під час виконання. Використовуй `environmentFiles` для ін’єкції секретів — ніколи не розміщуй токени безпосередньо у Nix‑конфігурації.
:::

### HTTP Transport (Remote Servers)

```nix
{
  services.hermes-agent.mcpServers.remote-api = {
    url = "https://mcp.example.com/v1/mcp";
    headers.Authorization = "Bearer \${MCP_REMOTE_API_KEY}";
    timeout = 180;
  };
}
```

### HTTP Transport with OAuth

Встанови `auth = "oauth"` для серверів, які використовують OAuth 2.1. Hermes реалізує повний PKCE‑потік — виявлення метаданих, динамічну реєстрацію клієнта, обмін токенами та автоматичне оновлення.

```nix
{
  services.hermes-agent.mcpServers.my-oauth-server = {
    url = "https://mcp.example.com/mcp";
    auth = "oauth";
  };
}
```

Токени зберігаються у `$HERMES_HOME/mcp-tokens/<server-name>.json` і залишаються між перезапусками та перебудовами.

<details>
<summary><strong>Initial OAuth authorization on headless servers</strong></summary>

Перша OAuth‑авторизація вимагає браузерного процесу згоди. У безголовому розгортанні Hermes виводить URL авторизації у stdout/логи замість відкриття браузера.

**Option A: Interactive bootstrap** — запусти процес один раз через `docker exec` (контейнер) або `sudo -u hermes` (нативно):

```bash
# Container mode
docker exec -it hermes-agent \
  hermes mcp add my-oauth-server --url https://mcp.example.com/mcp --auth oauth

# Native mode
sudo -u hermes HERMES_HOME=/var/lib/hermes/.hermes \
  hermes mcp add my-oauth-server --url https://mcp.example.com/mcp --auth oauth
```

Контейнер використовує `--network=host`, тому слухач OAuth‑callback на `127.0.0.1` доступний з браузера хоста.

**Option B: Pre-seed tokens** — завершити процес на робочій станції, потім скопіювати токени:

```bash
hermes mcp add my-oauth-server --url https://mcp.example.com/mcp --auth oauth
scp ~/.hermes/mcp-tokens/my-oauth-server{,.client}.json \
    server:/var/lib/hermes/.hermes/mcp-tokens/
# Ensure: chown hermes:hermes, chmod 0600
```

</details>

### Sampling (Server-Initiated LLM Requests)

Деякі сервери MCP можуть ініціювати запити LLM від агента:

```nix
{
  services.hermes-agent.mcpServers.analysis = {
    command = "npx";
    args = [ "-y" "analysis-server" ];
    sampling = {
      enabled = true;
      model = "google/gemini-3-flash";
      max_tokens_cap = 4096;
      timeout = 30;
      max_rpm = 10;
    };
  };
}
```

---
## Managed Mode

Коли hermes запускається через модуль NixOS, наступні CLI‑команди **заблоковані** з описовою помилкою, що вказує на `configuration.nix`:

| Заблокована команда | Чому |
|---|---|
| `hermes setup` | Конфігурація декларативна — відредагуй `settings` у своєму Nix‑конфігу |
| `hermes config edit` | Конфігурація генерується з `settings` |
| `hermes config set <key> <value>` | Конфігурація генерується з `settings` |
| `hermes gateway install` | Служба systemd керується NixOS |
| `hermes gateway uninstall` | Служба systemd керується NixOS |

Це запобігає відхиленням між тим, що оголошує Nix, і тим, що знаходиться на диску. Виявлення здійснюється за допомогою двох сигналів:

1. **`HERMES_MANAGED=true`** — змінна середовища, встановлюється службою systemd, видима процесу шлюзу
2. **`.managed`** — файл‑маркер у `HERMES_HOME`, створюється скриптом активації, видимий у інтерактивних оболонках (наприклад, `docker exec -it hermes-agent hermes config set ...` також заблоковано)

Щоб змінити конфігурацію, відредагуй свій Nix‑конфіг і запусти `sudo nixos-rebuild switch`.
## Архітектура контейнера

:::info
Цей розділ актуальний лише якщо ти використовуєш `container.enable = true`. Пропусти його для розгортань у native‑режимі.
:::

Коли режим контейнера увімкнено, hermes працює всередині постійного Ubuntu‑контейнера, а бінарник, зібраний Nix, прив’язується лише для читання з хоста:

```
Host                                    Container
────                                    ─────────
/nix/store/...-hermes-agent-0.1.0  ──►  /nix/store/... (ro)
~/.hermes -> /var/lib/hermes/.hermes       (symlink bridge, per hostUsers)
/var/lib/hermes/                    ──►  /data/          (rw)
  ├── current-package -> /nix/store/...    (symlink, updated each rebuild)
  ├── .gc-root -> /nix/store/...           (prevents nix-collect-garbage)
  ├── .container-identity                  (sha256 hash, triggers recreation)
  ├── .hermes/                             (HERMES_HOME)
  │   ├── .env                             (merged from environment + environmentFiles)
  │   ├── config.yaml                      (Nix-generated, deep-merged by activation)
  │   ├── .managed                         (marker file)
  │   ├── .container-mode                  (routing metadata: backend, exec_user, etc.)
  │   ├── state.db, sessions/, memories/   (runtime state)
  │   └── mcp-tokens/                      (OAuth tokens for MCP servers)
  ├── home/                                ──►  /home/hermes    (rw)
  └── workspace/                           (MESSAGING_CWD)
      ├── SOUL.md                          (from documents option)
      └── (agent-created files)

Container writable layer (apt/pip/npm):   /usr, /usr/local, /tmp
```

Бінарник, зібраний Nix, працює в Ubuntu‑контейнері, бо `/nix/store` прив’язується як bind‑mount — він містить власний інтерпретатор і всі залежності, тому не покладається на системні бібліотеки контейнера. Точка входу контейнера розв’язується через symlink `current-package`: `/data/current-package/bin/hermes gateway run --replace`. При `nixos-rebuild switch` оновлюється лише symlink — контейнер продовжує працювати.

### Що зберігається, а що ні

| Подія | Перезапускається контейнер? | `/data` (стан) | `/home/hermes` | Шар запису (`apt`/`pip`/`npm`) |
|---|---|---|---|---|
| `systemctl restart hermes-agent` | Ні | Залишається | Залишається | Залишається |
| `nixos-rebuild switch` (зміна коду) | Ні (оновлено symlink) | Залишається | Залишається | Залишається |
| Перезавантаження хоста | Ні | Залишається | Залишається | Залишається |
| `nix-collect-garbage` | Ні (GC‑root) | Залишається | Залишається | Залишається |
| Зміна образу (`container.image`) | **Так** | Залишається | Залишається | **Втрачається** |
| Зміна томів/опцій | **Так** | Залишається | Залишається | **Втрачається** |
| Зміна `environment`/`environmentFiles` | Ні | Залишається | Залишається | Залишається |

Контейнер перезапускається лише коли змінюється його **хеш ідентичності**. Хеш охоплює: версію схеми, образ, `extraVolumes`, `extraOptions` та скрипт точки входу. Зміни змінних середовища, налаштувань, документів або самого пакету hermes **не** викликають перезапуск.

:::warning Втрата шару запису
Коли хеш ідентичності змінюється (оновлення образу, нові томи, нові опції контейнера), контейнер знищується і створюється заново з чистого `container.image`. Будь‑які пакети, встановлені через `apt install`, `pip install` або `npm install` у шарі запису, втрачаються. Стан у `/data` та `/home/hermes` зберігається (це bind‑mounts).

Якщо агент залежить від конкретних пакетів, розглянь їх включення у власний образ (`container.image = "my-registry/hermes-base:latest"`) або скриптуй їх встановлення у `SOUL.md` агента.
:::

### Захист GC‑кореня

Скрипт `preStart` створює GC‑корінь у `${stateDir}/.gc-root`, який вказує на поточний пакет hermes. Це запобігає видаленню запущеного бінарника під час `nix-collect-garbage`. Якщо GC‑корінь якимось чином зламається, перезапуск сервісу відновить його.

---
## Плагіни

Модуль NixOS підтримує декларативну установку плагінів — без необхідності імперативного `hermes plugins install`.

### Плагіни‑каталоги (`extraPlugins`)

Для плагінів, які є просто деревом джерел з `plugin.yaml` + `__init__.py` (наприклад, [hermes‑lcm](https://github.com/stephenschoettler/hermes-lcm)):

```nix
services.hermes-agent.extraPlugins = [
  (pkgs.fetchFromGitHub {
    owner = "stephenschoettler";
    repo = "hermes-lcm";
    rev = "v0.7.0";
    hash = "sha256-...";
  })
];
```

Плагіни створюються як символічні посилання у `$HERMES_HOME/plugins/` під час активації. Hermes виявляє їх під час звичайного сканування каталогу. Видалення плагіна зі списку та запуск `nixos-rebuild switch` видаляє символічне посилання.

### Плагіни‑точки входу (`extraPythonPackages`)

Для pip‑пакетованих плагінів, які реєструються через `[project.entry-points."hermes_agent.plugins"]` (наприклад, [rtk‑hermes](https://github.com/ogallotti/rtk-hermes)):

```nix
services.hermes-agent.extraPythonPackages = [
  (pkgs.python312Packages.buildPythonPackage {
    pname = "rtk-hermes";
    version = "1.0.0";
    src = pkgs.fetchFromGitHub {
      owner = "ogallotti";
      repo = "rtk-hermes";
      rev = "v1.0.0";
      hash = "sha256-...";
    };
    format = "pyproject";
    build-system = [ pkgs.python312Packages.setuptools ];
  })
];
```

`site-packages` пакету додається до PYTHONPATH у обгортці hermes. `importlib.metadata` виявляє точку входу під час запуску сесії.

### Групи необов’язкових залежностей (`extraDependencyGroups`)

Для необов’язкових extras, оголошених у `pyproject.toml` hermes‑agent, використовуйте `extraDependencyGroups`, щоб включити їх у запечатане venv під час збірки. Це потрібно для будь‑якого extras, який не входить до набору `[all]` за замовчуванням — у Nix встановлення під час виконання у лише‑для‑читання сховищі неможливе.

```nix
# Enable Discord, Telegram, Slack
services.hermes-agent.extraDependencyGroups = [ "messaging" ];
```

```nix
# Enable a memory provider
services.hermes-agent = {
  extraDependencyGroups = [ "hindsight" ];
  settings.memory.provider = "hindsight";
};
```

Це вирішується uv разом з ядровими залежностями — без патчування PYTHONPATH, без ризику колізій. Доступні групи:

| Group | What it enables |
|-------|-----------------|
| `messaging` | Discord, Telegram, Slack |
| `matrix` | Matrix/Element (mautrix with encryption; Linux only) |
| `dingtalk` | DingTalk |
| `feishu` | Feishu/Lark |
| `voice` | Local speech-to-text (faster-whisper) |
| `edge-tts` | Edge TTS provider |
| `tts-premium` | ElevenLabs TTS |
| `anthropic` | Native Anthropic SDK (not needed via OpenRouter) |
| `bedrock` | AWS Bedrock (boto3) |
| `azure-identity` | Azure Entra ID auth |
| `honcho` | Honcho memory provider |
| `hindsight` | Hindsight memory provider |
| `modal` | Modal terminal backend |
| `daytona` | Daytona terminal backend |
| `exa` | Exa web search |
| `firecrawl` | Firecrawl web search |
| `fal` | FAL image generation |

Або використай готові flake‑пакети `#messaging` або `#full` замість конфігурації кожного extras (див. [Quick Start](#quick-start-any-nix-user)).

**Коли що використовувати:**

| Need | Option |
|------|--------|
| Увімкнути необов’язковий extra у `pyproject.toml` | `extraDependencyGroups` |
| Додати зовнішній Python‑плагін, якого немає у `pyproject.toml` | `extraPythonPackages` |
| Додати системний бінарник (pandoc, jq тощо) | `extraPackages` |
| Додати плагін‑каталог з джерельним деревом | `extraPlugins` |

### Поєднання обох

Плагін‑каталог із сторонніми Python‑залежностями потребує обох варіантів:

```nix
services.hermes-agent = {
  extraPlugins = [ my-plugin-src ];          # plugin source
  extraPythonPackages = [ pkgs.python312Packages.redis ];  # its Python dep
  extraPackages = [ pkgs.redis ];            # system binary it needs
};
```

### Використання оверлею

Зовнішні flakes можуть безпосередньо перевизначити пакет:

```nix
{
  inputs.hermes-agent.url = "github:NousResearch/hermes-agent";
  outputs = { hermes-agent, nixpkgs, ... }: {
    nixpkgs.overlays = [ hermes-agent.overlays.default ];
    # Then:
    #   pkgs.hermes-agent.override { extraPythonPackages = [...]; }
    #   pkgs.hermes-agent.override { extraDependencyGroups = [ "hindsight" ]; }
  };
}
```

### Конфігурація плагінів

Плагіни все ще потрібно ввімкнути у `config.yaml`. Додай їх через декларативні налаштування:

```nix
services.hermes-agent.settings.plugins.enabled = [
  "hermes-lcm"
  "rtk-rewrite"
];
```

:::note
Перевірка колізій під час збірки запобігає тому, щоб пакети плагінів перекривали ядрові залежності hermes. Якщо плагін надає пакет, який вже є у запечатаному venv, `nixos-rebuild` завершується з чіткою помилкою.
:::
## Development

### Dev Shell

Flake надає shell розробки з Python 3.12, uv, Node.js та усіма інструментами середовища виконання:

```bash
cd hermes-agent
nix develop

# Shell provides:
#   - Python 3.12 + uv (deps installed into .venv on first entry)
#   - Node.js 22, ripgrep, git, openssh, ffmpeg on PATH
#   - Stamp-file optimization: re-entry is near-instant if deps haven't changed

hermes setup
hermes chat
```

### direnv (Recommended)

Включений файл `.envrc` автоматично активує shell розробки:

```bash
cd hermes-agent
direnv allow    # one-time
# Subsequent entries are near-instant (stamp file skips dep install)
```

### Flake Checks

Flake включає перевірку під час збірки, яка виконується в CI та локально:

```bash
# Run all checks
nix flake check

# Individual checks
nix build .#checks.x86_64-linux.package-contents   # binaries exist + version
nix build .#checks.x86_64-linux.entry-points-sync  # pyproject.toml ↔ Nix package sync
nix build .#checks.x86_64-linux.cli-commands        # gateway/config subcommands
nix build .#checks.x86_64-linux.managed-guard       # HERMES_MANAGED blocks mutation
nix build .#checks.x86_64-linux.bundled-skills      # skills present in package
nix build .#checks.x86_64-linux.config-roundtrip    # merge script preserves user keys
```

<details>
<summary><strong>Що перевіряє кожна перевірка</strong></summary>

| Check | Що тестується |
|---|---|
| `package-contents` | Бінарні файли `hermes` і `hermes-agent` існують, і команда `hermes version` виконується |
| `entry-points-sync` | Кожен запис `[project.scripts]` у `pyproject.toml` має обгорнутий бінарний файл у пакеті Nix |
| `cli-commands` | `hermes --help` показує підкоманди `gateway` і `config` |
| `managed-guard` | `HERMES_MANAGED=true hermes config set ...` виводить помилку NixOS |
| `bundled-skills` | Каталог `Skills` існує, містить файли `SKILL.md`, змінна `HERMES_BUNDLED_SKILLS` встановлена в обгортці |
| `config-roundtrip` | 7 сценаріїв злиття: чиста інсталяція, перевизначення Nix, збереження користувацького ключа, змішане злиття, адитивне злиття MCP, глибоке вкладене злиття, ідемпотентність |

</details>

---
## Довідник параметрів

### Core

| Параметр | Тип | За замовчуванням | Опис |
|---|---|---|---|
| `enable` | `bool` | `false` | Увімкнути службу hermes-agent |
| `package` | `package` | `hermes-agent` | Пакет hermes-agent, який використовується |
| `user` | `str` | `"hermes"` | Системний користувач |
| `group` | `str` | `"hermes"` | Системна група |
| `createUser` | `bool` | `true` | Автоматично створювати користувача/групу |
| `stateDir` | `str` | `"/var/lib/hermes"` | Директорія стану (батьківська для `HERMES_HOME`) |
| `workingDirectory` | `str` | `"${stateDir}/workspace"` | Робоча директорія агента (`MESSAGING_CWD`) |
| `addToSystemPackages` | `bool` | `false` | Додати CLI `hermes` до системного PATH і встановити `HERMES_HOME` глобально |

### Configuration

| Параметр | Тип | За замовчуванням | Опис |
|---|---|---|---|
| `settings` | `attrs` (deep-merged) | `{}` | Декларативна конфігурація, що генерується у `config.yaml`. Підтримує довільну вкладеність; кілька визначень об’єднуються за допомогою `lib.recursiveUpdate` |
| `configFile` | `null` або `path` | `null` | Шлях до існуючого `config.yaml`. При встановленні повністю замінює `settings` |

### Secrets & Environment

| Параметр | Тип | За замовчуванням | Опис |
|---|---|---|---|
| `environmentFiles` | `listOf str` | `[]` | Шляхи до файлів env з секретами. Об’єднуються у `$HERMES_HOME/.env` під час активації |
| `environment` | `attrsOf str` | `{}` | Не‑секретні змінні середовища. **Видимі у Nix‑store** — не розміщуй тут секрети |
| `authFile` | `null` або `path` | `null` | Насіння OAuth‑облікових даних. Копіюється лише під час першого розгортання |
| `authFileForceOverwrite` | `bool` | `false` | Завжди перезаписувати `auth.json` з `authFile` під час активації |

### Documents

| Параметр | Тип | За замовчуванням | Опис |
|---|---|---|---|
| `documents` | `attrsOf (either str path)` | `{}` | Файли робочого простору. Ключі — імена файлів, значення — рядки‑вбудовки або шляхи. Встановлюються у `workingDirectory` під час активації |

### MCP Servers

| Параметр | Тип | За замовчуванням | Опис |
|---|---|---|---|
| `mcpServers` | `attrsOf submodule` | `{}` | Визначення серверів MCP, об’єднані у `settings.mcp_servers` |
| `mcpServers.<name>.command` | `null` або `str` | `null` | Команда сервера (транспорт stdio) |
| `mcpServers.<name>.args` | `listOf str` | `[]` | Аргументи команди |
| `mcpServers.<name>.env` | `attrsOf str` | `{}` | Змінні середовища для процесу сервера |
| `mcpServers.<name>.url` | `null` або `str` | `null` | URL‑endpoint сервера (транспорт HTTP/StreamableHTTP) |
| `mcpServers.<name>.headers` | `attrsOf str` | `{}` | HTTP‑заголовки, напр. `Authorization` |
| `mcpServers.<name>.auth` | `null` або `"oauth"` | `null` | Метод автентифікації. `"oauth"` вмикає OAuth 2.1 PKCE |
| `mcpServers.<name>.enabled` | `bool` | `true` | Увімкнути або вимкнути цей сервер |
| `mcpServers.<name>.timeout` | `null` або `int` | `null` | Тайм‑аут виклику інструменту в секундах (за замовчуванням: 120) |
| `mcpServers.<name>.connect_timeout` | `null` або `int` | `null` | Тайм‑аут підключення в секундах (за замовчуванням: 60) |
| `mcpServers.<name>.tools` | `null` або `submodule` | `null` | Фільтрація інструментів (`include`/`exclude` списки) |
| `mcpServers.<name>.sampling` | `null` або `submodule` | `null` | Конфігурація семплювання для запитів LLM, ініційованих сервером |

### Service Behavior

| Параметр | Тип | За замовчуванням | Опис |
|---|---|---|---|
| `extraArgs` | `listOf str` | `[]` | Додаткові аргументи для `hermes gateway` |
| `extraPackages` | `listOf package` | `[]` | Додаткові пакети, доступні агенту. Додаються до профілю користувача hermes, тому їх бачать термінальні команди, skills та cron‑завдання |
| `extraPlugins` | `listOf package` | `[]` | Пакети плагінів‑директорій, які створюються символічними посиланнями у `$HERMES_HOME/plugins/`. Кожен має містити `plugin.yaml` |
| `extraPythonPackages` | `listOf package` | `[]` | Пакети Python, додані до PYTHONPATH для виявлення плагінів‑точок входу. Будуються за допомогою `python312Packages` |
| `extraDependencyGroups` | `listOf str` | `[]` | Додаткові extras у pyproject.toml, які включаються у запаковане venv (наприклад, `["hindsight"]`). Розв’язуються uv — без конфліктів |
| `restart` | `str` | `"always"` | Політика systemd `Restart=` |
| `restartSec` | `int` | `5` | Значення systemd `RestartSec=` |

### Container

| Параметр | Тип | За замовчуванням | Опис |
|---|---|---|---|
| `container.enable` | `bool` | `false` | Увімкнути режим OCI‑контейнера |
| `container.backend` | `enum ["docker" "podman"]` | `"docker"` | Середовище виконання контейнера |
| `container.image` | `str` | `"ubuntu:24.04"` | Базовий образ (завантажується під час виконання) |
| `container.extraVolumes` | `listOf str` | `[]` | Додаткові монтування томів (`host:container:mode`) |
| `container.extraOptions` | `listOf str` | `[]` | Додаткові аргументи, передані `docker create` |
| `container.hostUsers` | `listOf str` | `[]` | Інтерактивні користувачі, які отримують символічне посилання `~/.hermes` на директорію стану служби та автоматично додаються до групи `hermes` |
---
## Макет каталогів

### Режим Native

```
/var/lib/hermes/                     # stateDir (owned by hermes:hermes, 0750)
├── .hermes/                         # HERMES_HOME
│   ├── config.yaml                  # Nix-generated (deep-merged each rebuild)
│   ├── .managed                     # Marker: CLI config mutation blocked
│   ├── .env                         # Merged from environment + environmentFiles
│   ├── auth.json                    # OAuth credentials (seeded, then self-managed)
│   ├── gateway.pid
│   ├── state.db
│   ├── mcp-tokens/                  # OAuth tokens for MCP servers
│   ├── sessions/
│   ├── memories/
│   ├── skills/
│   ├── cron/
│   └── logs/
├── home/                            # Agent HOME
└── workspace/                       # MESSAGING_CWD
    ├── SOUL.md                      # From documents option
    └── (agent-created files)
```

### Режим Container

Той самий макет, змонтований у контейнер:

| Шлях у контейнері | Шлях на хості | Режим | Примітки |
|---|---|---|---|
| `/nix/store` | `/nix/store` | `ro` | Бінарний файл Hermes + всі залежності Nix |
| `/data` | `/var/lib/hermes` | `rw` | Увесь стан, конфігурація, робочий простір |
| `/home/hermes` | `${stateDir}/home` | `rw` | Постійна домашня директорія агента — `pip install --user`, кеші інструментів |
| `/usr`, `/usr/local`, `/tmp` | (записуваний шар) | `rw` | Встановлення `apt`/`pip`/`npm` — зберігаються між перезапусками, втрачаються при створенні нового контейнера |

---
## Оновлення

```bash
# Update the flake input (run from the directory containing flake.nix)
cd /etc/nixos && nix flake update hermes-agent

# Rebuild
sudo nixos-rebuild switch
```

У режимі контейнера символічне посилання `current-package` оновлюється, і агент підхоплює новий бінарний файл при перезапуску. Без повторного створення контейнера, без втрати встановлених пакетів.

---
## Усунення проблем

:::tip Podman users
All `docker` commands below work the same with `podman`. Substitute accordingly if you set `container.backend = "podman"`.
:::

### Журнали сервісу

```bash
# Both modes use the same systemd unit
journalctl -u hermes-agent -f

# Container mode: also available directly
docker logs -f hermes-agent
```

### Перевірка контейнера

```bash
systemctl status hermes-agent
docker ps -a --filter name=hermes-agent
docker inspect hermes-agent --format='{{.State.Status}}'
docker exec -it hermes-agent bash
docker exec hermes-agent readlink /data/current-package
docker exec hermes-agent cat /data/.container-identity
```

### Примусове повторне створення контейнера

If you need to reset the writable layer (fresh Ubuntu):

```bash
sudo systemctl stop hermes-agent
docker rm -f hermes-agent
sudo rm /var/lib/hermes/.container-identity
sudo systemctl start hermes-agent
```

### Перевірка завантаження секретів

If the agent starts but can't authenticate with the LLM provider, check that the `.env` file was merged correctly:

```bash
# Native mode
sudo -u hermes cat /var/lib/hermes/.hermes/.env

# Container mode
docker exec hermes-agent cat /data/.hermes/.env
```

### Перевірка GC‑кореня

```bash
nix-store --query --roots $(docker exec hermes-agent readlink /data/current-package)
```

### Поширені проблеми

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot save configuration: managed by NixOS` | CLI guards active | Edit `configuration.nix` and `nixos-rebuild switch` |
| `No adapter available for discord` (or telegram/slack) | Messaging deps missing from the sealed Nix venv | Install `#messaging` variant: `nix profile install ...#messaging`. For NixOS module: `extraDependencyGroups = [ "messaging" ]`. Check `journalctl -u hermes-agent` for `FeatureUnavailable` or `requirements not met` for the underlying error. |
| Container recreated unexpectedly | `extraVolumes`, `extraOptions`, or `image` changed | Expected — writable layer resets. Reinstall packages or use a custom image |
| `hermes version` shows old version | Container not restarted | `systemctl restart hermes-agent` |
| Permission denied on `/var/lib/hermes` | State dir is `0750 hermes:hermes` | Use `docker exec` or `sudo -u hermes` |
| `nix-collect-garbage` removed hermes | GC root missing | Restart the service (preStart recreates the GC root) |
| `no container with name or ID "hermes-agent"` (Podman) | Podman rootful container not visible to regular user | Add passwordless sudo for podman (see [Container Mode](#container-mode) section) |
| `unable to find user hermes` | Container still starting (entrypoint hasn't created user yet) | Wait a few seconds and retry — the CLI retries automatically |
| Tool added via `extraPackages` not found in terminal | Requires `nixos-rebuild switch` to update the per-user profile | Rebuild and restart: `nixos-rebuild switch && systemctl restart hermes-agent` |