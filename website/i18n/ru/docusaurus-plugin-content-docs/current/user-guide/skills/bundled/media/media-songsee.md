---
title: "Songsee — аудио спектрограммы/фичи (mel, chroma, MFCC) через CLI"
sidebar_label: "Songsee"
description: "Аудио спектрограммы/признаки (mel, chroma, MFCC) через CLI"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Songsee

Аудио‑спектрограммы/фичи (mel, chroma, MFCC) через CLI.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/media/songsee` |
| Version | `1.0.0` |
| Author | community |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `Audio`, `Visualization`, `Spectrogram`, `Music`, `Analysis` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# songsee

Генерирует спектрограммы и многопанельные визуализации аудио‑фич из аудиофайлов.

## Предварительные требования

Требуется [Go](https://go.dev/doc/install):
```bash
go install github.com/steipete/songsee/cmd/songsee@latest
```

Опционально: `ffmpeg` для форматов, отличных от WAV/MP3.

## Быстрый старт

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

## Типы визуализаций

Используй `--viz` со значениями, разделёнными запятыми:

| Type | Description |
|------|-------------|
| `spectrogram` | Стандартная частотная спектрограмма |
| `mel` | Спектрограмма в мел‑шкале |
| `chroma` | Распределение классов высот |
| `hpss` | Гармоническое/перкуссивное разделение |
| `selfsim` | Матрица самоподобия |
| `loudness` | Громкость во времени |
| `tempogram` | Оценка темпа |
| `mfcc` | Мел‑частотные кепстральные коэффициенты |
| `flux` | Спектральный поток (детекция онсетов) |

Несколько типов `--viz` отображаются в виде сетки на одном изображении.

## Общие флаги

| Flag | Description |
|------|-------------|
| `--viz` | Типы визуализаций (через запятую) |
| `--style` | Цветовая палитра: `classic`, `magma`, `inferno`, `viridis`, `gray` |
| `--width` / `--height` | Размеры выходного изображения |
| `--window` / `--hop` | Окно FFT и шаг |
| `--min-freq` / `--max-freq` | Фильтр диапазона частот |
| `--start` / `--duration` | Временной отрезок аудио |
| `--format` | Формат вывода: `jpg` или `png` |
| `-o` | Путь к файлу вывода |

## Примечания

- WAV и MP3 декодируются нативно; другие форматы требуют `ffmpeg`
- Выходные изображения можно проанализировать с помощью `vision_analyze` для автоматизированного аудио‑анализа
- Полезно для сравнения аудио‑выводов, отладки синтеза или документирования аудио‑обработки pipelines