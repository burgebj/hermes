---
title: Provider маршрутизация
description: Настрой предпочтения провайдера OpenRouter для оптимизации по стоимости, скорости или качеству.
sidebar_label: Provider Routing
sidebar_position: 7
---

# Маршрутизация провайдера

При использовании [OpenRouter](https://openrouter.ai) в качестве провайдера LLM Hermes Agent поддерживает **маршрутизацию провайдера** — тонкий контроль над тем, какие базовые AI‑провайдеры обрабатывают твои запросы и как они приоритизируются.

OpenRouter направляет запросы к множеству провайдеров (например, Anthropic, Google, AWS Bedrock, Together AI). Маршрутизация провайдера позволяет оптимизировать стоимость, скорость, качество или обеспечить соблюдение конкретных требований к провайдеру.

:::tip
Трафик, проходящий через [Nous Portal](/integrations/nous-portal), по‑прежнему учитывает настройки маршрутизации и приоритетов для каждой модели — а подписчики Portal получают скидку 10 % на провайдеров, оплачиваемых токенами.
:::

## Конфигурация

Добавь секцию `provider_routing` в свой `~/.hermes/config.yaml`:

```yaml
provider_routing:
  sort: "price"           # How to rank providers
  only: []                # Whitelist: only use these providers
  ignore: []              # Blacklist: never use these providers
  order: []               # Explicit provider priority order
  require_parameters: false  # Only use providers that support all parameters
  data_collection: null   # Control data collection ("allow" or "deny")
```

:::info
Маршрутизация провайдера применяется только при использовании OpenRouter. Она не влияет на прямые подключения к провайдерам (например, при прямом подключении к API Anthropic).
:::

## Параметры

### `sort`

Определяет, как OpenRouter ранжирует доступные провайдеры для твоего запроса.

| Значение | Описание |
|----------|----------|
| `"price"` | Сначала самый дешёвый провайдер |
| `"throughput"` | Сначала провайдер с наибольшим количеством токенов в секунду |
| `"latency"` | Сначала провайдер с наименьшей задержкой до первого токена |

```yaml
provider_routing:
  sort: "price"
```

### `only`

Белый список имён провайдеров. При указании **только** эти провайдеры будут использованы. Все остальные исключаются.

```yaml
provider_routing:
  only:
    - "Anthropic"
    - "Google"
```

### `ignore`

Чёрный список имён провайдеров. Эти провайдеры **никогда** не будут использованы, даже если они предлагают самую низкую цену или наибольшую скорость.

```yaml
provider_routing:
  ignore:
    - "Together"
    - "DeepInfra"
```

### `order`

Явный порядок приоритетов. Провайдеры, указанные первыми, имеют предпочтение. Провайдеры, не перечисленные в списке, используются как запасные варианты.

```yaml
provider_routing:
  order:
    - "Anthropic"
    - "Google"
    - "AWS Bedrock"
```

### `require_parameters`

Если `true`, OpenRouter будет направлять запросы только к провайдерам, которые поддерживают **все** параметры твоего запроса (например, `temperature`, `top_p`, `tools` и т.д.). Это предотвращает тихое игнорирование параметров.

```yaml
provider_routing:
  require_parameters: true
```

### `data_collection`

Определяет, могут ли провайдеры использовать твои подсказки для обучения. Возможные варианты: `"allow"` или `"deny"`.

```yaml
provider_routing:
  data_collection: "deny"
```

## Практические примеры

### Оптимизация по стоимости

Направить запросы к самому дешёвому доступному провайдеру. Подходит для большого объёма использования и разработки:

```yaml
provider_routing:
  sort: "price"
```

### Оптимизация по скорости

Отдавать приоритет провайдерам с низкой задержкой для интерактивного использования:

```yaml
provider_routing:
  sort: "latency"
```

### Оптимизация по пропускной способности

Лучший вариант для генерации длинных текстов, где важна скорость токенов в секунду:

```yaml
provider_routing:
  sort: "throughput"
```

### Фиксация на конкретных провайдерах

Гарантировать, что все запросы проходят через определённый провайдер для согласованности:

```yaml
provider_routing:
  only:
    - "Anthropic"
```

### Исключение конкретных провайдеров

Исключить провайдеры, которые ты не хочешь использовать (например, из соображений конфиденциальности данных):

```yaml
provider_routing:
  ignore:
    - "Together"
    - "Lepton"
  data_collection: "deny"
```

### Предпочтительный порядок с запасными вариантами

Сначала попытаться использовать предпочтительные провайдеры, а при их недоступности переключаться на другие:

```yaml
provider_routing:
  order:
    - "Anthropic"
    - "Google"
  require_parameters: true
```

## Как это работает

Настройки маршрутизации провайдера передаются в API OpenRouter через поле `extra_body.provider` в каждом вызове API. Это применяется как к:

- **CLI‑режиму** — конфигурируется в `~/.hermes/config.yaml`, загружается при старте
- **Gateway‑режиму** — тот же файл конфигурации, загружается при запуске шлюза

Конфигурация маршрутизации читается из `config.yaml` и передаётся как параметры при создании `AIAgent`:

```
providers_allowed  ← from provider_routing.only
providers_ignored  ← from provider_routing.ignore
providers_order    ← from provider_routing.order
provider_sort      ← from provider_routing.sort
provider_require_parameters ← from provider_routing.require_parameters
provider_data_collection    ← from provider_routing.data_collection
```

:::tip
Можно комбинировать несколько опций. Например, сортировать по цене, но исключать определённые провайдеры и требовать поддержки параметров:

```yaml
provider_routing:
  sort: "price"
  ignore: ["Together"]
  require_parameters: true
  data_collection: "deny"
```
:::

## Поведение по умолчанию

Если секция `provider_routing` не настроена (поведение по умолчанию), OpenRouter использует собственную стандартную логику маршрутизации, которая обычно автоматически балансирует стоимость и доступность.

:::tip Provider Routing vs. Fallback Models
Маршрутизация провайдера управляет тем, какие **суб‑провайдеры внутри OpenRouter** обрабатывают твои запросы. Для автоматического переключения на полностью иной провайдер при сбое основной модели смотри [Fallback Providers](/user-guide/features/fallback-providers).
:::