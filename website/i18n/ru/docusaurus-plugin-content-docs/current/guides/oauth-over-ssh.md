---
sidebar_position: 17
title: "OAuth через SSH / удалённые хосты"
description: "Как завершить браузерный OAuth (xAI, Spotify, MCP servers), когда Hermes работает на удалённой машине, в контейнере или за промежуточным сервером."
---

# OAuth over SSH / Remote Hosts

Некоторые провайдеры Hermes — **xAI Grok OAuth**, **Spotify** и **удалённые MCP‑серверы** (Linear, Sentry, Atlassian, Asana, Figma, …) — используют поток OAuth с *loopback redirect*. Сервер аутентификации перенаправляет твой браузер на `http://127.0.0.1:<port>/callback`, чтобы крошечный HTTP‑слушатель, запущенный Hermes, смог захватить код авторизации.

Это работает идеально, когда Hermes и твой браузер находятся на одной машине. Как только они находятся на разных устройствах, всё ломается: браузер твоего ноутбука пытается достичь `127.0.0.1` **на твоём ноутбуке**, а слушатель привязан к `127.0.0.1` **на удалённом сервере**.

Решение — однострочный SSH‑local‑forward — **или**, если у тебя нет реального SSH‑клиента (GCP Cloud Shell, GitHub Codespaces, EC2 Instance Connect, Gitpod, веб‑IDE в браузере), новый флаг `--manual-paste`, добавленный в [#26923](https://github.com/NousResearch/hermes-agent/issues/26923).
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

Порт `56121` — это порт, который использует xAI OAuth. Для Spotify замени его на `43827`. Hermes выводит точный порт, к которому привязан, в строке `Waiting for callback on ...` — скопируй его оттуда.
## Browser-only remote (Cloud Shell / Codespaces / EC2 Instance Connect)

Если у тебя нет обычного SSH‑клиента — например, потому что ты запускаешь Hermes внутри GCP Cloud Shell, GitHub Codespaces, AWS EC2 Instance Connect, Gitpod или другой консоли в браузере — туннель SSH, описанный выше, недоступен. Используй `--manual-paste` вместо него:

```bash
hermes auth add xai-oauth --manual-paste
# → Hermes prints an authorize URL. Open it in a browser on your laptop.
# → Approve in the browser. The redirect to 127.0.0.1:56121/callback fails
#   to load — that's expected.
# → Copy the FULL URL from the failed page's address bar.
# → Paste it back into the terminal at the "Callback URL:" prompt.
```

Тот же флаг работает в `hermes model --manual-paste` для встроенного выбора модели. Hermes принимает три формы вставки обратного вызова взаимозаменяемо: полный URL, «голый» фрагмент запроса `?code=...&state=...` или — когда страница согласия upstream выводит код авторизации на странице вместо перенаправления (текущее поведение xAI в браузерных консолях) — просто значение кода без обёртки.

Hermes использует **один и тот же PKCE‑верификатор, state и nonce** для обоих путей, поэтому upstream‑поток OAuth идентичен побайтно — `--manual-paste` меняет лишь способ транспортировки обратного вызова и не ухудшает безопасность.
## Каким провайдерам это нужно

| Provider | loopback‑порт | Требуется туннель? |
|----------|---------------|--------------------|
| `xai-oauth` (Grok SuperGrok) | `56121` | Да, если Hermes работает удалённо |
| Spotify | `43827` | Да, если Hermes работает удалённо |
| MCP servers (`auth: oauth`) | auto-picked per server | Да, если Hermes работает удалённо |
| `anthropic` (Claude Pro/Max) | n/a | Нет — paste‑the‑code flow |
| `openai-codex` (ChatGPT Plus/Pro) | n/a | Нет — device code flow |
| `minimax`, `nous-portal` | n/a | Нет — device code flow |

Если твой провайдер отсутствует в таблице, туннель не нужен.
## MCP‑серверы

Удалённые MCP‑серверы (Linear, Sentry, Atlassian, Asana, Figma и др.) используют тот же поток перенаправления loopback. Hermes автоматически выбирает свободный порт для каждого сервера и выводит URL авторизации, когда запускается OAuth‑поток — либо при старте (когда в `mcp_servers:` появляется новый сервер), либо когда ты вызываешь `hermes mcp login <server>`.

У тебя есть два способа завершить процесс с удалённого хоста:

**Вариант 1 — вставить URL перенаправления обратно (без настройки, работает везде).** В интерактивном терминале Hermes предлагает вставить URL перенаправления одновременно с запуском локального слушателя. После подтверждения в браузере перенаправление на `http://127.0.0.1:<port>/callback` покажет ошибку соединения — это ожидаемо. Скопируй **полный URL из адресной строки браузера** и вставь его в запрос Hermes:

```
  MCP OAuth: authorization required.
  Open this URL in your browser:

    https://mcp.linear.app/authorize?response_type=code&...

  Or paste the redirect URL here (or the ?code=...&state=... portion) and press Enter:
> https://mcp.linear.app/callback?code=abc123&state=xyz
  Got authorization code from paste — completing flow.
```

Также принимается «голый» запрос `?code=...&state=...`. Это работает с любым MCP‑сервером, у которого `auth: oauth`, и не требует изменений конфигурации SSH.

**Вариант 2 — SSH‑перенаправление порта (как у xAI / Spotify).** Hermes выводит точный порт, к которому привязан, в подсказке SSH‑сессии. Открой отдельный терминал на ноутбуке:

```bash
ssh -N -L <port>:127.0.0.1:<port> user@remote-host
```

Затем открой URL авторизации в браузере как обычно; перенаправление проходит через туннель, и слушатель его получает. Используй это, когда процесс должен завершиться без вмешательства (например, скриптовая переаутентификация, когда нельзя вставлять вручную).

**Подводный камень — гонка перезагрузки конфигурации за 30 сек.** Если ты редактируешь `~/.hermes/config.yaml`, добавляя OAuth‑MCP‑сервер, изнутри запущенной сессии Hermes, CLI автоматически перезагружает MCP‑соединения с тайм‑аутом в 30 сек. Это недостаточно времени для завершения интерактивного OAuth‑потока, и перезагрузка прервётся. Запусти `hermes mcp login <server>` в новом терминале — там нет такого ограничения, и он ждёт полные 5 минут, пока ты вставишь URL обратно.
## Почему прослушиватель не может просто привязаться к 0.0.0.0

xAI и Spotify проверяют параметр `redirect_uri` по списку разрешённых значений. Оба требуют loopback‑форму (`http://127.0.0.1:<exact-port>/callback`). Привязка прослушивателя к `0.0.0.0` или к другому порту приведёт к отклонению запроса сервером аутентификации из‑за несоответствия `redirect_uri`. SSH‑туннель сохраняет URI loopback‑формы неизменным от начала до конца.
## Пошагово: один SSH‑переход

### 1. Запусти туннель с локального компьютера

```bash
# xAI Grok OAuth (port 56121)
ssh -N -L 56121:127.0.0.1:56121 user@remote-host

# Or for Spotify (port 43827)
ssh -N -L 43827:127.0.0.1:43827 user@remote-host
```

`-N` означает «не открывать удалённый shell, просто держать туннель открытым». Оставь этот терминал работающим на всё время сеанса.

### 2. В отдельной SSH‑сессии выполни команду авторизации

```bash
ssh user@remote-host
hermes auth add xai-oauth --no-browser
# or for Spotify:
# hermes auth add spotify --no-browser
```

Hermes обнаруживает SSH‑сессию, пропускает автоматическое открытие браузера и выводит URL для авторизации плюс строку `Waiting for callback on http://127.0.0.1:<port>/callback`.

### 3. Открой URL в локальном браузере

Скопируй URL для авторизации из удалённого терминала и вставь его в браузер на ноутбуке. Подтверди запрос на доступ. Сервер авторизации перенаправит на `http://127.0.0.1:<port>/callback`. Твой браузер попадёт в туннель, запрос будет переслан удалённому слушателю, и Hermes выведет `Login successful!`.

Можно закрыть туннель (Ctrl+C в первом терминале), как только увидишь строку об успехе.
## Пошагово: через jump‑box

Если ты подключаешься к Hermes через bastion / jump‑host, используй встроенный в SSH параметр `-J` (ProxyJump):

```bash
ssh -N -L 56121:127.0.0.1:56121 -J jump-user@jump-host user@final-host
```

Это создаёт цепочку SSH‑соединений через jump‑host, не открывая порт loopback на самом jump‑box. Локальный `127.0.0.1:56121` на твоём ноутбуке будет туннелировать напрямую к `127.0.0.1:56121` на конечном удалённом хосте.

Для более старых версий OpenSSH, которые не поддерживают `-J`, используй длинную форму:

```bash
ssh -N \
    -o "ProxyCommand=ssh -W %h:%p jump-user@jump-host" \
    -L 56121:127.0.0.1:56121 \
    user@final-host
```
## Mosh, tmux, ssh ControlMaster

Туннель — свойство базового SSH‑соединения. Если ты запускаешь Hermes внутри `tmux` поверх сессии mosh, роуминг mosh не передаёт перенаправление `-L`. Открой *отдельную* обычную SSH‑сессию **только** для туннеля `-L` — это соединение должно оставаться живым во время процесса аутентификации. Твоя интерактивная mosh/tmux‑сессия может продолжать работать с Hermes как обычно.

Если ты используешь `ssh -o ControlMaster=auto`, перенаправления портов в мультиплексированном соединении наследуют время жизни мастера. Перезапусти мастер, если туннель не поднимается:

```bash
ssh -O exit user@remote-host
ssh -N -L 56121:127.0.0.1:56121 user@remote-host
```
## Устранение неполадок

### `bind [127.0.0.1]:56121: Address already in use`

Что‑то на твоём ноутбуке уже использует этот порт. Либо предыдущий туннель не завершился корректно, либо локальный Hermes тоже слушает его. Найди и убей процесс‑нарушитель:

```bash
# macOS / Linux
lsof -iTCP:56121 -sTCP:LISTEN
kill <PID>
```

Затем повтори команду `ssh -L`.

### "Could not establish connection. We couldn't reach your app." (xAI)

Страница авторизации xAI показывает это, когда её перенаправление на `127.0.0.1:<port>/callback` не доходит до слушателя. Либо туннель не запущен, порт указан неверно, либо ты используешь порт, выведенный Hermes в предыдущем запуске (порт может быть автоматически изменён, если предпочтительный занят — всегда читай последнюю строку `Waiting for callback on ...`).

### `xAI authorization timed out waiting for the local callback`

Та же причина, что и выше — перенаправление никогда не вернулось. Проверь, что туннель всё ещё работает (`ssh -N` не выводит ничего, поэтому смотри терминал, из которого ты его запустил), при необходимости перезапусти его и снова выполни `hermes auth add xai-oauth --no-browser`.

### Токены попадают в неправильный каталог `~/.hermes`

Токены записываются под Linux‑пользователем, от имени которого был выполнен `hermes auth add ...`. Если твой gateway / сервис systemd работает от другого пользователя (например, `root` или отдельного пользователя `hermes`), аутентифицируйся **от этого** пользователя, чтобы токены оказались в его `~/.hermes/auth.json`. `sudo -u hermes -i` или аналогичная команда.
## См. также

- [xAI Grok OAuth](./xai-grok-oauth.md)
- [Spotify (`Running over SSH`)](../user-guide/features/spotify.md#running-over-ssh--in-a-headless-environment)
- [Native MCP client (OAuth section)](../user-guide/features/mcp.md#oauth-authenticated-http-servers)
- [SSH `-J` / ProxyJump (man page)](https://man.openbsd.org/ssh#J)