---
title: "Agentmail — Дай агенту его собственный выделенный почтовый ящик через AgentMail"
sidebar_label: "Agentmail"
description: "Дай агенту его собственный выделенный почтовый ящик через AgentMail"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Agentmail

Дай агенту собственный выделенный почтовый ящик через AgentMail. Отправляй, получай и управляй письмами автономно, используя адреса электронной почты, принадлежащие агенту (например, hermes-agent@agentmail.to).

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/email/agentmail` |
| Path | `optional-skills/email/agentmail` |
| Version | `1.0.0` |
| Platforms | linux, macos, windows |
| Tags | `email`, `communication`, `agentmail`, `mcp` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при активном навыке.
:::

# AgentMail — Agent-Owned Email Inboxes

## Требования

- **AgentMail API key** (обязательно) — зарегистрируйся на https://console.agentmail.to (бесплатный тариф: 3 ящика, 3 000 писем/мес; платные планы от $20/мес)
- Node.js 18+ (для сервера MCP)

## Когда использовать
Используй этот навык, когда нужно:
- Дать агенту собственный выделенный адрес электронной почты
- Отправлять письма автономно от имени агента
- Принимать и читать входящие письма
- Управлять цепочками писем и разговорами
- Регистрация в сервисах или аутентификация через электронную почту
- Общаться с другими агентами или людьми по электронной почте

Это НЕ предназначено для чтения личной почты пользователя (для этого используй himalaya или Gmail).
AgentMail предоставляет агенту собственную идентичность и ящик.

## Настройка

### 1. Получить API‑ключ
- Перейди на https://console.agentmail.to
- Создай аккаунт и сгенерируй API‑ключ (начинается с `am_`)

### 2. Настроить сервер MCP
Добавь в `~/.hermes/config.yaml` (вставь свой реальный ключ — переменные окружения MCP не подставляются из .env):
```yaml
mcp_servers:
  agentmail:
    command: "npx"
    args: ["-y", "agentmail-mcp"]
    env:
      AGENTMAIL_API_KEY: "am_your_key_here"
```

### 3. Перезапустить Hermes
```bash
hermes
```
Все 11 инструментов AgentMail теперь доступны автоматически.

## Доступные инструменты (через MCP)

| Инструмент | Описание |
|------|-------------|
| `list_inboxes` | Список всех ящиков агента |
| `get_inbox` | Получить детали конкретного ящика |
| `create_inbox` | Создать новый ящик (получить реальный адрес) |
| `delete_inbox` | Удалить ящик |
| `list_threads` | Список цепочек писем в ящике |
| `get_thread` | Получить конкретную цепочку писем |
| `send_message` | Отправить новое письмо |
| `reply_to_message` | Ответить на существующее письмо |
| `forward_message` | Переслать письмо |
| `update_message` | Обновить метки/статус сообщения |
| `get_attachment` | Скачать вложение письма |

## Процедура

### Создать ящик и отправить письмо
1. Создай выделенный ящик:
   - Вызови `create_inbox` с именем пользователя (например, `hermes-agent`)
   - Агент получит адрес: `hermes-agent@agentmail.to`
2. Отправь письмо:
   - Вызови `send_message` с `inbox_id`, `to`, `subject`, `text`
3. Проверь ответы:
   - Вызови `list_threads`, чтобы увидеть входящие разговоры
   - Вызови `get_thread`, чтобы прочитать конкретную цепочку

### Проверить входящие письма
1. Вызови `list_inboxes`, чтобы найти ID своего ящика
2. Вызови `list_threads` с ID ящика, чтобы увидеть разговоры
3. Вызови `get_thread`, чтобы прочитать цепочку и её сообщения

### Ответить на письмо
1. Получи цепочку с помощью `get_thread`
2. Вызови `reply_to_message` с ID сообщения и текстом ответа

## Примеры рабочих процессов

**Регистрация в сервисе:**
```
1. create_inbox (username: "signup-bot")
2. Use the inbox address to register on the service
3. list_threads to check for verification email
4. get_thread to read the verification code
```

**Обращение агента к человеку:**
```
1. create_inbox (username: "hermes-outreach")
2. send_message (to: user@example.com, subject: "Hello", text: "...")
3. list_threads to check for replies
```

## Подводные камни
- Бесплатный тариф ограничен 3 ящиками и 3 000 писем/мес
- Письма отправляются с домена `@agentmail.to` в бесплатном тарифе (кастомные домены в платных планах)
- Требуется Node.js (18+) для сервера MCP (`npx -y agentmail-mcp`)
- Пакет Python `mcp` должен быть установлен: `pip install mcp`
- Реальное получение входящих писем (webhooks) требует публичного сервера — вместо этого используй опрос `list_threads` через cronjob для личного использования

## Проверка
После настройки протестируй командой:
```
hermes --toolsets mcp -q "Create an AgentMail inbox called test-agent and tell me its email address"
```
Ты должен увидеть возвращённый новый адрес ящика.

## Ссылки
- Документация AgentMail: https://docs.agentmail.to/
- Консоль AgentMail: https://console.agentmail.to
- Репозиторий AgentMail MCP: https://github.com/agentmail-to/agentmail-mcp
- Цены: https://www.agentmail.to/pricing