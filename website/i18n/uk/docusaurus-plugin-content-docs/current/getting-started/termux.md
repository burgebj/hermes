---
sidebar_position: 3
title: "Android / Termux"
description: "Запусти Hermes Agent безпосередньо на Android‑телефоні за допомогою Termux"
---

# Hermes на Android з Termux

Це перевірений шлях для запуску Hermes Agent безпосередньо на Android‑телефоні через [Termux](https://termux.dev/).

Він надає працюючий локальний CLI на телефоні, а також основні додатки, які наразі відомо, що встановлюються без проблем на Android.

## Що підтримується у перевіреному шляху?

Перевірений пакет Termux встановлює:
- Hermes CLI
- підтримку cron
- підтримку PTY/фонових терміналів
- підтримку шлюзу Telegram (ручний / best‑effort запуск у фоні)
- підтримку MCP
- підтримку пам’яті Honcho
- підтримку ACP

Конкретно, це відповідає:

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

## Що ще не входить до перевіреного шляху?

Декілька функцій ще потребують залежностей типу desktop/server, які не опубліковані для Android, або ще не були перевірені на телефонах:

- `.[all]` сьогодні не підтримується на Android
- додаток `voice` блокується `faster‑whisper → ctranslate2`, а `ctranslate2` не публікує Android‑колеса
- автоматичне завантаження браузера / Playwright пропускається у встановлювачі Termux
- ізоляція терміналу на базі Docker недоступна всередині Termux
- Android може призупиняти фонова завдання Termux, тому стійкість шлюзу є best‑effort, а не звичайною керованою службою

Це не заважає Hermes працювати добре як нативний CLI‑агент для телефону — це лише означає, що рекомендована мобільна інсталяція навмисно вузька порівняно з настільною/серверною.

---

## Варіант 1: Однорядковий інсталятор

Hermes тепер постачається зі шляхом інсталяції, орієнтованим на Termux:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

У Termux інсталятор автоматично:
- використовує `pkg` для системних пакетів
- створює venv за допомогою `python -m venv`
- спочатку намагається встановити широке `.[termux-all]` і у випадку невдачі переходить до меншого `.[termux]` (потім базова інсталяція) — curl‑інсталятор автоматично дотримується цього порядку
- створює посилання `hermes` у `$PREFIX/bin`, щоб він залишався у PATH Termux
- пропускає неперевірене завантаження браузера / WhatsApp

Якщо потрібні явні команди або треба відлагодити невдалу інсталяцію, скористайся ручним шляхом нижче.

---

## Варіант 2: Ручна інсталяція (повністю явна)

### 1. Онови Termux і встанови системні пакети

```bash
pkg update
pkg install -y git python clang rust make pkg-config libffi openssl nodejs ripgrep ffmpeg
```

Навіщо ці пакети?
- `python` — середовище виконання + підтримка venv
- `git` — клонування/оновлення репозиторію
- `clang`, `rust`, `make`, `pkg-config`, `libffi`, `openssl` — потрібні для збірки деяких Python‑залежностей на Android
- `nodejs` — необов’язкове середовище Node для експериментів поза межами перевіреного ядра
- `ripgrep` — швидкий пошук файлів
- `ffmpeg` — медіа / TTS‑конвертації

### 2. Клонуй Hermes

```bash
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
```

Якщо ти вже клонував без підмодулів:

```bash
git submodule update --init --recursive
```

### 3. Створи віртуальне середовище

```bash
python -m venv venv
source venv/bin/activate
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install --upgrade pip setuptools wheel
```

`ANDROID_API_LEVEL` важливий для пакетів на базі Rust / maturin, таких як `jiter`.

### 4. Встанови перевірений пакет Termux

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

Якщо потрібен лише мінімальний ядровий агент, це також працює:

```bash
python -m pip install -e '.' -c constraints-termux.txt
```

### 5. Додай `hermes` у PATH Termux

```bash
ln -sf "$PWD/venv/bin/hermes" "$PREFIX/bin/hermes"
```

`$PREFIX/bin` вже у PATH у Termux, тому це робить команду `hermes` постійною між новими оболонками без повторної активації venv щоразу.

### 6. Перевір інсталяцію

```bash
hermes version
hermes doctor
```

### 7. Запусти Hermes

```bash
hermes
```

---

## Рекомендоване подальше налаштування

### Налаштуй модель

```bash
hermes model
```

Або встанови ключі безпосередньо у `~/.hermes/.env`.

### Пізніше запусти повний інтерактивний майстер налаштувань

```bash
hermes setup
```

### Встанови необов’язкові залежності Node вручну

У перевіреному шляху Termux навмисно пропускає завантаження Node/браузера. Якщо хочеш поекспериментувати з інструментами браузера пізніше:

```bash
pkg install nodejs-lts
npm install
```

Інструмент браузера автоматично включає каталоги Termux (`/data/data/com.termux/files/usr/bin`) у пошук PATH, тому `agent-browser` і `npx` знаходяться без додаткових налаштувань PATH.

Ставте інструменти браузера / WhatsApp на Android у статус експериментальних, доки не буде інше задокументовано.

---

## Усунення проблем

### `No solution found` під час встановлення `.[all]`

Використай перевірений пакет Termux замість цього:

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

Блокуючим є наразі додаток `voice`:
- `voice` тягне `faster‑whisper`
- `faster‑whisper` залежить від `ctranslate2`
- `ctranslate2` не публікує Android‑колеса

### `uv pip install` падає на Android

Використай шлях Termux зі стандартним venv + `pip`:

```bash
python -m venv venv
source venv/bin/activate
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

### `jiter` / `maturin` скаржаться на `ANDROID_API_LEVEL`

Встанови рівень API явно перед інсталяцією:

```bash
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

### `hermes doctor` повідомляє про відсутність ripgrep або Node

Встанови їх за допомогою пакетів Termux:

```bash
pkg install ripgrep nodejs
```

### Помилки збірки під час встановлення Python‑пакетів

Переконайся, що інструментарій збірки встановлений:

```bash
pkg install clang rust make pkg-config libffi openssl
```

Потім спробуй ще раз:

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

---

## Відомі обмеження на телефонах

- бекенд Docker недоступний
- локальна голосова транскрипція через `faster‑whisper` недоступна у перевіреному шляху
- налаштування автоматизації браузера навмисно пропускається інсталятором
- деякі необов’язкові додатки можуть працювати, але лише `.[termux]` і `.[termux-all]` наразі задокументовані як перевірені Android‑пакети

Якщо ти зіткнувся з новою Android‑специфічною проблемою, будь ласка, відкрий issue на GitHub з:
- твоєю версією Android
- `termux-info`
- `python --version`
- `hermes doctor`
- точною командою інсталяції та повним виводом помилки