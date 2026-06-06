---
title: "Jupyter Live Kernel — ітеративний Python через живий Jupyter kernel (hamelnb)"
sidebar_label: "Jupyter Live Kernel"
description: "Ітеративний Python через живий ядро Jupyter (hamelnb)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Jupyter Live Kernel

Ітеративний Python через живий Jupyter kernel (hamelnb).

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/data-science/jupyter-live-kernel` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `jupyter`, `notebook`, `repl`, `data-science`, `exploration`, `iterative` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# Jupyter Live Kernel (hamelnb)

Надає **становий Python REPL** через живий Jupyter kernel. Змінні зберігаються між виконаннями. Використовуй це замість `execute_code`, коли потрібно поступово будувати стан, досліджувати API, інспектувати DataFrames або ітерувати складний код.

## Коли використовувати цю навичку vs інші інструменти

| Tool | Use When |
|------|----------|
| **This skill** | Ітеративне дослідження, стан між кроками, data science, ML, «давай спробую це і перевірю» |
| `execute_code` | Одноразові скрипти, які потребують доступу до інструментів hermes (web_search, file ops). Без стану. |
| `terminal` | Команди оболонки, збірки, інсталяції, git, управління процесами |

**Rule of thumb:** Якщо ти б використав Jupyter notebook для завдання, використай цю навичку.

## Передумови

1. **uv** має бути встановлений (перевір: `which uv`)
2. **JupyterLab** має бути встановлений: `uv tool install jupyterlab`
3. Сервер Jupyter має бути запущений (дивись розділ Setup нижче)

## Налаштування

Розташування скрипту hamelnb:
```
SCRIPT="$HOME/.agent-skills/hamelnb/skills/jupyter-live-kernel/scripts/jupyter_live_kernel.py"
```

Якщо ще не клоновано:
```
git clone https://github.com/hamelsmu/hamelnb.git ~/.agent-skills/hamelnb
```

### Запуск JupyterLab

Перевір, чи вже працює сервер:
```
uv run "$SCRIPT" servers
```

Якщо серверів не знайдено, запусти один:
```
jupyter-lab --no-browser --port=8888 --notebook-dir=$HOME/notebooks \
  --IdentityProvider.token='' --ServerApp.password='' > /tmp/jupyter.log 2>&1 &
sleep 3
```

Примітка: Токен/пароль вимкнено для локального доступу агента. Сервер працює без графічного інтерфейсу.

### Створення ноутбука для використання REPL

Якщо потрібен лише REPL (без існуючого ноутбука), створи мінімальний файл ноутбука:
```
mkdir -p ~/notebooks
```
Запиши мінімальний JSON‑файл `.ipynb` з однією порожньою клітинкою коду, потім запусти сесію kernel через Jupyter REST API:
```
curl -s -X POST http://127.0.0.1:8888/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"path":"scratch.ipynb","type":"notebook","name":"scratch.ipynb","kernel":{"name":"python3"}}'
```

## Основний робочий процес

Усі команди повертають структурований JSON. Завжди використовуйте `--compact`, щоб заощадити токени.

### 1. Виявлення серверів і ноутбуків

```
uv run "$SCRIPT" servers --compact
uv run "$SCRIPT" notebooks --compact
```

### 2. Виконання коду (основна операція)

```
uv run "$SCRIPT" execute --path <notebook.ipynb> --code '<python code>' --compact
```

Стан зберігається між викликами `execute`. Змінні, імпорти, об’єкти залишаються.

Багаторядковий код працює з quoting `$'...'`:
```
uv run "$SCRIPT" execute --path scratch.ipynb --code $'import os\nfiles = os.listdir(".")\nprint(f"Found {len(files)} files")' --compact
```

### 3. Інспекція живих змінних

```
uv run "$SCRIPT" variables --path <notebook.ipynb> list --compact
uv run "$SCRIPT" variables --path <notebook.ipynb> preview --name <varname> --compact
```

### 4. Редагування клітинок ноутбука

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

### 5. Верифікація (перезапуск + запуск всього)

Використовуй лише коли користувач просить чисту верифікацію або потрібно підтвердити, що ноутбук виконується від початку до кінця:

```
uv run "$SCRIPT" restart-run-all --path <notebook.ipynb> --save-outputs --compact
```

## Практичні поради з досвіду

1. **Перше виконання після запуску сервера може завершитися тайм‑аутом** — kernel потребує моменту для ініціалізації. Якщо отримав тайм‑аут, просто повтори запит.

2. **Python kernel – це Python JupyterLab** — пакети мають бути встановлені в цьому середовищі. Якщо потрібні додаткові пакети, спочатку встанови їх у середовище інструменту JupyterLab.

3. **Прапорець `--compact` економить значну кількість токенів** — завжди використовуйте його. Вивід JSON може бути дуже довгим без нього.

4. **Для чистого використання REPL** створи файл `scratch.ipynb` і не займайся редагуванням клітинок. Просто використовуйте `execute` багаторазово.

5. **Порядок аргументів має значення** — прапорці підкоманд, такі як `--path`, йдуть ПЕРЕД під‑підкомандою. Наприклад: `variables --path nb.ipynb list`, а не `variables list --path nb.ipynb`.

6. **Якщо сесія ще не існує**, її потрібно запустити через REST API (дивись розділ Setup). Інструмент не може виконувати без живої сесії kernel.

7. **Помилки повертаються у вигляді JSON** з трасуванням стека — читай поля `ename` та `evalue`, щоб зрозуміти, що пішло не так.

8. **Інколи веб‑сокет тайм‑аутить** — деякі операції можуть завершитися тайм‑аутом при першій спробі, особливо після перезапуску kernel. Спробуй ще раз перед ескалацією.

## Тайм‑аут за замовчуванням

Скрипт має тайм‑аут 30 секунд за замовчуванням на кожне виконання. Для довготривалих операцій передай `--timeout 120`. Використовуй щедрі тайм‑ауты (60+ сек) для початкового налаштування або важких обчислень.