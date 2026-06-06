---
title: "Модель сегментации любого изображения — SAM: сегментация zero-shot с помощью точек, прямоугольников, масок"
sidebar_label: "Segment Anything Model"
description: "сегментация изображений без обучения с помощью точек, прямоугольников, масок"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Segment Anything Model

SAM: zero‑shot сегментация изображений с помощью точек, прямоугольников, масок.

## Метаданные навыка

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/mlops/models/segment-anything` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `segment-anything`, `transformers>=4.30.0`, `torch>=1.7.0` |
| Platforms | linux, macos, windows |
| Tags | `Multimodal`, `Image Segmentation`, `Computer Vision`, `SAM`, `Zero-Shot` |

## Ссылка: полный SKILL.md

:::info
Ниже приведено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# Segment Anything Model (SAM)

Полное руководство по использованию Segment Anything Model от Meta AI для zero‑shot сегментации изображений.

## Когда использовать SAM

**Используй SAM, когда:**
- Нужно сегментировать любой объект на изображениях без обучения под конкретную задачу
- Создаёшь интерактивные инструменты разметки с подсказками‑точками/‑прямоугольниками
- Генерируешь обучающие данные для других моделей компьютерного зрения
- Требуется zero‑shot перенос на новые домены изображений
- Строишь конвейеры обнаружения/сегментации объектов
- Обрабатываешь медицинские, спутниковые или специализированные изображения

**Ключевые особенности:**
- **Zero‑shot сегментация**: Работает в любой доменной области без дообучения
- **Гибкие подсказки**: Точки, ограничивающие рамки или предыдущие маски
- **Автоматическая сегментация**: Генерирует все маски объектов автоматически
- **Высокое качество**: Обучена на 1,1 млрд масок из 11 млн изображений
- **Несколько размеров модели**: ViT‑B (самая быстрая), ViT‑L, ViT‑H (самая точная)
- **Экспорт в ONNX**: Развёртывание в браузерах и на edge‑устройствах

**Используй альтернативы вместо:**
- **YOLO/Detectron2**: Для реального времени обнаружения объектов с классами
- **Mask2Former**: Для семантической/паноптической сегментации с категориями
- **GroundingDINO + SAM**: Для сегментации по текстовым подсказкам
- **SAM 2**: Для задач видеосегментации

## Быстрый старт

### Установка

```bash
# From GitHub
pip install git+https://github.com/facebookresearch/segment-anything.git

# Optional dependencies
pip install opencv-python pycocotools matplotlib

# Or use HuggingFace transformers
pip install transformers
```

### Скачивание контрольных точек

```bash
# ViT-H (largest, most accurate) - 2.4GB
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth

# ViT-L (medium) - 1.2GB
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth

# ViT-B (smallest, fastest) - 375MB
wget https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
```

### Базовое использование с SamPredictor

```python
import numpy as np
from segment_anything import sam_model_registry, SamPredictor

# Load model
sam = sam_model_registry["vit_h"](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/models/segment-anything/checkpoint="sam_vit_h_4b8939.pth")
sam.to(device="cuda")

# Create predictor
predictor = SamPredictor(sam)

# Set image (computes embeddings once)
image = cv2.imread("image.jpg")
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
predictor.set_image(image)

# Predict with point prompts
input_point = np.array([[500, 375]])  # (x, y) coordinates
input_label = np.array([1])  # 1 = foreground, 0 = background

masks, scores, logits = predictor.predict(
    point_coords=input_point,
    point_labels=input_label,
    multimask_output=True  # Returns 3 mask options
)

# Select best mask
best_mask = masks[np.argmax(scores)]
```

### HuggingFace Transformers

```python
import torch
from PIL import Image
from transformers import SamModel, SamProcessor

# Load model and processor
model = SamModel.from_pretrained("facebook/sam-vit-huge")
processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")
model.to("cuda")

# Process image with point prompt
image = Image.open("image.jpg")
input_points = [[[450, 600]]]  # Batch of points

inputs = processor(image, input_points=input_points, return_tensors="pt")
inputs = {k: v.to("cuda") for k, v in inputs.items()}

# Generate masks
with torch.no_grad():
    outputs = model(**inputs)

# Post-process masks to original size
masks = processor.image_processor.post_process_masks(
    outputs.pred_masks.cpu(),
    inputs["original_sizes"].cpu(),
    inputs["reshaped_input_sizes"].cpu()
)
```

## Основные концепции

### Архитектура модели

<!-- ascii-guard-ignore -->
<!-- ascii-guard-ignore -->
```
SAM Architecture:
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Image Encoder  │────▶│ Prompt Encoder  │────▶│  Mask Decoder   │
│     (ViT)       │     │ (Points/Boxes)  │     │ (Transformer)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
   Image Embeddings      Prompt Embeddings         Masks + IoU
   (computed once)       (per prompt)             predictions
```
<!-- ascii-guard-ignore-end -->
<!-- ascii-guard-ignore-end -->

### Варианты модели

| Model | Checkpoint | Size | Speed | Accuracy |
|-------|------------|------|-------|----------|
| ViT-H | `vit_h` | 2.4 GB | Slowest | Best |
| ViT-L | `vit_l` | 1.2 GB | Medium | Good |
| ViT-B | `vit_b` | 375 MB | Fastest | Good |

### Типы подсказок

| Prompt | Description | Use Case |
|--------|-------------|----------|
| Point (foreground) | Click on object | Single object selection |
| Point (background) | Click outside object | Exclude regions |
| Bounding box | Rectangle around object | Larger objects |
| Previous mask | Low‑res mask input | Iterative refinement |

## Интерактивная сегментация

### Точечные подсказки

```python
# Single foreground point
input_point = np.array([[500, 375]])
input_label = np.array([1])

masks, scores, logits = predictor.predict(
    point_coords=input_point,
    point_labels=input_label,
    multimask_output=True
)

# Multiple points (foreground + background)
input_points = np.array([[500, 375], [600, 400], [450, 300]])
input_labels = np.array([1, 1, 0])  # 2 foreground, 1 background

masks, scores, logits = predictor.predict(
    point_coords=input_points,
    point_labels=input_labels,
    multimask_output=False  # Single mask when prompts are clear
)
```

### Прямоугольные подсказки

```python
# Bounding box [x1, y1, x2, y2]
input_box = np.array([425, 600, 700, 875])

masks, scores, logits = predictor.predict(
    box=input_box,
    multimask_output=False
)
```

### Сочетанные подсказки

```python
# Box + points for precise control
masks, scores, logits = predictor.predict(
    point_coords=np.array([[500, 375]]),
    point_labels=np.array([1]),
    box=np.array([400, 300, 700, 600]),
    multimask_output=False
)
```

### Итеративное уточнение

```python
# Initial prediction
masks, scores, logits = predictor.predict(
    point_coords=np.array([[500, 375]]),
    point_labels=np.array([1]),
    multimask_output=True
)

# Refine with additional point using previous mask
masks, scores, logits = predictor.predict(
    point_coords=np.array([[500, 375], [550, 400]]),
    point_labels=np.array([1, 0]),  # Add background point
    mask_input=logits[np.argmax(scores)][None, :, :],  # Use best mask
    multimask_output=False
)
```

## Автоматическое создание масок

### Базовая автоматическая сегментация

```python
from segment_anything import SamAutomaticMaskGenerator

# Create generator
mask_generator = SamAutomaticMaskGenerator(sam)

# Generate all masks
masks = mask_generator.generate(image)

# Each mask contains:
# - segmentation: binary mask
# - bbox: [x, y, w, h]
# - area: pixel count
# - predicted_iou: quality score
# - stability_score: robustness score
# - point_coords: generating point
```

### Настраиваемая генерация

```python
mask_generator = SamAutomaticMaskGenerator(
    model=sam,
    points_per_side=32,          # Grid density (more = more masks)
    pred_iou_thresh=0.88,        # Quality threshold
    stability_score_thresh=0.95,  # Stability threshold
    crop_n_layers=1,             # Multi-scale crops
    crop_n_points_downscale_factor=2,
    min_mask_region_area=100,    # Remove tiny masks
)

masks = mask_generator.generate(image)
```

### Фильтрация масок

```python
# Sort by area (largest first)
masks = sorted(masks, key=lambda x: x['area'], reverse=True)

# Filter by predicted IoU
high_quality = [m for m in masks if m['predicted_iou'] > 0.9]

# Filter by stability score
stable_masks = [m for m in masks if m['stability_score'] > 0.95]
```

## Пакетный вывод

### Несколько изображений

```python
# Process multiple images efficiently
images = [cv2.imread(f"image_{i}.jpg") for i in range(10)]

all_masks = []
for image in images:
    predictor.set_image(image)
    masks, _, _ = predictor.predict(
        point_coords=np.array([[500, 375]]),
        point_labels=np.array([1]),
        multimask_output=True
    )
    all_masks.append(masks)
```

### Несколько подсказок на изображение

```python
# Process multiple prompts efficiently (one image encoding)
predictor.set_image(image)

# Batch of point prompts
points = [
    np.array([[100, 100]]),
    np.array([[200, 200]]),
    np.array([[300, 300]])
]

all_masks = []
for point in points:
    masks, scores, _ = predictor.predict(
        point_coords=point,
        point_labels=np.array([1]),
        multimask_output=True
    )
    all_masks.append(masks[np.argmax(scores)])
```

## Развёртывание в ONNX

### Экспорт модели

```bash
python scripts/export_onnx_model.py \
    --checkpoint sam_vit_h_4b8939.pth \
    --model-type vit_h \
    --output sam_onnx.onnx \
    --return-single-mask
```

### Использование ONNX‑модели

```python
import onnxruntime

# Load ONNX model
ort_session = onnxruntime.InferenceSession("sam_onnx.onnx")

# Run inference (image embeddings computed separately)
masks = ort_session.run(
    None,
    {
        "image_embeddings": image_embeddings,
        "point_coords": point_coords,
        "point_labels": point_labels,
        "mask_input": np.zeros((1, 1, 256, 256), dtype=np.float32),
        "has_mask_input": np.array([0], dtype=np.float32),
        "orig_im_size": np.array([h, w], dtype=np.float32)
    }
)
```

## Распространённые рабочие процессы

### Рабочий процесс 1: Инструмент разметки

```python
import cv2

# Load model
predictor = SamPredictor(sam)
predictor.set_image(image)

def on_click(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Foreground point
        masks, scores, _ = predictor.predict(
            point_coords=np.array([[x, y]]),
            point_labels=np.array([1]),
            multimask_output=True
        )
        # Display best mask
        display_mask(masks[np.argmax(scores)])
```

### Рабочий процесс 2: Выделение объектов

```python
def extract_object(image, point):
    """Extract object at point with transparent background."""
    predictor.set_image(image)

    masks, scores, _ = predictor.predict(
        point_coords=np.array([point]),
        point_labels=np.array([1]),
        multimask_output=True
    )

    best_mask = masks[np.argmax(scores)]

    # Create RGBA output
    rgba = np.zeros((image.shape[0], image.shape[1], 4), dtype=np.uint8)
    rgba[:, :, :3] = image
    rgba[:, :, 3] = best_mask * 255

    return rgba
```

### Рабочий процесс 3: Сегментация медицинских изображений

```python
# Process medical images (grayscale to RGB)
medical_image = cv2.imread("scan.png", cv2.IMREAD_GRAYSCALE)
rgb_image = cv2.cvtColor(medical_image, cv2.COLOR_GRAY2RGB)

predictor.set_image(rgb_image)

# Segment region of interest
masks, scores, _ = predictor.predict(
    box=np.array([x1, y1, x2, y2]),  # ROI bounding box
    multimask_output=True
)
```

## Формат вывода

### Структура данных маски

```python
# SamAutomaticMaskGenerator output
{
    "segmentation": np.ndarray,  # H×W binary mask
    "bbox": [x, y, w, h],        # Bounding box
    "area": int,                 # Pixel count
    "predicted_iou": float,      # 0-1 quality score
    "stability_score": float,    # 0-1 robustness score
    "crop_box": [x, y, w, h],    # Generation crop region
    "point_coords": [[x, y]],    # Input point
}
```

### Формат COCO RLE

```python
from pycocotools import mask as mask_utils

# Encode mask to RLE
rle = mask_utils.encode(np.asfortranarray(mask.astype(np.uint8)))
rle["counts"] = rle["counts"].decode("utf-8")

# Decode RLE to mask
decoded_mask = mask_utils.decode(rle)
```

## Оптимизация производительности

### Память GPU

```python
# Use smaller model for limited VRAM
sam = sam_model_registry["vit_b"](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/models/segment-anything/checkpoint="sam_vit_b_01ec64.pth")

# Process images in batches
# Clear CUDA cache between large batches
torch.cuda.empty_cache()
```

### Оптимизация скорости

```python
# Use half precision
sam = sam.half()

# Reduce points for automatic generation
mask_generator = SamAutomaticMaskGenerator(
    model=sam,
    points_per_side=16,  # Default is 32
)

# Use ONNX for deployment
# Export with --return-single-mask for faster inference
```

## Частые проблемы

| Issue | Solution |
|-------|----------|
| Out of memory | Use ViT-B model, reduce image size |
| Slow inference | Use ViT-B, reduce points_per_side |
| Poor mask quality | Try different prompts, use box + points |
| Edge artifacts | Use stability_score filtering |
| Small objects missed | Increase points_per_side |

## Ссылки

- **[Advanced Usage](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/models/segment-anything/references/advanced-usage.md)** - Batching, fine‑tuning, integration
- **[Troubleshooting](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/models/segment-anything/references/troubleshooting.md)** - Common issues and solutions

## Ресурсы

- **GitHub**: https://github.com/facebookresearch/segment-anything
- **Paper**: https://arxiv.org/abs/2304.02643
- **Demo**: https://segment-anything.com
- **SAM 2 (Video)**: https://github.com/facebookresearch/segment-anything-2
- **HuggingFace**: https://huggingface.co/facebook/sam-vit-huge