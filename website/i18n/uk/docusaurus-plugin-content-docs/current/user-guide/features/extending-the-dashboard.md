---
sidebar_position: 17
title: "Розширення панелі інструментів"
description: "Створи теми та плагіни для Hermes веб‑дашборду — палети, типографіка, макети, власні вкладки, слоти оболонки, слоти, прив’язані до сторінки, і маршрути бекенд API."
---

# Розширення панелі приладів

Веб‑панель Hermes (`hermes dashboard`) створена так, щоб її можна було змінювати зовнішній вигляд і розширювати без форкування кодової бази. Відкрито три рівні:

1. **Теми** — YAML‑файли, які змінюють палітру, типографіку, макет та оформлення окремих компонентів панелі. Додай файл у `~/.hermes/dashboard-themes/`; він з’явиться у перемикачі тем.
2. **UI‑плагіни** — каталог з `manifest.json` + JavaScript‑пакетом, який реєструє вкладку, замінює вбудовану сторінку, доповнює її через слот, прив’язаний до сторінки, або вставляє компоненти у названі слоти оболонки.
3. **Backend‑плагіни** — Python‑файл у цьому каталозі плагіна, який експортує FastAPI `router`; маршрути монтуються під `/api/plugins/<name>/` і викликаються з UI плагіна.

Усі три **підключаються «на льоту»**: без клонування репозиторію, без `npm run build`, без патчів до коду панелі. Ця сторінка є канонічним посиланням для всіх трьох.

Якщо ти просто хочеш користуватися панеллю, дивись [Web Dashboard](./web-dashboard). Якщо хочеш змінити зовнішній вигляд термінального CLI (не веб‑панелі), дивись [Skins & Themes](./skins) — система скінів CLI не пов’язана з темами панелі.

:::note Як компоненти взаємодіють
Теми та плагіни незалежні, але синергічні. Тема може працювати самостійно (лише YAML‑файл). Плагін може працювати самостійно (лише вкладка). Разом вони дозволяють створити повний візуальний рескін з кастомними HUD‑ами — приклад `strike-freedom-cockpit` (розташований у супутньому репозиторії `hermes-example-plugins` — дивись [Combined theme + plugin demo](#combined-theme--plugin-demo) для кроків встановлення) робить саме це.
:::
## Зміст

- [Теми](#themes)
  - [Швидкий старт — твоя перша тема](#quick-start--your-first-theme)
  - [Палітра, типографіка, макет](#palette-typography-layout)
  - [Варіанти макету](#layout-variants)
  - [Активи теми (зображення як CSS‑змінні)](#theme-assets-images-as-css-vars)
  - [Перевизначення chrome компонентів](#component-chrome-overrides)
  - [Перевизначення кольорів](#color-overrides)
  - [Необроблений `customCSS`](#raw-customcss)
  - [Вбудовані теми](#built-in-themes)
  - [Повна довідка щодо YAML теми](#full-theme-yaml-reference)
- [Плагіни](#plugins)
  - [Швидкий старт — твій перший плагін](#quick-start--your-first-plugin)
  - [Структура каталогу](#directory-layout)
  - [Довідка з маніфесту](#manifest-reference)
  - [SDK плагіна](#the-plugin-sdk)
  - [Слоти оболонки](#shell-slots)
  - [Замінювання вбудованих сторінок (`tab.override`)](#replacing-built-in-pages-taboverride)
  - [Розширення вбудованих сторінок (слоти, прив’язані до сторінки)](#augmenting-built-in-pages-page-scoped-slots)
  - [Плагіни лише зі слотами (`tab.hidden`)](#slot-only-plugins-tabhidden)
  - [Маршрути бекенд‑API](#backend-api-routes)
  - [Кастомний CSS для плагіна](#custom-css-per-plugin)
  - [Виявлення та перезавантаження плагінів](#plugin-discovery--reload)
- [Демонстрація комбінованої теми + плагіна](#combined-theme--plugin-demo)
- [Довідник API](#api-reference)
- [Усунення проблем](#troubleshooting)
## Теми

Теми — це YAML‑файли, що зберігаються в `~/.hermes/dashboard-themes/`. Назва файлу не має значення (система використовує поле `name:` теми), проте зазвичай використовується `<name>.yaml`. Кожне поле є необов’язковим — відсутні ключі підставляються зі вбудованої теми `default`, тому тема може бути настільки маленькою, як один колір.
### Швидкий старт — твоя перша тема

```bash
mkdir -p ~/.hermes/dashboard-themes
```

```yaml
# ~/.hermes/dashboard-themes/neon.yaml
name: neon
label: Neon
description: Pure magenta on black

palette:
  background: "#000000"
  midground: "#ff00ff"
```

Онови дашборд. Клацни на іконку палітри у заголовку та вибери **Neon**. Тло стане чорним, текст і акценти — маґентовими, а всі похідні кольори (card, border, muted, ring тощо) будуть перераховані з цього двокольорового трійника за допомогою `color-mix()` у CSS.

Ось і весь процес ознайомлення: один файл, два кольори. Все, що нижче, — це необов’язкове уточнення.
### Palette, typography, layout

These three blocks are the heart of a theme. Each is independent — override one, leave the others.

#### Palette (3-layer)

The palette is a triplet of color layers plus a warm-glow vignette color and a noise-grain multiplier. The dashboard's design-system cascade derives every shadcn-compatible token (card, popover, muted, border, primary, destructive, ring, etc.) from this triplet via CSS `color-mix()`. Overriding three colors cascades into the whole UI.

| Key | Description |
|-----|-------------|
| `palette.background` | Найглибший колір полотна — зазвичай майже чорний. Керує фоном сторінки та заповненням карток. |
| `palette.midground` | Основний текст і акцент. Більшість UI‑елементів читають це (текст переднього плану, контури кнопок, кільця фокусу). |
| `palette.foreground` | Виділення верхнього шару. Тема за замовчуванням встановлює його білим з альфа 0 (невидимий); теми, які хочуть яскравий акцент зверху, можуть підвищити його альфа. |
| `palette.warmGlow` | `rgba(...)` рядок, що використовується як колір віньєтки у `<Backdrop />`. |
| `palette.noiseOpacity` | 0–1.2 множник на шар зернистості. Нижче = м’якіше, вище = грубіше. |

Each layer accepts either `{hex: "#RRGGBB", alpha: 0.0–1.0}` or a bare hex string (alpha defaults to 1.0).

```yaml
palette:
  background:
    hex: "#05091a"
    alpha: 1.0
  midground: "#d8f0ff"          # bare hex, alpha = 1.0
  foreground:
    hex: "#ffffff"
    alpha: 0                    # invisible top layer
  warmGlow: "rgba(255, 199, 55, 0.24)"
  noiseOpacity: 0.7
```

#### Typography

| Key | Type | Description |
|-----|------|-------------|
| `fontSans` | string | CSS font-family стек для основного тексту (застосовується до `html`, `body`). |
| `fontMono` | string | CSS font-family стек для блоків коду, `<code>`, утиліт `.font-mono`. |
| `fontDisplay` | string | Додатковий стек заголовків/дисплея. Повертається до `fontSans`. |
| `fontUrl` | string | Додаткова URL зовнішньої таблиці стилів. Вставляється як `<link rel="stylesheet">` у `<head>` при перемиканні теми. Така URL ніколи не вставляється двічі. Працює з Google Fonts, Bunny Fonts, самохостингом `@font-face`‑таблиць — будь‑що, що можна підключити посиланням. |
| `baseSize` | string | Кореневий розмір шрифту — контролює масштаб `rem`. Напр., `"14px"`, `"16px"`. |
| `lineHeight` | string | Типова міжрядкова відстань. Напр., `"1.5"`, `"1.65"`. |
| `letterSpacing` | string | Типовий інтервал між літерами. Напр., `"0"`, `"0.01em"`, `"-0.01em"`. |

```yaml
typography:
  fontSans: '"Orbitron", "Eurostile", "Impact", sans-serif'
  fontMono: '"Share Tech Mono", ui-monospace, monospace'
  fontDisplay: '"Orbitron", "Eurostile", sans-serif'
  fontUrl: "https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;600;700&family=Share+Tech+Mono&display=swap"
  baseSize: "14px"
  lineHeight: "1.5"
  letterSpacing: "0.04em"
```

#### Layout

| Key | Values | Description |
|-----|--------|-------------|
| `radius` | any CSS length (`"0"`, `"0.25rem"`, `"0.5rem"`, `"1rem"`, ...) | Токен радіуса кутів. Відображається у `--radius` і розповсюджується на `--radius-sm/md/lg/xl` — всі округлені елементи змінюються одночасно. |
| `density` | `compact` \| `comfortable` \| `spacious` | Множник простору, застосовуваний як CSS‑змінна `--spacing-mul`. `compact = 0.85×`, `comfortable = 1.0×` (за замовчуванням), `spacious = 1.2×`. Масштабує базовий простір Tailwind, тому відступи, `gap` та утиліти `space-between` змінюються пропорційно. |

```yaml
layout:
  radius: "0"
  density: compact
```
### Варіанти макету

`layoutVariant` вибирає загальний макет оболонки. За замовчуванням — `"standard"`, якщо не вказано.

| Варіант | Поведінка |
|---------|-----------|
| `standard` | Одна колонка, максимальна ширина 1600 px (за замовчуванням). |
| `cockpit` | Ліва бічна панель (260 px) + основний вміст. Заповнюється плагінами через слот `sidebar` — дивись [Shell slots](#shell-slots). Якщо плагін відсутній, панель показує заповнювач. |
| `tiled` | Прибирає обмеження максимальної ширини, тож сторінки можуть займати всю ширину вікна перегляду. |

```yaml
layoutVariant: cockpit
```

Поточний варіант доступний як `document.documentElement.dataset.layoutVariant`, тому чистий CSS у `customCSS` може звертатися до нього через `:root[data-layout-variant="cockpit"] …`.
### Тема: активи (зображення як CSS‑змінні)

Додавай URL‑адреси зображень до теми. Кожен іменований слот стає CSS‑змінною (`--theme-asset-<name>`), яку може читати вбудована оболонка та будь‑який плагін. Слот `bg` автоматично підключається до заднього плану; інші слоти призначені для плагінів.

```yaml
assets:
  bg: "https://example.com/hero-bg.jpg"           # auto-wired into <Backdrop />
  hero: "/my-images/strike-freedom.png"           # for plugin sidebars
  crest: "/my-images/crest.svg"                   # for header-left plugins
  logo: "/my-images/logo.png"
  sidebar: "/my-images/rail.png"
  header: "/my-images/header-art.png"
  custom:
    scanLines: "/my-images/scanlines.png"         # → --theme-asset-custom-scanLines
```

Значення приймаються:

- Чисті URL‑адреси — автоматично обгортаються в `url(...)`.
- Попередньо обгорнені вирази `url(...)`, `linear-gradient(...)`, `radial-gradient(...)` — використовуються без змін.
- `"none"` — явна відмова.

Кожен актив також виводиться як `--theme-asset-<name>-raw` (необгорнутий URL), на випадок, якщо плагіну потрібно передати його в `<img src>` замість `background-image`.

Плагіни читають їх за допомогою звичайного CSS або JS:

```javascript
// In a plugin slot
const hero = getComputedStyle(document.documentElement)
  .getPropertyValue("--theme-asset-hero").trim();
```
### Перевизначення chrome‑компонентів

`componentStyles` змінює стиль окремих компонентів оболонки без написання CSS‑селекторів. Записи кожного bucket стають CSS‑змінними (`--component-<bucket>-<kebab-property>`), які читаються спільними компонентами оболонки. Тож перевизначення `card:` застосовуються до кожного `<Card>`, `header:` — до панелі застосунку тощо.

```yaml
componentStyles:
  card:
    clipPath: "polygon(12px 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%, 0 12px)"
    background: "linear-gradient(180deg, rgba(10, 22, 52, 0.85), rgba(5, 9, 26, 0.92))"
    boxShadow: "inset 0 0 0 1px rgba(64, 200, 255, 0.28)"
  header:
    background: "linear-gradient(180deg, rgba(16, 32, 72, 0.95), rgba(5, 9, 26, 0.9))"
  tab:
    clipPath: "polygon(6px 0, 100% 0, calc(100% - 6px) 100%, 0 100%)"
  sidebar: {}
  backdrop: {}
  footer: {}
  progress: {}
  badge: {}
  page: {}
```

Підтримувані bucket: `card`, `header`, `footer`, `sidebar`, `tab`, `progress`, `badge`, `backdrop`, `page`.

Назви властивостей використовують camelCase (`clipPath`) і генеруються у kebab‑case (`clip-path`). Значення — прості CSS‑рядки, будь‑що, що приймає CSS (`clip-path`, `border-image`, `background`, `box-shadow`, `animation`, …).
### Перевизначення кольорів

Більшість тем не потребуватимуть цього — 3‑шаровий набір палітри генерує кожен токен shadcn. Використовуй `colorOverrides`, коли потрібен конкретний акцент, який не буде створений під час генерування (м’який руйнівний червоний для пастельної теми, конкретний успішний зелений для бренду).

```yaml
colorOverrides:
  primary: "#ffce3a"
  primaryForeground: "#05091a"
  accent: "#3fd3ff"
  ring: "#3fd3ff"
  destructive: "#ff3a5e"
  border: "rgba(64, 200, 255, 0.28)"
```

Підтримувані ключі: `card`, `cardForeground`, `popover`, `popoverForeground`, `primary`, `primaryForeground`, `secondary`, `secondaryForeground`, `muted`, `mutedForeground`, `accent`, `accentForeground`, `destructive`, `destructiveForeground`, `success`, `warning`, `border`, `input`, `ring`.

Кожен ключ відповідає 1:1 змінній CSS `--color-<kebab>` (наприклад, `primaryForeground` → `--color-primary-foreground`). Будь‑яке встановлене тут значення має пріоритет над каскадом палітри лише для активної теми — перехід до іншої теми скидає перевизначення.
### Raw `customCSS`

Для селекторів, які Chrome підтримує, а `componentStyles` не може виразити — псевдо‑елементи, анімації, медіа‑запити, перевизначення в межах теми — вставляй необроблений CSS у `customCSS`:

```yaml
customCSS: |
  /* Scanline overlay — only visible when cockpit variant is active. */
  :root[data-layout-variant="cockpit"] body::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    z-index: 100;
    background: repeating-linear-gradient(to bottom,
      transparent 0px, transparent 2px,
      rgba(64, 200, 255, 0.035) 3px, rgba(64, 200, 255, 0.035) 4px);
    mix-blend-mode: screen;
  }
```

CSS інжектується як єдиний scoped `<style data-hermes-theme-css>` тег під час застосування теми і очищується при переключенні теми. **Обмеження — 32 КіБ на тему.**
### Вбудовані теми

Кожна вбудована тема має свою палітру, типографію та розмітку — перемикання призводить до помітних змін, окрім лише кольору.

| Тема | Палітра | Типографія | Розмітка |
|------|---------|------------|----------|
| **Hermes Teal** (`default`) | Темно-бірюзовий + кремовий | System stack, 15px | 0.5rem radius, comfortable |
| **Hermes Teal (Large)** (`default-large`) | Така ж, як у `default` | System stack, 18px, line-height 1.65 | 0.5rem radius, spacious |
| **Midnight** (`midnight`) | Насичений синьо‑фіолетовий | Inter + JetBrains Mono, 14px | 0.75rem radius, comfortable |
| **Ember** (`ember`) | Теплий малиновий + бронзовий | Spectral (serif) + IBM Plex Mono, 15px | 0.25rem radius, comfortable |
| **Mono** (`mono`) | Відтінки сірого | IBM Plex Sans + IBM Plex Mono, 13px | 0 radius, compact |
| **Cyberpunk** (`cyberpunk`) | Неоновий зелений на чорному | Share Tech Mono всюди, 14px | 0 radius, compact |
| **Rosé** (`rose`) | Рожевий + слонова кістка | Fraunces (serif) + DM Mono, 16px | 1rem radius, spacious |

Теми, які посилаються на Google Fonts (усі, крім Hermes Teal), завантажують таблицю стилів за запитом — під час першого перемикання на них у `<head>` вставляється тег `<link>`.
### Повний довідник YAML теми

Кожен елемент управління в одному файлі — скопіюй і видали те, що не потрібно:

```yaml
# ~/.hermes/dashboard-themes/ocean.yaml
name: ocean
label: Ocean Deep
description: Deep sea blues with coral accents

# 3-layer palette (accepts {hex, alpha} or bare hex)
palette:
  background:
    hex: "#0a1628"
    alpha: 1.0
  midground:
    hex: "#a8d0ff"
    alpha: 1.0
  foreground:
    hex: "#ffffff"
    alpha: 0.0
  warmGlow: "rgba(255, 107, 107, 0.35)"
  noiseOpacity: 0.7

typography:
  fontSans: "Poppins, system-ui, sans-serif"
  fontMono: "Fira Code, ui-monospace, monospace"
  fontDisplay: "Poppins, system-ui, sans-serif"   # optional
  fontUrl: "https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&family=Fira+Code:wght@400;500&display=swap"
  baseSize: "15px"
  lineHeight: "1.6"
  letterSpacing: "-0.003em"

layout:
  radius: "0.75rem"
  density: comfortable

layoutVariant: standard        # standard | cockpit | tiled

assets:
  bg: "https://example.com/ocean-bg.jpg"
  hero: "/my-images/kraken.png"
  crest: "/my-images/anchor.svg"
  logo: "/my-images/logo.png"
  custom:
    pattern: "/my-images/waves.svg"

componentStyles:
  card:
    boxShadow: "inset 0 0 0 1px rgba(168, 208, 255, 0.18)"
  header:
    background: "linear-gradient(180deg, rgba(10, 22, 40, 0.95), rgba(5, 9, 26, 0.9))"

colorOverrides:
  destructive: "#ff6b6b"
  ring: "#ff6b6b"

customCSS: |
  /* Any additional selector-level tweaks */
```

Онови дашборд після створення файлу. Перемикай теми в режимі реального часу з заголовка — натисни іконку палітри. Вибір зберігається у `config.yaml` під `dashboard.theme` і відновлюється при перезавантаженні.

---
## Плагіни

Dashboard‑плагін — це каталог із `manifest.json`, готовим JS‑bundle та, за потреби, CSS‑файлом і Python‑файлом із маршрутами FastAPI. Плагіни розташовані поряд з іншими плагінами Hermes у `~/.hermes/plugins/<name>/` — розширення панелі інструментів є підкаталогом `dashboard/` всередині цього каталогу плагіна, тож один плагін може розширювати як CLI/gateway, так і панель інструментів з однієї інсталяції.

Плагіни не включають React або UI‑компоненти. Вони використовують **Plugin SDK**, доступний через `window.__HERMES_PLUGIN_SDK__`. Це робить пакети плагінів крихітними (зазвичай кілька КБ) і запобігає конфліктам версій.
### Швидкий старт — твій перший плагін

Створи структуру каталогів:

```bash
mkdir -p ~/.hermes/plugins/my-plugin/dashboard/dist
```

Напиши маніфест:

```json
// ~/.hermes/plugins/my-plugin/dashboard/manifest.json
{
  "name": "my-plugin",
  "label": "My Plugin",
  "icon": "Sparkles",
  "version": "1.0.0",
  "tab": {
    "path": "/my-plugin",
    "position": "after:skills"
  },
  "entry": "dist/index.js"
}
```

Напиши JS‑bundle (звичайний IIFE — без кроку збірки):

```javascript
// ~/.hermes/plugins/my-plugin/dashboard/dist/index.js
(function () {
  "use strict";

  const SDK = window.__HERMES_PLUGIN_SDK__;
  const { React } = SDK;
  const { Card, CardHeader, CardTitle, CardContent } = SDK.components;

  function MyPage() {
    return React.createElement(Card, null,
      React.createElement(CardHeader, null,
        React.createElement(CardTitle, null, "My Plugin"),
      ),
      React.createElement(CardContent, null,
        React.createElement("p", { className: "text-sm text-muted-foreground" },
          "Hello from my custom dashboard tab.",
        ),
      ),
    );
  }

  window.__HERMES_PLUGINS__.register("my-plugin", MyPage);
})();
```

Онови дашборд — твоя вкладка з’явиться в панелі навігації після **Skills**.

:::tip Пропустити React.createElement
Якщо ти віддаєш перевагу JSX, використай будь‑який збирач (esbuild, Vite, rollup) з React як external і IIFE‑output. Єдина жорстка вимога — фінальний файл має бути одним JS‑файлом, який можна завантажити через `<script>`. React ніколи не включається у bundle; він підключається з `SDK.React`.
:::
### Макет каталогу

```
~/.hermes/plugins/my-plugin/
├── plugin.yaml              # optional — existing CLI/gateway plugin manifest
├── __init__.py              # optional — existing CLI/gateway hooks
└── dashboard/               # dashboard extension
    ├── manifest.json        # required — tab config, icon, entry point
    ├── dist/
    │   ├── index.js         # required — pre-built JS bundle (IIFE)
    │   └── style.css        # optional — custom CSS
    └── plugin_api.py        # optional — backend API routes (FastAPI)
```

Один каталог плагіна може містити три ортогональні розширення:

- `plugin.yaml` + `__init__.py` — CLI/gateway плагін ([дивись сторінку плагінів](./plugins)).
- `dashboard/manifest.json` + `dashboard/dist/index.js` — плагін UI‑панелі.
- `dashboard/plugin_api.py` — маршрути бекенду панелі.

Жоден з них не є обов’язковим; включай лише ті рівні, які потрібні.
### Посилання на Manifest

```json
{
  "name": "my-plugin",
  "label": "My Plugin",
  "description": "What this plugin does",
  "icon": "Sparkles",
  "version": "1.0.0",
  "tab": {
    "path": "/my-plugin",
    "position": "after:skills",
    "override": "/",
    "hidden": false
  },
  "slots": ["sidebar", "header-left"],
  "entry": "dist/index.js",
  "css": "dist/style.css",
  "api": "plugin_api.py"
}
```

| Поле | Обов’язково | Опис |
|------|--------------|------|
| `name` | Yes | Унікальний ідентифікатор плагіна. Нижній регістр, допускаються дефіси. Використовується в URL та реєстрації. |
| `label` | Yes | Відображувана назва, що показується у вкладці навігації. |
| `description` | No | Короткий опис (показується в адмін‑інтерфейсі панелі). |
| `icon` | No | Назва іконки Lucide. За замовчуванням `Puzzle`. Невідомі назви переходять у `Puzzle`. |
| `version` | No | Рядок semver. За замовчуванням `0.0.0`. |
| `tab.path` | Yes | URL‑шлях для вкладки (наприклад, `/my-plugin`). |
| `tab.position` | No | Де вставити вкладку. `"end"` (за замовчуванням), `"after:<path>"` або `"before:<path>"` — значення після двокрапки є **сегментом шляху** цільової вкладки (без початкового слешу). Приклади: `"after:skills"`, `"before:config"`. |
| `tab.override` | No | Встановити вбудований шлях маршруту (`"/"`, `"/sessions"`, `"/config"` тощо), щоб **замінити** цю сторінку замість додавання нової вкладки. Дивись [Replacing built-in pages](#replacing-built-in-pages-taboverride). |
| `tab.hidden` | No | Якщо `true`, зареєструвати компонент і будь‑які слоти без додавання вкладки до навігації. Використовується плагінами лише зі слотами. Дивись [Slot-only plugins](#slot-only-plugins-tabhidden). |
| `slots` | No | Іменовані слоти оболонки, які заповнює цей плагін. **Лише допоміжна документація** — реальна реєстрація відбувається з JS‑пакету через `registerSlot()`. Перерахування слотів тут робить поверхні пошуку інформативнішими. |
| `entry` | Yes | Шлях до JS‑пакету відносно `dashboard/`. За замовчуванням `dist/index.js`. |
| `css` | No | Шлях до CSS‑файлу, який буде ін’єктовано як тег `<link>`. |
| `api` | No | Шлях до Python‑файлу з FastAPI‑маршрутами. Монтується за `/api/plugins/<name>/`. |

#### Доступні іконки

Плагіни використовують назви іконок Lucide. Панель відображає їх за назвою — невідомі назви без повідомлень переходять у `Puzzle`.

Наразі відображені: `Activity`, `BarChart3`, `Clock`, `Code`, `Database`, `Eye`, `FileText`, `Globe`, `Heart`, `KeyRound`, `MessageSquare`, `Package`, `Puzzle`, `Settings`, `Shield`, `Sparkles`, `Star`, `Terminal`, `Wrench`, `Zap`.

Потрібна інша іконка? Відкрий PR до `web/src/App.tsx` у `ICON_MAP` — чисто додаткова зміна.
### SDK плагіна

Все, що потрібно плагіну, знаходиться в `window.__HERMES_PLUGIN_SDK__`. Плагіни ніколи не повинні імпортувати React безпосередньо.

```javascript
const SDK = window.__HERMES_PLUGIN_SDK__;

// React + hooks
SDK.React                    // the React instance
SDK.hooks.useState
SDK.hooks.useEffect
SDK.hooks.useCallback
SDK.hooks.useMemo
SDK.hooks.useRef
SDK.hooks.useContext
SDK.hooks.createContext

// UI components (shadcn/ui primitives)
SDK.components.Card
SDK.components.CardHeader
SDK.components.CardTitle
SDK.components.CardContent
SDK.components.Badge
SDK.components.Button
SDK.components.Input
SDK.components.Label
SDK.components.Select
SDK.components.SelectOption
SDK.components.Separator
SDK.components.Tabs
SDK.components.TabsList
SDK.components.TabsTrigger
SDK.components.PluginSlot    // render a named slot (useful for nested plugin UIs)

// Hermes API client + raw fetcher
SDK.api                      // typed client — getStatus, getSessions, getConfig, ...
SDK.fetchJSON                // raw fetch for custom endpoints (plugin-registered routes)

// Utilities
SDK.utils.cn                 // Tailwind class merger (clsx + twMerge)
SDK.utils.timeAgo            // "5m ago" from unix timestamp
SDK.utils.isoTimeAgo         // "5m ago" from ISO string

// Hooks
SDK.useI18n                  // i18n hook for multi-language plugins
```

#### Виклик бекенду вашого плагіна

```javascript
SDK.fetchJSON("/api/plugins/my-plugin/data")
  .then((data) => console.log(data))
  .catch((err) => console.error("API call failed:", err));
```

`fetchJSON` вставляє токен автентифікації сесії, перетворює помилки у викинуті виключення і автоматично розбирає JSON.

#### Виклик вбудованих кінцевих точок Hermes

```javascript
// Agent status
SDK.api.getStatus().then((s) => console.log("Version:", s.version));

// Recent sessions
SDK.api.getSessions(10).then((resp) => console.log(resp.sessions.length));
```

Дивись [Web Dashboard → REST API](./web-dashboard#rest-api) для повного списку.
### Shell slots

Слоти дозволяють плагіну вставляти компоненти у іменовані місця оболонки застосунку — бічну панель кокпіту, заголовок, підвал, шар‑оверлей — без створення окремої вкладки. Кілька плагінів можуть заповнювати один і той же слот; вони відображаються у стеку у порядку реєстрації.

Реєструй зі всередині пакету плагіну:

```javascript
window.__HERMES_PLUGINS__.registerSlot("my-plugin", "sidebar", MySidebar);
window.__HERMES_PLUGINS__.registerSlot("my-plugin", "header-left", MyCrest);
```

#### Каталог слотів

**Слоти, доступні по всій оболонці** (можуть рендеритися у будь‑якому місці інтерфейсу застосунку):

| Slot | Location |
|------|----------|
| `backdrop` | Усередині стеку шару `<Backdrop />`, над шаром шуму. |
| `header-left` | Перед брендом Hermes у верхній панелі. |
| `header-right` | Перед перемикачами теми/мови у верхній панелі. |
| `header-banner` | Смуга повної ширини під навігацією. |
| `sidebar` | Бічна панель кокпіту — **рендериться лише коли `layoutVariant === "cockpit"`**. |
| `pre-main` | Над виходом маршруту (всередині `<main>`). |
| `post-main` | Під виходом маршруту (всередині `<main>`). |
| `footer-left` | Вміст клітини підвалу (замінює стандартний). |
| `footer-right` | Вміст клітини підвалу (замінює стандартний). |
| `overlay` | Шар фіксованої позиції над усім іншим. Корисний для chrome (скан‑лінії, віньєтки), які `customCSS` не може створити самостійно. |

**Слоти, прив’язані до сторінки** (рендеряться лише на вказаній вбудованій сторінці — використовуйте їх, щоб вставляти віджети, картки або панелі інструментів у існуючу сторінку без заміни всього маршруту):

| Slot | Where it renders |
|------|------------------|
| `sessions:top` / `sessions:bottom` | Верх / низ сторінки `/sessions`. |
| `analytics:top` / `analytics:bottom` | Верх / низ сторінки `/analytics`. |
| `logs:top` / `logs:bottom` | Верх (над панеллю фільтрів) / низ (під переглядачем журналу) сторінки `/logs`. |
| `cron:top` / `cron:bottom` | Верх / низ сторінки `/cron`. |
| `skills:top` / `skills:bottom` | Верх / низ сторінки `/skills`. |
| `config:top` / `config:bottom` | Верх / низ сторінки `/config`. |
| `env:top` / `env:bottom` | Верх / низ сторінки `/env` (Keys). |
| `docs:top` / `docs:bottom` | Верх (над `<iframe>`) / низ сторінки `/docs`. |
| `chat:top` / `chat:bottom` | Верх / низ сторінки `/chat` (активний лише коли вбудований чат увімкнено). |

Приклад — додати картку‑банер у верхню частину сторінки Sessions:

```javascript
function PinnedSessionsBanner() {
  return React.createElement(Card, null,
    React.createElement(CardContent, { className: "py-2 text-xs" },
      "Pinned note injected by my-plugin"),
  );
}

window.__HERMES_PLUGINS__.registerSlot("my-plugin", "sessions:top", PinnedSessionsBanner);
```

Поєднуй слоти, прив’язані до сторінки, з `tab.hidden: true`, якщо твій плагін лише розширює існуючі сторінки і не потребує власної вкладки в бічній панелі.

Оболонка рендерить лише `<PluginSlot name="..." />` для наведених вище слотів. Додаткові імена приймаються реєстром для вкладених UI плагінів — плагін може експортувати власні слоти через `SDK.components.PluginSlot`.

#### Перереєстрація та HMR

Якщо одна й та сама пара `(plugin, slot)` зареєстрована двічі, пізніший виклик замінює попередній — це відповідає тому, як React HMR очікує поведінку повторних монтувань плагіну.
### Замінювання вбудованих сторінок (`tab.override`)

Встановлення `tab.override` у шлях вбудованого маршруту змушує компонент плагіна **замінити** цю сторінку замість додавання нової вкладки. Корисно, коли тема хоче власну головну сторінку (`/`), але хоче залишити решту панелі інструментів незмінною.

```json
{
  "name": "my-home",
  "label": "Home",
  "tab": {
    "path": "/my-home",
    "override": "/",
    "position": "end"
  },
  "entry": "dist/index.js"
}
```

При встановленому `override`:

- Оригінальний компонент сторінки за адресою `/` видаляється з роутера.
- Твій плагін відображається за адресою `/` замість нього.
- Для `tab.path` не додається вкладка навігації (перевизначення є точкою входу).

Лише один плагін може перевизначати даний шлях. Якщо два плагіни претендують на одне й те ж перевизначення, перший отримує перевагу, а другий ігнорується з попередженням у режимі розробки.

Якщо потрібно лише додати картку або панель інструментів до існуючої сторінки, не беручи її під контроль, використай [page-scoped slots](#augmenting-built-in-pages-page-scoped-slots) замість цього.
### Розширення вбудованих сторінок (slot‑и, прив’язані до сторінки)

Повна заміна за допомогою `tab.override` важка — твій плагін тепер володіє усією сторінкою, включаючи будь‑які майбутні оновлення, які ми випустимо. У більшості випадків ти просто хочеш додати банер, картку або панель інструментів до існуючої сторінки. Для цього і існують **slot‑и, прив’язані до сторінки**.

Кожна вбудована сторінка надає slot‑и `<page>:top` і `<page>:bottom`, які рендеряться у верхній та нижній частині її області вмісту. Твій плагін заповнює один із них, викликаючи `registerSlot()` — вбудована сторінка продовжує працювати звичайно, а твій компонент рендериться поруч.

Доступні slot‑и: `sessions:*`, `analytics:*`, `logs:*`, `cron:*`, `skills:*`, `config:*`, `env:*`, `docs:*`, `chat:*` (кожен з `:top` і `:bottom`). Дивись повний каталог у [Shell slots → Slot catalogue](#slot-catalogue).

Мінімальний приклад — прикріпити банер у верхній частині сторінки **Sessions**:

```json
// ~/.hermes/plugins/session-notes/dashboard/manifest.json
{
  "name": "session-notes",
  "label": "Session Notes",
  "tab": { "path": "/session-notes", "hidden": true },
  "slots": ["sessions:top"],
  "entry": "dist/index.js"
}
```

```javascript
// ~/.hermes/plugins/session-notes/dashboard/dist/index.js
(function () {
  const SDK = window.__HERMES_PLUGIN_SDK__;
  const { React } = SDK;
  const { Card, CardContent } = SDK.components;

  function Banner() {
    return React.createElement(Card, null,
      React.createElement(CardContent, { className: "py-2 text-xs" },
        "Remember to label important sessions before archiving."),
    );
  }

  // Placeholder for the hidden tab.
  window.__HERMES_PLUGINS__.register("session-notes", function () { return null; });

  // The real work.
  window.__HERMES_PLUGINS__.registerSlot("session-notes", "sessions:top", Banner);
})();
```

**Ключові моменти**

- `tab.hidden: true` тримає плагін поза боковою панеллю — у нього немає окремої сторінки.
- Поле маніфесту `slots` лише для документації. Реальне прив’язування відбувається у JS‑bundle через `registerSlot()`.
- Кілька плагінів можуть претендувати на один і той же slot, прив’язаний до сторінки. Вони рендеряться у стеку у порядку реєстрації.
- Нульовий слід, коли жоден плагін не реєструє slot: вбудована сторінка рендериться точно так само, як і раніше.

Приклад плагіна‑посилання (`example-dashboard` у [`hermes-example-plugins`](https://github.com/NousResearch/hermes-example-plugins/tree/main/example-dashboard)) постачається з живою демонстрацією, яка вставляє банер у `sessions:top` — встанови його, щоб побачити шаблон у дії.
### Плагіни лише для слотів (`tab.hidden`)

Коли `tab.hidden: true`, плагін реєструє свій компонент (для прямих переходів за URL) і будь‑які слоти, але ніколи не додає вкладку до навігації. Використовується плагінами, які існують лише для впровадження в слоти — герб заголовка, HUD бічної панелі, накладка.

```json
{
  "name": "header-crest",
  "label": "Header Crest",
  "tab": {
    "path": "/header-crest",
    "position": "end",
    "hidden": true
  },
  "slots": ["header-left"],
  "entry": "dist/index.js"
}
```

Пакет все одно викликає `register()` із заповнювальним компонентом (рекомендована практика на випадок, якщо хтось перейде за URL безпосередньо), а потім `registerSlot()` для виконання реальної роботи.
### Маршрути Backend API

Плагіни можуть реєструвати маршрути FastAPI, встановлюючи `api` у маніфесті. Створи файл і експортуй `router`:

```python
# ~/.hermes/plugins/my-plugin/dashboard/plugin_api.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/data")
async def get_data():
    return {"items": ["one", "two", "three"]}

@router.post("/action")
async def do_action(body: dict):
    return {"ok": True, "received": body}
```

Маршрути монтуються під `/api/plugins/<name>/`, тому наведене вище стає:

- `GET  /api/plugins/my-plugin/data`
- `POST /api/plugins/my-plugin/action`

Маршрути API плагіна обходять автентифікацію за допомогою `session-token`, оскільки сервер dashboard за замовчуванням прив’язується до `localhost`. **Не публікуй dashboard на публічному інтерфейсі за допомогою `--host 0.0.0.0`, якщо запускаєш ненадійні плагіни** — їхні маршрути також стануть доступними.

#### Доступ до внутрішніх компонентів Hermes

Маршрути бекенду виконуються всередині процесу dashboard, тому вони можуть імпортувати безпосередньо з кодової бази hermes-agent:

```python
from fastapi import APIRouter
from hermes_state import SessionDB
from hermes_cli.config import load_config

router = APIRouter()

@router.get("/session-count")
async def session_count():
    db = SessionDB()
    try:
        count = len(db.list_sessions(limit=9999))
        return {"count": count}
    finally:
        db.close()

@router.get("/config-snapshot")
async def config_snapshot():
    cfg = load_config()
    return {"model": cfg.get("model", {})}
```
### Користувацький CSS для плагіна

Якщо твоєму плагіну потрібні стилі, які виходять за межі класів Tailwind та інлайн‑`style=`, додай CSS‑файл і вкажи його у маніфесті:

```json
{
  "css": "dist/style.css"
}
```

Файл ін’єкціюється як тег `<link>` під час завантаження плагіна. Використовуй унікальні назви класів, щоб уникнути конфліктів зі стилями дашборду, і посилайся на CSS‑змінні дашборду, щоб залишатися сумісним із темою:

```css
/* dist/style.css */
.my-plugin-chart {
  border: 1px solid var(--color-border);
  background: var(--color-card);
  color: var(--color-card-foreground);
  padding: 1rem;
}
.my-plugin-chart:hover {
  border-color: var(--color-ring);
}
```

Дашборд експонує кожен токен shadcn як `--color-*` плюс додаткові змінні теми (`--theme-asset-*`, `--component-<bucket>-*`, `--radius`, `--spacing-mul`). Посилайся на них, і твій плагін автоматично підлаштується під активну тему.
### Виявлення та перезавантаження плагінів

Панель керування сканує три каталоги у пошуках `dashboard/manifest.json`:

| Пріоритет | Каталог | Мітка джерела |
|----------|-----------|--------------|
| 1 (перемагає у конфлікті) | `~/.hermes/plugins/<name>/dashboard/` | `user` |
| 2 | `<repo>/plugins/memory/<name>/dashboard/` | `bundled` |
| 2 | `<repo>/plugins/<name>/dashboard/` | `bundled` |
| 3 | `./.hermes/plugins/<name>/dashboard/` | `project` — лише коли встановлено `HERMES_ENABLE_PROJECT_PLUGINS` |

Результати виявлення кешуються для кожного процесу панелі. Після додавання нового плагіну, або:

```bash
# Force a rescan without restart
curl http://127.0.0.1:9119/api/dashboard/plugins/rescan
```

…або перезапусти `hermes dashboard`.

#### Життєвий цикл завантаження плагіну

1. Панель завантажується. `main.tsx` експонує SDK у `window.__HERMES_PLUGIN_SDK__` та реєстр у `window.__HERMES_PLUGINS__`.
2. `App.tsx` викликає `usePlugins()` → отримує `GET /api/dashboard/plugins`.
3. Для кожного маніфесту: вставляється CSS‑тег `<link>` (якщо вказано), потім тег `<script>` завантажує JS‑пакет.
4. IIFE плагіну виконується і викликає `window.__HERMES_PLUGINS__.register(name, Component)` — і, за потреби, `.registerSlot(name, slot, Component)` для кожного слоту.
5. Панель вирішує зареєстрований компонент згідно маніфесту, додає вкладку до навігації (якщо не `hidden`) і монтує компонент як маршрут.

Плагіни мають до **2 секунд** після завантаження їх скрипту, щоб викликати `register()`. Після цього панель припиняє очікування і завершує початковий рендер. Якщо плагін пізніше зареєструється, він все одно з’явиться — навігація реактивна.

Якщо не вдається завантажити скрипт плагіну (404, синтаксична помилка, виключення під час IIFE), панель виводить попередження в консоль браузера і продовжує роботу без нього.
## Демонстрація комбінованої теми + плагіна

Плагін [`strike-freedom-cockpit`](https://github.com/NousResearch/hermes-example-plugins/tree/main/strike-freedom-cockpit) (репозиторій‑компаньйон `hermes-example-plugins`) — це повна демонстрація редизайну. Він поєднує YAML‑тему з only‑slot плагіном, щоб створити HUD у стилі кокпіту без форкування дашборду.

**Що він демонструє:**

- Повну тему з палітрою, типографікою, `fontUrl`, `layoutVariant: cockpit`, `assets`, `componentStyles` (загострені кути карток, градієнтні фони), `colorOverrides` та `customCSS` (накладка скан‑лінії).
- Only‑slot плагін (`tab.hidden: true`), який реєструється в трьох слотах:
  - `sidebar` — панель MS‑STATUS з живими телеметричними смугами, що отримуються через `SDK.api.getStatus()`.
  - `header-left` — герб фракції, який читає `--theme-asset-crest` з активної теми.
  - `footer-right` — власний слоган, що замінює стандартний рядок організації.
- Плагін читає артефакти теми через CSS‑змінні, тому зміна теми змінює героя/герб без змін у коді плагіна.

**Встановлення:**

```bash
git clone https://github.com/NousResearch/hermes-example-plugins.git

# Theme
cp hermes-example-plugins/strike-freedom-cockpit/theme/strike-freedom.yaml \
   ~/.hermes/dashboard-themes/

# Plugin
cp -r hermes-example-plugins/strike-freedom-cockpit ~/.hermes/plugins/
```

Відкрий дашборд, вибери **Strike Freedom** у перемикачі тем. Появиться бокова панель кокпіту, герб відобразиться у заголовку, слоган замінить нижній колонтитул. Повернись до **Hermes Teal**, і плагін залишиться встановленим, але невидимим (слот `sidebar` рендериться лише при `layoutVariant: cockpit`).

Прочитай вихідний код плагіна (`strike-freedom-cockpit/dashboard/dist/index.js` у репозиторії‑компаньйоні), щоб побачити, як він читає CSS‑змінні, захищає від старих дашбордів без підтримки слотів і реєструє три слоти з одного пакету.
## API reference

### Theme endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/themes` | GET | Список доступних тем та назва активної. Вбудовані теми повертають `{name, label, description}`; теми користувача також містять поле `definition` з повним нормалізованим об’єктом теми. |
| `/api/dashboard/theme` | PUT | Встановити активну тему. Тіло запиту: `{"name": "midnight"}`. Зберігається у `config.yaml` під `dashboard.theme`. |

### Plugin endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/plugins` | GET | Список виявлених плагінів (з маніфестами, без внутрішніх полів). |
| `/api/dashboard/plugins/rescan` | GET | Примусово повторно сканувати каталоги плагінів без перезапуску. |
| `/dashboard-plugins/<name>/<path>` | GET | Обслуговування статичних ресурсів з каталогу `dashboard/` плагіна. Трасування шляхів блокується. |
| `/api/plugins/<name>/*` | * | Маршрути бекенду, зареєстровані плагіном. |

### SDK on `window`

| Global | Type | Provider |
|--------|------|----------|
| `window.__HERMES_PLUGIN_SDK__` | object | `registry.ts` — React, hooks, UI components, API client, utils. |
| `window.__HERMES_PLUGINS__.register(name, Component)` | function | Реєструє головний компонент плагіна. |
| `window.__HERMES_PLUGINS__.registerSlot(name, slot, Component)` | function | Реєструє у іменованому слоті оболонки. |
## Усунення проблем

**Моя тема не з’являється у вибірнику.**
Перевір, чи файл знаходиться в `~/.hermes/dashboard-themes/` і має розширення `.yaml` або `.yml`. Онови сторінку. Запусти `curl http://127.0.0.1:9119/api/dashboard/themes` — твоя тема має бути у відповіді. Якщо у YAML є помилка парсингу, дашборд записує її в `errors.log` у `~/.hermes/logs/`.

**Вкладка мого плагіну не показується.**
1. Переконайся, що маніфест розташований за шляхом `~/.hermes/plugins/<name>/dashboard/manifest.json` (зверни увагу на підкаталог `dashboard/`).
2. `curl http://127.0.0.1:9119/api/dashboard/plugins/rescan` — примусово повторити виявлення.
3. Відкрий інструменти розробника браузера → Network — переконайся, що `manifest.json`, `index.js` та будь‑які CSS завантажуються без 404.
4. Відкрий інструменти розробника браузера → Console — шукай помилки під час виконання IIFE або `window.__HERMES_PLUGINS__ is undefined` (означає, що SDK не ініціалізувався, зазвичай через збій рендерингу React раніше).
5. Перевір, чи твій пакет викликає `window.__HERMES_PLUGINS__.register(...)` з **тім же ім’ям**, що вказане в `manifest.json:name`.

**Компоненти, зареєстровані у слоті, не відображаються.**
Слот `sidebar` рендериться лише коли активна тема має `layoutVariant: cockpit`. Інші слоти завжди рендеряться. Якщо ти реєструєшся у слот, у якому немає жодних хітів, додай `console.log` всередині `registerSlot`, щоб підтвердити, що пакет плагіну взагалі виконався.

**Маршрути бекенду плагіну повертають 404.**
1. Переконайся, що в маніфесті вказано `"api": "plugin_api.py"` і файл дійсно існує у `dashboard/`.
2. Перезапусти `hermes dashboard` — маршрути API плагіну монтуються один раз під час старту, **не** під час сканування.
3. Перевір, чи `plugin_api.py` експортує змінну рівня модуля `router = APIRouter()`. Інші імена експорту не підхоплюються.
4. Переглянь `~/.hermes/logs/errors.log` на наявність `Failed to load plugin <name> API routes` — там логуються помилки імпорту.

**Зміна теми скидає мої перевизначення кольорів.**
`colorOverrides` прив’язані до активної теми і очищуються при переключенні теми — це задумано. Якщо потрібні постійні перевизначення, розмісти їх у YAML твоєї теми, а не у живому перемикачі.

**customCSS теми обрізується.**
Блок `customCSS` обмежений 32 КіБ на тему. Розділи великі таблиці стилів на кілька тем або використай плагін, який інжектить повний файл стилів через поле `css` (без обмеження розміру).

**Хочу розповсюдити плагін у PyPI.**
Плагіни дашборду встановлюються за структурою каталогів, а не через точку входу pip. Найпростіший шлях розповсюдження сьогодні — git‑репозиторій, який користувач клонуватиме у `~/.hermes/plugins/`. Пакетний інсталятор pip для плагінів дашборду наразі не реалізований.