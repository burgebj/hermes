---
title: Provider маршрутизація
description: Налаштуй параметри провайдера OpenRouter для оптимізації за вартістю, швидкістю або якістю.
sidebar_label: Provider Routing
sidebar_position: 7
---

# Маршрутизація провайдерів

Коли ти використовуєш [OpenRouter](https://openrouter.ai) як свого LLM‑провайдера, Hermes Agent підтримує **маршрутизацію провайдерів** — детальний контроль над тим, які саме AI‑провайдери обробляють твої запити і яким чином вони пріоритетизуються.

OpenRouter маршрутизує запити до багатьох провайдерів (наприклад, Anthropic, Google, AWS Bedrock, Together AI). Маршрутизація провайдерів дозволяє оптимізувати витрати, швидкість, якість або вимагати конкретні умови провайдера.

:::tip
Трафік, який проходить через [Nous Portal](/integrations/nous-portal), все одно дотримується налаштувань маршрутизації та пріоритету для кожної моделі — і підписники Порталу отримують 10 % знижки на провайдерів, які оплачуються токенами.
:::

## Конфігурація

Додай розділ `provider_routing` у свій `~/.hermes/config.yaml`:

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
Маршрутизація провайдерів застосовується лише при використанні OpenRouter. Вона не впливає на прямі підключення до провайдерів (наприклад, пряме підключення до API Anthropic).
:::

## Параметри

### `sort`

Керує тим, як OpenRouter ранжує доступні провайдери для твого запиту.

| Значення | Опис |
|----------|------|
| `"price"` | Спочатку найдешевший провайдер |
| `"throughput"` | Спочатку найшвидший за кількістю токенів за секунду |
| `"latency"` | Спочатку найнижча затримка до першого токену |

```yaml
provider_routing:
  sort: "price"
```

### `only`

Білий список імен провайдерів. Якщо встановлено, **лише** ці провайдери будуть використані. Усі інші виключені.

```yaml
provider_routing:
  only:
    - "Anthropic"
    - "Google"
```

### `ignore`

Чорний список імен провайдерів. Ці провайдери **ніколи** не будуть використані, навіть якщо вони найдешевші або найшвидші.

```yaml
provider_routing:
  ignore:
    - "Together"
    - "DeepInfra"
```

### `order`

Явний порядок пріоритету. Провайдери, зазначені першими, мають перевагу. Провайдери, які не вказані, використовуються як запасний варіант.

```yaml
provider_routing:
  order:
    - "Anthropic"
    - "Google"
    - "AWS Bedrock"
```

### `require_parameters`

Коли `true`, OpenRouter буде маршрутизувати лише до провайдерів, які підтримують **всі** параметри твого запиту (наприклад, `temperature`, `top_p`, `tools` тощо). Це запобігає тихому відкиданню параметрів.

```yaml
provider_routing:
  require_parameters: true
```

### `data_collection`

Керує тим, чи можуть провайдери використовувати твої підказки для навчання. Параметри: `"allow"` або `"deny"`.

```yaml
provider_routing:
  data_collection: "deny"
```

## Практичні приклади

### Оптимізація за вартістю

Маршрутуй до найдешевшого доступного провайдера. Підходить для великого обсягу використання та розробки:

```yaml
provider_routing:
  sort: "price"
```

### Оптимізація за швидкістю

Пріоритетно використовуй провайдери з низькою затримкою для інтерактивного використання:

```yaml
provider_routing:
  sort: "latency"
```

### Оптимізація за пропускною здатністю

Найкраще для довгих генерацій, коли важлива кількість токенів за секунду:

```yaml
provider_routing:
  sort: "throughput"
```

### Фіксація на конкретних провайдерах

Забезпеч, щоб усі запити проходили через певного провайдера для послідовності:

```yaml
provider_routing:
  only:
    - "Anthropic"
```

### Виключення певних провайдерів

Виключи провайдери, які не хочеш використовувати (наприклад, через конфіденційність даних):

```yaml
provider_routing:
  ignore:
    - "Together"
    - "Lepton"
  data_collection: "deny"
```

### Бажаний порядок з запасними варіантами

Спробуй спочатку свої улюблені провайдери, а при їх недоступності переходь до інших:

```yaml
provider_routing:
  order:
    - "Anthropic"
    - "Google"
  require_parameters: true
```

## Як це працює

Налаштування маршрутизації провайдерів передаються в API OpenRouter через поле `extra_body.provider` у кожному виклику API. Це стосується як:

- **CLI режим** — налаштовано у `~/.hermes/config.yaml`, завантажується під час старту
- **Gateway режим** — той самий файл конфігурації, завантажується при запуску шлюзу

Конфігурація маршрутизації читається з `config.yaml` і передається як параметри під час створення `AIAgent`:

```
providers_allowed  ← from provider_routing.only
providers_ignored  ← from provider_routing.ignore
providers_order    ← from provider_routing.order
provider_sort      ← from provider_routing.sort
provider_require_parameters ← from provider_routing.require_parameters
provider_data_collection    ← from provider_routing.data_collection
```

:::tip
Ти можеш комбінувати кілька опцій. Наприклад, сортувати за ціною, але виключити певних провайдерів і вимагати підтримки параметрів:

```yaml
provider_routing:
  sort: "price"
  ignore: ["Together"]
  require_parameters: true
  data_collection: "deny"
```
:::

## Поведінка за замовчуванням

Якщо розділ `provider_routing` не налаштовано (за замовчуванням), OpenRouter використовує власну логіку маршрутизації, яка зазвичай автоматично балансує вартість і доступність.

:::tip Provider Routing vs. Fallback Models
Маршрутизація провайдерів контролює, які **суб‑провайдери всередині OpenRouter** обробляють твої запити. Для автоматичного переключення на зовсім інший провайдер, коли основна модель не працює, дивись [Fallback Providers](/user-guide/features/fallback-providers).
:::