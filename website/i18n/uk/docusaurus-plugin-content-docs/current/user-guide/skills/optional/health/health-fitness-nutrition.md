---
title: "Fitness Nutrition — планувальник тренувань у залі та трекер харчування"
sidebar_label: "Fitness Nutrition"
description: "Планувальник тренувань у спортзалі та трекер харчування"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Фітнес і харчування

Планувальник тренувань у залі та трекер харчування. Пошук 690 + вправ за м’язом, обладнанням або категорією через wger. Переглядай макроси та калорії для 380 000 + продуктів через USDA FoodData Central. Обчислюй ІМТ, TDEE, одноповторний максимум, розподіл макросів та відсоток жиру — чистий Python, без встановлення pip. Створено для всіх, хто прагне набору маси, схуднення або просто хоче краще харчуватись.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/health/fitness-nutrition` |
| Path | `optional-skills/health/fitness-nutrition` |
| Version | `1.0.0` |
| License | MIT |
| Platforms | linux, macos, windows |
| Tags | `health`, `fitness`, `nutrition`, `gym`, `workout`, `diet`, `exercise` |

## Reference: full SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Фітнес & Харчування

Експертний тренер з фітнесу та спортивний дієтолог. Два джерела даних
плюс офлайн‑калькулятори — все, що потрібне любителю залу, в одному місці.

**Джерела даних (усі безкоштовні, без залежностей pip):**

- **wger** (https://wger.de/api/v2/) — відкрита база вправ, 690 + вправ з м’язами, обладнанням, зображеннями. Публічні ендпоінти не потребують автентифікації.
- **USDA FoodData Central** (https://api.nal.usda.gov/fdc/v1/) — державна база даних харчування США, 380 000 + продуктів. `DEMO_KEY` працює одразу; безкоштовна реєстрація — підвищені ліміти.

**Офлайн‑калькулятори (чистий stdlib Python):**

- ІМТ, TDEE (Mifflin‑St Jeor), одноповторний максимум (Epley/Brzycki/Lombardi), розподіл макросів, відсоток жиру (метод US Navy)

---

## Коли використовувати

Використовуй цей навик, коли користувач запитує про:
- Вправи, тренування, зал‑рутини, групи м’язів, розподіл тренувань
- Макроси їжі, калорії, вміст білка, планування прийомів їжі, підрахунок калорій
- Склад тіла: ІМТ, відсоток жиру, TDEE, надлишок/дефіцит калорій
- Оцінки одноповторного максимуму, відсотки навантаження, прогресивне перевантаження
- Співвідношення макросів для схуднення, набору маси або підтримки

---

## Процедура

### Пошук вправ (wger API)

Усі публічні ендпоінти wger повертають JSON і не вимагають auth. Завжди додавай
`format=json` і `language=2` (англійська) до запитів.

**Крок 1 — Визнач, що саме потрібно користувачеві:**

- За м’язом → ` /api/v2/exercise/?muscles={id}&language=2&status=2&format=json`
- За категорією → ` /api/v2/exercise/?category={id}&language=2&status=2&format=json`
- За обладнанням → ` /api/v2/exercise/?equipment={id}&language=2&status=2&format=json`
- За назвою → ` /api/v2/exercise/search/?term={query}&language=english&format=json`
- Повна інформація → ` /api/v2/exerciseinfo/{exercise_id}/?format=json`

**Крок 2 — Таблиці ідентифікаторів (щоб не робити зайві запити):**

Категорії вправ:

| ID | Категорія |
|----|-----------|
| 8  | Arms |
| 9  | Legs |
| 10 | Abs |
| 11 | Chest |
| 12 | Back |
| 13 | Shoulders |
| 14 | Calves |
| 15 | Cardio |

М’язи:

| ID | М’яз | ID | М’яз |
|----|------|----|------|
| 1  | Biceps brachii | 2  | Anterior deltoid |
| 3  | Serratus anterior | 4  | Pectoralis major |
| 5  | Obliquus externus | 6  | Gastrocnemius |
| 7  | Rectus abdominis | 8  | Gluteus maximus |
| 9  | Trapezius | 10 | Quadriceps femoris |
| 11 | Biceps femoris | 12 | Latissimus dorsi |
| 13 | Brachialis | 14 | Triceps brachii |
| 15 | Soleus |    |   |

Обладнання:

| ID | Обладнання |
|----|------------|
| 1  | Barbell |
| 3  | Dumbbell |
| 4  | Gym mat |
| 5  | Swiss Ball |
| 6  | Pull-up bar |
| 7  | none (bodyweight) |
| 8  | Bench |
| 9  | Incline bench |
| 10 | Kettlebell |

**Крок 3 — Отримай та представи результати:**

```bash
# Search exercises by name
QUERY="$1"
ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$QUERY")
curl -s "https://wger.de/api/v2/exercise/search/?term=${ENCODED}&language=english&format=json" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
for s in data.get('suggestions',[])[:10]:
    d=s.get('data',{})
    print(f\"  ID {d.get('id','?'):>4} | {d.get('name','N/A'):<35} | Category: {d.get('category','N/A')}\")
"
```

```bash
# Get full details for a specific exercise
EXERCISE_ID="$1"
curl -s "https://wger.de/api/v2/exerciseinfo/${EXERCISE_ID}/?format=json" \
  | python3 -c "
import json,sys,html,re
data=json.load(sys.stdin)
trans=[t for t in data.get('translations',[]) if t.get('language')==2]
t=trans[0] if trans else data.get('translations',[{}])[0]
desc=re.sub('<[^>]+>','',html.unescape(t.get('description','N/A')))
print(f\"Exercise  : {t.get('name','N/A')}\")
print(f\"Category  : {data.get('category',{}).get('name','N/A')}\")
print(f\"Primary   : {', '.join(m.get('name_en','') for m in data.get('muscles',[])) or 'N/A'}\")
print(f\"Secondary : {', '.join(m.get('name_en','') for m in data.get('muscles_secondary',[])) or 'none'}\")
print(f\"Equipment : {', '.join(e.get('name','') for e in data.get('equipment',[])) or 'bodyweight'}\")
print(f\"How to    : {desc[:500]}\")
imgs=data.get('images',[])
if imgs: print(f\"Image     : {imgs[0].get('image','')}\")
"
```

```bash
# List exercises filtering by muscle, category, or equipment
# Combine filters as needed: ?muscles=4&equipment=1&language=2&status=2
FILTER="$1"  # e.g. "muscles=4" or "category=11" or "equipment=3"
curl -s "https://wger.de/api/v2/exercise/?${FILTER}&language=2&status=2&limit=20&format=json" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
print(f'Found {data.get(\"count\",0)} exercises.')
for ex in data.get('results',[]):
    print(f\"  ID {ex['id']:>4} | muscles: {ex.get('muscles',[])} | equipment: {ex.get('equipment',[])}\")
"
```

### Пошук продуктів (USDA FoodData Central)

Використовує змінну середовища `USDA_API_KEY`, якщо вона встановлена, інакше переходить на `DEMO_KEY`.
`DEMO_KEY` — 30 запитів/годину. Безкоштовний ключ після реєстрації — 1 000 запитів/годину.

```bash
# Search foods by name
FOOD="$1"
API_KEY="${USDA_API_KEY:-DEMO_KEY}"
ENCODED=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$FOOD")
curl -s "https://api.nal.usda.gov/fdc/v1/foods/search?api_key=${API_KEY}&query=${ENCODED}&pageSize=5&dataType=Foundation,SR%20Legacy" \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
foods=data.get('foods',[])
if not foods: print('No foods found.'); sys.exit()
for f in foods:
    n={x['nutrientName']:x.get('value','?') for x in f.get('foodNutrients',[])}
    cal=n.get('Energy','?'); prot=n.get('Protein','?')
    fat=n.get('Total lipid (fat)','?'); carb=n.get('Carbohydrate, by difference','?')
    print(f\"{f.get('description','N/A')}\")
    print(f\"  Per 100g: {cal} kcal | {prot}g protein | {fat}g fat | {carb}g carbs\")
    print(f\"  FDC ID: {f.get('fdcId','N/A')}\")
    print()
"
```

```bash
# Detailed nutrient profile by FDC ID
FDC_ID="$1"
API_KEY="${USDA_API_KEY:-DEMO_KEY}"
curl -s "https://api.nal.usda.gov/fdc/v1/food/${FDC_ID}?api_key=${API_KEY}" \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(f\"Food: {d.get('description','N/A')}\")
print(f\"{'Nutrient':<40} {'Amount':>8} {'Unit'}\")
print('-'*56)
for x in sorted(d.get('foodNutrients',[]),key=lambda x:x.get('nutrient',{}).get('rank',9999)):
    nut=x.get('nutrient',{}); amt=x.get('amount',0)
    if amt and float(amt)>0:
        print(f\"  {nut.get('name',''):<38} {amt:>8} {nut.get('unitName','')}\")
"
```

### Офлайн‑калькулятори

Використовуй допоміжні скрипти в `scripts/` для пакетних операцій або запускай їх окремо:

- `python3 scripts/body_calc.py bmi <weight_kg> <height_cm>`
- `python3 scripts/body_calc.py tdee <weight_kg> <height_cm> <age> <M|F> <activity 1-5>`
- `python3 scripts/body_calc.py 1rm <weight> <reps>`
- `python3 scripts/body_calc.py macros <tdee_kcal> <cut|maintain|bulk>`
- `python3 scripts/body_calc.py bodyfat <M|F> <neck_cm> <waist_cm> [hip_cm] <height_cm>`

Дивись `references/FORMULAS.md` для наукового обґрунтування кожної формули.

---

## Підводні камені

- Ендпоінт wger `/exercise` повертає **усі мови за замовчуванням** — завжди додавай `language=2` для англійської.
- wger містить **неперевірені користувацькі внески** — додавай `status=2`, щоб отримати лише схвалені вправи.
- `DEMO_KEY` USDA має **30 запитів/годину** — став `sleep 2` між пакетними запитами або отримай безкоштовний ключ.
- Дані USDA подані **на 100 г** — нагадуй користувачам масштабувати до реальної порції.
- ІМТ не розрізняє м’язову та жирову масу — високий ІМТ у м’язистих людей не обов’язково означає нездоров’я.
- Формули відсотка жиру — **оцінки** (±3‑5 %) — радь DEXA‑сканування для точності.
- Формули 1RM втрачають точність понад 10 повторень — використовуйте підходи 3‑5 повторень для кращих оцінок.
- Ендпоінт wger `exercise/search` приймає параметр `term`, а не `query`.

---

## Перевірка

Після пошуку вправ: переконайся, що результати містять назву вправи, групу м’язів та обладнання.
Після пошуку продуктів: переконайся, що повертаються макроси на 100 г разом з ккал, білком, жиром, вуглеводами.
Після використання калькуляторів: швидко перевір результати (наприклад, TDEE має бути в діапазоні 1500‑3500 ккал для більшості дорослих).

---

## Швидка довідка

| Завдання | Джерело | Ендпоінт |
|----------|---------|----------|
| Пошук вправ за назвою | wger | `GET /api/v2/exercise/search/?term=&language=english` |
| Деталі вправи | wger | `GET /api/v2/exerciseinfo/{id}/` |
| Фільтр за м’язом | wger | `GET /api/v2/exercise/?muscles={id}&language=2&status=2` |
| Фільтр за обладнанням | wger | `GET /api/v2/exercise/?equipment={id}&language=2&status=2` |
| Список категорій | wger | `GET /api/v2/exercisecategory/` |
| Список м’язів | wger | `GET /api/v2/muscle/` |
| Пошук продуктів | USDA | `GET /fdc/v1/foods/search?query=&dataType=Foundation,SR Legacy` |
| Деталі продукту | USDA | `GET /fdc/v1/food/{fdcId}` |
| ІМТ / TDEE / 1RM / макроси | offline | `python3 scripts/body_calc.py` |