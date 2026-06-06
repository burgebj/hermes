---
title: "Эскизы — одноразовые HTML‑мокапы: 2‑3 варианта дизайна для сравнения"
sidebar_label: "Sketch"
description: "Бросовые HTML‑макеты: 2‑3 варианта дизайна для сравнения"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Sketch

Быстрые HTML‑мокапы: 2‑3 варианта дизайна для сравнения.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/creative/sketch` |
| Version | `1.0.0` |
| Author | Hermes Agent (adapted from gsd-build/get-shit-done) |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `sketch`, `mockup`, `design`, `ui`, `prototype`, `html`, `variants`, `exploration`, `wireframe`, `comparison` |
| Related skills | [`spike`](/docs/user-guide/skills/bundled/software-development/software-development-spike), [`claude-design`](/docs/user-guide/skills/bundled/creative/creative-claude-design), [`popular-web-designs`](/docs/user-guide/skills/bundled/creative/creative-popular-web-designs), [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw) |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Sketch

Используй этот навык, когда пользователь хочет **увидеть направление дизайна до того, как принять окончательное решение** — исследовать идею UI/UX в виде одноразовых HTML‑мокапов. Суть — сгенерировать 2‑3 интерактивных варианта, чтобы пользователь мог сравнить визуальные направления бок о бок, а не создавать готовый к выпуску код.

Загружай, когда пользователь говорит что‑то вроде «нарисуй этот экран», «покажи, как может выглядеть X», «сравни макет A и B», «дай 2‑3 варианта этого UI», «покажи несколько вариантов», «сделай мокап перед тем, как я начну».

## Когда НЕ использовать

- Пользователь хочет готовый компонент — используй `claude-design` или сделай его правильно
- Пользователь хочет отполированный одноразовый HTML‑артефакт (лендинг, презентацию) — `claude-design`
- Пользователь хочет диаграмму — `excalidraw`, `architecture-diagram`
- Дизайн уже зафиксирован — просто реализуй его

## Если у пользователя установлен полный набор GSD

Если `gsd-sketch` появляется как соседний навык (установлен через `npx get-shit-done-cc --hermes`), отдавай предпочтение **`gsd-sketch`** для полного рабочего процесса: постоянный `.planning/sketches/` с MANIFEST, анализ в режиме frontier, аудиты согласованности между прошлыми скетчами и интеграция с остальной частью GSD. Этот навык — облегчённая автономная версия — одноразовое скетчинг без механизма состояния.

## Основной метод

```
intake  →  variants  →  head-to-head  →  pick winner (or iterate)
```

### 1. Приём (пропусти, если пользователь уже дал достаточно информации)

Перед генерацией вариантов получи три вещи — по одной за раз, а не всё сразу:

1. **Feel.** «Как это должно ощущаться? Прилагательные, эмоции, вайб.» — *«спокойный, редакционный, как Linear»* расскажет больше, чем *«минимальный»*.
2. **References.** «Какие приложения, сайты или продукты передают нужный вайб?» — реальные референсы лучше абстрактных описаний.
3. **Core action.** «Что пользователь делает на этом экране в первую очередь?» — варианты должны поддерживать это; если нет, они лишь украшение.

Кратко отрази каждый ответ перед следующим вопросом. Если пользователь сразу дал все три, переходи сразу к вариантам.

### 2. Варианты (2‑3, никогда 1, редко 4+)

Создай **2‑3 варианта** за один проход. Каждый вариант — полноценный, автономный HTML‑файл. Не описывай варианты — собирай их. Суть — сравнение.

Каждый вариант должен принимать **разную дизайнерскую позицию**, а не просто отличаться пикселями. Три хорошие оси вариантов:

- **Density:** compact / airy / ultra-dense (выбери два противоположных полюса)
- **Emphasis:** content-first / action-first / tool-first
- **Aesthetic:** editorial / utilitarian / playful
- **Layout:** single-column / sidebar / split-pane
- **Grounding:** card-based / bare-content / document-style

Выбери одну ось и разверни её. Два варианта, различающиеся только цветом акцента, — пустая трата времени, пользователь их не различит.

**Именование вариантов:** описывай позицию, а не номер.

<!-- ascii-guard-ignore -->
```
sketches/
├── 001-calm-editorial/
│   ├── index.html
│   └── README.md
├── 001-utilitarian-dense/
│   ├── index.html
│   └── README.md
└── 001-playful-split/
    ├── index.html
    └── README.md
```
<!-- ascii-guard-ignore-end -->

### 3. Сделай их реальным HTML

Каждый вариант — **один самодостаточный HTML‑файл**:

- Inline `<style>` — без сборки, без внешних CSS
- Системные шрифты или один Google Font через `<link>`
- Tailwind через CDN (`<script src="https://cdn.tailwindcss.com"></script>`) допустим
- Реалистичный фейковый контент — настоящие предложения, настоящие имена, а не «Lorem ipsum»
- **Интерактивность**: кликабельные ссылки, реальные hover‑эффекты, минимум один переход состояния (открыть/закрыть, фильтр, переключатель). Замёрзшее статическое изображение хуже спайка, чем небрежно анимированное.

Открой в браузере. Если выглядит сломанным, исправь перед тем, как показывать пользователю.

**Проверь варианты визуально — используй инструменты браузера Hermes.** Не просто пиши HTML и надеешься, что он отобразится; загрузи каждый вариант и посмотри:

```
browser_navigate(url="file:///absolute/path/to/sketches/001-calm-editorial/index.html")
browser_vision(question="Does this layout look clean and readable? Any visible bugs (overlapping text, unstyled elements, broken images)?")
```

`browser_vision` возвращает AI‑описание того, что действительно находится на странице, плюс путь к скриншоту — ловит баги вёрстки, которые не видны при чистом просмотре кода (например, не загрузившийся шрифт, свернувшийся flex‑контейнер). Исправляй и переоткрывай, пока каждый вариант не выглядит правильно.

**Базовый CSS‑reset + системный стек шрифтов** для быстрого старта:

```html
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    color: #1a1a1a;
    background: #fafafa;
    line-height: 1.5;
  }
</style>
```

### 4. README для варианта

`README.md` каждого варианта отвечает на:

```markdown
## Variant: {stance name}

### Design stance
One sentence on the principle driving this variant.

### Key choices
- Layout: ...
- Typography: ...
- Color: ...
- Interaction: ...

### Trade-offs
- Strong at: ...
- Weak at: ...

### Best for
- The kind of user or use case this variant actually serves
```

### 5. Сравнение «лицом к лицу»

После создания всех вариантов представь их в виде сравнения. Не просто перечисляй — **вырази мнение**:

```markdown
## Three takes on the home screen

| Dimension | Calm editorial | Utilitarian dense | Playful split |
|-----------|----------------|-------------------|---------------|
| Density   | Low            | High              | Medium        |
| Primary action visibility | Low | High | Medium |
| Scan-ability | High | Medium | Low |
| Feel | Calm, trusted | Sharp, tool-like | Inviting, energetic |

**My take:** Utilitarian dense for power users, calm editorial for content-forward audiences. Playful split is weakest — tries to do both and commits to neither.
```

Позволь пользователю выбрать победителя, объединить два в гибрид или запросить ещё один раунд.

## Темизация (когда у проекта есть визуальная идентичность)

Если у пользователя уже есть тема (цвета, шрифты, токены), помести общие токены в `sketches/themes/tokens.css` и `@import` их в каждый вариант. Держи токены минимальными:

```css
/* sketches/themes/tokens.css */
:root {
  --color-bg: #fafafa;
  --color-fg: #1a1a1a;
  --color-accent: #0066ff;
  --color-muted: #666;
  --radius: 8px;
  --font-display: "Inter", sans-serif;
  --font-body: -apple-system, BlinkMacSystemFont, sans-serif;
}
```

Не переусложняй одноразовый скетч — обычно хватает трёх цветов и одного шрифта.

## Панель интерактивности

Скетч считается достаточно интерактивным, когда пользователь может:

1. **Кликнуть основное действие** и увидеть видимый результат (изменение состояния, модальное окно, toast, лёгкая навигация)
2. **Увидеть один значимый переход состояния** (фильтрация списка, переключение режима, открытие/закрытие панели)
3. **Навести курсор на узнаваемые affordances** (кнопки, строки, вкладки)

Больше — переусложнение одноразового макета. Меньше — просто скриншот.

## Frontier mode (выбор, что скетчить дальше)

Если скетчи уже существуют и пользователь спрашивает «что мне скетчить дальше?»:

- **Consistency gaps** — два победных варианта из разных скетчей сделали независимые решения, которые ещё не объединены
- **Unsketched screens** — упомянутые, но никогда не исследованные
- **State coverage** — пройден happy‑path, но не пустой / loading / error / 1000‑items
- **Responsive gaps** — проверено в одном viewport; как будет на мобильном / ультрашироком?
- **Interaction patterns** — статические макеты есть; переходы, drag, scroll‑поведение — нет

Предложи 2‑4 названных кандидата. Позволь пользователю выбрать.

## Вывод

- Создай `sketches/` (или `.planning/sketches/`, если пользователь использует конвенции GSD) в корне репозитория
- По одной подпапке на вариант: `NNN-stance-name/index.html` + `README.md`
- Сообщи пользователю, как их открыть: `open sketches/001-calm-editorial/index.html` на macOS, `xdg-open` на Linux, `start` на Windows
- Держи варианты одноразовыми — скетч, который захотелось сохранить, следует перенести в реальный код проекта, а не оставлять как активный ресурс

**Типичная последовательность инструментов для одного варианта:**

```
terminal("mkdir -p sketches/001-calm-editorial")
write_file("sketches/001-calm-editorial/index.html", "<!doctype html>...")
write_file("sketches/001-calm-editorial/README.md", "## Variant: Calm editorial\n...")
browser_navigate(url="file://$(pwd)/sketches/001-calm-editorial/index.html")
browser_vision(question="How does this look? Any obvious layout issues?")
```

Повтори для каждого варианта, затем представь таблицу сравнения.

## Атрибуция

Adapted from the GSD (Get Shit Done) project's `/gsd-sketch` workflow — MIT © 2025 Lex Christopherson ([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)). The full GSD system ships persistent sketch state, theme/variant pattern references, and consistency-audit workflows; install with `npx get-shit-done-cc --hermes --global`.