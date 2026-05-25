# Hermes Agent 配置备份

本仓库包含 Hermes Agent 的所有配置、记忆和 Skills。

## 目录结构

```
memories/          # Agent 记忆
  MEMORY.md        # 持久记忆（环境事实、项目约定）
  USER.md          # 用户偏好和配置

config/
  config.yaml      # Agent 配置文件（不含敏感密钥）

skills/            # 所有 Skills（按分类目录）
  apple/           # Apple/macOS 相关
  autonomous-ai-agents/  # AI Agent 委托
  browser/         # 浏览器自动化
  creative/        # 创意内容生成
  data-science/    # 数据科学
  devops/          # DevOps
  dongchedi-l90-watch/  # 懂车帝乐道L90监控
  email/           # 邮件
  gaming/          # 游戏
  github/          # GitHub 工作流
  leisure/         # 休闲娱乐
  mcp/             # MCP 协议
  media/           # 媒体处理
  mlops/           # ML 系统
  note-taking/     # 笔记
  productivity/    # 生产力工具
  research/        # 研究工具（包含 wallstreetcn-news）
  smart-home/      # 智能家居
  social-media/    # 社交媒体
  software-development/  # 软件开发
```

## 恢复方法

```bash
# 克隆本仓库
git clone git@github.com:liuchanchen/hermes-agent.git ~/.hermes_backup

# 恢复记忆
cp ~/.hermes_backup/memories/* ~/.hermes/memories/

# 恢复配置
cp ~/.hermes_backup/config/config.yaml ~/.hermes/config.yaml

# 恢复 Skills（合并，不覆盖已有的自定义 skills）
cp -r ~/.hermes_backup/skills/* ~/.hermes/skills/
```

## 定时任务

- 懂车帝乐道L90二手车监控 — 每天 22:00
- 每日财经早报 — 每天 08:00（华尔街见闻 + 美股总结）

---
*自动备份于 2026-04-24*