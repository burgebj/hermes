---
sidebar_position: 16
title: "LSP — Семантическая диагностика"
description: "Настоящие серверы языков (pyright, gopls, rust-analyzer, …) подключены к проверке lint после записи, используемой функциями write_file и patch."
---

# Протокол серверов языка (LSP)

Hermes запускает полноценные серверы языка — pyright, gopls, rust-analyzer,
typescript-language-server, clangd и ~20 других — как фоновые подпроцессы и передаёт их семантическую диагностику в проверку post‑write, используемую `write_file` и `patch`. Когда агент редактирует файл, он видит точно те ошибки, которые внесло редактирование — не только синтаксические ошибки, но **ошибки типов, неопределённые имена, отсутствующие импорты и проектные семантические проблемы**, обнаруженные сервером языка.

Это та же архитектура, которую используют топ‑уровневые кодирующие агенты. Hermes поставляется в самодостаточном виде: не требуется хост‑редактор, плагины или отдельный демон.

## Когда запускается LSP

LSP активируется только при **обнаружении git‑рабочей области**. Когда рабочий каталог агента (или редактируемый файл) находятся внутри git‑репозитория, LSP запускается для этой области. Если ни то, ни другое не находится в git‑репозитории, LSP остаётся неактивным — это полезно для шлюзов обмена сообщениями, где cwd — домашний каталог пользователя и нет проекта для диагностики.

Проверка происходит в два слоя: сначала синтаксическая проверка в процессе (микросекунды), затем диагностика LSP, если синтаксис чист. Нестабильный или отсутствующий сервер языка никогда не может прервать запись — каждый путь неудачи LSP тихо переходит к результату только синтаксической проверки.

Конкретно, при каждом успешном `write_file` или `patch`:

1. Hermes фиксирует базовый набор текущих диагностик для файла.
2. Выполняет запись.
3. Снова запрашивает сервер языка, отфильтровывает диагностики, уже присутствующие в базовом наборе, и выводит только новые.

Агент видит вывод вроде:

```
{
  "bytes_written": 42,
  "dirs_created": false,
  "lint": {"status": "ok", "output": ""},
  "lsp_diagnostics": "LSP diagnostics introduced by this edit:\n<diagnostics file=\"/path/to/foo.py\">\nERROR [42:5] Cannot find name 'foo' [reportUndefinedVariable] (Pyright)\nERROR [50:1] Argument of type \"str\" is not assignable to \"int\" [reportArgumentType] (Pyright)\n</diagnostics>"
}
```

Поле `lint` содержит результат синтаксической проверки (микросекунды внутри процесса через `ast.parse`, `json.loads` и т.д.); поле `lsp_diagnostics` — семантическую диагностику от реального сервера языка. Два канала, независимые сигналы — агент видит файл без синтаксических ошибок, но с семантическими проблемами как ``lint: ok`` плюс заполненный ``lsp_diagnostics``.

## Поддерживаемые языки

| Язык | Сервер | Авто‑установка |
|------|--------|----------------|
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

Для записей «manual» сервер устанавливается через любой подходящий инструмент управления цепочкой (rustup, ghcup, opam, brew и т.п.). Hermes автоматически обнаруживает бинарник в PATH или в `<HERMES_HOME>/lsp/bin/`.

Некоторые серверы устанавливаются вместе с зависимостью, которую npm не может автоматически подтянуть. Текущий пример — `typescript-language-server`, который требует SDK `typescript`, импортируемый из того же дерева `node_modules`. Hermes устанавливает оба пакета одновременно, когда ты выполняешь `hermes lsp install typescript` или авто‑установка срабатывает при первом использовании.

## CLI

```
hermes lsp status          # service state + per-server install status
hermes lsp list            # registry, optionally --installed-only
hermes lsp install <id>    # eagerly install one server
hermes lsp install-all     # try every server with a known recipe
hermes lsp restart         # tear down running clients
hermes lsp which <id>      # print resolved binary path
```

`hermes lsp status` — лучшее отправное место: он показывает, какие языки получат семантическую диагностику сегодня и какие требуют установки бинарника.

## Конфигурация

Стандартные настройки подходят для типовых конфигураций; ничего настраивать не нужно, если бинарники находятся в PATH.

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

### Параметры сервера

* `disabled: true` — полностью отключить этот сервер, даже если его расширения совпадают с файлом.
* `command: [bin, ...args]` — задать путь к пользовательскому бинарнику. Обходит авто‑установку.
* `env: {KEY: value}` — дополнительные переменные окружения, передаваемые в порождённый процесс.
* `initialization_options: {...}` — объединяется с полезной нагрузкой `initializationOptions` LSP, отправляемой в ходе рукопожатия `initialize`. Специфично для сервера; см. документацию конкретного сервера языка.

## Места установки

При `install_strategy: auto` Hermes помещает бинарники в `<HERMES_HOME>/lsp/bin/`. Пакеты NPM попадают в `<HERMES_HOME>/lsp/node_modules/` с символическими ссылками на bin‑файлы на уровень выше. Бинарники Go берутся из `go install` с `GOBIN`, указывающим на директорию staging.

Никакие файлы никогда не устанавливаются в `/usr/local/`, `~/.local/` или любое другое общее место — директория staging полностью принадлежит Hermes и удаляется при сбросе профиля.

## Характеристики производительности

Серверы LSP **лениво запускаются** при первом использовании. Редактирование Python‑файла в проекте, где ещё не было `.py`‑трафика, запускает pyright; запуск занимает 1‑3 секунды для большинства серверов (rust-analyzer может занять 10 секунд и более в холодном проекте). Последующие правки в той же рабочей области переиспользуют уже запущенный сервер.

Слой LSP добавляет несколько миллисекунд к чистым записям, когда диагностика не выдаётся. Когда диагностика появляется, время ожидания ограничено `wait_timeout` секундами — обычно сервер отвечает за десятки миллисекунд для pyright/tsserver и за несколько секунд для rust-analyzer во время индексации.

Серверы остаются живыми, пока работает процесс Hermes. Нет тайм‑аута простоя — перезапуск индекса сервера при каждой записи стоил бы намного дороже, чем удерживание демона.

## Отключение

Установи `lsp.enabled: false` в `config.yaml`, чтобы отключить всю подсистему. Пост‑записная проверка переходит к синтаксической проверке в процессе (`ast.parse` для Python, `json.loads` для JSON и т.д.), которая остаётся неизменной по сравнению с предыдущими версиями.

Чтобы отключить отдельный язык, не выключая весь слой:

```yaml
lsp:
  servers:
    rust-analyzer:
      disabled: true
```

## Устранение неполадок

**`hermes lsp status` показывает сервер как «missing»**
Бинарник отсутствует в PATH и в `<HERMES_HOME>/lsp/bin/`. Выполни `hermes lsp install <server_id>`, чтобы попытаться выполнить авто‑установку, или установи бинарник вручную через обычный инструмент цепочки языка.

**Раздел `Backend warnings` в `hermes lsp status`**
Некоторые серверы являются тонкими оболочками вокруг внешнего CLI, который действительно выполняет диагностику — они запускаются без ошибок, но не выдают диагностик, если отсутствует вспомогательный бинарник. Наиболее частый пример — `bash-language-server`, который делегирует диагностику `shellcheck`. Когда `hermes lsp status` выводит раздел `Backend warnings`, установи указанный инструмент через менеджер пакетов ОС:

```
apt install shellcheck      # Debian / Ubuntu
brew install shellcheck     # macOS
scoop install shellcheck    # Windows
```

То же предупреждение записывается один раз при запуске сервера в `~/.hermes/logs/agent.log`.

**Сервер стартует, но никогда не возвращает диагностику**
Проверь `~/.hermes/logs/agent.log` на наличие записей `[agent.lsp.client]` — как stderr сервера языка, так и ошибки протокола попадают туда. Некоторые серверы (особенно rust-analyzer) должны завершить проектную индексацию, прежде чем выдавать диагностику по отдельным файлам; первая правка после старта сервера может завершиться без диагностик, а последующие правки уже их получат.

**Сервер упал**
Упавший сервер добавляется в набор «сломанных» и не будет повторно использоваться в течение текущей сессии. Выполни `hermes lsp restart`, чтобы очистить набор; следующая правка запустит сервер заново.

**Редактирование файла вне любого git‑репозитория**
По замыслу LSP работает только внутри git‑репозитория. Если проект ещё не инициализирован, выполни `git init`, чтобы включить диагностику LSP. В противном случае применяется запасной (fallback) вариант проверки только синтаксиса.