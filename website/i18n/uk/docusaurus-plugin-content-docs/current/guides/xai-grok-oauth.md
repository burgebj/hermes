---
sidebar_position: 16
title: "xAI Grok OAuth (SuperGrok / X Premium+)"
description: "Увійди за допомогою підписки SuperGrok або X Premium+, щоб використовувати моделі Grok у Hermes Agent — API‑ключ не потрібен"
---

# xAI Grok OAuth (SuperGrok / X Premium+)

Hermes Agent підтримує xAI Grok через браузерний OAuth‑логін проти [accounts.x.ai](https://accounts.x.ai), використовуючи **підписку SuperGrok** ([grok.com](https://x.ai/grok)) або **підписку X Premium+** (пов’язаний обліковий запис X). `XAI_API_KEY` не потрібен — увійди один раз, і Hermes автоматично оновлює твою сесію у фоні.

Коли ти входиш за допомогою облікового запису X з Premium+, xAI автоматично прив’язує статус підписки до твоєї xAI сесії, тому OAuth‑процес працює так само, як і для прямих підписників SuperGrok.

Транспорт повторно використовує адаптер `codex_responses` (xAI надає кінцеву точку у стилі Responses), тому міркування, виклик інструментів, потокове передавання та кешування підказок працюють без змін адаптера.

Той самий OAuth‑токен також використовується кожним прямим доступом до xAI у Hermes — TTS, генерація зображень, генерація відео та транскрипція — тому один вхід охоплює всі чотири.
## Огляд

| Пункт | Значення |
|------|-------|
| Ідентифікатор провайдера | `xai-oauth` |
| Назва для відображення | xAI Grok OAuth (SuperGrok / X Premium+) |
| Тип автентифікації | Browser OAuth 2.0 PKCE (loopback callback) |
| Транспорт | xAI Responses API (`codex_responses`) |
| Модель за замовчуванням | `grok-4.3` |
| Кінцева точка | `https://api.x.ai/v1` |
| Сервер автентифікації | `https://accounts.x.ai` |
| Потрібна змінна оточення | Ні (`XAI_API_KEY` is **not** used for this provider) |
| Підписка | [SuperGrok](https://x.ai/grok) або [X Premium+](https://x.com/i/premium_sign_up) — see note below |
## Prerequisites

- Python 3.9+
- Hermes Agent installed
- Активна підписка **SuperGrok** на твоєму акаунті xAI, **або** підписка **X Premium+** на акаунті X, яким ти входиш (xAI автоматично прив’язує підписку)
- Браузер, доступний на локальній машині (або використай `--no-browser` для віддалених сесій)

:::warning xAI may restrict OAuth API access by tier
Бекенд xAI застосовує власний **білий список** до інтерфейсу OAuth API і був випадок, коли стандартних підписників SuperGrok відхиляло з `HTTP 403` (див. issue [#26847](https://github.com/NousResearch/hermes-agent/issues/26847)), хоча підписка в додатку активна. Якщо OAuth‑вхід успішний у браузері, а інференція повертає 403, встанови `XAI_API_KEY` і переключись на шлях з API‑ключем (`provider: xai`) — цей інтерфейс сьогодні не підлягає такому ж обмеженню.
:::
## Швидкий старт

```bash
# Launch the provider and model picker
hermes model
# → Select "xAI Grok OAuth (SuperGrok / X Premium+)" from the provider list
# → Hermes opens your browser to accounts.x.ai
# → Approve access in the browser
# → Pick a model (grok-4.3 is at the top)
# → Start chatting

hermes
```

Після першого входу облікові дані зберігаються у `~/.hermes/auth.json` і автоматично оновлюються перед закінченням їх терміну дії.
## Вхід вручну

Ти можеш ініціювати вхід, не використовуючи вибір моделі:

```bash
hermes auth add xai-oauth
```

### Віддалені / безголові сесії

На серверах, у контейнерах або в SSH‑сесіях, де немає браузера, Hermes визначає віддалене середовище та виводить URL авторизації замість відкриття браузера.

**Важливо:** слухач loopback все ще працює на віддаленій машині за адресою `127.0.0.1:56121`. Перенаправлення xAI має дістатися *цього* слухача, тому відкриття URL на твоєму ноутбуці завершиться помилкою (`Could not establish connection. We couldn't reach your app.`), якщо ти не переадресуєш порт:

```bash
# In a separate terminal on your local machine:
ssh -N -L 56121:127.0.0.1:56121 user@remote-host

# Then in your SSH session on the remote machine:
hermes auth add xai-oauth --no-browser
# Open the printed authorize URL in your local browser.
```

Через jump‑box / bastion: додай `-J jump-user@jump-host`.

Дивись [OAuth over SSH / Remote Hosts](./oauth-over-ssh.md) для повного покрокового опису, включаючи ланцюги ProxyJump, mosh/tmux та підводні камені ControlMaster.

### Тільки браузерні віддалені середовища (Cloud Shell, Codespaces, EC2 Instance Connect)

Якщо у тебе немає звичайного SSH‑клієнта (наприклад, ти запускаєш Hermes у GCP Cloud Shell, GitHub Codespaces, AWS EC2 Instance Connect, Gitpod або іншій консольній середовищі в браузері), рецепт `ssh -L`, наведений вище, недоступний. Використай `--manual-paste` — Hermes пропускає слухача loopback і дозволяє вставити URL з невдалим зворотним викликом безпосередньо з браузера:

```bash
hermes auth add xai-oauth --manual-paste
# Or via the model picker:
hermes model --manual-paste
```

Дивись [OAuth over SSH / Remote Hosts](./oauth-over-ssh.md#browser-only-remote-cloud-shell--codespaces--ec2-instance-connect) для повного покрокового керівництва. Виправлення регресії для [#26923](https://github.com/NousResearch/hermes-agent/issues/26923).

Якщо сторінка згоди відображає код авторизації безпосередньо на сторінці (поточна поведінка xAI у консольних середовищах) замість перенаправлення на твій `127.0.0.1:56121/callback`, встав **лише сам код** у запит `Callback URL:` — Hermes приймає повний URL, фрагмент запиту `?code=...&state=...` або сам код взаємозамінно.
## Як працює логін

1. Hermes відкриває твій браузер на `accounts.x.ai`.
2. Ти входиш у систему (або підтверджуєш існуючу сесію) і схвалюєш доступ.
3. xAI перенаправляє назад до Hermes, і токени зберігаються у `~/.hermes/auth.json`.
4. Відтоді Hermes оновлює токен доступу у фоні — ти залишаєшся залогіненим, доки не виконаєш `hermes auth remove xai-oauth` або не відкличеш доступ у налаштуваннях свого облікового запису xAI.
## Перевірка стану входу

```bash
hermes doctor
```

Розділ `◆ Auth Providers` покаже поточний стан кожного провайдера, включаючи `xai-oauth`.
## Перемикання моделей

```bash
hermes model
# → Select "xAI Grok OAuth (SuperGrok / X Premium+)"
# → Pick from the model list (grok-4.3 is pinned to the top)
```

Або встанови модель безпосередньо:

```bash
hermes config set model.default grok-4.3
hermes config set model.provider xai-oauth
```
## Довідник конфігурації

Після входу у систему файл `~/.hermes/config.yaml` міститиме:

```yaml
model:
  default: grok-4.3
  provider: xai-oauth
  base_url: https://api.x.ai/v1
```

### Псевдоніми провайдерів

Усі наведені нижче елементи розв’язуються до `xai-oauth`:

```bash
hermes --provider xai-oauth        # canonical
hermes --provider grok-oauth       # alias
hermes --provider x-ai-oauth       # alias
hermes --provider xai-grok-oauth   # alias
```
## Direct-to-xAI інструменти (TTS / Image / Video / Transcription / X Search)

Після входу через OAuth кожен direct-to-xAI інструмент автоматично повторно використовує той самий bearer‑token — **не потрібно окремого налаштування**, якщо ти не хочеш використовувати API‑key.

Щоб вибрати бекенд для кожного інструменту:

```bash
hermes tools
# → Text-to-Speech       → "xAI TTS"
# → Image Generation     → "xAI Grok Imagine (image)"
# → Video Generation     → "xAI Grok Imagine"
# → X (Twitter) Search   → "xAI Grok OAuth (SuperGrok / X Premium+)"
```

Якщо OAuth‑токени вже збережені, вибірник підтверджує це і пропускає запит облікових даних. Якщо ні OAuth, ні `XAI_API_KEY` не встановлені, вибірник пропонує 3‑вибірне меню: OAuth‑логін, вставити API‑key або пропустити.

:::note Відеогенерація вимкнена за замовчуванням
Набір інструментів `video_gen` вимкнено за замовчуванням. Увімкни його в `hermes tools` → `🎬 Video Generation` (натисни пробіл), перш ніж агент зможе викликати `video_generate`. Інакше агент може перейти до вбудованого ComfyUI skill, який також позначений для відеогенерації.
:::

:::note X search автоматично вмикається, коли присутні облікові дані xAI
Набір інструментів `x_search` автоматично вмикається, коли налаштовані облікові дані xAI (OAuth‑токен SuperGrok / X Premium+ або `XAI_API_KEY`). Вимкни його явно через `hermes tools` → `🐦 X (Twitter) Search` (натисни пробіл), якщо не потрібен цей функціонал. Інструмент працює через вбудований у xAI `x_search` Responses API — він працює **або** з твоїм OAuth‑логіном SuperGrok / X Premium+, **або** з платним `XAI_API_KEY`, і надає перевагу OAuth, коли обидва налаштовані (використовує твою підписку замість витрат на API). Схема інструменту прихована від моделі, коли облікові дані xAI не налаштовані, незалежно від того, чи увімкнено набір інструментів.
:::

### Моделі

| Інструмент | Модель | Примітки |
|------|-------|-------|
| Chat | `grok-4.3` | За замовчуванням; авто‑вибирається при вході через OAuth |
| Chat | `grok-4.20-0309-reasoning` | Варіант для reasoning |
| Chat | `grok-4.20-0309-non-reasoning` | Варіант без reasoning |
| Chat | `grok-4.20-multi-agent-0309` | Варіант multi‑agent |
| Image | `grok-imagine-image` | За замовчуванням; ~5–10 с |
| Image | `grok-imagine-image-quality` | Вища якість; ~10–20 с |
| Video | `grok-imagine-video` | Text‑to‑video та image‑to‑video; до 7 референсних зображень |
| TTS | (голос за замовчуванням) | xAI `/v1/tts` endpoint |

Каталог чат‑моделей формується в режимі реального часу з кешу `models.dev` на диску; нові випуски xAI з’являються автоматично після оновлення кешу. `grok-4.3` завжди закріплений у верхній частині списку.
## Змінні середовища

| Змінна | Вплив |
|----------|--------|
| `XAI_BASE_URL` | Перевизначити типову кінцеву точку `https://api.x.ai/v1` (рідко потрібно). |

Щоб вибрати xAI як активного провайдера, встанови `model.provider: xai-oauth` у `config.yaml` (використай `hermes setup` для покрокового процесу) або передай `--provider xai-oauth` для одноразового виклику.
## Усунення проблем

### Токен прострочився — автоматичний повторний вхід не відбувається

Hermes оновлює токен перед кожною сесією та реактивно при отриманні 401. Якщо оновлення не вдається через `invalid_grant` (токен оновлення відкликано або обліковий запис змінено), Hermes виводить типове повідомлення про повторну автентифікацію замість краху.

Коли помилка оновлення є фатальною (HTTP 4xx, `invalid_grant`, відкликаний грант тощо), Hermes позначає токен оновлення як недійсний і локально карантує його — подальші виклики пропускають безнадійні спроби оновлення замість нескінченного повторення 401. Агент виводить одне повідомлення «потрібна повторна автентифікація» і не заважає, доки ти знову не ввійдеш.

**Виправлення:** запусти `hermes auth add xai-oauth` ще раз, щоб розпочати новий вхід. Карантин знімається під час наступного успішного обміну.

### Час очікування авторизації минув

Loopback‑слухач має обмежений час дії (за замовчуванням 180 с). Якщо ти не підтвердив вхід вчасно, Hermes генерує помилку тайм‑ауту.

**Виправлення:** повторно запусти `hermes auth add xai-oauth` (або `hermes model`). Потік почнеться заново.

### Невідповідність стану (можливий CSRF)

Hermes виявив, що значення `state`, отримане від сервера авторизації, не збігається з тим, що було відправлено.

**Виправлення:** повторно пройди процес входу. Якщо проблема зберігається, перевір наявність проксі або перенаправлення, які змінюють відповідь OAuth.

### Вхід з віддаленого сервера

При SSH або в контейнері Hermes виводить URL авторизації замість відкриття браузера. Loopback‑слухач все ще прив’язується до `127.0.0.1:56121` на віддаленому хості — браузер твого ноутбука не зможе до нього дістатися без локального перенаправлення SSH:

```bash
# Local machine, separate terminal:
ssh -N -L 56121:127.0.0.1:56121 user@remote-host

# Remote machine:
hermes auth add xai-oauth --no-browser
```

Повний посібник (jump‑box, mosh/tmux, конфлікти портів): [OAuth over SSH / Remote Hosts](./oauth-over-ssh.md).

### HTTP 403 після успішного входу (рівень / права)

OAuth завершено в браузері, токени збережено, але під час інференсу або оновлення токену повертається `HTTP 403` з повідомленням типу *«Виконавець не має дозволу на виконання зазначеної операції»*.

Це **не** проблема застарілого токену — повторний запуск `hermes model` його не виправить. У бекенді xAI іноді обмежують доступ до OAuth API лише певними рівнями SuperGrok, навіть якщо підписка в додатку активна (issue [#26847](https://github.com/NousResearch/hermes-agent/issues/26847)).

**Виправлення:** встанови `XAI_API_KEY` і перейди на шлях з API‑ключем:

```bash
export XAI_API_KEY=xai-...
hermes config set model.provider xai
```

Або онови підписку на [x.ai/grok](https://x.ai/grok), якщо потрібен саме OAuth‑шлях.

### Помилка «No xAI credentials found» під час виконання

У сховищі автентифікації немає запису `xai-oauth` і змінна `XAI_API_KEY` не встановлена. Ти ще не ввійшов, або файл облікових даних був видалений.

**Виправлення:** запусти `hermes model` і обери провайдера xAI Grok OAuth, або запусти `hermes auth add xai-oauth`.
## Вихід з системи

Щоб видалити всі збережені OAuth‑облікові дані xAI Grok:

```bash
hermes auth logout xai-oauth
```

Це очищає як єдиний запис OAuth у `auth.json`, так і всі рядки пулу облікових даних для `xai-oauth`. Використай `hermes auth remove xai-oauth <index|id|label>`, якщо потрібно видалити лише один запис пулу (виконай `hermes auth list xai-oauth`, щоб переглянути їх).
## Дивись також

- [OAuth over SSH / Remote Hosts](./oauth-over-ssh.md) — обов’язкове читання, якщо Hermes працює на іншій машині, ніж твій браузер
- [AI Providers reference](../integrations/providers.md) — довідка щодо постачальників ШІ
- [Environment Variables](../reference/environment-variables.md) — змінні середовища
- [Configuration](../user-guide/configuration.md) — конфігурація
- [Voice & TTS](../user-guide/features/tts.md) — голос та TTS