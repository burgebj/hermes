---
name: dongchedi-l90-watch
description: 懂车帝 乐道L90 二手车价格监控 cron job。每天自动抓取列表页和详情页，对比此前快照报告新增/下架/价格变动。
category: car-scraper
trigger: cron job (daily, usually 14:00 UTC)
---

# 懂车帝 乐道L90 监控

## 用途
监控懂车帝上乐道L90二手车的挂牌价格、车源数量变化，通过SQLite持久化历史数据。

## 脚本路径
- 主脚本: `~/work/hermes-agent/tools/dongchedi_l90_watch.py`
- 工具包装器: `~/work/hermes-agent/tools/dongchedi_tool.py`
- SQLite数据库: `~/work/hermes-agent/tools/dongchedi_l90.sqlite`

## 运行方式

### 方法1: 直接运行（带xvfb，因为无X server）
```bash
cd ~/work/hermes-agent/tools
xvfb-run python3 dongchedi_l90_watch.py \
  --list-url "https://www.dongchedi.com/usedcar/20,!1-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-918-25234-310000-1-x-x-x-x-x" \
  --db "dongchedi_l90.sqlite" \
  --max-details 30 \
  --profile-dir "~/.crawl4ai/profiles/dongchedi_profile"
```

### 方法2: 通过 Hermes 工具
```python
dongchedi_watch(
  list_url="https://www.dongchedi.com/usedcar/...",
  max_details=30,
  headless=True
)
```

### 方法3: 手动验证（首次或验证码）
```bash
python3 dongchedi_l90_watch.py \
  --list-url "..." \
  --headed \
  --manual-verify-only
```

## 修复的 Bug
- `--headed` 默认值原来是 `True`，导致无X server环境启动headed浏览器失败。
- 已修复为 `default=False`（2026-05-15）。
- 工具包装器 (`dongchedi_tool.py`) 逻辑：headless=True时不传--headed；headless=False时传--headed。

## 输出格式
脚本输出JSON，包含：
- `matched_count`: 当前匹配车源数
- `new_count` / `removed_count` / `changed_count`: 相对于上次的变化
- `items`: 当前所有车源详情
- `delta.new / .removed / .changed`: 变化详情

## 注意
- 懂车帝可能有反爬验证，首次需要在headed模式下手动完成验证并保存profile
- profile目录: `~/.crawl4ai/profiles/dongchedi_profile`
- 每次运行会写入 `listings` 表（当前快照）和 `listings_history` 表（历史记录）
- 数据库 schema 无 `runs` 表 — 通过 `listings_history` 的 `fetched_at` 字段追踪历史
