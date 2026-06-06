---
title: "Llama Cpp — llama"
sidebar_label: "Llama Cpp"
description: "лама"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Llama Cpp

llama.cpp локальное инференсирование GGUF + обнаружение моделей в HF Hub.

## Метаданные навыка

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

## Ссылка: полный SKILL.md

:::info
Ниже представлено полное определение навыка, которое Hermes загружает, когда этот навык активирован. Это то, что агент видит как инструкции, когда навык включён.
:::

# llama.cpp + GGUF

Используй этот навык для локального инференса GGUF, выбора квантования или обнаружения репозитория Hugging Face для llama.cpp.

## Когда использовать

- Запуск локальных моделей на CPU, Apple Silicon, CUDA, ROCm или Intel GPUs
- Поиск подходящего GGUF для конкретного репозитория Hugging Face
- Сборка команды `llama-server` или `llama-cli` из Hub
- Поиск в Hub моделей, уже поддерживающих llama.cpp
- Перечисление доступных файлов `.gguf` и их размеров в репозитории
- Выбор между вариантами Q4/Q5/Q6/IQ в зависимости от ОЗУ или видеопамяти пользователя

## Рабочий процесс обнаружения модели

Отдавай предпочтение URL‑рабочим процессам перед запросом `hf`, Python или пользовательских скриптов.

1. Поиск кандидатов‑репозиториев в Hub:
   - База: `https://huggingface.co/models?apps=llama.cpp&sort=trending`
   - Добавь `search=<term>` для семейства моделей
   - Добавь `num_parameters=min:0,max:24B` или аналогичное, если у пользователя ограничения по размеру
2. Открой репозиторий в представлении локального приложения llama.cpp:
   - `https://huggingface.co/<repo>?local-app=llama.cpp`
3. Рассматривай сниппет локального приложения как источник истины, когда он видим:
   - скопируй точную команду `llama-server` или `llama-cli`
   - сообщи рекомендованную квантование точно так, как её показывает HF
4. Прочитай тот же URL `?local-app=llama.cpp` как текст страницы или HTML и извлеки раздел под `Hardware compatibility`:
   - отдавай предпочтение точным меткам квантования и размерам вместо общих таблиц
   - сохраняй специфичные для репозитория метки, такие как `UD-Q4_K_M` или `IQ4_NL_XL`
   - если этот раздел не виден в полученном исходном коде страницы, укажи об этом и перейди к API‑дереву плюс общим рекомендациям по квантованию
5. Запроси API‑дерево, чтобы подтвердить, что действительно существует:
   - `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`
   - оставляй записи, где `type` — `file` и `path` заканчивается на `.gguf`
   - используй `path` и `size` как источник истины для имён файлов и их размеров в байтах
   - отделяй квантованные контрольные точки от файлов проектора `mmproj-*.gguf` и шард‑файлов `BF16/`
   - используй `https://huggingface.co/<repo>/tree/main` только как человеческую запасную опцию
6. Если сниппет локального приложения не виден в тексте, восстанови команду из репозитория и выбранного квантования:
   - короткий выбор квантования: `llama-server -hf <repo>:<QUANT>`
   - запасной вариант точного файла: `llama-server --hf-repo <repo> --hf-file <filename.gguf>`
7. Предлагай конвертацию из весов Transformers только если репозиторий ещё не предоставляет файлы GGUF.

## Быстрый старт

### Установить llama.cpp

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

### Запуск напрямую из Hugging Face Hub

```bash
llama-cli -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

```bash
llama-server -hf bartowski/Llama-3.2-3B-Instruct-GGUF:Q8_0
```

### Запуск точного файла GGUF из Hub

Используй это, когда API‑дерево показывает пользовательские имена файлов или точный сниппет HF отсутствует.

```bash
llama-server \
    --hf-repo microsoft/Phi-3-mini-4k-instruct-gguf \
    --hf-file Phi-3-mini-4k-instruct-q4.gguf \
    -c 4096
```

### Проверка совместимости с сервером OpenAI

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a limerick about Python exceptions"}
    ]
  }'
```

## Python‑обёртки (llama-cpp-python)

`pip install llama-cpp-python` (CUDA: `CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --force-reinstall --no-cache-dir`; Metal: `CMAKE_ARGS="-DGGML_METAL=on" ...`).

### Базовая генерация

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

### Чат + потоковая передача

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

### Эмбеддинги

```python
llm = Llama(model_path="./model-q4_k_m.gguf", embedding=True, n_gpu_layers=35)
vec = llm.embed("This is a test sentence.")
print(f"Embedding dimension: {len(vec)}")
```

Ты также можешь загрузить GGUF напрямую из Hub:

```python
llm = Llama.from_pretrained(
    repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
    filename="*Q4_K_M.gguf",
    n_gpu_layers=35,
)
```

## Выбор квантования

Сначала используй страницу Hub, затем общие эвристики.

- Предпочитай точную квантование, которую HF помечает совместимой с аппаратным профилем пользователя.
- Для обычного чата начни с `Q4_K_M`.
- Для кода или технической работы предпочтительнее `Q5_K_M` или `Q6_K`, если хватает памяти.
- При очень ограниченном ОЗУ рассматривай `Q3_K_M`, варианты `IQ` или `Q2` только если пользователь явно ставит в приоритет размер над качеством.
- Для мультимодальных репозиториев упоминай `mmproj-*.gguf` отдельно. Проектор не является основным файлом модели.
- Не нормализуй метки, специфичные для репозитория. Если на странице указано `UD-Q4_K_M`, сообщи `UD-Q4_K_M`.

## Извлечение доступных GGUF из репозитория

Когда пользователь спрашивает, какие GGUF существуют, возвращай:

- имя файла
- размер файла
- метку квантования
- является ли это основной моделью или вспомогательным проектором

Игнорируй, если не просят:

- README
- шард‑файлы BF16
- blobs imatrix или калибровочные артефакты

Для этого шага используй API‑дерево:

- `https://huggingface.co/api/models/<repo>/tree/main?recursive=true`

Для репозитория вроде `unsloth/Qwen3.6-35B-A3B-GGUF` страница локального приложения может показывать метки квантования `UD-Q4_K_M`, `UD-Q5_K_M`, `UD-Q6_K` и `Q8_0`, тогда как API‑дерево раскрывает точные пути файлов, такие как `Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` и `Qwen3.6-35B-A3B-Q8_0.gguf` с указанием размеров в байтах. Используй API‑дерево, чтобы превратить метку квантования в точное имя файла.

## Шаблоны поиска

Используй эти формы URL напрямую:

```text
https://huggingface.co/models?apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&sort=trending
https://huggingface.co/models?search=<term>&apps=llama.cpp&num_parameters=min:0,max:24B&sort=trending
https://huggingface.co/<repo>?local-app=llama.cpp
https://huggingface.co/api/models/<repo>/tree/main?recursive=true
https://huggingface.co/<repo>/tree/main
```

## Формат вывода

При ответе на запросы обнаружения предпочитай компактный структурированный результат, например:

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

## Ссылки

- **[hub-discovery.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/hub-discovery.md)** — только URL‑рабочие процессы Hugging Face, шаблоны поиска, извлечение GGUF и восстановление команд
- **[advanced-usage.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/advanced-usage.md)** — спекулятивное декодирование, пакетный инференс, генерация с ограничениями грамматики, LoRA, мульти‑GPU, пользовательские сборки, скрипты бенчмарков
- **[quantization.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/quantization.md)** — компромиссы качества квантования, когда использовать Q4/Q5/Q6/IQ, масштабирование размеров модели, imatrix
- **[server.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/server.md)** — запуск сервера напрямую из Hub, конечные точки OpenAI API, развёртывание в Docker, балансировка нагрузки NGINX, мониторинг
- **[optimization.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/optimization.md)** — многопоточность CPU, BLAS, эвристики выгрузки на GPU, настройка батчей, бенчмарки
- **[troubleshooting.md](https://github.com/NousResearch/hermes-agent/blob/main/skills/mlops/inference/llama-cpp/references/troubleshooting.md)** — проблемы установки/конвертации/квантования/инференса/сервера, Apple Silicon, отладка

## Ресурсы

- **GitHub**: https://github.com/ggml-org/llama.cpp
- **Hugging Face GGUF + llama.cpp docs**: https://huggingface.co/docs/hub/gguf-llamacpp
- **Hugging Face Local Apps docs**: https://huggingface.co/docs/hub/main/local-apps
- **Hugging Face Local Agents docs**: https://huggingface.co/docs/hub/agents-local
- **Пример страницы локального приложения**: https://huggingface.co/unsloth/Qwen3.6-35B-A3B-GGUF?local-app=llama.cpp
- **Пример API‑дерева**: https://huggingface.co/api/models/unsloth/Qwen3.6-35B-A3B-GGUF/tree/main?recursive=true
- **Пример поиска llama.cpp**: https://huggingface.co/models?num_parameters=min:0,max:24B&apps=llama.cpp&sort=trending
- **Лицензия**: MIT