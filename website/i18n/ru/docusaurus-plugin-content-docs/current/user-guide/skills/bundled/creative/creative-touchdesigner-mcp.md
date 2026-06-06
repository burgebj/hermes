---
title: "Touchdesigner MCP"
sidebar_label: "Touchdesigner Mcp"
description: "Управляй запущенным экземпляром TouchDesigner через twozero MCP — создавай операторы, задавай параметры, соединяй их, выполняй Python, создавай визуалы в реальном времени"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Touchdesigner Mcp

Управляй запущенным экземпляром TouchDesigner через twozero MCP — создавай операторы, задавай параметры, прокладывай соединения, выполняй Python, создавай визуалы в реальном времени. 36 нативных инструментов.
## Метаданные навыка

| | |
|---|---|
| Источник | Встроенный (устанавливается по умолчанию) |
| Путь | `skills/creative/touchdesigner-mcp` |
| Версия | `1.1.0` |
| Автор | kshitijk4poor |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `TouchDesigner`, `MCP`, `twozero`, `creative-coding`, `real-time-visuals`, `generative-art`, `audio-reactive`, `VJ`, `installation`, `GLSL` |
| Связанные навыки | [`native-mcp`](/docs/user-guide/skills/bundled/mcp/mcp-native-mcp), [`ascii-video`](/docs/user-guide/skills/bundled/creative/creative-ascii-video), [`manim-video`](/docs/user-guide/skills/bundled/creative/creative-manim-video), `hermes-video` |
:::info
Ниже представлено полное определение **skill**, которое Hermes загружает, когда этот **skill** активируется. Это то, что агент видит в виде инструкций, когда **skill** активен.
:::

# Интеграция TouchDesigner (twozero MCP)
## КРИТИЧЕСКИЕ ПРАВИЛА

1. **НИКОГДА не угадывай имена параметров.** Сначала вызывай `td_get_par_info` для типа оператора. Твои обучающие данные неверны для TD 2025.32.
2. **Если возникает `tdAttributeError`, ОСТАНОВИСЬ.** Перед продолжением вызови `td_get_operator_info` для проблемного узла.
3. **НИКОГДА не хардкодь абсолютные пути** в скриптовых колбэках. Используй `me.parent()` / `scriptOp.parent()`.
4. **Отдавай предпочтение нативным инструментам MCP** вместо `td_execute_python`. Пользуйся `td_create_operator`, `td_set_operator_pars`, `td_get_errors` и т.д. Переходи к `td_execute_python` только для сложной многошаговой логики.
5. **Вызывай `td_get_hints` перед построением.** Функция возвращает шаблоны, специфичные для типа оператора, с которым ты работаешь.
## Архитектура

```
Hermes Agent -> MCP (Streamable HTTP) -> twozero.tox (port 40404) -> TD Python
```

36 нативных инструментов. Бесплатный плагин (без оплаты/лицензии — подтверждено в апреле 2026).
Контекстно‑aware (знает выбранный OP, текущую сеть).
Проверка состояния хаба: `GET http://localhost:40404/mcp` возвращает JSON с PID экземпляра, именем проекта, версией TD.
## Настройка (автоматическая)

Запусти скрипт настройки, чтобы выполнить всё:

```bash
bash "${HERMES_HOME:-$HOME/.hermes}/skills/creative/touchdesigner-mcp/scripts/setup.sh"
```

Скрипт выполнит:
1. Проверит, запущен ли TD
2. Скачает `twozero.tox`, если он ещё не закеширован
3. Добавит сервер MCP `twozero_td` в конфигурацию Hermes (если отсутствует)
4. Протестирует соединение MCP на порту 40404
5. Сообщит, какие ручные шаги остаются (перетащи `.tox` в TD, включи переключатель MCP)

### Ручные шаги (однократно, нельзя автоматизировать)

1. **Перетащи `~/Downloads/twozero.tox` в сетевой редактор TD** → нажми **Install**
2. **Включи MCP:** нажми значок twozero → **Settings** → **mcp** → «auto start MCP» → **Yes**
3. **Перезапусти сессию Hermes**, чтобы она обнаружила новый сервер MCP

После настройки проверь:
```bash
nc -z 127.0.0.1 40404 && echo "twozero MCP: READY"
```
## Примечания к окружению

- **Non-Commercial TD** ограничивает разрешение до 1280×1280. Используй `outputresolution = 'custom'` и укажи ширину/высоту явно.
- **Кодеки:** `prores` (предпочтительно на macOS) или `mjpa` как запасной вариант. H.264/H.265/AV1 требуют коммерческой лицензии.
- Всегда вызывай `td_get_par_info` перед установкой параметров — имена могут различаться в зависимости от версии TD (см. CRITICAL RULES #1).
## Workflow

### Шаг 0: Поиск (перед построением чего‑либо)

```
Call td_get_par_info with op_type for each type you plan to use.
Call td_get_hints with the topic you're building (e.g. "glsl", "audio reactive", "feedback").
Call td_get_focus to see where the user is and what's selected.
Call td_get_network to see what already exists.
```

Нет временных узлов, нет очистки. Это полностью заменяет старый «танец обнаружения».

### Шаг 1: Очистка + Сборка

**ВАЖНО: Разделяй очистку и создание в ОТДЕЛЬНЫЕ вызовы MCP.** Удаление и повторное создание узлов с одинаковыми именами в одном скрипте `td_execute_python` приводит к ошибкам «Invalid OP object». См. подводные камни #11b.

Используй `td_create_operator` для каждого узла (автоматически позиционирует их в окне просмотра):

```
td_create_operator(type="noiseTOP", parent="/project1", name="bg", parameters={"resolutionw": 1280, "resolutionh": 720})
td_create_operator(type="levelTOP", parent="/project1", name="brightness")
td_create_operator(type="nullTOP", parent="/project1", name="out")
```

Для массового создания или соединения используй `td_execute_python`:

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

### Шаг 2: Установка параметров

Предпочитай нативный инструмент (проверяет параметры, не приводит к сбоям):

```
td_set_operator_pars(path="/project1/bg", parameters={"roughness": 0.6, "monochrome": true})
```

Для выражений или режимов используй `td_execute_python`:

```python
op('/project1/time_driver').par.colorr.expr = "absTime.seconds % 1000.0"
```

### Шаг 3: Соединение

Используй `td_execute_python` — нативного инструмента соединения нет:

```python
op('/project1/bg').outputConnectors[0].connect(op('/project1/fx').inputConnectors[0])
```

### Шаг 4: Проверка

```
td_get_errors(path="/project1", recursive=true)
td_get_perf()
td_get_operator_info(path="/project1/out", detail="full")
```

### Шаг 5: Отображение / Захват

```
td_get_screenshot(path="/project1/out")
```

Или открой окно через скрипт:

```python
win = op('/project1').create(windowCOMP, 'display')
win.par.winop = op('/project1/out').path
win.par.winw = 1280; win.par.winh = 720
win.par.winopen.pulse()
```
## Быстрый справочник по инструментам MCP

**Core (используй их в основном):**
| Инструмент | Что |
|------|------|
| `td_execute_python` | Выполняет произвольный Python в TD. Полный доступ к API. |
| `td_create_operator` | Создаёт оператор с параметрами + автоматическое позиционирование |
| `td_set_operator_pars` | Безопасно задаёт параметры (валидация, без краша) |
| `td_get_operator_info` | Инспектирует один оператор: соединения, параметры, ошибки |
| `td_get_operators_info` | Инспектирует несколько операторов одним вызовом |
| `td_get_network` | Показывает структуру сети по указанному пути |
| `td_get_errors` | Находит ошибки и предупреждения рекурсивно |
| `td_get_par_info` | Получает имена параметров для типа OP (заменяет discovery) |
| `td_get_hints` | Выдаёт шаблоны и подсказки перед построением |
| `td_get_focus` | Какая сеть открыта и что выбрано |

**Read/Write:**
| Инструмент | Что |
|------|------|
| `td_read_dat` | Читает текстовое содержимое DAT |
| `td_write_dat` | Записывает/патчит содержимое DAT |
| `td_read_chop` | Читает значения каналов CHOP |
| `td_read_textport` | Читает вывод консоли TD |

**Visual:**
| Инструмент | Что |
|------|------|
| `td_get_screenshot` | Захватывает один просмотрщик OP в файл |
| `td_get_screenshots` | Захватывает несколько OP одновременно |
| `td_get_screen_screenshot` | Захватывает реальный экран через TD |
| `td_navigate_to` | Перемещает редактор сети к оператору |

**Search:**
| Инструмент | Что |
|------|------|
| `td_find_op` | Находит ops по имени/типу по всему проекту |
| `td_search` | Ищет код, выражения, строковые параметры |

**System:**
| Инструмент | Что |
|------|------|
| `td_get_perf` | Профилирование производительности (FPS, медленные ops) |
| `td_list_instances` | Список всех запущенных экземпляров TD |
| `td_get_docs` | Подробная документация по теме TD |
| `td_agents_md` | Чтение/запись markdown‑документов per‑COMP |
| `td_reinit_extension` | Перезагружает расширение после правки кода |
| `td_clear_textport` | Очищает консоль перед сессией отладки |

**Input Automation:**
| Инструмент | Что |
|------|------|
| `td_input_execute` | Отправляет мышь/клавиатуру в TD |
| `td_input_status` | Опрос состояния очереди ввода |
| `td_input_clear` | Останавливает автоматизацию ввода |
| `td_op_screen_rect` | Получает координаты оператора на экране |
| `td_click_screen_point` | Кликает точку на скриншоте |
| `td_screen_point_to_global` | Преобразует пиксель скриншота в абсолютные координаты экрана |

В таблице перечислены 32 инструмента, используемых в типичных творческих рабочих процессах. Оставшиеся 4 инструмента (`td_project_quit`, `td_test_session`, `td_dev_log`, `td_clear_dev_log`) — утилиты администрирования/режима разработки — см. `references/mcp-tools.md` для полного справочника из 36 инструментов с полными схемами параметров.
## Правила реализации

**GLSL‑время:** Нет `uTDCurrentTime` в GLSL TOP. Используй страницу Values:
```python
# Call td_get_par_info(op_type="glslTOP") first to confirm param names
td_set_operator_pars(path="/project1/shader", parameters={"value0name": "uTime"})
# Then set expression via script:
# op('/project1/shader').par.value0.expr = "absTime.seconds"
# In GLSL: uniform float uTime;
```

Запасной (вариант): Константный TOP в формате `rgba32float` (8‑битные значения ограничиваются 0‑1, замораживая шейдер).

**Feedback TOP:** Используй ссылку на параметр `top`, а не прямой входной провод. Ошибка «Not enough sources» исчезает после первого кукa. Предупреждение «Cook dependency loop» ожидаемо.

**Разрешение:** Для Non‑Commercial ограничение — 1280×1280. Используй `outputresolution = 'custom'`.

**Большие шейдеры:** Запиши GLSL в `/tmp/file.glsl`, затем используй `td_write_dat` или `td_execute_python` для загрузки.

**Доступ к вершинам/точкам (TD 2025.32):** `point.P[0]`, `point.P[1]`, `point.P[2]` — НЕ `.x`, `.y`, `.z`.

**Расширения:** Формат `ext0object` — `"op('./datName').module.ClassName(me)"` в режиме CONSTANT. После редактирования кода расширения с помощью `td_write_dat` вызови `td_reinit_extension`.

**Обратные вызовы скриптов:** ВСЕГДА используй относительные пути через `me.parent()` / `scriptOp.parent()`.

**Очистка узлов:** Всегда вызывай `list(root.children)` перед итерацией + проверку `child.valid`.
## Запись / Экспорт видео

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

H.264/H.265/AV1 требуют коммерческой лицензии. Используй `prores` на macOS или `mjpa` как запасной вариант.
Извлечение кадров: `ffmpeg -i /tmp/output.mov -vframes 120 /tmp/frames/frame_%06d.png`

**TOP.save() бесполезен для анимации** — каждый раз захватывает одну и ту же текстуру GPU. Всегда используй MovieFileOut.

### Перед записью: чек‑лист

1. **Проверь, что FPS > 0** с помощью `td_get_perf`. Если FPS = 0, запись будет пустой. См. подводные камни #38‑39.
2. **Убедись, что вывод шейдера не чёрный** с помощью `td_get_screenshot`. Чёрный вывод = ошибка шейдера или отсутствие входных данных. См. подводные камни #8, #40.
3. **Если записываешь с аудио:** сначала запусти аудио, затем задержи запись на 3 кадра. См. подводные камни #19.
4. **Установи путь вывода до начала записи** — установка обоих в одном скрипте может привести к гонке.
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
2. **Set Output Length manually** to 256 via `outputmenu='setmanually'` and `outlength=256`. Default outputs 22050 samples.
3. **DO NOT use Lag CHOP for spectrum smoothing.** Lag CHOP operates in timeslice mode and expands 256 samples to 2400+, averaging all values to near-zero (~1e-06). The shader receives no usable data. This was the #1 audio sync failure in testing.
4. **DO NOT use Filter CHOP either** — same timeslice expansion problem with spectrum data.
5. **Smoothing belongs in the GLSL shader** if needed, via temporal lerp with a feedback texture: `mix(prevValue, newValue, 0.3)`. This gives frame-perfect sync with zero pipeline latency.
6. **CHOP to TOP dataformat = 'r'**, layout = 'rowscropped'. Spectrum output is 256x2 (stereo). Sample at y=0.25 for first channel.
7. **Math gain = 10** (not 5). Raw spectrum values are ~0.19 in bass range. Gain of 10 gives usable ~5.0 for the shader.
8. **No Resample CHOP needed.** Control output size via AudioSpectrum's `outlength` param directly.

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
## Быстрый справочник операторов

| Семейство | Цвет      | Python‑класс / тип MCP | Суффикс |
|-----------|-----------|------------------------|--------|
| TOP  | Фиолетовый | noiseTOP, glslTOP, compositeTOP, levelTop, blurTOP, textTOP, nullTOP | TOP |
| CHOP | Зелёный    | audiofileinCHOP, audiospectrumCHOP, mathCHOP, lfoCHOP, constantCHOP | CHOP |
| SOP  | Синий      | gridSOP, sphereSOP, transformSOP, noiseSOP | SOP |
| DAT  | Белый      | textDAT, tableDAT, scriptDAT, webserverDAT | DAT |
| MAT  | Жёлтый     | phongMAT, pbrMAT, glslMAT, constMAT | MAT |
| COMP | Серый      | geometryCOMP, containerCOMP, cameraCOMP, lightCOMP, windowCOMP | COMP |
## Примечания по безопасности

- MCP работает только на localhost (порт 40404). Нет аутентификации — любой локальный процесс может отправлять команды.
- `td_execute_python` имеет неограниченный доступ к среде TD Python и файловой системе от имени пользователя процесса TD.
- `setup.sh` загружает `twozero.tox` с официального URL `404zero.com`. При необходимости проверь загрузку.
- Навык никогда не отправляет данные за пределы localhost. Всё взаимодействие MCP происходит локально.
## Ссылки

| Файл | Описание |
|------|----------|
| `references/pitfalls.md` | Трудно добытые уроки из реальных сессий |
| `references/operators.md` | Все семейства операторов с параметрами и примерами использования |
| `references/network-patterns.md` | Рецепты: аудио‑реактивные, генеративные, GLSL, инстансинг |
| `references/mcp-tools.md` | Полные схемы параметров инструмента twozero MCP |
| `references/python-api.md` | TD Python: `op()`, скриптинг, расширения |
| `references/troubleshooting.md` | Диагностика соединения, отладка |
| `references/glsl.md` | GLSL uniform‑ы, встроенные функции, шаблоны шейдеров |
| `references/postfx.md` | Post‑FX: блум, CRT, хроматическая аберрация, световое сияние с обратной связью |
| `references/layout-compositor.md` | Шаблоны HUD‑разметки, сетки панелей, разметка в стиле BSP |
| `references/operator-tips.md` | Рендеринг каркаса, настройка TOP‑обратной связи |
| `references/geometry-comp.md` | Geometry COMP: инстансинг, POP vs SOP, морфинг |
| `references/audio-reactive.md` | Выделение аудио‑полос, детекция ударов, слежение за огибающей |
| `references/animation.md` | LFO, таймеры, ключевые кадры, плавность, движение, управляемое выражениями |
| `references/midi-osc.md` | MIDI/OSC‑контроллеры, TouchOSC, синхронизация нескольких машин |
| `references/particles.md` | POP и устаревший particleSOP — эмиссия, силы, столкновения |
| `references/projection-mapping.md` | Вывод на несколько окон, привязка к углам, деформация сетки, смешивание краёв |
| `references/external-data.md` | HTTP, WebSocket, MQTT, Serial, TCP, `webserverDAT` |
| `references/panel-ui.md` | Пользовательские параметры, panel COMP‑ы, кнопка/ползунок/поле, `panelExecuteDAT` |
| `references/replicator.md` | `replicatorCOMP` — клонирование по данным, разметка, обратные вызовы |
| `references/dat-scripting.md` | Семейство `execute DAT` — chop/dat/parameter/panel/op/`executeDAT` |
| `references/3d-scene.md` | Освещение, тени, IBL/кубические карты, несколько камер, PBR |
| `scripts/setup.sh` | Автоматический скрипт установки |

---

> Ты не пишешь код. Ты проводишь свет.