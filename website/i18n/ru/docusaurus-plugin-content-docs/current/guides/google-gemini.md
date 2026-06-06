---
sidebar_position: 16
title: "Google Gemini"
description: "Используй Hermes Agent с Google Gemini — нативный AI Studio API, настройка API‑key, вариант OAuth, вызов инструментов, потоковая передача и рекомендации по квотам"
---

# Google Gemini

Hermes Agent поддерживает Google Gemini как нативного провайдера, используя **Google AI Studio / Gemini API** — не совместимый с OpenAI endpoint. Это позволяет Hermes переводить свой внутренний цикл сообщений и инструментов, построенный по схеме OpenAI, в нативный API `generateContent` Gemini, сохраняя вызов инструментов, потоковую передачу, мультимодальные входные данные и специфичные для Gemini метаданные ответа.

Hermes также поддерживает отдельный провайдер **Google Gemini (OAuth)**, который использует тот же бэкенд Cloud Code Assist, что и CLI Google Gemini. Используй провайдер с API‑ключом (`gemini`) для пути официального API с наименьшим риском.
## Предварительные требования

- **Google AI Studio API key** — создай его на [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- **Billing-enabled Google Cloud project** — рекомендуется для использования агента. Бесплатный уровень Gemini слишком мал для длительных сессий агента, поскольку Hermes может выполнять несколько вызовов модели за один ход пользователя.
- **Hermes installed** — дополнительный пакет Python не требуется для нативного провайдера `gemini`.

:::tip API key path
Установи `GOOGLE_API_KEY` или `GEMINI_API_KEY`. Hermes проверяет оба имени для провайдера `gemini`.
:::
## Быстрый старт

```bash
# Add your Gemini API key
echo "GOOGLE_API_KEY=..." >> ~/.hermes/.env

# Select Gemini as your provider
hermes model
# → Choose "More providers..." → "Google AI Studio"
# → Hermes checks your key tier and shows Gemini models
# → Select a model

# Start chatting
hermes chat
```

Если ты предпочитаешь прямое редактирование конфигурации, используй базовый URL API Gemini:

```yaml
model:
  default: gemini-3-flash-preview
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta
```
## Конфигурация

После выполнения `hermes model` ваш файл `~/.hermes/config.yaml` будет содержать:

```yaml
model:
  default: gemini-3-flash-preview
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta
```

А в `~/.hermes/.env`:

```bash
GOOGLE_API_KEY=...
```

### Native Gemini API

Рекомендуемый endpoint:

```text
https://generativelanguage.googleapis.com/v1beta
```

Hermes обнаруживает этот endpoint и создаёт свой native Gemini‑адаптер. Внутренне Hermes всё равно хранит цикл агента в сообщениях формата OpenAI, а затем переводит каждый запрос в native‑схему Gemini:

- `messages[]` → Gemini `contents[]`
- системные подсказки → Gemini `systemInstruction`
- схемы инструментов → Gemini `functionDeclarations`
- результаты инструментов → Gemini `functionResponse`‑части
- потоковые ответы → чанки формата OpenAI для цикла Hermes

:::note Gemini 3 thought signatures
Для использования инструментов Gemini 3 Hermes сохраняет значения `thoughtSignature`, прикреплённые к частям вызова функции, и воспроизводит их на следующем ходу инструмента. Это покрывает критически важный путь валидации для многошаговых рабочих процессов агента.

Gemini 3 также может прикреплять thought signatures к другим частям ответа. Native‑адаптер Hermes оптимизирован сегодня для циклов инструментов агента, поэтому пока не воспроизводит каждую подпись, не связанную с вызовом инструмента, с полной точностью на уровне частей.
:::

### Предпочтительно использовать native‑endpoint

Google также предоставляет совместимый с OpenAI endpoint:

```text
https://generativelanguage.googleapis.com/v1beta/openai/
```

Для сессий агента Hermes предпочтительно использовать native‑endpoint Gemini, указанный выше. Hermes включает native‑адаптер Gemini, поэтому может напрямую сопоставлять многоходовое использование инструментов, результаты вызовов инструментов, потоковую передачу, мультимодальные вводы и метаданные ответов Gemini с API `generateContent`. Совместимый с OpenAI endpoint всё ещё полезен, когда тебе специально нужна совместимость с API OpenAI.

Если ты ранее устанавливала `GEMINI_BASE_URL` на URL `/openai`, удали его или измени:

```bash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
```

### OAuth‑провайдер

У Hermes также есть провайдер `google-gemini-cli`:

```bash
hermes model
# → Choose "Google Gemini (OAuth)"
```

Он использует вход в браузер через PKCE и бэкенд Cloud Code Assist. Это может быть полезно для пользователей, желающих OAuth в стиле Gemini CLI, но Hermes выводит явное предупреждение, поскольку Google может рассматривать использование клиента OAuth Gemini CLI из стороннего программного обеспечения как нарушение политики. Для продакшн‑использования или с минимальными рисками предпочтительно использовать провайдера с API‑ключом, указанный выше.
## Доступные модели

Панель выбора `hermes model` показывает модели Gemini, находящиеся в реестре провайдеров Hermes. Часто используемые варианты включают:

| Модель | ID | Примечания |
|-------|----|------------|
| Gemini 3.1 Pro Preview | `gemini-3.1-pro-preview` | Самая мощная предварительная модель, когда доступна |
| Gemini 3 Pro Preview | `gemini-3-pro-preview` | Сильная модель для рассуждений и кодирования |
| Gemini 3 Flash Preview | `gemini-3-flash-preview` | Рекомендуемый баланс скорости и возможностей по умолчанию |
| Gemini 3.1 Flash Lite Preview | `gemini-3.1-flash-lite-preview` | Самый быстрый / самый дешёвый вариант, когда доступен |

Доступность моделей меняется со временем. Если модель исчезла или не включена для твоего ключа, запусти `hermes model` снова и выбери одну из текущего списка.

:::info Идентификаторы моделей
Используй нативные идентификаторы Gemini, такие как `gemini-3-flash-preview`, а не идентификаторы в стиле OpenRouter вроде `google/gemini-3-flash-preview`, когда `provider: gemini`.
:::

### Последние алиасы

Google публикует «движущиеся» алиасы для семейств Pro и Flash Gemini. `gemini-pro-latest` и `gemini-flash-latest` полезны, когда ты хочешь, чтобы Google автоматически обновлял модель без изменения конфигурации Hermes.

| Алиас | Текущий трек | Примечания |
|-------|--------------|------------|
| `gemini-pro-latest` | Последняя модель Gemini Pro | Лучший вариант, когда нужен текущий Pro‑по‑умолчанию от Google |
| `gemini-flash-latest` | Последняя модель Gemini Flash | Лучший вариант, когда нужен текущий Flash‑по‑умолчанию от Google |

```yaml
model:
  default: gemini-pro-latest
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta
```

Если нужна строгая воспроизводимость, предпочитай явные идентификаторы моделей, такие как `gemini-3.1-pro-preview` или `gemini-3-flash-preview`.

### Gemma через Gemini API

Google также предоставляет модели Gemma через Gemini API. Hermes распознаёт их как модели Google, но скрывает очень низкопроизводительные записи Gemma из стандартного списка, чтобы новые пользователи случайно не выбрали модель уровня оценки для длительной сессии агента.

Полезные идентификаторы для оценки:

| Модель | ID | Примечания |
|-------|----|------------|
| Gemma 4 31B IT | `gemma-4-31b-it` | Большая модель Gemma; полезна для совместимости и оценки качества |
| Gemma 4 26B A4B IT | `gemma-4-26b-a4b-it` | Меньший вариант с активными параметрами, когда доступен |

Эти модели лучше рассматривать как варианты оценки при использовании ключей Gemini API. Ценообразование Gemma API от Google ограничено бесплатным уровнем, а лимиты использования низки по сравнению с производственными моделями Gemini, поэтому при длительном использовании агента Hermes обычно переходят на платную модель Gemini, собственный развернутый вариант или другого провайдера с соответствующей квотой.

Чтобы использовать модель Gemma, скрытую в списке, укажи её напрямую:

```yaml
model:
  default: gemma-4-31b-it
  provider: gemini
  base_url: https://generativelanguage.googleapis.com/v1beta
```
## Переключение моделей в процессе сессии

Используй команду `/model` во время разговора:

```text
/model gemini-3-flash-preview
/model gemini-flash-latest
/model gemini-3-pro-preview
/model gemini-pro-latest
/model gemma-4-31b-it
/model gemini-3.1-flash-lite-preview
```

Если ты ещё не настроил Gemini, выйди из сессии и сначала запусти `hermes model`. Команда `/model` переключает между уже настроенными провайдерами и моделями; она не собирает новые API‑ключи.
## Диагностика

```bash
hermes doctor
```

Проверяется:

- Доступен ли `GOOGLE_API_KEY` или `GEMINI_API_KEY`
- Существуют ли учётные данные Gemini OAuth для `google-gemini-cli`
- Можно ли разрешить настроенные учётные данные провайдера

Для просмотра использования квоты OAuth запусти это внутри сессии Hermes:

```text
/gquota
```

`/gquota` относится к провайдеру OAuth `google-gemini-cli`, а не к провайдеру API‑ключа AI Studio.
## Шлюз (Платформы обмена сообщениями)

Gemini работает со всеми платформами шлюза Hermes (Telegram, Discord, Slack, WhatsApp, LINE, Feishu и т.д.). Настрой Gemini как своего провайдера, затем запусти шлюз обычным способом:

```bash
hermes gateway setup
hermes gateway start
```

Шлюз читает `config.yaml` и использует ту же конфигурацию провайдера Gemini.
## Устранение неполадок

### «Gemini native client requires an API key»

Hermes не удалось найти пригодный API‑ключ. Добавь один из них в `~/.hermes/.env`:

```bash
GOOGLE_API_KEY=...
# or
GEMINI_API_KEY=...
```

Затем запусти `hermes model` снова.

### «This Google API key is on the free tier»

Hermes проверяет Gemini API‑ключи во время настройки. Квоты бесплатного уровня могут быть исчерпаны после нескольких ходов агента, потому что использование инструментов, повторные попытки, сжатие и вспомогательные задачи могут требовать множества вызовов модели.

Включи биллинг в проекте Google Cloud, к которому привязан твой ключ, при необходимости сгенерируй новый ключ, затем выполни:

```bash
hermes model
```

### «404 model not found»

Выбранная модель недоступна для твоего аккаунта, региона или ключа. Запусти `hermes model` снова и выбери другую модель Gemini из текущего списка.

### Модель Gemma не отображается в `hermes model`

Hermes может скрывать модели Gemma с низкой пропускной способностью в списке по умолчанию. Если ты намеренно хочешь её оценить, задай ID модели напрямую в `~/.hermes/config.yaml`.

### «429 quota exceeded» на Gemma

Модели Gemma, доступные через Gemini API, полезны для оценки, но их бесплатные квоты низки. Используй их для тестов совместимости, затем переключись на платную модель Gemini или другого провайдера для длительных сессий агента.

### OpenAI‑compatible endpoint is configured

Проверь `~/.hermes/.env` на наличие:

```bash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

Измени его на нативный эндпоинт или удали переопределение:

```bash
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta
```

### Предупреждение OAuth‑входа

Провайдер `google-gemini-cli` использует OAuth‑поток Gemini CLI / Cloud Code Assist. Hermes предупреждает перед его запуском, потому что он отличается от официального пути с API‑ключом AI Studio. Используй `provider: gemini` с `GOOGLE_API_KEY` для официальной интеграции по API‑ключу.

### Ошибки вызова инструмента из‑за схемы

Обнови Hermes и запусти `hermes model` снова. Нативный адаптер Gemini очищает схемы инструментов для более строгого формата объявлений функций Gemini; более старые сборки или пользовательские эндпоинты могут этого не делать.
## Связанные

- [AI Providers](/integrations/providers)
- [Configuration](/user-guide/configuration)
- [Fallback Providers](/user-guide/features/fallback-providers)
- [AWS Bedrock](/guides/aws-bedrock) — нативная интеграция облачного провайдера с использованием учётных данных AWS