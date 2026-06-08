## 📣 Latest Updates

- **Merge conflicts resolved** — branch synced with upstream main (2026-06-04)
- **@Yuxin-Qiao's helper PR merged** — adds Vitest tests for locale key parity + normalizeLocale coverage
- **Thank you @Yuxin-Qiao** for the thorough review and contributions!

---

## 🇬🇧 English

### Hermes Desktop — Multilingual i18n Support (8 Languages)

We love Hermes Agent. It's the most capable open-source AI agent we've ever used, and we wanted to make it accessible to everyone, regardless of their native language.

### What This PR Does

Adds full internationalization (i18n) support to the Hermes Desktop (Electron) app with **8 languages**:

| Language | Code | Coverage |
|----------|------|----------|
| English (source) | en | 857/857 (100%) |
| 简体中文 | zh-CN | 843/857 (98.4%) |
| 繁體中文 | zh-Hant | 840/857 (98.0%) |
| 日本語 | ja | 835/857 (97.4%) |
| 한국어 | ko | 842/857 (98.2%) |
| Deutsch | de | 817/857 (95.3%) |
| Español | es | 835/857 (97.4%) |
| Français | fr | 824/857 (96.1%) |

### Architecture

- **Auto-discovery**: uses Vite `import.meta.glob` — drop a new `{code}.json` file in `src/locales/` and it's automatically available. **No code changes needed** to add a 9th language.
- **React Context**: `I18nProvider` wraps the app root, `useTranslation()` hook for components
- **Standalone `t()` function**: for non-React code (statusbar, gateway boot, overlays)
- **`useLocaleSync()`**: forces re-render of components using standalone `t()` when locale changes
- **Language switcher**: globe + language icon combo button in the titlebar
- **System language auto-detection**: defaults to the OS language
- **Persistent**: saves preference to localStorage

### Translation Guide

See `src/locales/TRANSLATING.md` for how to add a new language. The source of truth is `en.json` with 857 keys across 41 sections.

### Files Changed

- **59 files**: 6,500+ insertions, 540 deletions
- Core: `store/i18n.tsx`, `hooks/use-translation.ts`, `store/use-locale-sync.ts`, `main.tsx`
- Locale files: 8 JSON files in `src/locales/`
- Components: ~50 files across settings, shell, chat, overlays, sidebars, command center

### Closes

Closes #37897, Closes #38064, Closes #37793, Closes #37562, Closes #37543, Closes #37503, Closes #37295, Closes #33749

---

## 🇨🇳 简体中文

### Hermes 桌面端 — 多语言国际化支持（8 种语言）

我们热爱 Hermes Agent。这是我们用过的最强大的开源 AI 代理，我们希望让每个人都能用自己的母语使用它。

### 本 PR 做了什么

为 Hermes 桌面端添加了完整的 i18n 支持，覆盖 **8 种语言**。详见上方英文表格。

### 架构亮点

- **自动发现**：使用 Vite `import.meta.glob`，只需在 `src/locales/` 放入新的 `{code}.json` 文件即可自动识别。添加第 9 种语言零代码改动。
- **React Context** + **独立 t() 函数** + **useLocaleSync()**
- **语言切换器**：标题栏右上角地球 + 文A 组合按钮
- **系统语言自动检测**，偏好设置持久化存储

### 翻译指南

详见 `src/locales/TRANSLATING.md`。

### 关联 Issues

Closes #37897, #38064, #37793, #37562, #37543, #37503, #37295, #33749

---

## 🇯🇵 日本語

### Hermes Desktop — 多言語 i18n 対応（8 言語）

私たちは Hermes Agent を愛用しています。この素晴らしいオープンソース AI エージェントを、母国語に関係なく誰でも使えるようにしたかったのです。

8 言語に対応し、新しい言語の追加もコード変更不要です。詳細は英語版をご覧ください。

---

## 🇰🇷 한국어

### Hermes Desktop — 다국어 i18n 지원 (8개 언어)

우리는 Hermes Agent를 사랑합니다. 이 뛰어난 오픈소스 AI 에이전트를 모국어에 관계없이 누구나 사용할 수 있도록 만들고 싶었습니다.

8개 언어를 지원하며, 새 언어 추가도 코드 변경 없이 가능합니다. 자세한 내용은 영문 버전을 참조하세요.

---

## 🇩🇪 Deutsch

### Hermes Desktop — Mehrsprachige i18n-Unterstützung (8 Sprachen)

Wir lieben Hermes Agent. Wir wollten diesen großartigen Open-Source-KI-Agenten für jeden zugänglich machen, unabhängig von der Muttersprache.

8 Sprachen werden unterstützt. Neue Sprachen können ohne Code-Änderungen hinzugefügt werden. Details siehe englische Version.

---

## 🇪🇸 Español

### Hermes Desktop — Soporte i18n multilingüe (8 idiomas)

Amamos Hermes Agent. Queríamos hacer que este increíble agente de IA de código abierto fuera accesible para todos, sin importar su idioma nativo.

Soporta 8 idiomas. Añadir un nuevo idioma no requiere cambios de código. Consulta la versión en inglés para más detalles.

---

## 🇫🇷 Français

### Hermes Desktop — Support i18n multilingue (8 langues)

Nous aimons Hermes Agent. Nous voulions rendre cet excellent agent IA open-source accessible à tous, quelle que soit leur langue maternelle.

8 langues sont supportées. L'ajout d'une nouvelle langue ne nécessite aucune modification de code. Voir la version anglaise pour les détails.

---

## 🇹🇼 繁體中文

### Hermes 桌面端 — 多語言國際化支援（8 種語言）

我們熱愛 Hermes Agent。這是我們用過最強大的開源 AI 代理，我們希望讓每個人都能用自己的母語使用它。

8 種語言支援，新增語言無需修改程式碼。詳情請見英文版本。

---

**If you like this project, please ⭐ star and share!**  
**Need another language? Leave a comment — Hermes will maintain this continuously.**  
**如有更多語言需求，請留言，Hermes 將持續維護本項目。**

💬 Follow the discussion: [Project Page](https://github.com/marvin/hermes-desktop-i18n)
