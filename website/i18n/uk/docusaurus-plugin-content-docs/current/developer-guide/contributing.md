---
sidebar_position: 4
title: "Внесок"
description: "Як внести свій внесок у Hermes Agent — налаштування розробки, стиль коду, процес PR"
---

# Внесок

Дякуємо за внесок у Hermes Agent! У цьому посібнику розглянуто налаштування середовища розробки, ознайомлення з кодовою базою та процес злиття твого PR.

## Пріоритети внесків

Ми цінуємо внески у такому порядку:

1. **Виправлення помилок** — збої, неправильна поведінка, втрата даних
2. **Крос‑платформенна сумісність** — macOS, різні дистрибутиви Linux, WSL2
3. **Посилення безпеки** — ін’єкція команд оболонки, prompt injection, обходи шляхів
4. **Продуктивність і стійкість** — логіка повторних спроб, обробка помилок, плавне деградування
5. **Нові навички** — широко корисні (див. [Creating Skills](creating-skills.md))
6. **Нові інструменти** — рідко потрібні; більшість можливостей мають бути навичками
7. **Документація** — виправлення, уточнення, нові приклади

## Типові шляхи внеску

- Створюєш власний/локальний інструмент без зміни ядра Hermes? Почни з [Build a Hermes Plugin](../guides/build-a-hermes-plugin.md)
- Створюєш новий вбудований інструмент для самого Hermes? Почни з [Adding Tools](./adding-tools.md)
- Створюєш нову навичку? Почни з [Creating Skills](./creating-skills.md)
- Створюєш нового провайдера інференції? Почни з [Adding Providers](./adding-providers.md)

## Налаштування розробки

### Передумови

| Вимога | Примітки |
|--------|----------|
| **Git** | Підтримка `--recurse-submodules` та встановлене розширення `git-lfs` |
| **Python 3.11+** | `uv` встановить його, якщо відсутній |
| **uv** | Швидкий менеджер пакетів Python ([install](https://docs.astral.sh/uv/)) |
| **Node.js 20+** | Необов’язково — потрібен для інструментів браузера та мосту WhatsApp (відповідає `engines` у кореневому `package.json`) |

### Клонування та встановлення

```bash
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# Create venv with Python 3.11
uv venv venv --python 3.11
export VIRTUAL_ENV="$(pwd)/venv"

# Install with all extras (messaging, cron, CLI menus, dev tools)
uv pip install -e ".[all,dev]"

# Optional: browser tools
npm install
```

### Конфігурація для розробки

```bash
mkdir -p ~/.hermes/{cron,sessions,logs,memories,skills}
cp cli-config.yaml.example ~/.hermes/config.yaml
touch ~/.hermes/.env

# Add at minimum an LLM provider key:
echo 'OPENROUTER_API_KEY=sk-or-v1-your-key' >> ~/.hermes/.env
```

### Запуск

```bash
# Symlink for global access
mkdir -p ~/.local/bin
ln -sf "$(pwd)/venv/bin/hermes" ~/.local/bin/hermes

# Verify
hermes doctor
hermes chat -q "Hello"
```

### Запуск тестів

```bash
pytest tests/ -v
```

## Стиль коду

- **PEP 8** з практичними винятками (жодних жорстких обмежень довжини рядка)
- **Коментарі**: лише коли пояснюється неочевидний намір, компроміси або особливості API
- **Обробка помилок**: ловити конкретні виключення. Використовувати `logger.warning()`/`logger.error()` з `exc_info=True` для неочікуваних помилок
- **Крос‑платформеність**: ніколи не припускати Unix (див. нижче)
- **Шляхи, безпечні для профілю**: не хардкодити `~/.hermes` — використовуй `get_hermes_home()` з `hermes_constants` для кодових шляхів та `display_hermes_home()` для повідомлень користувачеві. Див. [AGENTS.md](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md#profiles-multi-instance-support) для повних правил.

## Крос‑платформенна сумісність

Hermes офіційно підтримує **Linux, macOS, WSL2 та нативний Windows (рання бета — через встановлення PowerShell)**. Нативний Windows використовує Git Bash (з [Git for Windows](https://git-scm.com/download/win)) для команд оболонки. Декілька функцій потребують примітивів ядра POSIX і доступні лише частково: вбудована панель PTY‑терміналу (`/chat` tab) працює лише в WSL2. Шлях для нативного Windows новий і швидко розвивається — якщо ти працюєш переважно у Windows, очікуй «грубі» місця та їх виправлення.

При внесенні коду пам’ятай про такі правила:

- **Не додавай небезпечні посилання на `signal.SIGKILL`.** Він не визначений у Windows. Або маршрутизуй через `gateway.status.terminate_pid(pid, force=True)` (централізований примітив, що виконує `taskkill /T /F` у Windows та `SIGKILL` у POSIX), або використай запасний варіант `getattr(signal, "SIGKILL", signal.SIGTERM)`.
- **Лови `OSError` разом з `ProcessLookupError` у викликах `os.kill(pid, 0)`.** У Windows під час спроби вбити вже неіснуючий PID піднімається `OSError` (WinError 87, «parameter is incorrect») замість `ProcessLookupError`.
- **Не примушуй термінал до POSIX‑семантики.** `os.setsid`, `os.killpg`, `os.getpgid`, `os.fork` піднімають виключення у Windows — огороди їх умовою `if sys.platform != "win32":` або `if os.name != "nt":`.
- **Відкривай файли з явним `encoding="utf-8"`.** За замовчуванням у Windows використовується системна локаль (часто cp1252), що призводить до «мозайки» або краху при роботі з нелатинським текстом.
- **Використовуй `pathlib.Path` / `os.path.join` — ніколи не конкатенуй рядки вручну за допомогою `/`.** Це важливо не лише для рядків, які повертає ОС, а й для рядків, які ми формуємо для підпроцесів.

Ключові шаблони:

### 1. `termios` і `fcntl` — лише Unix

Завжди ловити і `ImportError`, і `NotImplementedError`:

```python
try:
    from simple_term_menu import TerminalMenu
    menu = TerminalMenu(options)
    idx = menu.show()
except (ImportError, NotImplementedError):
    # Fallback: numbered menu
    for i, opt in enumerate(options):
        print(f"  {i+1}. {opt}")
    idx = int(input("Choice: ")) - 1
```

### 2. Кодування файлів

Деякі середовища можуть зберігати `.env` у не‑UTF‑8 кодуванні:

```python
try:
    load_dotenv(env_path)
except UnicodeDecodeError:
    load_dotenv(env_path, encoding="latin-1")
```

### 3. Управління процесами

`os.setsid()`, `os.killpg()` та обробка сигналів різняться між платформами:

```python
import platform
if platform.system() != "Windows":
    kwargs["preexec_fn"] = os.setsid
```

### 4. Роздільники шляхів

Використовуй `pathlib.Path` замість конкатенації рядків через `/`.

## Зауваження щодо безпеки

Hermes має доступ до терміналу. Безпека важлива.

### Існуючі захисти

| Шар | Реалізація |
|-----|------------|
| **Пайпінг пароля sudo** | Використовує `shlex.quote()` для запобігання ін’єкції оболонки |
| **Виявлення небезпечних команд** | Регекс‑шаблони у `tools/approval.py` з процесом схвалення користувачем |
| **Cron‑prompt injection** | Сканер блокує шаблони, що переважають інструкції |
| **Білий список запису** | Захищені шляхи резолвляться через `os.path.realpath()` для запобігання обходу через симлінки |
| **Захист навичок** | Сканер безпеки для навичок, встановлених у хабі |
| **Пісочниця виконання коду** | Дочірній процес запускається без API‑ключів |
| **Посилення контейнера** | Docker: усі можливості відключені, без підвищення привілеїв, обмеження PID |

### Внесення коду, чутливого до безпеки

- Завжди використовуйте `shlex.quote()` при підстановці користувацького вводу у команди оболонки
- Перед перевірками доступу розв’язуйте симлінки за допомогою `os.path.realpath()`
- Не логувати секрети
- Ловити широкі виключення навколо виконання інструменту
- Тестувати на всіх платформах, якщо зміна стосується шляхів файлів або процесів

## Процес Pull Request

### Іменування гілки

```
fix/description        # Bug fixes
feat/description       # New features
docs/description       # Documentation
test/description       # Tests
refactor/description   # Code restructuring
```

### Перед поданням

1. **Запусти тести**: `pytest tests/ -v`
2. **Тестування вручну**: Запусти `hermes` і перевір шлях коду, який ти змінив
3. **Перевір вплив на крос‑платформеність**: Подумай про macOS та різні дистрибутиви Linux
4. **Тримай PR сфокусованими**: Один логічний змін у кожному PR

### Опис PR

Включи:
- **Що** змінено і **чому**
- **Як протестувати**
- **На яких платформах** ти тестував
- Посилання на пов’язані issue

### Повідомлення комітів

Ми використовуємо [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

| Тип | Використання |
|-----|--------------|
| `fix` | Виправлення помилок |
| `feat` | Нові функції |
| `docs` | Документація |
| `test` | Тести |
| `refactor` | Переструктуризація коду |
| `chore` | Build, CI, оновлення залежностей |

Області: `cli`, `gateway`, `tools`, `skills`, `agent`, `install`, `whatsapp`, `security`

Приклади:
```
fix(cli): prevent crash in save_config_value when model is a string
feat(gateway): add WhatsApp multi-user session isolation
fix(security): prevent shell injection in sudo password piping
```

## Повідомлення про проблеми

- Використовуй [GitHub Issues](https://github.com/NousResearch/hermes-agent/issues)
- Включай: ОС, версію Python, версію Hermes (`hermes version`), повний стек трасування помилки
- Опис кроків для відтворення
- Перевір наявність схожих issue перед створенням дублювання
- Для вразливостей безпеки, будь ласка, повідомляй конфіденційно

## Спільнота

- **Discord**: [discord.gg/NousResearch](https://discord.gg/NousResearch)
- **GitHub Discussions**: Для пропозицій дизайну та архітектурних обговорень
- **Skills Hub**: Завантажуй спеціалізовані навички та ділись ними з спільнотою

## Ліцензія

Вносячи зміни, ти погоджуєшся, що твій внесок буде ліцензовано під [MIT License](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE).