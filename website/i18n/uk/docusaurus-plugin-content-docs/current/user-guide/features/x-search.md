---
title: X (Twitter) Пошук
description: Шукай пости та треди X (Twitter) з агента, використовуючи вбудований інструмент x_search Responses від xAI — працює з будь‑яким входом SuperGrok OAuth або XAI_API_KEY.
sidebar_label: X (Twitter) Search
sidebar_position: 7
---

# X (Twitter) Search

Інструмент `x_search` дозволяє агенту шукати пости, профілі та теми в X (Twitter) безпосередньо. Він працює завдяки вбудованому інструменту xAI `x_search` у Responses API за адресою `https://api.x.ai/v1/responses` — сам Grok виконує пошук на сервері та повертає синтезовані результати з посиланнями на вихідні пости.

**Використовуй його замість `web_search`**, коли тобі потрібні саме актуальні обговорення, реакції або твердження **в X**. Для загальних веб‑сторінок продовжуй користуватися `web_search` / `web_extract`.

:::tip
Якщо ти все одно оплачуєш модель xAI у Portal, виклики Live Search списуються з того ж xAI‑ключа, який налаштовано для чату. Дивись [Nous Portal](/integrations/nous-portal).
:::

## Authentication

`x_search` реєструється, коли **будь‑яка** з доступних шляхів облікових даних xAI присутня:

| Credential | Source | Setup |
|------------|--------|-------|
| **SuperGrok / X Premium+ OAuth** (рекомендовано) | Вхід у браузері на `accounts.x.ai`, оновлюється автоматично | `hermes auth add xai-oauth` — дивись [xAI Grok OAuth (SuperGrok / X Premium+)](../../guides/xai-grok-oauth.md) |
| **`XAI_API_KEY`** | Платний xAI API‑ключ | Встановити у `~/.hermes/.env` |

Обидва звертаються до того ж ендпоінту з однаковим payload — різниця лише у токені bearer. **Коли налаштовано обидва, перевагу має SuperGrok OAuth**, тому `x_search` працює в межах твоєї підписки, а не витрачає платний API‑бюджет.

`check_fn` інструменту виконує резолвер облікових даних xAI щоразу, коли список інструментів моделі перебудовується. Повернення `True` означає, що токен можна отримати, він не порожній і (якщо був прострочений) успішно оновився. Відкликані токени з невдалим оновленням приховують інструмент зі схеми; модель просто його не бачить.

## Enabling the tool

Автоматично вмикається, коли присутні облікові дані xAI (OAuth‑токен або `XAI_API_KEY`). Вимкнути явно можна через `hermes tools` → Search → x_search, якщо це не потрібно.

```bash
hermes tools
# → 🐦 X (Twitter) Search   (press space to toggle on)
```

У діалоговому вікні пропонуються два варіанти облікових даних:

1. **xAI Grok OAuth (SuperGrok / Premium+)** — відкриває браузер на `accounts.x.ai`, якщо ти ще не ввійшов
2. **xAI API key** — запитує `XAI_API_KEY`

Будь‑який варіант задовольняє вимоги. Ти можеш вибрати ті облікові дані, які вже маєш; інструмент працює однаково з обома. Якщо налаштовано обидва, під час виклику перевагу має OAuth.

## Configuration

```yaml
# ~/.hermes/config.yaml
x_search:
  # xAI model used for the Responses call.
  # grok-4.20-reasoning is the recommended default; any Grok model
  # with x_search tool access works.
  model: grok-4.20-reasoning

  # Request timeout in seconds. x_search can take 60–120s for
  # complex queries — the default is generous. Minimum: 30.
  timeout_seconds: 180

  # Number of automatic retries on 5xx / ReadTimeout / ConnectionError.
  # Each retry backs off (1.5x attempt seconds, capped at 5s).
  retries: 2
```

## Tool parameters

Агент викликає `x_search` з такими аргументами:

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string (required) | Що шукати в X. |
| `allowed_x_handles` | string array | Необов’язковий список хендлів, які включати **виключно** (макс. 10). Початковий `@` видаляється. |
| `excluded_x_handles` | string array | Необов’язковий список хендлів, які виключати (макс. 10). Взаємно виключає `allowed_x_handles`. |
| `from_date` | string | Необов’язкова дата початку у форматі `YYYY-MM-DD`. |
| `to_date` | string | Необов’язкова дата завершення у форматі `YYYY-MM-DD`. |
| `enable_image_understanding` | boolean | Попросити xAI проаналізувати зображення, прикріплені до підходящих постів. |
| `enable_video_understanding` | boolean | Попросити xAI проаналізувати відео, прикріплені до підходящих постів. |

Інструмент повертає JSON з:

- `answer` — синтезований текстовий відповідь від Grok
- `citations` — посилання, повернені у верхньому полі Responses API
- `inline_citations` — анотації `url_citation`, витягнуті з тіла повідомлення (кожна містить `url`, `title`, `start_index`, `end_index`)
- `degraded` — `true`, коли був встановлений будь‑який фільтр (`allowed_x_handles`, `excluded_x_handles`, `from_date`, `to_date`) **і** обидва канали цитувань повернули порожньо. У цьому випадку `answer` синтезовано з власних знань моделі, а не з індексу X, тому його слід вважати безджерельним. `false` в інших випадках (включно з випадком, коли фільтри не задано — широке безджерельне повідомлення все одно є відповіддю, а не помилкою фільтра).
- `degraded_reason` — короткий рядок, що називає активні фільтри, або `null`, коли `degraded` — `false`
- `credential_source` — `"xai-oauth"` якщо використано OAuth, `"xai"` якщо використано API‑ключ
- `model`, `query`, `provider`, `tool`, `success`

### Date validation

`from_date` / `to_date` перевіряються на боці клієнта перед HTTP‑запитом:

- Якщо вказані, їх потрібно розпарсити як `YYYY-MM-DD`.
- Якщо обидві вказані, `from_date` має бути не пізніше `to_date`.
- `from_date` не може бути пізніше сьогоднішньої дати UTC — у такому вікні ще не може бути постів, тому запит гарантовано поверне нуль цитувань.
- `to_date` у майбутньому дозволено (користувачі можуть запитати «з вчорашнього до завтрашнього», щоб отримати пости, які ще надходять).

Помилки валідації повертаються у вигляді структуруваного результату `{"error": "..."}`, а не як HTTP‑запит до xAI.

## Example

Розмова з агентом:

> What are people on X saying about the new Grok image features? Focus on responses from @xai.

Агент:

1. Викликає `x_search` з `query="reactions to new Grok image features"`, `allowed_x_handles=["xai"]`
2. Отримує синтезовану відповідь та список цитувань, що посилаються на конкретні пости
3. Відповідає текстом і посиланнями

## Troubleshooting

### "No xAI credentials available"

Інструмент повідомляє це, коли обидва шляхи автентифікації не спрацювали. Додай `XAI_API_KEY` у `~/.hermes/.env` або виконай `hermes auth add xai-oauth` і завершити вхід у браузері. Потім перезапусти сесію, щоб агент перечитав реєстр інструментів.

### "`x_search` is not enabled for this model"

Налаштована модель `x_search.model` не має доступу до серверного інструменту `x_search`. Перемкнись на `grok-4.20-reasoning` (за замовчуванням) або іншу модель Grok, яка його підтримує. Перевір актуальний список у [xAI documentation](https://docs.x.ai/).

### Tool doesn't appear in the schema

Можливі причини:

1. **Toolset не ввімкнено.** Запусти `hermes tools` і переконайся, що галочка **🐦 X (Twitter) Search** встановлена.
2. **Відсутні облікові дані xAI.** `check_fn` повертає `False`, тому схема залишається прихованою. Виконай `hermes auth status`, щоб перевірити стан входу xai-oauth, і переконайся, що `XAI_API_KEY` встановлено (якщо використовуєш шлях API‑ключа).

### `degraded: true` — answer with no citations

Коли ти використав `allowed_x_handles`, `excluded_x_handles` або діапазон дат, і відповідь повернула `degraded: true`, індекс X не знайшов підходящих постів, а Grok все ж створив відповідь зі своїх навчальних даних. Відповідь безджерельна — не сприймай її як реальний результат X.

Що перевіряти:

- **Помилка в хендлі.** Видали `@`, перевір правопис і наявність акаунту.
- **Занадто вузький діапазон дат** або діапазон, що проходить повз сьогоднішні пости; розширюй його і повтори запит.
- **Прогалини в індексі xAI.** Деякі активні акаунти іноді не потрапляють у `x_search`, навіть якщо постять регулярно. Спробуй ще через кілька хвилин або використай навичку `xurl` для прямого читання таймлайну конкретного акаунту.

## See Also

- [xAI Grok OAuth (SuperGrok / Premium+)](../../guides/xai-grok-oauth.md) — посібник з налаштування OAuth
- [Web Search & Extract](web-search.md) — для загального (не‑X) веб‑пошуку
- [Tools Reference](../../reference/tools-reference.md) — повний каталог інструментів