---
title: "Huggingface Hub — HuggingFace hf CLI: пошук/завантаження/вивантаження моделей, наборів даних"
sidebar_label: "Huggingface Hub"
description: "HuggingFace hf CLI: пошук/завантаження/вивантаження моделей, наборів даних"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Huggingface Hub

HuggingFace hf CLI: search/download/upload models, datasets.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/mlops/huggingface-hub` |
| Version | `1.0.0` |
| Author | Hugging Face |
| License | MIT |
| Platforms | linux, macos, windows |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час активної навички.
:::

# Hugging Face CLI (`hf`) Reference Guide

Команда `hf` — це сучасний інтерфейс командного рядка для взаємодії з Hugging Face Hub, що надає інструменти для керування репозиторіями, моделями, наборами даних та Spaces.

> **IMPORTANT:** Команда `hf` замінює застарілу команду `huggingface-cli`.

## Швидкий старт
*   **Встановлення:** `curl -LsSf https://hf.co/cli/install.sh | bash -s`
*   **Допомога:** Використовуй `hf --help`, щоб переглянути всі доступні функції та реальні приклади.
*   **Автентифікація:** Рекомендовано через змінну середовища `HF_TOKEN` або прапорець `--token`.

---

## Основні команди

### Загальні операції
*   `hf download REPO_ID`: Завантажити файли з Hub.
*   `hf upload REPO_ID`: Завантажити файли/папки (рекомендовано для одноразового коміту).
*   `hf upload-large-folder REPO_ID LOCAL_PATH`: Рекомендовано для відновлюваних завантажень великих директорій.
*   `hf sync`: Синхронізувати файли між локальною директорією та бакетом.
*   `hf env` / `hf version`: Переглянути інформацію про середовище та версію.

### Автентифікація (`hf auth`)
*   `login` / `logout`: Керувати сесіями за допомогою токенів з [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
*   `list` / `switch`: Керувати та перемикатися між кількома збереженими токенами доступу.
*   `whoami`: Визначити поточний обліковий запис.

### Управління репозиторіями (`hf repos`)
*   `create` / `delete`: Створити або назавжди видалити репозиторії.
*   `duplicate`: Клонувати модель, набір даних або Space до нового ID.
*   `move`: Перенести репозиторій між просторами імен.
*   `branch` / `tag`: Керувати Git‑подібними посиланнями.
*   `delete-files`: Видалити конкретні файли за шаблонами.

---

## Спеціалізовані взаємодії з Hub

### Набори даних та моделі
*   **Datasets:** `hf datasets list`, `info` та `parquet` (перелік parquet‑URL).
*   **SQL‑запити:** `hf datasets sql SQL` — виконати сирий SQL через DuckDB над parquet‑URL набору даних.
*   **Models:** `hf models list` та `info`.
*   **Papers:** `hf papers list` — переглянути щоденні статті.

### Обговорення та Pull Requests (`hf discussions`)
*   Керувати життєвим циклом внесків у Hub: `list`, `create`, `info`, `comment`, `close`, `reopen` та `rename`.
*   `diff`: Переглянути зміни у PR.
*   `merge`: Завершити pull request.

### Інфраструктура та обчислення
*   **Endpoints:** Розгортати та керувати Inference Endpoints (`deploy`, `pause`, `resume`, `scale-to-zero`, `catalog`).
*   **Jobs:** Запускати обчислювальні завдання на інфраструктурі HF. Включає `hf jobs uv` для запуску Python‑скриптів з вбудованими залежностями та `stats` для моніторингу ресурсів.
*   **Spaces:** Керувати інтерактивними застосунками. Включає `dev-mode` та `hot-reload` для Python‑файлів без повних перезапусків.

### Зберігання та автоматизація
*   **Buckets:** Повне управління S3‑подібними бакетами (`create`, `cp`, `mv`, `rm`, `sync`).
*   **Cache:** Керувати локальним сховищем за допомогою `list`, `prune` (видалення відокремлених ревізій) та `verify` (перевірка контрольних сум).
*   **Webhooks:** Автоматизувати робочі процеси, керуючи веб‑хуками Hub (`create`, `watch`, `enable`/`disable`).
*   **Collections:** Організовувати елементи Hub у колекції (`add-item`, `update`, `list`).

---

## Розширене використання та поради

### Глобальні прапорці
*   `--format json`: Повертає машинозчитуваний вивід для автоматизації.
*   `-q` / `--quiet`: Обмежує вивід лише ID.

### Розширення та навички
*   **Extensions:** Розширювати функціональність CLI через репозиторії GitHub за допомогою `hf extensions install REPO_ID`.
*   **Skills:** Керувати навичками AI‑асистента за допомогою `hf skills add`.