---
title: "Отладчик Node Inspect — Debug Node"
sidebar_label: "Node Inspect Debugger"
description: "Отладка узла"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Node Inspect Debugger

Отладка Node.js через `--inspect` + Chrome DevTools Protocol CLI.

## Skill metadata

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
Ниже представлено полное определение скилла, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда скилл включён.
:::

# Node.js Inspect Debugger

## Overview

Когда `console.log` уже не хватает, управляй встроенным V8‑инспектором Node программно из терминала. Ты получаешь настоящие контрольные точки, пошаговое выполнение (внутрь/через/вне), просмотр стека вызовов, дампы локальных/замкнутых областей и произвольную оценку выражений в приостановленном кадре.

Два инструмента, выбирай один:

- **`node inspect`** — встроенный, без установки, CLI‑REPL. Лучший вариант для быстрого «тыкания».
- **`ndb` / CDP через `chrome-remote-interface`** — скриптуем из Node/Python; предпочтительно, когда нужно автоматизировать множество контрольных точек, собрать состояние между запусками или отлаживать без интерактивного вмешательства из цикла агента.

**Сначала предпочтительно `node inspect`.** Он всегда доступен, а REPL быстрый.

## When to Use

- Тест Node падает, и нужно увидеть промежуточное состояние.
- `ui-tui` падает или работает неправильно, и требуется инспектировать состояние React/Ink до рендера.
- Дочерние процессы `tui_gateway` (`_SlashWorker`, PTY‑мосты) ведут себя странно.
- Нужно исследовать значение в замыкании, которое `console.log` не может достать без правки кода.
- Производительность: подключись к работающему процессу, чтобы захватить CPU‑профиль или снимок кучи.

**Не используй, если:** задача решается `console.log` за минуту. Отладка через контрольные точки тяжелее; применяй её, когда выгода реальна.

## Quick Reference: `node inspect` REPL

Запуск приостановлен на первой строке:

```bash
node inspect path/to/script.js
# or with tsx
node --inspect-brk $(which tsx) path/to/script.ts
```

Подсказка `debug>` принимает:

| Command | Action |
|---|---|
| `c` или `cont` | continue |
| `n` или `next` | step over |
| `s` или `step` | step into |
| `o` или `out` | step out |
| `pause` | pause running code |
| `sb('file.js', 42)` | установить контрольную точку в `file.js` на строке 42 |
| `sb(42)` | установить контрольную точку на строке 42 текущего файла |
| `sb('functionName')` | остановиться при вызове функции |
| `cb('file.js', 42)` | снять контрольную точку |
| `breakpoints` | список всех контрольных точек |
| `bt` | backtrace (стек вызовов) |
| `list(5)` | показать 5 строк исходника вокруг текущей позиции |
| `watch('expr')` | вычислять `expr` при каждой паузе |
| `watchers` | показать наблюдаемые выражения |
| `repl` | перейти в REPL текущей области (Ctrl+C — выйти в `debug>`) |
| `exec expr` | выполнить выражение один раз |
| `restart` | перезапустить скрипт |
| `kill` | завершить скрипт |
| `.exit` | выйти из отладчика |

**В подрежиме `repl`** можно вводить любые JS‑выражения, включая доступ к локальным и замкнутым переменным. `Ctrl+C` возвращает в `debug>`.

## Attaching to a Running Process

Когда процесс уже запущен (например, длительный dev‑сервер или шлюз TUI):

```bash
# 1. Send SIGUSR1 to enable the inspector on an existing process
kill -SIGUSR1 <pid>
# Node prints: Debugger listening on ws://127.0.0.1:9229/<uuid>

# 2. Attach the debugger CLI
node inspect -p <pid>
# or by URL
node inspect ws://127.0.0.1:9229/<uuid>
```

Чтобы запустить процесс с инспектором с самого начала:

```bash
node --inspect script.js           # listen on 127.0.0.1:9229, keep running
node --inspect-brk script.js       # listen AND pause on first line
node --inspect=0.0.0.0:9230 script.js   # custom host:port
```

Для TypeScript через `tsx`:

```bash
node --inspect-brk --import tsx script.ts
# or older tsx
node --inspect-brk -r tsx/cjs script.ts
```

## Programmatic CDP (scripting from terminal)

Когда требуется автоматизация — много контрольных точек, сбор состояния, скрипт‑репродукция — используй `chrome-remote-interface`:

```bash
npm i -g chrome-remote-interface        # or project-local
# Start your target:
node --inspect-brk=9229 target.js &
```

Скрипт‑драйвер (сохрани как `/tmp/cdp-debug.js`):

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

Запусти его:

```bash
node /tmp/cdp-debug.js
```

Примечание для Hermes: `chrome-remote-interface` НЕ указан в `ui-tui/package.json`. Установи его во временную директорию, если не хочешь «запачкать» проект:

```bash
mkdir -p /tmp/cdp-tools && cd /tmp/cdp-tools && npm i chrome-remote-interface
NODE_PATH=/tmp/cdp-tools/node_modules node /tmp/cdp-debug.js
```

## Debugging Hermes ui-tui

TUI построен на Ink + tsx. Два типичных сценария:

### Debugging a single Ink component under dev

В `ui-tui/package.json` есть `npm run dev` (tsx --watch). Добавь `--inspect-brk`, запустив `tsx` напрямую:

```bash
cd /home/bb/hermes-agent/ui-tui
npm run build    # produce dist/ once so transpile isn't needed on first load
node --inspect-brk dist/entry.js
# In another terminal:
node inspect -p <node pid>
```

Затем в `debug>`:

```
sb('dist/app.js', 220)     # or wherever the suspect render is
cont
```

Когда приостановится, `repl` → исследуй `props`, ссылки на состояние, значения обработчиков `useInput` и т.д.

### Debugging a running `hermes --tui`

TUI порождает Node из Python‑CLI. Самый простой путь:

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

Взаимодействие с TUI (ввод в его окне) продолжает выполнение; твой отладчик может приостановить его на любой `sb(...)`.

### Debugging `_SlashWorker` / PTY child processes

Это Python‑процессы, а не Node — используй скилл `python-debugpy`. Только Node‑части (Ink UI, клиент `tui_gateway`, тесты `tsx` в `ui-tui/`) используют данный скилл.

## Running Vitest Tests Under the Debugger

```bash
cd /home/bb/hermes-agent/ui-tui
# Run a single test file paused on entry
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
```

В другом терминале: `node inspect -p <pid>`, затем `sb('src/app/foo.tsx', 42)`, `cont`.

Используй `--no-file-parallelism` (vitest) или `--runInBand` (jest), чтобы был только один воркер — отладка пула крайне неудобна.

## Heap Snapshots & CPU Profiles (Non-interactive)

Из драйвера CDP выше замени Debugger на `HeapProfiler` / `Profiler`:

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

## Common Pitfalls

1. **Неправильные номера строк в TS‑исходнике.** Контрольные точки срабатывают в скомпилированном JS, а не в `.ts`. Либо (a) ставь их в построенный `dist/*.js`, либо (b) включи sourcemaps (`node --enable-source-maps`) и используй `sb('src/app.tsx', N)` — но только с CDP‑клиентами, поддерживающими sourcemaps. CLI `node inspect` их не обрабатывает.

2. **`--inspect` vs `--inspect-brk`.** `--inspect` запускает инспектор, но не приостанавливает процесс; скрипт может пройти первую контрольную точку, если ты подключился слишком поздно. Используй `--inspect-brk`, когда нужно установить точки до начала выполнения кода.

3. **Коллизии портов.** По умолчанию — `9229`. Если несколько процессов Node инспектируются, передай `--inspect=0` (случайный порт) и прочитай реальный URL из `/json/list`:
   ```bash
   curl -s http://127.0.0.1:9229/json/list   # lists all inspectable targets on the host
   ```

4. **Дочерние процессы.** `--inspect` у родителя **не** инспектирует его детей. Запусти `NODE_OPTIONS='--inspect-brk' node parent.js`, чтобы передать опцию каждому дочернему процессу; учти, что им нужны уникальные порты (Node автоматически инкрементирует их, если наследуется `--inspect`).

5. **Фоновое завершение.** Если выйти из `node inspect` через `Ctrl+C`, пока цель приостановлена, она останется в паузе. Сначала выполните `cont` или явно `kill` цель.

6. **Запуск `node inspect` через терминал агента.** Это REPL, дружелюбный к PTY. В Hermes запускай его через `terminal(pty=true)` или `background=true` + `process(action='submit', data='...')`. Неподдерживаемый PTY‑режим работает только для одноразовых команд, но не для интерактивного пошагового выполнения.

7. **Безопасность.** `--inspect=0.0.0.0:9229` открывает возможность удалённого выполнения кода. Всегда привязывайся к `127.0.0.1` (по умолчанию), если только не работаешь в изолированной сети.

## Verification Checklist

После настройки отладочной сессии проверь:

- [ ] `curl -s http://127.0.0.1:9229/json/list` возвращает именно тот процесс, к которому ты подключён.
- [ ] Первая контрольная точка действительно срабатывает (если нет — вероятно, пропущен `--inspect-brk` или подключение произошло после завершения выполнения).
- [ ] Список исходного кода при паузе показывает правильный файл (несоответствие — проблема с sourcemap, см. пункт 1).
- [ ] `exec process.pid` в `repl` возвращает PID того процесса, к которому ты хотел подключиться.

## One-Shot Recipes

**«Почему переменная undefined на строке X?»**
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

**«Каков путь вызова в эту функцию?»**
```
debug> sb('suspectFn')
debug> cont
# paused on entry
debug> bt
```

**«Эта асинхронная цепочка зависает — где?»**
```
# Start with --inspect (no -brk), let it run to the hang, then:
debug> pause
debug> bt
# Now you see the stuck frame
```