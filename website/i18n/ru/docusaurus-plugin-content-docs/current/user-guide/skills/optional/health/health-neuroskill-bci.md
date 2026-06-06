---
title: "Neuroskill Bci"
sidebar_label: "Neuroskill Bci"
description: "Подключись к запущенному экземпляру NeuroSkill и интегрируй реальное когнитивное и эмоциональное состояние пользователя (фокус, расслабление, настроение, когнитивная нагрузка, сонливость…)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Neuroskill Bci

Подключись к запущенному экземпляру NeuroSkill и интегрируй в ответы реальное когнитивное и эмоциональное состояние пользователя в режиме реального времени (фокус, расслабление, настроение, когнитивная нагрузка, сонливость, частота сердечных сокращений, HRV, стадии сна и более 40 производных EXG‑оценок). Требуется носимое BCI‑устройство (Muse 2/S или OpenBCI) и локально запущенное настольное приложение NeuroSkill.
## Метаданные навыка

| | |
|---|---|
| Источник | Опционально — установить с помощью `hermes skills install official/health/neuroskill-bci` |
| Путь | `optional-skills/health/neuroskill-bci` |
| Версия | `1.0.0` |
| Автор | Hermes Agent + Nous Research |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `BCI`, `neurofeedback`, `health`, `focus`, `EEG`, `cognitive-state`, `biometrics`, `neuroskill` |
:::info
Это полное определение skill, которое Hermes загружает, когда этот skill активируется. Это то, что агент видит в виде инструкций, пока skill включён.
:::

# Интеграция NeuroSkill BCI

Подключи Hermes к работающему экземпляру [NeuroSkill](https://neuroskill.com/) для чтения метрик мозга и тела в реальном времени с носимого BCI‑устройства. Используй их для когнитивно‑осознанных ответов, предложений вмешательств и отслеживания умственной производительности со временем.

> **⚠️ Только для исследовательских целей** — NeuroSkill — это инструмент с открытым исходным кодом для исследований. Он **НЕ является медицинским устройством** и **НЕ прошёл одобрения** FDA, CE или любого другого регулирующего органа. Никогда не используй эти метрики для клинической диагностики или лечения.

См. `references/metrics.md` для полного справочника метрик, `references/protocols.md` для протоколов вмешательства и `references/api.md` для WebSocket/HTTP API.

---
## Предварительные требования

- **Node.js 20+** установлен (`node --version`)
- **NeuroSkill desktop app** запущено с подключённым BCI‑устройством
- **BCI hardware**: Muse 2, Muse S или OpenBCI (4‑канальный ЭЭГ + PPG + IMU через BLE)
- `npx neuroskill status` возвращает данные без ошибок

### Проверка настройки
```bash
node --version                    # Must be 20+
npx neuroskill status             # Full system snapshot
npx neuroskill status --json      # Machine-parseable JSON
```

Если `npx neuroskill status` возвращает ошибку, сообщи пользователю:
- Убедись, что приложение **NeuroSkill desktop** открыто
- Убедись, что BCI‑устройство включено и подключено по Bluetooth
- Проверь качество сигнала — зелёные индикаторы в **NeuroSkill** (≥ 0.7 на каждый электрод)
- Если `command not found`, установи **Node.js 20+**.
## Справочник CLI: `npx neuroskill <command>`

Все команды поддерживают `--json` (сырой JSON, pipe‑safe) и `--full` (человекочитаемое резюме + JSON).

| Команда | Описание |
|---------|----------|
| `status` | Полный снимок системы: устройство, оценки, диапазоны, коэффициенты, сон, история |
| `session [N]` | Разбор одной сессии с тенденциями первой/второй половины (0 = самая последняя) |
| `sessions` | Список всех записанных сессий за все дни |
| `search` | ANN‑поиск нейронно‑похожих моментов в истории |
| `compare` | Сравнение сессий A/B с дельтами метрик и анализом тенденций |
| `sleep [N]` | Классификация фаз сна (Wake/N1/N2/N3/REM) с анализом |
| `label "text"` | Создать аннотацию‑метку с отметкой времени в текущий момент |
| `search-labels "query"` | Семантический векторный поиск по прошлым меткам |
| `interactive "query"` | Кросс‑модальный 4‑слойный графовый поиск (текст → EXG → метки) |
| `listen` | Потоковое вещание событий в реальном времени (по умолчанию 5 с, задаётся `--seconds N`) |
| `umap` | 3‑D‑проекция UMAP встраиваний сессий |
| `calibrate` | Открыть окно калибровки и запустить профиль |
| `timer` | Запустить таймер фокусировки (пресеты Pomodoro/Deep Work/Short Focus) |
| `notify "title" "body"` | Отправить системное уведомление через приложение NeuroSkill |
| `raw '{json}'` | Прямой проход сырого JSON к серверу |

### Глобальные флаги
| Флаг | Описание |
|------|----------|
| `--json` | Вывод сырого JSON (без ANSI, pipe‑safe) |
| `--full` | Человекочитаемое резюме + цветной JSON |
| `--port <N>` | Переопределить порт сервера (по умолчанию: автообнаружение, обычно 8375) |
| `--ws` | Принудительно использовать транспорт WebSocket |
| `--http` | Принудительно использовать транспорт HTTP |
| `--k <N>` | Количество ближайших соседей (search, search‑labels) |
| `--seconds <N>` | Длительность для `listen` (по умолчанию 5) |
| `--trends` | Показать тенденции метрик по сессиям (`sessions`) |
| `--dot` | Вывод Graphviz DOT (interactive) |
## 1. Проверка текущего состояния

### Получить живые метрики
```bash
npx neuroskill status --json
```

**Всегда используй `--json`** для надёжного разбора. Вывод по умолчанию — цветной человекочитаемый текст.

### Ключевые поля в ответе

Объект `scores` содержит все живые метрики (шкала 0–1, если не указано иначе):

```jsonc
{
  "scores": {
    "focus": 0.70,           // β / (α + θ) — sustained attention
    "relaxation": 0.40,      // α / (β + θ) — calm wakefulness
    "engagement": 0.60,      // active mental investment
    "meditation": 0.52,      // alpha + stillness + HRV coherence
    "mood": 0.55,            // composite from FAA, TAR, BAR
    "cognitive_load": 0.33,  // frontal θ / temporal α · f(FAA, TBR)
    "drowsiness": 0.10,      // TAR + TBR + falling spectral centroid
    "hr": 68.2,              // heart rate in bpm (from PPG)
    "snr": 14.3,             // signal-to-noise ratio in dB
    "stillness": 0.88,       // 0–1; 1 = perfectly still
    "faa": 0.042,            // Frontal Alpha Asymmetry (+ = approach)
    "tar": 0.56,             // Theta/Alpha Ratio
    "bar": 0.53,             // Beta/Alpha Ratio
    "tbr": 1.06,             // Theta/Beta Ratio (ADHD proxy)
    "apf": 10.1,             // Alpha Peak Frequency in Hz
    "coherence": 0.614,      // inter-hemispheric coherence
    "bands": {
      "rel_delta": 0.28, "rel_theta": 0.18,
      "rel_alpha": 0.32, "rel_beta": 0.17, "rel_gamma": 0.05
    }
  }
}
```

Также включены: `device` (state, battery, firmware), `signal_quality` (по электродам 0–1), `session` (duration, epochs), `embeddings`, `labels`, сводка `sleep` и `history`.

### Интерпретация вывода

Разбери JSON и переведи метрики в естественный язык. Никогда не сообщай только сырые числа — всегда придай им смысл:

**ДЕЛАЙ:**
> "Твой focus сейчас solid — 0.70, это территория состояния потока. Частота сердечных сокращений стабильна — 68 bpm, а твой FAA положительный, что говорит о хорошей мотивации к действию. Отличный момент, чтобы взяться за что‑то сложное."

**НЕ ДЕЛАЙ:**
> "Focus: 0.70, Relaxation: 0.40, HR: 68"

Ключевые пороги интерпретации (см. `references/metrics.md` для полного руководства):
- **Focus > 0.70** → территория состояния потока, защищай её
- **Focus < 0.40** → предложи перерыв или протокол
- **Drowsiness > 0.60** → предупреждение о усталости, риск микросна
- **Relaxation < 0.30** → требуется вмешательство против стресса
- **Cognitive Load > 0.70 sustained** → выгрузка ума или перерыв
- **TBR > 1.5** → доминирование тета, сниженный исполнительный контроль
- **FAA < 0** → отстранённость/негативный аффект — рассмотрите ребалансировку FAA
- **SNR < 3 dB** → ненадёжный сигнал, предложи переустановку электродов

---
## 2. Анализ сессии

### Разбор отдельной сессии
```bash
npx neuroskill session --json         # most recent session
npx neuroskill session 1 --json       # previous session
npx neuroskill session 0 --json | jq '{focus: .metrics.focus, trend: .trends.focus}'
```

Возвращает полные метрики с **тенденциями первой и второй половины** (`"up"`, `"down"`, `"flat"`).
Используй их, чтобы описать, как развивалась сессия:

> "Твой фокус началcя с 0.64 и к концу поднялся до 0.76 — явная восходящая тенденция.
> Когнитивная нагрузка упала с 0.38 до 0.28, что указывает на то, что задача стала более автоматической, когда ты освоился."

### Список всех сессий
```bash
npx neuroskill sessions --json
npx neuroskill sessions --trends      # show per-session metric trends
```

---
## 3. Исторический поиск

### Поиск нейронного сходства
```bash
npx neuroskill search --json                    # auto: last session, k=5
npx neuroskill search --k 10 --json             # 10 nearest neighbors
npx neuroskill search --start <UTC> --end <UTC> --json
```

Находит моменты в истории, нейронно схожие, используя приближённый поиск ближайших соседей HNSW по 128‑мерным ZUNA‑векторным представлениям. Возвращает статистику расстояний, временное распределение (час дня) и дни с наилучшим совпадением.

Используй, когда пользователь спрашивает:
- «Когда я в последний раз был в таком состоянии?»
- «Найди мои лучшие сессии фокусировки»
- «Когда я обычно «крашусь» после обеда?»

### Поиск по семантическим меткам
```bash
npx neuroskill search-labels "deep focus" --k 10 --json
npx neuroskill search-labels "stress" --json | jq '[.results[].EXG_metrics.tbr]'
```

Ищет текст меток с помощью векторных представлений (Xenova/bge-small-en-v1.5). Возвращает совпадающие метки с их связанными метриками EXG на момент их назначения.

### Кросс‑модальный графовый поиск
```bash
npx neuroskill interactive "deep focus" --json
npx neuroskill interactive "deep focus" --dot | dot -Tsvg > graph.svg
```

4‑слойный граф: запрос → текстовые метки → точки EXG → соседние метки. Используй `--k-text`, `--k-EXG`, `--reach <minutes>` для настройки.

---
## 4. Сравнение сессий
```bash
npx neuroskill compare --json                   # auto: last 2 sessions
npx neuroskill compare --a-start <UTC> --a-end <UTC> --b-start <UTC> --b-end <UTC> --json
```

Возвращает дельты метрик с абсолютным изменением, процентным изменением и направлением для
~50 метрик. Также включает массивы `insights.improved[]` и `insights.declined[]`,
sleep staging для обеих сессий и идентификатор задачи UMAP.

Интерпретируй сравнения в контексте — упоминай тенденции, а не только дельты:
> "Вчера у тебя было два сильных блока фокусировки (10 ч и 14 ч). Сегодня был один,
> начавшийся около 11 ч и продолжающийся. Твоя общая вовлечённость сегодня выше, но
> появилось больше всплесков стресса — твой стресс‑индекс вырос на 15 %, а FAA чаще
> опускался в отрицательную зону."

```bash
# Sort metrics by improvement percentage
npx neuroskill compare --json | jq '.insights.deltas | to_entries | sort_by(.value.pct) | reverse'
```

---
## 5. Данные сна
```bash
npx neuroskill sleep --json                     # last 24 hours
npx neuroskill sleep 0 --json                   # most recent sleep session
npx neuroskill sleep --start <UTC> --end <UTC> --json
```

Возвращает данные о стадиях сна по эпохам (окна по 5 секунд) с анализом:
- **Коды стадий**: 0 = Бодрствование, 1 = N1, 2 = N2, 3 = N3 (глубокий), 4 = REM
- **Анализ**: efficiency_pct, onset_latency_min, rem_latency_min, количество эпизодов (bout counts)
- **Нормативные значения**: N3 15–25 %, REM 20–25 %, эффективность > 85 %, начало < 20 мин

```bash
npx neuroskill sleep --json | jq '.summary | {n3: .n3_epochs, rem: .rem_epochs}'
npx neuroskill sleep --json | jq '.analysis.efficiency_pct'
```

Используй это, когда пользователь упоминает сон, усталость или восстановление.

---
## 6. Маркировка моментов
```bash
npx neuroskill label "breakthrough"
npx neuroskill label "studying algorithms"
npx neuroskill label "post-meditation"
npx neuroskill label --json "focus block start"   # returns label_id
```

Автоматически присваивать метки моментам, когда:
- Пользователь сообщает о прорыве или озарении
- Пользователь начинает новый тип задачи (например, «переключаюсь на код‑ревью»)
- Пользователь завершает значимый протокол
- Пользователь просит отметить текущий момент
- Происходит заметный переход состояния (вход в поток/выход из потока)

Метки сохраняются в базе данных и индексируются для последующего получения через команды `search-labels` и `interactive`.

---
## 7. Потоковая передача в реальном времени
```bash
npx neuroskill listen --seconds 30 --json
npx neuroskill listen --seconds 5 --json | jq '[.[] | select(.event == "scores")]'
```

Поток передаёт живые события WebSocket (EXG, PPG, IMU, scores, labels) в течение указанного времени. Требуется соединение WebSocket (недоступно при использовании `--http`).

Используй это для сценариев непрерывного мониторинга или для наблюдения за изменениями метрик в реальном времени во время протокола.

---
## 8. Визуализация UMAP
```bash
npx neuroskill umap --json                      # auto: last 2 sessions
npx neuroskill umap --a-start <UTC> --a-end <UTC> --b-start <UTC> --b-end <UTC> --json
```

GPU‑ускоренная 3D‑проекция UMAP‑встраиваний ZUNA. `separation_score` отображает степень нейронного различия двух сессий:
- **> 1.5** → Сессии нейронно различны (разные состояния мозга)
- **< 0.5** → Состояния мозга схожи в обеих сессиях

---
## 9. Проактивное осознание состояния

### Проверка при начале сессии
В начале сессии, при желании, можно выполнить проверку статуса, если пользователь упоминает,
что носит устройство, или спрашивает о своём состоянии:
```bash
npx neuroskill status --json
```

Вставь краткое резюме состояния:
> «Быстрая проверка: фокус — 0.62, расслабление — 0.55, ваш FAA положительный — мотивация подхода активирована. Похоже, хороший старт.»

### Когда проактивно упоминать состояние

Упоминай когнитивное состояние **только** когда:
- Пользователь явно спрашивает («Как я себя чувствую?», «Проверь мой фокус»)
- Пользователь сообщает о трудностях с концентрацией, стрессом или усталостью
- Пересекается критический порог (сонливость > 0.70, фокус < 0.30 длительно)
- Пользователь собирается выполнить требующее когнитивных усилий действие и спрашивает о готовности

**Не** прерывай состояние потока, чтобы сообщать метрики. Если фокус > 0.75, защищай
сессию — молчание является правильным ответом.
## 10. Предложение протоколов

Когда метрики указывают на необходимость, предложи протокол из `references/protocols.md`.
Всегда спрашивай перед началом — не прерывай состояние потока:

> "Твоя концентрация падает уже 15 минут, а TBR поднимается выше 1.5 — признаки доминирования тета‑ритма и умственной усталости. Хочешь, чтобы я провёл тебя через якорь Theta‑Beta Neurofeedback? Это 90‑секундное упражнение, использующее ритмический счёт и дыхание для подавления тета и повышения бета."

Ключевые триггеры:
- **Focus &lt; 0.40, TBR > 1.5** → Theta‑Beta Neurofeedback Anchor или Box Breathing
- **Relaxation &lt; 0.30, stress_index high** → Cardiac Coherence или 4‑7‑8 Breathing
- **Cognitive Load > 0.70 sustained** → Cognitive Load Offload (mind dump)
- **Drowsiness > 0.60** → Ultradian Reset или Wake Reset
- **FAA &lt; 0 (negative)** → FAA Rebalancing
- **Flow State (focus > 0.75, engagement > 0.70)** → Do NOT interrupt
- **High stillness + headache_index** → Neck Release Sequence
- **Low RMSSD (&lt; 25 ms)** → Vagal Toning

---
## 11. Дополнительные инструменты

### Focus Timer
```bash
npx neuroskill timer --json
```
Запускает окно **Focus Timer** с предустановками Pomodoro (25/5), Deep Work (50/10) или Short Focus (15/5).

### Calibration
```bash
npx neuroskill calibrate
npx neuroskill calibrate --profile "Eyes Open"
```
Открывает окно калибровки. Полезно, когда качество сигнала низкое или пользователь хочет установить персонализированный базовый уровень.

### OS Notifications
```bash
npx neuroskill notify "Break Time" "Your focus has been declining for 20 minutes"
```

### Raw JSON Passthrough
```bash
npx neuroskill raw '{"command":"status"}' --json
```
Для любой серверной команды, ещё не сопоставленной с подкомандой CLI.

---
## Обработка ошибок

| Ошибка | Вероятная причина | Исправление |
|-------|-------------------|-------------|
| `npx neuroskill status` hangs | Приложение NeuroSkill не запущено | Открой приложение NeuroSkill на рабочем столе |
| `device.state: "disconnected"` | BCI‑устройство не подключено | Проверь Bluetooth и заряд батареи устройства |
| All scores return 0 | Плохой контакт электродов | Перемести головную повязку, увлажни электроды |
| `signal_quality` values &lt; 0.7 | Слишком свободные электроды | Отрегулируй посадку, очисти контакты электродов |
| SNR &lt; 3 dB | Шумный сигнал | Минимизируй движение головы, проверь условия |
| `command not found: npx` | Node.js не установлен | Установи Node.js 20+ |
## Примеры взаимодействий

**"How am I doing right now?"**
```bash
npx neuroskill status --json
```
→ Интерпретировать оценки естественно, упомянув фокус, расслабление, настроение и любые заметные показатели (FAA, TBR). Предложить действие только если метрики указывают на необходимость.

**"I can't concentrate"**
```bash
npx neuroskill status --json
```
→ Проверить, подтверждают ли метрики это (высокая тета, низкая бета, растущий TBR, высокая сонливость).
→ Если подтверждено, предложить подходящий протокол из `references/protocols.md`.
→ Если метрики выглядят нормально, проблема, скорее всего, мотивационная, а не нейрологическая.

**"Compare my focus today vs yesterday"**
```bash
npx neuroskill compare --json
```
→ Интерпретировать тенденции, а не только цифры. Указать, что улучшилось, что ухудшилось и возможные причины.

**"When was I last in a flow state?"**
```bash
npx neuroskill search-labels "flow" --json
npx neuroskill search --json
```
→ Сообщить временные метки, связанные метрики и то, чем пользователь занимался (из меток).

**"How did I sleep?"**
```bash
npx neuroskill sleep --json
```
→ Сообщить архитектуру сна (N3 %, REM %, эффективность), сравнить с здоровыми целями и отметить любые проблемы (много периодов бодрствования, низкий REM).

**"Mark this moment — I just had a breakthrough"**
```bash
npx neuroskill label "breakthrough"
```
→ Подтвердить сохранение метки. При желании добавить текущие метрики, чтобы запомнить состояние.
## Ссылки

- [NeuroSkill Paper — arXiv:2603.03212](https://arxiv.org/abs/2603.03212) (Kosmyna & Hauptmann, MIT Media Lab)
- [NeuroSkill Desktop App](https://github.com/NeuroSkill-com/skill) (GPLv3)
- [NeuroLoop CLI Companion](https://github.com/NeuroSkill-com/neuroloop) (GPLv3)
- [MIT Media Lab Project](https://www.media.mit.edu/projects/neuroskill/overview/)