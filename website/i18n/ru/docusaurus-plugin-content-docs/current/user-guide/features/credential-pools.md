---
title: пул учётных данных
description: Создай пул нескольких API‑ключей или OAuth‑токенов на каждого провайдера для автоматической ротации и восстановления после ограничения скорости.
sidebar_label: Credential Pools
sidebar_position: 9
---

# Пулы учётных данных

Пулы учётных данных позволяют регистрировать несколько API‑ключей или OAuth‑токенов для одного и того же провайдера. Когда один ключ достигает ограничения по скорости или квоте биллинга, Hermes автоматически переключается на следующий здоровый ключ — поддерживая твою сессию в работе без смены провайдера.

Это отличается от [запасных провайдеров](./fallback-providers.md), которые переключаются на *другой* провайдер полностью. Пулы — это ротация внутри одного провайдера; запасные провайдеры — это переключение между провайдерами. Сначала пробуются пула; если все ключи пула исчерпаны, *только тогда* активируется запасный провайдер.

:::tip
Пулы учётных данных в основном предназначены для провайдеров с API‑ключами (OpenRouter, Anthropic). Один OAuth‑токен [Nous Portal](/integrations/nous-portal) покрывает более 300 моделей, поэтому большинству пользователей пул не нужен при работе через Portal.
:::

## Как это работает

```
Your request
  → Pick key from pool (round_robin / least_used / fill_first / random)
  → Send to provider
  → 429 rate limit?
      → Plan/usage limit reached (e.g. ChatGPT/Codex "usage limit reached")?
          → Rotate to next pool key immediately (no retry — the cap won't clear on retry)
      → Generic / transient 429?
          → Retry same key once (transient blip)
          → Second 429 → rotate to next pool key
      → All keys exhausted → fallback_model (different provider)
  → 402 billing error?
      → Immediately rotate to next pool key (24h cooldown)
  → 401 auth expired?
      → Try refreshing the token (OAuth)
      → Refresh failed → rotate to next pool key
  → Success → continue normally
```

## Быстрый старт

Если у тебя уже есть API‑ключ, указанный в `.env`, Hermes автоматически обнаружит его как пул из одного ключа. Чтобы воспользоваться преимуществами пула, добавь ещё ключи:

```bash
# Add a second OpenRouter key
hermes auth add openrouter --api-key sk-or-v1-your-second-key

# Add a second Anthropic key
hermes auth add anthropic --type api-key --api-key sk-ant-api03-your-second-key

# Add an Anthropic OAuth credential (requires Claude Max plan + extra usage credits)
hermes auth add anthropic --type oauth
# Opens browser for OAuth login
```

Проверь свои пула:

```bash
hermes auth list
```

Вывод:
```
openrouter (2 credentials):
  #1  OPENROUTER_API_KEY   api_key env:OPENROUTER_API_KEY ←
  #2  backup-key           api_key manual

anthropic (3 credentials):
  #1  hermes_pkce          oauth   hermes_pkce ←
  #2  claude_code          oauth   claude_code
  #3  ANTHROPIC_API_KEY    api_key env:ANTHROPIC_API_KEY
```

Стрелка `←` указывает на текущие выбранные учётные данные.

## Интерактивное управление

Запусти `hermes auth` без подкоманды — это интерактивный мастер:

```bash
hermes auth
```

Он покажет полное состояние пула и предложит меню:

```
What would you like to do?
  1. Add a credential
  2. Remove a credential
  3. Reset cooldowns for a provider
  4. Set rotation strategy for a provider
  5. Exit
```

Для провайдеров, поддерживающих как API‑ключи, так и OAuth (Anthropic, Nous, Codex), процесс добавления спрашивает тип:

```
anthropic supports both API keys and OAuth login.
  1. API key (paste a key from the provider dashboard)
  2. OAuth login (authenticate via browser)
Type [1/2]:
```

## Команды CLI

| Команда | Описание |
|---------|----------|
| `hermes auth` | Интерактивный мастер управления пулом |
| `hermes auth list` | Показать все пула и учётные данные |
| `hermes auth list <provider>` | Показать пул конкретного провайдера |
| `hermes auth add <provider>` | Добавить учётные данные (спросит тип и ключ) |
| `hermes auth add <provider> --type api-key --api-key <key>` | Добавить API‑ключ без интерактивного ввода |
| `hermes auth add <provider> --type oauth` | Добавить OAuth‑учётные данные через вход в браузер |
| `hermes auth remove <provider> <index>` | Удалить учётные данные по индексу (нумерация с 1) |
| `hermes auth reset <provider>` | Очистить все статусы cooldown/исчерпания |

## Стратегии ротации

Настраивается через `hermes auth` → «Set rotation strategy» или в `config.yaml`:

```yaml
credential_pool_strategies:
  openrouter: round_robin
  anthropic: least_used
```

| Стратегия | Поведение |
|----------|-----------|
| `fill_first` (по умолчанию) | Использовать первый здоровый ключ, пока он не будет исчерпан, затем переходить к следующему |
| `round_robin` | Равномерно чередовать ключи, переключаясь после каждого выбора |
| `least_used` | Всегда выбирать ключ с наименьшим счётчиком запросов |
| `random` | Случайный выбор среди здоровых ключей |

## Восстановление после ошибок

Пул обрабатывает разные ошибки по‑разному:

| Ошибка | Поведение | Cooldown |
|--------|-----------|----------|
| **429 Rate Limit** | Один раз повторить запрос тем же ключом (временное). При второй последовательной 429 переключиться на следующий ключ | 1 час |
| **402 Billing/Quota** | Немедленно переключиться на следующий ключ | 24 часа |
| **401 Auth Expired** | Сначала попытаться обновить OAuth‑токен. Переключиться только если обновление не удалось | — |
| **All keys exhausted** | Перейти к `fallback_model`, если он настроен | — |

Флаг `has_retried_429` сбрасывается после каждого успешного API‑вызова, поэтому единичный временный 429 не приводит к ротации.

## Пулы пользовательских эндпоинтов

Пользовательские эндпоинты, совместимые с OpenAI (Together.ai, RunPod, локальные серверы), получают собственные пула, ключом которых является имя эндпоинта из `custom_providers` в `config.yaml`.

Когда ты настраиваешь пользовательский эндпоинт через `hermes model`, автоматически генерируется имя вроде «Together.ai» или «Local (localhost:8080)». Это имя становится ключом пула.

```bash
# After setting up a custom endpoint via hermes model:
hermes auth list
# Shows:
#   Together.ai (1 credential):
#     #1  config key    api_key config:Together.ai ←

# Add a second key for the same endpoint:
hermes auth add Together.ai --api-key sk-together-second-key
```

Пулы пользовательских эндпоинтов хранятся в `auth.json` под `credential_pool` с префиксом `custom:`:

```json
{
  "credential_pool": {
    "openrouter": [...],
    "custom:together.ai": [...]
  }
}
```

## Автообнаружение

Hermes автоматически обнаруживает учётные данные из разных источников и заполняет пул при запуске:

| Источник | Пример | Автозаполнение? |
|----------|--------|-----------------|
| Переменные окружения | `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY` | Да |
| OAuth‑токены (auth.json) | Codex device code, Nous device code | Да |
| Учётные данные Claude Code | `~/.claude/.credentials.json` | Да (Anthropic) |
| Hermes PKCE OAuth | `~/.hermes/auth.json` | Да (Anthropic) |
| Конфигурация пользовательского эндпоинта | `model.api_key` в config.yaml | Да (пользовательские эндпоинты) |
| Ручные записи | Добавленные через `hermes auth add` | Сохраняются в auth.json |

Автозаполненные записи обновляются при каждой загрузке пула — если удалить переменную окружения, её запись в пуле автоматически удаляется. Ручные записи (добавленные через `hermes auth add`) никогда не удаляются автоматически.

Заимствованные секреты времени выполнения (например, переменные окружения, ссылки Bitwarden/Vault/keyring/systemd и пользовательские значения конфигурации) являются только ссылками на границе `auth.json`. Hermes может использовать разрешённое значение в памяти для текущего запуска, но сохраняет лишь метаданные: источник ссылки, метку, статус, счётчики запросов и необратимый отпечаток. Ручные записи и состояние OAuth/device‑code, принадлежащее Hermes, сохраняют долговременные токены, необходимые для обновления.

## Делегирование и совместное использование пула субагентами

Когда агент создаёт субагентов через `delegate_task`, пул учётных данных родителя автоматически передаётся детям:

- **Тот же провайдер** — субагент получает полный пул родителя, позволяя ротацию ключей при ограничениях
- **Другой провайдер** — субагент загружает собственный пул этого провайдера (если он настроен)
- **Пул не настроен** — субагент использует унаследованный одиночный API‑ключ

Это значит, что субагенты получают ту же устойчивость к ограничениям скорости, что и родитель, без дополнительной настройки. Аренда учётных данных per‑task гарантирует, что дети не конфликтуют при одновременной ротации ключей.

## Потокобезопасность

Пул учётных данных использует блокировку потоков для всех изменений состояния (`select()`, `mark_exhausted_and_rotate()`, `try_refresh_current()`, `mark_used()`). Это обеспечивает безопасный конкурентный доступ, когда шлюз обслуживает несколько чат‑сессий одновременно.

## Архитектура

Полную схему потока данных смотри в [`docs/credential-pool-flow.excalidraw`](https://excalidraw.com/#json=2Ycqhqpi6f12E_3ITyiwh,c7u9jSt5BwrmiVzHGbm87g) репозитория.

Пул учётных данных интегрирован на уровне разрешения провайдера:

1. **`agent/credential_pool.py`** — менеджер пула: хранение, выбор, ротация, cooldown‑ы
2. **`hermes_cli/auth_commands.py`** — команды CLI и интерактивный мастер
3. **`hermes_cli/runtime_provider.py`** — разрешение учётных данных с учётом пула
4. **`run_agent.py`** — восстановление после ошибок: 429/402/401 → ротация пула → запасной провайдер

## Хранение

Состояние пула сохраняется в `~/.hermes/auth.json` под ключом `credential_pool`:

```json
{
  "version": 1,
  "credential_pool": {
    "openrouter": [
      {
        "id": "abc123",
        "label": "OPENROUTER_API_KEY",
        "auth_type": "api_key",
        "priority": 0,
        "source": "env:OPENROUTER_API_KEY",
        "secret_source": "bitwarden",
        "secret_fingerprint": "sha256:12ab34cd56ef7890",
        "last_status": "ok",
        "request_count": 142
      }
    ],
    "anthropic": [
      {
        "id": "manual1",
        "label": "personal-api-key",
        "auth_type": "api_key",
        "priority": 0,
        "source": "manual",
        "access_token": "sk-ant-api03-..."
      }
    ]
  }
}
```

Запись OpenRouter выше была заимствована из внешнего источника, поэтому сырой ключ не сохраняется в `auth.json`. Запись Anthropic была намеренно добавлена в хранилище учётных данных Hermes, поэтому её токен остаётся сохраняемым.

Стратегии хранятся в `config.yaml` (не в `auth.json`):

```yaml
credential_pool_strategies:
  openrouter: round_robin
  anthropic: least_used
```