---
title: "Touchdesigner Mcp"
sidebar_label: "Touchdesigner Mcp"
description: "Керуй запущеним екземпляром TouchDesigner через twozero MCP — створюй оператори, встановлюй параметри, з’єднуй їх, виконуй Python, створюй реальні візуали в режимі реального часу"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Touchdesigner Mcp

Керуй запущеним екземпляром TouchDesigner через twozero MCP — створюй оператори, встановлюй параметри, з’єднуй їх, виконуй Python, створюй реальні‑часові візуалізації. 36 вбудованих інструментів.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудована (встановлюється за замовчуванням) |
| Шлях | `skills/creative/touchdesigner-mcp` |
| Версія | `1.1.0` |
| Автор | kshitijk4poor |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `TouchDesigner`, `MCP`, `twozero`, `creative-coding`, `real-time-visuals`, `generative-art`, `audio-reactive`, `VJ`, `installation`, `GLSL` |
| Пов’язані навички | [`native-mcp`](/docs/user-guide/skills/bundled/mcp/mcp-native-mcp), [`ascii-video`](/docs/user-guide/skills/bundled/creative/creative-ascii-video), [`manim-video`](/docs/user-guide/skills/bundled/creative/creative-manim-video), `hermes-video` |
:::info
Нижче наведено повне визначення **skill**, яке Hermes завантажує, коли цей **skill** активовано. Це те, що агент бачить як інструкції, коли **skill** активний.
:::

# Інтеграція TouchDesigner (twozero MCP)
## КРИТИЧНІ ПРАВИЛА

1. **НИКОЛИ не вгадуй назви параметрів.** Спочатку виклич `td_get_par_info` для типу оператора. Твої навчальні дані неправильні для TD 2025.32.
2. **Якщо виникає `tdAttributeError`, ЗУПИНИСЬ.** Перед продовженням виклич `td_get_operator_info` на вузлі, що викликав помилку.
3. **НИКОЛИ не жорстко кодуй абсолютні шляхи** у скриптових зворотних викликах. Використовуй `me.parent()` / `scriptOp.parent()`.
4. **Віддавай перевагу нативним інструментам MCP** замість `td_execute_python`. Використовуй `td_create_operator`, `td_set_operator_pars`, `td_get_errors` тощо. Переходь до `td_execute_python` лише для складної багатокрокової логіки.
5. **Викликай `td_get_hints` перед створенням.** Він повертає шаблони, специфічні для типу оператора, з яким ти працюєш.
## Архітектура

```
Hermes Agent -> MCP (Streamable HTTP) -> twozero.tox (port 40404) -> TD Python
```

36 нативних інструментів. Безкоштовний плагін (без оплати/ліцензії — підтверджено у квітні 2026 року).
Контекстно‑обізнаний (знає обраний OP, поточну мережу).
Перевірка стану хаба: `GET http://localhost:40404/mcp` повертає JSON з PID інстанції, назвою проєкту, версією TD.
## Setup (Automated)

Запусти скрипт налаштування, щоб виконати всі дії:

```bash
bash "${HERMES_HOME:-$HOME/.hermes}/skills/creative/touchdesigner-mcp/scripts/setup.sh"
```

Скрипт виконає:
1. Перевірить, чи запущений TD
2. Завантажить `twozero.tox`, якщо його ще немає в кеші
3. Додасть сервер `twozero_td` MCP до конфігурації Hermes (якщо його немає)
4. Перевірить з’єднання MCP на порту `40404`
5. Повідомить, які ручні кроки залишилися (перетягнути .tox у TD, увімкнути перемикач MCP)

### Manual steps (one-time, cannot be automated)

1. **Перетягни `~/Downloads/twozero.tox` у мережевий редактор TD** → натисни **Install**
2. **Увімкни MCP:** натисни іконку twozero → **Settings** → **mcp** → «auto start MCP» → **Yes**
3. **Перезапусти сесію Hermes**, щоб новий сервер MCP підхопився

Після налаштування перевір:
```bash
nc -z 127.0.0.1 40404 && echo "twozero MCP: READY"
```
## Примітки щодо середовища

- **Non-Commercial TD** обмежує роздільну здатність до 1280×1280. Використовуй `outputresolution = 'custom'` і явно задавай ширину/висоту.
- **Кодеки:** `prores` (рекомендовано на macOS) або `mjpa` як запасний (варіант). H.264/H.265/AV1 потребують комерційної ліцензії.
- Завжди викликай `td_get_par_info` перед встановленням параметрів — назви залежать від версії TD (див. CRITICAL RULES #1).
## Робочий процес

### Крок 0: Виявлення (перед створенням будь‑чого)

```
Call td_get_par_info with op_type for each type you plan to use.
Call td_get_hints with the topic you're building (e.g. "glsl", "audio reactive", "feedback").
Call td_get_focus to see where the user is and what's selected.
Call td_get_network to see what already exists.
```

Немає тимчасових вузлів, немає прибирання. Це повністю замінює старий танець виявлення.

### Крок 1: Очищення + Побудова

**ВАЖЛИВО: Розділяй прибирання та створення в ОКРЕМІ виклики MCP.** Знищення та повторне створення вузлів з однаковими іменами в одному скрипті `td_execute_python` викликає помилки «Invalid OP object». Дивись підводні камені #11b.

Використовуй `td_create_operator` для кожного вузла (автоматично розташовує у viewport):

```
td_create_operator(type="noiseTOP", parent="/project1", name="bg", parameters={"resolutionw": 1280, "resolutionh": 720})
td_create_operator(type="levelTOP", parent="/project1", name="brightness")
td_create_operator(type="nullTOP", parent="/project1", name="out")
```

Для масового створення або підключення використай `td_execute_python`:

```python
# td_execute_python script:
root = op('/project1')
nodes = []
for name, optype in [('bg', noiseTOP), ('fx', levelTOP), ('out', nullTOP)]:
    n = root.create(optype, name)
    nodes.append(n.path)
# Wire chain
for i in range(len(nodes)-1):
    op(nodes[i]).outputConnectors[0].connect(op(nodes[i+1]).inputConnectors[0])
result = {'created': nodes}
```

### Крок 2: Встановлення параметрів

Віддавай перевагу вбудованому інструменту (перевіряє параметри, не викличе збій):

```
td_set_operator_pars(path="/project1/bg", parameters={"roughness": 0.6, "monochrome": true})
```

Для виразів або режимів використай `td_execute_python`:

```python
op('/project1/time_driver').par.colorr.expr = "absTime.seconds % 1000.0"
```

### Крок 3: З’єднання

Використовуй `td_execute_python` — нативного інструменту з’єднання не існує:

```python
op('/project1/bg').outputConnectors[0].connect(op('/project1/fx').inputConnectors[0])
```

### Крок 4: Перевірка

```
td_get_errors(path="/project1", recursive=true)
td_get_perf()
td_get_operator_info(path="/project1/out", detail="full")
```

### Крок 5: Відображення / Захоплення

```
td_get_screenshot(path="/project1/out")
```

Або відкрий вікно через скрипт:

```python
win = op('/project1').create(windowCOMP, 'display')
win.par.winop = op('/project1/out').path
win.par.winw = 1280; win.par.winh = 720
win.par.winopen.pulse()
```
## MCP Tool Quick Reference

**Core (use these most):**
| Tool | What |
|------|------|
| `td_execute_python` | Запуск довільного Python у TD. Повний доступ до API. |
| `td_create_operator` | Створення вузла з параметрами + автоматичне розташування |
| `td_set_operator_pars` | Безпечне встановлення параметрів (перевіряє, не викличе краху) |
| `td_get_operator_info` | Перегляд одного OP: з’єднання, параметри, помилки |
| `td_get_operators_info` | Перегляд кількох OP в одному виклику |
| `td_get_network` | Перегляд структури мережі за шляхом |
| `td_get_errors` | Пошук помилок/попереджень рекурсивно |
| `td_get_par_info` | Отримання імен параметрів для типу OP (замінює discovery) |
| `td_get_hints` | Отримання шаблонів/підказок перед створенням |
| `td_get_focus` | Яка мережа відкрита, що вибрано |

**Read/Write:**
| Tool | What |
|------|------|
| `td_read_dat` | Читання текстового вмісту DAT |
| `td_write_dat` | Запис/патч вмісту DAT |
| `td_read_chop` | Читання значень каналів CHOP |
| `td_read_textport` | Читання виводу консолі TD |

**Visual:**
| Tool | What |
|------|------|
| `td_get_screenshot` | Захоплення одного переглядача OP у файл |
| `td_get_screenshots` | Захоплення кількох OP одночасно |
| `td_get_screen_screenshot` | Захоплення реального екрану через TD |
| `td_navigate_to` | Перехід у редакторі мережі до OP |

**Search:**
| Tool | What |
|------|------|
| `td_find_op` | Пошук OP за назвою/типом у всьому проєкті |
| `td_search` | Пошук коду, виразів, рядкових параметрів |

**System:**
| Tool | What |
|------|------|
| `td_get_perf` | Профілювання продуктивності (FPS, повільні OP) |
| `td_list_instances` | Список усіх запущених інстанцій TD |
| `td_get_docs` | Детальна документація з теми TD |
| `td_agents_md` | Читання/запис markdown‑документації per‑COMP |
| `td_reinit_extension` | Перезавантаження розширення після редагування коду |
| `td_clear_textport` | Очищення консолі перед сесією налагодження |

**Input Automation:**
| Tool | What |
|------|------|
| `td_input_execute` | Надсилання миші/клавіатури до TD |
| `td_input_status` | Опитування стану черги вводу |
| `td_input_clear` | Зупинка автоматизації вводу |
| `td_op_screen_rect` | Отримання координат екрану вузла |
| `td_click_screen_point` | Клік по точці у скріншоті |
| `td_screen_point_to_global` | Перетворення пікселя скріншоту у абсолютні координати екрану |

The table above covers the 32 tools used in typical creative workflows. The remaining 4 tools (`td_project_quit`, `td_test_session`, `td_dev_log`, `td_clear_dev_log`) are admin/dev‑mode utilities — see `references/mcp-tools.md` for the full 36‑tool reference with complete parameter schemas.
## Ключові правила реалізації

**GLSL‑час:** Не використовуйте `uTDCurrentTime` у GLSL TOP. Скористайтеся сторінкою **Values**:
```python
# Call td_get_par_info(op_type="glslTOP") first to confirm param names
td_set_operator_pars(path="/project1/shader", parameters={"value0name": "uTime"})
# Then set expression via script:
# op('/project1/shader').par.value0.expr = "absTime.seconds"
# In GLSL: uniform float uTime;
```

Запасний (варіант): константний TOP у форматі `rgba32float` (8‑бітові значення обрізаються до 0‑1, «заморожуючи» шейдер).

**Feedback TOP:** Використовуйте посилання на параметр `top`, а не прямий вхідний дріт. Попередження «Not enough sources» зникає після першого **cook**. Попередження «Cook dependency loop» є очікуваним.

**Роздільна здатність:** Для Non‑Commercial обмеження — 1280×1280. Використовуйте `outputresolution = 'custom'`.

**Великі шейдери:** Запишіть GLSL у `/tmp/file.glsl`, потім завантажте його за допомогою `td_write_dat` або `td_execute_python`.

**Доступ до вершин/точок (TD 2025.32):** `point.P[0]`, `point.P[1]`, `point.P[2]` — НЕ `.x`, `.y`, `.z`.

**Розширення:** Формат `ext0object` — `"op('./datName').module.ClassName(me)"` у режимі **CONSTANT**. Після редагування коду розширення за допомогою `td_write_dat` викличте `td_reinit_extension`.

**Колбеки скриптів:** ЗАВЖДИ використовуйте відносні шляхи через `me.parent()` / `scriptOp.parent()`.

**Очищення вузлів:** Завжди спочатку створюйте `list(root.children)`, а потім ітеруйте + перевіряйте `child.valid`.
## Запис / Експорт відео

```python
# via td_execute_python:
root = op('/project1')
rec = root.create(moviefileoutTOP, 'recorder')
op('/project1/out').outputConnectors[0].connect(rec.inputConnectors[0])
rec.par.type = 'movie'
rec.par.file = '/tmp/output.mov'
rec.par.videocodec = 'prores'  # Apple ProRes — NOT license-restricted on macOS
rec.par.record = True   # start
# rec.par.record = False  # stop (call separately later)
```

H.264/H.265/AV1 потребують комерційної ліцензії. Використовуй `prores` на macOS або `mjpa` як запасний (варіант).
Витяг кадрів: `ffmpeg -i /tmp/output.mov -vframes 120 /tmp/frames/frame_%06d.png`

**TOP.save() марний для анімації** — захоплює одну й ту ж текстуру GPU щоразу. Завжди використовуй MovieFileOut.

### Перед записом: чек‑лист

1. **Перевір FPS > 0** за допомогою `td_get_perf`. Якщо FPS=0, запис буде порожнім. Див. підводні камені #38‑39.
2. **Перевір, що вихід шейдера не чорний** за допомогою `td_get_screenshot`. Чорний вихід = помилка шейдера або відсутній вхід. Див. підводні камені #8, #40.
3. **Якщо записуєш з аудіо:** спочатку подай аудіо, потім затримай запис на 3 кадри. Див. підводні камені #19.
4. **Встанови шлях виводу перед стартом запису** — встановлення обох у одному скрипті може призвести до гонки.
## Audio-Reactive GLSL (Proven Recipe)

### Correct signal chain (tested April 2026)

```
AudioFileIn CHOP (playmode=sequential)
  → AudioSpectrum CHOP (FFT=512, outputmenu=setmanually, outlength=256, timeslice=ON)
  → Math CHOP (gain=10)
  → CHOP to TOP (dataformat=r, layout=rowscropped)
  → GLSL TOP input 1 (spectrum texture, 256x2)

Constant TOP (rgba32float, time) → GLSL TOP input 0
GLSL TOP → Null TOP → MovieFileOut
```

### Critical audio-reactive rules (empirically verified)

1. **TimeSlice must stay ON** for AudioSpectrum. OFF = processes entire audio file → 24000+ samples → CHOP to TOP overflow.
2. **Set Output Length manually** to 256 via `outputmenu='setmanually'` and `outlength=256`. За замовчуванням виводиться 22050 зразків.
3. **DO NOT use Lag CHOP for spectrum smoothing.** Lag CHOP працює в режимі timeslice і розширює 256 зразків до 2400+, усереднюючи всі значення до майже нуля (~1e‑06). Шейдер не отримує придатних даних. Це була головна причина збою синхронізації аудіо під час тестування.
4. **DO NOT use Filter CHOP either** — та сама проблема розширення в режимі timeslice з даними спектру.
5. **Smoothing belongs in the GLSL shader** if needed, via temporal lerp with a feedback texture: `mix(prevValue, newValue, 0.3)`. Це забезпечує синхронізацію кадр‑за‑кадром без затримки в конвеєрі.
6. **CHOP to TOP dataformat = 'r'**, layout = 'rowscropped'. Вихід спектру – 256×2 (стерео). Зчитуй значення при y=0.25 для першого каналу.
7. **Math gain = 10** (не 5). Сирові значення спектру становлять ~0.19 у басовому діапазоні. Підсилення 10 дає придатні ~5.0 для шейдера.
8. **No Resample CHOP needed.** Керуйте розміром виходу безпосередньо параметром `outlength` у AudioSpectrum.

### GLSL spectrum sampling

```glsl
// Input 0 = time (1x1 rgba32float), Input 1 = spectrum (256x2)
float iTime = texture(sTD2DInputs[0], vec2(0.5)).r;

// Sample multiple points per band and average for stability:
// NOTE: y=0.25 for first channel (stereo texture is 256x2, first row center is 0.25)
float bass = (texture(sTD2DInputs[1], vec2(0.02, 0.25)).r +
              texture(sTD2DInputs[1], vec2(0.05, 0.25)).r) / 2.0;
float mid  = (texture(sTD2DInputs[1], vec2(0.2, 0.25)).r +
              texture(sTD2DInputs[1], vec2(0.35, 0.25)).r) / 2.0;
float hi   = (texture(sTD2DInputs[1], vec2(0.6, 0.25)).r +
              texture(sTD2DInputs[1], vec2(0.8, 0.25)).r) / 2.0;
```

See `references/network-patterns.md` for complete build scripts + shader code.
## Короткий довідник операторів

| Сім'я | Колір | Python‑клас / тип MCP | Суфікс |
|--------|-------|--------------------------|--------|
| TOP | Purple | noiseTOP, glslTOP, compositeTOP, levelTop, blurTOP, textTOP, nullTOP | TOP |
| CHOP | Green | audiofileinCHOP, audiospectrumCHOP, mathCHOP, lfoCHOP, constantCHOP | CHOP |
| SOP | Blue | gridSOP, sphereSOP, transformSOP, noiseSOP | SOP |
| DAT | White | textDAT, tableDAT, scriptDAT, webserverDAT | DAT |
| MAT | Yellow | phongMAT, pbrMAT, glslMAT, constMAT | MAT |
| COMP | Gray | geometryCOMP, containerCOMP, cameraCOMP, lightCOMP, windowCOMP | COMP |
## Примітки щодо безпеки

- MCP працює лише на localhost (порт 40404). Без аутентифікації — будь‑який локальний процес може надсилати команди.
- `td_execute_python` має необмежений доступ до середовища TD Python та файлової системи від імені користувача процесу TD.
- `setup.sh` завантажує `twozero.tox` з офіційного URL 404zero.com. Перевірте завантаження, якщо це викликає занепокоєння.
- Skill ніколи не надсилає дані за межі localhost. Уся комунікація MCP є локальною.
## Посилання

| Файл | Що |
|------|------|
| `references/pitfalls.md` | Уроки, отримані з реальних сесій |
| `references/operators.md` | Усі сімейства операторів з параметрами та випадками використання |
| `references/network-patterns.md` | Рецепти: аудіо‑реактивні, генеративні, GLSL, інстансинг |
| `references/mcp-tools.md` | Повні схеми параметрів інструментів twozero MCP |
| `references/python-api.md` | TD Python: `op()`, скрипти, розширення |
| `references/troubleshooting.md` | Діагностика підключень, налагодження |
| `references/glsl.md` | GLSL uniform‑и, вбудовані функції, шаблони шейдерів |
| `references/postfx.md` | Post‑FX: bloom, CRT, хроматична аберація, feedback glow |
| `references/layout-compositor.md` | Шаблони розташування HUD, сітки панелей, BSP‑подібні макети |
| `references/operator-tips.md` | Візуалізація у режимі wireframe, налаштування feedback TOP |
| `references/geometry-comp.md` | Geometry COMP: інстансинг, POP vs SOP, морфінг |
| `references/audio-reactive.md` | Видобуток аудіо‑діапазонів, детекція бітів, слідкування за огинами |
| `references/animation.md` | LFO, таймери, ключові кадри, easing, анімація за виразами |
| `references/midi-osc.md` | MIDI/OSC контролери, TouchOSC, синхронізація кількох машин |
| `references/particles.md` | POP та застарілі particleSOP — емісія, сили, зіткнення |
| `references/projection-mapping.md` | Вивід на кілька вікон, corner pin, mesh warp, edge blending |
| `references/external-data.md` | HTTP, WebSocket, MQTT, Serial, TCP, webserverDAT |
| `references/panel-ui.md` | Користувацькі параметри, panel COMPs, кнопка/слайдер/поле, panelExecuteDAT |
| `references/replicator.md` | replicatorCOMP — клонування за даними, макети, зворотні виклики |
| `references/dat-scripting.md` | Сімейство Execute DAT — chop/dat/parameter/panel/op/executeDAT |
| `references/3d-scene.md` | Освітлювальні установки, тіні, IBL/cubemaps, кілька камер, PBR |
| `scripts/setup.sh` | Автоматизований скрипт налаштування |

---

> Ти не пишеш код. Ти проводиш світло.