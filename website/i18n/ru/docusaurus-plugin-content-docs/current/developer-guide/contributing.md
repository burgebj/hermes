---
sidebar_position: 4
title: "Вклад"
description: "Как внести вклад в Hermes Agent — настройка разработки, стиль кода, процесс PR"
---

# Вклад

Спасибо за вклад в Hermes Agent! Это руководство охватывает настройку среды разработки, понимание кодовой базы и процесс слияния твоего PR.

## Приоритеты вклада

Мы ценим вклады в следующем порядке:

1. **Исправления багов** — краши, некорректное поведение, потеря данных
2. **Кроссплатформенная совместимость** — macOS, различные дистрибутивы Linux, WSL2
3. **Укрепление безопасности** — внедрение команд оболочки, внедрение prompt‑injection, обход путей
4. **Производительность и надёжность** — логика повторных попыток, обработка ошибок, плавное деградирование
5. **Новые навыки** — широко полезные (см. [Creating Skills](creating-skills.md))
6. **Новые инструменты** — редко нужны; большинство возможностей должны быть навыками
7. **Документация** — исправления, уточнения, новые примеры

## Общие пути вклада

- Создаёшь кастомный/локальный инструмент без изменения ядра Hermes? Начни с [Build a Hermes Plugin](../guides/build-a-hermes-plugin.md)
- Создаёшь новый встроенный основной инструмент для самого Hermes? Начни с [Adding Tools](./adding-tools.md)
- Создаёшь новый навык? Начни с [Creating Skills](./creating-skills.md)
- Создаёшь нового провайдера вывода? Начни с [Adding Providers](./adding-providers.md)

## Настройка разработки

### Требования

| Требование | Примечания |
|------------|------------|
| **Git** | С поддержкой `--recurse-submodules` и установленным расширением `git-lfs` |
| **Python 3.11+** | `uv` установит его при отсутствии |
| **uv** | Быстрый менеджер пакетов Python ([install](https://docs.astral.sh/uv/)) |
| **Node.js 20+** | Необязательно — нужен для браузерных инструментов и моста WhatsApp (соответствует `engines` в корневом `package.json`) |

### Клонирование и установка

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

### Конфигурация для разработки

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

### Запуск тестов

```bash
pytest tests/ -v
```

## Стиль кода

- **PEP 8** с практическими исключениями (нет строгого ограничения длины строк)
- **Комментарии**: только когда объясняешь неочевидный замысел, компромиссы или особенности API
- **Обработка ошибок**: лови конкретные исключения. Используй `logger.warning()`/`logger.error()` с `exc_info=True` для неожиданных ошибок
- **Кроссплатформенность**: никогда не предполагая Unix (см. ниже)
- **Безопасные пути профиля**: никогда не хардкодь `~/.hermes` — используй `get_hermes_home()` из `hermes_constants` для кодовых путей и `display_hermes_home()` для сообщений пользователю. См. [AGENTS.md](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md#profiles-multi-instance-support) для полного набора правил.

## Кроссплатформенная совместимость

Hermes официально поддерживает **Linux, macOS, WSL2 и нативный Windows (ранняя бета — через установку PowerShell)**. Нативный Windows использует Git Bash (из [Git for Windows](https://git-scm.com/download/win)) для команд оболочки. Некоторые функции требуют примитивов ядра POSIX и ограничены: встроенная панель терминала PTY в дашборде (`/chat`‑вкладка) доступна только в WSL2. Путь нативного Windows новый и быстро развивается — если ты работаешь преимущественно в Windows, ожидай шероховатости и их исправление.

При внесении кода учитывай следующие правила:

- **Не добавляй необработанные ссылки на `signal.SIGKILL`.** Он не определён в Windows. Либо маршрутизируй через `gateway.status.terminate_pid(pid, force=True)` (централизованный примитив, который вызывает `taskkill /T /F` в Windows и `SIGKILL` в POSIX), либо используй запасной вариант `getattr(signal, "SIGKILL", signal.SIGTERM)`.
- **Лови `OSError` вместе с `ProcessLookupError` при проверках `os.kill(pid, 0)`.** В Windows вместо `ProcessLookupError` бросается `OSError` (WinError 87, «параметр некорректен») для уже завершённого PID.
- **Не принуждай терминал к семантике POSIX.** `os.setsid`, `os.killpg`, `os.getpgid`, `os.fork` бросают исключения в Windows — ограждай их условием `if sys.platform != "win32":` или `if os.name != "nt":`.
- **Открывай файлы с явным `encoding="utf-8"`.** По умолчанию в Windows используется системная кодировка (часто cp1252), что приводит к «мойдже» или падениям при работе с нелатинским текстом.
- **Используй `pathlib.Path` / `os.path.join` — никогда не конкатенируй строки с `/`.** Это важно не только для строк, получаемых от ОС, но и для тех, которые ты формируешь для передачи в подпроцессы.

### Ключевые шаблоны

#### 1. `termios` и `fcntl` — только для Unix

Всегда лови как `ImportError`, так и `NotImplementedError`:

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

#### 2. Кодировка файлов

Некоторые окружения могут сохранять файлы `.env` в кодировках, отличных от UTF‑8:

```python
try:
    load_dotenv(env_path)
except UnicodeDecodeError:
    load_dotenv(env_path, encoding="latin-1")
```

#### 3. Управление процессами

`os.setsid()`, `os.killpg()` и обработка сигналов различаются между платформами:

```python
import platform
if platform.system() != "Windows":
    kwargs["preexec_fn"] = os.setsid
```

#### 4. Разделители путей

Используй `pathlib.Path` вместо конкатенации строк через `/`.

## Соображения безопасности

Hermes имеет доступ к терминалу. Безопасность важна.

### Существующие защиты

| Слой | Реализация |
|------|------------|
| **Пайпинг пароля sudo** | Использует `shlex.quote()` для предотвращения внедрения команд оболочки |
| **Обнаружение опасных команд** | Регулярные выражения в `tools/approval.py` с пользовательским подтверждением |
| **Cron‑внедрение prompt‑injection** | Сканер блокирует паттерны переопределения инструкций |
| **Запрет записи** | Защищённые пути разрешаются через `os.path.realpath()` для предотвращения обхода через симлинки |
| **Защита навыков** | Сканер безопасности для навыков, установленных из хаба |
| **Песочница выполнения кода** | Дочерний процесс запускается без API‑ключей |
| **Укрепление контейнера** | Docker: все возможности сняты, без повышения привилегий, ограничения PID |

### Вклад кода, чувствительного к безопасности

- Всегда используй `shlex.quote()` при подстановке пользовательского ввода в команды оболочки
- Разрешай симлинки через `os.path.realpath()` перед проверками контроля доступа
- Не логируй секреты
- Лови широкие исключения вокруг выполнения инструмента
- Тестируй на всех платформах, если изменение затрагивает пути файлов или процессы

## Процесс Pull Request

### Именование ветки

```
fix/description        # Bug fixes
feat/description       # New features
docs/description       # Documentation
test/description       # Tests
refactor/description   # Code restructuring
```

### Перед отправкой

1. **Запусти тесты**: `pytest tests/ -v`
2. **Тестируй вручную**: запусти `hermes` и пройди изменённый код
3. **Проверь кроссплатформенное влияние**: учти macOS и разные дистрибутивы Linux
4. **Сохраняй PR сфокусированными**: один логический набор изменений в каждом PR

### Описание PR

Включи:
- **Что** изменилось и **почему**
- **Как протестировать**
- **На каких платформах** ты тестировал
- Ссылку на связанные задачи

### Сообщения коммитов

Мы используем [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

| Тип | Для чего |
|-----|----------|
| `fix` | Исправления багов |
| `feat` | Новые возможности |
| `docs` | Документация |
| `test` | Тесты |
| `refactor` | Реструктуризация кода |
| `chore` | Сборка, CI, обновления зависимостей |

Области: `cli`, `gateway`, `tools`, `skills`, `agent`, `install`, `whatsapp`, `security`

Примеры:

```
fix(cli): prevent crash in save_config_value when model is a string
feat(gateway): add WhatsApp multi-user session isolation
fix(security): prevent shell injection in sudo password piping
```

## Сообщение об ошибках

- Используй [GitHub Issues](https://github.com/NousResearch/hermes-agent/issues)
- Укажи: ОС, версию Python, версию Hermes (`hermes version`), полный стек ошибки
- Описание шагов воспроизведения
- Проверь существующие задачи, чтобы не создавать дубликаты
- Для уязвимостей безопасности, пожалуйста, сообщай конфиденциально

## Сообщество

- **Discord**: [discord.gg/NousResearch](https://discord.gg/NousResearch)
- **GitHub Discussions**: для предложений дизайна и обсуждений архитектуры
- **Skills Hub**: загружай специализированные навыки и делись ими с сообществом

## Лицензия

Внося вклад, ты соглашаешься, что твой код будет лицензирован под [MIT License](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE).