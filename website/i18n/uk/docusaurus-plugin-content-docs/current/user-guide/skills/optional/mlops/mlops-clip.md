---
title: "Clip — модель OpenAI, що поєднує зір та мову"
sidebar_label: "Clip"
description: "модель OpenAI, що поєднує зір і мову"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Clip

Модель OpenAI, що поєднує зір та мову. Дозволяє класифікацію зображень zero‑shot, зіставлення зображення‑тексту та крос‑модальний пошук. Навчена на 400 млн пар зображення‑текст. Використовується для пошуку зображень, модерації контенту або завдань зір‑мова без донавчання. Найкраща для загального розуміння зображень.

## Метадані навички

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

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції під час роботи навички.
:::

# CLIP – Contrastive Language-Image Pre-Training

Модель OpenAI, яка розуміє зображення за допомогою природної мови.

## Коли використовувати CLIP

**Використовуй, коли:**
- Класифікація зображень zero‑shot (без потреби у навчальних даних)
- Подібність/зіставлення зображення‑тексту
- Семантичний пошук зображень
- Модерація контенту (виявлення NSFW, насильства)
- Візуальне питання‑відповідь
- Крос‑модальний пошук (зображення→текст, текст→зображення)

**Метрики**:
- **25 300+ зірок на GitHub**
- Навчена на 400 млн пар зображення‑текст
- Порівнюється з ResNet‑50 на ImageNet (zero‑shot)
- Ліцензія MIT

**Використовуй альтернативи**:
- **BLIP-2**: краща генерація підписів
- **LLaVA**: чат зір‑мова
- **Segment Anything**: сегментація зображень

## Швидкий старт

### Встановлення

```bash
pip install git+https://github.com/openai/CLIP.git
pip install torch torchvision ftfy regex tqdm
```

### Класифікація zero‑shot

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

## Доступні моделі

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

## Подібність зображення‑тексту

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

## Семантичний пошук зображень

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

## Модерація контенту

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

## Пакетна обробка

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

## Інтеграція з векторними базами даних

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

## Кращі практики

1. **Використовуй ViT-B/32 у більшості випадків** – хороший баланс
2. **Нормалізуй ембедінги** – необхідно для косинусної схожості
3. **Пакетна обробка** – ефективніше
4. **Кешуй ембедінги** – їх дорого перераховувати
5. **Використовуй описові мітки** – краща продуктивність zero‑shot
6. **GPU рекомендовано** – 10‑50× швидше
7. **Попередня обробка зображень** – використай надану функцію `preprocess`

## Продуктивність

| Operation | CPU | GPU (V100) |
|-----------|-----|------------|
| Image encoding | ~200ms | ~20ms |
| Text encoding | ~50ms | ~5ms |
| Similarity compute | &lt;1ms | &lt;1ms |

## Обмеження

1. **Не підходить для детальних завдань** – найкраще для широких категорій
2. **Потрібен описовий текст** – розмиті мітки працюють погано
3. **Зміщеність на веб‑даних** – можливі упередження набору даних
4. **Немає обмежувальних рамок** – лише ціле зображення
5. **Обмежене просторове розуміння** – слабкі позиція/рахунок

## Ресурси

- **GitHub**: https://github.com/openai/CLIP ⭐ 25,300+
- **Paper**: https://arxiv.org/abs/2103.00020
- **Colab**: https://colab.research.google.com/github/openai/clip/
- **License**: MIT