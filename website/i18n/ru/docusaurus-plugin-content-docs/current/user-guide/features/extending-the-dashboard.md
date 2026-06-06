---
sidebar_position: 17
title: "Расширение панели управления"
description: "Создай темы и плагины для веб‑дашборда Hermes — палитры, типографика, макеты, пользовательские вкладки, слоты оболочки, слоты scoped‑страницы и маршруты backend API."
---

# Расширение панели управления

Веб‑панель Hermes (`hermes dashboard`) построена так, чтобы её можно было переоформлять и расширять без форка кодовой базы. Предоставляются три уровня:

1. **Темы** — YAML‑файлы, которые перекрашивают палитру, типографику, макет и стили отдельных компонентов панели. Помести файл в `~/.hermes/dashboard-themes/`; он появится в переключателе тем.
2. **UI‑плагины** — каталог с `manifest.json` + JavaScript‑бандлом, который регистрирует вкладку, заменяет встроенную страницу, дополняет её через слоты, ограниченные страницей, или внедряет компоненты в именованные слоты оболочки.
3. **Backend‑плагины** — Python‑файл внутри каталога плагина, который экспортирует FastAPI `router`; маршруты монтируются под `/api/plugins/<name>/` и вызываются из UI плагина.

Все три **подключаются «на лету»**: без клонирования репозитория, без `npm run build`, без патчей исходного кода панели. Эта страница является каноническим справочником для всех трёх вариантов.

Если ты просто хочешь использовать панель, смотри [Web Dashboard](./web-dashboard). Если хочешь переоформить терминальный CLI (а не веб‑панель), смотри [Skins & Themes](./skins) — система скинов CLI не связана с темами панели.

:::note Как компоненты сочетаются
Темы и плагины независимы, но работают синергично. Тема может существовать сама по себе (только YAML‑файл). Плагин может существовать сам по себе (только вкладка). Вместе они позволяют собрать полное визуальное переоформление с пользовательскими HUD‑ами — пример `strike-freedom-cockpit` (находится в сопутствующем репозитории `hermes-example-plugins` — смотри [Combined theme + plugin demo](#combined-theme--plugin-demo) для шагов установки) делает именно это.
:::
## Содержание

- [Темы](#themes)
  - [Быстрый старт — твоя первая тема](#quick-start--your-first-theme)
  - [Палитра, типография, макет](#palette-typography-layout)
  - [Варианты макета](#layout-variants)
  - [Активы темы (изображения как CSS‑переменные)](#theme-assets-images-as-css-vars)
  - [Переопределения оформления компонентов](#component-chrome-overrides)
  - [Переопределения цветов](#color-overrides)
  - [Необработанный `customCSS`](#raw-customcss)
  - [Встроенные темы](#built-in-themes)
  - [Полный справочник YAML темы](#full-theme-yaml-reference)
- [Плагины](#plugins)
  - [Быстрый старт — твой первый плагин](#quick-start--your-first-plugin)
  - [Структура каталогов](#directory-layout)
  - [Справочник манифеста](#manifest-reference)
  - [SDK плагина](#the-plugin-sdk)
  - [Слоты оболочки](#shell-slots)
  - [Замена встроенных страниц (`tab.override`)](#replacing-built-in-pages-taboverride)
  - [Дополнение встроенных страниц (слоты, привязанные к странице)](#augmenting-built-in-pages-page-scoped-slots)
  - [Плагины только со слотом (`tab.hidden`)](#slot-only-plugins-tabhidden)
  - [Маршруты API бекенда](#backend-api-routes)
  - [Пользовательский CSS для плагина](#custom-css-per-plugin)
  - [Обнаружение и перезагрузка плагинов](#plugin-discovery--reload)
- [Демонстрация комбинированной темы + плагина](#combined-theme--plugin-demo)
- [Справочник API](#api-reference)
- [Устранение неполадок](#troubleshooting)
## Темы

Темы — это YAML‑файлы, хранящиеся в `~/.hermes/dashboard-themes/`. Имя файла не имеет значения (поле темы `name:` — то, что использует система), но принято использовать `<name>.yaml`. Все поля опциональны — отсутствующие ключи падают к встроенной теме `default`, поэтому тема может быть настолько маленькой, как один цвет.

### Быстрый старт — твоя первая тема

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

Обнови панель. Нажми на иконку палитры в заголовке и выбери **Neon**. Фон станет чёрным, текст и акценты — пурпурными, а каждый производный цвет (card, border, muted, ring и т.д.) будет пересчитан из этой 2‑цветной тройки с помощью `color-mix()` в CSS.

Это весь вводный процесс: один файл, два цвета. Всё остальное — необязательная доработка.

### Палитра, типография, макет

Эти три блока — сердце темы. Каждый независим — переопредели один, остальные оставь.

#### Палитра (3‑слой)

Палитра — это тройка цветовых слоёв плюс цвет виньетты `warmGlow` и множитель шума. Система каскадов design‑system дашборда выводит каждый совместимый с shadcn токен (card, popover, muted, border, primary, destructive, ring и т.д.) из этой тройки через CSS `color-mix()`. Переопределение трёх цветов распространяется на весь UI.

| Ключ | Описание |
|-----|----------|
| `palette.background` | Самый глубокий цвет канвы — обычно почти чёрный. Управляет фоном страницы и заливкой карточек. |
| `palette.midground` | Основной текст и акцент. Большая часть UI‑хрома читает его (текст переднего плана, контуры кнопок, кольца фокуса). |
| `palette.foreground` | Слой‑выделение. Тема по умолчанию задаёт его как белый с альфа 0 (невидим); темы, желающие яркий акцент сверху, могут увеличить альфа. |
| `palette.warmGlow` | Строка `rgba(...)`, используемая как цвет виньетты в `<Backdrop />`. |
| `palette.noiseOpacity` | Множитель 0–1.2 для наложения зерна. Ниже = мягче, выше = «зернистее». |

Каждый слой принимает либо `{hex: "#RRGGBB", alpha: 0.0–1.0}`, либо «голый» hex‑строку (альфа по умолчанию = 1.0).

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

#### Типография

| Ключ | Тип | Описание |
|-----|-----|----------|
| `fontSans` | string | CSS‑стек `font-family` для основного текста (применяется к `html`, `body`). |
| `fontMono` | string | CSS‑стек `font-family` для блоков кода, `<code>`, утилит `.font-mono`. |
| `fontDisplay` | string | Необязательный стек заголовков/дисплея. При отсутствии падает к `fontSans`. |
| `fontUrl` | string | Необязательный URL внешней таблицы стилей. Вставляется как `<link rel="stylesheet">` в `<head>` при переключении темы. Один и тот же URL никогда не вставляется дважды. Работает с Google Fonts, Bunny Fonts, самохостингом `@font-face` — любым доступным по ссылке. |
| `baseSize` | string | Размер базового шрифта — управляет масштабом `rem`. Например, `"14px"`, `"16px"`. |
| `lineHeight` | string | Стандартный `line-height`. Например, `"1.5"`, `"1.65"`. |
| `letterSpacing` | string | Стандартный `letter-spacing`. Например, `"0"`, `"0.01em"`, `"-0.01em"`. |

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

#### Макет

| Ключ | Значения | Описание |
|-----|----------|----------|
| `radius` | любой CSS‑длина (`"0"`, `"0.25rem"`, `"0.5rem"`, `"1rem"` …) | Токен радиуса углов. Привязывается к `--radius` и распространяется в `--radius-sm/md/lg/xl` — все скруглённые элементы меняются вместе. |
| `density` | `compact` \| `comfortable` \| `spacious` | Множитель отступов, задаваемый как CSS‑переменная `--spacing-mul`. `compact = 0.85×`, `comfortable = 1.0×` (по умолчанию), `spacious = 1.2×`. Масштабирует базовые отступы Tailwind, поэтому padding, gap и utilities `space-between` смещаются пропорционально. |

```yaml
layout:
  radius: "0"
  density: compact
```

### Варианты макета

`layoutVariant` выбирает общий макет оболочки. По умолчанию — `"standard"`, если параметр отсутствует.

| Вариант | Поведение |
|--------|-----------|
| `standard` | Одна колонка, максимальная ширина 1600 px (по умолчанию). |
| `cockpit` | Левая боковая панель‑рейл (260 px) + основной контент. Заполняется плагинами через слот `sidebar` — см. [Shell slots](#shell-slots). Без плагина рейл показывает заглушку. |
| `tiled` | Убирает ограничение максимальной ширины, позволяя страницам использовать всю ширину окна. |

```yaml
layoutVariant: cockpit
```

Текущий вариант доступен как `document.documentElement.dataset.layoutVariant`, поэтому сырой CSS в `customCSS` может адресовать его через `:root[data-layout-variant="cockpit"] …`.

### Активы темы (изображения как CSS‑переменные)

Пакуй URL‑адреса изображений вместе с темой. Каждый именованный слот становится CSS‑переменной (`--theme-asset-<name>`), которую может читать встроенная оболочка и любые плагины. Слот `bg` автоматически подключается к бекдропу; остальные слоты предназначены для плагинов.

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

Значения принимают:

- «Голые» URL — автоматически оборачиваются в `url(...)`.
- Уже обёрнутые `url(...)`, `linear-gradient(...)`, `radial-gradient(...)` — используются как есть.
- `"none"` — явный отказ.

Каждый актив также экспортируется как `--theme-asset-<name>-raw` (необёрнутый URL) на случай, если плагину нужно передать его в `<img src>` вместо `background-image`.

Плагины читают их обычным CSS или JS:

```javascript
// In a plugin slot
const hero = getComputedStyle(document.documentElement)
  .getPropertyValue("--theme-asset-hero").trim();
```

### Переопределения стилей компонентов

`componentStyles` переоформляет отдельные компоненты оболочки без написания CSS‑селекторов. Записи каждой «корзины» становятся CSS‑переменными (`--component-<bucket>-<kebab-property>`), которые читают общие компоненты оболочки. Поэтому переопределения `card:` применяются ко всем `<Card>`, `header:` — к панели заголовка и т.д.

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

Поддерживаемые корзины: `card`, `header`, `footer`, `sidebar`, `tab`, `progress`, `badge`, `backdrop`, `page`.

Имена свойств записываются в camelCase (`clipPath`) и выводятся в kebab‑case (`clip-path`). Значения — обычные CSS‑строки, любые, что принимает CSS (`clip-path`, `border-image`, `background`, `box-shadow`, `animation` …).

### Переопределения цветов

Большинству тем это не понадобится — 3‑слойная палитра выводит все токены shadcn. Используй `colorOverrides`, когда нужен конкретный акцент, который не получится вывести из палитры (мягкий destructive‑red для пастельной темы, определённый success‑green для бренда).

```yaml
colorOverrides:
  primary: "#ffce3a"
  primaryForeground: "#05091a"
  accent: "#3fd3ff"
  ring: "#3fd3ff"
  destructive: "#ff3a5e"
  border: "rgba(64, 200, 255, 0.28)"
```

Поддерживаемые ключи: `card`, `cardForeground`, `popover`, `popoverForeground`, `primary`, `primaryForeground`, `secondary`, `secondaryForeground`, `muted`, `mutedForeground`, `accent`, `accentForeground`, `destructive`, `destructiveForeground`, `success`, `warning`, `border`, `input`, `ring`.

Каждый ключ напрямую сопоставляется с CSS‑переменной `--color-<kebab>` (например, `primaryForeground` → `--color-primary-foreground`). Любой ключ, установленный здесь, переопределяет каскад палитры только для активной темы — при переключении на другую тему переопределения сбрасываются.

### Необработанный `customCSS`

Для стилизации на уровне селекторов, которую `componentStyles` не может выразить — псевдоэлементы, анимации, медиазапросы, переопределения в области темы — помещай сырой CSS в `customCSS`:

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

CSS вставляется как один ограниченный областью `<style data-hermes-theme-css>` при применении темы и удаляется при её смене. **Ограничение — 32 KiB на тему.**

### Встроенные темы

Каждая встроенная тема поставляется со своей палитрой, типографикой и макетом — переключение меняет не только цвета.

| Тема | Палитра | Типография | Макет |
|------|---------|------------|-------|
| **Hermes Teal** (`default`) | Тёмный бирюзовый + кремовый | Системный стек, 15 px | Радиус 0.5 rem, comfortable |
| **Hermes Teal (Large)** (`default-large`) | Как у `default` | Системный стек, 18 px, line-height 1.65 | Радиус 0.5 rem, spacious |
| **Midnight** (`midnight`) | Глубокий синий‑фиолетовый | Inter + JetBrains Mono, 14 px | Радиус 0.75 rem, comfortable |
| **Ember** (`ember`) | Тёплый малиновый + бронза | Spectral (serif) + IBM Plex Mono, 15 px | Радиус 0.25 rem, comfortable |
| **Mono** (`mono`) | Оттенки серого | IBM Plex Sans + IBM Plex Mono, 13 px | Радиус 0, compact |
| **Cyberpunk** (`cyberpunk`) | Неоновый зелёный на чёрном | Share Tech Mono везде, 14 px | Радиус 0, compact |
| **Rosé** (`rose`) | Розовый + слоновая кость | Fraunces (serif) + DM Mono, 16 px | Радиус 1 rem, spacious |

Темы, использующие Google Fonts (все, кроме Hermes Teal), загружают таблицу стилей по требованию — при первом переключении на них в `<head>` вставляется тег `<link>`.

### Полный справочник YAML темы

Все настройки в одном файле — копируй и убирай то, что не нужно:

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

Обнови панель после создания файла. Переключай темы в реальном времени из строки заголовка — нажми иконку палитры. Выбор сохраняется в `config.yaml` под `dashboard.theme` и восстанавливается при перезагрузке.
## Плагины

Dashboard‑плагин — это каталог, содержащий `manifest.json`, предварительно собранный JS‑bundle и, опционально, CSS‑файл и Python‑файл с FastAPI‑маршрутами. Плагины находятся рядом с другими плагинами Hermes в `~/.hermes/plugins/<name>/` — расширение панели представляет собой подпапку `dashboard/` внутри каталога плагина, так что один плагин может расширять как CLI/gateway, так и dashboard из единой установки.

Плагины не включают React или UI‑компоненты. Они используют **Plugin SDK**, доступный через `window.__HERMES_PLUGIN_SDK__`. Это делает bundle‑ы плагинов крошечными (обычно несколько КБ) и избегает конфликтов версий.

### Быстрый старт — твой первый плагин

Создай структуру каталогов:

```bash
mkdir -p ~/.hermes/plugins/my-plugin/dashboard/dist
```

Напиши манифест:

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

Напиши JS‑bundle (обычный IIFE — без этапа сборки):

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

Обнови dashboard — твоя вкладка появится в навигационной панели после **Skills**.

:::tip Пропуск React.createElement
Если предпочитаешь JSX, используй любой бандлер (esbuild, Vite, rollup) с React в качестве внешней зависимости и выводом IIFE. Единственное требование — чтобы итоговый файл был одним JS‑файлом, загружаемым через `<script>`. React никогда не включается в bundle; он берётся из `SDK.React`.
:::

### Структура каталогов

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

Один каталог плагина может содержать три независимых расширения:

- `plugin.yaml` + `__init__.py` — CLI/gateway‑плагин ([см. страницу plugins](./plugins)).
- `dashboard/manifest.json` + `dashboard/dist/index.js` — UI‑плагин dashboard.
- `dashboard/plugin_api.py` — бекенд‑маршруты dashboard.

Ни одно из них не является обязательным; включай только те слои, которые нужны.

### Справочник манифеста

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

| Поле | Обязательно | Описание |
|------|--------------|----------|
| `name` | Да | Уникальный идентификатор плагина. Нижний регистр, допускаются дефисы. Используется в URL и при регистрации. |
| `label` | Да | Отображаемое имя, показываемое во вкладке навигации. |
| `description` | Нет | Краткое описание (отображается в админ‑интерфейсе dashboard). |
| `icon` | Нет | Имя иконки Lucide. По умолчанию `Puzzle`. Неизвестные имена падают к `Puzzle`. |
| `version` | Нет | Строка semver. По умолчанию `0.0.0`. |
| `tab.path` | Да | URL‑путь для вкладки (например `/my-plugin`). |
| `tab.position` | Нет | Где вставить вкладку. `"end"` (по умолчанию), `"after:<path>"`, `"before:<path>"` — значение после двоеточия — **сегмент пути** целевой вкладки (без начального слеша). Примеры: `"after:skills"`, `"before:config"`. |
| `tab.override` | Нет | Установить путь встроенного маршрута (`"/"`, `"/sessions"`, `"/config"` и т.д.) для **замены** этой страницы вместо добавления новой вкладки. См. [Замена встроенных страниц](#replacing-built-in-pages-taboverride). |
| `tab.hidden` | Нет | При `true` регистрирует компонент и любые слоты без добавления вкладки в навигацию. Используется плагинами только со слотами. См. [Плагины только со слотами](#slot-only-plugins-tabhidden). |
| `slots` | Нет | Именованные слоты оболочки, которые заполняет плагин. **Только для документации** — реальная регистрация происходит из JS‑bundle через `registerSlot()`. Перечисление слотов здесь делает поверхности обнаружения более информативными. |
| `entry` | Да | Путь к JS‑bundle относительно `dashboard/`. По умолчанию `dist/index.js`. |
| `css` | Нет | Путь к CSS‑файлу, который будет вставлен как тег `<link>`. |
| `api` | Нет | Путь к Python‑файлу с FastAPI‑маршрутами. Монтируется по `/api/plugins/<name>/`. |

#### Доступные иконки

Плагины используют имена иконок Lucide. Dashboard сопоставляет их по имени — неизвестные имена тихо падают к `Puzzle`.

Сейчас сопоставлены: `Activity`, `BarChart3`, `Clock`, `Code`, `Database`, `Eye`, `FileText`, `Globe`, `Heart`, `KeyRound`, `MessageSquare`, `Package`, `Puzzle`, `Settings`, `Shield`, `Sparkles`, `Star`, `Terminal`, `Wrench`, `Zap`.

Нужна другая иконка? Открой PR в `web/src/App.tsx` в `ICON_MAP` — чисто добавляющее изменение.

### Plugin SDK

Всё, что нужно плагину, находится на `window.__HERMES_PLUGIN_SDK__`. Плагины никогда не должны импортировать React напрямую.

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

#### Вызов бекенда твоего плагина

```javascript
SDK.fetchJSON("/api/plugins/my-plugin/data")
  .then((data) => console.log(data))
  .catch((err) => console.error("API call failed:", err));
```

`fetchJSON` добавляет токен аутентификации сессии, преобразует ошибки в выбрасываемые исключения и автоматически парсит JSON.

#### Вызов встроенных эндпоинтов Hermes

```javascript
// Agent status
SDK.api.getStatus().then((s) => console.log("Version:", s.version));

// Recent sessions
SDK.api.getSessions(10).then((resp) => console.log(resp.sessions.length));
```

См. [Web Dashboard → REST API](./web-dashboard#rest-api) для полного списка.

### Слоты оболочки

Слоты позволяют плагину внедрять компоненты в именованные места оболочки приложения — боковую панель cockpit, шапку, подвал, слой‑оверлей — без создания отдельной вкладки. Несколько плагинов могут заполнять один и тот же слот; они рендерятся в порядке регистрации.

Регистрация изнутри bundle плагина:

```javascript
window.__HERMES_PLUGINS__.registerSlot("my-plugin", "sidebar", MySidebar);
window.__HERMES_PLUGINS__.registerSlot("my-plugin", "header-left", MyCrest);
```

#### Каталог слотов

**Слоты, доступные во всей оболочке** (рендерятся где‑угодно в хроме приложения):

| Слот | Расположение |
|------|--------------|
| `backdrop` | Внутри стека слоя `<Backdrop />`, над шумовым слоем. |
| `header-left` | Перед брендом Hermes в верхней панели. |
| `header-right` | Перед переключателями темы/языка в верхней панели. |
| `header-banner` | Полноширинная полоса под навигацией. |
| `sidebar` | Рельс боковой панели cockpit — **рендерится только когда `layoutVariant === "cockpit"`**. |
| `pre-main` | Над outlet‑ом маршрута (внутри `<main>`). |
| `post-main` | Под outlet‑ом маршрута (внутри `<main>`). |
| `footer-left` | Содержимое ячейки подвала (заменяет дефолт). |
| `footer-right` | Содержимое ячейки подвала (заменяет дефолт). |
| `overlay` | Фиксированный слой над всем остальным. Полезно для хрома (сканлайны, виньетки), чего нельзя достичь только `customCSS`. |

**Слоты, ограниченные страницей** (рендерятся только на указанной встроенной странице — используют их для внедрения виджетов, карточек или тулбаров без переопределения всего маршрута):

| Слот | Где рендерится |
|------|-----------------|
| `sessions:top` / `sessions:bottom` | Верх / низ страницы `/sessions`. |
| `analytics:top` / `analytics:bottom` | Верх / низ страницы `/analytics`. |
| `logs:top` / `logs:bottom` | Верх (над панелью фильтров) / низ (под просмотрщиком логов) страницы `/logs`. |
| `cron:top` / `cron:bottom` | Верх / низ страницы `/cron`. |
| `skills:top` / `skills:bottom` | Верх / низ страницы `/skills`. |
| `config:top` / `config:bottom` | Верх / низ страницы `/config`. |
| `env:top` / `env:bottom` | Верх / низ страницы `/env` (Keys). |
| `docs:top` / `docs:bottom` | Верх (над iframe) / низ страницы `/docs`. |
| `chat:top` / `chat:bottom` | Верх / низ `/chat` (активно только при включённом встроенном чате). |

Пример — добавить баннер‑карту в верхнюю часть страницы Sessions:

```javascript
function PinnedSessionsBanner() {
  return React.createElement(Card, null,
    React.createElement(CardContent, { className: "py-2 text-xs" },
      "Pinned note injected by my-plugin"),
  );
}

window.__HERMES_PLUGINS__.registerSlot("my-plugin", "sessions:top", PinnedSessionsBanner);
```

Комбинируй слоты, ограниченные страницей, с `tab.hidden: true`, если плагин лишь дополняет существующие страницы и не нуждается в собственной вкладке боковой панели.

Оболочка рендерит `<PluginSlot name="..." />` только для слотов, перечисленных выше. Дополнительные имена принимаются реестром для вложенных UI‑плагинов — плагин может объявлять свои собственные слоты через `SDK.components.PluginSlot`.

#### Повторная регистрация и HMR

Если одна и та же пара `(plugin, slot)` регистрируется дважды, более поздний вызов заменяет предыдущий — это соответствует поведению React HMR при пере‑монтировании плагинов.

### Замена встроенных страниц (`tab.override`)

Установка `tab.override` в путь встроенного маршрута заставляет компонент плагина заменять эту страницу вместо добавления новой вкладки. Полезно, когда тема хочет кастомную домашнюю страницу (`/`), но оставить остальную панель без изменений.

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

При установленном `override`:

- Оригинальный компонент страницы `/` удаляется из роутера.
- Твой плагин рендерится по `/`.
- Вкладка навигации для `tab.path` не добавляется (переопределение — это цель).

Только один плагин может переопределять данный путь. Если два плагина заявят один и тот же `override`, победит первый, а второй будет проигнорирован с предупреждением в режиме разработки.

Если нужно лишь добавить карточку или тулбар к существующей странице, используй [слоты, ограниченные страницей](#augmenting-built-in-pages-page-scoped-slots) вместо полной замены.

### Дополнение встроенных страниц (слоты, ограниченные страницей)

Полная замена через `tab.override` тяжёлая — плагин полностью владеет страницей, включая любые будущие обновления. Чаще всего требуется лишь добавить баннер, карточку или тулбар к существующей странице. Для этого и предназначены **слоты, ограниченные страницей**.

Каждая встроенная страница предоставляет слоты `<page>:top` и `<page>:bottom`, рендерящиеся в верхней и нижней части её области контента. Плагин заполняет один из них, вызывая `registerSlot()` — встроенная страница продолжает работать как обычно, а твой компонент рендерится рядом.

Доступные слоты: `sessions:*`, `analytics:*`, `logs:*`, `cron:*`, `skills:*`, `config:*`, `env:*`, `docs:*`, `chat:*` (каждый с `:top` и `:bottom`). См. полный каталог в [Shell slots → Slot catalogue](#slot-catalogue).

Минимальный пример — закрепить баннер в верхней части страницы Sessions:

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

Ключевые моменты:

- `tab.hidden: true` удерживает плагин от появления в боковой панели — у него нет отдельной страницы.
- Поле `slots` в манифесте служит только документации. Реальная привязка происходит в JS‑bundle через `registerSlot()`.
- Несколько плагинов могут заявлять один и тот же слот, ограниченный страницей; они рендерятся в порядке регистрации.
- При отсутствии зарегистрированных плагинов следа нет — встроенная страница рендерится как прежде.

Пример плагина (`example-dashboard` в [`hermes-example-plugins`](https://github.com/NousResearch/hermes-example-plugins/tree/main/example-dashboard)) поставляется с живой демонстрацией, которая внедряет баннер в `sessions:top` — установи его, чтобы увидеть паттерн от начала до конца.

### Плагины только со слотами (`tab.hidden`)

Когда `tab.hidden: true`, плагин регистрирует свой компонент (для прямых URL‑запросов) и любые слоты, но никогда не добавляет вкладку в навигацию. Используется плагинами, которые существуют лишь для внедрения в слоты — шапка, HUD боковой панели, оверлей.

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

Bundle всё равно вызывает `register()` с заглушкой компонента (хорошая практика на случай прямого обращения к URL) и затем `registerSlot()` для реальной работы.

### Бекенд‑маршруты API

Плагины могут регистрировать FastAPI‑маршруты, указав `api` в манифесте. Создай файл и экспортируй `router`:

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

Маршруты монтируются под `/api/plugins/<name>/`, так что выше будет:

- `GET  /api/plugins/my-plugin/data`
- `POST /api/plugins/my-plugin/action`

API‑маршруты плагина обходят аутентификацию токеном сессии, поскольку сервер dashboard по умолчанию привязан к localhost. **Не выставляй dashboard в публичный интерфейс с `--host 0.0.0.0`, если запускаешь недоверенные плагины** — их маршруты тоже станут доступными.

#### Доступ к внутренностям Hermes

Бекенд‑маршруты работают внутри процесса dashboard, поэтому могут импортировать код из репозитория hermes-agent напрямую:

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

### Пользовательский CSS для плагина

Если плагину нужны стили, выходящие за рамки классов Tailwind и инлайн‑`style=`, добавь CSS‑файл и укажи его в манифесте:

```json
{
  "css": "dist/style.css"
}
```

Файл будет вставлен как тег `<link>` при загрузке плагина. Используй специфичные имена классов, чтобы избежать конфликтов со стилями dashboard, и обращайся к CSS‑переменным dashboard, чтобы оставаться в теме:

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

Dashboard экспортирует каждый токен shadcn как `--color-*` плюс дополнительные переменные темы (`--theme-asset-*`, `--component-<bucket>-*`, `--radius`, `--spacing-mul`). Ссылайся на них, и твой плагин автоматически подстроится под активную тему.

### Обнаружение плагинов и перезагрузка

Dashboard сканирует три каталога в поисках `dashboard/manifest.json`:

| Приоритет | Каталог | Метка источника |
|----------|--------|------------------|
| 1 (побеждает при конфликте) | `~/.hermes/plugins/<name>/dashboard/` | `user` |
| 2 | `<repo>/plugins/memory/<name>/dashboard/` | `bundled` |
| 2 | `<repo>/plugins/<name>/dashboard/` | `bundled` |
| 3 | `./.hermes/plugins/<name>/dashboard/` | `project` — только при установленной переменной `HERMES_ENABLE_PROJECT_PLUGINS` |

Результаты обнаружения кэшируются в процессе dashboard. После добавления нового плагина сделай одно из следующее:

```bash
# Force a rescan without restart
curl http://127.0.0.1:9119/api/dashboard/plugins/rescan
```

…или перезапусти `hermes dashboard`.

#### Жизненный цикл загрузки плагина

1. Dashboard загружается. `main.tsx` выставляет SDK на `window.__HERMES_PLUGIN_SDK__` и реестр на `window.__HERMES_PLUGINS__`.
2. `App.tsx` вызывает `usePlugins()` → делает запрос `GET /api/dashboard/plugins`.
3. Для каждого манифеста: вставляется CSS‑`<link>` (если указан), затем загружается JS‑bundle через `<script>`.
4. IIFE плагина исполняется и вызывает `window.__HERMES_PLUGINS__.register(name, Component)` — и опционально `.registerSlot(name, slot, Component)` для каждого слота.
5. Dashboard сопоставляет зарегистрированный компонент с манифестом, добавляет вкладку в навигацию (если не `hidden`) и монтирует компонент как маршрут.

У плагинов есть **2 секунды** после загрузки скрипта, чтобы вызвать `register()`. После этого dashboard прекращает ожидание и завершает первоначальный рендер. Если плагин регистрируется позже, он всё равно появляется — навигация реактивна.

Если скрипт плагина не загружается (404, синтаксическая ошибка, исключение в IIFE), dashboard выводит предупреждение в консоль браузера и продолжает работу без него.
## Combined theme + plugin demo

Плагин [`strike-freedom-cockpit`](https://github.com/NousResearch/hermes-example-plugins/tree/main/strike-freedom-cockpit) (репозиторий‑компаньон `hermes-example-plugins`) — это полноценный демонстрационный пример перекраски. Он сочетает YAML‑тему с плагином‑только‑слот, чтобы создать HUD в стиле кокпита без форка дашборда.

**Что демонстрируется:**

- Полная тема, использующая `palette`, `typography`, `fontUrl`, `layoutVariant: cockpit`, `assets`, `componentStyles` (скруглённые углы карточек, градиентные фоны), `colorOverrides` и `customCSS` (наложение сканлайн‑оверлея).
- Плагин‑только‑слот (`tab.hidden: true`), который регистрируется в трёх слотах:
  - `sidebar` — панель MS‑STATUS с живыми телеметрическими полосами, управляемыми `SDK.api.getStatus()`.
  - `header-left` — герб фракции, читающий `--theme-asset-crest` из активной темы.
  - `footer-right` — пользовательский слоган, заменяющий строку организации по умолчанию.
- Плагин читает предоставленные темой графические ресурсы через CSS‑переменные, поэтому смена темы меняет герой/герб без изменений кода плагина.

**Установка:**

```bash
git clone https://github.com/NousResearch/hermes-example-plugins.git

# Theme
cp hermes-example-plugins/strike-freedom-cockpit/theme/strike-freedom.yaml \
   ~/.hermes/dashboard-themes/

# Plugin
cp -r hermes-example-plugins/strike-freedom-cockpit ~/.hermes/plugins/
```

Открой дашборд, выбери **Strike Freedom** в переключателе тем. Появится боковая панель кокпита, герб отобразится в заголовке, слоган заменит нижний колонтитул. Переключи обратно на **Hermes Teal**, и плагин останется установленным, но будет невидим (слот `sidebar` рендерится только при варианте раскладки `cockpit`).

Прочитай исходный код плагина (`strike-freedom-cockpit/dashboard/dist/index.js` в репозитории‑компаньоне), чтобы увидеть, как он читает CSS‑переменные, защищается от более старых дашбордов без поддержки слотов и регистрирует три слота из одного пакета.
## Справочник API

### Эндпоинты тем

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/themes` | GET | Список доступных тем и имя активной. Встроенные возвращают `{name, label, description}`; пользовательские темы также включают поле `definition` с полным нормализованным объектом темы. |
| `/api/dashboard/theme` | PUT | Установить активную тему. Тело: `{"name": "midnight"}`. Сохраняется в `config.yaml` под `dashboard.theme`. |

### Эндпоинты плагинов

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/plugins` | GET | Список обнаруженных плагинов (с манифестами, без внутренних полей). |
| `/api/dashboard/plugins/rescan` | GET | Принудительно пересканировать каталоги плагинов без перезапуска. |
| `/dashboard-plugins/<name>/<path>` | GET | Обслуживание статических ресурсов из каталога `dashboard/` плагина. Перемещение по пути блокируется. |
| `/api/plugins/<name>/*` | * | Маршруты бэкенда, зарегистрированные плагином. |

### SDK в `window`

| Global | Type | Provider |
|--------|------|----------|
| `window.__HERMES_PLUGIN_SDK__` | object | `registry.ts` — React, хуки, UI‑компоненты, клиент API, утилиты. |
| `window.__HERMES_PLUGINS__.register(name, Component)` | function | Регистрация основного компонента плагина. |
| `window.__HERMES_PLUGINS__.registerSlot(name, slot, Component)` | function | Регистрация в именованный слот оболочки. |

---
## Устранение неполадок

**Моя тема не появляется в выборе.**
Проверь, что файл находится в `~/.hermes/dashboard-themes/` и имеет расширение `.yaml` или `.yml`. Обнови страницу. Выполни `curl http://127.0.0.1:9119/api/dashboard/themes` — тема должна присутствовать в ответе. Если в YAML есть ошибка разбора, дашборд пишет в `errors.log` в `~/.hermes/logs/`.

**Вкладка моего плагина не отображается.**
1. Убедись, что манифест находится по пути `~/.hermes/plugins/<name>/dashboard/manifest.json` (обрати внимание на подпапку `dashboard/`).
2. Выполни `curl http://127.0.0.1:9119/api/dashboard/plugins/rescan`, чтобы принудительно выполнить повторное обнаружение.
3. Открой инструменты разработчика браузера → **Network** — убедись, что `manifest.json`, `index.js` и любые CSS‑файлы загружаются без 404.
4. Открой инструменты разработчика браузера → **Console** — ищи ошибки во время выполнения IIFE или сообщение `window.__HERMES_PLUGINS__ is undefined` (это значит, что SDK не инициализировался, обычно из‑за краха рендера React ранее).
5. Проверь, что твой бандл вызывает `window.__HERMES_PLUGINS__.register(...)` с **тем же именем**, что указано в `manifest.json:name`.

**Компоненты, зарегистрированные в слотах, не рендерятся.**
Слот `sidebar` рендерится только тогда, когда активная тема имеет `layoutVariant: cockpit`. Остальные слоты всегда рендерятся. Если ты регистрируешь компонент в слот, где нет попаданий, добавь `console.log` внутри `registerSlot`, чтобы убедиться, что бандл плагина вообще выполнился.

**Маршруты backend‑плагина возвращают 404.**
1. Убедись, что в манифесте указано `"api": "plugin_api.py"` и файл действительно существует в папке `dashboard/`.
2. Перезапусти `hermes dashboard` — маршруты API плагина монтируются один раз при старте, **не** при повторном сканировании.
3. Проверь, что `plugin_api.py` экспортирует переменную уровня модуля `router = APIRouter()`. Другие имена экспорта не распознаются.
4. Просмотри `~/.hermes/logs/errors.log` на наличие строки `Failed to load plugin <name> API routes` — ошибки импорта записываются туда.

**Смена темы сбрасывает мои переопределения цветов.**
`colorOverrides` привязаны к активной теме и очищаются при переключении темы — это задумано так. Если нужны переопределения, сохраняющие состояние, помести их в YAML темы, а не в живой переключатель.

**`customCSS` темы обрезается.**
Блок `customCSS` ограничен 32 КиБ на тему. Раздели большие таблицы стилей на несколько тем или используй плагин, который внедряет полный файл стилей через поле `css` (без ограничения размера).

**Хочу разместить плагин в PyPI.**
Плагины дашборда устанавливаются по структуре каталогов, а не через точку входа pip. Наиболее чистый способ распространения сегодня — git‑репозиторий, который пользователь клонирует в `~/.hermes/plugins/`. Установщик на основе pip для плагинов дашборда пока не реализован.