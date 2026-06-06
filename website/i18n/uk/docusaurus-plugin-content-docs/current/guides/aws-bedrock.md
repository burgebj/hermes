---
sidebar_position: 14
title: "AWS Bedrock"
description: "Використовуй Hermes Agent з Amazon Bedrock — нативний Converse API, автентифікація IAM, Guardrails та міжрегіональне виведення."
---

# AWS Bedrock

Hermes Agent підтримує Amazon Bedrock як рідний провайдер, використовуючи **Converse API** — не сумісну з OpenAI кінцеву точку. Це дає повний доступ до екосистеми Bedrock: автентифікація IAM, Guardrails, профілі інференсу між регіонами та всі фундаментальні моделі.

## Передумови

- **AWS credentials** — будь‑яке джерело, підтримуване [ланцюжком облікових даних boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html):
  - IAM роль інстанції (EC2, ECS, Lambda — нульова конфігурація)
  - змінні середовища `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
  - `AWS_PROFILE` для SSO або іменованих профілів
  - `aws configure` для локальної розробки
- **boto3** — встановити за допомогою `pip install hermes-agent[bedrock]`
- **IAM permissions** — мінімум:
  - `bedrock:InvokeModel` і `bedrock:InvokeModelWithResponseStream` (для інференсу)
  - `bedrock:ListFoundationModels` і `bedrock:ListInferenceProfiles` (для виявлення моделей)

:::tip EC2 / ECS / Lambda
На обчислювальних ресурсах AWS підключи IAM роль з `AmazonBedrockFullAccess` — і готово. Без API‑ключів, без конфігурації `.env` — Hermes автоматично визначає роль інстанції.
:::

## Швидкий старт

```bash
# Install with Bedrock support
pip install hermes-agent[bedrock]

# Select Bedrock as your provider
hermes model
# → Choose "More providers..." → "AWS Bedrock"
# → Select your region and model

# Start chatting
hermes chat
```

## Конфігурація

Після запуску `hermes model` ваш файл `~/.hermes/config.yaml` міститиме:

```yaml
model:
  default: us.anthropic.claude-sonnet-4-6
  provider: bedrock
  base_url: https://bedrock-runtime.us-east-2.amazonaws.com

bedrock:
  region: us-east-2
```

### Регіон

Вкажи регіон AWS одним із способів (пріоритет від найвищого):

1. `bedrock.region` у `config.yaml`
2. змінна середовища `AWS_REGION`
3. змінна середовища `AWS_DEFAULT_REGION`
4. За замовчуванням — `us-east-1`

### Guardrails

Щоб застосувати [Amazon Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html) до всіх викликів моделей:

```yaml
bedrock:
  region: us-east-2
  guardrail:
    guardrail_identifier: "abc123def456"  # From the Bedrock console
    guardrail_version: "1"                # Version number or "DRAFT"
    stream_processing_mode: "async"       # "sync" or "async"
    trace: "disabled"                     # "enabled", "disabled", or "enabled_full"
```

### Виявлення моделей

Hermes автоматично виявляє доступні моделі через контрольну площину Bedrock. Ти можеш налаштувати процес виявлення:

```yaml
bedrock:
  discovery:
    enabled: true
    provider_filter: ["anthropic", "amazon"]  # Only show these providers
    refresh_interval: 3600                     # Cache for 1 hour
```

## Доступні моделі

Моделі Bedrock використовують **ідентифікатори профілів інференсу** для виклику на вимогу. Пікер `hermes model` показує їх автоматично, а рекомендовані моделі розташовані вгорі:

| Model | ID | Notes |
|-------|-----|-------|
| Claude Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` | Recommended — best balance of speed and capability |
| Claude Opus 4.6 | `us.anthropic.claude-opus-4-6-v1` | Most capable |
| Claude Haiku 4.5 | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Fastest Claude |
| Amazon Nova Pro | `us.amazon.nova-pro-v1:0` | Amazon's flagship |
| Amazon Nova Micro | `us.amazon.nova-micro-v1:0` | Fastest, cheapest |
| DeepSeek V3.2 | `deepseek.v3.2` | Strong open model |
| Llama 4 Scout 17B | `us.meta.llama4-scout-17b-instruct-v1:0` | Meta's latest |

:::info Cross-Region Inference
Моделі з префіксом `us.` використовують профілі інференсу між регіонами, що забезпечують кращу пропускну здатність та автоматичний фейловер між регіонами AWS. Моделі з префіксом `global.` маршрутизуються через усі доступні регіони світу.
:::

## Перемикання моделей під час сесії

Використай команду `/model` під час розмови:

```
/model us.amazon.nova-pro-v1:0
/model deepseek.v3.2
/model us.anthropic.claude-opus-4-6-v1
```

## Діагностика

```bash
hermes doctor
```

Доктор перевіряє:
- Чи доступні AWS‑облікові дані (змінні середовища, IAM‑роль, SSO)
- Чи встановлений `boto3`
- Чи доступний API Bedrock (ListFoundationModels)
- Кількість доступних моделей у вашому регіоні

## Шлюз (Messaging Platforms)

Bedrock працює зі всіма платформами шлюзу Hermes (Telegram, Discord, Slack, Feishu тощо). Налаштуй Bedrock як провайдера, а потім запусти шлюз звичайним способом:

```bash
hermes gateway setup
hermes gateway start
```

Шлюз читає `config.yaml` і використовує ту ж конфігурацію провайдера Bedrock.

## Усунення проблем

### “No API key found” / “No AWS credentials”

Hermes перевіряє облікові дані у такому порядку:
1. `AWS_BEARER_TOKEN_BEDROCK`
2. `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
3. `AWS_PROFILE`
4. Метадані інстанції EC2 (IMDS)
5. Облікові дані контейнера ECS
6. Роль виконання Lambda

Якщо нічого не знайдено, запусти `aws configure` або підключи IAM‑роль до вашого обчислювального ресурсу.

### “Invocation of model ID … with on-demand throughput isn’t supported”

Використай **ідентифікатор профілю інференсу** (з префіксом `us.` або `global.`) замість «голого» ідентифікатора фундаментальної моделі. Наприклад:
- ❌ `anthropic.claude-sonnet-4-6`
- ✅ `us.anthropic.claude-sonnet-4-6`

### “ThrottlingException”

Ти досяг ліміту швидкості Bedrock для конкретної моделі. Hermes автоматично повторює запит з бекоффом. Щоб збільшити ліміти, запроси підвищення квоти в консолі [AWS Service Quotas console](https://console.aws.amazon.com/servicequotas/).

## Одно‑клікове розгортання AWS

Для повністю автоматизованого розгортання на EC2 за допомогою CloudFormation:

**[sample-hermes-agent-on-aws-with-bedrock](https://github.com/JiaDe-Wu/sample-hermes-agent-on-aws-with-bedrock)** — створює VPC, IAM‑роль, інстанцію EC2 та автоматично налаштовує Bedrock. Розгорни у будь‑якому регіоні одним кліком.