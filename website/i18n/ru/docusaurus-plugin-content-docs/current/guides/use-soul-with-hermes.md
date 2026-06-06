---
sidebar_position: 7
title: "Используй SOUL.md с Hermes"
description: "Как использовать SOUL.md для формирования голоса Hermes Agent по умолчанию, что должно в нём быть и чем он отличается от AGENTS.md и /personality"
---

# Использовать SOUL.md с Hermes

`SOUL.md` — **основная идентичность** твоего экземпляра Hermes. Это первое, что попадает в системный запрос — он определяет, кто такой агент, как он говорит и чего избегает.

Если ты хочешь, чтобы Hermes каждый раз был похожим помощником, или если ты хочешь полностью заменить персонаж Hermes своим — этот файл как раз для этого.

## Для чего нужен SOUL.md

Используй `SOUL.md` для:
- тона
- личности
- стиля общения
- того, насколько прямым или тёплым должен быть Hermes
- чего Hermes должен избегать стилистически
- того, как Hermes относится к неопределённости, несогласию и неоднозначности

Короче:
- `SOUL.md` — это о том, кто такой Hermes и как он говорит

## Для чего НЕ нужен SOUL.md

Не используй его для:
- специфических для репозитория правил кодирования
- путей к файлам
- команд
- портов сервисов
- заметок об архитектуре
- инструкций рабочего процесса проекта

Это относится к `AGENTS.md`.

Хорошее правило:
- если это должно применяться везде, помещай в `SOUL.md`
- если относится только к одному проекту, помещай в `AGENTS.md`

## Где он находится

Hermes сейчас использует только глобальный файл SOUL для текущего экземпляра:

```text
~/.hermes/SOUL.md
```

Если ты запускаешь Hermes с пользовательским домашним каталогом, он будет находиться здесь:

```text
$HERMES_HOME/SOUL.md
```

## Поведение при первом запуске

Hermes автоматически создаёт стартовый `SOUL.md`, если такого файла ещё нет.

Это значит, что большинство пользователей теперь начинают с реального файла, который можно сразу прочитать и отредактировать.

Важно:
- если у тебя уже есть `SOUL.md`, Hermes не перезапишет его
- если файл существует, но пуст, Hermes не добавит из него ничего в запрос

## Как Hermes использует его

Когда Hermes начинает сессию, он читает `SOUL.md` из `HERMES_HOME`, сканирует его на наличие шаблонов инъекции в запрос, при необходимости обрезает и использует как **идентичность агента** — слот №1 в системном запросе. Это значит, что `SOUL.md` полностью заменяет встроенный текст идентичности по умолчанию.

Если `SOUL.md` отсутствует, пуст или не может быть загружен, Hermes переходит к встроенной идентичности по умолчанию.

Никакой обёртки вокруг файла не добавляется. Содержимое имеет значение — пиши так, как хочешь, чтобы твой агент думал и говорил.

## Хорошее первое редактирование

Если ничего больше не делать, открой файл и измени несколько строк, чтобы он стал похож на тебя.

Например:

```markdown
You are direct, calm, and technically precise.
Prefer substance over politeness theater.
Push back clearly when an idea is weak.
Keep answers compact unless deeper detail is useful.
```

Этого достаточно, чтобы заметно изменить ощущение от Hermes.

## Примеры стилей

### 1. Прагматичный инженер

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

### 2. Партнёр‑исследователь

```markdown
You are a thoughtful research collaborator.
You are curious, honest about uncertainty, and excited by unusual ideas.

## Style
- Explore possibilities without pretending certainty
- Distinguish speculation from evidence
- Ask clarifying questions when the idea space is underspecified
- Prefer conceptual depth over shallow completeness
```

### 3. Учитель / объяснитель

```markdown
You are a patient technical teacher.
You care about understanding, not performance.

## Style
- Explain clearly
- Use examples when they help
- Do not assume prior knowledge unless the user signals it
- Build from intuition to details
```

### 4. Жёсткий рецензент

```markdown
You are a rigorous reviewer.
You are fair, but you do not soften important criticism.

## Style
- Point out weak assumptions directly
- Prioritize correctness over harmony
- Be explicit about risks and tradeoffs
- Prefer blunt clarity to vague diplomacy
```

## Что делает `SOUL.md` сильным?

Сильный `SOUL.md`:
- стабилен
- широко применим
- конкретен в голосе
- не перегружен временными инструкциями

Слабый `SOUL.md`:
- полон деталей проекта
- противоречив
- пытается микроменеджировать каждую форму ответа
- в основном состоит из общих заполнителей вроде «быть полезным» и «быть ясным»

Hermes уже старается быть полезным и ясным. `SOUL.md` должен добавить реальную личность и стиль, а не просто повторять очевидные настройки по умолчанию.

## Предлагаемая структура

Заголовки не обязательны, но помогают.

Простая структура, которая хорошо работает:

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

## `SOUL.md` vs `/personality`

Это взаимодополняющие вещи.

Используй `SOUL.md` для своей постоянной базовой линии.
Используй `/personality` для временных переключений режима.

Примеры:
- твой базовый SOUL — прагматичный и прямой
- затем на одну сессию ты используешь `/personality teacher`
- позже возвращаешься к базовому голосу без изменения файла

## `SOUL.md` vs `AGENTS.md`

Это самая распространённая ошибка.

### Помести это в `SOUL.md`
- «Будь прямым».
- «Избегай рекламного языка».
- «Отдавай предпочтение коротким ответам, если только глубина не нужна».
- «Отталкивай пользователя, когда он ошибается».

### Помести это в `AGENTS.md`
- «Используй pytest, а не unittest».
- «Фронтенд находится в `frontend/`.»
- «Никогда не редактируй миграции напрямую».
- «API работает на порту 8000».

## Как редактировать

```bash
nano ~/.hermes/SOUL.md
```

или

```bash
vim ~/.hermes/SOUL.md
```

Затем перезапусти Hermes или начни новую сессию.

## Практический рабочий процесс

1. Начни с созданного по умолчанию файла
2. Удали всё, что не соответствует желаемому голосу
3. Добавь 4–8 строк, чётко определяющих тон и настройки
4. Поговори с Hermes некоторое время
5. Скорректируй, исходя из того, что всё ещё кажется не тем

Такой итеративный подход работает лучше, чем попытка сразу спроектировать идеальную личность.

## Устранение неполадок

### Я отредактировал `SOUL.md`, но Hermes звучит так же

Проверь:
- ты редактировал `~/.hermes/SOUL.md` или `$HERMES_HOME/SOUL.md`
- а не какой‑то локальный `SOUL.md` в репозитории
- файл не пуст
- твоя сессия была перезапущена после правки
- наложение `/personality` не переопределяет результат

### Hermes игнорирует части моего `SOUL.md`

Возможные причины:
- инструкции более высокого приоритета переопределяют его
- файл содержит противоречивые указания
- файл слишком длинный и был обрезан
- часть текста выглядит как контент инъекции и может быть заблокирована или изменена сканером

### Мой `SOUL.md` стал слишком специфичным для проекта

Перенеси проектные инструкции в `AGENTS.md` и оставь `SOUL.md` сфокусированным на идентичности и стиле.

## Связанные документы

- [Personality & SOUL.md](/user-guide/features/personality)
- [Context Files](/user-guide/features/context-files)
- [Configuration](/user-guide/configuration)
- [Tips & Best Practices](/guides/tips)