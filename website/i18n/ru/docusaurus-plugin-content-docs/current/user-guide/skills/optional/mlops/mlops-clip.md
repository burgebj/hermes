---
title: "Clip — модель OpenAI, соединяющая зрение и язык"
sidebar_label: "Clip"
description: "Модель OpenAI, соединяющая зрение и язык"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Clip

Модель OpenAI, соединяющая зрение и язык. Позволяет выполнять классификацию изображений без обучения, сопоставление изображений и текста, а также кросс‑модальное извлечение. Обучена на 400 млн пар изображение‑текст. Используется для поиска изображений, модерации контента или задач зрительно‑языкового взаимодействия без дообучения. Лучшее решение для универсального понимания изображений.

## Метаданные навыка

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/clip` |
| Path | `optional-skills/mlops/clip` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `transformers`, `torch`, `pillow` |
| Platforms | linux, macos, windows |
| Tags | `Multimodal`, `CLIP`, `Vision-Language`, `Zero-Shot`, `Image Classification`, `OpenAI`, `Image Search`, `Cross-Modal Retrieval`, `Content Moderation` |

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает при срабатывании этого навыка. Это то, что агент видит как инструкции, когда навык активен.
:::

# CLIP — Contrastive Language-Image Pre-Training

Модель OpenAI, понимающая изображения через естественный язык.

## Когда использовать CLIP

**Используй, когда:**
- Классификация изображений без обучения (zero-shot)
- Сопоставление изображений и текста
- Семантический поиск изображений
- Модерация контента (обнаружение NSFW, насилия)
- Визуальные вопросы‑ответы
- Кросс‑модальное извлечение (изображение→текст, текст→изображение)

**Метрики**:
- **25 300+ звёзд на GitHub**
- Обучена на 400 млн пар изображение‑текст
- Сопоставима с ResNet‑50 на ImageNet (zero-shot)
- MIT License

**Используй альтернативы вместо этого**:
- **BLIP-2**: Лучшее создание подписей
- **LLaVA**: Чат зрительно‑языковой
- **Segment Anything**: Сегментация изображений

## Быстрый старт

### Установка

```bash
pip install git+https://github.com/openai/CLIP.git
pip install torch torchvision ftfy regex tqdm
```

### Классификация zero-shot

```python
import torch
import clip
from PIL import Image

# Load model
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

# Load image
image = preprocess(Image.open("photo.jpg")).unsqueeze(0).to(device)

# Define possible labels
text = clip.tokenize(["a dog", "a cat", "a bird", "a car"]).to(device)

# Compute similarity
with torch.no_grad():
    image_features = model.encode_image(image)
    text_features = model.encode_text(text)

    # Cosine similarity
    logits_per_image, logits_per_text = model(image, text)
    probs = logits_per_image.softmax(dim=-1).cpu().numpy()

# Print results
labels = ["a dog", "a cat", "a bird", "a car"]
for label, prob in zip(labels, probs[0]):
    print(f"{label}: {prob:.2%}")
```

## Доступные модели

```python
# Models (sorted by size)
models = [
    "RN50",           # ResNet-50
    "RN101",          # ResNet-101
    "ViT-B/32",       # Vision Transformer (recommended)
    "ViT-B/16",       # Better quality, slower
    "ViT-L/14",       # Best quality, slowest
]

model, preprocess = clip.load("ViT-B/32")
```

| Model | Parameters | Speed | Quality |
|-------|------------|-------|---------|
| RN50 | 102M | Fast | Good |
| ViT-B/32 | 151M | Medium | Better |
| ViT-L/14 | 428M | Slow | Best |

## Сходство изображение‑текст

```python
# Compute embeddings
image_features = model.encode_image(image)
text_features = model.encode_text(text)

# Normalize
image_features /= image_features.norm(dim=-1, keepdim=True)
text_features /= text_features.norm(dim=-1, keepdim=True)

# Cosine similarity
similarity = (image_features @ text_features.T).item()
print(f"Similarity: {similarity:.4f}")
```

## Семантический поиск изображений

```python
# Index images
image_paths = ["img1.jpg", "img2.jpg", "img3.jpg"]
image_embeddings = []

for img_path in image_paths:
    image = preprocess(Image.open(img_path)).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model.encode_image(image)
        embedding /= embedding.norm(dim=-1, keepdim=True)
    image_embeddings.append(embedding)

image_embeddings = torch.cat(image_embeddings)

# Search with text query
query = "a sunset over the ocean"
text_input = clip.tokenize([query]).to(device)
with torch.no_grad():
    text_embedding = model.encode_text(text_input)
    text_embedding /= text_embedding.norm(dim=-1, keepdim=True)

# Find most similar images
similarities = (text_embedding @ image_embeddings.T).squeeze(0)
top_k = similarities.topk(3)

for idx, score in zip(top_k.indices, top_k.values):
    print(f"{image_paths[idx]}: {score:.3f}")
```

## Модерация контента

```python
# Define categories
categories = [
    "safe for work",
    "not safe for work",
    "violent content",
    "graphic content"
]

text = clip.tokenize(categories).to(device)

# Check image
with torch.no_grad():
    logits_per_image, _ = model(image, text)
    probs = logits_per_image.softmax(dim=-1)

# Get classification
max_idx = probs.argmax().item()
max_prob = probs[0, max_idx].item()

print(f"Category: {categories[max_idx]} ({max_prob:.2%})")
```

## Пакетная обработка

```python
# Process multiple images
images = [preprocess(Image.open(f"img{i}.jpg")) for i in range(10)]
images = torch.stack(images).to(device)

with torch.no_grad():
    image_features = model.encode_image(images)
    image_features /= image_features.norm(dim=-1, keepdim=True)

# Batch text
texts = ["a dog", "a cat", "a bird"]
text_tokens = clip.tokenize(texts).to(device)

with torch.no_grad():
    text_features = model.encode_text(text_tokens)
    text_features /= text_features.norm(dim=-1, keepdim=True)

# Similarity matrix (10 images × 3 texts)
similarities = image_features @ text_features.T
print(similarities.shape)  # (10, 3)
```

## Интеграция с векторными базами данных

```python
# Store CLIP embeddings in Chroma/FAISS
import chromadb

client = chromadb.Client()
collection = client.create_collection("image_embeddings")

# Add image embeddings
for img_path, embedding in zip(image_paths, image_embeddings):
    collection.add(
        embeddings=[embedding.cpu().numpy().tolist()],
        metadatas=[{"path": img_path}],
        ids=[img_path]
    )

# Query with text
query = "a sunset"
text_embedding = model.encode_text(clip.tokenize([query]))
results = collection.query(
    query_embeddings=[text_embedding.cpu().numpy().tolist()],
    n_results=5
)
```

## Лучшие практики

1. **Используй ViT-B/32 в большинстве случаев** — хороший баланс
2. **Нормализуй эмбеддинги** — требуется для косинусного сходства
3. **Пакетная обработка** — более эффективно
4. **Кешируй эмбеддинги** — их пересчёт дорогой
5. **Используй описательные метки** — лучшая производительность zero-shot
6. **GPU рекомендуется** — 10‑50× быстрее
7. **Предобрабатывай изображения** — используй предоставленную функцию предобработки

## Производительность

| Operation | CPU | GPU (V100) |
|-----------|-----|------------|
| Image encoding | ~200ms | ~20ms |
| Text encoding | ~50ms | ~5ms |
| Similarity compute | &lt;1ms | &lt;1ms |

## Ограничения

1. **Не подходит для тонко‑детализированных задач** — лучше для широких категорий
2. **Требует описательного текста** — расплывчатые метки работают плохо
3. **Смещение из веб‑данных** — возможны предвзятости набора данных
4. **Нет ограничивающих рамок** — только полное изображение
5. **Ограниченное пространственное понимание** — слаб в позиционировании/подсчёте

## Ресурсы

- **GitHub**: https://github.com/openai/CLIP ⭐ 25,300+
- **Paper**: https://arxiv.org/abs/2103.00020
- **Colab**: https://colab.research.google.com/github/openai/clip/
- **License**: MIT