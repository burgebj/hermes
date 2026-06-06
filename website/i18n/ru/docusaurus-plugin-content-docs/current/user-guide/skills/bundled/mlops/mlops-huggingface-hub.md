---
title: "Huggingface Hub — HuggingFace hf CLI: поиск/загрузка/отправка моделей, наборов данных"
sidebar_label: "Huggingface Hub"
description: "HuggingFace hf CLI: поиск/загрузка/отправка моделей, наборов данных"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Huggingface Hub

HuggingFace hf CLI: поиск/загрузка/выгрузка моделей, наборов данных.

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/mlops/huggingface-hub` |
| Version | `1.0.0` |
| Author | Hugging Face |
| License | MIT |
| Platforms | linux, macos, windows |

## Reference: full SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции при активном навыке.
:::

# Hugging Face CLI (`hf`) Reference Guide

Команда `hf` — современный интерфейс командной строки для взаимодействия с Hugging Face Hub, предоставляющий инструменты для управления репозиториями, моделями, наборами данных и Spaces.

> **IMPORTANT:** Команда `hf` заменяет устаревшую команду `huggingface-cli`.

## Quick Start
*   **Installation:** `curl -LsSf https://hf.co/cli/install.sh | bash -s`
*   **Help:** Используй `hf --help`, чтобы увидеть все доступные функции и практические примеры.
*   **Authentication:** Рекомендуется через переменную окружения `HF_TOKEN` или флаг `--token`.

---

## Core Commands

### General Operations
*   `hf download REPO_ID`: Скачать файлы с Hub.
*   `hf upload REPO_ID`: Выгрузить файлы/папки (рекомендовано для однокоммитных загрузок).
*   `hf upload-large-folder REPO_ID LOCAL_PATH`: Рекомендовано для возобновляемых загрузок больших каталогов.
*   `hf sync`: Синхронизировать файлы между локальной папкой и бакетом.
*   `hf env` / `hf version`: Просмотреть информацию об окружении и версии.

### Authentication (`hf auth`)
*   `login` / `logout`: Управлять сессиями с помощью токенов из [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
*   `list` / `switch`: Управлять и переключаться между несколькими сохранёнными токенами доступа.
*   `whoami`: Определить текущий вошедший аккаунт.

### Repository Management (`hf repos`)
*   `create` / `delete`: Создать или окончательно удалить репозитории.
*   `duplicate`: Клонировать модель, набор данных или Space в новый ID.
*   `move`: Переместить репозиторий между пространствами имён.
*   `branch` / `tag`: Управлять ссылками, аналогичными Git.
*   `delete-files`: Удалить конкретные файлы по шаблону.

---

## Specialized Hub Interactions

### Datasets & Models
*   **Datasets:** `hf datasets list`, `info` и `parquet` (список parquet‑URL).
*   **SQL Queries:** `hf datasets sql SQL` — выполнить произвольный SQL через DuckDB над parquet‑URL набора данных.
*   **Models:** `hf models list` и `info`.
*   **Papers:** `hf papers list` — просмотр ежедневных статей.

### Discussions & Pull Requests (`hf discussions`)
*   Управление жизненным циклом вкладов в Hub: `list`, `create`, `info`, `comment`, `close`, `reopen` и `rename`.
*   `diff`: Просмотр изменений в PR.
*   `merge`: Завершить pull request.

### Infrastructure & Compute
*   **Endpoints:** Развёртывание и управление Inference Endpoints (`deploy`, `pause`, `resume`, `scale-to-zero`, `catalog`).
*   **Jobs:** Запуск вычислительных задач в инфраструктуре HF. Включает `hf jobs uv` для выполнения Python‑скриптов с inline‑зависимостями и `stats` для мониторинга ресурсов.
*   **Spaces:** Управление интерактивными приложениями. Включает `dev-mode` и `hot-reload` для Python‑файлов без полной перезагрузки.

### Storage & Automation
*   **Buckets:** Полное управление бакетами, аналогичными S3 (`create`, `cp`, `mv`, `rm`, `sync`).
*   **Cache:** Управление локальным хранилищем с помощью `list`, `prune` (удаление оторванных ревизий) и `verify` (проверка контрольных сумм).
*   **Webhooks:** Автоматизация рабочих процессов через управление Hub webhooks (`create`, `watch`, `enable`/`disable`).
*   **Collections:** Организация элементов Hub в коллекции (`add-item`, `update`, `list`).

---

## Advanced Usage & Tips

### Global Flags
*   `--format json`: Выводит машинно‑читаемый результат для автоматизации.
*   `-q` / `--quiet`: Ограничивает вывод только ID.

### Extensions & Skills
*   **Extensions:** Расширяй функциональность CLI через репозитории GitHub с помощью `hf extensions install REPO_ID`.
*   **Skills:** Управляй навыками AI‑ассистента с помощью `hf skills add`.