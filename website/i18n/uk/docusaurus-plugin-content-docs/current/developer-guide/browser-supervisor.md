---
sidebar_position: 18
title: "Браузер CDP Супервізор"
description: "Як Hermes виявляє та реагує на вбудовані діалоги JS і взаємодіє з крос‑доменною iframe через постійне підключення CDP."
---

# Супервізор CDP браузера

Супервізор CDP закриває два довготривалі прогалини в інструментах браузера Hermes:

1. **Вбудовані діалоги JS** (`alert`/`confirm`/`prompt`/`beforeunload`) блокують
   JS‑потік сторінки. Без нагляду агент не має способу дізнатися, що діалог
   відкритий — подальші виклики інструментів зависають або викидають
   непрозорі помилки.
2. **Крос‑доменні iframe (OOPIFs)** невидимі для `Runtime.evaluate` верхнього рівня.
   Агент може бачити вузли iframe у знімку DOM, але не може клікати, вводити
   текст або виконувати `eval` всередині них без підключеної CDP‑сесії до
   дочірньої цілі.

Супервізор вирішує обидві проблеми, утримуючи постійне WebSocket‑з’єднання
з CDP‑кінцевою точкою бекенду для кожного завдання браузера, передаючи
очікувані діалоги та структуру кадрів у `browser_snapshot` та надаючи інструмент
`browser_dialog` для явних відповідей.
## Підтримка бекендів

| Бекенд | Виявлення діалогів | Відповідь діалогу | Дерево кадрів | OOPIF `Runtime.evaluate` через `browser_cdp(frame_id=…)` |
|---|---|---|---|---|
| Local Chrome (`--remote-debugging-port`) / `/browser connect` | ✓ | ✓ повний робочий процес | ✓ | ✓ |
| Browserbase | ✓ (через міст) | ✓ повний робочий процес (через міст) | ✓ | ✓ |
| Camofox | ✗ немає CDP (лише REST) | ✗ | частково за допомогою знімка DOM | ✗ |

**Особливість Browserbase.** Проксі CDP у Browserbase використовує Playwright внутрішньо і автоматично закриває нативні діалоги приблизно за ~10 мс, тому `Page.handleJavaScriptDialog` не встигає. Супервізор інжектує скрипт‑мост через `Page.addScriptToEvaluateOnNewDocument`, який перевизначає `window.alert`/`confirm`/`prompt` синхронним XHR до магічного хоста (`hermes-dialog-bridge.invalid`). `Fetch.enable` перехоплює ці XHR до того, як вони потраплять у мережу — діалог стає подією `Fetch.requestPaused`, яку захоплює супервізор, і `respond_to_dialog` виконує запит через `Fetch.fulfillRequest` з JSON‑тілом, яке декодує інжектований скрипт.

З точки зору сторінки, `prompt()` все ще повертає рядок, наданий агентом.
З точки зору агента, це той самий API `browser_dialog(action=…)` у будь‑якому випадку.

Camofox не підтримується — немає поверхні CDP, лише REST.
## Architecture

### CDPSupervisor

Один `asyncio.Task`, що працює у фоні в демон‑потоку для кожного Hermes `task_id`.
Тримає постійне WebSocket‑з’єднання з CDP‑endpoint бекенду. Підтримує:

- **Dialog queue** — `List[PendingDialog]` з `{id, type, message, default_prompt, session_id, opened_at}`
- **Frame tree** — `Dict[frame_id, FrameInfo]` з батьківськими зв’язками, URL, origin, чи є дочірня крос‑origin сесія
- **Session map** — `Dict[session_id, SessionInfo]`, щоб інструменти взаємодії могли маршрутизувати до потрібної приєднаної сесії для OOPIF‑операцій
- **Recent console errors** — кільцевий буфер останніх 50 помилок для діагностики

Підписується під час приєднання:

- `Page.enable` — `javascriptDialogOpening`, `frameAttached`, `frameNavigated`, `frameDetached`
- `Runtime.enable` — `executionContextCreated`, `consoleAPICalled`, `exceptionThrown`
- `Target.setAutoAttach {autoAttach: true, flatten: true}` — виявляє дочірні OOPIF‑цілі; супервізор вмикає `Page`+`Runtime` для кожної

Доступ до стану безпечний у багатопоточному середовищі через знімок під блокуванням; обробники інструментів (sync) читають заморожений знімок без `await`.

### Lifecycle

- **Start:** `SupervisorRegistry.get_or_start(task_id, cdp_url)` — викликається `browser_navigate`, створенням сесії Browserbase, `/browser connect`. Ідемпотентний.
- **Stop:** завершення сесії або `/browser disconnect`. Скасовує asyncio‑задачу, закриває WebSocket, відкидає стан.
- **Rebind:** якщо CDP‑URL змінюється (користувач підключається до нового Chrome), старий супервізор зупиняється і запускається новий — стан ніколи не використовується повторно між endpoint‑ами.

### Dialog policy

Налаштовується у `config.yaml` під `browser.dialog_policy`:

- **`must_respond`** (за замовчуванням) — захоплює, показує у `browser_snapshot`, чекає явного виклику `browser_dialog(action=…)`. Після 300 s тайм‑ауту без відповіді автоматично відхиляє і логірує. Запобігає зависанню агента.
- `auto_dismiss` — записує і одразу відхиляє; агент бачить це пізніше через `browser_state` у `browser_snapshot`.
- `auto_accept` — записує і приймає (корисно для `beforeunload`, коли workflow хоче чисто перейти).

Політика застосовується до кожного завдання; переозначення для окремих діалогів не передбачено.
## Поверхня агента

### Інструмент `browser_dialog`

```
browser_dialog(action, prompt_text=None, dialog_id=None)
```

- `action="accept"` / `"dismiss"` → відповідає на вказаний або єдиний очікуючий діалог (обов’язково)
- `prompt_text=...` → текст, який слід передати діалогу `prompt()`
- `dialog_id=...` → розрізняє діалоги, коли їх у черзі кілька (рідко)

Інструмент лише для відповіді. Агент читає очікуючі діалоги з виводу `browser_snapshot` перед викликом.

### Розширення `browser_snapshot`

Додає три необов’язкові поля до існуючого виводу знімка, коли підключений супервізор:

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

- **`pending_dialogs`** — діалоги, які наразі блокують JS‑потік сторінки. Агент повинен викликати `browser_dialog(action=…)`, щоб відповісти. Порожньо у Browserbase, оскільки їхній CDP‑проксі автоматично відхиляє діалоги протягом ~10 мс.
- **`recent_dialogs`** — кільцевий буфер до 20 нещодавно закритих діалогів з тегом `closed_by`: `"agent"` (ми відповіли), `"auto_policy"` (локальне auto_dismiss/auto_accept), `"watchdog"` (тайм‑аут must_respond), або `"remote"` (браузер/бекенд закрив його, напр. Browserbase). Так агенти в Browserbase все ще бачать, що сталося.
- **`frame_tree`** — структура фреймів, включаючи дочірні (OOPIF) з різних походжень. Обмежено 30 записами + глибиною OOPIF 2, щоб не збільшувати розмір знімка на сторінках з великою кількістю реклами. `truncated: true` з’являється, коли досягнуті ліміти; агенти, яким потрібне повне дерево, можуть скористатися `browser_cdp` з `Page.getFrameTree`.

Немає нової схеми інструмента для жодного з цих полів — агент читає вже запитуваний знімок.

### Обмеження доступності

Обидві поверхні залежать від `_browser_cdp_check` (супервізор може працювати лише коли CDP‑кінцева точка доступна). У сесіях Camofox / без бекенду інструмент діалогу прихований, а знімок не містить нових полів — без зайвого навантаження схеми.
## Взаємодія з крос‑оригінальними iframe

`browser_cdp(frame_id=…)` маршрутизує виклики CDP (зокрема `Runtime.evaluate`) через вже підключений WebSocket супервізора, використовуючи `sessionId` дочірнього OOPIF. Агент отримує `frame_id` з `browser_snapshot.frame_tree.children[]`, де `is_oopif=true`, і передає їх у `browser_cdp`. Для iframe того ж походження (без окремої CDP‑сесії) агент використовує `contentWindow`/`contentDocument` з верхнього рівня `Runtime.evaluate` — супервізор повертає помилку, що вказує на цей запасний (фолбек) варіант, коли `frame_id` належить не‑OOPIF.

У Browserbase це єдиний надійний шлях для взаємодії з iframe — безстанові CDP‑з’єднання (відкриті для кожного виклику `browser_cdp`) стикаються з закінченням терміну дії підписаних URL, тоді як довготривале з’єднання супервізора підтримує дійсну сесію.
## Структура файлів

- `tools/browser_supervisor.py` — `CDPSupervisor`, `SupervisorRegistry`, `PendingDialog`, `FrameInfo`
- `tools/browser_dialog_tool.py` — обробник інструмента `browser_dialog`
- `tools/browser_tool.py` — стартовий хук `browser_navigate`, злиття `browser_snapshot`, повторне підключення `/browser connect`, завершення `_cleanup_browser_session`
- `toolsets.py` — реєструє `browser_dialog` у `browser`, `hermes-acp`, `hermes-api-server` та у базових наборах інструментів (залежно від доступності CDP)
- `hermes_cli/config.py` — значення за замовчуванням `browser.dialog_policy` та `browser.dialog_timeout_s`
## Нецілі

- Виявлення/взаємодія з Camofox (проблема на верхньому рівні; відстежується окремо)
- Потокове передавання подій діалогу/кадрів у реальному часі користувачеві (потрібні гачки шлюзу)
- Збереження історії діалогу між сесіями (лише в пам'яті)
- Політики діалогу для кожного iframe (агент може вказати їх за допомогою `dialog_id`)
- Заміну `browser_cdp` — вона залишається «запасним виходом» для довгого хвоста (куки, розмір вікна, обмеження мережі)
## Тестування

Юніт‑тести (`tests/tools/test_browser_supervisor.py`) використовують asyncio‑мок CDP‑сервер, який підтримує достатньо протоколу, щоб перевірити всі переходи станів: `attach`, `enable`, `navigate`, `dialog fire`, `dialog dismiss`, `frame attach/detach`, `child target attach`, `session teardown`. Реальний бекенд E2E (Browserbase + локальний браузер сімейства Chromium) тестується вручну — виконуй підключення до живого браузера сімейства Chromium через `/browser connect` і запускай описані вище тестові випадки діалогів/фреймів.