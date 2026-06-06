---
title: "Llama Cpp — llama"
sidebar_label: "Llama Cpp"
description: "лама"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Llama Cpp

llama.cpp local GGUF inference + HF Hub model discovery.

## Метадані навички

| | |
|---|---|
| Source | Bundled (installed by default) |
| Path | `skills/mlops/inference/llama-cpp` |
| Version | `2.1.2` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `llama-cpp-python>=0.2.0` |
| Platforms | linux, macos, windows |
| Tags | `llama.cpp`, `GGUF`, `Quantization`, `Hugging Face Hub`, `CPU Inference`, `Apple Silicon`, `Edge Deployment`, `AMD GPUs`, `Intel GPUs`, `NVIDIA`, `URL-first` |

## Довідка: повний SKILL.md

:::info
Нижче наведено повне визначення навички, яке Hermes завантажує, коли ця навичка активується. Це те, що агент бачить як інструкції, коли навичка активна.
:::

# llama.cpp + GGUF

Використовуй цю навичку для локального GGUF inference, вибору кванту або пошуку репозиторію Hugging Face для llama.cpp.

## Коли використовувати

- Запуск локальних моделей на CPU, Apple Silicon, CUDA, ROCm або Intel GPUs
- Пошук потрібного GGUF для конкретного репозиторію Hugging Face
- Створення команди `llama-server` або `llama-cli` з Hub
- Пошук у Hub моделей, які вже підтримують llama.cpp
- Перерахування доступних `.gguf`‑файлів і їх розмірів у репозиторії
- Вибір між варіантами Q4/Q5/Q6/IQ відповідно до RAM або VRAM користувача

## Робочий процес виявлення моделей

Надавай перевагу URL‑процесам перед запитом `hf`, Python або кастомних скриптів.

1. Шукай кандидатні репо у Hub:
   - База: `https://huggingface.co/models?apps=llama.cpp&sort=trending`
   - Додай `search=<term>` для сімейства моделей
   - Додай `num_parameters=min:0,max:24B` або подібне, коли у користувача є обмеження за розміром
2. Відкрий репо у вигляді локального додатку llama.cpp:
   - `https://huggingface.co/<repo>?local-app=llama.cpp`
3. Сприймай фрагмент локального додатку як джерело правди, коли він видимий:
   - скопіюй точну команду `llama-server` або `llama-cli`
   - повідом точний квант, який показує HF
4. Прочитай той самий URL `?local-app=llama.cpp` як текст сторінки або HTML і витягни розділ під **Hardware compatibility**:
   - віддай перевагу його точним міткам кванту та розмірам над загальними таблицями
   - зберігай специфічні для репо мітки, такі як `UD-Q4_K_M` або `IQ4_NL_XL`
   - якщо цей розділ не видимий у отриманому коді сторінки, повідом про це і використай запасний варіант через tree API плюс загальні рекомендації щодо кванту
5. Запитай tree API, щоб підтвердити, що саме існує:
   - `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`
   - залишай записи, де `type` — `file` і `path` закінчується на `.gguf`
   - використай `path` і `size` як джерело правди для імен файлів і їх розмірів у байтах
   - розділяй квантовані контрольні точки від файлів проектора `mmproj-*.gguf` та шард‑файлів `BF16/`
   - використай `https://huggingface.co/<repo>/tree/main` лише як людський запасний варіант
6. Якщо фрагмент локального додатку не текстово‑видимий, відтвори команду з репо та обраного кванту:
   - скорочений вибір кванту: `llama-server -hf <repo>:<QUANT>`
   - запасний варіант точного файлу: `llama-server --hf-repo <repo> --hf-file <filename.gguf>`
7. Пропонуй конвертацію з ваг Transformer лише тоді, коли репо ще не містить GGUF‑файлів.

## Швидкий старт

### Встановити llama.cpp

```bash
# macOS / Linux (simplest)
brew install llama.cpp
```

```bash
winget install llama.cpp
```

```bash
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build
cmake --build build --config Release
```

### Запустити безпосередньо з Hugging Face Hub

```bash
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

```bash
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

### Запустити точний GGUF‑файл з Hub

Використовуй це, коли tree API показує кастомні імена файлів або точний фрагмент HF відсутній.

```bash
llama-server \
    --hf-repo microsoft/Phi-3-mini-4k-instruct-gguf \
    --hf-file Phi-3-mini-4k-instruct-q4.gguf \
    -c 4096
```

### Перевірка сумісності з OpenAI‑серверами

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a limerick about Python exceptions"}
    ]
  }'
```

## Python‑зв’язки (llama-cpp-python)

`pip install llama-cpp-python` (CUDA: `CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir`; Metal: `CMAKE_ARGS="-DGGML_METAL=on" ...`).

### Базова генерація

```python
from llama_cpp import Llama

llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,     # 0 for CPU, 99 to offload everything
    n_threads=8,
)

out = llm("What is machine learning?", max_tokens=256, temperature=0.7)
print(out["choices"][0]["text"])
```

### Чат + стрімінг

```python
llm = Llama(
    model_path="./model-q4_k_m.gguf",
    n_ctx=4096,
    n_gpu_layers=35,
    chat_format="llama-3",   # or "chatml", "mistral", etc.
)

resp = llm.create_chat_completion(
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"},
    ],
    max_tokens=256,
)
print(resp["choices"][0]["message"]["content"])

# Streaming
for chunk in llm("Explain quantum computing:", max_tokens=256, stream=True):
    print(chunk["choices"][0]["text"], end="", flush=True)
```

### Ембеддинги

```python
llm = Llama(model_path="./model-q4_k_m.gguf", embedding=True, n_gpu_layers=35)
vec = llm.embed("This is a test sentence.")
print(f"Embedding dimension: {len(vec)}")
```

Ти також можеш завантажити GGUF безпосередньо з Hub:

```python
llm = Llama.from_pretrained(
    repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
    filename="*Q4_K_M.gguf",
    n_gpu_layers=35,
)
```

## Вибір кванту

Спочатку користуйся сторінкою Hub, потім загальними евристиками.

- Надавай перевагу точному кванту, який HF позначає як сумісний з апаратним профілем користувача.
- Для загального чату починай з `Q4_K_M`.
- Для коду або технічної роботи віддавай перевагу `Q5_K_M` або `Q6_K`, якщо дозволяє пам’ять.
- При дуже обмеженій RAM розглядай `Q3_K_M`, варіанти `IQ` або `Q2` лише якщо користувач явно пріоритетує підгонку над якістю.
- Для мультимодальних репо згадуй `mmproj-*.gguf` окремо. Проектор не є основним файлом моделі.
- Не нормалізуй мітки, властиві репо. Якщо сторінка каже `UD‑Q4_K_M`, повідом `UD‑Q4_K_M`.

## Витяг доступних GGUF‑ів з репо

Коли користувач запитує, які GGUF‑и існують, поверни:

- ім’я файлу
- розмір файлу
- мітку кванту
- чи це основна модель, чи допоміжний проектор

Ігноруй, якщо не просять:

- README
- BF16 шард‑файли
- imatrix‑блоби або калібрувальні артефакти

Використай tree API для цього кроку:

- `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`

Для репо типу `unsloth/Qwen3.6-35B-A3B-GGUF` сторінка локального додатку може показувати кванти типу `UD‑Q4_K_M`, `UD‑Q5_K_M`, `UD‑Q6_K` та `Q8_0`, тоді як tree API розкриває точні шляхи файлів, наприклад `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` і `Qwen3.6-35B-A3B-Q8_0.gguf` з розмірами у байтах. Використай tree API, щоб перетворити мітку кванту у точну назву файлу.

## Шаблони пошуку

Використовуй ці форми URL безпосередньо:

```text
https://huggingface.co/models?apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&num_parameters=min:0,max:24B&sort=trending
https://huggingface.co/<repo>?local-app=llama.cpp
https://huggingface.co/api/models/<repo>/tree/main?recursive=true
https://huggingface.co/<repo>/tree/main
```

## Формат виводу

При відповіді на запити про виявлення надавай компактний структурований результат, наприклад:

```text
Repo: <repo>
Recommended quant from HF: <label> (<size>)
llama-server: <command>
Other GGUFs:
- <filename> - <size>
- <filename> - <size>
Source URLs:
- <local-app URL>
- <tree API URL>
```

## Посилання

- **[hub-discovery.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/hub-discovery.md)** – URL‑only Hugging Face робочі процеси, шаблони пошуку, витяг GGUF та відтворення команд
- **[advanced-usage.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/advanced-usage.md)** — спекулятивне декодування, пакетна інференція, генерація з обмеженням граматики, LoRA, multi‑GPU, кастомні збірки, скрипти бенчмарків
- **[quantization.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/quantization.md)** — компроміси якості кванту, коли використовувати Q4/Q5/Q6/IQ, масштабування розмірів моделей, imatrix
- **[server.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/server.md)** — запуск сервера безпосередньо з Hub, кінцеві точки OpenAI API, розгортання в Docker, балансування навантаження NGINX, моніторинг
- **[optimization.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/optimization.md)** — багатопоточність CPU, BLAS, евристики відвантаження на GPU, налаштування батчів, бенчмарки
- **[troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/troubleshooting.md)** — проблеми встановлення/конвертації/квантування/інференції/сервера, Apple Silicon, налагодження

## Ресурси

- **GitHub**: https://github.com/ggml-org/llama.cpp
- **Hugging Face GGUF + llama.cpp docs**: https://huggingface.co/docs/hub/gguf-llamacpp
- **Hugging Face Local Apps docs**: https://huggingface.co/docs/hub/main/local-apps
- **Hugging Face Local Agents docs**: https://huggingface.co/docs/hub/agents-local
- **Приклад сторінки локального додатку**: https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF?local-app=llama.cpp
- **Приклад tree API**: https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main?recursive=true
- **Приклад пошуку llama.cpp**: https://huggingface.co/models?num_parameters=min:0,max:24B&apps=llama.cpp&sort=trending
- **Ліцензія**: MIT