---
name: auto-data-cross-verify
description: 多数据源交叉验证中文车型参数（整备质量、尺寸、续航等），对用户报告的数字必须核实且注明来源。
---

# 多数据源车型参数交叉验证

从多个中文汽车数据源获取车型参数，交叉验证一致性后向用户报告。

## 何时使用

- 用户询问车型参数（整备质量/车重/尺寸/续航等）
- 用户要求"交叉验证"
- 需要对比不同配置的车型参数

## 数据源优先级

| 来源 | URL模式 | 优点 | 缺点 |
|------|---------|------|------|
| **汽车之家 (autohome)** | `config/series/{ID}.html` | 参数最详细，按配置分列 | React渲染需browser_console提取 |
| **维基百科 (en)** | `wiki/<Model>` | 规格表标准、简洁 | 只有主流车型、可能有延迟 |
| **维基百科 (zh)** | `zh.wikipedia.org/wiki/<Model>` | 中文规格 | 车型词条覆盖较少 |
| **百度百科 (baike)** | `baike.baidu.com/item/<Name>` | 官方中文资料 | URL编码敏感、参数可能简略 |
| **懂车帝 (dongchedi)** | 反爬严重 | — | 不可靠，有验证码拦截 |

## 工作流程

### 1. 找到车型系列ID（汽车之家）

```
https://www.autohome.com.cn/grade/carhtml/{首字母大写}.html
```

用 JS 查找品牌 dt → nextElementSibling dd → 找车型链接 → 提取ID

### 2. 提取 autohome 参数

访问 `https://www.autohome.com.cn/config/series/{ID}.html`，用 `browser_console` 跑：

```javascript
(() => { const lines = document.body.innerText.split('\n').map(l => l.trim()).filter(l => l && l.length > 1); let result = []; let capture = false; for(let i = 0; i < lines.length; i++) { if(lines[i].includes('整备质量')) capture = true; if(capture) result.push(lines[i]); if(lines[i].includes('最大满载质量') && capture) { result.push(lines[i]); break; } } return result.join('\n'); })()
```

参数行顺序与页面显示的车型列顺序一致（从左到右）。

### 3. 提取维基百科/Baidu Baike 数据

- **英文维基**: 页面 infobox 通常有 "Kerb weight" 或 "Curb weight" 行
- **百度百科**: 用 `browser_console` 执行 `document.body.innerText.substring(0, 5000)` 搜索含量

### 4. 交叉验证原则

- 不同数据源的数据**必须逐条对照**
- autohome 按配置分列的重量，维基通常取四驱版单一值
- 值落在 autohome 范围内 = 一致 ✅
- 值在范围外 = 不一致 ⚠️，需标记
- 不要猜测"暂无"的数据
- 不要假定全部配置数据相同

### 5. 报告格式

```
## 📊 <车型> 整备质量 — 多数据源交叉验证

### 数据源1：汽车之家（按配置分列）

| 车型 | 驱动 | 整备质量 |
|------|:----:|:--------:|
| <配置名> | <后驱/四驱> | **<数字> kg** |
| ... | ... | ... |

### 数据源2：维基百科 / 百度百科

<来源名>：**<数字> kg**（配置说明）

---

### ✅ 交叉验证结论

| 配置 | 汽车之家 | 维基百科 | 结果 |
|:----|:--------:|:--------:|:---:|
| <配置> | <值> | <值> | ✅/⚠️ 一致/不一致 |
```

## 已确认的车型ID（autohome）

- 乐道L90: 8045
- 比亚迪大唐 (BYD Datang): 通过品牌列表页 `/grade/carhtml/B.html` 进
- 零跑D19: 8273
- 零跑D99: 8257

## 已知坑点

- **autohome 搜索重定向**: 搜索页URL `search.autohome.com.cn` 不可用，必须通过品牌字母列表页进
- **百度百科 404**: URL 编码必须正确，如果直接访问 404 说明词条不存在
- **懂车帝有验证码**: 不适用于自动化提取
- **维基百科中文词条覆盖不全**: 新车（如比亚迪大唐）可能没有中文词条
- **autohome 列序**: 提取的整备质量数组列顺序=页面车型从左到右，通过截取"厂商指导价"到"整备质量"段来确认
- **不同年款混排**: autohome 同时显示所有年款，注意区分 2025/2026 款的重量差异
