---
sidebar_position: 9
title: "Особистість & ДУША.md"
description: "Налаштуй персональність Hermes Agent за допомогою глобального SOUL.md, вбудованих персональностей та власних визначень персонажів"
---

# Personality & SOUL.md

Персональність Hermes Agent повністю налаштовується. `SOUL.md` — це **основна ідентичність**: вона перша у системному підказці і визначає, хто такий агент.

- `SOUL.md` — стійкий файл персонажу, який живе в `HERMES_HOME` і слугує ідентичністю агента (слот #1 у системній підказці)
- вбудовані або користувацькі пресети `/personality` — накладки системних підказок рівня сесії

Якщо ти хочеш змінити, ким є Hermes — або замінити його на зовсім іншу агент‑персональність — відредагуй `SOUL.md`.

## How SOUL.md works now

Hermes тепер автоматично створює типову `SOUL.md` у:

```text
~/.hermes/SOUL.md
```

Точніше, використовується поточний `HERMES_HOME` інстансу, тому якщо ти запускаєш Hermes з кастомною домашньою текою, буде використано:

```text
$HERMES_HOME/SOUL.md
```

### Important behavior

- **SOUL.md — це основна ідентичність агента.** Вона займає слот #1 у системній підказці, замінюючи жорстко закодовану типову ідентичність.
- Hermes автоматично створює стартовий `SOUL.md`, якщо його ще немає.
- Існуючі користувацькі файли `SOUL.md` ніколи не перезаписуються.
- Hermes завантажує `SOUL.md` лише з `HERMES_HOME`.
- Hermes не шукає `SOUL.md` у поточному робочому каталозі.
- Якщо `SOUL.md` існує, але порожній, або його не вдається завантажити, Hermes переходить до вбудованої типової ідентичності.
- Якщо `SOUL.md` має вміст, цей вміст вставляється дослівно після сканування безпеки та обрізки.
- `SOUL.md` **не** дублюється у розділі файлів контексту — він з’являється лише один раз, як ідентичність.

Таким чином `SOUL.md` є справжньою ідентичністю для кожного користувача або інстансу, а не лише додатковим шаром.

## Why this design

Так забезпечується передбачуваність персональності.

Якби Hermes завантажував `SOUL.md` з будь‑якої теки, в якій ти його запустив, твоя персональність могла б змінюватися несподівано між проєктами. Завантажуючи лише з `HERMES_HOME`, персональність належить саме інстансу Hermes.

Це також спрощує навчання користувачів:

- «Відредагуй `~/.hermes/SOUL.md`, щоб змінити типову персональність Hermes.»

## Where to edit it

Для більшості користувачів:

```bash
~/.hermes/SOUL.md
```

Якщо ти використовуєш кастомну домашню теку:

```bash
$HERMES_HOME/SOUL.md
```

## What should go in SOUL.md?

Використовуй його для довготривалої інструкції щодо голосу та персональності, наприклад:

- тон
- стиль спілкування
- рівень прямоти
- типова манера взаємодії
- чого уникати стилістично
- як Hermes має поводитися у випадку невизначеності, розбіжностей або неоднозначності

Використовуй його менше для:

- одноразових інструкцій проєкту
- шляхів до файлів
- конвенцій репозиторію
- тимчасових деталей робочого процесу

Це належить до `AGENTS.md`, а не `SOUL.md`.

## Good SOUL.md content

Хороший файл `SOUL.md` є:

- стабільним у різних контекстах
- достатньо широким, щоб застосовуватись у багатьох розмовах
- достатньо конкретним, щоб суттєво формувати голос
- зосередженим на комунікації та ідентичності, а не на інструкціях щодо завдань

### Example

```markdown
# Personality

You are a pragmatic senior engineer with strong taste.
You optimize for truth, clarity, and usefulness over politeness theater.

## Style
- Be direct without being cold
- Prefer substance over filler
- Push back when something is a bad idea
- Admit uncertainty plainly
- Keep explanations compact unless depth is useful

## What to avoid
- Sycophancy
- Hype language
- Repeating the user's framing if it's wrong
- Overexplaining obvious things

## Technical posture
- Prefer simple systems over clever systems
- Care about operational reality, not idealized architecture
- Treat edge cases as part of the design, not cleanup
```

## What Hermes injects into the prompt

Вміст `SOUL.md` потрапляє безпосередньо у слот #1 системної підказки — позицію ідентичності агента. Жодних додаткових обгорток не додається.

Вміст проходить:

- сканування на ін’єкції підказки
- обрізку, якщо він занадто великий

Якщо файл порожній, містить лише пробіли або не може бути прочитаний, Hermes переходить до вбудованої типової ідентичності («You are Hermes Agent, an intelligent AI assistant created by Nous Research…»). Така відмова також застосовується, коли встановлено `skip_context_files` (наприклад, у контекстах subagent/delegation).

## Security scanning

`SOUL.md` сканується так само, як інші файли контексту, на предмет шаблонів ін’єкції підказки перед включенням.

Тому варто залишати його зосередженим на персонажі/голосі, а не на спробах підмітати дивні мета‑інструкції.

## SOUL.md vs AGENTS.md

Це найважливіша різниця.

### SOUL.md
Використовуй для:

- ідентичності
- тону
- стилю
- типових налаштувань комунікації
- поведінки на рівні персональності

### AGENTS.md
Використовуй для:

- архітектури проєкту
- конвенцій кодування
- уподобань інструментів
- робочих процесів, специфічних для репозиторію
- команд, портів, шляхів, нотаток щодо розгортання

Корисне правило:

- якщо це має слідувати за тобою скрізь, це `SOUL.md`
- якщо це прив’язано до проєкту, це `AGENTS.md`

## SOUL.md vs `/personality`

`SOUL.md` — твоя довготривала типова персональність.

`/personality` — накладка рівня сесії, яка змінює або доповнює поточну системну підказку.

Отже:

- `SOUL.md` = базовий голос
- `/personality` = тимчасове перемикання режиму

### Приклади

- тримай практичний типовий `SOUL.md`, а потім використай `/personality teacher` для репетиторської розмови
- тримай стислий `SOUL.md`, а потім використай `/personality creative` для мозкового штурму

## Built-in personalities

Hermes постачається з вбудованими персональностями, які можна переключати за допомогою `/personality`.

| Name | Description |
|------|-------------|
| **helpful** | Дружелюбний, універсальний помічник |
| **concise** | Короткі, по суті відповіді |
| **technical** | Детальний, точний технічний експерт |
| **creative** | Інноваційне, нестандартне мислення |
| **teacher** | Терплячий викладач з чіткими прикладами |
| **kawaii** | Милі вирази, блиск та ентузіазм ★ |
| **catgirl** | Неко‑чан з котячими виразами, ня~ |
| **pirate** | Капітан Hermes, технічно підкований пірат |
| **shakespeare** | Бардівська проза з драматичним відтінком |
| **surfer** | Повністю chill‑бро вайб |
| **noir** | Жорстка детективна нарація |
| **uwu** | Максимальна милота з uwu‑мовою |
| **philosopher** | Глибоке розмірковування над кожним запитом |
| **hype** | МАКСИМАЛЬНА ЕНЕРГІЯ ТА ЗАХОПЛЕННЯ!!! |

## Switching personalities with commands

### CLI

```text
/personality
/personality concise
/personality technical
```

### Messaging platforms

```text
/personality teacher
```

Це зручні накладки, але твій глобальний `SOUL.md` все одно задає Hermes постійну типову персональність, якщо накладка не змінює її суттєво.

## Custom personalities in config

Ти також можеш визначити іменовані кастомні персональності у `~/.hermes/config.yaml` під `agent.personalities`.

```yaml
agent:
  personalities:
    codereviewer: >
      You are a meticulous code reviewer. Identify bugs, security issues,
      performance concerns, and unclear design choices. Be precise and constructive.
```

Потім перемкнись на неї за допомогою:

```text
/personality codereviewer
```

## Recommended workflow

Сильна типова конфігурація:

1. Тримай продуманий глобальний `SOUL.md` у `~/.hermes/SOUL.md`
2. Розміщуй інструкції проєкту в `AGENTS.md`
3. Використовуй `/personality` лише коли потрібне тимчасове перемикання режиму

Це дає тобі:

- стабільний голос
- поведінку, специфічну для проєкту, там, де вона належить
- тимчасовий контроль за потреби

## How personality interacts with the full prompt

На високому рівні стек підказок включає:

1. **SOUL.md** (ідентичність агента — або вбудована відмова, якщо `SOUL.md` недоступний)
2. керівництво щодо інструментально‑обізнаної поведінки
3. пам’ять/контекст користувача
4. керівництво щодо навичок
5. файли контексту (`AGENTS.md`, `.cursorrules`)
6. timestamp
7. підказки, специфічні для платформи
8. додаткові накладки системних підказок, такі як `/personality`

`SOUL.md` — фундамент, на якому будуються всі інші шари.

## Related docs

- [Context Files](/user-guide/features/context-files)
- [Configuration](/user-guide/configuration)
- [Tips & Best Practices](/guides/tips)
- [SOUL.md Guide](/guides/use-soul-with-hermes)

## CLI appearance vs conversational personality

Розмовна персональність і вигляд у CLI — це окремі речі:

- `SOUL.md`, `agent.system_prompt` та `/personality` впливають на те, як Hermes говорить
- `display.skin` та `/skin` впливають на те, як Hermes виглядає в терміналі

Для вигляду в терміналі дивись [Skins & Themes](./skins.md).