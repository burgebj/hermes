---
title: "Huggingface Tokenizers — быстрые токенизаторы, оптимизированные для исследований и производства"
sidebar_label: "Huggingface Tokenizers"
description: "Быстрые токенизаторы, оптимизированные для исследований и производства"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Токенизаторы Hugherface

Быстрые токенизаторы, оптимизированные для исследований и продакшн. Реализация на Rust токенизирует 1 ГБ за &lt;20 секунд. Поддерживает алгоритмы BPE, WordPiece и Unigram. Позволяет обучать пользовательские словари, отслеживать выравнивания, работать с паддингом и усечением. Бесшовно интегрируется с transformers. Используй, когда нужна высокопроизводительная токенизация или обучение собственного токенизатора.
## Метаданные навыка

| | |
|---|---|
| Источник | Необязательно — установить командой `hermes skills install official/mlops/huggingface-tokenizers` |
| Путь | `optional-skills/mlops/huggingface-tokenizers` |
| Версия | `1.0.0` |
| Автор | Orchestra Research |
| Лицензия | MIT |
| Зависимости | `tokenizers`, `transformers`, `datasets` |
| Платформы | linux, macos, windows |
| Теги | `Tokenization`, `HuggingFace`, `BPE`, `WordPiece`, `Unigram`, `Fast Tokenization`, `Rust`, `Custom Tokenizer`, `Alignment Tracking`, `Production` |
:::info
Ниже представлено полное определение **skill**, которое Hermes загружает, когда этот **skill** активируется. Это то, что агент видит как инструкции, когда **skill** активен.
:::

# Токенизаторы HuggingFace — быстрая токенизация для NLP

Быстрые, готовые к использованию в продакшн‑окружениях токенизаторы с производительностью Rust и удобством использования Python.
## Когда использовать HuggingFace Tokenizers

**Используй HuggingFace Tokenizers, когда:**
- Требуется чрезвычайно быстрая токенизация (<20 с на 1 ГБ текста)
- Нужно обучать собственные токенизаторы с нуля
- Нужен контроль выравнивания (токен → позиция в оригинальном тексте)
- Создаёшь производственные NLP‑конвейеры
- Требуется эффективно токенизировать большие корпуса

**Производительность**:
- **Скорость**: <20 секунд для токенизации 1 ГБ на CPU
- **Реализация**: ядро на Rust с привязками для Python/Node.js
- **Эффективность**: в 10–100 раз быстрее, чем чисто Python‑реализации

**Используй альтернативы вместо этого**:
- **SentencePiece**: независимый от языка, используется в T5/ALBERT
- **tiktoken**: BPE‑токенизатор OpenAI для моделей GPT
- **transformers AutoTokenizer**: только загрузка предобученных (внутри использует эту библиотеку)
## Быстрый старт

### Установка

```bash
# Install tokenizers
pip install tokenizers

# With transformers integration
pip install tokenizers transformers
```

### Загрузка предобученного токенизатора

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

### Обучение собственного BPE‑токенизатора

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

**Время обучения**: ~1‑2 минуты для корпуса 100 МБ, ~10‑20 минут для 1 ГБ

### Пакетное кодирование с паддингом

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
## Алгоритмы токенизации

### BPE (Byte-Pair Encoding)

**Как работает**:
1. Начинаем со словаря на уровне символов
2. Находим наиболее часто встречающуюся пару символов
3. Объединяем её в новый токен и добавляем в словарь
4. Повторяем, пока не достигнем нужного размера словаря

**Используется в**: GPT‑2, GPT‑3, RoBERTa, BART, DeBERTa

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

**Преимущества**:
- Хорошо обрабатывает OOV‑слова (разбивает их на субслова)
- Гибкий размер словаря
- Подходит для морфологически богатых языков

**Компромиссы**:
- Токенизация зависит от порядка слияний
- Может неожиданно разбивать часто используемые слова

### WordPiece

**Как работает**:
1. Начинаем со словаря символов
2. Оцениваем пары для слияния: `frequency(pair) / (frequency(first) × frequency(second))`
3. Объединяем пару с наивысшим баллом
4. Повторяем, пока не достигнем нужного размера словаря

**Используется в**: BERT, DistilBERT, MobileBERT

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

**Преимущества**:
- Приоритет у осмысленных слияний (высокий балл = семантически связанные)
- Успешно применён в BERT (результаты state‑of‑the‑art)

**Компромиссы**:
- Неизвестные слова становятся `[UNK]`, если нет подходящего субслова
- Сохраняется словарь, а не правила слияний (большие файлы)

### Unigram

**Как работает**:
1. Начинаем с большого словаря (все подстроки)
2. Вычисляем потерю для корпуса с текущим словарём
3. Удаляем токены, минимально влияющие на потерю
4. Повторяем, пока не достигнем нужного размера словаря

**Используется в**: ALBERT, T5, mBART, XLNet (через SentencePiece)

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

**Преимущества**:
- Вероятностный (находит наиболее вероятную токенизацию)
- Хорошо работает для языков без границ слов
- Обрабатывает разнообразные лингвистические контексты

**Компромиссы**:
- Вычислительно затратен при обучении
- Требует настройки большего количества гиперпараметров
## Конвейер токенизации

Полный конвейер: **Normalization → Pre-tokenization → Model → Post-processing**

### Нормализация

Очистка и стандартизация текста:

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

**Распространённые нормализаторы**:
- `NFD`, `NFC`, `NFKD`, `NFKC` — формы нормализации Unicode
- `Lowercase()` — приведение к нижнему регистру
- `StripAccents()` — удаление акцентов (é → e)
- `Strip()` — удаление пробельных символов
- `Replace(pattern, content)` — замена по регулярному выражению

### Претокенизация

Разделение текста на словоподобные единицы:

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

**Распространённые претокенизаторы**:
- `Whitespace()` — разделение по пробелам, табуляциям, переводам строк
- `ByteLevel()` — токенизация на уровне байтов в стиле GPT‑2
- `Punctuation()` — выделение пунктуации
- `Digits(individual_digits=True)` — разбиение цифр по отдельности
- `Metaspace()` — замена пробелов на ▁ (в стиле SentencePiece)

### Постобработка

Добавление специальных токенов для ввода модели:

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

**Распространённые шаблоны**:
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
## Отслеживание выравнивания

Отслеживание позиций токенов в оригинальном тексте:

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

**Сценарии применения**:
- Распознавание именованных сущностей (соотнесение предсказаний с исходным текстом)
- Ответы на вопросы (извлечение фрагментов ответов)
- Классификация токенов (выравнивание меток с оригинальными позициями)
## Интеграция с Transformers

### Загрузка с помощью AutoTokenizer

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

### Преобразование пользовательского токенизатора в Transformers

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
## Общие шаблоны

### Обучение из итератора (большие наборы данных)

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

**Производительность**: Обрабатывает 1 ГБ за ~10‑20 минут

### Включение усечения и дополнения

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

### Многопроцессная обработка

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

**Ускорение**: 5‑8× при 8 ядрах
## Бенчмарки производительности

### Скорость обучения

| Размер корпуса | BPE (30k vocab) | WordPiece (30k) | Unigram (8k) |
|---------------|-----------------|-----------------|--------------|
| 10 МБ         | 15 сек          | 18 сек          | 25 сек       |
| 100 МБ        | 1,5 мин         | 2 мин           | 4 мин        |
| 1 ГБ          | 15 мин          | 20 мин          | 40 мин       |

**Аппаратное обеспечение**: 16‑ядерный CPU, тестировано на английской Wikipedia

### Скорость токенизации

| Реализация      | 1 ГБ корпус | Пропускная способность |
|-----------------|------------|--------------------------|
| Pure Python     | ~20 минут  | ~50 МБ/мин               |
| HF Tokenizers   | ~15 секунд | ~4 ГБ/мин                |
| **Ускорение**   | **80×**    | **80×**                  |

**Тест**: английский текст, средняя длина предложения — 20 слов

### Использование памяти

| Задача                     | Память |
|---------------------------|--------|
| Загрузка токенизатора     | ~10 МБ |
| Обучение BPE (30k vocab)  | ~200 МБ |
| Кодирование 1 М предложений | ~500 МБ |
## Поддерживаемые модели

Предобученные токенизаторы доступны через `from_pretrained()`:

**Семейство BERT**:
- `bert-base-uncased`, `bert-large-cased`
- `distilbert-base-uncased`
- `roberta-base`, `roberta-large`

**Семейство GPT**:
- `gpt2`, `gpt2-medium`, `gpt2-large`
- `distilgpt2`

**Семейство T5**:
- `t5-small`, `t5-base`, `t5-large`
- `google/flan-t5-xxl`

**Прочие**:
- `facebook/bart-base`, `facebook/mbart-large-cc25`
- `albert-base-v2`, `albert-xlarge-v2`
- `xlm-roberta-base`, `xlm-roberta-large`

Просмотреть все: https://huggingface.co/models?library=tokenizers
## Ссылки

- **[Training Guide](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/huggingface-tokenizers/references/training.md)** – обучение пользовательским токенизаторам, настройка тренеров, работа с большими наборами данных
- **[Algorithms Deep Dive](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/huggingface-tokenizers/references/algorithms.md)** – подробное объяснение BPE, WordPiece, Unigram
- **[Pipeline Components](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/huggingface-tokenizers/references/pipeline.md)** – нормализаторы, предтокенизаторы, постпроцессоры, декодеры
- **[Transformers Integration](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/huggingface-tokenizers/references/integration.md)** – AutoTokenizer, PreTrainedTokenizerFast, специальные токены
## Ресурсы

- **Документация**: https://huggingface.co/docs/tokenizers
- **GitHub**: https://github.com/huggingface/tokenizers ⭐ 9 000+
- **Версия**: 0.20.0+
- **Курс**: https://huggingface.co/learn/nlp-course/chapter6/1
- **Научная статья**: BPE (Sennrich et al., 2016), WordPiece (Schuster & Nakajima, 2012)