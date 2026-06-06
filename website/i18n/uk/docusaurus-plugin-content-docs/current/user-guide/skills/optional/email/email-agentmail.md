---
title: "Agentmail — Дай агенту його власну виділену поштову скриньку через AgentMail"
sidebar_label: "Agentmail"
description: "Надай агенту його власну виділену електронну поштову скриньку через AgentMail"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Agentmail

Надай агенту власну виділену поштову скриньку за допомогою AgentMail. Надсилай, отримуй і керуй електронною поштою автономно, використовуючи адреси, що належать агенту (наприклад, hermes-agent@agentmail.to).

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/email/agentmail` |
| Path | `optional-skills/email/agentmail` |
| Version | `1.0.0` |
| Platforms | linux, macos, windows |
| Tags | `email`, `communication`, `agentmail`, `mcp` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# AgentMail — Поштові скриньки, що належать агенту

## Вимоги

- **AgentMail API key** (обов’язково) — зареєструйся на https://console.agentmail.to (безкоштовний тариф: 3 скриньки, 3 000 листів/міс; платні плани від $20/міс)
- Node.js 18+ (для сервера MCP)

## Коли використовувати
Використовуй цю навичку, коли потрібно:
- Надати агенту власну виділену електронну адресу
- Надсилати листи автономно від імені агента
- Отримувати та читати вхідні листи
- Керувати ланцюжками листів та розмовами
- Реєструватися в сервісах або проходити автентифікацію через електронну пошту
- Спілкуватися з іншими агентами або людьми через електронну пошту

Це НЕ для читання особистої пошти користувача (для цього використай himalaya або Gmail).
AgentMail надає агенту власну ідентичність та скриньку.

## Налаштування

### 1. Отримай API‑ключ
- Перейди на https://console.agentmail.to
- Створи обліковий запис і згенеруй API‑ключ (починається з `am_`)

### 2. Налаштуй сервер MCP
Додай до `~/.hermes/config.yaml` (встав свій реальний ключ — змінні середовища MCP не розширюються з .env):
```yaml
mcp_servers:
  agentmail:
    command: "npx"
    args: ["-y", "agentmail-mcp"]
    env:
      AGENTMAIL_API_KEY: "am_your_key_here"
```

### 3. Перезапусти Hermes
```bash
hermes
```
Тепер усі 11 інструментів AgentMail доступні автоматично.

## Доступні інструменти (через MCP)

| Інструмент | Опис |
|------|-------------|
| `list_inboxes` | Показати всі скриньки агента |
| `get_inbox` | Отримати деталі конкретної скриньки |
| `create_inbox` | Створити нову скриньку (отримати реальну електронну адресу) |
| `delete_inbox` | Видалити скриньку |
| `list_threads` | Показати листові теми в скриньці |
| `get_thread` | Отримати конкретну листову тему |
| `send_message` | Надіслати новий лист |
| `reply_to_message` | Відповісти на існуючий лист |
| `forward_message` | Переслати лист |
| `update_message` | Оновити мітки/статус листа |
| `get_attachment` | Завантажити вкладення листа |

## Процедура

### Створити скриньку та надіслати лист
1. Створи виділену скриньку:
   - Використай `create_inbox` з ім’ям користувача (наприклад, `hermes-agent`)
   - Агент отримає адресу: `hermes-agent@agentmail.to`
2. Надішли лист:
   - Використай `send_message` з `inbox_id`, `to`, `subject`, `text`
3. Перевір відповіді:
   - Використай `list_threads`, щоб побачити вхідні розмови
   - Використай `get_thread`, щоб прочитати конкретну тему

### Перевірити вхідну пошту
1. Використай `list_inboxes`, щоб знайти ID своєї скриньки
2. Використай `list_threads` з цим ID, щоб побачити розмови
3. Використай `get_thread`, щоб прочитати тему і її повідомлення

### Відповісти на лист
1. Отримай тему за допомогою `get_thread`
2. Використай `reply_to_message` з ID повідомлення та текстом відповіді

## Приклади робочих процесів

**Реєстрація в сервісі:**
```
1. create_inbox (username: "signup-bot")
2. Use the inbox address to register on the service
3. list_threads to check for verification email
4. get_thread to read the verification code
```

**Взаємодія агент‑людина:**
```
1. create_inbox (username: "hermes-outreach")
2. send_message (to: user@example.com, subject: "Hello", text: "...")
3. list_threads to check for replies
```

## Підводні камені
- Безкоштовний тариф обмежений 3 скриньками та 3 000 листами/міс
- Листи надсилаються з домену `@agentmail.to` у безкоштовному тарифі (кастомні домени у платних планах)
- Потрібен Node.js (18+) для сервера MCP (`npx -y agentmail-mcp`)
- Пакет `mcp` для Python має бути встановлений: `pip install mcp`
- Реальний час вхідної пошти (webhooks) вимагає публічного сервера — замість цього використай опитування `list_threads` через cronjob для особистого використання

## Перевірка
Після налаштування протестуй за допомогою:
```
hermes --toolsets mcp -q "Create an AgentMail inbox called test-agent and tell me its email address"
```
Ти маєш побачити повернену нову адресу скриньки.

## Посилання
- AgentMail docs: https://docs.agentmail.to/
- AgentMail console: https://console.agentmail.to
- AgentMail MCP repo: https://github.com/agentmail-to/agentmail-mcp
- Pricing: https://www.agentmail.to/pricing