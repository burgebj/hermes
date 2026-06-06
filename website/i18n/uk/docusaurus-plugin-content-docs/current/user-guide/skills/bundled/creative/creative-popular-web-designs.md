---
title: "Популярні веб‑дизайни — 54 реальні системи дизайну (Stripe, Linear, Vercel) у HTML/CSS"
sidebar_label: "Popular Web Designs"
description: "54 реальні системи дизайну (Stripe, Linear, Vercel) як HTML/CSS"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Популярні веб‑дизайни

54 реальні системи дизайну (Stripe, Linear, Vercel) у вигляді HTML/CSS.
## Метадані навички

| | |
|---|---|
| Джерело | Вбудовано (встановлено за замовчуванням) |
| Шлях | `skills/creative/popular-web-designs` |
| Версія | `1.0.0` |
| Автор | Hermes Agent + Teknium (design systems sourced from VoltAgent/awesome-design-md) |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
:::info
The following is the complete skill definition that Hermes loads when this skill is triggered. This is what the agent sees as instructions when the skill is active.
:::

# Популярні веб‑дизайни

54 реальних систем дизайну, готових до використання під час генерації HTML/CSS. Кожен шаблон захоплює
повну візуальну мову сайту: кольорову палітру, ієрархію типографіки, стилі компонентів, систему відступів,
тіні, адаптивну поведінку та практичні підказки агенту з точними значеннями CSS.
## Пов’язані навички дизайну

- **`claude-design`** — використовується для процесу та смаку дизайну *process and taste* (визначення обсягу завдання, створення варіантів, перевірка локального HTML‑артефакту, уникнення «AI‑design slop»). Поєднуй цю навичку з іншою, коли користувач хоче продумано оформлену сторінку у стилі відомого бренду: `claude-design` керує робочим процесом, ця навичка постачає візуальну лексику.
- **`design-md`** — використовується, коли результатом має бути формальний файл специфікації токену **DESIGN.md**, а не готовий артефакт.
## Як користуватися

1. Вибери дизайн із каталогу нижче
2. Завантаж його: `skill_view(name="popular-web-designs", file_path="templates/<site>.md")`
3. Використовуй токени дизайну та специфікації компонентів під час генерації HTML
4. Поєднай з навичкою `generative-widgets` для подачі результату через тунель cloudflared

Кожен шаблон містить блок **Hermes Implementation Notes** у верхній частині з:
- заміна шрифту CDN та тегом Google Fonts `<link>` (готовий до вставки)
- стек CSS‑font‑family для основного та моноширинного шрифтів
- нагадуванням використовувати `write_file` для створення HTML та `browser_vision` для перевірки
## Шаблон генерації HTML

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Page Title</title>
  <!-- Paste the Google Fonts <link> from the template's Hermes notes -->
  <link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet">
  <style>
    /* Apply the template's color palette as CSS custom properties */
    :root {
      --color-bg: #ffffff;
      --color-text: #171717;
      --color-accent: #533afd;
      /* ... more from template Section 2 */
    }
    /* Apply typography from template Section 3 */
    body {
      font-family: 'Inter', system-ui, sans-serif;
      color: var(--color-text);
      background: var(--color-bg);
    }
    /* Apply component styles from template Section 4 */
    /* Apply layout from template Section 5 */
    /* Apply shadows from template Section 6 */
  </style>
</head>
<body>
  <!-- Build using component specs from the template -->
</body>
</html>
```

Запиши файл за допомогою `write_file`, запусти його за допомогою workflow `generative-widgets` (тунель cloudflared) і перевір результат за допомогою `browser_vision`, щоб підтвердити візуальну відповідність.
## Довідник заміни шрифтів

Більшість сайтів використовують пропрієтарні шрифти, недоступні через CDN. Кожен шаблон має заміну на Google Fonts, яка зберігає характер дизайну. Типові відповідності:

| Пропрієтарний шрифт | Замінник CDN | Характеристика |
|---|---|---|
| Geist / Geist Sans | Geist (на Google Fonts) | Геометричний, стислий кернінг |
| Geist Mono | Geist Mono (на Google Fonts) | Чистий моноширинний, лігатури |
| sohne‑var (Stripe) | Source Sans 3 | Легка елегантність |
| Berkeley Mono | JetBrains Mono | Технічний моноширинний |
| Airbnb Cereal VF | DM Sans | Округлий, дружній геометричний |
| Circular (Spotify) | DM Sans | Геометричний, теплий |
| figmaSans | Inter | Чистий гуманістичний |
| Pin Sans (Pinterest) | DM Sans | Дружній, округлий |
| NVIDIA‑EMEA | Inter (або системний Arial) | Індустріальний, чистий |
| CoinbaseDisplay/Sans | DM Sans | Геометричний, надійний |
| UberMove | DM Sans | Жирний, щільний |
| HashiCorp Sans | Inter | Корпоративний, нейтральний |
| waldenburgNormal (Sanity) | Space Grotesk | Геометричний, трохи стиснутий |
| IBM Plex Sans/Mono | IBM Plex Sans/Mono | Доступний у Google Fonts |
| Rubik (Sentry) | Rubik | Доступний у Google Fonts |

Коли шрифт CDN шаблону збігається з оригінальним (Inter, IBM Plex, Rubik, Geist), втрата якості не відбувається. Коли використовується заміна (DM Sans для Circular, Source Sans 3 для sohne‑var), слід точно дотримуватись значень **ваги**, **розміру** та **міжлітерного інтервалу** шаблону — вони несуть більше візуальної ідентичності, ніж конкретний шрифт.
## Каталог дизайну

### AI & Machine Learning

| Template | Site | Style |
|---|---|---|
| `claude.md` | Anthropic Claude | Теплий терракотовий акцент, чистий редакційний макет |
| `cohere.md` | Cohere | Яскраві градієнти, естетика інформаційної панелі, багата даними |
| `elevenlabs.md` | ElevenLabs | Темний кінематографічний інтерфейс, естетика аудіо‑хвиль |
| `minimax.md` | Minimax | Смiливий темний інтерфейс з неоновими акцентами |
| `mistral.ai.md` | Mistral AI | Французький інженерний мінімалізм, фіолетовий тон |
| `ollama.md` | Ollama | Терминал‑перше, монохромна простота |
| `opencode.ai.md` | OpenCode AI | Темна тема, орієнтована на розробників, повністю моноширинний |
| `replicate.md` | Replicate | Чисте біле полотно, код‑центричний |
| `runwayml.md` | RunwayML | Темний кінематографічний UI, медіа‑насичений макет |
| `together.ai.md` | Together AI | Технічний, дизайн у стилі креслення |
| `voltagent.md` | VoltAgent | Чорне полотно, смарагдовий акцент, термінал‑нативний |
| `x.ai.md` | xAI | Суворий монохром, футуристичний мінімалізм, повністю моноширинний |

### Developer Tools & Platforms

| Template | Site | Style |
|---|---|---|
| `cursor.md` | Cursor | Стриманий темний інтерфейс, градієнтні акценти |
| `expo.md` | Expo | Темна тема, щільний міжлітерний інтервал, код‑центричний |
| `linear.app.md` | Linear | Ультра‑мінімальний темний режим, точний, фіолетовий акцент |
| `lovable.md` | Lovable | Граціозні градієнти, дружня естетика для розробників |
| `mintlify.md` | Mintlify | Чистий, зелений акцент, оптимізований для читання |
| `posthog.md` | PostHog | Грайливий брендинг, темний UI, дружній до розробників |
| `raycast.md` | Raycast | Стриманий темний хром, яскраві градієнтні акценти |
| `resend.md` | Resend | Мінімальна темна тема, моноширинні акценти |
| `sentry.md` | Sentry | Темна панель, насичена даними, рожево‑фіолетовий акцент |
| `supabase.md` | Supabase | Темна смарагдова тема, інструмент для розробників, орієнтований на код |
| `superhuman.md` | Superhuman | Преміальний темний UI, клавіатура‑перше, фіолетове сяйво |
| `vercel.md` | Vercel | Чорно‑білий точний дизайн, система шрифтів Geist |
| `warp.md` | Warp | Темний інтерфейс у стилі IDE, блоковий інтерфейс команд |
| `zapier.md` | Zapier | Теплий оранжевий, дружня ілюстрація‑орієнтована |

### Infrastructure & Cloud

| Template | Site | Style |
|---|---|---|
| `clickhouse.md` | ClickHouse | Жовтий акцент, стиль технічної документації |
| `composio.md` | Composio | Сучасний темний дизайн з яскравими іконками інтеграцій |
| `hashicorp.md` | HashiCorp | Підприємницький чистий, чорно‑білий |
| `mongodb.md` | MongoDB | Зелене листя бренду, фокус на документації для розробників |
| `sanity.md` | Sanity | Червоний акцент, контент‑перше, редакційний макет |
| `stripe.md` | Stripe | Підписні фіолетові градієнти, елегантність weight‑300 |

### Design & Productivity

| Template | Site | Style |
|---|---|---|
| `airtable.md` | Airtable | Барвистий, дружній, естетика структурованих даних |
| `cal.md` | Cal.com | Чистий нейтральний UI, простота, орієнтована на розробників |
| `clay.md` | Clay | Органічні форми, м’які градієнти, арт‑дирекційний макет |
| `figma.md` | Figma | Яскраві багатокольорові, грайливі, але професійні |
| `framer.md` | Framer | Смiливий чорний і синій, motion‑first, дизайн‑орієнтований |
| `intercom.md` | Intercom | Дружня синя палітра, розмовні UI‑патерни |
| `miro.md` | Miro | Яскравий жовтий акцент, безмежне полотно |
| `notion.md` | Notion | Теплий мінімалізм, заголовки з засічками, м’які поверхні |
| `pinterest.md` | Pinterest | Червоний акцент, мозаїчний сітковий макет, орієнтований на зображення |
| `webflow.md` | Webflow | Синій акцент, полірований маркетинговий сайт, естетика |

### Fintech & Crypto

| Template | Site | Style |
|---|---|---|
| `coinbase.md` | Coinbase | Чистий синій ідентифікатор, орієнтований на довіру, інституційний вигляд |
| `kraken.md` | Kraken | Фіолетовий акцент, темний UI, насичені даними панелі |
| `revolut.md` | Revolut | Стриманий темний інтерфейс, градієнтні картки, точність фінтеху |
| `wise.md` | Wise | Яскравий зелений акцент, дружній та зрозумілий |

### Enterprise & Consumer

| Template | Site | Style |
|---|---|---|
| `airbnb.md` | Airbnb | Теплий кораловий акцент, орієнтований на фотографії, округлий UI |
| `apple.md` | Apple | Преміальний простір, SF Pro, кінематографічні зображення |
| `bmw.md` | BMW | Темні преміум‑поверхні, точна інженерна естетика |
| `ibm.md` | IBM | Система Carbon, структурована синя палітра |
| `nvidia.md` | NVIDIA | Зелено‑чорна енергія, технічна потужна естетика |
| `spacex.md` | SpaceX | Суворий чорний і білий, повноекранні зображення, футуристичний |
| `spotify.md` | Spotify | Яскравий зелений на темному фоні, сміливий шрифт, орієнтований на обкладинки альбомів |
| `uber.md` | Uber | Сміливий чорний і білий, щільний шрифт, міська енергія |
## Вибір дизайну

Підбери дизайн відповідно до контенту:

- **Інструменти розробника / дашборди:** Linear, Vercel, Supabase, Raycast, Sentry
- **Документація / контент‑сайти:** Mintlify, Notion, Sanity, MongoDB
- **Маркетинг / посадкові сторінки:** Stripe, Framer, Apple, SpaceX
- **Темні інтерфейси:** Linear, Cursor, ElevenLabs, Warp, Superhuman
- **Світлі / чисті інтерфейси:** Vercel, Stripe, Notion, Cal.com, Replicate
- **Грайливі / дружні:** PostHog, Figma, Lovable, Zapier, Miro
- **Преміум / розкішні:** Apple, BMW, Stripe, Superhuman, Revolut
- **Насичені даними / дашборди:** Sentry, Kraken, Cohere, ClickHouse
- **Моноширинний / термінальний стиль:** Ollama, OpenCode, x.ai, VoltAgent