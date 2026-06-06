---
sidebar_position: 3
title: "Android / Termux"
description: "Запусти Hermes Agent напрямую на Android‑телефоне с Termux"
---

# Hermes на Android с Termux

Это проверенный путь для запуска Hermes Agent напрямую на Android‑телефоне через [Termux](https://termux.dev/).

Он предоставляет работающий локальный CLI на телефоне, а также основные дополнительные возможности, которые сейчас известны как корректно устанавливающиеся на Android.

## Что поддерживается в проверенном пути?

Пакет Termux устанавливает:
- Hermes CLI
- поддержку cron
- поддержку PTY/фонового терминала
- поддержку шлюза Telegram (ручные / best‑effort фоновые запуски)
- поддержку MCP
- поддержку памяти Honcho
- поддержку ACP

Конкретно это соответствует:

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

## Что пока не входит в проверенный путь?

Некоторые функции всё ещё требуют зависимостей в стиле desktop/server, которые не опубликованы для Android, либо ещё не проверены на телефонах:

- `.[all]` не поддерживается на Android сегодня
- дополнительный `voice` блокируется `faster‑whisper → ctranslate2`, а `ctranslate2` не публикует Android‑колёса
- автоматический bootstrap браузера / Playwright пропускается в установщике Termux
- изоляция терминала на основе Docker недоступна внутри Termux
- Android может приостанавливать фоновые задачи Termux, поэтому устойчивость шлюза — best‑effort, а не обычный управляемый сервис

Это не мешает Hermes работать как нативный CLI‑агент для телефона — просто рекомендуемая мобильная установка намеренно уже, чем настольная/серверная.

---

## Вариант 1: Однострочный установщик

Hermes теперь поставляется с путём установки, учитывающим Termux:

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash
```

В Termux установщик автоматически:
- использует `pkg` для системных пакетов
- создаёт venv с помощью `python -m venv`
- сначала пытается установить широкий extra `.[termux-all]`, а при неудаче переходит к меньшему `.[termux]` (затем к базовой установке) — curl‑установщик автоматически следует этому порядку
- создаёт ссылку `hermes` в `$PREFIX/bin`, чтобы она оставалась в PATH Termux
- пропускает непроверенный bootstrap браузера / WhatsApp

Если нужны явные команды или требуется отладить неудачную установку, используй ручной путь ниже.

---

## Вариант 2: Ручная установка (полностью явно)

### 1. Обнови Termux и установи системные пакеты

```bash
pkg update
pkg install -y git python clang rust make pkg-config libffi openssl nodejs ripgrep ffmpeg
```

Зачем эти пакеты?
- `python` — среда выполнения + поддержка venv
- `git` — клонирование/обновление репозитория
- `clang`, `rust`, `make`, `pkg-config`, `libffi`, `openssl` — нужны для сборки некоторых Python‑зависимостей на Android
- `nodejs` — необязательная среда Node для экспериментов за пределами проверенного ядра
- `ripgrep` — быстрый поиск файлов
- `ffmpeg` — конверсия медиа / TTS

### 2. Клонируй Hermes

```bash
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
```

Если уже клонировал без подмодулей:

```bash
git submodule update --init --recursive
```

### 3. Создай виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install --upgrade pip setuptools wheel
```

`ANDROID_API_LEVEL` важен для пакетов на Rust / maturin, таких как `jiter`.

### 4. Установи проверенный пакет Termux

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

Если нужен только минимальный ядровой агент, подойдёт и:

```bash
python -m pip install -e '.' -c constraints-termux.txt
```

### 5. Добавь `hermes` в PATH Termux

```bash
ln -sf "$PWD/venv/bin/hermes" "$PREFIX/bin/hermes"
```

`$PREFIX/bin` уже находится в PATH в Termux, поэтому эта команда делает `hermes` доступным в новых оболочках без повторной активации venv каждый раз.

### 6. Проверь установку

```bash
hermes version
hermes doctor
```

### 7. Запусти Hermes

```bash
hermes
```

---

## Рекомендуемая последующая настройка

### Настройка модели

```bash
hermes model
```

Или укажи ключи напрямую в `~/.hermes/.env`.

### Позже запусти полный интерактивный мастер настройки

```bash
hermes setup
```

### Установи необязательные зависимости Node вручную

Проверенный путь Termux намеренно пропускает bootstrap Node/браузера. Если позже захочешь поэкспериментировать с браузерными инструментами:

```bash
pkg install nodejs-lts
npm install
```

Инструмент браузера автоматически включает каталоги Termux (`/data/data/com.termux/files/usr/bin`) в поиск PATH, поэтому `agent-browser` и `npx` находятся без дополнительной конфигурации PATH.

Относись к инструментам браузера / WhatsApp на Android как к экспериментальным, пока не будет иной документации.

---

## Устранение неполадок

### `No solution found` при установке `.[all]`

Используй проверенный пакет Termux:

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

Блокирующим фактором сейчас является extra `voice`:
- `voice` тянет `faster-whisper`
- `faster-whisper` зависит от `ctranslate2`
- `ctranslate2` не публикует Android‑колёса

### `uv pip install` падает на Android

Воспользуйся путём Termux со стандартным venv + `pip`:

```bash
python -m venv venv
source venv/bin/activate
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

### `jiter` / `maturin` жалуются на `ANDROID_API_LEVEL`

Укажи уровень API явно перед установкой:

```bash
export ANDROID_API_LEVEL="$(getprop ro.build.version.sdk)"
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

### `hermes doctor` сообщает, что ripgrep или Node отсутствуют

Установи их через пакеты Termux:

```bash
pkg install ripgrep nodejs
```

### Ошибки сборки при установке Python‑пакетов

Убедись, что установлен набор инструментов сборки:

```bash
pkg install clang rust make pkg-config libffi openssl
```

Затем повтори попытку:

```bash
python -m pip install -e '.[termux]' -c constraints-termux.txt
```

---

## Известные ограничения на телефонах

- Backend Docker недоступен
- локальная голосовая транскрипция через `faster-whisper` недоступна в проверенном пути
- настройка автоматизации браузера намеренно пропускается установщиком
- некоторые необязательные extras могут работать, но официально задокументированы только `.[termux]` и `.[termux-all]` как проверенные Android‑пакеты

Если столкнёшься с новой Android‑специфичной проблемой, открой issue на GitHub, указав:
- версию Android
- `termux-info`
- `python --version`
- `hermes doctor`
- точную команду установки и полный вывод ошибки