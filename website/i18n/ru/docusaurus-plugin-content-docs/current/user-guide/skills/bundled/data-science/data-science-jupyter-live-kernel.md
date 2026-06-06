---
title: "Jupyter Live Kernel — Итеративный Python через живое ядро Jupyter (hamelnb)"
sidebar_label: "Jupyter Live Kernel"
description: "Итеративный Python через живое ядро Jupyter (hamelnb)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Jupyter Live Kernel

Итеративный Python через живое ядро Jupyter (hamelnb).

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/data-science/jupyter-live-kernel` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `jupyter`, `notebook`, `repl`, `data-science`, `exploration`, `iterative` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Jupyter Live Kernel (hamelnb)

Предоставляет **состоящий Python REPL** через живое ядро Jupyter. Переменные сохраняются между выполнениями. Используй это вместо `execute_code`, когда нужно постепенно наращивать состояние, исследовать API, инспектировать DataFrames или итеративно работать со сложным кодом.

## Когда использовать это вместо других инструментов

| Инструмент | Когда использовать |
|------|----------|
| **Этот навык** | Итеративное исследование, состояние между шагами, наука о данных, ML, «давай попробуем и проверим» |
| `execute_code` | Одноразовые скрипты, требующие доступа к инструментам hermes (web_search, file ops). Без состояния. |
| `terminal` | Команды оболочки, сборки, установки, git, управление процессами |

**Практическое правило:** Если ты бы использовал Jupyter notebook для задачи, используй этот навык.

## Предпосылки

1. **uv** должен быть установлен (проверь: `which uv`)
2. **JupyterLab** должен быть установлен: `uv tool install jupyterlab`
3. Должен быть запущен сервер Jupyter (см. раздел Настройка ниже)

## Настройка

Расположение скрипта hamelnb:
```
SCRIPT="$HOME/.agent-skills/hamelnb/skills/jupyter-live-kernel/scripts/jupyter_live_kernel.py"
```

Если репозиторий ещё не клонирован:
```
git clone https://github.com/hamelsmu/hamelnb.git ~/.agent-skills/hamelnb
```

### Запуск JupyterLab

Проверь, запущен ли уже сервер:
```
uv run "$SCRIPT" servers
```

Если серверов не найдено, запусти один:
```
jupyter-lab --no-browser --port=8888 --notebook-dir=$HOME/notebooks \
  --IdentityProvider.token='' --ServerApp.password='' > /tmp/jupyter.log 2>&1 &
sleep 3
```

Примечание: токен/пароль отключены для локального доступа агента. Сервер работает в headless‑режиме.

### Создание ноутбука для использования REPL

Если нужен только REPL (нет существующего ноутбука), создай минимальный файл ноутбука:
```
mkdir -p ~/notebooks
```
Запиши минимальный JSON‑файл `.ipynb` с одной пустой ячейкой кода, затем запусти сессию ядра через Jupyter REST API:
```
curl -s -X POST http://127.0.0.1:8888/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"path":"scratch.ipynb","type":"notebook","name":"scratch.ipynb","kernel":{"name":"python3"}}'
```

## Основной рабочий процесс

Все команды возвращают структурированный JSON. Всегда используй `--compact`, чтобы экономить токены.

### 1. Обнаружение серверов и ноутбуков

```
uv run "$SCRIPT" servers --compact
uv run "$SCRIPT" notebooks --compact
```

### 2. Выполнение кода (основная операция)

```
uv run "$SCRIPT" execute --path <notebook.ipynb> --code '<python code>' --compact
```

Состояние сохраняется между вызовами `execute`. Переменные, импорты, объекты остаются.

Многострочный код работает с кавычками `$'...'`:
```
uv run "$SCRIPT" execute --path scratch.ipynb --code $'import os\nfiles = os.listdir(".")\nprint(f"Found {len(files)} files")' --compact
```

### 3. Инспекция живых переменных

```
uv run "$SCRIPT" variables --path <notebook.ipynb> list --compact
uv run "$SCRIPT" variables --path <notebook.ipynb> preview --name <varname> --compact
```

### 4. Редактирование ячеек ноутбука

```
# View current cells
uv run "$SCRIPT" contents --path <notebook.ipynb> --compact

# Insert a new cell
uv run "$SCRIPT" edit --path <notebook.ipynb> insert \
  --at-index <N> --cell-type code --source '<code>' --compact

# Replace cell source (use cell-id from contents output)
uv run "$SCRIPT" edit --path <notebook.ipynb> replace-source \
  --cell-id <id> --source '<new code>' --compact

# Delete a cell
uv run "$SCRIPT" edit --path <notebook.ipynb> delete --cell-id <id> --compact
```

### 5. Проверка (перезапуск + запуск всех ячеек)

Используй только когда пользователь просит чистую проверку или тебе нужно убедиться, что ноутбук выполняется от начала до конца:

```
uv run "$SCRIPT" restart-run-all --path <notebook.ipynb> --save-outputs --compact
```

## Практические советы из опыта

1. **Первое выполнение после запуска сервера может завершиться таймаутом** — ядру требуется немного времени для инициализации. Если получен таймаут, просто повтори запрос.

2. **Python ядра — это Python JupyterLab** — пакеты должны устанавливаться в этой среде. Если нужны дополнительные пакеты, установи их сначала в окружение инструмента JupyterLab.

3. **Флаг `--compact` экономит значительное количество токенов** — всегда используй его. Вывод JSON может быть очень объёмным без него.

4. **Для чистого использования REPL** создай `scratch.ipynb` и не трать время на редактирование ячеек. Просто многократно вызывай `execute`.

5. **Порядок аргументов важен** — флаги подкоманды, такие как `--path`, идут ПЕРЕД под‑подкомандой. Например: `variables --path nb.ipynb list`, а не `variables list --path nb.ipynb`.

6. **Если сессия ещё не существует**, её нужно запустить через REST API (см. раздел Настройка). Инструмент не может выполнять команды без живой сессии ядра.

7. **Ошибки возвращаются в виде JSON** с трассировкой стека — читай поля `ename` и `evalue`, чтобы понять, что пошло не так.

8. **Редкие таймауты веб‑сокетов** — некоторые операции могут завершиться таймаутом при первой попытке, особенно после перезапуска ядра. Повтори запрос один раз перед эскалацией.

## Значения таймаутов по умолчанию

Скрипт имеет таймаут 30 секунд по умолчанию на каждое выполнение. Для длительных операций передавай `--timeout 120`. Используй более длительные таймауты (60 +) для начальной настройки или тяжёлых вычислений.