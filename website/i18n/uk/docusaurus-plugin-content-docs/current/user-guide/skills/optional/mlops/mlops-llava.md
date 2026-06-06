---
title: "Llava — великий мовний та візуальний асистент"
sidebar_label: "Llava"
description: "Помічник великих мовних та візуальних моделей"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Llava

Large Language and Vision Assistant. Enables visual instruction tuning and image-based conversations. Combines CLIP vision encoder with Vicuna/LLaMA language models. Supports multi-turn image chat, visual question answering, and instruction following. Use for vision-language chatbots or image understanding tasks. Best for conversational image analysis.

## Метадані навички

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/llava` |
| Path | `optional-skills/mlops/llava` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `transformers`, `torch`, `pillow` |
| Platforms | linux, macos, windows |
| Tags | `LLaVA`, `Vision-Language`, `Multimodal`, `Visual Question Answering`, `Image Chat`, `CLIP`, `Vicuna`, `Conversational AI`, `Instruction Tuning`, `VQA` |

## Довідка: повний SKILL.md

:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# LLaVA — Large Language and Vision Assistant

Open-source vision-language model for conversational image understanding.

## Коли використовувати LLaVA

**Коли:**
- Створення чат‑ботів vision‑language
- Візуальне питання‑відповідь (VQA)
- Опис та підписування зображень
- Багатокрокові розмови з зображеннями
- Візуальне виконання інструкцій
- Розуміння документів із зображеннями

**Метрики:**
- **23 000+ GitHub stars**
- Можливості рівня GPT‑4V (ціль)
- Apache 2.0 License
- Різні розміри моделей (7B‑34B параметрів)

**Альтернативи:**
- **GPT‑4V**: Найвища якість, API‑базована
- **CLIP**: Проста zero‑shot класифікація
- **BLIP‑2**: Краще лише для підписування
- **Flamingo**: Дослідницька, не open‑source

## Швидкий старт

### Встановлення

```bash
# Clone repository
git clone https://github.com/haotian-liu/LLaVA
cd LLaVA

# Install
pip install -e .
```

### Базове використання

```python
from llava.model.builder import load_pretrained_model
from llava.mm_utils import get_model_name_from_path, process_images, tokenizer_image_token
from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN
from llava.conversation import conv_templates
from PIL import Image
import torch

# Load model
model_path = "liuhaotian/llava-v1.5-7b"
tokenizer, model, image_processor, context_len = load_pretrained_model(
    model_path=model_path,
    model_base=None,
    model_name=get_model_name_from_path(model_path)
)

# Load image
image = Image.open("image.jpg")
image_tensor = process_images([image], image_processor, model.config)
image_tensor = image_tensor.to(model.device, dtype=torch.float16)

# Create conversation
conv = conv_templates["llava_v1"].copy()
conv.append_message(conv.roles[0], DEFAULT_IMAGE_TOKEN + "\nWhat is in this image?")
conv.append_message(conv.roles[1], None)
prompt = conv.get_prompt()

# Generate response
input_ids = tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt').unsqueeze(0).to(model.device)

with torch.inference_mode():
    output_ids = model.generate(
        input_ids,
        images=image_tensor,
        do_sample=True,
        temperature=0.2,
        max_new_tokens=512
    )

response = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
print(response)
```

## Доступні моделі

| Model | Parameters | VRAM | Quality |
|-------|------------|------|---------|
| LLaVA-v1.5-7B | 7B | ~14 GB | Good |
| LLaVA-v1.5-13B | 13B | ~28 GB | Better |
| LLaVA-v1.6-34B | 34B | ~70 GB | Best |

```python
# Load different models
model_7b = "liuhaotian/llava-v1.5-7b"
model_13b = "liuhaotian/llava-v1.5-13b"
model_34b = "liuhaotian/llava-v1.6-34b"

# 4-bit quantization for lower VRAM
load_4bit = True  # Reduces VRAM by ~4×
```

## Використання CLI

```bash
# Single image query
python -m llava.serve.cli \
    --model-path liuhaotian/llava-v1.5-7b \
    --image-file image.jpg \
    --query "What is in this image?"

# Multi-turn conversation
python -m llava.serve.cli \
    --model-path liuhaotian/llava-v1.5-7b \
    --image-file image.jpg
# Then type questions interactively
```

## Веб‑інтерфейс (Gradio)

```bash
# Launch Gradio interface
python -m llava.serve.gradio_web_server \
    --model-path liuhaotian/llava-v1.5-7b \
    --load-4bit  # Optional: reduce VRAM

# Access at http://localhost:7860
```

## Багатокрокові розмови

```python
# Initialize conversation
conv = conv_templates["llava_v1"].copy()

# Turn 1
conv.append_message(conv.roles[0], DEFAULT_IMAGE_TOKEN + "\nWhat is in this image?")
conv.append_message(conv.roles[1], None)
response1 = generate(conv, model, image)  # "A dog playing in a park"

# Turn 2
conv.messages[-1][1] = response1  # Add previous response
conv.append_message(conv.roles[0], "What breed is the dog?")
conv.append_message(conv.roles[1], None)
response2 = generate(conv, model, image)  # "Golden Retriever"

# Turn 3
conv.messages[-1][1] = response2
conv.append_message(conv.roles[0], "What time of day is it?")
conv.append_message(conv.roles[1], None)
response3 = generate(conv, model, image)
```

## Типові завдання

### Опис зображення

```python
question = "Describe this image in detail."
response = ask(model, image, question)
```

### Візуальна відповідь на питання

```python
question = "How many people are in the image?"
response = ask(model, image, question)
```

### Текстове виявлення об’єктів

```python
question = "List all the objects you can see in this image."
response = ask(model, image, question)
```

### Розуміння сцени

```python
question = "What is happening in this scene?"
response = ask(model, image, question)
```

### Розуміння документів

```python
question = "What is the main topic of this document?"
response = ask(model, document_image, question)
```

## Навчання кастомної моделі

```bash
# Stage 1: Feature alignment (558K image-caption pairs)
bash scripts/v1_5/pretrain.sh

# Stage 2: Visual instruction tuning (150K instruction data)
bash scripts/v1_5/finetune.sh
```

## Квантовання (зменшення VRAM)

```python
# 4-bit quantization
tokenizer, model, image_processor, context_len = load_pretrained_model(
    model_path="liuhaotian/llava-v1.5-13b",
    model_base=None,
    model_name=get_model_name_from_path("liuhaotian/llava-v1.5-13b"),
    load_4bit=True  # Reduces VRAM ~4×
)

# 8-bit quantization
load_8bit=True  # Reduces VRAM ~2×
```

## Кращі практики

1. **Починай з моделі 7B** – хороша якість, прийнятна VRAM
2. **Використовуй 4‑бітове квантовання** – значно зменшує VRAM
3. **GPU обов’язковий** – інференс на CPU надзвичайно повільний
4. **Чіткі підказки** – конкретні питання дають кращі відповіді
5. **Багатокрокові розмови** – підтримуй контекст сесії
6. **Temperature 0.2‑0.7** – баланс креативності та послідовності
7. **max_new_tokens 512‑1024** – для детальних відповідей
8. **Batch processing** – обробляй кілька зображень послідовно

## Продуктивність

| Model | VRAM (FP16) | VRAM (4‑bit) | Speed (tokens/s) |
|-------|-------------|--------------|------------------|
| 7B | ~14 GB | ~4 GB | ~20 |
| 13B | ~28 GB | ~8 GB | ~12 |
| 34B | ~70 GB | ~18 GB | ~5 |

*On A100 GPU*

## Бенчмарки

LLaVA досягає конкурентних результатів у:
- **VQAv2**: 78.5%
- **GQA**: 62.0%
- **MM‑Vet**: 35.4%
- **MMBench**: 64.3%

## Обмеження

1. **Галюцинації** – може описувати те, чого немає на зображенні
2. **Просторове мислення** – труднощі з точними позиціями
3. **Малий текст** – важко розпізнавати дрібний шрифт
4. **Підрахунок об’єктів** – неточно при великій кількості
5. **Вимоги до VRAM** – потрібен потужний GPU
6. **Швидкість інференсу** – повільніше, ніж у CLIP

## Інтеграція з фреймворками

### LangChain

```python
from langchain.llms.base import LLM

class LLaVALLM(LLM):
    def _call(self, prompt, stop=None):
        # Custom LLaVA inference
        return response

llm = LLaVALLM()
```

### Gradio App

```python
import gradio as gr

def chat(image, text, history):
    response = ask_llava(model, image, text)
    return response

demo = gr.ChatInterface(
    chat,
    additional_inputs=[gr.Image(type="pil")],
    title="LLaVA Chat"
)
demo.launch()
```

## Ресурси

- **GitHub**: https://github.com/haotian-liu/LLaVA ⭐ 23,000+
- **Paper**: https://arxiv.org/abs/2304.08485
- **Demo**: https://llava.hliu.cc
- **Models**: https://huggingface.co/liuhaotian
- **License**: Apache 2.0