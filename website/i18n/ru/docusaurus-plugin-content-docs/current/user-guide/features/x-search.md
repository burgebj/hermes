---
title: X (Twitter) Поиск
description: Ищи посты и ветки X (Twitter) из агента, используя встроенный инструмент x_search Responses от xAI — работает с входом SuperGrok OAuth или XAI_API_KEY.
sidebar_label: X (Twitter) Search
sidebar_position: 7
---

# X (Twitter) Search

Инструмент `x_search` позволяет агенту искать посты, профили и ветки в X (Twitter) напрямую. Он использует встроенный в xAI инструмент `x_search` API Responses по адресу `https://api.x.ai/v1/responses` — сам Grok выполняет поиск на сервере и возвращает синтезированные результаты с цитатами на исходные посты.

**Используй его вместо `web_search`**, когда тебе нужны текущие обсуждения, реакции или утверждения **в X**. Для обычных веб‑страниц продолжай использовать `web_search` / `web_extract`.

:::tip
Если ты уже оплачиваешь модель xAI в Portal, вызовы Live Search списываются с того же xAI‑ключа, который настроен для чата. Смотри [Nous Portal](/integrations/nous-portal).
:::

## Authentication

`x_search` регистрируется, когда **любой** из путей учётных данных xAI доступен:

| Credential | Source | Setup |
|------------|--------|-------|
| **SuperGrok / X Premium+ OAuth** (preferred) | Вход в браузере на `accounts.x.ai`, обновляется автоматически | `hermes auth add xai-oauth` — см. [xAI Grok OAuth (SuperGrok / X Premium+)](../../guides/xai-grok-oauth.md) |
| **`XAI_API_KEY`** | Платный xAI API‑ключ | Установить в `~/.hermes/.env` |

Оба пути обращаются к одному и тому же эндпоинту с одинаковой нагрузкой — различие только в токене‑носителе. **Когда оба настроены, приоритет имеет SuperGrok OAuth**, поэтому `x_search` использует твою подписку, а не платный API‑расход.

Функция инструмента `check_fn` каждый раз, когда список инструментов модели перестраивается, запускает резолвер учётных данных xAI. Возврат `True` означает, что токен доступен, не пуст и (если истёк) успешно обновлён. Отозванные токены с неудачной попыткой обновления скрывают инструмент из схемы; модель просто не видит его.

## Enabling the tool

Автоматически включается, когда присутствуют учётные данные xAI (OAuth‑токен или `XAI_API_KEY`). Отключить явно можно через `hermes tools` → Search → x_search, если ты не хочешь его использовать.

```bash
hermes tools
# → 🐦 X (Twitter) Search   (press space to toggle on)
```

В диалоговом окне предлагаются два варианта учётных данных:

1. **xAI Grok OAuth (SuperGrok / Premium+)** — открывает браузер на `accounts.x.ai`, если ты ещё не вошёл
2. **xAI API key** — запрашивает `XAI_API_KEY`

Любой из вариантов удовлетворяет проверке доступа. Можно выбрать те учётные данные, которые уже есть; инструмент работает одинаково с обоими. Если оба пути настроены, при вызове предпочтение отдаётся OAuth.

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

Агент вызывает `x_search` с следующими аргументами:

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string (required) | Что искать в X. |
| `allowed_x_handles` | string array | Необязательный список handle‑ов, которые включать **исключительно** (макс. 10). Префикс `@` удаляется. |
| `excluded_x_handles` | string array | Необязательный список handle‑ов, которые исключать (макс. 10). Взаимоисключает `allowed_x_handles`. |
| `from_date` | string | Необязательная начальная дата в формате `YYYY-MM-DD`. |
| `to_date` | string | Необязательная конечная дата в формате `YYYY-MM-DD`. |
| `enable_image_understanding` | boolean | Попросить xAI проанализировать изображения, прикреплённые к найденным постам. |
| `enable_video_understanding` | boolean | Попросить xAI проанализировать видео, прикреплённые к найденным постам. |

Инструмент возвращает JSON со следующими полями:

- `answer` — синтезированный текстовый ответ от Grok
- `citations` — цитаты, возвращённые в верхнеуровневом поле Responses API
- `inline_citations` — аннотации `url_citation`, извлечённые из тела сообщения (каждая содержит `url`, `title`, `start_index`, `end_index`)
- `degraded` — `true`, если был установлен любой из фильтров (`allowed_x_handles`, `excluded_x_handles`, `from_date`, `to_date`) **и** оба канала цитирования вернулись пустыми. В этом случае `answer` синтезирован из знаний модели, а не из индекса X, поэтому считается несоставленным. `false` в остальных случаях (включая ситуацию без фильтров — широкий несоставленный ответ всё равно остаётся просто ответом).
- `degraded_reason` — короткая строка, указывающая, какие фильтры были активны, или `null`, когда `degraded` = `false`
- `credential_source` — `"xai-oauth"` если использован OAuth, `"xai"` если API‑ключ
- `model`, `query`, `provider`, `tool`, `success`

### Date validation

`from_date` / `to_date` проверяются на клиенте до HTTP‑запроса:

- Если указаны, обе должны парситься как `YYYY-MM-DD`.
- Когда обе заданы, `from_date` должна быть не позже `to_date`.
- `from_date` не может быть позже текущей даты UTC — постов в ещё не начавшемся окне не существует, запрос гарантированно вернёт ноль цитат.
- `to_date` в будущем разрешена (запросы типа «со вчерашнего дня до завтрашнего» допустимы).

Ошибки валидации возвращаются как структурированный результат инструмента `{"error": "..."}`, а не как HTTP‑ошибка от xAI.

## Example

Разговор с агентом:

> Что люди в X говорят о новых функциях генерации изображений в Grok? Сфокусируйся на ответах от @xai.

Агент выполнит:

1. Вызовет `x_search` с `query="reactions to new Grok image features"`, `allowed_x_handles=["xai"]`
2. Получит синтезированный ответ и список цитат, ссылающихся на конкретные посты
3. Ответит с текстом и ссылками

## Troubleshooting

### "No xAI credentials available"

Инструмент показывает это сообщение, когда оба пути аутентификации не удались. Установи `XAI_API_KEY` в `~/.hermes/.env` или выполни `hermes auth add xai-oauth` и пройди вход в браузере. Затем перезапусти сессию, чтобы агент перечитал реестр инструментов.

### "`x_search` is not enabled for this model"

Указанная модель `x_search.model` не имеет доступа к серверному инструменту `x_search`. Переключись на `grok-4.20-reasoning` (по умолчанию) или другую модель Grok, поддерживающую его. Смотри [xAI documentation](https://docs.x.ai/) для актуального списка.

### Tool doesn't appear in the schema

Две возможные причины:

1. **Набор инструментов не включён.** Выполни `hermes tools` и убедись, что галочка стоит у `🐦 X (Twitter) Search`.
2. **Отсутствуют учётные данные xAI.** `check_fn` возвращает `False`, поэтому схема скрыта. Выполни `hermes auth status`, чтобы проверить состояние входа xai-oauth, и убедись, что `XAI_API_KEY` установлен (если используешь путь с API‑ключом).

### `degraded: true` — answer with no citations

Если ты использовал `allowed_x_handles`, `excluded_x_handles` или диапазон дат и получил ответ с `degraded: true`, индекс X от xAI не нашёл подходящих постов, но Grok всё равно сгенерировал ответ из своей обучающей базы. Такой ответ несоставлен — не рассматривай его как реальный результат X.

Возможные причины:

- **Опечатка в handle.** Удали `@`, проверь правописание и наличие аккаунта.
- **Слишком узкий диапазон дат** или диапазон, прошедший текущие посты; расширь его и попробуй снова.
- **Проблемы индекса xAI.** Некоторые активные аккаунты иногда не попадают в результаты `x_search`, даже если публикуют регулярно. Повтори запрос через несколько минут или используй навык `xurl` для прямого чтения X API, когда нужен точный таймлайн конкретного аккаунта.

## See Also

- [xAI Grok OAuth (SuperGrok / Premium+)](../../guides/xai-grok-oauth.md) — руководство по настройке OAuth
- [Web Search & Extract](web-search.md) — для общего (не‑X) веб‑поиска
- [Tools Reference](../../reference/tools-reference.md) — полный каталог инструментов