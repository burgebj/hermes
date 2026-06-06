---
sidebar_position: 16
title: "LSP — семантична діагностика"
description: "Справжні сервери мов (pyright, gopls, rust-analyzer, …), підключені до перевірки lint після запису, яку використовують write_file та patch."
---

# Протокол серверу мови (LSP)

Hermes запускає повноцінні сервери мови — pyright, gopls, rust-analyzer,
typescript-language-server, clangd та ~20 інших — як фонові підпроцеси і передає їх семантичні діагностики у post‑write lint‑перевірку, яку використовують `write_file` та `patch`. Коли агент редагує файл, він бачить саме ті помилки, які внесло редагування — не лише синтаксичні, а **помилки типу, невизначені імена, відсутні імпорти та проєктні семантичні проблеми**, які виявляє сервер мови.

Це та сама архітектура, яку використовують найкращі агенти кодування. Hermes постачається самодостатньо: не потрібен хост‑редактор, жодних плагінів для встановлення, жодного окремого демона для керування.

## Коли запускається LSP

LSP активується лише при **виявленні git‑робочого простору**. Коли робочий каталог агента (або файл, що редагується) знаходиться всередині git‑репозиторію, LSP працює з цим простором. Якщо жоден із них не у git‑репозиторії, LSP залишається неактивним — це корисно для шлюзів обміну повідомленнями, де cwd є домашньою директорією користувача і немає проєкту для діагностики.

Перевірка здійснюється у два етапи: спочатку in‑process синтаксична перевірка (мікросекунди), потім діагностика LSP, коли синтаксис чистий. Нестабільний або відсутній сервер мови ніколи не зламає запис — будь‑який шлях збою LSP тихо повертається до результату лише синтаксичної перевірки.

Конкретно, при кожному успішному `write_file` або `patch`:

1. Hermes фіксує базовий рівень поточних діагностик для файлу.
2. Виконує запис.
3. Заново запитує сервер мови, фільтрує діагностики, які вже були в базовому рівні, і повертає лише нові.

Агент бачить вивід типу:

```
{
  "bytes_written": 42,
  "dirs_created": false,
  "lint": {"status": "ok", "output": ""},
  "lsp_diagnostics": "LSP diagnostics introduced by this edit:\n<diagnostics file=\"/path/to/foo.py\">\nERROR [42:5] Cannot find name 'foo' [reportUndefinedVariable] (Pyright)\nERROR [50:1] Argument of type \"str\" is not assignable to \"int\" [reportArgumentType] (Pyright)\n</diagnostics>"
}
```

Поле `lint` містить результат синтаксичної перевірки (мікросекунди in‑process парсингу через `ast.parse`, `json.loads` тощо); поле `lsp_diagnostics` містить семантичні діагностики реального сервера мови. Два канали, незалежні сигнали — агент бачить файл без синтаксичних помилок, але з семантичними проблемами як

``lint: ok`` плюс заповнений ``lsp_diagnostics``.

## Підтримувані мови

| Мова | Сервер | Авто‑встановлення |
|----------|--------|--------------|
| Python | `pyright-langserver` | npm |
| TypeScript / JavaScript / JSX / TSX | `typescript-language-server` | npm |
| Vue | `@vue/language-server` | npm |
| Svelte | `svelte-language-server` | npm |
| Astro | `@astrojs/language-server` | npm |
| Go | `gopls` | `go install` |
| Rust | `rust-analyzer` | manual (rustup) |
| C / C++ | `clangd` | manual (LLVM) |
| Bash / Zsh | `bash-language-server` | npm |
| YAML | `yaml-language-server` | npm |
| Lua | `lua-language-server` | manual (GitHub releases) |
| PHP | `intelephense` | npm |
| OCaml | `ocaml-lsp` | manual (opam) |
| Dockerfile | `dockerfile-language-server-nodejs` | npm |
| Terraform | `terraform-ls` | manual |
| Dart | `dart language-server` | manual (dart sdk) |
| Haskell | `haskell-language-server` | manual (ghcup) |
| Julia | `julia` + LanguageServer.jl | manual |
| Clojure | `clojure-lsp` | manual |
| Nix | `nixd` | manual |
| Zig | `zls` | manual |
| Gleam | `gleam lsp` | manual (gleam install) |
| Elixir | `elixir-ls` | manual |
| Prisma | `prisma language-server` | manual |
| Kotlin | `kotlin-language-server` | manual |
| Java | `jdtls` | manual |

Для записів «manual» встановлюй сервер через будь‑який інструмент керування ланцюжком інструментів, який підходить для даної мови (rustup, ghcup, opam, brew, …). Hermes автоматично виявляє бінарник у PATH або в `<HERMES_HOME>/lsp/bin/`.

Декілька серверів встановлюються разом із залежністю, яку npm не може автоматично підвантажити. Поточний випадок — `typescript-language-server`, який потребує SDK `typescript`, доступного у тому ж дереві `node_modules` — Hermes встановлює обидва пакети одночасно, коли ти виконуєш `hermes lsp install typescript` або коли авто‑встановлення спрацьовує при першому використанні.

## CLI

```
hermes lsp status          # service state + per-server install status
hermes lsp list            # registry, optionally --installed-only
hermes lsp install <id>    # eagerly install one server
hermes lsp install-all     # try every server with a known recipe
hermes lsp restart         # tear down running clients
hermes lsp which <id>      # print resolved binary path
```

`hermes lsp status` — найкраща відправна точка: вона показує, які мови отримають сьогодні семантичні діагностики і які потребують встановлення бінарника.

## Конфігурація

Типові налаштування підходять для більшості випадків; нічого не треба встановлювати, якщо бінарники вже в PATH.

```yaml
# config.yaml
lsp:
  # Master toggle. Disabling skips the entire subsystem — no servers
  # spawn, no background event loop runs.
  enabled: true

  # How long to wait for diagnostics after each write.
  wait_mode: document      # "document" or "full"
  wait_timeout: 5.0

  # How to handle missing server binaries.
  #   auto    — install via npm/pip/go install into <HERMES_HOME>/lsp/bin
  #   manual  — only use binaries already on PATH
  install_strategy: auto

  # Per-server overrides (all optional).
  servers:
    pyright:
      disabled: false
      command: ["/abs/path/to/pyright-langserver", "--stdio"]
      env: { PYRIGHT_LOG_LEVEL: "info" }
      initialization_options:
        python:
          analysis:
            typeCheckingMode: "strict"
    typescript:
      disabled: true       # skip TS even when its extensions match
```

### Ключі per‑server

* `disabled: true` — повністю пропустити цей сервер, навіть якщо його розширення відповідає файлу.
* `command: [bin, ...args]` — вказати власний шлях до бінарника. Оминає авто‑встановлення.
* `env: {KEY: value}` — додаткові змінні середовища, що передаються запущеному процесу.
* `initialization_options: {...}` — об’єднуються у payload `initializationOptions` LSP, що надсилається під час `initialize`. Специфічно для сервера; дивись документацію сервера мови.

## Місця встановлення

Коли `install_strategy: auto`, Hermes встановлює бінарники у `<HERMES_HOME>/lsp/bin/`. Пакети NPM потрапляють у `<HERMES_HOME>/lsp/node_modules/` з символічними посиланнями на bin на рівень вище. Бінарники Go беруться з `go install` з `GOBIN`, вказаним на staging‑директорію.

Ніщо не встановлюється у `/usr/local/`, `~/.local/` чи інші спільні шляхи — staging‑директорія повністю належить Hermes і видаляється при скиданні профілю.

## Характеристики продуктивності

Сервери LSP **lazy‑spawned** при першому використанні. Редагування Python‑файлу в проєкті, який раніше не мав `.py`‑трафіку, запускає pyright; спавн займає 1‑3 секунди для більшості серверів (rust‑analyzer може зайняти 10+ секунд у холодному проєкті). Подальші редагування в тому ж робочому просторі повторно використовують вже запущений сервер.

Шар LSP додає кілька мілісекунд до чистих записів, коли діагностик не виводиться. Коли діагностик виводиться, час очікування обмежений `wait_timeout` секундами — зазвичай сервер відповідає за десятки мілісекунд для pyright/tsserver і за кілька секунд для rust‑analyzer під час індексації.

Сервери тримаються активними протягом усього процесу Hermes. Немає idle‑timeout‑реапера — вартість перезапуску індексу сервера при кожному записі була б значно вищою, ніж утримання демона.

## Вимкнення

Встанови `lsp.enabled: false` у `config.yaml`, щоб вимкнути всю підсистему. Пост‑write перевірка повертається до in‑process синтаксичної перевірки (`ast.parse` для Python, `json.loads` для JSON тощо), яка залишається незмінною порівняно з попередніми версіями.

Щоб вимкнути одну мову без вимкнення всього шару:

```yaml
lsp:
  servers:
    rust-analyzer:
      disabled: true
```

## Усунення проблем

**`hermes lsp status` показує сервер як «missing»**

Бінарник відсутній у PATH і не знаходиться в `<HERMES_HOME>/lsp/bin/`. Запусти `hermes lsp install <server_id>`, щоб спробувати авто‑встановлення, або встанови бінарник вручну через звичний інструмент мови.

**Розділ `Backend warnings` у `hermes lsp status`**

Деякі сервери є тонкими обгортками навколо зовнішнього CLI для реальної діагностики — вони успішно стартують і приймають запити, але ніколи не виводять помилки, коли бічний бінарник відсутній. Найпоширеніший випадок — `bash-language-server`, який делегує діагностику `shellcheck`. Коли `hermes lsp status` показує розділ `Backend warnings`, встанови зазначений інструмент через менеджер пакетів ОС:

```
apt install shellcheck      # Debian / Ubuntu
brew install shellcheck     # macOS
scoop install shellcheck    # Windows
```

Те саме попередження записується один раз під час спавну сервера у `~/.hermes/logs/agent.log`.

**Сервер стартує, але ніколи не повертає діагностик**

Перевір `~/.hermes/logs/agent.log` на записи `[agent.lsp.client]` — туди потрапляє як stderr сервера мови, так і помилки протоколу. Деякі сервери (особливо rust‑analyzer) потребують завершити проєктний індекс, перш ніж вони почнуть видавати діагностики по окремих файлах; перше редагування після старту сервера може завершитися без діагностик, а наступні їх вже повернуть.

**Сервер впав**

Після падіння сервер додається до набору «broken» і не буде повторно викликаний протягом поточної сесії. Запусти `hermes lsp restart`, щоб очистити цей набір; наступне редагування перезапустить його.

**Редагування файлу поза будь‑яким git‑репозиторієм**

За замовчуванням LSP працює лише всередині git‑репозиторію. Якщо проєкт ще не ініціалізовано, виконай `git init`, щоб увімкнути діагностику LSP. Інакше застосовується запасний (варіант) лише синтаксичної перевірки.