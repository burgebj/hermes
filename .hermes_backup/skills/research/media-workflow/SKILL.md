---
name: media-workflow
description: Media monitoring, syndication, and processing — monitor automotive listings, financial news, social media, and process media via image generation/analysis/transcription.
---

# Media Workflow — 媒体监控与处理

涵盖外部数据源监控 (`media-monitor`) 和媒体内容处理 (`media-processing`) 的统一工作流。

## Subsections

### 1. 媒体监控 (Monitoring)

监控外部数据源、检测变化、生成摘要/告警。

#### 1.1 懂车帝二手车监控 (dongchedi-l90)

监控懂车帝乐道L90二手车，检测价格/里程变化。

**正确方法：用 `xvfb-run` 运行 Python 脚本（不要用 browser 工具）**

##### 依赖安装（首次）

```bash
cd /home/jianliu/work/hermes-agent && source venv/bin/activate
uv pip install crawl4ai
playwright install chromium
```

##### 运行命令

```bash
xvfb-run -a python tools/dongchedi_l90_watch.py \
  --list-url "https://www.dongchedi.com/usedcar/20,!1-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-918-25234-310000-1-x-x-x-x-x" \
  --db /home/jianliu/.hermes/dongchedi_l90.db \
  --max-details 40 \
  --profile-dir /tmp/dongchedi_profile
```

##### 关键要点

- **xvfb-run 是必须的** — WSL 无 X server，不加会报错
- **数据库注意事项** — 旧 DB 可能 schema 不兼容（缺 `platform` 列），推荐用新 DB
- **定时任务** — Job ID: 7c1e45b92026, Schedule: 每天 22:00

##### 输出格式

```
📋 **懂车帝乐道L90二手 — <日期>**

🆕 新增：<城市> <价格> <车型>
📉 下架：<城市> <价格> <车型>
🔄 价格/里程变化：<明细>（如有）

| 价格 | 里程 | 上牌 | 城市 | 车型 | 车商 |
|------|------|------|------|------|------|

**价格区间：** 最低~最高万 | 全部电池买断 | 全部商家
```

---

#### 1.2 华尔街见闻财经新闻 (wallstreetcn)

使用 API 获取华尔街见闻财经新闻。

##### API 接口

| 类型 | URL |
|------|-----|
| 最新 | `https://api-one-wscn.awtmt.com/apiv1/content/information-flow?channel=global&accept=article&limit=10` |
| 头条 | `https://api-one-wscn.awtmt.com/apiv1/content/carousel/information-flow?channel=global&limit=10` |
| 热文 | `https://api-one-wscn.awtmt.com/apiv1/content/articles/hot?period=all` |
| 搜索 | `https://api-one-wscn.awtmt.com/apiv1/search/article?query=关键词&limit=10` |

##### 数据解析

最新/头条数据在 `data.items[].resource` 中，含 `title`, `uri`, `content_short`, `display_time`, `author.display_name`。

热文数据在 `data.day_items[]` 中，含 `title`, `uri`, `display_time`, `pageviews`。

##### 输出格式

```markdown
### 📰 华尔街见闻 · WALLSTREETCN

---

**1.【文章标题】**

内容摘要...

> [阅读全文](https://wallstreetcn.com/articles/...) · 作者 · 日期

---

> 💡 华尔街见闻 —— 帮助投资者理解世界
```

**要求**: 品牌标识 + 分隔线 + 加粗标题 + 约50字摘要 + 引用格式元信息 + 品牌口号

---

#### 1.3 X/Twitter 社交媒体 (xitter)

使用 `x-cli` (官方 X API) 进行社交媒体操作。

##### 安装

```bash
uv tool install git+https://github.com/Infatoshi/x-cli.git
```

##### 凭据

需要5个值：`X_API_KEY`, `X_API_SECRET`, `X_BEARER_TOKEN`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`

从 https://developer.x.com/en/portal/dashboard 获取。

凭证存储在 `~/.config/x-cli/.env`：
```bash
ln -sf ~/.hermes/.env ~/.config/x-cli/.env
```

##### 常用命令

```bash
# 发推
x-cli tweet post "hello world"
x-cli tweet reply 1234567890 "nice post"
x-cli tweet quote 1234567890 "worth reading"

# 搜索/读取
x-cli tweet search "AI agents" --max 20
x-cli user timeline openai --max 10
x-cli me mentions --max 20

# 操作
x-cli like 1234567890
x-cli retweet 1234567890

# 结构化输出
x-cli -j tweet search "AI agents" --max 5
```

##### 已知问题

- **付费 API 访问**: 多数失败是权限/配额问题
- **403 oauth1-permissions**: 需在启用"Read and write"后重新生成access token
- **回复限制**: X 限制程序化回复，`tweet quote` 比 `tweet reply` 更可靠
- **速率限制**: 需要关注各端点的限制窗口

---

### 2. 媒体处理 (Processing)

涵盖图像生成 (Stable Diffusion)、视觉-语言理解 (CLIP)、和语音识别 (Whisper) 的工作流。

#### 2.1 图像生成 (Stable Diffusion)

使用 HuggingFace Diffusers 进行文本到图像、图像到图像、修补 (inpainting) 等操作。

##### 何时使用

- 从文本描述生成图像
- 图片风格迁移/增强
- 填充遮罩区域 (inpainting)
- 扩展图像边界 (outpainting)
- 创建现有图像的变体
- 构建自定义图像生成工作流

##### 安装

```bash
pip install diffusers transformers accelerate torch
pip install xformers  # 可选: 内存高效注意力
```

##### Quick Start

```python
from diffusers import StableDiffusionPipeline
import torch

pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
pipe = pipe.to("cuda")

image = pipe("a photo of an astronaut riding a horse on mars").images[0]
image.save("astronaut_horse.png")
```

##### 可用模型

| Model | Description | Recommended |
|-------|-------------|-------------|
| SD 1.5 | Fast, lightweight, widely supported | Good for CPU/low VRAM |
| SDXL | Higher quality, up to 1024x1024 | Best quality-to-speed |
| SD 3.0 | Latest, improved prompt following | Needs 16GB+ VRAM |
| Flux | High quality, detailed outputs | Best quality, needs 24GB+ |

##### 内存优化

```python
# Enable memory optimizations
pipe.enable_model_cpu_offload()
pipe.enable_attention_slicing()
pipe.enable_vae_slicing()
pipe.enable_xformers_memory_efficient_attention()
```

##### 控制技巧

- **负面提示词**: `negative_prompt="blurry, bad anatomy, extra limbs"` 排除不需要的内容
- **采样步数**: 20-50步，更多步数=更精细但更慢
- **引导比例**: 7.5-12，越高越遵循提示词但可能失真
- **种子值**: `generator=torch.Generator("cuda").manual_seed(42)` 确保可复现

---

#### 2.2 视觉-语言理解 (CLIP)

OpenAI 的 CLIP 模型：零样本图像分类、图像-文本匹配、跨模态检索。

##### 何时使用

- 零样本图像分类（无需训练数据）
- 图像-文本相似度/匹配
- 语义图像搜索
- 内容审核（检测 NSFW、暴力）
- 视觉问答
- 跨模态检索（图像→文本，文本→图像）

##### 快速开始

```python
import torch
import clip
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

image = preprocess(Image.open("photo.jpg")).unsqueeze(0).to(device)
text = clip.tokenize(["a dog", "a cat", "a bird"]).to(device)

with torch.no_grad():
    logits_per_image, _ = model(image, text)
    probs = logits_per_image.softmax(dim=-1).cpu().numpy()
```

##### 可用模型

| 模型 | 参数量 | 速度 | 质量 |
|------|--------|------|------|
| RN50 | 102M | 快 | 好 |
| ViT-B/32 | 151M | 中 | 更好 |
| ViT-L/14 | 428M | 慢 | 最好 |

##### 最佳实践

1. 大部分场景使用 **ViT-B/32**
2. 归一化嵌入向量 — 余弦相似度必需
3. 批量处理 — 效率更高
4. 缓存嵌入 — 重复计算开销大
5. 使用描述性标签 — 更好的零样本性能
6. GPU 推荐 — 10-50× 加速

##### 局限性

- 不适合细粒度分类
- 需描述性文本，模糊标签表现差
- 存在网络数据偏差
- 无边界框，仅整图级别
- 空间理解有限

---

#### 2.3 语音识别 (Whisper)

OpenAI 的多语言语音识别模型，支持 99 种语言。

##### 何时使用

- 语音转文字转录（99种语言）
- 播客/视频转录
- 会议记录自动化
- 翻译成英文
- 嘈杂音频转录
- 多语言音频处理

##### 快速开始

```bash
pip install -U openai-whisper
# 需要 ffmpeg
# Ubuntu: sudo apt install ffmpeg
```

```python
import whisper
model = whisper.load_model("base")
result = model.transcribe("audio.mp3")
print(result["text"])
```

##### 模型大小

| 模型 | 参数量 | 速度 | VRAM |
|------|--------|------|------|
| tiny | 39M | ~32x | ~1 GB |
| base | 74M | ~16x | ~1 GB |
| small | 244M | ~6x | ~2 GB |
| medium | 769M | ~2x | ~5 GB |
| large | 1550M | 1x | ~10 GB |
| turbo | 809M | ~8x | ~6 GB |

**推荐**: 使用 `turbo` 平衡速度与质量

##### 使用技巧

1. **指定语言** — 比自动检测更快
2. **添加初始提示** — 改善技术术语准确度
3. **使用 GPU** — 10-20× 更快
4. **使用 faster-whisper** — 比 openai-whisper 快 4×
5. **监控 VRAM** — 根据硬件缩放模型大小
6. **分割长音频** — 建议 <30 分钟分段

##### 局限性

- 可能产生幻觉（重复或编造文本）
- 长音频（>30分钟）准确度下降
- 无说话人识别（无 diarization）
- 口音影响质量
- 不适合实时字幕
