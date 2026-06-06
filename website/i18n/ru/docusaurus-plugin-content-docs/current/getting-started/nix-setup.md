---
sidebar_position: 3
title: "Настройка Nix и NixOS"
description: "Установи и разверни Hermes Agent с Nix — от быстрого `nix run` до полностью декларативного модуля NixOS в режиме контейнера"
---

# Настройка Nix & NixOS

Hermes Agent поставляется с Nix‑flake, предлагающим три уровня интеграции:

| Уровень | Для кого | Что ты получаешь |
|-------|-------------|--------------|
| **`nix run` / `nix profile install`** | Любой пользователь Nix (macOS, Linux) | Предварительно собранный бинарный файл со всеми зависимостями — затем используешь обычный CLI‑рабочий процесс |
| **NixOS‑модуль (native)** | Развёртывания серверов NixOS | Декларативная конфигурация, жёстко настроенный systemd‑сервис, управляемые секреты |
| **NixOS‑модуль (container)** | Агенты, которым нужна самомодификация | Всё выше перечисленное, плюс постоянный контейнер Ubuntu, где агент может выполнять `apt`/`pip`/`npm install` |

:::info Что отличается от стандартной установки
Установщик `curl | bash` сам управляет Python, Node и зависимостями. Nix‑flake заменяет всё это — каждая Python‑зависимость представляет собой Nix‑деривацию, построенную с помощью [uv2nix](https://github.com/pyproject-nix/uv2nix), а инструменты выполнения (Node.js, git, ripgrep, ffmpeg) включены в PATH бинарника. Нет pip во время выполнения, нет активации venv, нет `npm install`.

**Для пользователей, не использующих NixOS**, это меняет только шаг установки. Всё, что следует после (`hermes setup`, `hermes gateway install`, редактирование конфигурации), работает так же, как и при стандартной установке.

**Для пользователей NixOS‑модуля** весь жизненный цикл иной: конфигурация хранится в `configuration.nix`, секреты проходят через sops-nix/agenix, сервис представляет собой unit systemd, а команды CLI‑конфигурации заблокированы. Ты управляешь hermes так же, как любым другим сервисом NixOS.
:::
## Предварительные требования

- **Nix с включёнными flakes** — рекомендуется использовать [Determinate Nix](https://install.determinate.systems) (по умолчанию включает flakes)
- **API‑ключи** для сервисов, которые ты планируешь использовать (как минимум: ключ OpenRouter или Anthropic)
## Быстрый старт (Любой пользователь Nix)

Клонирование не требуется. Nix получает, собирает и запускает всё:

```bash
# Run directly (builds on first use, cached after)
nix run github:NousResearch/hermes-agent -- setup
nix run github:NousResearch/hermes-agent -- chat

# Or install persistently
nix profile install github:NousResearch/hermes-agent
hermes setup
hermes chat
```

После `nix profile install` `hermes`, `hermes-agent` и `hermes-acp` находятся в твоём `PATH`. Дальше рабочий процесс идентичен [стандартной установке](./installation.md) — `hermes setup` проведёт тебя через выбор провайдера, `hermes gateway install` настроит службу launchd (macOS) или пользовательскую службу systemd, а конфигурация хранится в `~/.hermes/`.

:::warning Платформы обмена сообщениями (Discord, Telegram, Slack)
Пакет по умолчанию не включает библиотеки платформ обмена сообщениями — они вынесены в установку по требованию, что невозможно в среде Nix с только‑чтением. Если планируешь подключать агент к Discord, Telegram или Slack, установи вариант `messaging`:

```bash
nix profile install github:NousResearch/hermes-agent#messaging
```

Для всех необязательных дополнений (голос, все провайдеры, все платформы):

```bash
nix profile install github:NousResearch/hermes-agent#full
```

Вариант `full` добавляет ~700 МБ к замыканию. Если нужны только платформы обмена сообщениями, `#messaging` добавит лишь ~33 МБ.
:::

<details>
<summary><strong>Сборка из локального клона</strong></summary>

```bash
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
nix build
./result/bin/hermes setup
```

</details>

---
## Модуль NixOS

Flake экспортирует `nixosModules.default` — полностью декларативный модуль службы NixOS, который управляет созданием пользователей, каталогов, генерацией конфигураций, секретами, документами и жизненным циклом службы.

:::note
Этот модуль требует NixOS. Для систем, не являющихся NixOS (macOS, другие дистрибутивы Linux), используй `nix profile install` и стандартный рабочий процесс CLI, описанный выше.
:::

### Добавление входного Flake

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

### Минимальная конфигурация

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

Вот и всё. `nixos-rebuild switch` создаёт пользователя `hermes`, генерирует `config.yaml`, подключает секреты и запускает **gateway** — длительно работающую службу, которая соединяет агент с платформами обмена сообщениями (Telegram, Discord и др.) и прослушивает входящие сообщения.

:::warning Secrets are required
Строка `environmentFiles`, приведённая выше, предполагает, что у тебя настроен [sops-nix](https://github.com/Mic92/sops-nix) или [agenix](https://github.com/ryantm/agenix). Файл должен содержать хотя бы один ключ поставщика LLM (например, `OPENROUTER_API_KEY=sk-or-...`). См. раздел [Secrets Management](#secrets-management) для полной настройки. Если у тебя ещё нет менеджера секретов, можешь использовать обычный файл как отправную точку — просто убедись, что он недоступен для чтения другими пользователями:

```bash
echo "OPENROUTER_API_KEY=sk-or-your-key" | sudo install -m 0600 -o hermes /dev/stdin /var/lib/hermes/env
```

```nix
services.hermes-agent.environmentFiles = [ "/var/lib/hermes/env" ];
```
:::

:::tip addToSystemPackages
Установка `addToSystemPackages = true` делает две вещи: помещает CLI `hermes` в системный `PATH` **и** задаёт системную переменную `HERMES_HOME`, чтобы интерактивный CLI делил состояние (сессии, инструменты, cron) с сервисом **gateway**. Без этого запуск `hermes` в оболочке создаёт отдельный каталог `~/.hermes/`.
:::

### CLI, учитывающий контейнер

:::info
Когда `container.enable = true` и `addToSystemPackages = true`, **каждая** команда `hermes` на хосте автоматически маршрутизируется в управляемый контейнер. Это значит, что твоя интерактивная сессия CLI работает в том же окружении, что и служба **gateway** — с доступом ко всем установленным в контейнере пакетам и инструментам.

- Маршрутизация прозрачна: `hermes chat`, `hermes sessions list`, `hermes version` и т.д. фактически выполняются внутри контейнера
- Все флаги CLI передаются без изменений
- Если контейнер не запущен, CLI несколько раз пытается подключиться (5 с с индикатором для интерактивного использования, 10 с без вывода для скриптов), после чего выдаёт понятную ошибку — без тихого запасного варианта
- Для разработчиков, работающих с кодовой базой hermes, установи `HERMES_DEV=1`, чтобы обойти маршрутизацию через контейнер и запустить локальную копию напрямую

Установи `container.hostUsers`, чтобы создать символическую ссылку `~/.hermes` на каталог состояния службы, так что CLI на хосте и контейнер будут делить сессии, конфиги и **память**:

```nix
services.hermes-agent = {
  container.enable = true;
  container.hostUsers = [ "your-username" ];
  addToSystemPackages = true;
};
```

Пользователи, указанные в `hostUsers`, автоматически добавляются в группу `hermes` для доступа к файлам.

**Пользователи Podman:** Служба NixOS запускает контейнер от имени root. Пользователи Docker получают доступ через сокет группы `docker`, но контейнеры Podman, работающие с правами root, требуют `sudo`. Предоставь безпарольный `sudo` для среды выполнения контейнера:

```nix
security.sudo.extraRules = [{
  users = [ "your-username" ];
  commands = [{
    command = "/run/current-system/sw/bin/podman";
    options = [ "NOPASSWD" ];
  }];
}];
```

CLI автоматически определяет, когда нужен `sudo`, и использует его прозрачно. Без этого придётся вручную запускать `sudo hermes chat`.
:::

### Проверка работоспособности

После `nixos-rebuild switch` проверь, что служба запущена:

```bash
# Check service status
systemctl status hermes-agent

# Watch logs (Ctrl+C to stop)
journalctl -u hermes-agent -f

# If addToSystemPackages is true, test the CLI
hermes version
hermes config       # shows the generated config
```

### Выбор режима развертывания

Модуль поддерживает два режима, управляемых параметром `container.enable`:

| | **Native** (по умолчанию) | **Container** |
|---|---|---|
| Как запускается | Жёстко ограниченная служба `systemd` на хосте | Постоянный контейнер Ubuntu с привязанным `/nix/store` |
| Безопасность | `NoNewPrivileges`, `ProtectSystem=strict`, `PrivateTmp` | Изоляция контейнера, запуск от непривилегированного пользователя внутри |
| Агент может самостоятельно устанавливать пакеты | Нет — только инструменты, доступные в PATH от Nix | Да — установки `apt`, `pip`, `npm` сохраняются между перезапусками |
| Поверхность конфигурации | Та же | Та же |
| Когда выбирать | Стандартные развертывания, максимальная безопасность, воспроизводимость | Агенту требуется установка пакетов во время работы, изменяемое окружение, экспериментальные инструменты |

Чтобы включить режим контейнера, добавь одну строку:

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
Режим контейнера автоматически включает `virtualisation.docker.enable` через `mkDefault`. Если ты используешь Podman, задай `container.backend = "podman"` и `virtualisation.docker.enable = false`.
:::

---
## Конфигурация

### Декларативные настройки

Опция `settings` принимает произвольный `attrset`, который рендерится в `config.yaml`. Она поддерживает глубокое слияние нескольких определений модулей (через `lib.recursiveUpdate`), поэтому конфигурацию можно разбить по файлам:

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

Оба набора глубоко объединяются во время оценки. Ключи, объявленные в Nix, всегда переопределяют ключи в существующем `config.yaml` на диске, но **ключи, добавленные пользователем и не затронутые Nix, сохраняются**. Это значит, что если агент или ручное редактирование добавляют такие ключи, как `skills.disabled` или `streaming.enabled`, они сохраняются после `nixos-rebuild switch`.

:::note Именование модели
`settings.model.default` использует идентификатор модели, ожидаемый твоим провайдером. В случае [OpenRouter](https://openrouter.ai) (по умолчанию) они выглядят как `"anthropic/claude-sonnet-4"` или `"google/gemini-3-flash"`. Если ты используешь провайдера напрямую (Anthropic, OpenAI), задай `settings.model.base_url`, указывая их API, и используй их собственные идентификаторы моделей (например, `"claude-sonnet-4-20250514"`). Когда `base_url` не задан, Hermes использует OpenRouter по умолчанию.
:::

:::tip Как узнать доступные ключи конфигурации
Выполни `nix build .#configKeys && cat result`, чтобы увидеть каждый листовой ключ конфигурации, извлечённый из `DEFAULT_CONFIG` в Python. Ты можешь вставить свой существующий `config.yaml` в `attrset` `settings` — структура отображается 1:1.
:::

<details>
<summary><strong>Полный пример: все часто настраиваемые параметры</strong></summary>

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

### Обходной путь: принеси свою конфигурацию

Если ты предпочитаешь полностью управлять `config.yaml` вне Nix, используй `configFile`:

```nix
services.hermes-agent.configFile = /etc/hermes/config.yaml;
```

Это полностью обходится без `settings` — нет слияния, нет генерации. Файл копируется как есть в `$HERMES_HOME/config.yaml` при каждой активации.

### Шпаргалка по настройке

Быстрый справочник самых часто настраиваемых параметров для пользователей Nix:

| Я хочу… | Опция | Пример |
|---|---|---|
| Сменить модель LLM | `settings.model.default` | `"anthropic/claude-sonnet-4"` |
| Использовать другую конечную точку провайдера | `settings.model.base_url` | `"https://openrouter.ai/api/v1"` |
| Добавить API‑ключи | `environmentFiles` | `[ config.sops.secrets."hermes-env".path ]` |
| Дать агенту «личность» | `${services.hermes-agent.stateDir}/.hermes/SOUL.md` | управлять файлом напрямую |
| Добавить серверы MCP‑инструментов | `mcpServers.<name>` | См. [MCP Servers](#mcp-servers) |
| Включить Discord/Telegram/Slack | `extraDependencyGroups` | `[ "messaging" ]` |
| Примонтировать каталоги хоста в контейнер | `container.extraVolumes` | `[ "/data:/data:rw" ]` |
| Передать доступ к GPU в контейнер | `container.extraOptions` | `[ "--gpus" "all" ]` |
| Использовать Podman вместо Docker | `container.backend` | `"podman"` |
| Делить состояние между CLI хоста и контейнером | `container.hostUsers` | `[ "sidbin" ]` |
| Сделать дополнительные инструменты доступными агенту | `extraPackages` | `[ pkgs.pandoc pkgs.imagemagick ]` |
| Использовать пользовательский базовый образ | `container.image` | `"ubuntu:24.04"` |
| Переопределить пакет hermes | `package` | `inputs.hermes-agent.packages.${system}.default.override { ... }` |
| Сменить каталог состояния | `stateDir` | `"/opt/hermes"` |
| Установить рабочий каталог агента | `workingDirectory` | `"/home/user/projects"` |

---
## Управление секретами

:::danger Никогда не помещай API‑ключи в `settings` или `environment`
Значения в Nix‑выражениях попадают в `/nix/store`, который доступен для чтения всем пользователям. Всегда используй `environmentFiles` вместе с менеджером секретов.
:::

И `environment` (несекретные переменные), и `environmentFiles` (секретные файлы) объединяются в `$HERMES_HOME/.env` во время активации (`nixos-rebuild switch`). Hermes читает этот файл при каждом запуске, поэтому изменения вступают в силу после `systemctl restart hermes-agent` — пересоздавать контейнер не требуется.

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

Файл секретов содержит пары «ключ‑значение»:

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

Для платформ, требующих OAuth (например, Discord), используй `authFile` для начального заполнения учётных данных при первом развертывании:

```nix
{
  services.hermes-agent = {
    authFile = config.sops.secrets."hermes/auth.json".path;
    # authFileForceOverwrite = true;  # overwrite on every activation
  };
}
```

Файл копируется только если `auth.json` ещё не существует (если только `authFileForceOverwrite = true` не задано). Обновления токенов OAuth во время работы записываются в каталог состояния и сохраняются между пересборками.
## Документы

Опция `documents` устанавливает файлы в рабочий каталог агента (в `workingDirectory`, который агент использует как рабочее пространство). Hermes ищет определённые имена файлов по соглашению:

- **`USER.md`** — контекст пользователя, с которым взаимодействует агент.
- Любые другие файлы, размещённые здесь, видимы агенту как файлы рабочего пространства.

Файл идентификации агента отдельный: Hermes загружает основной `SOUL.md` из `$HERMES_HOME/SOUL.md`, который в модуле NixOS находится по пути `${services.hermes-agent.stateDir}/.hermes/SOUL.md`. Помещение `SOUL.md` в `documents` создаёт лишь файл рабочего пространства и не заменит основной файл персонажа.

```nix
{
  services.hermes-agent.documents = {
    "USER.md" = ./documents/USER.md;  # path reference, copied from Nix store
  };
}
```

Значения могут быть строками‑инлайн или ссылками на пути. Файлы устанавливаются при каждом `nixos-rebuild switch`.

---
## MCP‑серверы

Опция `mcpServers` декларативно настраивает серверы [MCP (Model Context Protocol)](https://modelcontextprotocol.io). Каждый сервер использует транспорт **stdio** (локальная команда) или **HTTP** (удалённый URL).

### Транспорт stdio (локальные серверы)

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
Переменные окружения в значениях `env` разрешаются из `$HERMES_HOME/.env` во время выполнения. Используй `environmentFiles` для внедрения секретов — никогда не помещай токены напрямую в конфигурацию Nix.
:::

### Транспорт HTTP (удалённые серверы)

```nix
{
  services.hermes-agent.mcpServers.remote-api = {
    url = "https://mcp.example.com/v1/mcp";
    headers.Authorization = "Bearer \${MCP_REMOTE_API_KEY}";
    timeout = 180;
  };
}
```

### Транспорт HTTP с OAuth

Установи `auth = "oauth"` для серверов, использующих OAuth 2.1. Hermes реализует полный поток PKCE — обнаружение метаданных, динамическую регистрацию клиента, обмен токенами и автоматическое обновление.

```nix
{
  services.hermes-agent.mcpServers.my-oauth-server = {
    url = "https://mcp.example.com/mcp";
    auth = "oauth";
  };
}
```

Токены сохраняются в `$HERMES_HOME/mcp-tokens/<server-name>.json` и сохраняются между перезапусками и пересборками.

<details>
<summary><strong>Первичная авторизация OAuth на безголовых серверах</strong></summary>

Первая авторизация OAuth требует согласования через браузер. В безголовой среде Hermes выводит URL авторизации в `stdout`/логи вместо открытия браузера.

**Вариант A: Интерактивный bootstrap** — выполните процесс один раз через `docker exec` (контейнер) или `sudo -u hermes` (нативно):

```bash
# Container mode
docker exec -it hermes-agent \
  hermes mcp add my-oauth-server --url https://mcp.example.com/mcp --auth oauth

# Native mode
sudo -u hermes HERMES_HOME=/var/lib/hermes/.hermes \
  hermes mcp add my-oauth-server --url https://mcp.example.com/mcp --auth oauth
```

Контейнер использует `--network=host`, поэтому слушатель обратного вызова OAuth на `127.0.0.1` доступен из браузера хоста.

**Вариант B: Предзагрузка токенов** — завершите процесс на рабочей станции, затем скопируйте токены:

```bash
hermes mcp add my-oauth-server --url https://mcp.example.com/mcp --auth oauth
scp ~/.hermes/mcp-tokens/my-oauth-server{,.client}.json \
    server:/var/lib/hermes/.hermes/mcp-tokens/
# Ensure: chown hermes:hermes, chmod 0600
```

</details>

### Сэмплирование (инициированные сервером запросы LLM)

Некоторые MCP‑серверы могут запрашивать завершения LLM у агента:

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
## Управляемый режим

Когда hermes запускается через модуль NixOS, следующие команды CLI **заблокированы** с описательной ошибкой, указывающей на `configuration.nix`:

| Заблокированная команда | Почему |
|---|---|
| `hermes setup` | Конфигурация декларативна — редактируй `settings` в своей конфигурации Nix |
| `hermes config edit` | Конфигурация генерируется из `settings` |
| `hermes config set <key> <value>` | Конфигурация генерируется из `settings` |
| `hermes gateway install` | Служба systemd управляется NixOS |
| `hermes gateway uninstall` | Служба systemd управляется NixOS |

Это предотвращает расхождение между тем, что объявлено в Nix, и тем, что находится на диске. Обнаружение использует два сигнала:

1. **`HERMES_MANAGED=true`** — переменная окружения, задаваемая службой systemd, видимая процессу шлюза
2. **`.managed`** — файл‑маркер в `HERMES_HOME`, создаваемый скриптом активации, видимый интерактивным оболочкам (например, `docker exec -it hermes-agent hermes config set …` также блокируется)

Чтобы изменить конфигурацию, отредактируй свой Nix‑конфиг и выполни `sudo nixos-rebuild switch`.

---
## Архитектура контейнера

:::info
Этот раздел актуален только если ты используешь `container.enable = true`. Пропусти его для развертываний в нативном режиме.
:::

Когда режим контейнера включён, hermes работает внутри постоянного Ubuntu‑контейнера, а бинарник, собранный Nix, bind‑монтируется только для чтения из хоста:

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

Бинарник, собранный Nix, работает внутри Ubuntu‑контейнера, потому что `/nix/store` bind‑монтируется — он содержит собственный интерпретатор и все зависимости, поэтому не зависит от системных библиотек контейнера. Точка входа контейнера разрешается через символическую ссылку `current-package`: `/data/current-package/bin/hermes gateway run --replace`. При `nixos-rebuild switch` обновляется только ссылка — контейнер продолжает работать.

### Что сохраняется при разных событиях

| Событие | Пересоздаётся контейнер? | `/data` (состояние) | `/home/hermes` | Записываемый слой (`apt`/`pip`/`npm`) |
|---|---|---|---|---|
| `systemctl restart hermes-agent` | Нет | Сохраняется | Сохраняется | Сохраняется |
| `nixos-rebuild switch` (изменение кода) | Нет (обновлена ссылка) | Сохраняется | Сохраняется | Сохраняется |
| Перезагрузка хоста | Нет | Сохраняется | Сохраняется | Сохраняется |
| `nix-collect-garbage` | Нет (GC‑корень) | Сохраняется | Сохраняется | Сохраняется |
| Смена образа (`container.image`) | **Да** | Сохраняется | Сохраняется | **Утеряно** |
| Смена томов/опций | **Да** | Сохраняется | Сохраняется | **Утеряно** |
| Изменение `environment`/`environmentFiles` | Нет | Сохраняется | Сохраняется | Сохраняется |

Контейнер пересоздаётся только когда меняется его **хеш идентичности**. Хеш охватывает: версию схемы, образ, `extraVolumes`, `extraOptions` и скрипт точки входа. Изменения переменных окружения, настроек, документов или самого пакета hermes **не** вызывают пересоздание.

:::warning Записываемый слой теряется
Когда меняется хеш идентичности (обновление образа, новые тома, новые опции контейнера), контейнер уничтожается и создаётся заново из свежего `container.image`. Любые пакеты, установленные через `apt install`, `pip install` или `npm install` в записываемом слое, теряются. Состояние в `/data` и `/home/hermes` сохраняется (это bind‑монтирования).

Если агент зависит от конкретных пакетов, рассмотрите их включение в пользовательский образ (`container.image = "my-registry/hermes-base:latest"`) или скрипт их установки в `SOUL.md` агента.
:::

### Защита GC‑корня

Скрипт `preStart` создаёт GC‑корень в `${stateDir}/.gc-root`, указывающий на текущий пакет hermes. Это препятствует удалению работающего бинарника командой `nix-collect-garbage`. Если GC‑корень каким‑то образом ломается, перезапуск сервиса воссоздаёт его.

---
## Плагины

Модуль NixOS поддерживает декларативную установку плагинов — без необходимости выполнять императивную команду `hermes plugins install`.

### Плагины‑каталоги (`extraPlugins`)

Для плагинов, представляющих собой просто дерево исходников с `plugin.yaml` + `__init__.py` (например, [hermes‑lcm](https://github.com/stephenschoettler/hermes-lcm)):

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

Плагины символически связываются в `$HERMES_HOME/plugins/` во время активации. Hermes обнаруживает их обычным сканированием каталога. Удаление плагина из списка и запуск `nixos-rebuild switch` удалит символическую ссылку.

### Плагины‑точки входа (`extraPythonPackages`)

Для pip‑упакованных плагинов, регистрируемых через `[project.entry-points."hermes_agent.plugins"]` (например, [rtk‑hermes](https://github.com/ogallotti/rtk-hermes)):

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

`site-packages` пакета добавляется в `PYTHONPATH` в обёртке hermes. `importlib.metadata` обнаруживает точку входа при запуске сессии.

### Группы необязательных зависимостей (`extraDependencyGroups`)

Для необязательных extras, объявленных в `pyproject.toml` hermes‑agent, используйте `extraDependencyGroups`, чтобы включить их в запечатанную venv во время сборки. Это требуется для любого extra, не входящего в набор `[all]` — на Nix установка во время выполнения в только‑для‑чтения store невозможна.

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

Это решается uv вместе с основными зависимостями — без патчей `PYTHONPATH`, без риска конфликтов. Доступные группы:

| Группа | Что она включает |
|-------|-----------------|
| `messaging` | Discord, Telegram, Slack |
| `matrix` | Matrix/Element (mautrix с шифрованием; только Linux) |
| `dingtalk` | DingTalk |
| `feishu` | Feishu/Lark |
| `voice` | Локальное распознавание речи (faster‑whisper) |
| `edge-tts` | Провайдер Edge TTS |
| `tts-premium` | ElevenLabs TTS |
| `anthropic` | Нативный SDK Anthropic (не требуется через OpenRouter) |
| `bedrock` | AWS Bedrock (boto3) |
| `azure-identity` | Аутентификация Azure Entra ID |
| `honcho` | Провайдер памяти Honcho |
| `hindsight` | Провайдер памяти Hindsight |
| `modal` | Бэкенд терминала Modal |
| `daytona` | Бэкенд терминала Daytona |
| `exa` | Веб‑поиск Exa |
| `firecrawl` | Веб‑поиск Firecrawl |
| `fal` | Генерация изображений FAL |

Или используйте готовые flake‑пакеты `#messaging` или `#full` вместо конфигурации отдельных extras (см. [Quick Start](#quick-start-any-nix-user)).

**Когда использовать что:**

| Потребность | Опция |
|------|--------|
| Включить необязательный extra из `pyproject.toml` | `extraDependencyGroups` |
| Добавить внешний Python‑плагин, не указанный в `pyproject.toml` | `extraPythonPackages` |
| Добавить системный бинарный файл (pandoc, jq и др.) | `extraPackages` |
| Добавить плагин‑каталог с исходным деревом | `extraPlugins` |

### Комбинирование обоих вариантов

Плагин‑каталог с сторонними Python‑зависимостями требует обеих опций:

```nix
services.hermes-agent = {
  extraPlugins = [ my-plugin-src ];          # plugin source
  extraPythonPackages = [ pkgs.python312Packages.redis ];  # its Python dep
  extraPackages = [ pkgs.redis ];            # system binary it needs
};
```

### Использование overlay

Внешние flakes могут переопределять пакет напрямую:

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

### Конфигурация плагинов

Плагины всё равно нужно включить в `config.yaml`. Добавьте их через декларативные настройки:

```nix
services.hermes-agent.settings.plugins.enabled = [
  "hermes-lcm"
  "rtk-rewrite"
];
```

:::note
Проверка конфликтов во время сборки предотвращает перекрытие пакетов плагинов над основными зависимостями hermes. Если плагин предоставляет пакет, уже присутствующий в запечатанной venv, `nixos-rebuild` завершится с понятной ошибкой.
:::
## Development

### Dev Shell

Flake предоставляет **dev‑shell** с Python 3.12, uv, Node.js и всеми runtime‑tools:

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

Включённый файл `.envrc` автоматически активирует dev‑shell:

```bash
cd hermes-agent
direnv allow    # one-time
# Subsequent entries are near-instant (stamp file skips dep install)
```

### Flake Checks

Flake включает проверку сборки, которая запускается в CI и локально:

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
<summary><strong>Что проверяет каждая проверка</strong></summary>

| Check | Что проверяется |
|---|---|
| `package-contents` | существуют бинарные файлы `hermes` и `hermes-agent`, и команда `hermes version` работает |
| `entry-points-sync` | каждый пункт `[project.scripts]` в `pyproject.toml` имеет обёрнутый бинарный файл в пакете Nix |
| `cli-commands` | `hermes --help` показывает подкоманды `gateway` и `config` |
| `managed-guard` | `HERMES_MANAGED=true hermes config set …` выводит ошибку NixOS |
| `bundled-skills` | директория `skills` существует, содержит файлы `SKILL.md`, переменная `HERMES_BUNDLED_SKILLS` установлена в обёртке |
| `config-roundtrip` | 7 сценариев слияния: свежая установка, переопределение Nix, сохранение пользовательского ключа, смешанное слияние, аддитивное слияние MCP, глубокое вложенное слияние, идемпотентность |

</details>

---
## Справочник опций

### Core

| Опция | Тип | По умолчанию | Описание |
|---|---|---|---|
| `enable` | `bool` | `false` | Включить сервис hermes-agent |
| `package` | `package` | `hermes-agent` | Пакет hermes-agent, который использовать |
| `user` | `str` | `"hermes"` | Системный пользователь |
| `group` | `str` | `"hermes"` | Системная группа |
| `createUser` | `bool` | `true` | Автоматически создавать пользователя/группу |
| `stateDir` | `str` | `"/var/lib/hermes"` | Каталог состояния (родитель `HERMES_HOME`) |
| `workingDirectory` | `str` | `"${stateDir}/workspace"` | Рабочий каталог агента (`MESSAGING_CWD`) |
| `addToSystemPackages` | `bool` | `false` | Добавить CLI `hermes` в системный PATH и установить `HERMES_HOME` глобально |

### Configuration

| Опция | Тип | По умолчанию | Описание |
|---|---|---|---|
| `settings` | `attrs` (deep-merged) | `{}` | Декларативная конфигурация, рендерится как `config.yaml`. Поддерживает произвольную вложенность; несколько определений объединяются через `lib.recursiveUpdate` |
| `configFile` | `null` or `path` | `null` | Путь к существующему `config.yaml`. При указании полностью переопределяет `settings` |

### Secrets & Environment

| Опция | Тип | По умолчанию | Описание |
|---|---|---|---|
| `environmentFiles` | `listOf str` | `[]` | Пути к файлам env с секретами. Объединяются в `$HERMES_HOME/.env` во время активации |
| `environment` | `attrsOf str` | `{}` | Не‑секретные переменные окружения. **Видимы в Nix‑store** — не помещай сюда секреты |
| `authFile` | `null` or `path` | `null` | Файл‑засев OAuth‑учётных данных. Копируется только при первом развертывании |
| `authFileForceOverwrite` | `bool` | `false` | Всегда перезаписывать `auth.json` из `authFile` при активации |

### Documents

| Опция | Тип | По умолчанию | Описание |
|---|---|---|---|
| `documents` | `attrsOf (either str path)` | `{}` | Файлы рабочего пространства. Ключи — имена файлов, значения — встроенные строки или пути. Устанавливаются в `workingDirectory` при активации |

### MCP Servers

| Опция | Тип | По умолчанию | Описание |
|---|---|---|---|
| `mcpServers` | `attrsOf submodule` | `{}` | Определения серверов MCP, объединяемые в `settings.mcp_servers` |
| `mcpServers.<name>.command` | `null` or `str` | `null` | Команда сервера (транспорт stdio) |
| `mcpServers.<name>.args` | `listOf str` | `[]` | Аргументы команды |
| `mcpServers.<name>.env` | `attrsOf str` | `{}` | Переменные окружения для процесса сервера |
| `mcpServers.<name>.url` | `null` or `str` | `null` | URL конечной точки сервера (транспорт HTTP/StreamableHTTP) |
| `mcpServers.<name>.headers` | `attrsOf str` | `{}` | HTTP‑заголовки, например `Authorization` |
| `mcpServers.<name>.auth` | `null` or `"oauth"` | `null` | Метод аутентификации. `"oauth"` включает OAuth 2.1 PKCE |
| `mcpServers.<name>.enabled` | `bool` | `true` | Включить или отключить этот сервер |
| `mcpServers.<name>.timeout` | `null` or `int` | `null` | Таймаут вызова инструмента в секундах (по умолчанию: 120) |
| `mcpServers.<name>.connect_timeout` | `null` or `int` | `null` | Таймаут соединения в секундах (по умолчанию: 60) |
| `mcpServers.<name>.tools` | `null` or `submodule` | `null` | Фильтрация инструментов (списки `include`/`exclude`) |
| `mcpServers.<name>.sampling` | `null` or `submodule` | `null` | Конфигурация сэмплинга для запросов LLM, инициируемых сервером |

### Service Behavior

| Опция | Тип | По умолчанию | Описание |
|---|---|---|---|
| `extraArgs` | `listOf str` | `[]` | Дополнительные аргументы для `hermes gateway` |
| `extraPackages` | `listOf package` | `[]` | Дополнительные пакеты, доступные агенту. Добавляются в per‑user профиль пользователя hermes, чтобы терминальные команды, skills и cron‑задачи их видели |
| `extraPlugins` | `listOf package` | `[]` | Пакеты плагинов‑директорий, которые симлинкуются в `$HERMES_HOME/plugins/`. Каждый должен содержать `plugin.yaml` |
| `extraPythonPackages` | `listOf package` | `[]` | Пакеты Python, добавляемые в PYTHONPATH для обнаружения плагинов‑точек входа. Сборка через `python312Packages` |
| `extraDependencyGroups` | `listOf str` | `[]` | Необязательные extras из pyproject.toml, включаемые в запечатанное venv (например `["hindsight"]`). Разрешаются uv — без конфликтов |
| `restart` | `str` | `"always"` | Политика systemd `Restart=` |
| `restartSec` | `int` | `5` | Значение systemd `RestartSec=` |

### Container

| Опция | Тип | По умолчанию | Описание |
|---|---|---|---|
| `container.enable` | `bool` | `false` | Включить режим OCI‑контейнера |
| `container.backend` | `enum ["docker" "podman"]` | `"docker"` | Среда выполнения контейнера |
| `container.image` | `str` | `"ubuntu:24.04"` | Базовый образ (загружается во время выполнения) |
| `container.extraVolumes` | `listOf str` | `[]` | Дополнительные монтирования томов (`host:container:mode`) |
| `container.extraOptions` | `listOf str` | `[]` | Дополнительные аргументы, передаваемые `docker create` |
| `container.hostUsers` | `listOf str` | `[]` | Интерактивные пользователи, которым создаётся ссылка `~/.hermes` на каталог состояния сервиса и которые автоматически добавляются в группу `hermes` |
## Структура каталогов

### Нативный режим

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

### Режим контейнера

Та же структура, монтируется в контейнер:

| Путь в контейнере | Путь на хосте | Режим | Примечания |
|---|---|---|---|
| `/nix/store` | `/nix/store` | `ro` | Бинарный файл Hermes + все зависимости Nix |
| `/data` | `/var/lib/hermes` | `rw` | Всё состояние, конфигурация, рабочая область |
| `/home/hermes` | `${stateDir}/home` | `rw` | Постоянный домашний каталог агента — `pip install --user`, кэши инструментов |
| `/usr`, `/usr/local`, `/tmp` | (writable layer) | `rw` | `apt`/`pip`/`npm` установки — сохраняются между перезапусками, теряются при воссоздании |

---
## Обновление

```bash
# Update the flake input (run from the directory containing flake.nix)
cd /etc/nixos && nix flake update hermes-agent

# Rebuild
sudo nixos-rebuild switch
```

В режиме контейнера ссылка `current-package` обновляется, и агент подхватывает новый бинарный файл при перезапуске. Контейнер не пересоздаётся, установленные пакеты не теряются.
## Устранение неполадок

:::tip Пользователи Podman
Все команды `docker`, указанные ниже, работают одинаково с `podman`. Замени их соответственно, если в конфигурации указано `container.backend = "podman"`.
:::

### Журналы сервиса

```bash
# Both modes use the same systemd unit
journalctl -u hermes-agent -f

# Container mode: also available directly
docker logs -f hermes-agent
```

### Инспекция контейнера

```bash
systemctl status hermes-agent
docker ps -a --filter name=hermes-agent
docker inspect hermes-agent --format='{{.State.Status}}'
docker exec -it hermes-agent bash
docker exec hermes-agent readlink /data/current-package
docker exec hermes-agent cat /data/.container-identity
```

### Принудительное воссоздание контейнера

Если нужно сбросить слой записи (чистый Ubuntu):

```bash
sudo systemctl stop hermes-agent
docker rm -f hermes-agent
sudo rm /var/lib/hermes/.container-identity
sudo systemctl start hermes-agent
```

### Проверка загрузки секретов

Если агент запускается, но не может аутентифицироваться у провайдера LLM, проверь, что файл `.env` был корректно объединён:

```bash
# Native mode
sudo -u hermes cat /var/lib/hermes/.hermes/.env

# Container mode
docker exec hermes-agent cat /data/.hermes/.env
```

### Проверка корня GC

```bash
nix-store --query --roots $(docker exec hermes-agent readlink /data/current-package)
```

### Распространённые проблемы

| Симптом | Причина | Решение |
|---|---|---|
| `Cannot save configuration: managed by NixOS` | Включены защиты CLI | Отредактируй `configuration.nix` и выполни `nixos-rebuild switch` |
| `No adapter available for discord` (или telegram/slack) | В запечатанном Nix‑окружении отсутствуют зависимости мессенджинга | Установи вариант `#messaging`: `nix profile install ...#messaging`. Для модуля NixOS: `extraDependencyGroups = [ "messaging" ]`. Проверь `journalctl -u hermes-agent` на наличие `FeatureUnavailable` или `requirements not met` для основной ошибки. |
| Контейнер воссоздан неожиданно | Изменены `extraVolumes`, `extraOptions` или `image` | Ожидаемо — сбрасывается слой записи. Переустанови пакеты или используй кастомный образ |
| `hermes version` показывает старую версию | Контейнер не был перезапущен | Выполни `systemctl restart hermes-agent` |
| Отказ в доступе к `/var/lib/hermes` | Директория состояния имеет права `0750 hermes:hermes` | Используй `docker exec` или `sudo -u hermes` |
| `nix-collect-garbage` удалил hermes | Отсутствует корень GC | Перезапусти сервис (preStart воссоздаёт корень GC) |
| `no container with name or ID "hermes-agent"` (Podman) | Корневой контейнер Podman недоступен обычному пользователю | Добавь безпарольный sudo для podman (см. раздел [Container Mode](#container-mode)) |
| `unable to find user hermes` | Контейнер ещё запускается (entrypoint ещё не создал пользователя) | Подожди несколько секунд и повтори запрос — CLI автоматически делает повторные попытки |
| Инструмент, добавленный через `extraPackages`, не найден в терминале | Требуется `nixos-rebuild switch` для обновления профиля пользователя | Пересобери и перезапусти: `nixos-rebuild switch && systemctl restart hermes-agent` |