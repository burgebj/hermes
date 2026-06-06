---
sidebar_position: 17
title: "OAuth через SSH / віддалені хости"
description: "Як завершити браузерний OAuth (xAI, Spotify, MCP servers), коли Hermes працює на віддаленій машині, у контейнері або за межами jump box."
---

# OAuth over SSH / Remote Hosts

Деякі провайдери Hermes — **xAI Grok OAuth**, **Spotify** та **remote MCP servers** (Linear, Sentry, Atlassian, Asana, Figma, …) — використовують *loopback‑redirect* OAuth‑потік. Сервер автентифікації перенаправляє твій браузер на `http://127.0.0.1:<port>/callback`, щоб невеликий HTTP‑прослуховувач, запущений Hermes, міг отримати код авторизації.

Це працює ідеально, коли Hermes і твій браузер знаходяться на одній машині. Воно ламається, щойно вони розділені: браузер твого ноутбука намагається дістатися `127.0.0.1` на **твоєму ноутбуці**, а прослуховувач прив’язаний до `127.0.0.1` на **віддаленому сервері**.

Виправлення — однорядковий SSH local‑forward — **або**, якщо у тебе немає реального SSH‑клієнта (GCP Cloud Shell, GitHub Codespaces, EC2 Instance Connect, Gitpod, веб‑IDE в браузері), новий прапорець `--manual-paste`, представлений у [#26923](https://github.com/NousResearch/hermes-agent/issues/26923).
## TL;DR

```bash
# On your local machine (laptop), in a separate terminal:
ssh -N -L 56121:127.0.0.1:56121 user@remote-host

# In your existing SSH session on the remote machine:
hermes auth add xai-oauth --no-browser
# → Hermes prints an authorize URL. Open it in a browser on your laptop.
# → Your browser redirects to 127.0.0.1:56121/callback, the tunnel forwards
#   the request to the remote listener, login completes.
```

Порт `56121` — це порт, який використовує xAI OAuth. Для Spotify заміни його на `43827`. Hermes виводить точний порт, до якого він прив’язався, у рядку `Waiting for callback on ...` — скопіюй його звідти.
## Browser-only remote (Cloud Shell / Codespaces / EC2 Instance Connect)

Якщо у тебе немає звичайного SSH‑клієнта — наприклад, тому що ти запускаєш Hermes всередині GCP Cloud Shell, GitHub Codespaces, AWS EC2 Instance Connect, Gitpod або іншої браузерної консолі — тунель SSH, описаний вище, недоступний. Використай `--manual-paste` замість цього:

```bash
hermes auth add xai-oauth --manual-paste
# → Hermes prints an authorize URL. Open it in a browser on your laptop.
# → Approve in the browser. The redirect to 127.0.0.1:56121/callback fails
#   to load — that's expected.
# → Copy the FULL URL from the failed page's address bar.
# → Paste it back into the terminal at the "Callback URL:" prompt.
```

Те саме прапорець працює з `hermes model --manual-paste` для вбудованого вибирача моделей. Hermes приймає три форми вставки зворотного виклику взаємозамінно: повний URL, чистий фрагмент запиту `?code=...&state=...` або — коли сторінка згоди upstream відображає код авторизації в самій сторінці замість перенаправлення (поточна поведінка xAI у браузерних консолях) — просто чисте значення коду окремо.

Hermes використовує **той самий PKCE‑верифікатор, state і nonce** для обох шляхів, тому upstream‑OAuth‑процес ідентичний на рівні байтів — `--manual-paste` лише змінює транспорт для кроку зворотного виклику і не знижує безпеку.
## Які провайдери потребують цього

| Провайдер | Порт loopback | Чи потрібен тунель? |
|----------|---------------|----------------------|
| `xai-oauth` (Grok SuperGrok) | `56121` | Так, коли Hermes працює віддалено |
| Spotify | `43827` | Так, коли Hermes працює віддалено |
| MCP servers (`auth: oauth`) | вибирається автоматично для кожного сервера | Так, коли Hermes працює віддалено |
| `anthropic` (Claude Pro/Max) | n/a | Ні — потік вставки коду |
| `openai-codex` (ChatGPT Plus/Pro) | n/a | Ні — потік коду пристрою |
| `minimax`, `nous-portal` | n/a | Ні — потік коду пристрою |

Якщо твій провайдер не в таблиці, тунель не потрібен.
## Сервери MCP

Віддалені сервери MCP (Linear, Sentry, Atlassian, Asana, Figma тощо) використовують той самий цикл loopback‑перенаправлення. Hermes автоматично вибирає вільний порт для кожного сервера і виводить URL авторизації, коли запускається OAuth‑потік — або під час старту (коли новий сервер з’являється в `mcp_servers:`), або коли ти виконуєш `hermes mcp login <server>`.

У тебе є два способи завершити його з віддаленого хоста:

**Варіант 1 — вставити URL перенаправлення назад (без налаштувань, працює будь‑де).** У інтерактивному терміналі Hermes пропонує вставити URL перенаправлення під час запуску локального слухача. Після підтвердження у браузері перенаправлення на `http://127.0.0.1:<port>/callback` покаже помилку підключення — це очікувано. Скопіюй **повний URL з адресного рядка браузера** і встав його у підказку Hermes:

```
  MCP OAuth: authorization required.
  Open this URL in your browser:

    https://mcp.linear.app/authorize?response_type=code&...

  Or paste the redirect URL here (or the ?code=...&state=... portion) and press Enter:
> https://mcp.linear.app/callback?code=abc123&state=xyz
  Got authorization code from paste — completing flow.
```

Приймається також «голий» рядок запиту `?code=...&state=...`. Це працює з будь‑яким сервером MCP, у якому `auth: oauth`, і не потребує змін у конфігурації SSH.

**Варіант 2 — SSH‑перенаправлення порту (те саме, що xAI / Spotify).** Hermes виводить точний порт, який він прив’язав, у підказці SSH‑сесії. Відкрий окремий термінал на ноутбуці:

```bash
ssh -N -L <port>:127.0.0.1:<port> user@remote-host
```

Потім відкрий URL авторизації у браузері звичайним способом; перенаправлення пройде через тунель, і слухач його підхопить. Використовуй цей спосіб, коли потрібно завершити процес без участі користувача (наприклад, скриптове повторне авторизування, коли неможливо вставляти дані вручну).

**Підводний камінь — гонка 30‑секундного перезавантаження конфігурації.** Якщо ти редагуєш `~/.hermes/config.yaml`, додаючи OAuth‑сервер MCP, всередині запущеної сесії Hermes, CLI автоматично перезавантажує з’єднання MCP з тайм‑аутом у 30 секунд. Це недостатньо часу, щоб завершити інтерактивний OAuth‑потік, і перезавантаження завершиться невдачею. Використай `hermes mcp login <server>` у новому терміналі — там немає такого обмеження, і процес чекатиме повних 5 хвилин, щоб ти міг вставити URL назад.
## Чому прослуховувач не може просто прив’язатися до 0.0.0.0

xAI і Spotify обидва перевіряють параметр `redirect_uri` проти білого списку. Обидва вимагають форму loopback (`http://127.0.0.1:<exact-port>/callback`). Прив’язка прослуховувача до `0.0.0.0` або іншого порту призведе до того, що сервер автентифікації відхилить запит через невідповідність `redirect_uri`. SSH‑тунель зберігає loopback‑URI недоторканим від початку до кінця.
## Крок за кроком: один SSH‑перехід

### 1. Запусти тунель зі свого локального комп’ютера

```bash
# xAI Grok OAuth (port 56121)
ssh -N -L 56121:127.0.0.1:56121 user@remote-host

# Or for Spotify (port 43827)
ssh -N -L 43827:127.0.0.1:43827 user@remote-host
```

`-N` означає «не відкривати віддалений шелл, просто тримати тунель відкритим». Тримай цей термінал запущеним протягом усього процесу входу.

### 2. В окремій SSH‑сесії виконай команду авторизації

```bash
ssh user@remote-host
hermes auth add xai-oauth --no-browser
# or for Spotify:
# hermes auth add spotify --no-browser
```

Hermes виявляє SSH‑сесію, пропускає автоматичне відкриття браузера і виводить URL для авторизації та рядок `Waiting for callback on http://127.0.0.1:<port>/callback`.

### 3. Відкрий URL у своєму локальному браузері

Скопіюй URL для авторизації з віддаленого терміналу і встав його у браузер на ноутбуці. Підтверди екран згоди. Сервер авторизації перенаправляє на `http://127.0.0.1:<port>/callback`. Твій браузер потрапляє в тунель, запит передається віддаленому слухачу, і Hermes виводить `Login successful!`.

Ти можеш зупинити тунель (Ctrl+C у першому терміналі), коли побачиш рядок успішного входу.
## Крок за кроком: через jump‑box

Якщо ти підключаєшся до Hermes через bastion / jump‑host, використай вбудований у SSH параметр `-J` (ProxyJump):

```bash
ssh -N -L 56121:127.0.0.1:56121 -J jump-user@jump-host user@final-host
```

Це створює ланцюжок SSH‑з’єднань через jump‑host, не розміщуючи порт loopback безпосередньо на jump‑box. Локальний `127.0.0.1:56121` на твоєму ноутбуці тунелює прямо до `127.0.0.1:56121` на кінцевому віддаленому хості.

Для старіших версій OpenSSH, які не підтримують `-J`, використовується довга форма:

```bash
ssh -N \
    -o "ProxyCommand=ssh -W %h:%p jump-user@jump-host" \
    -L 56121:127.0.0.1:56121 \
    user@final-host
```
## Mosh, tmux, ssh ControlMaster

Тунель є властивістю базового SSH‑з’єднання. Якщо ти запускаєш Hermes всередині `tmux` через сесію mosh, то роумінг mosh не передає `-L`‑перенаправлення. Відкрий *окрему* звичайну SSH‑сесію **лише** для `-L`‑тунелю — це з’єднання має залишатися активним протягом процесу автентифікації. Твоя інтерактивна сесія mosh/tmux може продовжувати працювати з Hermes у звичайному режимі.

Якщо ти використовуєш `ssh -o ControlMaster=auto`, порт‑перенаправлення на мультиплексованому з’єднанні спільно використовують час життя майстра. Перезапусти майстра, якщо тунель не піднімається:

```bash
ssh -O exit user@remote-host
ssh -N -L 56121:127.0.0.1:56121 user@remote-host
```
## Усунення проблем

### `bind [127.0.0.1]:56121: Address already in use`

Щось на твоєму ноутбуці вже використовує цей порт. Або попередній тунель не завершився коректно, або локальний Hermes теж слухає його. Знайди і завершити процес‑порушник:

```bash
# macOS / Linux
lsof -iTCP:56121 -sTCP:LISTEN
kill <PID>
```

Потім повтори команду `ssh -L`.

### "Could not establish connection. We couldn't reach your app." (xAI)

Сторінка авторизації xAI показує це, коли її перенаправлення на `127.0.0.1:<port>/callback` не досягає слухача. Або тунель не запущений, порт неправильний, або ти використовуєш порт, який вивів Hermes у попередньому запуску (порт може бути автоматично змінений, якщо бажаний зайнятий — завжди читай останній рядок `Waiting for callback on ...`).

### `xAI authorization timed out waiting for the local callback`

Те ж саме, що й вище — перенаправлення ніколи не повернулося. Перевір, що тунель ще живий (`ssh -N` не виводить нічого, тому подивися у термінал, з якого його запустив), перезапусти його за потреби і знову виконай `hermes auth add xai-oauth --no-browser`.

### Tokens land in the wrong `~/.hermes`

Токени записуються під Linux‑користувачем, який виконав `hermes auth add …`. Якщо твій gateway / сервіс systemd працює під іншим користувачем (наприклад, `root` або спеціальним користувачем `hermes`), аутентифікуйся **цим** користувачем, щоб токени потрапили у його `~/.hermes/auth.json`. `sudo -u hermes -i` або еквівалент.
## Дивись також

- [xAI Grok OAuth](./xai-grok-oauth.md)
- [Spotify (`Running over SSH`)](../user-guide/features/spotify.md#running-over-ssh--in-a-headless-environment)
- [Native MCP client (розділ OAuth)](../user-guide/features/mcp.md#oauth-authenticated-http-servers)
- [SSH `-J` / ProxyJump (man‑сторінка)](https://man.openbsd.org/ssh#J)