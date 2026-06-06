---
title: "Songsee — аудіо спектрограми/особливості (mel, chroma, MFCC) через CLI"
sidebar_label: "Songsee"
description: "Аудіо спектрограми/особливості (mel, chroma, MFCC) через CLI"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Songsee

Аудіо спектрограми/особливості (mel, chroma, MFCC) через CLI.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/songsee` |
| Version | `1.0.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Audio`, `Visualization`, `Spectrogram`, `Music`, `Analysis` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# songsee

Генерує спектрограми та багатопанельні візуалізації аудіо‑особливостей з аудіофайлів.

## Передумови

Потрібен [Go](https://go.dev/doc/install):
```bash
go install github.com/steipete/songsee/cmd/songsee@latest
```

Необов’язково: `ffmpeg` для форматів, відмінних від WAV/MP3.

## Швидкий старт

```bash
# Basic spectrogram
songsee track.mp3

# Save to specific file
songsee track.mp3 -o spectrogram.png

# Multi-panel visualization grid
songsee track.mp3 --viz spectrogram,mel,chroma,hpss,selfsim,loudness,tempogram,mfcc,flux

# Time slice (start at 12.5s, 8s duration)
songsee track.mp3 --start 12.5 --duration 8 -o slice.jpg

# From stdin
cat track.mp3 | songsee - --format png -o out.png
```

## Типи візуалізацій

Використовуй `--viz` зі значеннями, розділеними комами:

| Тип | Опис |
|------|-------------|
| `spectrogram` | Стандартна частотна спектрограма |
| `mel` | Спектрограма з мел‑масштабуванням |
| `chroma` | Розподіл класів висот |
| `hpss` | Гармонічне/перкусивне розділення |
| `selfsim` | Матриця самоподібності |
| `loudness` | Гучність у часі |
| `tempogram` | Оцінка темпу |
| `mfcc` | Мел‑частотні кепстральні коефіцієнти |
| `flux` | Спектральний флюкс (детекція онсетів) |

Кілька типів `--viz` відображаються у вигляді сітки в одному зображенні.

## Поширені прапорці

| Прапорець | Опис |
|------|-------------|
| `--viz` | Типи візуалізацій (розділені комами) |
| `--style` | Колірна палітра: `classic`, `magma`, `inferno`, `viridis`, `gray` |
| `--width` / `--height` | Розміри вихідного зображення |
| `--window` / `--hop` | Вікно FFT та крок |
| `--min-freq` / `--max-freq` | Фільтр діапазону частот |
| `--start` / `--duration` | Сегмент часу аудіо |
| `--format` | Формат виводу: `jpg` або `png` |
| `-o` | Шлях до вихідного файлу |

## Примітки

- WAV і MP3 декодуються нативно; інші формати потребують `ffmpeg`
- Вихідні зображення можна проаналізувати за допомогою `vision_analyze` для автоматизованого аудіо‑аналізу
- Корисно для порівняння аудіо‑виходів, налагодження синтезу або документування аудіо‑обробних конвеєрів