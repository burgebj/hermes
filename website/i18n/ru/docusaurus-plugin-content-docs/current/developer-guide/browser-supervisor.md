---
sidebar_position: 18
title: "Супервизор CDP браузера"
description: "Как Hermes обнаруживает и реагирует на нативные диалоги JS и взаимодействует с кросс‑доменными iframe через постоянное соединение CDP."
---

# Супервизор CDP браузера

Супервизор CDP закрывает два давних пробела в наборе инструментов браузера Hermes:

1. **Нативные диалоги JS** (`alert`/`confirm`/`prompt`/`beforeunload`) блокируют
   JS‑поток страницы. Без надзора агент не может узнать, что диалог открыт — последующие вызовы инструментов зависают или бросают непонятные ошибки.
2. **Кросс‑доменные iframe (OOPIF)** невидимы для верхнеуровневого
   `Runtime.evaluate`. Агент видит узлы iframe в снимке DOM, но не может кликнуть, ввести текст или выполнить `eval` внутри них без CDP‑сессии, привязанной к дочернему таргету.

Супервизор решает обе проблемы, удерживая постоянный WebSocket к CDP‑конечному пункту бэкенда для каждой задачи браузера, выводя ожидающие диалоги и структуру фреймов в `browser_snapshot` и предоставляя инструмент `browser_dialog` для явных ответов.
## Поддержка бекендов

| Backend | Обнаружение диалогов | Ответ на диалог | Дерево фреймов | OOPIF `Runtime.evaluate` через `browser_cdp(frame_id=...)` |
|---|---|---|---|---|
| Local Chrome (`--remote-debugging-port`) / `/browser connect` | ✓ | ✓ полный рабочий процесс | ✓ | ✓ |
| Browserbase | ✓ (через мост) | ✓ полный рабочий процесс (через мост) | ✓ | ✓ |
| Camofox | ✗ нет CDP (только REST) | ✗ | частично через снимок DOM | ✗ |

**Особенность Browserbase.** Прокси CDP от Browserbase использует Playwright внутри и автоматически отклоняет нативные диалоги примерно за 10 мс, поэтому `Page.handleJavaScriptDialog` не успевает. Супервизор внедряет скрипт‑мост через `Page.addScriptToEvaluateOnNewDocument`, который переопределяет `window.alert`/`confirm`/`prompt` синхронным XHR на магический хост (`hermes-dialog-bridge.invalid`). `Fetch.enable` перехватывает эти XHR до выхода в сеть — диалог превращается в событие `Fetch.requestPaused`, которое захватывает супервизор, и `respond_to_dialog` отвечает через `Fetch.fulfillRequest` с JSON‑телом, которое декодирует внедрённый скрипт.

С точки зрения страницы, `prompt()` всё равно возвращает строку, переданную агентом. С точки зрения агента, это один и тот же API `browser_dialog(action=...)` в любом случае.

Camofox не поддерживается — нет CDP‑поверхности, только REST.
## Architecture

### CDPSupervisor

Один `asyncio.Task`, работающий в фоновом демоном‑потоке для каждого Hermes `task_id`.
Поддерживает постоянное WebSocket‑соединение с CDP‑конечной точкой бэкенда. Хранит:

- **Очередь диалогов** — `List[PendingDialog]` с `{id, type, message, default_prompt, session_id, opened_at}`
- **Дерево фреймов** — `Dict[frame_id, FrameInfo]` с отношениями родителя, URL, origin, информацией о том, является ли дочерняя сессия кросс‑origin
- **Карту сессий** — `Dict[session_id, SessionInfo]`, чтобы инструменты взаимодействия могли маршрутизировать запросы к нужной прикреплённой сессии для операций OOPIF
- **Недавние ошибки консоли** — кольцевой буфер последних 50 записей для диагностики

Подписывается при присоединении:

- `Page.enable` — `javascriptDialogOpening`, `frameAttached`, `frameNavigated`, `frameDetached`
- `Runtime.enable` — `executionContextCreated`, `consoleAPICalled`, `exceptionThrown`
- `Target.setAutoAttach {autoAttach: true, flatten: true}` — выявляет дочерние OOPIF‑цели; supervisor включает `Page`+`Runtime` для каждой из них

Потокобезопасный доступ к состоянию осуществляется через блокировку‑снимок; обработчики инструментов (синхронные) читают замороженный снимок без `await`.

### Lifecycle

- **Start:** `SupervisorRegistry.get_or_start(task_id, cdp_url)` — вызывается из `browser_navigate`, создания сессии Browserbase, `/browser connect`. Идемпотентен.
- **Stop:** завершение сессии или `/browser disconnect`. Отменяет `asyncio`‑задачу, закрывает WebSocket, удаляет состояние.
- **Rebind:** если CDP‑URL меняется (пользователь переподключается к новому Chrome), старый supervisor останавливается и запускается новый — состояние никогда не переиспользуется между конечными точками.

### Dialog policy

Настраивается через `config.yaml` в разделе `browser.dialog_policy`:

- **`must_respond`** (по умолчанию) — захват, отображение в `browser_snapshot`, ожидание явного вызова `browser_dialog(action=...)`. После тайм‑аута безопасности в 300 с без ответа происходит автоматическое отклонение и запись в лог. Предотвращает зависание агента из‑за ошибки.
- `auto_dismiss` — запись и немедленное отклонение; агент видит её позже через `browser_state` внутри `browser_snapshot`.
- `auto_accept` — запись и принятие (полезно для `beforeunload`, когда workflow хочет корректно перейти на другую страницу).

Политика задаётся на уровне задачи; переопределения для отдельных диалогов не поддерживаются.
## Поверхность агента

### Инструмент `browser_dialog`

```
browser_dialog(action, prompt_text=None, dialog_id=None)
```

- `action="accept"` / `"dismiss"` → отвечает на указанный или единственный ожидающий диалог (обязательно)
- `prompt_text=...` → текст, который будет передан в диалог `prompt()`
- `dialog_id=...` → уточнение, когда в очереди несколько диалогов (редко)

Инструмент только для ответа. Агент читает ожидающие диалоги из вывода `browser_snapshot` перед вызовом.

### Расширение `browser_snapshot`

Добавляет три необязательных поля к существующему выводу снимка, когда подключён супервизор:

```json
{
  "pending_dialogs": [
    {"id": "d-1", "type": "alert", "message": "Hello", "opened_at": 1650000000.0}
  ],
  "recent_dialogs": [
    {"id": "d-1", "type": "alert", "message": "...", "opened_at": 1650000000.0,
     "closed_at": 1650000000.1, "closed_by": "remote"}
  ],
  "frame_tree": {
    "top": {"frame_id": "FRAME_A", "url": "https://example.com/", "origin": "https://example.com"},
    "children": [
      {"frame_id": "FRAME_B", "url": "about:srcdoc", "is_oopif": false},
      {"frame_id": "FRAME_C", "url": "https://ads.example.net/", "is_oopif": true, "session_id": "SID_C"}
    ],
    "truncated": false
  }
}
```

- **`pending_dialogs`** — диалоги, в данный момент блокирующие JS‑поток страницы. Агент должен вызвать `browser_dialog(action=…)`, чтобы ответить. Пусто в Browserbase, потому что их CDP‑прокси автоматически отклоняет диалог примерно за 10 мс.

- **`recent_dialogs`** — кольцевой буфер до 20 недавно закрытых диалогов с тегом `closed_by`: `"agent"` (мы ответили), `"auto_policy"` (локальное auto_dismiss/auto_accept), `"watchdog"` (истёк таймаут must_respond) или `"remote"` (браузер/бэкенд закрыл его за нас, например Browserbase). Так агенты в Browserbase всё ещё видят, что произошло.

- **`frame_tree`** — структура фреймов, включая дочерние кросс‑origin (OOPIF) элементы. Ограничено 30 записями + глубина OOPIF 2, чтобы ограничить размер снимка на страницах с большим количеством рекламы. `truncated: true` появляется, когда лимиты достигнуты; агентам, которым нужно полное дерево, можно использовать `browser_cdp` с `Page.getFrameTree`.

Никакой новой схемы инструмента для этих полей не появляется — агент читает уже запрашиваемый снимок.

### Ограничение доступности

Обе поверхности зависят от `_browser_cdp_check` (супервизор может работать только когда CDP‑конечная точка доступна). В сессиях Camofox / без бэкенда инструмент диалога скрыт, а снимок не содержит новых полей — без увеличения схемы.
## Взаимодействие с кросс‑доменной iframe

`browser_cdp(frame_id=…)` направляет вызовы CDP (в частности `Runtime.evaluate`) через уже подключённый WebSocket супервизора, используя `sessionId` дочернего OOPIF. Агент выбирает `frame_id` из `browser_snapshot.frame_tree.children[]`, где `is_oopif=true`, и передаёт их в `browser_cdp`. Для iframe того же происхождения (без отдельной CDP‑сессии) агент использует `contentWindow`/`contentDocument` из верхнего уровня `Runtime.evaluate` — супервизор выдаёт ошибку, указывающую на этот запасной (вариант), когда `frame_id` относится к не‑OOPIF.

В Browserbase это единственный надёжный путь для взаимодействия с iframe — безсостоящие CDP‑соединения (открываемые при каждом вызове `browser_cdp`) сталкиваются с истечением срока действия подписанного URL, тогда как долговременное соединение супервизора сохраняет действительную сессию.
## Структура файлов

- `tools/browser_supervisor.py` — `CDPSupervisor`, `SupervisorRegistry`, `PendingDialog`, `FrameInfo`
- `tools/browser_dialog_tool.py` — обработчик инструмента `browser_dialog`
- `tools/browser_tool.py` — start‑hook `browser_navigate`, merge `browser_snapshot`, reattach `/browser connect`, teardown `_cleanup_browser_session`
- `toolsets.py` — регистрирует `browser_dialog` в `browser`, `hermes‑acp`, `hermes‑api‑server` и в основных наборов инструментов (доступно только при достижимости CDP)
- `hermes_cli/config.py` — значения по умолчанию `browser.dialog_policy` и `browser.dialog_timeout_s`
## Нецели

- Обнаружение/взаимодействие с Camofox (пробел в upstream; отслеживается отдельно)
- Потоковая передача событий диалога/кадра пользователю в реальном времени (требует хуков шлюза)
- Сохранение истории диалога между сессиями (только в памяти)
- Политики диалога для каждого iframe (агент может выразить это через `dialog_id`)
- Замена `browser_cdp` — он остаётся запасным вариантом для редких случаев (cookies, viewport, ограничение сети)
## Тестирование

Юнит‑тесты (`tests/tools/test_browser_supervisor.py`) используют asyncio‑мок‑сервер CDP, который реализует достаточную часть протокола для проверки всех переходов состояний: attach, enable, navigate, dialog fire, dialog dismiss, frame attach/detach, child target attach, session teardown. Реальный бекенд E2E (Browserbase + локальный браузер семейства Chromium) тестируется вручную — выполнять через `/browser connect` к живому браузеру семейства Chromium и запускать описанные выше тест‑кейсы диалогов/фреймов.