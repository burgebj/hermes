---
sidebar_position: 2
title: "Внутреннее устройство ACP"
description: "Как работает ACP‑адаптер: жизненный цикл, сессии, мост событий, одобрения и рендеринг инструментов"
---

# Внутреннее устройство ACP

Адаптер ACP оборачивает синхронный `AIAgent` Hermes в асинхронный сервер JSON‑RPC stdio.

Ключевые файлы реализации:

- `acp_adapter/entry.py`
- `acp_adapter/server.py`
- `acp_adapter/session.py`
- `acp_adapter/events.py`
- `acp_adapter/permissions.py`
- `acp_adapter/tools.py`
- `acp_adapter/auth.py`
- `acp_registry/agent.json`

## Поток запуска

```text
hermes acp / hermes-acp / python -m acp_adapter
  -> acp_adapter.entry.main()
  -> parse --version / --check / --setup before server startup
  -> load ~/.hermes/.env
  -> configure stderr logging
  -> construct HermesACPAgent
  -> acp.run_agent(agent, use_unstable_protocol=True)
```

Путь реестра Zed ACP запускает тот же адаптер через `uvx --from 'hermes-agent[acp]==<version>' hermes-acp`, указывая на релиз `hermes-agent` в PyPI.

`stdout` зарезервирован для транспортировки ACP JSON‑RPC. Читаемые человеком логи выводятся в `stderr`.

## Основные компоненты

### `HermesACPAgent`

`acp_adapter/server.py` реализует протокол агента ACP.

Обязанности:

- инициализация / аутентификация
- методы создания/загрузки/возобновления/форка/списка/отмены сессий
- выполнение подсказок
- переключение модели сессии
- связывание синхронных обратных вызовов `AIAgent` с асинхронными уведомлениями ACP

### `SessionManager`

`acp_adapter/session.py` отслеживает живые сессии ACP.

Каждая сессия хранит:

- `session_id`
- `agent`
- `cwd`
- `model`
- `history`
- `cancel_event`

Менеджер потокобезопасен и поддерживает:

- создание
- получение
- удаление
- форк
- список
- очистку
- обновления `cwd`

### Мост событий

`acp_adapter/events.py` преобразует обратные вызовы `AIAgent` в события ACP `session_update`.

Мостовые обратные вызовы:

- `tool_progress_callback`
- `thinking_callback` (в данный момент установлен в `None` в мосту ACP — рассуждения передаются через `step_callback`)
- `step_callback`

Поскольку `AIAgent` работает в рабочем потоке, а ввод/вывод ACP — в главном цикле событий, мост использует:

```python
asyncio.run_coroutine_threadsafe(...)
```

### Мост разрешений

`acp_adapter/permissions.py` адаптирует опасные запросы подтверждения терминала в запросы разрешений ACP.

Отображение:

- `allow_once` → Hermes `once`
- `allow_always` → Hermes `always`
- варианты отклонения → Hermes `deny`

Тайм‑ауты и сбои моста отклоняют запросы по умолчанию.

### Вспомогательные функции рендеринга инструментов

`acp_adapter/tools.py` сопоставляет инструменты Hermes с типами инструментов ACP и формирует контент для редактора.

Примеры:

- `patch` / `write_file` → диффы файлов
- `terminal` → текст команды оболочки
- `read_file` / `search_files` → предварительный просмотр текста
- большие результаты → усечённые блоки текста для безопасности UI

## Жизненный цикл сессии

```text
new_session(cwd)
  -> create SessionState
  -> create AIAgent(platform="acp", enabled_toolsets=["hermes-acp"])
  -> bind task_id/session_id to cwd override

prompt(..., session_id)
  -> extract text from ACP content blocks
  -> reset cancel event
  -> install callbacks + approval bridge
  -> run AIAgent in ThreadPoolExecutor
  -> update session history
  -> emit final agent message chunk
```

### Отмена

`cancel(session_id)`:

- устанавливает событие отмены сессии
- вызывает `agent.interrupt()`, если он доступен
- заставляет ответ подсказки вернуть `stop_reason="cancelled"`

### Форк

`fork_session()` глубоко копирует историю сообщений в новую живую сессию, сохраняя состояние диалога, но предоставляя форку собственный `session_id` и `cwd`.

## Поведение провайдера/аутентификации

ACP не реализует собственное хранилище учётных данных.

Вместо этого он переиспользует разрешитель среды Hermes:

- `acp_adapter/auth.py`
- `hermes_cli/runtime_provider.py`

Таким образом, ACP рекламирует и использует текущие настроенные провайдер/учётные данные Hermes. Он также всегда рекламирует метод аутентификации настройки терминала (`hermes-setup`, аргументы `--setup`), чтобы клиенты реестра при первом запуске могли открыть интерактивную конфигурацию модели/провайдера Hermes перед началом обычной сессии ACP.

## Привязка рабочей директории

Сессии ACP несут `cwd` редактора.

Менеджер сессий привязывает этот `cwd` к `session_id` ACP через переопределения терминала/файлов в рамках задачи, поэтому инструменты файлов и терминала работают относительно рабочего пространства редактора.

## Дублирование вызовов инструментов с одинаковым именем

Мост событий отслеживает идентификаторы инструментов FIFO по имени инструмента, а не один ID на имя. Это важно для:

- параллельных вызовов с одинаковым именем
- повторных вызовов с одинаковым именем в одном шаге

Без очередей FIFO события завершения привязывались бы к неверному вызову инструмента.

## Восстановление обратного вызова подтверждения

ACP временно устанавливает обратный вызов подтверждения на инструмент терминала во время выполнения подсказки, а затем восстанавливает предыдущий обратный вызов. Это предотвращает постоянную глобальную установку обработчиков подтверждения, специфичных для сессии ACP.

## Текущие ограничения

- Сессии ACP сохраняются в общий `~/.hermes/state.db` (SessionDB) и автоматически восстанавливаются после перезапуска процесса; они видны в `session_search`.
- Блоки подсказок, не содержащие текст, в настоящее время игнорируются при извлечении текста запроса.
- UX, специфичный для редактора, различается в зависимости от реализации клиента ACP.

## Связанные файлы

- `tests/acp/` — набор тестов ACP
- `toolsets.py` — определение наборов инструментов `hermes-acp`
- `hermes_cli/main.py` — подкоманда CLI `hermes acp`
- `pyproject.toml` — опциональная зависимость `[acp]` + скрипт `hermes-acp`