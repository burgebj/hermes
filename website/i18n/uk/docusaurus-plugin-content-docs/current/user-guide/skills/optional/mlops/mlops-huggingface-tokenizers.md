---
title: "Huggingface Tokenizers — Швидкі токенізатори, оптимізовані для досліджень і виробництва"
sidebar_label: "Huggingface Tokenizers"
description: "Швидкі токенізатори, оптимізовані для досліджень та виробництва"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Токенізатори Huggingface

Швидкі токенізатори, оптимізовані для досліджень та продакшн. Реалізація на Rust токенізує 1 ГБ за &lt;20 секунд. Підтримує алгоритми BPE, WordPiece та Unigram. Тренуй власні словники, відстежуй вирівнювання, працюй з паддінгом/обрізанням. Безшовно інтегрується з transformers. Використовуй, коли потрібна високопродуктивна токенізація або навчання кастомного токенізатора.
## Метадані навички

| | |
|---|---|
| Джерело | Optional — install with `hermes skills install official/mlops/huggingface-tokenizers` |
| Шлях | `optional-skills/mlops/huggingface-tokenizers` |
| Версія | `1.0.0` |
| Автор | Orchestra Research |
| Ліцензія | MIT |
| Залежності | `tokenizers`, `transformers`, `datasets` |
| Платформи | linux, macos, windows |
| Теги | `Tokenization`, `HuggingFace`, `BPE`, `WordPiece`, `Unigram`, `Fast Tokenization`, `Rust`, `Custom Tokenizer`, `Alignment Tracking`, `Production` |
:::info
Нижче наведено повне визначення **skill**, яке Hermes завантажує, коли цей **skill** активовано. Це те, що агент бачить як інструкції, коли **skill** активний.
:::

# Токенізатори HuggingFace — швидка токенізація для NLP

Швидкі, готові до продакшн токенізатори з продуктивністю Rust та зручністю використання Python.
## Коли використовувати HuggingFace Tokenizers

**Використовуй HuggingFace Tokenizers, коли:**
- Потрібна надзвичайно швидка токенізація (<20 секунд на 1 ГБ тексту)
- Навчання власних токенізаторів з нуля
- Потрібне відстеження вирівнювання (токен → позиція у вихідному тексті)
- Створюєш промислові NLP‑конвеєри
- Потрібно ефективно токенізувати великі корпуси

**Продуктивність**:
- **Швидкість**: <20 секунд для токенізації 1 ГБ на CPU
- **Реалізація**: ядро на Rust з прив’язками до Python/Node.js
- **Ефективність**: 10‑100× швидше, ніж чисті Python‑реалізації

**Використовуй альтернативи**:
- **SentencePiece**: мовно‑незалежний, використовується в T5/ALBERT
- **tiktoken**: BPE‑токенізатор OpenAI для моделей GPT
- **transformers AutoTokenizer**: лише завантаження попередньо навчених (внутрішньо використовує цю бібліотеку)
## Швидкий старт

### Встановлення

```bash
# Install tokenizers
pip install tokenizers

# With transformers integration
pip install tokenizers transformers
```

### Завантажити попередньо навчений токенізатор

```python
from tokenizers import Tokenizer

# Load from HuggingFace Hub
tokenizer = Tokenizer.from_pretrained("bert-base-uncased")

# Encode text
output = tokenizer.encode("Hello, how are you?")
print(output.tokens)  # ['hello', ',', 'how', 'are', 'you', '?']
print(output.ids)     # [7592, 1010, 2129, 2024, 2017, 1029]

# Decode back
text = tokenizer.decode(output.ids)
print(text)  # "hello, how are you?"
```

### Навчити власний BPE‑токенізатор

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

# Initialize tokenizer with BPE model
tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
tokenizer.pre_tokenizer = Whitespace()

# Configure trainer
trainer = BpeTrainer(
    vocab_size=30000,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    min_frequency=2
)

# Train on files
files = ["train.txt", "validation.txt"]
tokenizer.train(files, trainer)

# Save
tokenizer.save("my-tokenizer.json")
```

**Час навчання**: ~1-2 хвилини для 100 МБ корпусу, ~10-20 хвилин для 1 ГБ

### Пакетне кодування з паддінгом

```python
# Enable padding
tokenizer.enable_padding(pad_id=3, pad_token="[PAD]")

# Encode batch
texts = ["Hello world", "This is a longer sentence"]
encodings = tokenizer.encode_batch(texts)

for encoding in encodings:
    print(encoding.ids)
# [101, 7592, 2088, 102, 3, 3, 3]
# [101, 2023, 2003, 1037, 2936, 6251, 102]
```
## Алгоритми токенізації

### BPE (Byte-Pair Encoding)

**Як це працює**
1. Почати зі словника на рівні символів
2. Знайти найчастішу пару символів
3. Об’єднати її в новий токен і додати до словника
4. Повторювати, доки не буде досягнуто потрібного розміру словника

**Використовується в**: GPT-2, GPT-3, RoBERTa, BART, DeBERTa

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import ByteLevel

tokenizer = Tokenizer(BPE(unk_token="<|endoftext|>"))
tokenizer.pre_tokenizer = ByteLevel()

trainer = BpeTrainer(
    vocab_size=50257,
    special_tokens=["<|endoftext|>"],
    min_frequency=2
)

tokenizer.train(files=["data.txt"], trainer=trainer)
```

**Переваги**
- Добре працює з OOV‑словами (розбиває їх на субслова)
- Гнучкий розмір словника
- Підходить для морфологічно багатих мов

**Компроміси**
- Токенізація залежить від порядку об’єднань
- Може неочікувано розбивати поширені слова

### WordPiece

**Як це працює**
1. Почати зі словника символів
2. Оцінити пари для об’єднання: `frequency(pair) / (frequency(first) × frequency(second))`
3. Об’єднати пару з найвищим балом
4. Повторювати, доки не буде досягнуто потрібного розміру словника

**Використовується в**: BERT, DistilBERT, MobileBERT

```python
from tokenizers import Tokenizer
from tokenizers.models import WordPiece
from tokenizers.trainers import WordPieceTrainer
from tokenizers.pre_tokenizers import Whitespace
from tokenizers.normalizers import BertNormalizer

tokenizer = Tokenizer(WordPiece(unk_token="[UNK]"))
tokenizer.normalizer = BertNormalizer(lowercase=True)
tokenizer.pre_tokenizer = Whitespace()

trainer = WordPieceTrainer(
    vocab_size=30522,
    special_tokens=["[UNK]", "[CLS]", "[SEP]", "[PAD]", "[MASK]"],
    continuing_subword_prefix="##"
)

tokenizer.train(files=["corpus.txt"], trainer=trainer)
```

**Переваги**
- Пріоритетно об’єднує змістовні пари (високий бал = семантично пов’язані)
- Успішно застосовано в BERT, що дає результати state‑of‑the‑art

**Компроміси**
- Невідомі слова стають `[UNK]`, якщо немає збігів субслова
- Заощаджує лише словник, а не правила об’єднань (більші файли)

### Unigram

**Як це працює**
1. Почати з великого словника (всі підрядки)
2. Обчислити втрату для корпусу за поточним словником
3. Видалити токени з мінімальним впливом на втрату
4. Повторювати, доки не буде досягнуто потрібного розміру словника

**Використовується в**: ALBERT, T5, mBART, XLNet (через SentencePiece)

```python
from tokenizers import Tokenizer
from tokenizers.models import Unigram
from tokenizers.trainers import UnigramTrainer

tokenizer = Tokenizer(Unigram())

trainer = UnigramTrainer(
    vocab_size=8000,
    special_tokens=["<unk>", "<s>", "</s>"],
    unk_token="<unk>"
)

tokenizer.train(files=["data.txt"], trainer=trainer)
```

**Переваги**
- Ймовірнісний (знаходить найімовірнішу токенізацію)
- Добре працює для мов без меж слів
- Обробляє різноманітний лінгвістичний контекст

**Компроміси**
- Витратний у обчисленнях під час навчання
- Потрібно налаштувати більше гіперпараметрів
## Конвеєр токенізації

Повний конвеєр: **Normalization → Pre-tokenization → Model → Post-processing**

### Нормалізація

Очищення та стандартизація тексту:

```python
from tokenizers.normalizers import NFD, StripAccents, Lowercase, Sequence

tokenizer.normalizer = Sequence([
    NFD(),           # Unicode normalization (decompose)
    Lowercase(),     # Convert to lowercase
    StripAccents()   # Remove accents
])

# Input: "Héllo WORLD"
# After normalization: "hello world"
```

**Загальні нормалізатори**:
- `NFD`, `NFC`, `NFKD`, `NFKC` – форми нормалізації Unicode
- `Lowercase()` – Перетворення у нижній регістр
- `StripAccents()` – Видалення акцентів (é → e)
- `Strip()` – Видалення пробілів
- `Replace(pattern, content)` – Заміна за регулярним виразом

### Попередня токенізація

Розбиття тексту на словоподібні одиниці:

```python
from tokenizers.pre_tokenizers import Whitespace, Punctuation, Sequence, ByteLevel

# Split on whitespace and punctuation
tokenizer.pre_tokenizer = Sequence([
    Whitespace(),
    Punctuation()
])

# Input: "Hello, world!"
# After pre-tokenization: ["Hello", ",", "world", "!"]
```

**Загальні попередні токенізатори**:
- `Whitespace()` – Розбиття за пробілами, табуляціями, новими рядками
- `ByteLevel()` – Токенізація у стилі GPT‑2 на рівні байтів
- `Punctuation()` – Відокремлення пунктуації
- `Digits(individual_digits=True)` – Розбиття цифр поодинці
- `Metaspace()` – Заміна пробілів на ▁ (у стилі SentencePiece)

### Пост‑обробка

Додавання спеціальних токенів для входу моделі:

```python
from tokenizers.processors import TemplateProcessing

# BERT-style: [CLS] sentence [SEP]
tokenizer.post_processor = TemplateProcessing(
    single="[CLS] $A [SEP]",
    pair="[CLS] $A [SEP] $B [SEP]",
    special_tokens=[
        ("[CLS]", 1),
        ("[SEP]", 2),
    ],
)
```

**Загальні шаблони**:
```python
# GPT-2: sentence <|endoftext|>
TemplateProcessing(
    single="$A <|endoftext|>",
    special_tokens=[("<|endoftext|>", 50256)]
)

# RoBERTa: <s> sentence </s>
TemplateProcessing(
    single="<s> $A </s>",
    pair="<s> $A </s> </s> $B </s>",
    special_tokens=[("<s>", 0), ("</s>", 2)]
)
```
## Відстеження вирівнювання

Відстеження позицій токенів у вихідному тексті:

```python
output = tokenizer.encode("Hello, world!")

# Get token offsets
for token, offset in zip(output.tokens, output.offsets):
    start, end = offset
    print(f"{token:10} → [{start:2}, {end:2}): {text[start:end]!r}")

# Output:
# hello      → [ 0,  5): 'Hello'
# ,          → [ 5,  6): ','
# world      → [ 7, 12): 'world'
# !          → [12, 13): '!'
```

**Випадки використання**:
- Розпізнавання іменованих сутностей (повернення передбачень у текст)
- Відповіді на питання (видобування діапазонів відповідей)
- Класифікація токенів (вирівнювання міток до оригінальних позицій)
## Інтеграція з transformers

### Завантаження за допомогою AutoTokenizer

```python
from transformers import AutoTokenizer

# AutoTokenizer automatically uses fast tokenizers
tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")

# Check if using fast tokenizer
print(tokenizer.is_fast)  # True

# Access underlying tokenizers.Tokenizer
fast_tokenizer = tokenizer.backend_tokenizer
print(type(fast_tokenizer))  # <class 'tokenizers.Tokenizer'>
```

### Перетворення власного токенізатора у transformers

```python
from tokenizers import Tokenizer
from transformers import PreTrainedTokenizerFast

# Train custom tokenizer
tokenizer = Tokenizer(BPE())
# ... train tokenizer ...
tokenizer.save("my-tokenizer.json")

# Wrap for transformers
transformers_tokenizer = PreTrainedTokenizerFast(
    tokenizer_file="my-tokenizer.json",
    unk_token="[UNK]",
    pad_token="[PAD]",
    cls_token="[CLS]",
    sep_token="[SEP]",
    mask_token="[MASK]"
)

# Use like any transformers tokenizer
outputs = transformers_tokenizer(
    "Hello world",
    padding=True,
    truncation=True,
    max_length=512,
    return_tensors="pt"
)
```
## Типові шаблони

### Навчання з ітератора (великі набори даних)

```python
from datasets import load_dataset

# Load dataset
dataset = load_dataset("wikitext", "wikitext-103-raw-v1", split="train")

# Create batch iterator
def batch_iterator(batch_size=1000):
    for i in range(0, len(dataset), batch_size):
        yield dataset[i:i + batch_size]["text"]

# Train tokenizer
tokenizer.train_from_iterator(
    batch_iterator(),
    trainer=trainer,
    length=len(dataset)  # For progress bar
)
```

**Продуктивність**: Обробляє 1 ГБ за ~10–20 хв

### Увімкнути обрізання та доповнення

```python
# Enable truncation
tokenizer.enable_truncation(max_length=512)

# Enable padding
tokenizer.enable_padding(
    pad_id=tokenizer.token_to_id("[PAD]"),
    pad_token="[PAD]",
    length=512  # Fixed length, or None for batch max
)

# Encode with both
output = tokenizer.encode("This is a long sentence that will be truncated...")
print(len(output.ids))  # 512
```

### Багатопроцесорність

```python
from tokenizers import Tokenizer
from multiprocessing import Pool

# Load tokenizer
tokenizer = Tokenizer.from_file("tokenizer.json")

def encode_batch(texts):
    return tokenizer.encode_batch(texts)

# Process large corpus in parallel
with Pool(8) as pool:
    # Split corpus into chunks
    chunk_size = 1000
    chunks = [corpus[i:i+chunk_size] for i in range(0, len(corpus), chunk_size)]

    # Encode in parallel
    results = pool.map(encode_batch, chunks)
```

**Прискорення**: 5–8× на 8 ядрах
## Бенчмарки продуктивності

### Швидкість навчання

| Розмір корпусу | BPE (30 k vocab) | WordPiece (30 k) | Unigram (8 k) |
|----------------|-------------------|------------------|---------------|
| 10 МБ          | 15 сек            | 18 сек           | 25 сек        |
| 100 МБ         | 1,5 хв            | 2 хв             | 4 хв          |
| 1 ГБ           | 15 хв             | 20 хв            | 40 хв         |

**Обладнання**: 16‑ядерний CPU, тестовано на English Wikipedia

### Швидкість токенізації

| Реалізація      | 1 ГБ корпус | Пропускна здатність |
|-----------------|-------------|----------------------|
| Pure Python     | ~20 хвилин  | ~50 МБ/хв            |
| HF Tokenizers   | ~15 секунд  | ~4 ГБ/хв             |
| **Прискорення** | **80×**     | **80×**              |

**Тест**: English text, середня довжина речення — 20 слів

### Використання пам’яті

| Завдання                | Пам’ять |
|------------------------|----------|
| Завантаження токенізатора | ~10 МБ   |
| Навчання BPE (30 k vocab) | ~200 МБ |
| Кодування 1 млн речень   | ~500 МБ |
## Підтримувані моделі

Попередньо навчені токенізатори доступні через `from_pretrained()`:

**Родина BERT**:
- `bert-base-uncased`, `bert-large-cased`
- `distilbert-base-uncased`
- `roberta-base`, `roberta-large`

**Родина GPT**:
- `gpt2`, `gpt2-medium`, `gpt2-large`
- `distilgpt2`

**Родина T5**:
- `t5-small`, `t5-base`, `t5-large`
- `google/flan-t5-xxl`

**Інші**:
- `facebook/bart-base`, `facebook/mbart-large-cc25`
- `albert-base-v2`, `albert-xlarge-v2`
- `xlm-roberta-base`, `xlm-roberta-large`

Переглянути всі: https://huggingface.co/models?library=tokenizers
## Посилання

- **[Посібник з навчання](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/huggingface-tokenizers/references/training.md)** – Навчання власних токенізаторів, налаштування тренерів, обробка великих наборів даних
- **[Глибокий аналіз алгоритмів](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/huggingface-tokenizers/references/algorithms.md)** – Детальне пояснення BPE, WordPiece, Unigram
- **[Компоненти конвеєра](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/huggingface-tokenizers/references/pipeline.md)** – Нормалізатори, передтокенізатори, постпроцесори, декодери
- **[Інтеграція з Transformers](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/huggingface-tokenizers/references/integration.md)** – AutoTokenizer, PreTrainedTokenizerFast, спеціальні токени
## Ресурси

- **Документація**: https://huggingface.co/docs/tokenizers
- **GitHub**: https://github.com/huggingface/tokenizers ⭐ 9 000+
- **Версія**: 0.20.0+
- **Курс**: https://huggingface.co/learn/nlp-course/chapter6/1
- **Наукова стаття**: BPE (Sennrich et al., 2016), WordPiece (Schuster & Nakajima, 2012)