---
title: "Управление Docker"
sidebar_label: "Docker Management"
description: "Управляй контейнерами Docker, образами, томами, сетями и стеками Compose — операции жизненного цикла, отладка, очистка и оптимизация Dockerfile"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Управление Docker

Управляй контейнерами Docker, образами, томами, сетями и стеками Compose — операции жизненного цикла, отладка, очистка и оптимизация Dockerfile.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/devops/docker-management` |
| Path | `optional-skills/devops/docker-management` |
| Version | `1.0.0` |
| Author | sprmn24 |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `docker`, `containers`, `devops`, `infrastructure`, `compose`, `images`, `volumes`, `networks`, `debugging` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Управление Docker

Управляй контейнерами Docker, образами, томами, сетями и стеками Compose с помощью стандартных команд Docker CLI. Нет дополнительных зависимостей, кроме самого Docker.

## Когда использовать

- Запуск, остановка, перезапуск, удаление или инспекция контейнеров
- Сборка, загрузка, выгрузка, тегирование или очистка образов Docker
- Работа с Docker Compose (мультисервисные стеки)
- Управление томами или сетями
- Отладка падающего контейнера или анализ логов
- Проверка использования диска Docker и освобождение места
- Просмотр или оптимизация Dockerfile

## Предварительные требования

- Установлен и запущен Docker Engine
- Пользователь добавлен в группу `docker` (или используй `sudo`)
- Docker Compose v2 (включён в современные установки Docker)

Быстрая проверка:

```bash
docker --version && docker compose version
```

## Быстрая справка

| Задача | Команда |
|------|---------|
| Запустить контейнер (в фоне) | `docker run -d --name NAME IMAGE` |
| Остановить + удалить | `docker stop NAME && docker rm NAME` |
| Просмотр логов (следить) | `docker logs --tail 50 -f NAME` |
| Открыть shell в контейнере | `docker exec -it NAME /bin/sh` |
| Список всех контейнеров | `docker ps -a` |
| Сборка образа | `docker build -t TAG .` |
| Поднять Compose | `docker compose up -d` |
| Остановить Compose | `docker compose down` |
| Использование диска | `docker system df` |
| Очистка висячих образов | `docker image prune && docker container prune` |

## Процедура

### 1. Определить область

Определи, к какой области относится запрос:

- **Жизненный цикл контейнера** → run, stop, start, restart, rm, pause/unpause
- **Взаимодействие с контейнером** → exec, cp, logs, inspect, stats
- **Управление образами** → build, pull, push, tag, rmi, save/load
- **Docker Compose** → up, down, ps, logs, exec, build, config
- **Тома и сети** → create, inspect, rm, prune, connect
- **Отладка** → анализ логов, коды выхода, проблемы с ресурсами

### 2. Операции с контейнерами

**Запуск нового контейнера:**

```bash
# Detached service with port mapping
docker run -d --name web -p 8080:80 nginx

# With environment variables
docker run -d -e POSTGRES_PASSWORD=secret -e POSTGRES_DB=mydb --name db postgres:16

# With persistent data (named volume)
docker run -d -v pgdata:/var/lib/postgresql/data --name db postgres:16

# For development (bind mount source code)
docker run -d -v $(pwd)/src:/app/src -p 3000:3000 --name dev my-app

# Interactive debugging (auto-remove on exit)
docker run -it --rm ubuntu:22.04 /bin/bash

# With resource limits and restart policy
docker run -d --memory=512m --cpus=1.5 --restart=unless-stopped --name app my-app
```

Ключевые флаги: `-d` (detached), `-it` (interactive + tty), `--rm` автоудаление, `-p` порт (host:container), `-e` переменная окружения, `-v` том, `--name` имя, `--restart` политика перезапуска.

**Управление работающими контейнерами:**

```bash
docker ps                        # running containers
docker ps -a                     # all (including stopped)
docker stop NAME                 # graceful stop
docker start NAME                # start stopped container
docker restart NAME              # stop + start
docker rm NAME                   # remove stopped container
docker rm -f NAME                # force remove running container
docker container prune           # remove ALL stopped containers
```

**Взаимодействие с контейнерами:**

```bash
docker exec -it NAME /bin/sh          # shell access (use /bin/bash if available)
docker exec NAME env                   # view environment variables
docker exec -u root NAME apt update    # run as specific user
docker logs --tail 100 -f NAME         # follow last 100 lines
docker logs --since 2h NAME            # logs from last 2 hours
docker cp NAME:/path/file ./local      # copy file from container
docker cp ./file NAME:/path/           # copy file to container
docker inspect NAME                    # full container details (JSON)
docker stats --no-stream               # resource usage snapshot
docker top NAME                        # running processes
```

### 3. Управление образами

```bash
# Build
docker build -t my-app:latest .
docker build -t my-app:prod -f Dockerfile.prod .
docker build --no-cache -t my-app .              # clean rebuild
DOCKER_BUILDKIT=1 docker build -t my-app .       # faster with BuildKit

# Pull and push
docker pull node:20-alpine
docker login ghcr.io
docker tag my-app:latest registry/my-app:v1.0
docker push registry/my-app:v1.0

# Inspect
docker images                          # list local images
docker history IMAGE                   # see layers
docker inspect IMAGE                   # full details

# Cleanup
docker image prune                     # remove dangling (untagged) images
docker image prune -a                  # remove ALL unused images (careful!)
docker image prune -a --filter "until=168h"   # unused images older than 7 days
```

### 4. Docker Compose

```bash
# Start/stop
docker compose up -d                   # start all services detached
docker compose up -d --build           # rebuild images before starting
docker compose down                    # stop and remove containers
docker compose down -v                 # also remove volumes (DESTROYS DATA)

# Monitoring
docker compose ps                      # list services
docker compose logs -f api             # follow logs for specific service
docker compose logs --tail 50          # last 50 lines all services

# Interaction
docker compose exec api /bin/sh        # shell into running service
docker compose run --rm api npm test   # one-off command (new container)
docker compose restart api             # restart specific service

# Validation
docker compose config                  # validate and view resolved config
```

**Минимальный пример `compose.yml`:**

```yaml
services:
  api:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=postgres://user:pass@db:5432/mydb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

### 5. Тома и сети

```bash
# Volumes
docker volume ls                       # list volumes
docker volume create mydata            # create named volume
docker volume inspect mydata           # details (mount point, etc.)
docker volume rm mydata                # remove (fails if in use)
docker volume prune                    # remove unused volumes

# Networks
docker network ls                      # list networks
docker network create mynet            # create bridge network
docker network inspect mynet           # details (connected containers)
docker network connect mynet NAME      # attach container to network
docker network disconnect mynet NAME   # detach container
docker network rm mynet                # remove network
docker network prune                   # remove unused networks
```

### 6. Использование диска и очистка

Всегда начинай с диагностики перед очисткой:

```bash
# Check what's using space
docker system df                       # summary
docker system df -v                    # detailed breakdown

# Targeted cleanup (safe)
docker container prune                 # stopped containers
docker image prune                     # dangling images
docker volume prune                    # unused volumes
docker network prune                   # unused networks

# Aggressive cleanup (confirm with user first!)
docker system prune                    # containers + images + networks
docker system prune -a                 # also unused images
docker system prune -a --volumes       # EVERYTHING — named volumes too
```

**Warning:** Никогда не запускай `docker system prune -a --volumes` без подтверждения пользователя. Это удалит именованные тома с потенциально важными данными.

## Подводные камни

| Проблема | Причина | Решение |
|---------|-------|-----|
| Контейнер сразу завершается | Основной процесс завершён или упал | Проверь `docker logs NAME`, попробуй `docker run -it --entrypoint /bin/sh IMAGE` |
| “port is already allocated” | Другой процесс использует этот порт | `docker ps` или `lsof -i :PORT` — найдите процесс |
| “no space left on device” | Диск Docker заполнен | `docker system df`, затем целенаправленная очистка |
| Не удаётся подключиться к контейнеру | Приложение привязано к 127.0.0.1 внутри контейнера | Приложение должно слушать `0.0.0.0`, проверь маппинг `-p` |
| Отказ доступа к тому | Несоответствие UID/GID хоста и контейнера | Используй `--user $(id -u):$(id -g)` или исправь права |
| Сервисы Compose не видят друг друга | Неправильная сеть или имя сервиса | Сервисы используют имя сервиса как hostname, проверь `docker compose config` |
| Кеш сборки не работает | Неправильный порядок слоёв в Dockerfile | Помести редко меняющиеся слои первыми (зависимости → исходный код) |
| Образ слишком большой | Нет multi-stage сборки, нет `.dockerignore` | Используй multi-stage сборки, добавь `.dockerignore` |

## Проверка

После любой операции Docker проверь результат:

- **Контейнер запущен?** → `docker ps` (статус «Up»)
- **Логи чисты?** → `docker logs --tail 20 NAME` (нет ошибок)
- **Порт доступен?** → `curl -s http://localhost:PORT` или `docker port NAME`
- **Образ собран?** → `docker images | grep TAG`
- **Стек Compose здоров?** → `docker compose ps` (все сервисы «running» или «healthy»)
- **Диск освобождён?** → `docker system df` (сравни до/после)

## Советы по оптимизации Dockerfile

При просмотре или создании Dockerfile предлагай следующие улучшения:

1. **Multi-stage сборки** — отдели среду сборки от среды выполнения, чтобы уменьшить размер финального образа
2. **Порядок слоёв** — помещай зависимости перед исходным кодом, чтобы изменения не инвалидировали кешированные слои
3. **Объединяй RUN‑команды** — меньше слоёв, меньше образ
4. **Используй `.dockerignore`** — исключи `node_modules`, `.git`, `__pycache__` и т.п.
5. **Фиксируй версии базовых образов** — `node:20-alpine`, а не `node:latest`
6. **Запускай от не‑root** — добавь инструкцию `USER` для безопасности
7. **Выбирай slim/alpine‑базы** — `python:3.12-slim`, а не `python:3.12`