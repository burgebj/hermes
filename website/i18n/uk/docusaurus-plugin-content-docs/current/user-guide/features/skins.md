---
sidebar_position: 10
title: "Скіни та теми"
description: "Налаштуй Hermes CLI за допомогою вбудованих та визначених користувачем шкір"
---

# Шкіри та теми

Шкіри керують **візуальним представленням** Hermes CLI: кольорами банера, обличчями спінера та дієсловами, мітками у вікнах відповіді, текстом бренду та префіксом активності інструменту.

Стиль розмови та візуальний стиль — це окремі поняття:

- **Персональність** змінює тон і формулювання агента.
- **Шкіра** змінює зовнішній вигляд CLI.
## Змінити скіни

```bash
/skin                # show the current skin and list available skins
/skin ares           # switch to a built-in skin
/skin mytheme        # switch to a custom skin from ~/.hermes/skins/mytheme.yaml
```

Або встанови типову шкірку у `~/.hermes/config.yaml`:

```yaml
display:
  skin: default
```
## Вбудовані теми

| Тема | Опис | Брендування агента | Візуальний характер |
|------|------|-------------------|--------------------|
| `default` | Класичний Hermes — золотий і каваї | `Hermes Agent` | Теплі золоті рамки, текст cornsilk, каваї‑обличчя у спінерах. Знайомий банер з кадуцеєм. Чисто і запрошуюче. |
| `ares` | Тема бога війни — малиновий і бронзовий | `Ares Agent` | Глибокі малинові рамки з бронзовими акцентами. Агресивні дієслова спінера («forging», «marching», «tempering steel»). Кастомний ASCII‑банер меча‑та‑щита. |
| `mono` | Монохром — чистий сіро‑білий | `Hermes Agent` | Весь сірий — без кольору. Рамки `#555555`, текст `#c9d1d9`. Ідеально для мінімальних налаштувань терміналу або запису екрану. |
| `slate` | Холодний синій — орієнтований на розробників | `Hermes Agent` | Королівські сині рамки (`#4169e1`), м’який синій текст. Спокійно і професійно. Без кастомного спінера — використовується стандартний. |
| `daylight` | Світла тема для яскравих терміналів з темним текстом і холодними синіми акцентами | `Hermes Agent` | Призначена для білих або яскравих терміналів. Темний slate‑текст з синіми рамками, бліді поверхні статусу та легке меню завершення, що залишається читабельним у світлих профілях терміналу. |
| `warm-lightmode` | Теплий коричнево‑золотий текст для світлих фонів терміналу | `Hermes Agent` | Теплі пергаментні тони для світлих терміналів. Темний коричневий текст з акцентами saddle‑brown, кремові поверхні статусу. Земна альтернатива охолодженій темі daylight. |
| `poseidon` | Тема бога океану — глибокий синій і морська піна | `Poseidon Agent` | Глибокий синій градієнт до морської піни. Океанічні спінери («charting currents», «sounding the depth»). ASCII‑банер тризуба. |
| `sisyphus` | Сисіфічна тема — суворий сіро‑білий з наполегливістю | `Sisyphus Agent` | Світлі сірі тони з різким контрастом. Спінери з темою валу («pushing uphill», «resetting the boulder», «enduring the loop»). ASCII‑банер валу‑і‑гори. |
| `charizard` | Вулканічна тема — спалений помаранч і жар | `Charizard Agent` | Теплий градієнт від спаленого помаранчу до жару. Спінери з темою вогню («banking into the draft», «measuring burn»). ASCII‑банер силуету дракона. |
## Повний список налаштовуваних ключів

### Colors (`colors:`)

Керує всіма кольоровими значеннями у CLI. Значення – рядки у шістнадцятковому форматі.

| Key | Description | Default (`default` skin) |
|-----|-------------|--------------------------|
| `banner_border` | Межа панелі навколо стартового банеру | `#CD7F32` (бронза) |
| `banner_title` | Колір тексту заголовка в банері | `#FFD700` (золото) |
| `banner_accent` | Заголовки розділів у банері (Available Tools тощо) | `#FFBF00` (янтар) |
| `banner_dim` | Приглушений текст у банері (розділювачі, вторинні мітки) | `#B8860B` (темний золотистий) |
| `banner_text` | Основний текст у банері (назви інструментів, назви навичок) | `#FFF8DC` (cornsilk) |
| `ui_accent` | Загальний колір акценту UI (виділення, активні елементи) | `#FFBF00` |
| `ui_label` | Мітки та теги UI | `#4dd0e1` (бірюзовий) |
| `ui_ok` | Індикатори успіху (галочки, завершення) | `#4caf50` (зелений) |
| `ui_error` | Індикатори помилок (збої, блокування) | `#ef5350` (червоний) |
| `ui_warn` | Індикатори попереджень (увага, запити підтвердження) | `#ffa726` (оранжевий) |
| `prompt` | Колір тексту інтерактивного підказника | `#FFF8DC` |
| `input_rule` | Горизонтальна лінія над областю вводу | `#CD7F32` |
| `response_border` | Межа навколо вікна відповіді агента (ANSI escape) | `#FFD700` |
| `session_label` | Колір мітки сесії | `#DAA520` |
| `session_border` | Приглушений колір межі ID сесії | `#8B8682` |
| `status_bar_bg` | Колір фону смуги стану / використання TUI | `#1a1a2e` |
| `voice_status_bg` | Колір фону бейджа стану голосового режиму | `#1a1a2e` |
| `selection_bg` | Колір фону підсвічування мишкою в TUI. Повертається до `completion_menu_current_bg`, якщо не встановлено. | `#333355` |
| `completion_menu_bg` | Колір фону списку меню автодоповнення | `#1a1a2e` |
| `completion_menu_current_bg` | Колір фону активного рядка автодоповнення | `#333355` |
| `completion_menu_meta_bg` | Колір фону колонки метаданих автодоповнення | `#1a1a2e` |
| `completion_menu_meta_current_bg` | Колір фону активної колонки метаданих автодоповнення | `#333355` |

### Spinner (`spinner:`)

Керує анімованим спінером, що показується під час очікування відповідей API.

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `waiting_faces` | list of strings | Обличчя, що циклічно змінюються під час очікування відповіді API | `["(⚔)", "(⛨)", "(▲)"]` |
| `thinking_faces` | list of strings | Обличчя, що циклічно змінюються під час роздумів моделі | `["(⚔)", "(⌁)", "(<>)"]` |
| `thinking_verbs` | list of strings | Дієслова, що показуються в повідомленнях спінера | `["forging", "plotting", "hammering plans"]` |
| `wings` | list of [left, right] pairs | Декоративні дужки навколо спінера | `[["⟪⚔", "⚔⟫"], ["⟪▲", "▲⟫"]]` |

Коли значення спінера порожні (наприклад у `default` та `mono`), використовуються жорстко закодовані значення за замовчуванням з `display.py`.

### Branding (`branding:`)

Текстові рядки, що використовуються у всьому інтерфейсі CLI.

| Key | Description | Default |
|-----|-------------|---------|
| `agent_name` | Назва, що показується в заголовку банеру та індикаторі стану | `Hermes Agent` |
| `welcome` | Привітальне повідомлення при запуску CLI | `Welcome to Hermes Agent! Type your message or /help for commands.` |
| `goodbye` | Повідомлення при виході | `Goodbye! ⚕` |
| `response_label` | Мітка в заголовку вікна відповіді | ` ⚕ Hermes ` |
| `prompt_symbol` | Символ перед підказкою вводу користувача (голий токен, рендерери додають пробіл) | `❯` |
| `help_header` | Текст заголовка виводу команди `/help` | `(^_^)? Available Commands` |

### Інші ключі верхнього рівня

| Key | Type | Description | Default |
|-----|------|-------------|---------|
| `tool_prefix` | string | Символ, що префіксує рядки виводу інструменту в CLI | `┊` |
| `tool_emojis` | dict | Перезапис емодзі для окремих інструментів у спінерах та прогресі (`{tool_name: emoji}`) | `{}` |
| `banner_logo` | string | ASCII‑арт логотипу у Rich‑розмітці (замінює банер HERMES_AGENT за замовчуванням) | `""` |
| `banner_hero` | string | ASCII‑арт героя у Rich‑розмітці (замінює арт кадуцея за замовчуванням) | `""` |
## Користувацькі скіни

Створюй YAML‑файли у `~/.hermes/skins/`. Скіни користувачів успадковують відсутні значення від вбудованого скіна `default`, тому тобі потрібно вказати лише ті ключі, які треба змінити.

### Повний шаблон YAML для користувацького скіна

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

### Приклад мінімального користувацького скіна

Оскільки все успадковується від `default`, мінімальний скин потребує змінити лише те, що відрізняється:

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
## Hermes Mod — Visual Skin Editor

[Hermes Mod](https://github.com/cocktailpeanut/hermes-mod) — це створений спільнотою веб‑інтерфейс для візуального створення та керування скіннами. Замість ручного написання YAML ти отримуєш редактор «вказати‑і‑клацнути» з живим попереднім переглядом.

![Hermes Mod skin editor](https://raw.githubusercontent.com/cocktailpeanut/hermes-mod/master/nous.png)

**Що він робить:**

- Перелічує всі вбудовані та користувацькі скінни
- Відкриває будь‑який скін у візуальному редакторі з усіма полями скіну Hermes (кольори, спінер, брендинг, префікс інструменту, емодзі інструменту)
- Генерує текстове мистецтво `banner_logo` за текстовим запитом
- Перетворює завантажені зображення (PNG, JPG, GIF, WEBP) у ASCII‑мистецтво `banner_hero` з кількома стилями рендерингу (braille, ASCII ramp, blocks, dots)
- Зберігає безпосередньо у `~/.hermes/skins/`
- Активує скін, оновлюючи `~/.hermes/config.yaml`
- Показує згенерований YAML та живий попередній перегляд

### Install

**Option 1 — Pinokio (1-click):**

Знайди його на [pinokio.computer](https://pinokio.computer) і встанови одним кліком.

**Option 2 — npx (quickest from terminal):**

```bash
npx -y hermes-mod
```

**Option 3 — Manual:**

```bash
git clone https://github.com/cocktailpeanut/hermes-mod.git
cd hermes-mod/app
npm install
npm start
```

### Usage

1. Запусти застосунок (через Pinokio або термінал).
2. Відкрий **Skin Studio**.
3. Вибери вбудований або користувацький скін для редагування.
4. Згенеруй логотип з тексту та/або завантаж зображення для hero‑арт. Вибери стиль рендерингу та ширину.
5. Відредагуй кольори, спінер, брендинг та інші поля.
6. Натисни **Save**, щоб записати YAML скіну у `~/.hermes/skins/`.
7. Натисни **Activate**, щоб встановити його як поточний скін (оновлює `display.skin` у `config.yaml`).

Hermes Mod враховує змінну середовища `HERMES_HOME`, тому працює і з [profiles](/user-guide/profiles).
## Операційні нотатки

- Вбудовані теми завантажуються з `hermes_cli/skin_engine.py`.
- Невідомі теми автоматично переходять до `default`.
- `/skin` одразу оновлює активну тему CLI у поточній сесії.
- Теми користувача в `~/.hermes/skins/` мають пріоритет над вбудованими темами з такою ж назвою.
- Зміни теми через `/skin` діють лише протягом сесії. Щоб зробити тему постійною за замовчуванням, встанови її в `config.yaml`.
- Поля `banner_logo` і `banner_hero` підтримують розмітку Rich console (наприклад, `[bold #FF0000]text[/]`) для кольорового ASCII‑арт.