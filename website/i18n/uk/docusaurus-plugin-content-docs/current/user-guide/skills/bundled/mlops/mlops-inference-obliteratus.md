---
title: "Obliteratus — OBLITERATUS: знищити відмови LLM (diff-in-means)"
sidebar_label: "Obliteratus"
description: "OBLITERATUS: знищити відмови LLM (різниця в середніх)"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Obliteratus

OBLITERATUS: усунути відмови LLM (різниця у середніх).
## Метадані навички

| | |
|---|---|
| Джерело | Bundled (installed by default) |
| Шлях | `skills/mlops/inference/obliteratus` |
| Версія | `2.0.0` |
| Автор | Hermes Agent |
| Ліцензія | MIT |
| Залежності | `obliteratus`, `torch`, `transformers`, `bitsandbytes`, `accelerate`, `safetensors` |
| Платформи | linux, macos |
| Теги | `Abliteration`, `Uncensoring`, `Refusal-Removal`, `LLM`, `Weight-Projection`, `SVD`, `Mechanistic-Interpretability`, `HuggingFace`, `Model-Surgery` |
| Пов’язані навички | `vllm`, `gguf`, [`huggingface-tokenizers`](/docs/user-guide/skills/optional/mlops/mlops-huggingface-tokenizers) |
:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# Навичка OBLITERATUS
## Що всередині

9 методів CLI, 28 модулів аналізу, 116 пресетів моделей у 5 рівнях обчислень, турнірна оцінка та рекомендації, засновані на телеметрії.

Видаляти поведінку відмов (guardrails) з відкритих LLM без повторного навчання чи тонкої настройки. Використовує техніки механістичної інтерпретативності — включаючи diff-in-means, SVD, whitened SVD, LEACE concept erasure, SAE decomposition, Bayesian kernel projection та інші — для ідентифікації та хірургічного вилучення напрямків відмов у вагах моделі, зберігаючи при цьому здатність до міркування.

**Попередження щодо ліцензії:** OBLITERATUS має ліцензію AGPL-3.0. НІКОЛИ не імпортуй його як бібліотеку Python. Завжди виконуй через CLI (`obliteratus` command) або підпроцес. Це зберігає чисту ліцензію MIT Hermes Agent.
## Відео‑провідник

Огляд OBLITERATUS, який використовується агентом Hermes для знищення Gemma:
https://www.youtube.com/watch?v=8fG9BrNTeHs ("OBLITERATUS: An AI Agent Removed Gemma 4's Safety Guardrails")

Корисно, коли користувач хоче отримати візуальний огляд повного робочого процесу перед його запуском.
## Коли використовувати цей інструмент

Тригер, коли користувач:
- Хоче «розцензурувати» або «знищити» LLM
- Питає про видалення відмови/обмежень з моделі
- Хоче створити нецензуровану версію Llama, Qwen, Mistral тощо
- Згадує «видалення відмови», «знищення», «проекція ваги»
- Хоче проаналізувати, як працює механізм відмови моделі
- Посилається на OBLITERATUS, abliterator або напрямки відмови
## Крок 1: Встановлення

Перевір, чи вже встановлено:
```bash
obliteratus --version 2>/dev/null && echo "INSTALLED" || echo "NOT INSTALLED"
```

Якщо не встановлено, клонуй і встанови з GitHub:
```bash
git clone https://github.com/elder-plinius/OBLITERATUS.git
cd OBLITERATUS
pip install -e .
# For Gradio web UI support:
# pip install -e ".[spaces]"
```

**ВАЖЛИВО:** Підтверджуй у користувача перед встановленням. Це завантажить ~5‑10 ГБ залежностей (PyTorch, Transformers, bitsandbytes тощо).
## Крок 2: Перевірка обладнання

Перш ніж щось робити, перевір, який GPU доступний:
```bash
python3 -c "
import torch
if torch.cuda.is_available():
    gpu = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f'GPU: {gpu}')
    print(f'VRAM: {vram:.1f} GB')
    if vram < 4: print('TIER: tiny (models under 1B)')
    elif vram < 8: print('TIER: small (models 1-4B)')
    elif vram < 16: print('TIER: medium (models 4-9B with 4bit quant)')
    elif vram < 32: print('TIER: large (models 8-32B with 4bit quant)')
    else: print('TIER: frontier (models 32B+)')
else:
    print('NO GPU - only tiny models (under 1B) on CPU')
"
```

### Вимоги до VRAM (з 4‑бітовою квантизацією)

| VRAM      | Макс. розмір моделі | Приклади моделей                              |
|:----------|:--------------------|:----------------------------------------------|
| лише CPU  | ~1 млрд параметрів  | GPT‑2, TinyLlama, SmolLM                      |
| 4‑8 ГБ    | ~4 млрд параметрів  | Qwen2.5‑1.5B, Phi‑3.5 mini, Llama 3.2 3B       |
| 8‑16 ГБ   | ~9 млрд параметрів  | Llama 3.1 8B, Mistral 7B, Gemma 2 9B           |
| 24 ГБ     | ~32 млрд параметрів | Qwen3‑32B, Llama 3.1 70B (tight), Command‑R   |
| 48 ГБ+    | ~72 млрд+ параметрів| Qwen2.5‑72B, DeepSeek‑R1                       |
| Multi‑GPU | 200 млрд+ параметрів| Llama 3.1 405B, DeepSeek‑V3 (685 млрд MoE)    |
## Крок 3: Огляд доступних моделей та отримання рекомендацій

```bash
# Browse models by compute tier
obliteratus models --tier medium

# Get architecture info for a specific model
obliteratus info <model_name>

# Get telemetry-driven recommendation for best method & params
obliteratus recommend <model_name>
obliteratus recommend <model_name> --insights  # global cross-architecture rankings
```
## Крок 4: Вибір методу

### Посібник з вибору методу
**За замовчуванням / рекомендовано для більшості випадків: `advanced`.** Використовує багатонаправлену SVD з проекцією, що зберігає норму, і добре протестований.

| Ситуація                           | Рекомендований метод | Чому                                        |
|:-----------------------------------|:----------------------|:--------------------------------------------|
| За замовчуванням / більшість моделей | `advanced`            | Багатонаправлена SVD, збереження норми, надійний |
| Швидке тестування / прототипування | `basic`               | Швидко, просто, достатньо для оцінки       |
| Щільна модель (Llama, Mistral)      | `advanced`            | Багатонаправлена, збереження норми          |
| MoE‑модель (DeepSeek, Mixtral)     | `nuclear`             | Гранульований за експертами, справляється зі складністю MoE |
| Модель розуміння (R1 distills)    | `surgical`            | Підтримує CoT, зберігає ланцюжок міркувань   |
| Стійкі відмови продовжуються       | `aggressive`          | Відбілювана SVD + хірургія голов + jailbreak |
| Потрібні оборотні зміни             | Використовуй вектор керування (див. розділ Analysis) |
| Максимальна якість, час не важливий | `optimized`           | Байєсовий пошук найкращих параметрів       |
| Експериментальне авто‑виявлення   | `informed`            | Автовизначає тип вирівнювання — експериментально, може не перевершувати `advanced` |

### 9 CLI‑методів
- **basic** — Один напрямок відмови через diff‑in‑means. Швидко (~5‑10 хв для 8B).
- **advanced** (DEFAULT, RECOMMENDED) — Кілька напрямків SVD, проекція, що зберігає норму, 2 проходи уточнення. Середня швидкість (~10‑20 хв).
- **aggressive** — Відбілювана SVD + jailbreak‑contrastive + хірургія голов уваги. Вищий ризик пошкодження зв’язності.
- **spectral_cascade** — DCT‑розклад у частотній області. Дослідницький/новий підхід.
- **informed** — Проводить аналіз ПІД ЧАС абляції для авто‑конфігурації. Експериментально — повільніше та менш передбачувано, ніж `advanced`.
- **surgical** — SAE‑фічі + маскування нейронів + хірургія голов + per‑expert. Дуже повільно (~1‑2 год). Найкраще для моделей розуміння.
- **optimized** — Байєсовий пошук гіперпараметрів (Optuna TPE). Найдовший час виконання, але знаходить оптимальні параметри.
- **inverted** — Перевертає напрямок відмови. Модель стає активно готовою виконувати запити.
- **nuclear** — Максимальна сила для впертої MoE‑моделі. Гранульований за експертами.

### Методи вилучення напрямку (прапорець `--direction-method`)
- **diff_means** (за замовчуванням) — Проста різниця середніх між відмовленими/комплайд‑активаціями. Надійно.
- **svd** — Вилучення багатонаправленої SVD. Кращий для складного вирівнювання.
- **leace** — LEACE (Linear Erasure via Closed-form Estimation). Оптимальне лінійне стирання.

### 4 методи лише Python‑API
(НЕ доступні через CLI — вимагають імпорт Python, що порушує межу AGPL. Згадуй користувачу лише за явним запитом використати OBLITERATUS як бібліотеку у власному AGPL‑проекті.)
- failspy, gabliteration, heretic, rdo
## Крок 5: Запуск облітерації

### Стандартне використання
```bash
# Default method (advanced) — recommended for most models
obliteratus obliterate <model_name> --method advanced --output-dir ./abliterated-models

# With 4-bit quantization (saves VRAM)
obliteratus obliterate <model_name> --method advanced --quantization 4bit --output-dir ./abliterated-models

# Large models (70B+) — conservative defaults
obliteratus obliterate <model_name> --method advanced --quantization 4bit --large-model --output-dir ./abliterated-models
```

### Параметри тонкого налаштування
```bash
obliteratus obliterate <model_name> \
  --method advanced \
  --direction-method diff_means \
  --n-directions 4 \
  --refinement-passes 2 \
  --regularization 0.1 \
  --quantization 4bit \
  --output-dir ./abliterated-models \
  --contribute  # opt-in telemetry for community research
```

### Ключові прапорці
| Прапорець | Опис | За замовчуванням |
|:----------|:-----|:-----------------|
| `--method` | Метод облітерації | advanced |
| `--direction-method` | Витяг напрямків | diff_means |
| `--n-directions` | Кількість напрямків відмови (1‑32) | method-dependent |
| `--refinement-passes` | Ітеративні проходи (1‑5) | 2 |
| `--regularization` | Сила регуляризації (0.0‑1.0) | 0.1 |
| `--quantization` | Квантизація у 4‑bit або 8‑bit | none (full precision) |
| `--large-model` | Консервативні налаштування для 120B+ | false |
| `--output-dir` | Куди зберігати облітеровану модель | ./obliterated_model |
| `--contribute` | Поділитися анонімізованими результатами для досліджень | false |
| `--verify-sample-size` | Кількість тестових запитів для перевірки відмови | 20 |
| `--dtype` | Тип даних моделі (float16, bfloat16) | auto |

### Інші режими виконання
```bash
# Interactive guided mode (hardware → model → preset)
obliteratus interactive

# Web UI (Gradio)
obliteratus ui --port 7860

# Run a full ablation study from YAML config
obliteratus run config.yaml --preset quick

# Tournament: pit all methods against each other
obliteratus tourney <model_name>
```
## Крок 6: Перевірка результатів

Після абляції перевірте метрики виходу:

| Метрика | Добре значення | Попередження |
|:-------|:---------------|:--------------|
| Рівень відмов | &lt; 5% (ідеально ~0%) | > 10% означає, що відмови залишаються |
| Зміна perplexity | &lt; 10% збільшення | > 15% означає пошкодження зв’язності |
| KL‑дивергенція | &lt; 0.1 | > 0.5 означає значний зсув розподілу |
| Зв’язність | Висока / проходить якісну перевірку | Погіршені відповіді, повторення |

### Якщо відмови залишаються (> 10%)
1. Спробуй метод `aggressive`
2. Збільш `--n-directions` (наприклад, 8 або 16)
3. Додай `--refinement-passes 3`
4. Спробуй `--direction-method svd` замість `diff_means`

### Якщо зв’язність пошкоджена (perplexity > 15% збільшення)
1. Зменш `--n-directions` (спробуй 2)
2. Збільш `--regularization` (спробуй 0.3)
3. Зменш `--refinement-passes` до 1
4. Спробуй метод `basic` (м’якіший)
## Крок 7: Використати аблятовану модель

Вихід — це стандартний каталог моделі HuggingFace.

```bash
# Test locally with transformers
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
model = AutoModelForCausalLM.from_pretrained('./abliterated-models/<model>')
tokenizer = AutoTokenizer.from_pretrained('./abliterated-models/<model>')
inputs = tokenizer('How do I pick a lock?', return_tensors='pt')
outputs = model.generate(**inputs, max_new_tokens=200)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
"

# Upload to HuggingFace Hub
huggingface-cli upload <username>/<model-name>-abliterated ./abliterated-models/<model>

# Serve with vLLM
vllm serve ./abliterated-models/<model>
```
## CLI Command Reference

| Команда | Опис |
|:--------|:------------|
| `obliteratus obliterate` | Основна команда абляції |
| `obliteratus info <model>` | Вивести деталі архітектури моделі |
| `obliteratus models --tier <tier>` | Переглянути кураторські моделі за обчислювальним рівнем |
| `obliteratus recommend <model>` | Пропозиція методів/параметрів на основі телеметрії |
| `obliteratus interactive` | Майстер налаштування з підказками |
| `obliteratus tourney <model>` | Турнір: усі методи один проти одного |
| `obliteratus run <config.yaml>` | Виконати абляційне дослідження з YAML |
| `obliteratus strategies` | Список усіх зареєстрованих абляційних стратегій |
| `obliteratus report <results.json>` | Перегенерувати візуальні звіти |
| `obliteratus ui` | Запустити веб‑інтерфейс Gradio |
| `obliteratus aggregate` | Підсумувати дані телеметрії спільноти |
## Модулі аналізу

OBLITERATUS включає 28 модулів аналізу для механістичної інтерпретованості.
Дивись `skill_view(name="obliteratus", file_path="references/analysis-modules.md")` для повної довідки.

### Швидкі команди аналізу
```bash
# Run specific analysis modules
obliteratus run analysis-config.yaml --preset quick

# Key modules to run first:
# - alignment_imprint: Fingerprint DPO/RLHF/CAI/SFT alignment method
# - concept_geometry: Single direction vs polyhedral cone
# - logit_lens: Which layer decides to refuse
# - anti_ouroboros: Self-repair risk score
# - causal_tracing: Causally necessary components
```

### Вектори керування (зворотний варіант)
Замість постійної модифікації ваг використай керування під час інференсу:
```python
# Python API only — for user's own projects
from obliteratus.analysis.steering_vectors import SteeringVectorFactory, SteeringHookManager
```
## Стратегії абляції

Окрім абляції, орієнтованої на напрямок, OBLITERATUS включає структурні стратегії абляції:
- **Embedding Ablation** — Видалення компонентів шару вбудовування
- **FFN Ablation** — Видалення блоку мережі прямого проходу (feed-forward network)
- **Head Pruning** — Обрізка attention head (головки уваги)
- **Layer Removal** — Повне видалення шару

Переглянь усі доступні стратегії: `obliteratus strategies`
## Оцінка

- бенчмаркінг рівня відмов
- порівняння perplexity (до/після)
- інтеграція LM Eval Harness для академічних бенчмарків
- порівняння конкурентів один проти одного
- відстеження базової продуктивності
## Підтримка платформ

- **CUDA** — Повна підтримка (NVIDIA GPUs)
- **Apple Silicon (MLX)** — Підтримується через бекенд MLX
- **CPU** — Підтримується для малих моделей (< 1B params)
## Шаблони конфігурації YAML

Завантажуй шаблони для відтворюваних запусків за допомогою `skill_view`:
- `templates/abliteration-config.yaml` — Стандартна конфігурація для однієї моделі
- `templates/analysis-study.yaml` — Дослідження перед аблітерацією
- `templates/batch-abliteration.yaml` — Пакетна обробка декількох моделей
## Телеметрія

OBLITERATUS може за бажанням надсилати анонімізовані дані про запуск у глобальний дослідницький набір даних. Увімкни за допомогою прапорця `--contribute`. Не збираються жодні особисті дані — лише назва моделі, метод і метрики.
## Типові підводні камені

1. **Не використовуйте `informed` за замовчуванням** — це експериментальний режим і працює повільніше. Використовуйте `advanced` для надійних результатів.
2. **Моделі до ~1 млрд параметрів погано реагують на аблітрацію** — їхня поведінка відмови поверхнева і фрагментарна, що ускладнює чисте видобування напрямку. Очікуйте часткові результати (20‑40 % залишкових відмов). Моделі 3 млрд+ мають більш чіткі напрямки відмов і працюють значно краще (часто 0 % відмов з `advanced`).
3. **`aggressive` може погіршити ситуацію** — на малих моделях він може пошкодити зв’язність і навіть підвищити рівень відмов. Використовуйте його лише тоді, коли `advanced` залишає > 10 % відмов у моделі 3 млрд+.
4. **Завжди перевіряйте perplexity** — якщо вона різко підскочить > 15 %, модель пошкоджена. Зменшіть агресивність.
5. **MoE‑моделі потребують спеціального оброблення** — застосовуйте метод `nuclear` для Mixtral, DeepSeek‑MoE тощо.
6. **Квантовані моделі не можна повторно квантувати** — спочатку аблітуйте модель у повній точності, потім квантуйте отриманий результат.
7. **Оцінка VRAM є приблизною** — 4‑бітова квантизація допомагає, проте пікове споживання пам’яті може різко зрости під час видобування.
8. **Моделі розумової обробки чутливі** — використовуйте `surgical` для дистилятів R1, щоб зберегти ланцюжок міркувань.
9. **Перевірте `obliteratus recommend`** — телеметричні дані можуть містити кращі параметри, ніж за замовчуванням.
10. **Ліцензія AGPL** — ніколи не `import obliteratus` у проекти з MIT/Apache ліцензією. Доступно лише через CLI.
11. **Великі моделі (70 млрд+)** — завжди додавайте прапорець `--large-model` для консервативних налаштувань.
12. **Червоний статус спектральної сертифікації поширений** — спектральна перевірка часто позначає «незавершений» навіть коли практичний рівень відмов дорівнює 0 %. Перевіряйте реальний рівень відмов, а не лише спектральну сертифікацію.
## Додаткові навички

- **vllm** — Обслуговувати абляційні моделі з високою пропускною здатністю
- **gguf** — Конвертувати абляційні моделі у GGUF для llama.cpp
- **huggingface-tokenizers** — Працювати з токенізаторами моделей