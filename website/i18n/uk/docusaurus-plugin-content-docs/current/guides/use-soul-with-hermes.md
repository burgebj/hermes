---
sidebar_position: 7
title: "Використовуй SOUL.md з Hermes"
description: "Як використовувати SOUL.md для формування голосу за замовчуванням Hermes Agent, що має там бути, і чим це відрізняється від AGENTS.md та /personality."
---

# Використовуй SOUL.md з Hermes

`SOUL.md` — це **основна ідентичність** твоєї інстанції Hermes. Це перше, що бачить системний підказник — він визначає, хто такий агент, як він говорить і чого уникає.

Якщо ти хочеш, щоб Hermes відчувався як один і той самий помічник щоразу, коли ти з ним спілкуєшся — або якщо ти хочеш повністю замінити персонаж Hermes на свій власний — це файл, який треба використовувати.

## Для чого потрібен SOUL.md

Використовуй `SOUL.md` для:
- тону
- особистості
- стилю спілкування
- того, наскільки прямим або теплим має бути Hermes
- чого Hermes має уникати стилістично
- як Hermes має ставитися до невизначеності, незгоди та неоднозначності

Коротко:
- `SOUL.md` стосується того, хто такий Hermes і як Hermes говорить

## Для чого НЕ потрібен SOUL.md

Не використовуйте його для:
- специфічних для репозиторію правил кодування
- шляхів до файлів
- команд
- портів сервісів
- нотаток про архітектуру
- інструкцій щодо робочого процесу проєкту

Це належить до `AGENTS.md`.

Хороше правило:
- якщо це має застосовуватись скрізь, розмісти в `SOUL.md`
- якщо це стосується лише одного проєкту, розмісти в `AGENTS.md`

## Де він розташований

Hermes зараз використовує лише глобальний файл SOUL для поточної інстанції:

```text
~/.hermes/SOUL.md
```

Якщо ти запускаєш Hermes з власним домашнім каталогом, це буде:

```text
$HERMES_HOME/SOUL.md
```

## Поведінка при першому запуску

Hermes автоматично створює стартовий `SOUL.md`, якщо такого ще немає.

Тобто більшість користувачів тепер починають з реального файлу, який можна одразу читати та редагувати.

**Важливо**:
- якщо у тебе вже є `SOUL.md`, Hermes його не перезаписує
- якщо файл існує, але порожній, Hermes нічого не додає з нього до підказки

## Як Hermes його використовує

Коли Hermes запускає сесію, він читає `SOUL.md` з `HERMES_HOME`, сканує його на шаблони ін’єкції підказки, за потреби обрізає і використовує як **ідентичність агента** — слот #1 у системному підказнику. Це означає, що `SOUL.md` повністю замінює вбудований текст ідентичності за замовчуванням.

Якщо `SOUL.md` відсутній, порожній або не може бути завантажений, Hermes переходить до вбудованої ідентичності за замовчуванням.

Навколо файлу не додається жодна обгортка мови. Важливий сам вміст — напиши так, як ти хочеш, щоб твій агент думав і говорив.

## Хороше перше редагування

Якщо нічого іншого не робити, відкрий файл і зміни лише кілька рядків, щоб він відчувався твоїм.

Наприклад:

```markdown
You are direct, calm, and technically precise.
Prefer substance over politeness theater.
Push back clearly when an idea is weak.
Keep answers compact unless deeper detail is useful.
```

Саме це може помітно змінити, як Hermes себе проявляє.

## Приклади стилів

### 1. Практичний інженер

```markdown
You are a pragmatic senior engineer.
You care more about correctness and operational reality than sounding impressive.

## Style
- Be direct
- Be concise unless complexity requires depth
- Say when something is a bad idea
- Prefer practical tradeoffs over idealized abstractions

## Avoid
- Sycophancy
- Hype language
- Overexplaining obvious things
```

### 2. Партнер‑дослідник

```markdown
You are a thoughtful research collaborator.
You are curious, honest about uncertainty, and excited by unusual ideas.

## Style
- Explore possibilities without pretending certainty
- Distinguish speculation from evidence
- Ask clarifying questions when the idea space is underspecified
- Prefer conceptual depth over shallow completeness
```

### 3. Викладач / пояснювач

```markdown
You are a patient technical teacher.
You care about understanding, not performance.

## Style
- Explain clearly
- Use examples when they help
- Do not assume prior knowledge unless the user signals it
- Build from intuition to details
```

### 4. Суворий рецензент

```markdown
You are a rigorous reviewer.
You are fair, but you do not soften important criticism.

## Style
- Point out weak assumptions directly
- Prioritize correctness over harmony
- Be explicit about risks and tradeoffs
- Prefer blunt clarity to vague diplomacy
```

## Що робить SOUL.md сильним?

Сильний `SOUL.md`:
- стабільний
- широко застосовний
- конкретний у голосі
- не перевантажений тимчасовими інструкціями

Слабкий `SOUL.md`:
- сповнений деталями проєкту
- суперечливий
- намагається мікроменеджити кожну форму відповіді
- в основному заповнений загальними фразами типу «будь корисним» та «будь чітким»

Hermes вже намагається бути корисним і чітким. `SOUL.md` має додати реальну особистість і стиль, а не лише повторювати очевидні налаштування за замовчуванням.

## Запропонована структура

Ти не зобов’язаний використовувати заголовки, але вони допомагають.

Проста структура, що добре працює:

```markdown
# Identity
Who Hermes is.

# Style
How Hermes should sound.

# Avoid
What Hermes should not do.

# Defaults
How Hermes should behave when ambiguity appears.
```

## SOUL.md vs /personality

Це доповнює одне одного.

Використовуй `SOUL.md` для довготривалої базової лінії.
Використовуй `/personality` для тимчасових перемикань режиму.

Приклади:
- твоя базова SOUL — практична і пряма
- потім для однієї сесії ти використовуєш `/personality teacher`
- пізніше повертаєшся назад, не змінюючи базовий файл голосу

## SOUL.md vs AGENTS.md

Це найпоширеніша помилка.

### Розмісти це в SOUL.md
- “Be direct.”
- “Avoid hype language.”
- “Prefer short answers unless depth helps.”
- “Push back when the user is wrong.”

### Розмісти це в AGENTS.md
- “Use pytest, not unittest.”
- “Frontend lives in `frontend/`.”
- “Never edit migrations directly.”
- “The API runs on port 8000.”

## Як редагувати

```bash
nano ~/.hermes/SOUL.md
```

або

```bash
vim ~/.hermes/SOUL.md
```

Потім перезапусти Hermes або запусти нову сесію.

## Практичний робочий процес

1. Почни з створеного за замовчуванням файлу
2. Видали все, що не відповідає потрібному голосу
3. Додай 4–8 рядків, які чітко визначають тон і налаштування
4. Поспілкуйся з Hermes деякий час
5. Скоригуй, виходячи з того, що ще здається недоречним

Такий ітеративний підхід працює краще, ніж спроба створити ідеальну особистість за один раз.

## Усунення проблем

### Я відредагував SOUL.md, а Hermes все одно звучить однаково

Перевір:
- ти редагував `~/.hermes/SOUL.md` або `$HERMES_HOME/SOUL.md`
- а не якийсь локальний `SOUL.md` у репозиторії
- файл не порожній
- твоя сесія була перезапущена після редагування
- накладка `/personality` не переважає результат

### Hermes ігнорує частини мого SOUL.md

Можливі причини:
- інструкції вищого пріоритету їх перекривають
- файл містить суперечливі вказівки
- файл занадто довгий і був обрізаний
- частина тексту схожа на вміст ін’єкції підказки і може бути заблокована або змінена сканером

### Мій SOUL.md став надто специфічним для проєкту

Перенеси проєктні інструкції в `AGENTS.md` і залиш `SOUL.md` зосередженим на ідентичності та стилі.

## Пов’язані документи

- [Personality & SOUL.md](/user-guide/features/personality)
- [Context Files](/user-guide/features/context-files)
- [Configuration](/user-guide/configuration)
- [Tips & Best Practices](/guides/tips)