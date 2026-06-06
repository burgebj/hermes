---
title: "Neuroskill Bci"
sidebar_label: "Neuroskill Bci"
description: "Підключись до запущеного екземпляра NeuroSkill і включи реальний час стану користувача — когнітивний та емоційний (фокус, розслаблення, настрій, когнітивне навантаження, сонливість…)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Neuroskill Bci

Підключись до запущеного екземпляра NeuroSkill і включи в відповіді дані про когнітивний та емоційний стан користувача в реальному часі (зосередженість, розслаблення, настрій, когнітивне навантаження, сонливість, частоту серцебиття, HRV, стадії сну та понад 40 похідних EXG‑балів). Потрібен BCI‑пристрій (Muse 2/S або OpenBCI) та локально запущений десктоп‑додаток NeuroSkill.
## Метадані навички

| | |
|---|---|
| Source | Необов’язково — install with `hermes skills install official/health/neuroskill-bci` |
| Path | `optional-skills/health/neuroskill-bci` |
| Version | `1.0.0` |
| Author | Hermes Agent + Nous Research |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `BCI`, `neurofeedback`, `health`, `focus`, `EEG`, `cognitive-state`, `biometrics`, `neuroskill` |
:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це інструкції, які бачить агент під час роботи навички.
:::

# NeuroSkill BCI Integration

Підключи Hermes до запущеного екземпляра [NeuroSkill](https://neuroskill.com/), щоб читати
метрики мозку та тіла в реальному часі з BCI‑пристрою. Використовуй їх для
надання когнітивно‑орієнтованих відповідей, пропозиції втручань та відстеження
ментальної продуктивності з часом.

> **⚠️ Тільки для дослідницького використання** — NeuroSkill — це інструмент з відкритим кодом для досліджень. Він
> НЕ є медичним пристроєм і НЕ пройшов сертифікацію FDA, CE чи будь‑якого іншого регуляторного органу. Не використовуйте ці метрики для клінічної діагностики чи лікування.

Дивись `references/metrics.md` для повного опису метрик, `references/protocols.md`
для протоколів втручань та `references/api.md` для WebSocket/HTTP API.

---
## Передумови

- **Node.js 20+** встановлений (`node --version`)
- **NeuroSkill desktop app** запущений з підключеним BCI‑пристроєм
- **BCI‑апаратура**: Muse 2, Muse S або OpenBCI (4‑канальний EEG + PPG + IMU через BLE)
- `npx neuroskill status` повертає дані без помилок

### Перевірка налаштувань
```bash
node --version                    # Must be 20+
npx neuroskill status             # Full system snapshot
npx neuroskill status --json      # Machine-parseable JSON
```

Якщо `npx neuroskill status` повертає помилку, повідом користувачу:
- Переконайся, що NeuroSkill desktop app відкритий
- Переконайся, що BCI‑пристрій увімкнено і підключено через Bluetooth
- Перевір якість сигналу — зелені індикатори в NeuroSkill (≥0.7 на електрод)
- Якщо `command not found`, встанови Node.js 20+

---
## Довідник CLI: `npx neuroskill <command>`

Усі команди підтримують `--json` (raw JSON, pipe‑safe) та `--full` (human summary + JSON).

| Command | Description |
|---------|-------------|
| `status` | Повний знімок системи: пристрій, бали, діапазони, співвідношення, сон, історія |
| `session [N]` | Розбір однієї сесії з тенденціями першої/другої половини (0 = найновіша) |
| `sessions` | Список усіх записаних сесій за всі дні |
| `search` | ANN‑пошук схожості для нейронно схожих історичних моментів |
| `compare` | Порівняння сесій A/B з дельтами метрик та аналізом тенденцій |
| `sleep [N]` | Класифікація стадій сну (Wake/N1/N2/N3/REM) з аналізом |
| `label "text"` | Створити часову мітку в поточний момент |
| `search-labels "query"` | Семантичний векторний пошук по минулих мітках |
| `interactive "query"` | Крос‑модальний 4‑шаровий графовий пошук (text → EXG → labels) |
| `listen` | Потокове передавання подій у реальному часі (за замовчуванням 5 s, встанови `--seconds N`) |
| `umap` | 3D‑проекція UMAP вбудовувань сесій |
| `calibrate` | Відкрити вікно калібрування та запустити профіль |
| `timer` | Запустити таймер фокусування (пресети Pomodoro/Deep Work/Short Focus) |
| `notify "title" "body"` | Надіслати OS‑повідомлення через додаток NeuroSkill |
| `raw '{json}'` | Прямий JSON‑прохід до сервера |

### Глобальні прапорці
| Flag | Description |
|------|-------------|
| `--json` | Вивід raw JSON (без ANSI, pipe‑safe) |
| `--full` | Human summary + colorized JSON |
| `--port <N>` | Перевизначити порт сервера (за замовчуванням: авто‑виявлення, зазвичай 8375) |
| `--ws` | Примусово використовувати транспорт WebSocket |
| `--http` | Примусово використовувати транспорт HTTP |
| `--k <N>` | Кількість найближчих сусідів (search, search‑labels) |
| `--seconds <N>` | Тривалість для `listen` (за замовчуванням: 5) |
| `--trends` | Показати тенденції метрик по сесіях (`sessions`) |
| `--dot` | Вивід Graphviz DOT (interactive) |

---
## 1. Перевірка поточного стану

### Отримання живих метрик
```bash
npx neuroskill status --json
```

**Завжди використовуйте `--json`** для надійного парсингу. Типовий вивід — це кольоровий
людсько‑читабельний текст.

### Ключові поля у відповіді

Об’єкт `scores` містить усі живі метрики (шкала 0–1, якщо не зазначено інше):

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

Також включає: `device` (стан, батарея, прошивка), `signal_quality` (по‑електродно 0–1),
`session` (тривалість, епохи), `embeddings`, `labels`, підсумок `sleep` та `history`.

### Інтерпретація виводу

Парсьте JSON і переводьте метрики в природну мову. Ніколи не повідомляйте лише
сирі числа — завжди додавайте їхнє значення:

**РОБИ:**
> "Твоя концентрація зараз стабільна на рівні 0.70 — це територія стану потоку. Частота
> серцебиття стабільна — 68 bpm, а твій FAA позитивний, що свідчить про хорошу
> мотивацію підходу. Чудовий час, щоб зайнятись чимось складним."

**НЕ РОБИ:**
> "Focus: 0.70, Relaxation: 0.40, HR: 68"

Ключові пороги інтерпретації (дивись `references/metrics.md` для повного гіда):
- **Focus > 0.70** → територія стану потоку, захищай її
- **Focus < 0.40** → пропонуй перерву або протокол
- **Drowsiness > 0.60** → попередження про втому, ризик мікросну
- **Relaxation < 0.30** → потрібне втручання проти стресу
- **Cognitive Load > 0.70 протягом тривалого часу** → розвантаження розуму або перерва
- **TBR > 1.5** → домінування тети, знижений виконавчий контроль
- **FAA < 0** → відступ/негативний афект — розглянь балансування FAA
- **SNR < 3 dB** → ненадійний сигнал, пропонуй переналаштування електродів

---
## 2. Аналіз сесії

### Розбір окремої сесії
```bash
npx neuroskill session --json         # most recent session
npx neuroskill session 1 --json       # previous session
npx neuroskill session 0 --json | jq '{focus: .metrics.focus, trend: .trends.focus}'
```

Повертає повні метрики з **тендами першої половини проти другої половини** (`"up"`, `"down"`, `"flat"`).
Використовуй це, щоб описати, як розвивалась сесія:

> "Твій фокус почався з 0.64 і піднявся до 0.76 до кінця — чіткий висхідний тренд.
> Навантаження на когнітивні ресурси впало з 0.38 до 0.28, що свідчить про те, що завдання стало більш автоматичним, коли ти освоївся."

### Перелік усіх сесій
```bash
npx neuroskill sessions --json
npx neuroskill sessions --trends      # show per-session metric trends
```

---
## 3. Historical Search

### Neural Similarity Search
```bash
npx neuroskill search --json                    # auto: last session, k=5
npx neuroskill search --k 10 --json             # 10 nearest neighbors
npx neuroskill search --start <UTC> --end <UTC> --json
```

Знаходить моменти в історії, які нейронно схожі, використовуючи HNSW‑аппроксимативний пошук найближчих сусідів за 128‑вимірними ZUNA‑ембеддінгами. Повертає статистику відстаней, часовий розподіл (година доби) та топ‑збіги днів.

Використовуй це, коли користувач запитує:
- «Коли я останній раз був у такому стані?»
- «Знайди мої найкращі сесії фокусування»
- «Коли я зазвичай падаю в післяобідню втому?»

### Semantic Label Search
```bash
npx neuroskill search-labels "deep focus" --k 10 --json
npx neuroskill search-labels "stress" --json | jq '[.results[].EXG_metrics.tbr]'
```

Шукає текст міток за допомогою векторних ембеддінгів (Xenova/bge-small-en-v1.5). Повертає відповідні мітки з їхніми пов’язаними EXG‑метриками на момент маркування.

### Cross-Modal Graph Search
```bash
npx neuroskill interactive "deep focus" --json
npx neuroskill interactive "deep focus" --dot | dot -Tsvg > graph.svg
```

4‑шаровий граф: запит → текстові мітки → EXG‑точки → близькі мітки. Використовуй `--k-text`, `--k-EXG`, `--reach <minutes>` для налаштування.

---
## 4. Порівняння сесій
```bash
npx neuroskill compare --json                   # auto: last 2 sessions
npx neuroskill compare --a-start <UTC> --a-end <UTC> --b-start <UTC> --b-end <UTC> --json
```

Повертає дельти метрик з абсолютною зміною, відсотковою зміною та напрямком для
~50 метрик. Також включає масиви `insights.improved[]` і `insights.declined[]`,
стадіювання сну для обох сесій та ідентифікатор завдання UMAP.

Інтерпретуй порівняння в контексті — згадуй тенденції, а не лише дельти:
> «Учора у тебе було два сильних блоки фокусування (10 год і 14 год). Сьогодні був один,
> який розпочався близько 11 год і ще триває. Твоя загальна залученість сьогодні вища,
> але було більше сплесків стресу — індекс стресу підскочив на 15 %, а FAA частіше падала в негатив.»

```bash
# Sort metrics by improvement percentage
npx neuroskill compare --json | jq '.insights.deltas | to_entries | sort_by(.value.pct) | reverse'
```

---
## 5. Дані сну
```bash
npx neuroskill sleep --json                     # last 24 hours
npx neuroskill sleep 0 --json                   # most recent sleep session
npx neuroskill sleep --start <UTC> --end <UTC> --json
```

Повертає дані про стадії сну за епохами (вікна по 5 секунд) з аналізом:
- **Коди стадій**: 0 = Wake, 1 = N1, 2 = N2, 3 = N3 (глибокий), 4 = REM
- **Аналіз**: efficiency_pct, onset_latency_min, rem_latency_min, кількість фрагментів
- **Здорові цілі**: N3 15–25 %, REM 20–25 %, ефективність > 85 %, затримка < 20 хв

```bash
npx neuroskill sleep --json | jq '.summary | {n3: .n3_epochs, rem: .rem_epochs}'
npx neuroskill sleep --json | jq '.analysis.efficiency_pct'
```

Використовуй це, коли користувач згадує сон, втому або відновлення.

---
## 6. Позначення моментів
```bash
npx neuroskill label "breakthrough"
npx neuroskill label "studying algorithms"
npx neuroskill label "post-meditation"
npx neuroskill label --json "focus block start"   # returns label_id
```

Автоматично позначати мітки для моментів, коли:
- Користувач повідомляє про прорив або нове розуміння
- Користувач починає новий тип завдання (наприклад, «перехід до перегляду коду»)
- Користувач завершує значущий протокол
- Користувач просить тебе позначити поточний момент
- Відбувається помітна зміна стану (вхід/вихід із потоку)

Мітки зберігаються в базі даних і індексуються для подальшого отримання за допомогою команд `search-labels` та `interactive`.

---
## 7. Real‑Time Streaming
```bash
npx neuroskill listen --seconds 30 --json
npx neuroskill listen --seconds 5 --json | jq '[.[] | select(.event == "scores")]'
```

Потік передає живі події WebSocket (EXG, PPG, IMU, scores, labels) протягом вказаної тривалості. Потрібне підключення WebSocket (не доступне з `--http`).

Використовуй це для сценаріїв безперервного моніторингу або щоб спостерігати зміни метрик у реальному часі під час протоколу.

---
## 8. Візуалізація UMAP
```bash
npx neuroskill umap --json                      # auto: last 2 sessions
npx neuroskill umap --a-start <UTC> --a-end <UTC> --b-start <UTC> --b-end <UTC> --json
```

GPU‑прискорена 3D‑проекція UMAP‑ембеддінгів ZUNA. `separation_score`
вказує, наскільки нейронно відрізняються дві сесії:
- **> 1.5** → Сесії нейронно різні (різні стани мозку)
- **< 0.5** → Подібні стани мозку в обох сесій

---
## 9. Proactive State Awareness

### Перевірка початку сесії
На початку сесії, за бажанням, можна виконати перевірку стану, якщо користувач згадує,
що носить пристрій, або запитує про свій стан:
```bash
npx neuroskill status --json
```

Встав короткий підсумок стану:
> "Швидка перевірка: фокус зростає до 0.62, розслаблення хороше — 0.55, і ваш FAA позитивний — мотивація підходу активна. Схоже, це міцний старт."

### Коли проактивно згадувати стан

Згадуй когнітивний стан **лише** коли:
- Користувач явно запитує («Як я справляюся?», «Перевірте мій фокус»)
- Користувач повідомляє про труднощі з концентрацією, стрес або втому
- Перевищено критичний поріг (сонливість > 0.70, фокус < 0.30 протягом тривалого часу)
- Користувач збирається виконувати когнітивно вимогливе завдання і запитує про готовність

**Не** переривай стан потоку, щоб повідомляти метрики. Якщо фокус > 0.75, захисти
сесію — мовчання є правильним реагуванням.
## 10. Пропонування протоколів

Коли метрики вказують на потребу, пропонуй протокол із `references/protocols.md`.
Завжди запитуй перед початком — ніколи не переривай стан потоку:

> "Твоя концентрація падала протягом останніх 15 хвилин, а TBR піднявся вище 1.5 — ознаки домінування тета та ментальної втоми. Хочеш, щоб я провів тебе через **Theta-Beta Neurofeedback Anchor**? Це 90‑секундна вправа, що використовує ритмічний підрахунок і дихання для придушення тета та підвищення бета."

Ключові тригери:
- **Focus < 0.40, TBR > 1.5** → Theta-Beta Neurofeedback Anchor або Box Breathing
- **Relaxation < 0.30, stress_index high** → Cardiac Coherence або 4-7-8 Breathing
- **Cognitive Load > 0.70 sustained** → Cognitive Load Offload (mind dump)
- **Drowsiness > 0.60** → Ultradian Reset або Wake Reset
- **FAA < 0 (negative)** → FAA Rebalancing
- **Flow State (focus > 0.75, engagement > 0.70)** → Do NOT interrupt
- **High stillness + headache_index** → Neck Release Sequence
- **Low RMSSD (< 25 ms)** → Vagal Toning

---
## 11. Додаткові інструменти

### Таймер фокусування
```bash
npx neuroskill timer --json
```
Запускає вікно Таймера фокусування з пресетами Pomodoro (25/5), Deep Work (50/10) або Short Focus (15/5).

### Калібрування
```bash
npx neuroskill calibrate
npx neuroskill calibrate --profile "Eyes Open"
```
Відкриває вікно калібрування. Корисно, коли якість сигналу низька або користувач хоче встановити персоналізований базовий рівень.

### Сповіщення ОС
```bash
npx neuroskill notify "Break Time" "Your focus has been declining for 20 minutes"
```

### Прямий пропуск Raw JSON
```bash
npx neuroskill raw '{"command":"status"}' --json
```
Для будь‑якої серверної команди, яка ще не прив’язана до підкоманди CLI.
## Обробка помилок

| Помилка | Ймовірна причина | Виправлення |
|-------|-------------|-----|
| `npx neuroskill status` hangs | Додаток NeuroSkill не запущений | Відкрити десктопний додаток NeuroSkill |
| `device.state: "disconnected"` | BCI‑пристрій не підключений | Перевірити Bluetooth, заряд батареї пристрою |
| All scores return 0 | Поганий контакт електродів | Переставити головний ремінець, зволожити електроди |
| `signal_quality` values &lt; 0.7 | Слабко закріплені електроди | Скоригувати посадку, очистити контакти електродів |
| SNR &lt; 3 dB | Шумний сигнал | Мінімізувати рухи голови, перевірити оточення |
| `command not found: npx` | Node.js не встановлений | Встановити Node.js 20+ |
## Приклади взаємодій

**"How am I doing right now?"**
```bash
npx neuroskill status --json
```
→ Інтерпретуй оцінки природно, згадуючи фокус, розслабленість, настрій та будь‑які помітні співвідношення (FAA, TBR). Запропонуй дію лише якщо метрики вказують на потребу.

**"I can't concentrate"**
```bash
npx neuroskill status --json
```
→ Перевір, чи метрики це підтверджують (високий тета, низький бета, зростаючий TBR, висока сонливість).
→ Якщо підтверджено, запропонуй відповідний протокол із `references/protocols.md`.
→ Якщо метрики виглядають нормальними, проблема може бути мотиваційною, а не нейрологічною.

**"Compare my focus today vs yesterday"**
```bash
npx neuroskill compare --json
```
→ Інтерпретуй тенденції, а не лише цифри. Зазнач, що покращилося, що погіршилося та можливі причини.

**"When was I last in a flow state?"**
```bash
npx neuroskill search-labels "flow" --json
npx neuroskill search --json
```
→ Повідом часові мітки, пов’язані метрики та те, чим користувач займався (з міток).

**"How did I sleep?"**
```bash
npx neuroskill sleep --json
```
→ Повідом архітектуру сну (N3 %, REM %, ефективність), порівняй із здоровими орієнтирами та зазнач будь‑які проблеми (висока кількість пробуджень, низький REM).

**"Mark this moment — I just had a breakthrough"**
```bash
npx neuroskill label "breakthrough"
```
→ Підтверди збереження мітки. За бажанням зазнач поточні метрики, щоб запам’ятати стан.
## Посилання

- [NeuroSkill Paper — arXiv:2603.03212](https://arxiv.org/abs/2603.03212) (Kosmyna & Hauptmann, MIT Media Lab)
- [NeuroSkill Desktop App](https://github.com/NeuroSkill-com/skill) (GPLv3)
- [NeuroLoop CLI Companion](https://github.com/NeuroSkill-com/neuroloop) (GPLv3)
- [проект MIT Media Lab](https://www.media.mit.edu/projects/neuroskill/overview/)