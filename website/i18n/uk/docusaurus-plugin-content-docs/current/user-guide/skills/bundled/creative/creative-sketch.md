---
title: "Sketch — одноразові HTML‑мокапи: 2‑3 варіанти дизайну для порівняння"
sidebar_label: "Sketch"
description: "Одноразові HTML‑мокапи: 2‑3 варіанти дизайну для порівняння"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Sketch

Тимчасові HTML‑мокапи: 2‑3 варіанти дизайну для порівняння.

## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/creative/sketch` |
| Версія | `1.0.0` |
| Автор | Hermes Agent (adapted from gsd-build/get-shit-done) |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `sketch`, `mockup`, `design`, `ui`, `prototype`, `html`, `variants`, `exploration`, `wireframe`, `comparison` |
| Пов’язані навички | [`spike`](/docs/user-guide/skills/bundled/software-development/software-development-spike), [`claude-design`](/docs/user-guide/skills/bundled/creative/creative-claude-design), [`popular-web-designs`](/docs/user-guide/skills/bundled/creative/creative-popular-web-designs), [`excalidraw`](/docs/user-guide/skills/bundled/creative/creative-excalidraw) |

## Довідка: повний SKILL.md

:::info
Нижче наведено повний опис навички, який Hermes завантажує під час її активації. Це інструкції, які бачить агент, коли навичка активна.
:::

# Sketch

Використовуй цю навичку, коли користувач хоче **побачити напрямок дизайну перед тим, як закріпити його** — дослідження UI/UX‑ідеї у вигляді тимчасових HTML‑мокапів. Мета — створити 2‑3 інтерактивних варіанти, щоб користувач міг порівняти візуальні напрямки бок‑о‑бок, а не отримати готовий до випуску код.

Запускай, коли користувач каже типу «sketch this screen», «show me what X could look like», «compare layout A vs B», «give me 2‑3 takes on this UI», «let me see some variants», «mockup this before I build».

## Коли НЕ слід використовувати

- Користувач хоче готовий продакшн‑компонент — використай `claude-design` або реалізуй його самостійно
- Користувач хоче полірований одноразовий HTML‑артефакт (лендінг, презентація) — `claude-design`
- Потрібна діаграма — `excalidraw`, `architecture-diagram`
- Дизайн вже затверджений — просто реалізуй його

## Якщо у користувача встановлена повна система GSD

Якщо `gsd-sketch` присутній як sibling‑skill (встановлено через `npx get-shit-done-cc --hermes`), віддавай перевагу **`gsd-sketch`** для повного робочого процесу: постійна папка `.planning/sketches/` з MANIFEST, аналіз у frontier‑mode, аудити узгодженості між попередніми скетчами та інтеграція з рештою GSD. Ця навичка — легка автономна версія, що дозволяє робити одноразові скетчі без механізмів стану.

## Основний метод

```
intake  →  variants  →  head-to-head  →  pick winner (or iterate)
```

### 1. Збір інформації (пропусти, якщо користувач вже надав усе)

Перед створенням варіантів отримай три речі — по одній, а не одразу всі:

1. **Настрій.** «Яким має бути настрій? Прикметники, емоції, вібрація.» — *«calm, editorial, like Linear»* розповідає більше, ніж *«minimal»*.
2. **Референси.** «Які додатки, сайти або продукти передають потрібний тобі настрій?» — реальні референси кращі за абстрактні описи.
3. **Ключова дія.** «Що користувач робить на цьому екрані в першу чергу?» — усі варіанти мають підтримувати цю дію; якщо ні — це лише декорація.

Коротко підсумуй відповідь перед наступним запитанням. Якщо користувач вже надав усі три відповіді, переходь одразу до варіантів.

### 2. Варіанти (2‑3, ніколи 1, рідко 4+)

Створи **2‑3 варіанти** за один раз. Кожен варіант — повний, автономний HTML‑файл. Не описуй варіанти — створюй їх. Мета — порівняння.

Кожен варіант має займати **різну дизайнерську позицію**, а не просто різні піксельні значення. Три хороші осі варіантності:

- **Щільність:** compact / airy / ultra‑dense (вибери два протилежних полюса)
- **Акцент:** content‑first / action‑first / tool‑first
- **Естетика:** editorial / utilitarian / playful
- **Макет:** single‑column / sidebar / split‑pane
- **Основа:** card‑based / bare‑content / document‑style

Обери одну вісь і розвивай її. Два варіанти, що відрізняються лише кольором акценту, — марна трата часу, користувач їх не розрізнить.

**Назви варіантів:** описуй позицію, а не номер.

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

### 3. Реалізуй справжній HTML

Кожен варіант — **один самодостатній HTML‑файл**:

- Inline‑`<style>` — без етапу збірки, без зовнішнього CSS
- Системні шрифти або один Google Font через `<link>`
- Tailwind через CDN (`<script src="https://cdn.tailwindcss.com"></script>`) — допускається
- Реалістичний фейковий контент — справжні речення, справжні імена, а не «Lorem ipsum»
- **Інтерактивність:** клікабельні посилання, реальні hover‑ефекти, принаймні один перехід стану (відкриття/закриття, фільтр, перемикач). Заморожене статичне зображення гірше, ніж неакуратно анімоване.

Відкрий у браузері. Якщо виглядає зламано, виправ перед показом користувачу.

**Перевірка варіантів візуально — використай інструменти браузера Hermes.** Не просто пиши HTML і сподівайся, що він відрендериться; завантаж кожен варіант і подивись:

```
browser_navigate(url="file:///absolute/path/to/sketches/001-calm-editorial/index.html")
browser_vision(question="Does this layout look clean and readable? Any visible bugs (overlapping text, unstyled elements, broken images)?")
```

`browser_vision` повертає AI‑опис того, що дійсно знаходиться на сторінці, плюс шлях до скріншоту — виявляє баги розмітки, які не помітні при чистому перегляді коду (наприклад, невдалий імпорт шрифту, згорнутий flex‑контейнер). Виправляй і переходимо, доки кожен варіант не виглядає правильно.

**Базовий CSS‑reset + системний стек шрифтів** для швидкого старту:

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

### 4. README для варіанту

`README.md` кожного варіанту має відповідати на:

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

### 5. Порівняння «голова‑до‑голови»

Після створення всіх варіантів представ їх у вигляді порівняння. Не просто перелічуй — **вислови свою оцінку**:

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

Дай користувачу можливість обрати переможця, з’єднати два варіанти в гібрид або попросити новий раунд.

## Темізація (коли проєкт має візуальну ідентичність)

Якщо у користувача є готова тема (кольори, шрифти, токени), розмісти спільні токени у `sketches/themes/tokens.css` і підключи їх в кожному варіанті через `@import`. Тримай токени мінімальними:

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

Не перебільшуй токенізацію тимчасового скетчу — зазвичай достатньо трьох кольорів і одного шрифту.

## Бар’єр інтерктивності

Скетч вважається достатньо інтерактивним, коли користувач може:

1. **Клікнути головну дію** і побачити помітну реакцію (зміна стану, модальне вікно, toast, навігаційний підказ)
2. **Спостерігати один значущий перехід стану** (фільтрація списку, перемикач режиму, відкриття/закриття панелі)
3. **Навести курсор на впізнавані affordances** (кнопки, рядки, вкладки)

Більше — надмірна інженерія для тимчасового скетчу. Менше — просто скріншот.

## Frontier‑mode (вибір наступного скетчу)

Якщо скетчі вже існують і користувач запитує «what should I sketch next?», пропонуй 2‑4 названі кандидати, орієнтуючись на:

- **Прогалини узгодженості** — два переможних варіанти з різних скетчів зробили незалежні рішення, які ще не об’єднані
- **Ненаписані екрани** — згадані, але ще не досліджені
- **Покриття станів** — щасливий шлях є, а ось пустий / loading / error / 1000‑items — ні
- **Прогалини адаптивності** — перевірено лише один viewport; чи працює на мобільному / ультраширокому?
- **Шаблони взаємодії** — статичні макети є, а переходи, drag, scroll‑поведінка — ні

Пропонуй варіанти, дай користувачу обрати.

## Вихідні дані

- Створи `sketches/` (або `.planning/sketches/`, якщо користувач дотримується конвенцій GSD) у корені репозиторію
- По одному підкаталогу на варіант: `NNN-stance-name/index.html` + `README.md`
- Поясни, як їх відкрити: `open sketches/001-calm-editorial/index.html` на macOS, `xdg-open` на Linux, `start` на Windows
- Тримай варіанти тимчасовими — скетч, який треба зберегти, слід перенести в реальний код проєкту, а не залишати як актив.

**Типова послідовність інструментів для одного варіанту:**

```
terminal("mkdir -p sketches/001-calm-editorial")
write_file("sketches/001-calm-editorial/index.html", "<!doctype html>...")
write_file("sketches/001-calm-editorial/README.md", "## Variant: Calm editorial\n...")
browser_navigate(url="file://$(pwd)/sketches/001-calm-editorial/index.html")
browser_vision(question="How does this look? Any obvious layout issues?")
```

Повтори для кожного варіанту, потім представ таблицю порівняння.

## Атрибуція

Адаптовано з workflow проєкту GSD (Get Shit Done) `/gsd-sketch` — MIT © 2025 Lex Christopherson ([gsd-build/get-shit-done](https://github.com/gsd-build/get-shit-done)). Повна система GSD постачає постійний стан скетчів, посилання на теми/патерни варіантів та процеси аудиту узгодженості; встановити можна через `npx get-shit-done-cc --hermes --global`.