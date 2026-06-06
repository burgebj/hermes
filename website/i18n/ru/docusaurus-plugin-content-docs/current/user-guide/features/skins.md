---
sidebar_position: 10
title: "Скины & Темы"
description: "Настрой Hermes CLI с помощью встроенных и пользовательских скинов"
---

# Скины и темы

Скины управляют **визуальным оформлением** Hermes CLI: цветами баннера, видами спиннеров и глаголами, метками в `response‑box`, текстом брендинга и префиксом активности инструмента.

Стиль общения и визуальный стиль — отдельные понятия:

- **Персональность** меняет тон и формулировки агента.
- **Скин** меняет внешний вид CLI.
## Сменить скины

```bash
/skin                # show the current skin and list available skins
/skin ares           # switch to a built-in skin
/skin mytheme        # switch to a custom skin from ~/.hermes/skins/mytheme.yaml
```

Или установить skin по умолчанию в `~/.hermes/config.yaml`:

```yaml
display:
  skin: default
```
## Встроенные скины

| Скин | Описание | Брендинг агента | Визуальный образ |
|------|----------|----------------|------------------|
| `default` | Классический Hermes — золотой и каваий | `Hermes Agent` | Тёплые золотые рамки, текст цвета corn‑silk, каваий‑лица в спиннерах. Знакомый баннер с кадуцеем. Чистый и приветливый. |
| `ares` | Тема бога войны — багровый и бронзовый | `Ares Agent` | Глубокие багровые рамки с бронзовыми акцентами. Агрессивные глаголы‑спиннеры («ковка», «марш», «закалка стали»). Пользовательский баннер‑арт меча и щита в ASCII. |
| `mono` | Монохромный — чистый градации серого | `Hermes Agent` | Всё в серых тонах — без цвета. Рамки `#555555`, текст `#c9d1d9`. Идеально для минималистичных терминалов или записи экрана. |
| `slate` | Холодный синий — для разработчиков | `Hermes Agent` | Королевские синие рамки (`#4169e1`), мягкий синий текст. Спокойно и профессионально. Без пользовательского спиннера — используется стандартный набор лиц. |
| `daylight` | Светлая тема для ярких терминалов с тёмным текстом и холодными синими акцентами | `Hermes Agent` | Предназначена для белых или ярких терминалов. Тёмный сланцевый текст с синими рамками, бледные статус‑поверхности и лёгкое меню завершения, остающееся читаемым в светлых профилях терминала. |
| `warm-lightmode` | Тёплый коричнево‑золотой текст для светлых терминалов | `Hermes Agent` | Тёплые тона пергамента для светлых терминалов. Тёмно‑коричневый текст с акцентами saddle‑brown, кремовые статус‑поверхности. Землистая альтернатива более холодной теме daylight. |
| `poseidon` | Тема бога океана — глубокий синий и морская пена | `Poseidon Agent` | Градиент от глубокого синего к морской пене. Спиннеры морской тематики («прокладываем течения», «измеряем глубину»). Баннер‑арт трезубца в ASCII. |
| `sisyphus` | Сизифовская тема — строгие градации серого с настойчивостью | `Sisyphus Agent` | Светлые серые тона с резким контрастом. Спиннеры в стиле валуна («поднимаем в гору», «перезапускаем валун», «выдерживаем цикл»). Баннер‑арт валуна и холма в ASCII. |
| `charizard` | Вулканическая тема — выжженный оранжевый и жар | `Charizard Agent` | Тёплый градиент от выжженного оранжевого к жару. Спиннеры огненной тематики («переключаемся в поток», «измеряем жар»). Баннер‑арт силуэта дракона в ASCII. |
## Полный список настраиваемых ключей

### Colors (`colors:`)

Управляет всеми цветовыми значениями в CLI. Значения — строки HEX‑цветов.

| Ключ | Описание | По умолчанию (`default` skin) |
|-----|-------------|--------------------------|
| `banner_border` | Граница панели вокруг стартового баннера | `#CD7F32` (bronze) |
| `banner_title` | Цвет текста заголовка в баннере | `#FFD700` (gold) |
| `banner_accent` | Заголовки разделов в баннере (Available Tools и т.д.) | `#FFBF00` (amber) |
| `banner_dim` | Приглушённый текст в баннере (разделители, вторичные метки) | `#B8860B` (dark goldenrod) |
| `banner_text` | Основной текст в баннере (названия инструментов, навыков) | `#FFF8DC` (cornsilk) |
| `ui_accent` | Общий акцент UI (подсветка, активные элементы) | `#FFBF00` |
| `ui_label` | Метки и теги UI | `#4dd0e1` (teal) |
| `ui_ok` | Индикаторы успеха (галочки, завершение) | `#4caf50` (green) |
| `ui_error` | Индикаторы ошибок (неудачи, блокировки) | `#ef5350` (red) |
| `ui_warn` | Индикаторы предупреждений (осторожность, запросы подтверждения) | `#ffa726` (orange) |
| `prompt` | Цвет текста интерактивного приглашения | `#FFF8DC` |
| `input_rule` | Горизонтальная линия над областью ввода | `#CD7F32` |
| `response_border` | Граница вокруг окна ответа агента (ANSI‑escape) | `#FFD700` |
| `session_label` | Цвет метки сессии | `#DAA520` |
| `session_border` | Цвет приглушённой границы ID сессии | `#8B8682` |
| `status_bar_bg` | Цвет фона статус‑/полосы использования TUI | `#1a1a2e` |
| `voice_status_bg` | Цвет фона бейджа статуса голосового режима | `#1a1a2e` |
| `selection_bg` | Цвет фона подсветки мышью в TUI. При отсутствии значения используется `completion_menu_current_bg`. | `#333355` |
| `completion_menu_bg` | Цвет фона списка меню автодополнения | `#1a1a2e` |
| `completion_menu_current_bg` | Цвет фона активной строки меню автодополнения | `#333355` |
| `completion_menu_meta_bg` | Цвет фона столбца метаданных автодополнения | `#1a1a2e` |
| `completion_menu_meta_current_bg` | Цвет фона активного столбца метаданных автодополнения | `#333355` |

### Spinner (`spinner:`)

Управляет анимированным спиннером, отображаемым во время ожидания ответов API.

| Ключ | Тип | Описание | Пример |
|-----|------|-------------|---------|
| `waiting_faces` | list of strings | Лица, переключающиеся во время ожидания ответа API | `["(⚔)", "(⛨)", "(▲)"]` |
| `thinking_faces` | list of strings | Лица, переключающиеся во время рассуждения модели | `["(⚔)", "(⌁)", "(<>)"]` |
| `thinking_verbs` | list of strings | Глаголы, показываемые в сообщениях спиннера | `["forging", "plotting", "hammering plans"]` |
| `wings` | list of [left, right] pairs | Декоративные скобки вокруг спиннера | `[["⟪⚔", "⚔⟫"], ["⟪▲", "▲⟫"]]` |

Когда значения спиннера пусты (как в `default` и `mono`), используются жёстко заданные значения из `display.py`.

### Branding (`branding:`)

Текстовые строки, используемые по всему интерфейсу CLI.

| Ключ | Описание | По умолчанию |
|-----|-------------|---------|
| `agent_name` | Имя, отображаемое в заголовке баннера и статусе | `Hermes Agent` |
| `welcome` | Приветственное сообщение при запуске CLI | `Welcome to Hermes Agent! Type your message or /help for commands.` |
| `goodbye` | Сообщение при выходе | `Goodbye! ⚕` |
| `response_label` | Метка в заголовке окна ответа | ` ⚕ Hermes ` |
| `prompt_symbol` | Символ перед приглашением ввода пользователя (голый токен, рендереры добавляют пробел) | `❯` |
| `help_header` | Текст заголовка вывода команды `/help` | `(^_^)? Available Commands` |

### Другие ключи верхнего уровня

| Ключ | Тип | Описание | По умолчанию |
|-----|------|-------------|---------|
| `tool_prefix` | string | Символ, добавляемый к строкам вывода инструмента в CLI | `┊` |
| `tool_emojis` | dict | Переопределения эмодзи для каждого инструмента в спиннерах и прогрессе (`{tool_name: emoji}`) | `{}` |
| `banner_logo` | string | ASCII‑арт логотип в формате Rich‑markup (заменяет баннер HERMES_AGENT) | `""` |
| `banner_hero` | string | ASCII‑арт «героя» в формате Rich‑markup (заменяет арт кадуцея) | `""` |
## Пользовательские скины

Создай YAML‑файлы в `~/.hermes/skins/`. Пользовательские скины наследуют недостающие значения из встроенного скина `default`, поэтому тебе нужно указывать только те ключи, которые ты хочешь изменить.

### Полный шаблон YAML пользовательского скина

```yaml
# ~/.hermes/skins/mytheme.yaml
# Complete skin template — all keys shown. Delete any you don't need;
# missing values automatically inherit from the 'default' skin.

name: mytheme
description: My custom theme

colors:
  banner_border: "#CD7F32"
  banner_title: "#FFD700"
  banner_accent: "#FFBF00"
  banner_dim: "#B8860B"
  banner_text: "#FFF8DC"
  ui_accent: "#FFBF00"
  ui_label: "#4dd0e1"
  ui_ok: "#4caf50"
  ui_error: "#ef5350"
  ui_warn: "#ffa726"
  prompt: "#FFF8DC"
  input_rule: "#CD7F32"
  response_border: "#FFD700"
  session_label: "#DAA520"
  session_border: "#8B8682"
  status_bar_bg: "#1a1a2e"
  voice_status_bg: "#1a1a2e"
  selection_bg: "#333355"
  completion_menu_bg: "#1a1a2e"
  completion_menu_current_bg: "#333355"
  completion_menu_meta_bg: "#1a1a2e"
  completion_menu_meta_current_bg: "#333355"

spinner:
  waiting_faces:
    - "(⚔)"
    - "(⛨)"
    - "(▲)"
  thinking_faces:
    - "(⚔)"
    - "(⌁)"
    - "(<>)"
  thinking_verbs:
    - "processing"
    - "analyzing"
    - "computing"
    - "evaluating"
  wings:
    - ["⟪⚡", "⚡⟫"]
    - ["⟪●", "●⟫"]

branding:
  agent_name: "My Agent"
  welcome: "Welcome to My Agent! Type your message or /help for commands."
  goodbye: "See you later! ⚡"
  response_label: " ⚡ My Agent "
  prompt_symbol: "⚡"
  help_header: "(⚡) Available Commands"

tool_prefix: "┊"

# Per-tool emoji overrides (optional)
tool_emojis:
  terminal: "⚔"
  web_search: "🔮"
  read_file: "📄"

# Custom ASCII art banners (optional, Rich markup supported)
# banner_logo: |
#   [bold #FFD700] MY AGENT [/]
# banner_hero: |
#   [#FFD700]  Custom art here  [/]
```

### Минимальный пример пользовательского скина

Поскольку всё наследуется от `default`, минимальному скину достаточно изменить только отличающиеся параметры:

```yaml
name: cyberpunk
description: Neon terminal theme

colors:
  banner_border: "#FF00FF"
  banner_title: "#00FFFF"
  banner_accent: "#FF1493"

spinner:
  thinking_verbs: ["jacking in", "decrypting", "uploading"]
  wings:
    - ["⟨⚡", "⚡⟩"]

branding:
  agent_name: "Cyber Agent"
  response_label: " ⚡ Cyber "

tool_prefix: "▏"
```
## Hermes Mod — визуальный редактор скинов

[Hermes Mod](https://github.com/cocktailpeanut/hermes-mod) — это созданный сообществом веб‑интерфейс для визуального создания и управления скинами. Вместо ручного написания YAML ты получаешь редактор «укажи‑и‑кликни» с живым предпросмотром.

![Hermes Mod skin editor](https://raw.githubusercontent.com/cocktailpeanut/hermes-mod/master/nous.png)

**Что он делает:**

- Показывает список всех встроенных и пользовательских скинов
- Открывает любой скин в визуальном редакторе со всеми полями скина Hermes (цвета, спиннер, брендинг, префикс инструмента, эмодзи инструмента)
- Генерирует текстовый арт `banner_logo` по текстовому запросу
- Преобразует загруженные изображения (PNG, JPG, GIF, WEBP) в ASCII‑арт `banner_hero` с несколькими стилями рендеринга (braille, ASCII ramp, blocks, dots)
- Сохраняет напрямую в `~/.hermes/skins/`
- Активирует скин, обновляя `~/.hermes/config.yaml`
- Показывает сгенерированный YAML и живой предпросмотр

### Установка

**Вариант 1 — Pinokio (один клик):**

Найди его на [pinokio.computer](https://pinokio.computer) и установи одним нажатием.

**Вариант 2 — npx (самый быстрый из терминала):**

```bash
npx -y hermes-mod
```

**Вариант 3 — вручную:**

```bash
git clone https://github.com/cocktailpeanut/hermes-mod.git
cd hermes-mod/app
npm install
npm start
```

### Использование

1. Запусти приложение (через Pinokio или терминал).
2. Открой **Skin Studio**.
3. Выбери встроенный или пользовательский скин для редактирования.
4. Сгенерируй логотип из текста и/или загрузите изображение для hero‑арта. Выбери стиль рендеринга и ширину.
5. Отредактируй цвета, спиннер, брендинг и другие поля.
6. Нажми **Save**, чтобы записать YAML скина в `~/.hermes/skins/`.
7. Нажми **Activate**, чтобы установить его текущим скином (обновляет `display.skin` в `config.yaml`).

Hermes Mod учитывает переменную окружения `HERMES_HOME`, поэтому работает и с [profiles](/user-guide/profiles).
## Примечания к эксплуатации

- Встроенные скины загружаются из `hermes_cli/skin_engine.py`.
- Неизвестные скины автоматически переключаются на `default`.
- Команда `/skin` сразу обновляет активный CLI‑скин для текущей сессии.
- Пользовательские скины в `~/.hermes/skins/` имеют приоритет над встроенными скинами с тем же именем.
- Изменения скина через `/skin` действуют только в рамках сессии. Чтобы сделать скин постоянным по умолчанию, укажи его в `config.yaml`.
- Поля `banner_logo` и `banner_hero` поддерживают разметку Rich console (например, `[bold #FF0000]text[/]`) для цветного ASCII‑искусства.