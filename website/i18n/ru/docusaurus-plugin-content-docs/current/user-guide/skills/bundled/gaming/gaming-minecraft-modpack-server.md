---
title: "Minecraft Modpack Server — Хостить модифицированные серверы Minecraft (CurseForge, Modrinth)"
sidebar_label: "Minecraft Modpack Server"
description: "Размещай модифицированные серверы Minecraft (CurseForge, Modrinth)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Minecraft Modpack Server

Хостинг модифицированных серверов Minecraft (CurseForge, Modrinth).

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/gaming/minecraft-modpack-server` |
| Platforms | linux, macos |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# Настройка сервера Minecraft Modpack

## Когда использовать
- Пользователь хочет развернуть модифицированный сервер Minecraft из zip‑пакета.
- Пользователь нуждается в помощи с конфигурацией сервера NeoForge/Forge.
- Пользователь интересуется настройкой производительности сервера Minecraft или резервным копированием.

## Сбор предпочтений пользователя
Перед началом настройки спроси пользователя о следующем:
- **Название сервера / MOTD** — что должно отображаться в списке серверов?
- **Seed** — конкретный сид или случайный?
- **Сложность** — peaceful / easy / normal / hard?
- **Режим игры** — survival / creative / adventure?
- **Online mode** — true (аутентификация Mojang, легитимные аккаунты) или false (LAN/кряк‑дружелюбный)?
- **Количество игроков** — сколько ожидается игроков? (влияет на настройку ОЗУ и дистанцию прорисовки)
- **Выделение ОЗУ** — или позволить агенту решить исходя из количества модов и доступной памяти?
- **Дистанция прорисовки / симуляции** — или позволить агенту подобрать исходя из количества игроков и железа?
- **PvP** — включено или выключено?
- **Whitelist** — открытый сервер или только по вайтлисту?
- **Резервные копии** — нужны автоматические бэкапы? Как часто?

Если пользователь не имеет предпочтений, используй разумные значения по умолчанию, но всегда уточняй перед генерацией конфигурации.

## Шаги

### 1. Скачать и изучить пакет
```bash
mkdir -p ~/minecraft-server
cd ~/minecraft-server
wget -O serverpack.zip "<URL>"
unzip -o serverpack.zip -d server
ls server/
```
Ищи файлы: `startserver.sh`, установочный jar (neoforge/forge), `user_jvm_args.txt`, папку `mods/`.
Проверь скрипт, чтобы определить тип загрузчика модов, его версию и требуемую версию Java.

### 2. Установить Java
- Minecraft 1.21+ → Java 21: `sudo apt install openjdk-21-jre-headless`
- Minecraft 1.18‑1.20 → Java 17: `sudo apt install openjdk-17-jre-headless`
- Minecraft 1.16 и ниже → Java 8: `sudo apt install openjdk-8-jre-headless`
- Проверка: `java -version`

### 3. Установить загрузчик модов
Большинство пакетов включают скрипт установки. Используй переменную окружения `INSTALL_ONLY`, чтобы установить без запуска:
```bash
cd ~/minecraft-server/server
ATM10_INSTALL_ONLY=true bash startserver.sh
# Or for generic Forge packs:
# java -jar forge-*-installer.jar --installServer
```
Это скачает библиотеки, пропатчит server‑jar и т.д.

### 4. Принять EULA
```bash
echo "eula=true" > ~/minecraft-server/server/eula.txt
```

### 5. Настроить `server.properties`
Ключевые параметры для модифицированных/LAN‑серверов:
```properties
motd=\u00a7b\u00a7lServer Name \u00a7r\u00a78| \u00a7aModpack Name
server-port=25565
online-mode=true          # false for LAN without Mojang auth
enforce-secure-profile=true  # match online-mode
difficulty=hard            # most modpacks balance around hard
allow-flight=true          # REQUIRED for modded (flying mounts/items)
spawn-protection=0         # let everyone build at spawn
max-tick-time=180000       # modded needs longer tick timeout
enable-command-block=true
```

Настройки производительности (масштабировать под железо):
```properties
# 2 players, beefy machine:
view-distance=16
simulation-distance=10

# 4-6 players, moderate machine:
view-distance=10
simulation-distance=6

# 8+ players or weaker hardware:
view-distance=8
simulation-distance=4
```

### 6. Тюнинг JVM‑аргументов (`user_jvm_args.txt`)
Подбирай ОЗУ в зависимости от количества игроков и модов. Ориентир для модифицированных серверов:
- 100‑200 модов: 6‑12 ГБ
- 200‑350+ модов: 12‑24 ГБ
- Оставляй минимум 8 ГБ свободными для ОС и прочих задач

```
-Xms12G
-Xmx24G
-XX:+UseG1GC
-XX:+ParallelRefProcEnabled
-XX:MaxGCPauseMillis=200
-XX:+UnlockExperimentalVMOptions
-XX:+DisableExplicitGC
-XX:+AlwaysPreTouch
-XX:G1NewSizePercent=30
-XX:G1MaxNewSizePercent=40
-XX:G1HeapRegionSize=8M
-XX:G1ReservePercent=20
-XX:G1HeapWastePercent=5
-XX:G1MixedGCCountTarget=4
-XX:InitiatingHeapOccupancyPercent=15
-XX:G1MixedGCLiveThresholdPercent=90
-XX:G1RSetUpdatingPauseTimePercent=5
-XX:SurvivorRatio=32
-XX:+PerfDisableSharedMem
-XX:MaxTenuringThreshold=1
```

### 7. Открыть порт в брандмауэре
```bash
sudo ufw allow 25565/tcp comment "Minecraft Server"
```
Проверь командой: `sudo ufw status | grep 25565`

### 8. Создать скрипт запуска
```bash
cat > ~/start-minecraft.sh << 'EOF'
#!/bin/bash
cd ~/minecraft-server/server
java @user_jvm_args.txt @libraries/net/neoforged/neoforge/<VERSION>/unix_args.txt nogui
EOF
chmod +x ~/start-minecraft.sh
```
Важно: для Forge (не NeoForge) путь к файлу аргументов отличается. Проверь точный путь в `startserver.sh`.

### 9. Настроить автоматическое резервное копирование
Создай скрипт бэкапа:
```bash
cat > ~/minecraft-server/backup.sh << 'SCRIPT'
#!/bin/bash
SERVER_DIR="$HOME/minecraft-server/server"
BACKUP_DIR="$HOME/minecraft-server/backups"
WORLD_DIR="$SERVER_DIR/world"
MAX_BACKUPS=24
mkdir -p "$BACKUP_DIR"
[ ! -d "$WORLD_DIR" ] && echo "[BACKUP] No world folder" && exit 0
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_FILE="$BACKUP_DIR/world_${TIMESTAMP}.tar.gz"
echo "[BACKUP] Starting at $(date)"
tar -czf "$BACKUP_FILE" -C "$SERVER_DIR" world
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[BACKUP] Saved: $BACKUP_FILE ($SIZE)"
BACKUP_COUNT=$(ls -1t "$BACKUP_DIR"/world_*.tar.gz 2>/dev/null | wc -l)
if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    REMOVE=$((BACKUP_COUNT - MAX_BACKUPS))
    ls -1t "$BACKUP_DIR"/world_*.tar.gz | tail -n "$REMOVE" | xargs rm -f
    echo "[BACKUP] Pruned $REMOVE old backup(s)"
fi
echo "[BACKUP] Done at $(date)"
SCRIPT
chmod +x ~/minecraft-server/backup.sh
```

Добавь ежечасный cron:
```bash
(crontab -l 2>/dev/null | grep -v "minecraft/backup.sh"; echo "0 * * * * $HOME/minecraft-server/backup.sh >> $HOME/minecraft-server/backups/backup.log 2>&1") | crontab -
```

## Подводные камни
- **Всегда** ставь `allow-flight=true` для модифицированных серверов — иначе моды с реактивными ранцами/полётом выгонят игроков.
- `max-tick-time=180000` или выше — модифицированные серверы часто имеют длительные тики во время генерации мира.
- Первый запуск **медленный** (несколько минут для больших пакетов) — не паникуй.
- Предупреждения «Can't keep up!» при первом старте нормальны, они исчезают после генерации начальных чанков.
- Если `online-mode=false`, также установи `enforce-secure-profile=false`, иначе клиенты будут отклоняться.
- В `startserver.sh` часто есть цикл авто‑перезапуска — создай чистый скрипт запуска без него.
- Удали папку `world/`, чтобы сгенерировать мир заново с новым сидом.
- Некоторые пакеты используют переменные окружения для управления поведением (например, ATM10: `ATM10_JAVA`, `ATM10_RESTART`, `ATM10_INSTALL_ONLY`).

## Проверка
- `pgrep -fa neoforge` или `pgrep -fa minecraft` — убедиться, что процесс запущен.
- Просмотр логов: `tail -f ~/minecraft-server/server/logs/latest.log`.
- Ищи строку «Done (Xs)!» в логе — сервер готов.
- Тестовое подключение: игрок добавляет IP сервера в раздел Multiplayer.