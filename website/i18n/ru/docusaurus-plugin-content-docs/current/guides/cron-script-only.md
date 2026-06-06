---
sidebar_position: 13
title: "Только скриптовые cron‑задания (без LLM)"
description: "Классические задачи cron‑watchdog, которые полностью обходят LLM — скрипт запускается по расписанию, а его stdout доставляется в твою платформу обмена сообщениями. Оповещения о памяти, оповещения о диске, пинги CI, периодические проверки состояния."
---

# Cron‑задачи только со скриптом

Иногда ты уже точно знаешь, какое сообщение нужно отправить. Агент не нужен — достаточно скрипта, который будет запускаться по расписанию, и его вывод (если он есть) попадёт в Telegram / Discord / Slack / Signal.

Hermes называет это **режим без агента**. Это система cron без LLM.

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

- **Без вызова LLM.** Ноль токенов, ноль циклов агента, ноль расходов модели.
- **Скрипт — это задача.** Скрипт решает, нужно ли оповещение. Выводит сообщение → сообщение отправляется. Не выводит ничего → тихий тик.
- **Bash или Python.** Файлы `.sh` / `.bash` запускаются под `/bin/bash`; любое другое расширение — под текущим интерпретатором Python. Принимаются любые файлы в `~/.hermes/scripts/`.
- **Тот же планировщик.** Находится в `cronjob` рядом с LLM‑задачами — пауза, возобновление, список, логи и выбор цели доставки работают одинаково.

## Когда использовать

Используй режим без агента для:

- **Контроллеров памяти / диска / GPU.** Запускается каждые 5 минут, оповещает только при превышении порога.
- **CI‑хуков.** Завершённый деплой → отправить SHA коммита. Сборка провалилась → отправить последние 100 строк лога.
- **Периодических метрик.** «Ежедневный доход Stripe в 9 утра» как простой API‑запрос + pretty‑print.
- **Внешних опросов событий.** Проверить API, оповестить при изменении состояния.
- **Хартбитов.** Пинговать дашборд каждые N минут, чтобы доказать, что хост жив.

Используй обычную (LLM‑управляемую) cron‑задачу, когда агент должен **решать**, что сказать — резюмировать длинный документ, выбрать интересные пункты из ленты, подготовить дружелюбное сообщение. Путь без агента предназначен для случаев, когда stdout скрипта уже ЯВЛЯЕТСЯ сообщением.

## Создать из чата

Главное преимущество режима без агента — сам агент может настроить watchdog за тебя — без редактора, без оболочки, без запоминания флагов CLI. Ты описываешь, что нужно, Hermes пишет скрипт, планирует его и сообщает, когда он сработает.

### Пример диалога

> **Ты:** ping me on telegram if RAM is over 85% every 5 minutes
> **Hermes:** *(writes `~/.hermes/scripts/memory-watchdog.sh`, then calls `cronjob(...)` with `no_agent=true`)*
> Set up. Runs every 5 min, alerts Telegram only when RAM is over 85 %. Script: `memory-watchdog.sh`. Job ID: `abc123`.

Под капотом агент делает два вызова инструмента:

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

С этого момента каждый тик бесплатен: планировщик запускает скрипт, передаёт его stdout в Telegram, если он не пуст, и никогда не обращается к модели.

### Что агент решает за тебя

Когда ты формулируешь запрос типа «alert me when X» или «every N minutes check Y and tell me if Z», описание инструмента `cronjob` в Hermes указывает использовать `no_agent=True`, если содержание сообщения полностью определяется скриптом. При необходимости рассуждения (*«summarize the new issues»*, *«pick the most interesting headlines»*, *«draft a friendly reminder»*) происходит откат к обычному LLM‑пути.

Тебе не нужно явно указывать `--no-agent`. Просто опиши поведение.

### Управление watchdog‑ами из чата

Агент может ставить на паузу, возобновлять, редактировать и удалять задачи так же, как они создаются:

> **Ты:** stop the memory watchdog for tonight
> **Hermes:** *(calls `cronjob(action='pause', job_id='abc123')`)*
> Paused. Resume with "turn it back on" or via `hermes cron resume abc123`.

> **Ты:** change it to every 15 minutes
> **Hermes:** *(calls `cronjob(action='update', job_id='abc123', schedule='every 15m')`)*

Полный жизненный цикл (create / list / update / pause / resume / run‑now / remove) доступен агенту без необходимости изучать команды CLI.

## Создать из CLI

Предпочитаешь оболочку? Путь CLI даёт тот же результат тремя командами:

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

Вот и всё. Без подсказок, без скилла, без модели.

## Как вывод скрипта сопоставляется с доставкой

| Поведение скрипта | Результат |
|-------------------|-----------|
| Exit 0, non‑empty stdout | stdout доставляется дословно |
| Exit 0, empty stdout | Тихий тик — доставка отсутствует |
| Exit 0, stdout содержит `{"wakeAgent": false}` в последней строке | Тихий тик (общие ворота с LLM‑задачами) |
| Non‑zero exit code | Доставляется ошибка‑оповещение (чтобы сломанный watchdog не молчал) |
| Таймаут скрипта | Доставляется ошибка‑оповещение |

Поведение «тихо, если пусто» — ключ к классическому паттерну watchdog: скрипт может запускаться каждую минуту, а канал видит сообщение только при реальной необходимости.

## Правила для скриптов

Скрипты должны находиться в `~/.hermes/scripts/`. Это проверяется как при создании задачи, так и во время её выполнения — абсолютные пути, `~/`‑расширение и паттерны обхода (`../`) отклоняются. Та же директория используется шлюзом пред‑проверки скриптов для LLM‑задач.

Выбор интерпретатора определяется расширением файла:

| Расширение | Интерпретатор |
|------------|---------------|
| `.sh`, `.bash` | `/bin/bash` |
| всё остальное | `sys.executable` (текущий Python) |

Мы намеренно НЕ учитываем shebang (`#!/...`) — явное и небольшое указание интерпретатора уменьшает поверхность доверия планировщика.

## Синтаксис расписания

То же, что и у всех остальных cron‑задач:

```bash
hermes cron create "every 5m"        # interval
hermes cron create "every 2h"
hermes cron create "0 9 * * *"       # standard cron: 9am daily
hermes cron create "30m"             # one-shot: run once in 30 minutes
```

См. [cron feature reference](/user-guide/features/cron) для полного синтаксиса.

## Цели доставки

`--deliver` принимает всё, что знает шлюз. Некоторые типичные варианты:

```bash
--deliver telegram                       # platform home channel
--deliver telegram:-1001234567890        # specific chat
--deliver telegram:-1001234567890:17585  # specific Telegram forum topic
--deliver discord:#ops
--deliver slack:#engineering
--deliver signal:+15551234567
--deliver local                          # just save to ~/.hermes/cron/output/
```

Во время выполнения скрипта не требуется работающий шлюз для платформ с токеном бота (Telegram, Discord, Slack, Signal, SMS, WhatsApp) — инструмент напрямую вызывает REST‑endpoint каждой платформы, используя учётные данные из `~/.hermes/.env` / `~/.hermes/config.yaml`.

## Редактирование и жизненный цикл

```bash
hermes cron list                                    # see all jobs
hermes cron pause <job_id>                          # stop firing, keep definition
hermes cron resume <job_id>
hermes cron edit <job_id> --schedule "every 10m"    # adjust cadence
hermes cron edit <job_id> --agent                   # flip to LLM mode
hermes cron edit <job_id> --no-agent --script …     # flip back
hermes cron remove <job_id>                         # delete it
```

Всё, что работает с LLM‑задачами (pause, resume, ручной запуск, изменение цели доставки), работает и с задачами без агента.

## Пример: оповещение о заполнении диска

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

Тихо, пока обе файловые системы находятся ниже 90 %; срабатывает ровно одной строкой на каждый превышенный порог, когда одна из файловых систем заполняется.

## Сравнение с другими паттернами

| Подход | Что запускается | Когда использовать |
|--------|----------------|----------------------|
| `cronjob --no-agent` (эта страница) | Твой скрипт по расписанию Hermes | Периодические watchdog‑ы / оповещения / метрики, не требующие рассуждений |
| `cronjob` (по умолчанию, LLM) | Агент с опциональным пред‑проверочным скриптом | Когда содержание сообщения требует рассуждения над данными |
| OS‑cron + `curl` к [webhook subscription](/user-guide/messaging/webhooks) | Твой скрипт по расписанию ОС | Когда Hermes может быть недоступен (то, что ты мониторишь) |

Для критически важных watchdog‑ов системного здоровья, которые должны срабатывать *даже при падении шлюза*, используй OS‑уровневый cron с простым `curl` к подписке Hermes webhook (или любой внешней точке оповещения) — они работают как независимые процессы ОС и не зависят от доступности Hermes. Планировщик внутри шлюза подходит, когда мониторится внешняя система.

## Связанные материалы

- [Automate Anything with Cron](/guides/automate-with-cron) — LLM‑управляемые cron‑паттерны.
- [Scheduled Tasks (Cron) reference](/user-guide/features/cron) — полный синтаксис расписания, жизненный цикл, маршрутизация доставки.
- [Webhook Subscriptions](/user-guide/messaging/webhooks) — fire‑and‑forget HTTP‑точки входа для внешних планировщиков.
- [Gateway Internals](/developer-guide/gateway-internals) — внутренности маршрутизатора доставки.