---
title: "Minecraft Modpack Server — Хостити модифіковані сервери Minecraft (CurseForge, Modrinth)"
sidebar_label: "Minecraft Modpack Server"
description: "Хостити модифіковані сервери Minecraft (CurseForge, Modrinth)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Minecraft Modpack Server

Host modded Minecraft servers (CurseForge, Modrinth).

## Skill metadata

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/gaming/minecraft-modpack-server` |
| Platforms | linux, macos |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Налаштування Minecraft Modpack Server

## Коли використовувати
- Користувач хоче налаштувати модифікований сервер Minecraft з zip‑пакунка серверу
- Користувач потребує допомоги з конфігурацією серверу NeoForge/Forge
- Користувач запитує про оптимізацію продуктивності або резервне копіювання серверу Minecraft

## Спочатку зберіть уподобання користувача
Перш ніж починати налаштування, запитай у користувача:
- **Назва сервера / MOTD** — що має відображатися у списку серверів?
- **Seed** — конкретний seed чи випадковий?
- **Difficulty** — peaceful / easy / normal / hard?
- **Gamemode** — survival / creative / adventure?
- **Online mode** — true (автентифікація Mojang, легітимні акаунти) чи false (LAN/cracked friendly)?
- **Кількість гравців** — скільки гравців очікується? (впливає на налаштування RAM та відстані перегляду)
- **Розподіл RAM** — або дозволити агенту визначити на основі кількості модів та доступної RAM?
- **Відстань перегляду / simulation distance** — або дозволити агенту вибрати на основі кількості гравців та обладнання?
- **PvP** — увімкнено чи вимкнено?
- **Whitelist** — відкритий сервер чи лише whitelist?
- **Резервні копії** — потрібні автоматичні резервні копії? Як часто?

Використовуй розумні значення за замовчуванням, якщо користувач не має уподобань, але завжди запитуй перед генерацією конфігурації.

## Кроки

### 1. Завантажити та проаналізувати пакунок
```bash
mkdir -p ~/minecraft-server
cd ~/minecraft-server
wget -O serverpack.zip "<URL>"
unzip -o serverpack.zip -d server
ls server/
```
Шукай: `startserver.sh`, installer jar (neoforge/forge), `user_jvm_args.txt`, папку `mods/`.
Перевір скрипт, щоб визначити тип завантажувача модів, версію та потрібну версію Java.

### 2. Встановити Java
- Minecraft 1.21+ → Java 21: `sudo apt install openjdk-21-jre-headless`
- Minecraft 1.18‑1.20 → Java 17: `sudo apt install openjdk-17-jre-headless`
- Minecraft 1.16 і нижче → Java 8: `sudo apt install openjdk-8-jre-headless`
- Перевірка: `java -version`

### 3. Встановити завантажувач модів
Більшість серверних пакунків містять скрипт інсталяції. Використай змінну середовища `INSTALL_ONLY`, щоб встановити без запуску:
```bash
cd ~/minecraft-server/server
ATM10_INSTALL_ONLY=true bash startserver.sh
# Or for generic Forge packs:
# java -jar forge-*-installer.jar --installServer
```
Це завантажує бібліотеки, патчить jar серверу тощо.

### 4. Прийняти EULA
```bash
echo "eula=true" > ~/minecraft-server/server/eula.txt
```

### 5. Налаштувати `server.properties`
Ключові налаштування для модифікованих/LAN серверів:
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

Налаштування продуктивності (масштабування під обладнання):
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

### 6. Тюнінг JVM‑аргументів (`user_jvm_args.txt`)
Масштабуй RAM відповідно до кількості гравців та модів. Орієнтовно для модифікованих серверів:
- 100‑200 модів: 6‑12 GB
- 200‑350+ модів: 12‑24 GB
- Залишай принаймні 8 GB вільними для ОС та інших задач

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

### 7. Відкрити порт у брандмауері
```bash
sudo ufw allow 25565/tcp comment "Minecraft Server"
```
Перевір за допомогою: `sudo ufw status | grep 25565`

### 8. Створити скрипт запуску
```bash
cat > ~/start-minecraft.sh << 'EOF'
#!/bin/bash
cd ~/minecraft-server/server
java @user_jvm_args.txt @libraries/net/neoforged/neoforge/<VERSION>/unix_args.txt nogui
EOF
chmod +x ~/start-minecraft.sh
```
Примітка: для Forge (не NeoForge) шлях до файлу аргументів інший. Перевір `startserver.sh` для точного шляху.

### 9. Налаштувати автоматичне резервне копіювання
Створи скрипт резервного копіювання:
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

Додай щогодинний cron:
```bash
(crontab -l 2>/dev/null | grep -v "minecraft/backup.sh"; echo "0 * * * * $HOME/minecraft-server/backup.sh >> $HOME/minecraft-server/backups/backup.log 2>&1") | crontab -
```

## Підводні камені
- ЗАВЖДИ встановлюй `allow-flight=true` для модифікованих серверів — моди з джетпаками/політами інакше кикають гравців
- `max-tick-time=180000` або вище — модифіковані сервери часто мають довгі тики під час генерації світу
- Перший запуск ПОВІЛЬНИЙ (кілька хвилин для великих пакунків) — не панікуй
- Попередження «Can't keep up!» під час першого запуску — це нормально, стабілізується після генерації початкових чанків
- Якщо `online-mode=false`, також встанови `enforce-secure-profile=false`, інакше клієнти будуть відхилені
- У `startserver.sh` часто є цикл автоперезапуску — створити чистий скрипт запуску без нього
- Видали папку `world/`, щоб згенерувати новий світ з новим seed
- Деякі пакунки мають змінні середовища для керування поведінкою (наприклад, ATM10 використовує `ATM10_JAVA`, `ATM10_RESTART`, `ATM10_INSTALL_ONLY`)

## Перевірка
- `pgrep -fa neoforge` або `pgrep -fa minecraft` для перевірки, чи працює
- Переглянь логи: `tail -f ~/minecraft-server/server/logs/latest.log`
- Шукай «Done (Xs)!» у логу — сервер готовий
- Перевір підключення: гравець додає IP сервера у Multiplayer