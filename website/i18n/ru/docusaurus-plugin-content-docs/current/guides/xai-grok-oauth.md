---
sidebar_position: 16
title: "xAI Grok OAuth (SuperGrok / X Premium+)"
description: "Войди с помощью своей подписки SuperGrok или X Premium+ чтобы использовать модели Grok в Hermes Agent — ключ API не требуется"
---

# xAI Grok OAuth (SuperGrok / X Premium+)

Hermes Agent поддерживает xAI Grok через браузерный поток OAuth‑входа на [accounts.x.ai](https://accounts.x.ai), используя либо **подписку SuperGrok** ([grok.com](https://x.ai/grok)), либо **подписку X Premium+** (привязанную учётную запись X). `XAI_API_KEY` не требуется — войди один раз, и Hermes автоматически обновит твою сессию в фоне.

Когда ты входишь в систему через учётную запись X с Premium+, xAI автоматически связывает статус подписки с твоей xAI‑сессией, поэтому поток OAuth работает так же, как и для прямых подписчиков SuperGrok.

Транспорт повторно использует адаптер `codex_responses` (xAI предоставляет endpoint в стиле Responses), поэтому рассуждения, вызов инструментов, потоковая передача и кэширование подсказок работают без каких‑либо изменений адаптера.

Тот же OAuth‑токен‑носитель также используется всеми прямыми к xAI‑поверхностям в Hermes — TTS, генерация изображений, генерация видео и транскрипция — так что один вход покрывает все четыре.
## Обзор

| Параметр | Значение |
|------|----------|
| Идентификатор провайдера | `xai-oauth` |
| Отображаемое имя | xAI Grok OAuth (SuperGrok / X Premium+) |
| Тип аутентификации | Browser OAuth 2.0 PKCE (loopback callback) |
| Транспорт | xAI Responses API (`codex_responses`) |
| Модель по умолчанию | `grok-4.3` |
| Конечная точка | `https://api.x.ai/v1` |
| Сервер аутентификации | `https://accounts.x.ai` |
| Требуется переменная окружения | Нет (`XAI_API_KEY` **не используется** для этого провайдера) |
| Подписка | [SuperGrok](https://x.ai/grok) или [X Premium+](https://x.com/i/premium_sign_up) — см. примечание ниже |
## Предварительные требования

- Python 3.9+
- Hermes Agent установлен
- Действующая подписка **SuperGrok** в твоём аккаунте xAI, **или** подписка **X Premium+** в аккаунте X, которым ты входишь (xAI автоматически связывает подписку)
- Браузер, доступный на локальном компьютере (или используй `--no-browser` для удалённых сессий)

:::warning xAI may restrict OAuth API access by tier
Бэкенд xAI применяет собственный белый список к поверхности OAuth API и, как было замечено, отклоняет обычных подписчиков SuperGrok с ошибкой `HTTP 403` (см. проблему [#26847](https://github.com/NousResearch/hermes-agent/issues/26847)), даже если подписка в приложении активна. Если вход OAuth проходит в браузере, но инференс возвращает 403, задай `XAI_API_KEY` и переключись на путь с API‑ключом (`provider: xai`) — эта поверхность сегодня не подвержена тем же ограничениям.
:::
## Быстрый старт

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

После первого входа в систему учётные данные сохраняются в файле `~/.hermes/auth.json` и автоматически обновляются до истечения срока их действия.
## Вход в систему вручную

Ты можешь инициировать вход без использования выбора модели:

```bash
hermes auth add xai-oauth
```

### Удалённые / безголовые сессии

На серверах, в контейнерах или в SSH‑сессиях, где нет браузера, Hermes определяет удалённую среду и выводит URL авторизации вместо открытия браузера.

**Важно:** loopback‑listener всё равно работает на удалённой машине по адресу `127.0.0.1:56121`. Перенаправление xAI должно достичь *этого* listener’а, поэтому открытие URL на твоём ноутбуке завершится ошибкой (`Could not establish connection. We couldn't reach your app.`), если не пробросить порт:

```bash
# In a separate terminal on your local machine:
ssh -N -L 56121:127.0.0.1:56121 user@remote-host

# Then in your SSH session on the remote machine:
hermes auth add xai-oauth --no-browser
# Open the printed authorize URL in your local browser.
```

Через jump‑box / bastion: добавь `-J jump-user@jump-host`.

См. [OAuth over SSH / Remote Hosts](./oauth-over-ssh.md) для полного пошагового руководства, включая цепочки ProxyJump, mosh/tmux и подводные камни ControlMaster.

### Удалённые среды только с браузером (Cloud Shell, Codespaces, EC2 Instance Connect)

Если у тебя нет обычного SSH‑клиента (например, ты запускаешь Hermes внутри GCP Cloud Shell, GitHub Codespaces, AWS EC2 Instance Connect, Gitpod или другой консоли в браузере), рецепт `ssh -L`, описанный выше, недоступен. Используй `--manual-paste` — Hermes пропускает loopback‑listener и позволяет вставить неудавшийся URL обратного вызова прямо из браузера:

```bash
hermes auth add xai-oauth --manual-paste
# Or via the model picker:
hermes model --manual-paste
```

См. [OAuth over SSH / Remote Hosts](./oauth-over-ssh.md#browser-only-remote-cloud-shell--codespaces--ec2-instance-connect) для полного пошагового руководства. Исправление регрессии для [#26923](https://github.com/NousResearch/hermes-agent/issues/26923).

Если страница согласия выводит код авторизации непосредственно на странице (текущее поведение xAI в браузерных консолях) вместо перенаправления на твой `127.0.0.1:56121/callback`, вставь **только сам код** в запросе `Callback URL:` — Hermes принимает как полный URL, так и отдельный фрагмент запроса `?code=...&state=...`, либо просто код.
## Как работает вход

1. Hermes открывает твой браузер на `accounts.x.ai`.
2. Ты входишь в систему (или подтверждаешь существующую сессию) и одобряешь запрос доступа.
3. xAI перенаправляет обратно в Hermes, и токены сохраняются в `~/.hermes/auth.json`.
4. С этого момента Hermes обновляет токены доступа в фоновом режиме — ты остаёшься вошедшим, пока не выполнит `hermes auth remove xai-oauth` или не отзовёшь доступ в настройках своей учётной записи xAI.
## Проверка статуса входа

```bash
hermes doctor
```

Раздел `◆ Auth Providers` покажет текущее состояние всех провайдеров, включая `xai-oauth`.
## Переключение моделей

```bash
hermes model
# → Select "xAI Grok OAuth (SuperGrok / X Premium+)"
# → Pick from the model list (grok-4.3 is pinned to the top)
```

Или установить модель напрямую:

```bash
hermes config set model.default grok-4.3
hermes config set model.provider xai-oauth
```
## Справочник конфигурации

После входа в систему `~/.hermes/config.yaml` будет содержать:

```yaml
model:
  default: grok-4.3
  provider: xai-oauth
  base_url: https://api.x.ai/v1
```

### Псевдонимы провайдеров

Все перечисленные ниже разрешаются в `xai-oauth`:

```bash
hermes --provider xai-oauth        # canonical
hermes --provider grok-oauth       # alias
hermes --provider x-ai-oauth       # alias
hermes --provider xai-grok-oauth   # alias
```
## Инструменты Direct-to-xAI (TTS / Image / Video / Transcription / X Search)

После входа через OAuth каждый инструмент Direct-to-xAI автоматически повторно использует один и тот же токен доступа — не требуется отдельная настройка, если только ты не хочешь использовать API‑ключ.

Чтобы выбрать бэкенд для каждого инструмента:

```bash
hermes tools
# → Text-to-Speech       → "xAI TTS"
# → Image Generation     → "xAI Grok Imagine (image)"
# → Video Generation     → "xAI Grok Imagine"
# → X (Twitter) Search   → "xAI Grok OAuth (SuperGrok / X Premium+)"
```

Если OAuth‑токены уже сохранены, выборщик подтверждает их наличие и пропускает запрос учётных данных. Если ни OAuth, ни `XAI_API_KEY` не заданы, выборщик предлагает меню из трёх вариантов: вход через OAuth, вставить API‑ключ или пропустить.

:::note Генерация видео отключена по умолчанию
Набор инструментов `video_gen` отключён по умолчанию. Включи его в `hermes tools` → `🎬 Video Generation` (нажми пробел), прежде чем агент сможет вызвать `video_generate`. Иначе агент может перейти к встроенному навыку ComfyUI, который также помечен для генерации видео.
:::

:::note X‑поиск автоматически включается при наличии учётных данных xAI
Набор инструментов `x_search` автоматически включается, когда настроены учётные данные xAI (OAuth‑токен SuperGrok / X Premium+ или `XAI_API_KEY`). Отключи его явно через `hermes tools` → `🐦 X (Twitter) Search` (нажми пробел), если не нужен этот функционал. Инструмент работает через встроенный API `x_search` Responses от xAI — он поддерживает **любой** из твоих входов: OAuth‑логин SuperGrok / X Premium+ или платный `XAI_API_KEY`, при этом отдаёт предпочтение OAuth, когда оба заданы (использует твою подписку вместо расходов на API). Схема инструмента скрыта от модели, если учётные данные xAI не настроены, независимо от того, включён набор инструментов или нет.
:::

### Модели

| Инструмент | Модель | Примечания |
|------|-------|-------|
| Chat | `grok-4.3` | По умолчанию; автоматически выбирается при входе через OAuth |
| Chat | `grok-4.20-0309-reasoning` | Вариант с рассуждениями |
| Chat | `grok-4.20-0309-non-reasoning` | Вариант без рассуждений |
| Chat | `grok-4.20-multi-agent-0309` | Вариант с несколькими агентами |
| Image | `grok-imagine-image` | По умолчанию; ~5–10 с |
| Image | `grok-imagine-image-quality` | Более высокое качество; ~10–20 с |
| Video | `grok-imagine-video` | Текст‑в‑видео и изображение‑в‑видео; до 7 референс‑изображений |
| TTS | (голос по умолчанию) | endpoint xAI `/v1/tts` |

Каталог чатов формируется в реальном времени из кэша `models.dev` на диске; новые релизы xAI появляются автоматически после обновления кэша. `grok-4.3` всегда закреплён вверху списка.
## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `XAI_BASE_URL` | Переопределить URL‑адрес по умолчанию `https://api.x.ai/v1` (редко требуется). |

Чтобы выбрать xAI в качестве активного провайдера, установи `model.provider: xai-oauth` в `config.yaml` (используй `hermes setup` для пошагового процесса) или передай `--provider xai-oauth` для однократного вызова.
## Устранение неполадок

### Токен истёк — автоматический повторный вход не происходит

Hermes обновляет токен перед каждой сессией и реактивно при получении 401. Если обновление завершается ошибкой `invalid_grant` (refresh‑токен был отозван или учётная запись была изменена), Hermes выводит типизированное сообщение о повторной аутентификации вместо падения.

Когда ошибка обновления является конечной (HTTP 4xx, `invalid_grant`, отозванный грант и т.п.), Hermes помечает refresh‑токен как недействительный и помещает его в карантин локально — последующие вызовы пропускают безнадёжную попытку обновления вместо бесконечного повторения 401. Агент выводит единственное сообщение «требуется повторная аутентификация» и не мешает работе, пока ты не войдёшь снова.

**Исправление:** запусти `hermes auth add xai-oauth` ещё раз, чтобы начать новый вход. Карантин будет снят при следующем успешном обмене.

### Истёк тайм‑аут авторизации

Слушатель loopback имеет ограниченный период действия (по умолчанию 180 с). Если ты не одобряешь вход вовремя, Hermes выдаёт ошибку тайм‑аута.

**Исправление:** повторно запусти `hermes auth add xai-oauth` (или `hermes model`). Процесс начнётся заново.

### Несоответствие состояния (возможный CSRF)

Hermes обнаружил, что значение `state`, возвращённое сервером авторизации, не совпадает с отправленным.

**Исправление:** повторно выполни вход. Если проблема сохраняется, проверь наличие прокси или перенаправления, изменяющего ответ OAuth.

### Вход с удалённого сервера

При работе через SSH или в контейнере Hermes выводит URL авторизации вместо открытия браузера. Слушатель обратного вызова всё равно привязывается к `127.0.0.1:56121` на удалённом хосте — браузер твоего ноутбука не может к нему подключиться без локального перенаправления SSH:

```bash
# Local machine, separate terminal:
ssh -N -L 56121:127.0.0.1:56121 user@remote-host

# Remote machine:
hermes auth add xai-oauth --no-browser
```

Полный гайд (jump‑boxes, mosh/tmux, конфликты портов): [OAuth over SSH / Remote Hosts](./oauth-over-ssh.md).

### HTTP 403 после успешного входа (уровень / права)

OAuth завершён в браузере, токены сохранены, но запросы инференса или обновления токена возвращают `HTTP 403` с сообщением вроде *«У вызывающего нет прав на выполнение указанной операции»*.

Это **не** проблема с устаревшим токеном — повторный запуск `hermes model` не поможет. Было замечено, что бекенд xAI ограничивает доступ к OAuth API определёнными уровнями SuperGrok, несмотря на активную подписку в приложении (issue [#26847](https://github.com/NousResearch/hermes-agent/issues/26847)).

**Исправление:** задай переменную `XAI_API_KEY` и переключись на путь с API‑ключом:

```bash
export XAI_API_KEY=xai-...
hermes config set model.provider xai
```

Либо обнови подписку на [x.ai/grok](https://x.ai/grok), если нужен именно OAuth‑путь.

### Ошибка «No xAI credentials found» во время выполнения

В хранилище аутентификации отсутствует запись `xai-oauth`, и переменная `XAI_API_KEY` не задана. Ты ещё не вошёл в систему, либо файл учётных данных был удалён.

**Исправление:** запусти `hermes model` и выбери провайдера xAI Grok OAuth, либо запусти `hermes auth add xai-oauth`.
## Выход из системы

Чтобы удалить все сохранённые учётные данные OAuth для xAI Grok:

```bash
hermes auth logout xai-oauth
```

Это очищает как единственную запись OAuth в `auth.json`, так и все строки пула учётных данных для `xai-oauth`. Используй `hermes auth remove xai-oauth <index|id|label>`, если нужно удалить только одну запись пула (выполни `hermes auth list xai-oauth`, чтобы увидеть их).
## См. также

- [OAuth через SSH / удалённые хосты](./oauth-over-ssh.md) — обязательное к прочтению, если Hermes находится на другой машине, чем твой браузер
- [Справочник провайдеров ИИ](../integrations/providers.md)
- [Переменные окружения](../reference/environment-variables.md)
- [Конфигурация](../user-guide/configuration.md)
- [Голос и TTS](../user-guide/features/tts.md)