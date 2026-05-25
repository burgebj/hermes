---
name: autohome-param-extract
description: 从汽车之家(autohome.com.cn)参数配置页提取车型参数数据，适用于Next.js/React动态渲染页面
---

# Autohome 参数页数据提取

从汽车之家(autohome.com.cn)的参数配置页提取车型参数数据。

## 背景

汽车之家参数配置页使用 Next.js (React) 渲染，传统的页面快照(snapshot)和 accessibility tree 都不包含参数值数据。API 接口直接请求返回 404/500。参数数据隐藏在 JavaScript 渲染的内容中。

## 解决方案

通过 `browser_console` 执行 JavaScript，直接提取 `document.body.innerText` 获取完整文本内容，比 accessibility tree 更完整。

```javascript
// 方法1：直接获取全页文本
(() => { 
  const allText = document.body.innerText; 
  const lines = allText.split('\n'); 
  let result = [];
  for(let i = 0; i < lines.length; i++) { 
    const line = lines[i].trim(); 
    if(line && line.length > 1) { result.push(line); } 
  } 
  return result.slice(0, 200).join('\n'); 
})()

// 方法2：查找品牌下的车型链接（品牌列表页）
(() => { 
  const dts = document.querySelectorAll('dt'); 
  let targetDt = null; 
  for(let dt of dts) { 
    if(dt.textContent.trim() === '乐道') { targetDt = dt; break; } 
  } 
  if(!targetDt) return 'not found'; 
  const dd = targetDt.nextElementSibling; 
  if(!dd) return 'dd not found'; 
  const items = dd.querySelectorAll('li'); 
  let results = []; 
  for(let li of items) { 
    const name = li.querySelector('h4'); 
    const link = li.querySelector('h4 a') || li.querySelector('a'); 
    if(name && name.textContent.includes('L90')) return link ? link.href : 'no link'; 
  } 
  return 'L90 not found'; 
})()
```

## 关键步骤

1. 先访问 `https://www.autohome.com.cn/grade/carhtml/L.html` 品牌字母列表页
2. 用 JS 找到品牌 dt 元素，通过 `nextElementSibling` 找到 dd，再找具体车型链接
3. 获取车型 ID（如 8045=乐道L90, 8273=零跑D19）
4. 访问 `https://www.autohome.com.cn/config/series/{ID}.html`
5. 用 `document.body.innerText` 提取所有参数行

## 乐道/零跑车型ID（截至2026年4月）

- 乐道L90: 8045
- 乐道L90: 8045
- 比亚迪大唐 (BYD Datang): 系列ID不固定，通过字母品牌列表页 `/grade/carhtml/B.html` → 找到"比亚迪" → 点击"大唐"链接进入车系首页 → 点击"参数配置"进入配置页
- 零跑D19: 8273
- 零跑D99: 8257
- 比亚迪唐 (BYD Tang, old): 不同ID，通过 `/grade/carhtml/B.html` 找

## 数据可靠性注意

autohome页面参数数据可能存在错误或过时，用户会直接纠正（如之前乐道L90价格被用户纠正）。提取数据后：
- 页面标注"暂无"的参数值不要猜测，标记为"未公开"
- 多个配置显示相同数据不代表全部配置相同（autohome会合并相同值，但实际各配置可能有差异）
- 涉及关键差异的参数（如转弯半径、轮距等）建议与懂车帝等第二数据源交叉验证
- **注意**：当前对话中发现零跑D19页面统一显示转弯半径3.6m，但用户指出三电机性能版才具有此数据，说明页面可能存在错误

## 重要教训

- **vision工具注意**：browser_vision 依赖多模态模型，当前使用的模型可能不支持视觉分析（会返回400错误）。`document.body.innerText` 是唯一可靠提取手段
- **搜索页面不工作**：autohome的搜索页面会重定向到首页，无法用搜索URL直接访问车型
- **品牌列表页+JS提取**：正确方法是访问字母品牌列表页（`/grade/carhtml/{Letter}.html`），用 JS 遍历 dt/dd 找到品牌和车型链接
- **直接猜ID不可靠**：车型ID每年变化，必须通过列表页实际获取

## 适用场景

- autohome 参数配置页
- 其他 Next.js/React 渲染的动态页面
- accessibility tree 捕获不到文本的情况