---
sidebar_position: 14
title: "AWS Bedrock"
description: "Используй Hermes Agent с Amazon Bedrock — нативный Converse API, аутентификация IAM, Guardrails и межрегионный вывод"
---

# AWS Bedrock

Hermes Agent поддерживает Amazon Bedrock как нативного провайдера, используя **Converse API** — а не совместимый с OpenAI endpoint. Это даёт полный доступ к экосистеме Bedrock: аутентификация IAM, Guardrails, кросс‑региональные профили вывода и все базовые модели.

## Требования

- **AWS credentials** — любой источник, поддерживаемый [цепочкой учётных данных boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html):
  - IAM‑роль экземпляра (EC2, ECS, Lambda — нулевая конфигурация)
  - переменные окружения `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
  - `AWS_PROFILE` для SSO или именованных профилей
  - `aws configure` для локальной разработки
- **boto3** — установить командой `pip install hermes-agent[bedrock]`
- **IAM permissions** — минимум:
  - `bedrock:InvokeModel` и `bedrock:InvokeModelWithResponseStream` (для вывода)
  - `bedrock:ListFoundationModels` и `bedrock:ListInferenceProfiles` (для обнаружения моделей)

:::tip EC2 / ECS / Lambda
На вычислительных ресурсах AWS привяжи IAM‑роль с `AmazonBedrockFullAccess` — и всё готово. Нет API‑ключей, нет конфигурации `.env` — Hermes автоматически обнаруживает роль экземпляра.
:::

## Быстрый старт

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

## Конфигурация

После выполнения `hermes model` ваш файл `~/.hermes/config.yaml` будет содержать:

```yaml
model:
  default: us.anthropic.claude-sonnet-4-6
  provider: bedrock
  base_url: https://bedrock-runtime.us-east-2.amazonaws.com

bedrock:
  region: us-east-2
```

### Регион

Укажи регион AWS одним из способов (приоритет от высшего к низшему):

1. `bedrock.region` в `config.yaml`
2. переменная окружения `AWS_REGION`
3. переменная окружения `AWS_DEFAULT_REGION`
4. По умолчанию: `us-east-1`

### Guardrails

Чтобы применить [Amazon Bedrock Guardrails](https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html) ко всем вызовам моделей:

```yaml
bedrock:
  region: us-east-2
  guardrail:
    guardrail_identifier: "abc123def456"  # From the Bedrock console
    guardrail_version: "1"                # Version number or "DRAFT"
    stream_processing_mode: "async"       # "sync" or "async"
    trace: "disabled"                     # "enabled", "disabled", or "enabled_full"
```

### Обнаружение моделей

Hermes автоматически обнаруживает доступные модели через контрольную плоскость Bedrock. Вы можете настроить процесс обнаружения:

```yaml
bedrock:
  discovery:
    enabled: true
    provider_filter: ["anthropic", "amazon"]  # Only show these providers
    refresh_interval: 3600                     # Cache for 1 hour
```

## Доступные модели

Модели Bedrock используют **ID инференс‑профилей** для вызова по требованию. Пикер `hermes model` показывает их автоматически, а рекомендованные модели находятся вверху списка:

| Model | ID | Notes |
|-------|-----|-------|
| Claude Sonnet 4.6 | `us.anthropic.claude-sonnet-4-6` | Recommended — лучший баланс скорости и возможностей |
| Claude Opus 4.6 | `us.anthropic.claude-opus-4-6-v1` | Наиболее мощная |
| Claude Haiku 4.5 | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Самая быстрая Claude |
| Amazon Nova Pro | `us.amazon.nova-pro-v1:0` | Флагманская модель Amazon |
| Amazon Nova Micro | `us.amazon.nova-micro-v1:0` | Самая быстрая, самая дешёвая |
| DeepSeek V3.2 | `deepseek.v3.2` | Сильная открытая модель |
| Llama 4 Scout 17B | `us.meta.llama4-scout-17b-instruct-v1:0` | Последняя модель Meta |

:::info Cross-Region Inference
Модели с префиксом `us.` используют кросс‑региональные инференс‑профили, что обеспечивает большую ёмкость и автоматический запасной (fallback) между регионами AWS. Модели с префиксом `global.` маршрутизируются через все доступные регионы мира.
:::

## Смена модели в середине сессии

Используй команду `/model` во время разговора:

```
/model us.amazon.nova-pro-v1:0
/model deepseek.v3.2
/model us.anthropic.claude-opus-4-6-v1
```

## Диагностика

```bash
hermes doctor
```

Доктор проверяет:
- Доступны ли учётные данные AWS (переменные окружения, IAM‑роль, SSO)
- Установлен ли `boto3`
- Доступен ли API Bedrock (ListFoundationModels)
- Количество доступных моделей в вашем регионе

## Шлюз (платформы обмена сообщениями)

Bedrock работает со всеми платформами шлюза Hermes (Telegram, Discord, Slack, Feishu и др.). Настройте Bedrock как провайдера, затем запустите шлюз обычным способом:

```bash
hermes gateway setup
hermes gateway start
```

Шлюз читает `config.yaml` и использует ту же конфигурацию провайдера Bedrock.

## Устранение неполадок

### «No API key found» / «No AWS credentials»

Hermes проверяет наличие учётных данных в следующем порядке:
1. `AWS_BEARER_TOKEN_BEDROCK`
2. `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`
3. `AWS_PROFILE`
4. Метаданные экземпляра EC2 (IMDS)
5. Учётные данные контейнера ECS
6. Роль выполнения Lambda

Если ничего не найдено, выполните `aws configure` или привяжите IAM‑роль к вашему вычислительному ресурсу.

### «Invocation of model ID … with on-demand throughput isn’t supported»

Используйте **ID инференс‑профиля** (с префиксом `us.` или `global.`) вместо «голого» ID базовой модели. Например:
- ❌ `anthropic.claude-sonnet-4-6`
- ✅ `us.anthropic.claude-sonnet-4-6`

### «ThrottlingException»

Вы достигли лимита запросов к модели Bedrock. Hermes автоматически повторяет запросы с экспоненциальной задержкой. Чтобы увеличить лимиты, запросите повышение квоты в [консоли AWS Service Quotas](https://console.aws.amazon.com/servicequotas/).

## Однокликовое развертывание в AWS

Для полностью автоматизированного развертывания на EC2 с помощью CloudFormation:

**[sample-hermes-agent-on-aws-with-bedrock](https://github.com/JiaDe-Wu/sample-hermes-agent-on-aws-with-bedrock)** — создаёт VPC, IAM‑роль, экземпляр EC2 и автоматически настраивает Bedrock. Разворачивается в любом регионе одним кликом.