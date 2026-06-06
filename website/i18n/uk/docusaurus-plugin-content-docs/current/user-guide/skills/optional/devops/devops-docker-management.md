---
title: "Управління Docker"
sidebar_label: "Docker Management"
description: "Керування контейнерами Docker, образами, томами, мережами та стеком Compose — операції життєвого циклу, налагодження, очищення та оптимізація Dockerfile"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Управління Docker

Керуйте контейнерами Docker, образами, томами, мережами та стеком Compose — операції життєвого циклу, налагодження, очищення та оптимізація Dockerfile.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/devops/docker-management` |
| Path | `optional-skills/devops/docker-management` |
| Version | `1.0.0` |
| Author | sprmn24 |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `docker`, `containers`, `devops`, `infrastructure`, `compose`, `images`, `volumes`, `networks`, `debugging` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Управління Docker

Керуйте контейнерами Docker, образами, томами, мережами та стеком Compose за допомогою стандартних команд Docker CLI. Додаткових залежностей, окрім самого Docker, не потрібно.

## Коли використовувати

- Запуск, зупинка, перезапуск, видалення або інспекція контейнерів
- Побудова, завантаження, відправка, тегування або очищення образів Docker
- Робота з Docker Compose (стекі з кількома сервісами)
- Керування томами або мережами
- Налагодження збоїв контейнера або аналіз журналів
- Перевірка використання диска Docker або звільнення місця
- Перегляд або оптимізація Dockerfile

## Передумови

- Docker Engine встановлений і працює
- Користувач доданий до групи `docker` (або використовуйте `sudo`)
- Docker Compose v2 (включений у сучасні установки Docker)

Швидка перевірка:

```bash
docker --version && docker compose version
```

## Швидка довідка

| Task | Command |
|------|---------|
| Запуск контейнера (у фоні) | `docker run -d --name NAME IMAGE` |
| Зупинити + видалити | `docker stop NAME && docker rm NAME` |
| Переглянути журнали (follow) | `docker logs --tail 50 -f NAME` |
| Отримати оболонку в контейнері | `docker exec -it NAME /bin/sh` |
| Список усіх контейнерів | `docker ps -a` |
| Побудувати образ | `docker build -t TAG .` |
| Compose up | `docker compose up -d` |
| Compose down | `docker compose down` |
| Використання диска | `docker system df` |
| Очищення «завислих» образів | `docker image prune && docker container prune` |

## Процедура

### 1. Визначити домен

З’ясуйте, до якої області належить запит:

- **Життєвий цикл контейнера** → run, stop, start, restart, rm, pause/unpause
- **Взаємодія з контейнером** → exec, cp, logs, inspect, stats
- **Керування образами** → build, pull, push, tag, rmi, save/load
- **Docker Compose** → up, down, ps, logs, exec, build, config
- **Томи та мережі** → create, inspect, rm, prune, connect
- **Труднощі** → аналіз журналів, коди виходу, проблеми ресурсів

### 2. Операції з контейнерами

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

Ключові прапорці: `-d` (detached), `-it` (interactive + tty), `--rm` (auto‑remove), `-p` (port host:container), `-e` (env var), `-v` (volume), `--name` (name), `--restart` (restart policy).

**Керування запущеними контейнерами:**

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

**Взаємодія з контейнерами:**

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

### 3. Керування образами

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

**Мінімальний приклад `compose.yml`:**

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

### 5. Томи та мережі

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

### 6. Використання диска та очищення

Завжди починайте з діагностики перед очищенням:

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

**Попередження:** Не запускайте `docker system prune -a --volumes` без підтвердження користувачем. Це видаляє іменовані томи з потенційно важливими даними.

## Підводні камені

| Проблема | Причина | Вирішення |
|---------|--------|-----------|
| Контейнер завершується одразу | Основний процес завершився або впав | Перевірте `docker logs NAME`, спробуйте `docker run -it --entrypoint /bin/sh IMAGE` |
| “port is already allocated” | Інший процес зайняв порт | `docker ps` або `lsof -i :PORT` для пошуку |
| “no space left on device” | Диск Docker заповнений | `docker system df`, потім цілеспрямований prune |
| Не вдається підключитися до контейнера | Додаток прив’язується до 127.0.0.1 всередині контейнера | Додаток має прив’язуватись до `0.0.0.0`, перевірте параметр `-p` |
| Permission denied on volume | Невідповідність UID/GID між хостом і контейнером | Використайте `--user $(id -u):$(id -g)` або виправте права |
| Сервіси Compose не бачать один одного | Неправильна мережа або назва сервісу | Сервіси використовують назву сервісу як hostname, перевірте `docker compose config` |
| Кеш збірки не працює | Неправильний порядок шарів у Dockerfile | Розміщуйте рідко змінювані шари першими (залежності перед кодом) |
| Образ занадто великий | Відсутність multi‑stage build, відсутність `.dockerignore` | Використовуйте multi‑stage, додайте `.dockerignore` |

## Перевірка

Після будь‑якої операції Docker перевірте результат:

- **Контейнер запущено?** → `docker ps` (статус “Up”)
- **Журнали чисті?** → `docker logs --tail 20 NAME` (без помилок)
- **Порт доступний?** → `curl -s http://localhost:PORT` або `docker port NAME`
- **Образ побудовано?** → `docker images | grep TAG`
- **Стек Compose здоровий?** → `docker compose ps` (усі сервіси “running” або “healthy”)
- **Диск звільнено?** → `docker system df` (порівняйте до/після)

## Поради з оптимізації Dockerfile

При перегляді або створенні Dockerfile пропонуй такі покращення:

1. **Multi‑stage builds** — розділити середовище збірки та виконання, щоб зменшити кінцевий розмір образу
2. **Layer ordering** — розташовувати залежності перед вихідним кодом, щоб зміни не інвалідизували кешовані шари
3. **Combine RUN commands** — менше шарів, менший образ
4. **Use .dockerignore** — виключити `node_modules`, `.git`, `__pycache__` тощо
5. **Pin base image versions** — `node:20-alpine`, а не `node:latest`
6. **Run as non‑root** — додати інструкцію `USER` для підвищення безпеки
7. **Use slim/alpine bases** — `python:3.12-slim`, а не `python:3.12`