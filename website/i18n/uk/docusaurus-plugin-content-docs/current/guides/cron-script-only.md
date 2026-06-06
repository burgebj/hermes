---
sidebar_position: 13
title: "Cron‑завдання лише скрипти (без LLM)"
description: "Класичні watchdog cron‑завдання, які повністю обходять LLM — скрипт запускається за розкладом, і його stdout доставляється на твою платформу обміну повідомленнями. Сповіщення про пам'ять, сповіщення про диск, CI‑пінги, періодичні перевірки стану."
---

# Тільки скриптові Cron‑завдання

Інколи ти вже точно знаєш, яке повідомлення потрібно надіслати. Не потрібен агент, щоб розмірковувати — потрібен лише скрипт, який запускається за таймером, і його вивід (якщо є) потрапляє в Telegram / Discord / Slack / Signal.

Hermes називає це **режимом без агента**. Це система cron без LLM.

<!-- ascii-guard-ignore -->
```
   ┌──────────────────┐          ┌──────────────────┐
   │ scheduler tick   │  every   │ run script       │
   │ (every N minutes)│ ──────▶ │ (bash or python) │
   └──────────────────┘          └──────────────────┘
                                          │
                                          │ stdout
                                          ▼
                                 ┌──────────────────┐
                                 │ delivery router  │
                                 │ (telegram/disc…) │
                                 └──────────────────┘
```
<!-- ascii-guard-ignore-end -->

- **Без виклику LLM.** Нуль токенів, нуль циклу агента, нуль витрат на модель.
- **Скрипт — це завдання.** Скрипт вирішує, чи слати сповіщення. Якщо виводить щось → повідомлення надсилається. Якщо нічого не виводить → тихий тик.
- **Bash або Python.** Файли `.sh` / `.bash` виконуються під `/bin/bash`; будь‑яке інше розширення — під поточним інтерпретатором Python. Приймаються всі файли в `~/.hermes/scripts/`.
- **Той самий планувальник.** Живе в `cronjob` разом із LLM‑завданнями — паузи, відновлення, перелік, логи та цільове доставлення працюють однаково.

## Коли це використовувати

Використовуй режим без агента для:

- **Контролерів пам’яті / диска / GPU.** Запускаються кожні 5 хвилин, сповіщають лише коли поріг перевищено.
- **CI‑хукiв.** Завершений деплой → постити SHA коміту. Помилка збірки → надіслати останні 100 рядків логу.
- **Періодичних метрик.** “Щоденний дохід Stripe о 9:00” як простий API‑виклик + pretty‑print.
- **Зовнішніх поллерів подій.** Перевіряти API, сповіщати про зміну стану.
- **Хартбітів.** Пінгувати дашборд кожні N хвилин, щоб довести, що хост живий.

Використовуй звичайне (LLM‑кероване) cron‑завдання, коли агент має **вирішити**, що сказати — підсумувати довгий документ, вибрати цікаві елементи з потоку, підготувати дружнє повідомлення. Шлях без агента підходить, коли stdout скрипту вже Є повідомленням.

## Створити таке завдання з чату

Справжня перевага режиму без агента — агент сам може налаштувати watchdog для тебе — без редактора, без оболонки, без запам’ятовування CLI‑прапорців. Ти описуєш, що потрібно, Hermes пише скрипт, планує його і повідомляє, коли він спрацює.

### Приклад транскрипту

> **Ти:** ping me on telegram if RAM is over 85% every 5 minutes
> **Hermes:** *(writes `~/.hermes/scripts/memory-watchdog.sh`, then calls `cronjob(...)` with `no_agent=true`)*
> Налаштовано. Запускається кожні 5 хв, сповіщає Telegram лише коли RAM > 85 %. Скрипт: `memory-watchdog.sh`. ID завдання: `abc123`.

За лаштунками агент робить два виклики інструментів:

```python
# 1. Write the check script
write_file(
    path="~/.hermes/scripts/memory-watchdog.sh",
    content='''#!/usr/bin/env bash
ram_pct=$(free | awk '/^Mem:/ {printf "%d", $3 * 100 / $2}')
if [ "$ram_pct" -ge 85 ]; then
  echo "RAM ${ram_pct}% on $(hostname)"
fi
# Empty stdout = silent tick; no message sent.
''',
)

# 2. Schedule it — no_agent=True skips the LLM on every tick
cronjob(
    action="create",
    schedule="every 5m",
    script="memory-watchdog.sh",
    no_agent=True,
    deliver="telegram",
    name="memory-watchdog",
)
```

Від цього моменту кожен тик безкоштовний: планувальник запускає скрипт, передає його stdout у Telegram, якщо він не порожній, і ніколи не торкається моделі.

### Що агент вирішує за тебе

Коли ти формулюєш запит типу “сповістити мене, коли X” або “кожні N хвилин перевіряти Y і повідомляти, якщо Z”, опис інструмента `cronjob` Hermes вказує використовувати `no_agent=True`, якщо вміст повідомлення повністю визначений скриптом. При потребі розумової обробки агент переходить до звичайного LLM‑шляху (*“підсумувати нові проблеми”*, *“вибрати найцікавіші заголовки”*, *“підготувати дружнє нагадування”*).

Тобі не треба явно вказувати `--no-agent`. Просто опиши поведінку.

### Керування watchdog‑ами з чату

Агент може паузити, відновлювати, редагувати та видаляти завдання так само, як їх створює:

> **Ти:** stop the memory watchdog for tonight
> **Hermes:** *(calls `cronjob(action='pause', job_id='abc123')`)*
> Поставлено на паузу. Віднови командою “turn it back on” або через `hermes cron resume abc123`.

> **Ти:** change it to every 15 minutes
> **Hermes:** *(calls `cronjob(action='update', job_id='abc123', schedule='every 15m')`)*

Повний життєвий цикл (create / list / update / pause / resume / run‑now / remove) доступний агенту без потреби вивчати CLI‑команди.

## Створити завдання з CLI

Віддаєш перевагу оболонці? Шлях CLI дає той самий результат трьома командами:

```bash
# 1. Write your script
cat > ~/.hermes/scripts/memory-watchdog.sh <<'EOF'
#!/usr/bin/env bash
# Alert when RAM usage is over 85%. Silent otherwise.
RAM_PCT=$(free | awk '/^Mem:/ {printf "%d", $3 * 100 / $2}')
if [ "$RAM_PCT" -ge 85 ]; then
  echo "⚠ RAM ${RAM_PCT}% on $(hostname)"
fi
# Empty stdout = silent run; no message sent.
EOF
chmod +x ~/.hermes/scripts/memory-watchdog.sh

# 2. Schedule it
hermes cron create "every 5m" \
  --no-agent \
  --script memory-watchdog.sh \
  --deliver telegram \
  --name "memory-watchdog"

# 3. Verify
hermes cron list
hermes cron run <job_id>    # fire it once to test
```

Ось і все. Без підказки, без skill, без моделі.

## Як вивід скрипту співвідноситься з доставкою

| Поведінка скрипту | Результат |
|-------------------|----------|
| Exit 0, non‑empty stdout | stdout доставляється дослівно |
| Exit 0, empty stdout | Тихий тик — без доставки |
| Exit 0, stdout contains `{"wakeAgent": false}` on the last line | Тихий тик (спільні ворота з LLM‑завданнями) |
| Non‑zero exit code | Надсилається сповіщення про помилку (щоб поламаний watchdog не “мовчав”) |
| Script timeout | Надсилається сповіщення про помилку |

Поведінка “тихо, коли порожньо” — ключ до класичного шаблону watchdog: скрипт може працювати щохвилини, а канал бачить повідомлення лише коли дійсно потрібна увага.

## Правила для скриптів

Скрипти мають знаходитися в `~/.hermes/scripts/`. Це перевіряється як під час створення завдання, так і під час виконання — абсолютні шляхи, розширення `~/` та патерни переходу по каталогах (`../`) відхиляються. Той самий каталог спільний із “pre‑check”‑воротами, що використовуються LLM‑завданнями.

Вибір інтерпретатора залежить від розширення файлу:

| Розширення | Інтерпретатор |
|-----------|---------------|
| `.sh`, `.bash` | `/bin/bash` |
| будь‑що інше | `sys.executable` (поточний Python) |

Навмисно НЕ підтримуємо shebang `#!/...` — явне та мале налаштування інтерпретатора зменшує поверхню довіри планувальника.

## Синтаксис розкладу

Те саме, що й у всіх інших cron‑завдань:

```bash
hermes cron create "every 5m"        # interval
hermes cron create "every 2h"
hermes cron create "0 9 * * *"       # standard cron: 9am daily
hermes cron create "30m"             # one-shot: run once in 30 minutes
```

Дивись [cron feature reference](/user-guide/features/cron) для повного синтаксису.

## Цілі доставки

`--deliver` приймає все, що знає шлюз. Декілька поширених форм:

```bash
--deliver telegram                       # platform home channel
--deliver telegram:-1001234567890        # specific chat
--deliver telegram:-1001234567890:17585  # specific Telegram forum topic
--deliver discord:#ops
--deliver slack:#engineering
--deliver signal:+15551234567
--deliver local                          # just save to ~/.hermes/cron/output/
```

Для платформ з бот‑токенами (Telegram, Discord, Slack, Signal, SMS, WhatsApp) під час виконання скрипту не потрібен запущений шлюз — інструмент викликає REST‑endpoint кожної платформи безпосередньо, використовуючи облікові дані, вже збережені в `~/.hermes/.env` / `~/.hermes/config.yaml`.

## Редагування та життєвий цикл

```bash
hermes cron list                                    # see all jobs
hermes cron pause <job_id>                          # stop firing, keep definition
hermes cron resume <job_id>
hermes cron edit <job_id> --schedule "every 10m"    # adjust cadence
hermes cron edit <job_id> --agent                   # flip to LLM mode
hermes cron edit <job_id> --no-agent --script …     # flip back
hermes cron remove <job_id>                         # delete it
```

Все, що працює з LLM‑завданнями (pause, resume, manual trigger, зміна цілі доставки), працює і з завданнями без агента.

## Приклад: сповіщення про заповнення диска

```bash
cat > ~/.hermes/scripts/disk-alert.sh <<'EOF'
#!/usr/bin/env bash
# Alert when / or /home is over 90% full.
THRESHOLD=90
df -h / /home 2>/dev/null | awk -v t="$THRESHOLD" '
  NR > 1 && $5+0 >= t {
    printf "⚠ Disk %s full on %s\n", $5, $6
  }
'
EOF
chmod +x ~/.hermes/scripts/disk-alert.sh

hermes cron create "*/15 * * * *" \
  --no-agent \
  --script disk-alert.sh \
  --deliver telegram \
  --name "disk-alert"
```

Тихо, коли обидві файлові системи нижче 90 %; спрацьовує один рядок на кожну файлову систему, що перевищила поріг.

## Порівняння з іншими підходами

| Підхід | Що виконується | Коли використовувати |
|--------|----------------|-----------------------|
| `cronjob --no-agent` (ця сторінка) | Твій скрипт за розкладом Hermes | Регулярні watchdog‑и / сповіщення / метрики, що не потребують розумової обробки |
| `cronjob` (за замовчуванням, LLM) | Агент з optional pre‑check скриптом | Коли вміст повідомлення вимагає розумової обробки даних |
| OS cron + `curl` до [webhook subscription](/user-guide/messaging/webhooks) | Твій скрипт за розкладом ОС | Коли Hermes може бути недоступний (річ, яку ти моніториш) |

Для критичних watchdog‑ів системного здоров’я, які мають спрацьовувати *навіть коли шлюз недоступний*, використай cron ОС з простим `curl` до Hermes webhook (або будь‑якої зовнішньої точки сповіщення) — такі завдання працюють незалежно від стану Hermes. Планувальник у шлюзі підходить, коли моніториться зовнішня система.

## Пов’язані матеріали

- [Automate Anything with Cron](/guides/automate-with-cron) — LLM‑керовані cron‑шаблони.
- [Scheduled Tasks (Cron) reference](/user-guide/features/cron) — повний синтаксис розкладу, життєвий цикл, маршрутизація доставки.
- [Webhook Subscriptions](/user-guide/messaging/webhooks) — fire‑and‑forget HTTP‑точки входу для зовнішніх планувальників.
- [Gateway Internals](/developer-guide/gateway-internals) — внутрішня логіка delivery‑router.