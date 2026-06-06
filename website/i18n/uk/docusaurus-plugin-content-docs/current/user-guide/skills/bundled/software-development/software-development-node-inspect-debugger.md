---
title: "Node Inspect Debugger — налагодження Node"
sidebar_label: "Node Inspect Debugger"
description: "Налагодження Node"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Node Inspect Debugger

Debug Node.js via --inspect + Chrome DevTools Protocol CLI.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/software-development/node-inspect-debugger` |
| Version | `1.0.0` |
| Author | Hermes Agent |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `debugging`, `nodejs`, `node-inspect`, `cdp`, `breakpoints`, `ui-tui` |
| Related skills | [`systematic-debugging`](/docs/user-guide/skills/bundled/software-development/software-development-systematic-debugging), [`python-debugpy`](/docs/user-guide/skills/bundled/software-development/software-development-python-debugpy), [`debugging-hermes-tui-commands`](/docs/user-guide/skills/bundled/software-development/software-development-debugging-hermes-tui-commands) |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Node.js Inspect Debugger

## Огляд

Коли `console.log` недостатньо, керуй вбудованим V8‑inspector у Node програмно з терміналу. Ти отримуєш реальні контрольні точки, кроки in/over/out, перегляд стеку викликів, дампи локальної/закритої області та довільну оцінку виразів у паузованому кадрі.

Два інструменти, вибери один:

- **`node inspect`** — вбудований, без встановлення, CLI REPL. Найкращий для швидкого «покапання».
- **`ndb` / CDP via `chrome-remote-interface`** — скриптований з Node/Python; найкращий, коли треба автоматизувати багато контрольних точок, збирати стан між запусками або дебажити не‑інтерактивно з циклу агента.

**Надавай перевагу `node inspect` спочатку.** Він завжди доступний, а REPL швидкий.

## Коли використовувати

- Тест Node падає і треба побачити проміжний стан
- ui‑tui падає або поводиться неправильно і треба проінспектувати стан React/Ink до рендеру
- tui_gateway дочірні процеси (`_SlashWorker`, PTY bridge workers) поводяться дивно
- Потрібно інспектувати значення у замиканні, яке `console.log` не може вивести без патчу
- Perf: підключитися до запущеного процесу, щоб захопити профіль CPU або знімок heap

**Не використовуйте для:** речей, які `console.log` вирішує за хвилину. Дебаг з контрольними точками важчий; використовуйте його, коли вигода реальна.

## Швидка довідка: REPL `node inspect`

Запуск паузи на першому рядку:

```bash
node inspect path/to/script.js
# or with tsx
node --inspect-brk $(which tsx) path/to/script.ts
```

Підказка `debug>` приймає:

| Command | Action |
|---|---|
| `c` or `cont` | continue |
| `n` or `next` | step over |
| `s` or `step` | step into |
| `o` or `out` | step out |
| `pause` | pause running code |
| `sb('file.js', 42)` | set breakpoint at file.js line 42 |
| `sb(42)` | set breakpoint at line 42 of current file |
| `sb('functionName')` | break when function is called |
| `cb('file.js', 42)` | clear breakpoint |
| `breakpoints` | list all breakpoints |
| `bt` | backtrace (call stack) |
| `list(5)` | show 5 lines of source around current position |
| `watch('expr')` | evaluate expr on every pause |
| `watchers` | show watched expressions |
| `repl` | drop into REPL in current scope (Ctrl+C to exit REPL) |
| `exec expr` | evaluate expression once |
| `restart` | restart script |
| `kill` | kill the script |
| `.exit` | quit debugger |

**У підрежимі `repl`:** вводь будь‑який JS‑вираз, включаючи доступ до локальних/закритих змінних. `Ctrl+C` виходить назад до `debug>`.

## Приєднання до запущеного процесу

Коли процес вже працює (наприклад, довгоживучий dev‑сервер або шлюз TUI):

```bash
# 1. Send SIGUSR1 to enable the inspector on an existing process
kill -SIGUSR1 <pid>
# Node prints: Debugger listening on ws://127.0.0.1:9229/<uuid>

# 2. Attach the debugger CLI
node inspect -p <pid>
# or by URL
node inspect ws://127.0.0.1:9229/<uuid>
```

Щоб запустити процес з інспектором від самого початку:

```bash
node --inspect script.js           # listen on 127.0.0.1:9229, keep running
node --inspect-brk script.js       # listen AND pause on first line
node --inspect=0.0.0.0:9230 script.js   # custom host:port
```

Для TypeScript через tsx:

```bash
node --inspect-brk --import tsx script.ts
# or older tsx
node --inspect-brk -r tsx/cjs script.ts
```

## Програмний CDP (скриптування з терміналу)

Коли треба автоматизувати — встановити багато контрольних точок, захопити стан області, написати репродукцію — використай `chrome-remote-interface`:

```bash
npm i -g chrome-remote-interface        # or project-local
# Start your target:
node --inspect-brk=9229 target.js &
```

Скрипт‑драйвер (збережи як `/tmp/cdp-debug.js`):

```javascript
const CDP = require('chrome-remote-interface');

(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;

  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);

    // Walk scopes for locals
    for (const scope of top.scopeChain) {
      if (scope.type === 'local' || scope.type === 'closure') {
        const { result } = await Runtime.getProperties({
          objectId: scope.object.objectId,
          ownProperties: true,
        });
        for (const p of result) {
          console.log(`  ${scope.type}.${p.name} =`, p.value?.value ?? p.value?.description);
        }
      }
    }

    // Evaluate an expression in the paused frame
    const { result } = await Debugger.evaluateOnCallFrame({
      callFrameId: top.callFrameId,
      expression: 'typeof state !== "undefined" ? JSON.stringify(state) : "n/a"',
    });
    console.log('state =', result.value ?? result.description);

    await Debugger.resume();
  });

  await Runtime.enable();
  await Debugger.enable();

  // Set a breakpoint by URL regex + line
  await Debugger.setBreakpointByUrl({
    urlRegex: '.*app\\.tsx$',
    lineNumber: 119,       // 0-indexed
    columnNumber: 0,
  });

  await Runtime.runIfWaitingForDebugger();
})();
```

Запусти його:

```bash
node /tmp/cdp-debug.js
```

Примітка Hermes: `chrome-remote-interface` НЕ входить до `ui-tui/package.json`. Встанови його в тимчасове місце, якщо не хочеш забруднювати проект:

```bash
mkdir -p /tmp/cdp-tools && cd /tmp/cdp-tools && npm i chrome-remote-interface
NODE_PATH=/tmp/cdp-tools/node_modules node /tmp/cdp-debug.js
```

## Дебаг Hermes ui‑tui

TUI побудований на Ink + tsx. Два типові сценарії:

### Дебаг одного Ink‑компоненту під час розробки

У `ui-tui/package.json` є `npm run dev` (tsx --watch). Додай `--inspect-brk`, запустивши tsx безпосередньо:

```bash
cd /home/bb/hermes-agent/ui-tui
npm run build    # produce dist/ once so transpile isn't needed on first load
node --inspect-brk dist/entry.js
# In another terminal:
node inspect -p <node pid>
```

Потім у `debug>`:

```
sb('dist/app.js', 220)     # or wherever the suspect render is
cont
```

Коли пауза, `repl` → інспектуй `props`, стан refs, значення обробників `useInput` тощо.

### Дебаг запущеного `hermes --tui`

TUI спауниє Node з Python‑CLI. Найпростіший шлях:

```bash
# 1. Launch TUI
hermes --tui &
TUI_PID=$(pgrep -f 'ui-tui/dist/entry' | head -1)

# 2. Enable inspector on that Node PID
kill -SIGUSR1 "$TUI_PID"

# 3. Find the WS URL
curl -s http://127.0.0.1:9229/json/list | jq -r '.[0].webSocketDebuggerUrl'

# 4. Attach
node inspect ws://127.0.0.1:9229/<uuid>
```

Взаємодія з TUI (введення у його вікні) продовжує виконання; твій дебагер може зупинити його на будь‑якій `sb(...)`.

### Дебаг процесів `_SlashWorker` / PTY

Вони написані на Python, не на Node — використай навичку `python-debugpy` для них. Тільки частини Node (Ink UI, клієнт tui_gateway, тести tsx‑run у `ui-tui/`) використовують цю навичку.

## Запуск тестів Vitest під дебагером

```bash
cd /home/bb/hermes-agent/ui-tui
# Run a single test file paused on entry
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
```

В іншому терміналі: `node inspect -p <pid>`, потім `sb('src/app/foo.tsx', 42)`, `cont`.

Використай `--no-file-parallelism` (vitest) або `--runInBand` (jest), щоб був лише один воркер — дебаг пулу болісний.

## Знімки heap та профілі CPU (не‑інтерактивно)

З CDP‑драйвера вище, заміни Debugger на `HeapProfiler` / `Profiler`:

```javascript
// CPU profile for 5 seconds
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
require('fs').writeFileSync('/tmp/cpu.cpuprofile', JSON.stringify(profile));
// Open /tmp/cpu.cpuprofile in Chrome DevTools → Performance tab
```

```javascript
// Heap snapshot
await client.HeapProfiler.enable();
const chunks = [];
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
require('fs').writeFileSync('/tmp/heap.heapsnapshot', chunks.join(''));
```

## Поширені підводні камені

1. **Неправильні номери рядків у TS‑джерелі.** Точки зупину спрацьовують у згенерованому JS, а не у `.ts`. Або (a) став їх у зібраному `dist/*.js`, або (b) увімкни sourcemaps (`node --enable-source-maps`) і використай `sb('src/app.tsx', N)` — але лише з CDP‑клієнтами, які підтримують sourcemaps. CLI `node inspect` їх не підтримує.

2. **`--inspect` vs `--inspect-brk`.** `--inspect` запускає інспектор, але не паузить; скрипт може пройти твою першу точку зупину, якщо підключитися занадто пізно. Використай `--inspect-brk`, коли треба встановити точки перед будь‑яким кодом.

3. **Колізії портів.** За замовчуванням `9229`. Якщо кілька процесів Node інспектуються, передай `--inspect=0` (випадковий порт) і прочитай реальну URL з `/json/list`:
   ```bash
   curl -s http://127.0.0.1:9229/json/list   # lists all inspectable targets on the host
   ```

4. **Дочірні процеси.** `--inspect` у батька НЕ інспектує його дітей. Використай `NODE_OPTIONS='--inspect-brk' node parent.js`, щоб передати всім дітям; пам’ятай, що кожен потребує унікального порту (Node авто‑інкрементує при успадкуванні `NODE_OPTIONS='--inspect'`).

5. **Фонові вбивства.** Якщо ти `Ctrl+C` вийдеш з `node inspect`, коли ціль паузить, ціль залишиться паузованою. Спочатку `cont`, або явно `kill` ціль.

6. **Запуск `node inspect` через термінал агента.** Це PTY‑дружній REPL. У Hermes запускай його з `terminal(pty=true)` або `background=true` + `process(action='submit', data='...')`. НепТЙ‑режим переднього плану працює лише для одноразових команд, не для інтерактивного крокування.

7. **Безпека.** `--inspect=0.0.0.0:9229` відкриває довільне виконання коду. Завжди прив’язуйся до `127.0.0.1` (за замовчуванням), якщо тільки не працюєш в ізольованій мережі.

## Чек‑лист перевірки

Після налаштування сесії дебагу, перевір:

- [ ] `curl -s http://127.0.0.1:9229/json/list` повертає саме ціль, яку ти очікуєш
- [ ] Перша точка зупину дійсно спрацьовує (якщо ні — ймовірно пропущено `--inspect-brk` або підключено після завершення виконання)
- [ ] Список джерел у паузі показує правильний файл (невідповідність = проблема sourcemap, дивись підводний камінь 1)
- [ ] `exec process.pid` у `repl` повертає PID, до якого ти підключився

## Одноразові рецепти

**«Чому ця змінна undefined у рядку X?»**
```bash
node --inspect-brk script.js &
node inspect -p $!
# debug>
sb('script.js', X)
cont
# paused. Now:
repl
> myVariable
> Object.keys(this)
```

**«Який шлях виклику веде у цю функцію?»**
```
debug> sb('suspectFn')
debug> cont
# paused on entry
debug> bt
```

**«Цей async‑ланцюжок завис — де?»**
```
# Start with --inspect (no -brk), let it run to the hang, then:
debug> pause
debug> bt
# Now you see the stuck frame
```