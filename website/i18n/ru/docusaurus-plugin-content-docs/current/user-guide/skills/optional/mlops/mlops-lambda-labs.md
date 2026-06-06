---
title: "Резервированные и по запросу GPU‑облачные инстансы для обучения и инференса ML"
sidebar_label: "Lambda Labs Gpu Cloud"
description: "Резервированные и по запросу GPU облачные инстансы для обучения и инференса ML"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Lambda Labs GPU Cloud

Резервированные и по‑запросу GPU‑облачные инстансы для обучения и инференса ML. Используй, когда нужны выделенные GPU‑инстансы с простым SSH‑доступом, постоянными файловыми системами или высокопроизводительными многонодными кластерами для масштабного обучения.

## Skill metadata

| | |
|---|---|
| Source | Optional — install with `hermes skills install official/mlops/lambda-labs` |
| Path | `optional-skills/mlops/lambda-labs` |
| Version | `1.0.0` |
| Author | Orchestra Research |
| License | MIT |
| Dependencies | `lambda-cloud-client>=1.0.0` |
| Platforms | linux, macos, windows |
| Tags | `Infrastructure`, `GPU Cloud`, `Training`, `Inference`, `Lambda Labs` |

## Reference: full SKILL.md

:::info
Ниже приведено полное определение скилла, которое Hermes загружает при его активации. Это то, что агент видит как инструкции, когда скилл включён.
:::

# Lambda Labs GPU Cloud

Полное руководство по запуску ML‑нагрузок в облаке Lambda Labs GPU с инстансами по запросу и кластерами «в один клик».

## Когда использовать Lambda Labs

**Используй Lambda Labs, когда:**
- нужны выделенные GPU‑инстансы с полным SSH‑доступом
- запускаются длительные задачи обучения (от часов до дней)
- требуется простое ценообразование без платы за исходящий трафик
- нужна постоянная память между сессиями
- требуются высокопроизводительные многонодные кластеры (16‑512 GPU)
- нужен предустановленный ML‑стек (Lambda Stack с PyTorch, CUDA, NCCL)

**Ключевые возможности:**
- **Разнообразие GPU**: B200, H100, GH200, A100, A10, A6000, V100
- **Lambda Stack**: предустановленные PyTorch, TensorFlow, CUDA, cuDNN, NCCL
- **Постоянные файловые системы**: данные сохраняются между перезапусками инстанса
- **Кластеры в один клик**: Slurm‑кластеры 16‑512 GPU с InfiniBand
- **Простое ценообразование**: оплата по минуте, без платы за egress
- **Глобальные регионы**: более 12 регионов по всему миру

**Альтернативы:**
- **Modal**: для безсерверных, автоматически масштабируемых задач
- **SkyPilot**: для оркестрации в мульти‑облаке и оптимизации расходов
- **RunPod**: для более дешёвых spot‑инстансов и безсерверных эндпоинтов
- **Vast.ai**: рынок GPU с самыми низкими ценами

## Быстрый старт

### Настройка аккаунта

1. Создай аккаунт на https://lambda.ai
2. Добавь способ оплаты
3. Сгенерируй API‑ключ в панели управления
4. Добавь SSH‑ключ (обязательно перед запуском инстансов)

### Запуск через консоль

1. Перейди на https://cloud.lambda.ai/instances
2. Нажми «Launch instance»
3. Выбери тип GPU и регион
4. Выбери SSH‑ключ
5. При желании привяжи файловую систему
6. Запусти инстанс и подожди 3‑15 минут

### Подключение по SSH

```bash
# Get instance IP from console
ssh ubuntu@<INSTANCE-IP>

# Or with specific key
ssh -i ~/.ssh/lambda_key ubuntu@<INSTANCE-IP>
```

## GPU‑инстансы

### Доступные GPU

| GPU | VRAM | Цена за GPU/ч | Лучшее применение |
|-----|------|---------------|-------------------|
| B200 SXM6 | 180 GB | $4.99 | Самые крупные модели, самая быстрая тренировка |
| H100 SXM | 80 GB | $2.99‑3.29 | Обучение больших моделей |
| H100 PCIe | 80 GB | $2.49 | Стоимостно‑эффективный H100 |
| GH200 | 96 GB | $1.49 | Большие модели на одном GPU |
| A100 80GB | 80 GB | $1.79 | Производственное обучение |
| A100 40GB | 40 GB | $1.29 | Стандартное обучение |
| A10 | 24 GB | $0.75 | Инференс, дообучение |
| A6000 | 48 GB | $0.80 | Хорошее соотношение VRAM/цена |
| V100 | 16 GB | $0.55 | Обучение с ограниченным бюджетом |

### Конфигурации инстансов

```
8x GPU: Best for distributed training (DDP, FSDP)
4x GPU: Large models, multi-GPU training
2x GPU: Medium workloads
1x GPU: Fine-tuning, inference, development
```

### Время запуска

- Один GPU: 3‑5 минут
- Несколько GPU: 10‑15 минут

## Lambda Stack

На всех инстансах предустановлен Lambda Stack:

```bash
# Included software
- Ubuntu 22.04 LTS
- NVIDIA drivers (latest)
- CUDA 12.x
- cuDNN 8.x
- NCCL (for multi-GPU)
- PyTorch (latest)
- TensorFlow (latest)
- JAX
- JupyterLab
```

### Проверка установки

```bash
# Check GPU
nvidia-smi

# Check PyTorch
python -c "import torch; print(torch.cuda.is_available())"

# Check CUDA version
nvcc --version
```

## Python API

### Установка

```bash
pip install lambda-cloud-client
```

### Аутентификация

```python
import os
import lambda_cloud_client

# Configure with API key
configuration = lambda_cloud_client.Configuration(
    host="https://cloud.lambdalabs.com/api/v1",
    access_token=os.environ["LAMBDA_API_KEY"]
)
```

### Список доступных инстансов

```python
with lambda_cloud_client.ApiClient(configuration) as api_client:
    api = lambda_cloud_client.DefaultApi(api_client)

    # Get available instance types
    types = api.instance_types()
    for name, info in types.data.items():
        print(f"{name}: {info.instance_type.description}")
```

### Запуск инстанса

```python
from lambda_cloud_client.models import LaunchInstanceRequest

request = LaunchInstanceRequest(
    region_name="us-west-1",
    instance_type_name="gpu_1x_h100_sxm5",
    ssh_key_names=["my-ssh-key"],
    file_system_names=["my-filesystem"],  # Optional
    name="training-job"
)

response = api.launch_instance(request)
instance_id = response.data.instance_ids[0]
print(f"Launched: {instance_id}")
```

### Список запущенных инстансов

```python
instances = api.list_instances()
for instance in instances.data:
    print(f"{instance.name}: {instance.ip} ({instance.status})")
```

### Завершение инстанса

```python
from lambda_cloud_client.models import TerminateInstanceRequest

request = TerminateInstanceRequest(
    instance_ids=[instance_id]
)
api.terminate_instance(request)
```

### Управление SSH‑ключами

```python
from lambda_cloud_client.models import AddSshKeyRequest

# Add SSH key
request = AddSshKeyRequest(
    name="my-key",
    public_key="ssh-rsa AAAA..."
)
api.add_ssh_key(request)

# List keys
keys = api.list_ssh_keys()

# Delete key
api.delete_ssh_key(key_id)
```

## CLI с curl

### Список типов инстансов

```bash
curl -u $LAMBDA_API_KEY: \
  https://cloud.lambdalabs.com/api/v1/instance-types | jq
```

### Запуск инстанса

```bash
curl -u $LAMBDA_API_KEY: \
  -X POST https://cloud.lambdalabs.com/api/v1/instance-operations/launch \
  -H "Content-Type: application/json" \
  -d '{
    "region_name": "us-west-1",
    "instance_type_name": "gpu_1x_h100_sxm5",
    "ssh_key_names": ["my-key"]
  }' | jq
```

### Завершение инстанса

```bash
curl -u $LAMBDA_API_KEY: \
  -X POST https://cloud.lambdalabs.com/api/v1/instance-operations/terminate \
  -H "Content-Type: application/json" \
  -d '{"instance_ids": ["<INSTANCE-ID>"]}' | jq
```

## Постоянное хранилище

### Файловые системы

Файловые системы сохраняют данные между перезапусками инстанса:

```bash
# Mount location
/lambda/nfs/<FILESYSTEM_NAME>

# Example: save checkpoints
python train.py --checkpoint-dir /lambda/nfs/my-storage/checkpoints
```

### Создание файловой системы

1. Открой раздел **Storage** в консоли Lambda
2. Нажми «Create filesystem»
3. Выбери регион (должен совпадать с регионом инстанса)
4. Задай имя и создай

### Привязка к инстансу

Файловые системы необходимо привязывать при запуске инстанса:
- Через консоль: выбери файловую систему в процессе запуска
- Через API: укажи `file_system_names` в запросе на запуск

### Лучшие практики

<!-- ascii-guard-ignore -->
```bash
# Store on filesystem (persists)
/lambda/nfs/storage/
  ├── datasets/
  ├── checkpoints/
  ├── models/
  └── outputs/

# Local SSD (faster, ephemeral)
/home/ubuntu/
  └── working/  # Temporary files
```
<!-- ascii-guard-ignore-end -->

## Конфигурация SSH

### Добавление SSH‑ключа

```bash
# Generate key locally
ssh-keygen -t ed25519 -f ~/.ssh/lambda_key

# Add public key to Lambda console
# Or via API
```

### Несколько ключей

```bash
# On instance, add more keys
echo 'ssh-rsa AAAA...' >> ~/.ssh/authorized_keys
```

### Импорт из GitHub

```bash
# On instance
ssh-import-id gh:username
```

### SSH‑туннелирование

```bash
# Forward Jupyter
ssh -L 8888:localhost:8888 ubuntu@<IP>

# Forward TensorBoard
ssh -L 6006:localhost:6006 ubuntu@<IP>

# Multiple ports
ssh -L 8888:localhost:8888 -L 6006:localhost:6006 ubuntu@<IP>
```

## JupyterLab

### Запуск из консоли

1. Открой страницу **Instances**
2. Нажми «Launch» в колонке **Cloud IDE**
3. JupyterLab откроется в браузере

### Ручной доступ

```bash
# On instance
jupyter lab --ip=0.0.0.0 --port=8888

# From local machine with tunnel
ssh -L 8888:localhost:8888 ubuntu@<IP>
# Open http://localhost:8888
```

## Рабочие процессы обучения

### Обучение на одном GPU

```bash
# SSH to instance
ssh ubuntu@<IP>

# Clone repo
git clone https://github.com/user/project
cd project

# Install dependencies
pip install -r requirements.txt

# Train
python train.py --epochs 100 --checkpoint-dir /lambda/nfs/storage/checkpoints
```

### Обучение на нескольких GPU (один узел)

```python
# train_ddp.py
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

def main():
    dist.init_process_group("nccl")
    rank = dist.get_rank()
    device = rank % torch.cuda.device_count()

    model = MyModel().to(device)
    model = DDP(model, device_ids=[device])

    # Training loop...

if __name__ == "__main__":
    main()
```

```bash
# Launch with torchrun (8 GPUs)
torchrun --nproc_per_node=8 train_ddp.py
```

### Сохранение контрольных точек в файловую систему

```python
import os

checkpoint_dir = "/lambda/nfs/my-storage/checkpoints"
os.makedirs(checkpoint_dir, exist_ok=True)

# Save checkpoint
torch.save({
    'epoch': epoch,
    'model_state_dict': model.state_dict(),
    'optimizer_state_dict': optimizer.state_dict(),
    'loss': loss,
}, f"{checkpoint_dir}/checkpoint_{epoch}.pt")
```

## Кластеры в один клик

### Обзор

Высокопроизводительные Slurm‑кластеры с:
- 16‑512 GPU NVIDIA H100 или B200
- NVIDIA Quantum‑2 400 Gb/s InfiniBand
- GPUDirect RDMA 3200 Gb/s
- Предустановленным распределённым ML‑стеком

### Включённое ПО

- Ubuntu 22.04 LTS + Lambda Stack
- NCCL, Open MPI
- PyTorch с DDP и FSDP
- TensorFlow
- OFED‑драйверы

### Хранилище

- 24 TB NVMe на каждый вычислительный узел (временное)
- Lambda файловые системы для постоянных данных

### Обучение на нескольких узлах

```bash
# On Slurm cluster
srun --nodes=4 --ntasks-per-node=8 --gpus-per-node=8 \
  torchrun --nnodes=4 --nproc_per_node=8 \
  --rdzv_backend=c10d --rdzv_endpoint=$MASTER_ADDR:29500 \
  train.py
```

## Сетевое взаимодействие

### Пропускная способность

- Межинстансовая (в том же регионе): до 200 Gbps
- Исходящий интернет: максимум 20 Gbps

### Брандмауэр

- По умолчанию открыт только порт 22 (SSH)
- Дополнительные порты настраиваются в консоли Lambda
- ICMP‑трафик разрешён по умолчанию

### Приватные IP‑адреса

```bash
# Find private IP
ip addr show | grep 'inet '
```

## Типовые рабочие процессы

### Workflow 1: Дообучение LLM

```bash
# 1. Launch 8x H100 instance with filesystem

# 2. SSH and setup
ssh ubuntu@<IP>
pip install transformers accelerate peft

# 3. Download model to filesystem
python -c "
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained('meta-llama/Llama-2-7b-hf')
model.save_pretrained('/lambda/nfs/storage/models/llama-2-7b')
"

# 4. Fine-tune with checkpoints on filesystem
accelerate launch --num_processes 8 train.py \
  --model_path /lambda/nfs/storage/models/llama-2-7b \
  --output_dir /lambda/nfs/storage/outputs \
  --checkpoint_dir /lambda/nfs/storage/checkpoints
```

### Workflow 2: Пакетный инференс

```bash
# 1. Launch A10 instance (cost-effective for inference)

# 2. Run inference
python inference.py \
  --model /lambda/nfs/storage/models/fine-tuned \
  --input /lambda/nfs/storage/data/inputs.jsonl \
  --output /lambda/nfs/storage/data/outputs.jsonl
```

## Оптимизация расходов

### Выбор подходящего GPU

| Задача | Рекомендованный GPU |
|--------|--------------------|
| Дообучение LLM (7 B) | A100 40GB |
| Дообучение LLM (70 B) | 8× H100 |
| Инференс | A10, A6000 |
| Разработка | V100, A10 |
| Максимальная производительность | B200 |

### Снижение затрат

1. **Используй файловые системы**: не скачивай данные повторно
2. **Часто сохраняй контрольные точки**: возможность возобновления прерванного обучения
3. **Подбирай размер**: не переусердствуй с количеством GPU
4. **Заверши неиспользуемые инстансы**: авто‑остановки нет, завершай вручную

### Мониторинг использования

- Панель отображает текущую загрузку GPU в реальном времени
- API позволяет получать метрики программно

## Распространённые проблемы

| Проблема | Решение |
|----------|---------|
| Инстанс не запускается | Проверь доступность региона, попробуй другой тип GPU |
| SSH‑подключение отклонено | Дождись инициализации инстанса (3‑15 минут) |
| Данные потерялись после завершения | Используй постоянные файловые системы |
| Медленная передача данных | Выбирай файловую систему в том же регионе |
| GPU не обнаружен | Перезагрузи инстанс, проверь драйверы |

## Ссылки

- **[Advanced Usage](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/lambda-labs/references/advanced-usage.md)** — обучение на нескольких узлах, автоматизация через API
- **[Troubleshooting](https://github.com/NousResearch/hermes-agent/blob/main/optional-skills/mlops/lambda-labs/references/troubleshooting.md)** — типичные проблемы и их решения

## Ресурсы

- **Документация**: https://docs.lambda.ai
- **Консоль**: https://cloud.lambda.ai
- **Цены**: https://lambda.ai/instances
- **Поддержка**: https://support.lambdalabs.com
- **Блог**: https://lambda.ai/blog