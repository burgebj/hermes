---
sidebar_position: 15
title: "MiniMax OAuth"
description: "Войди в MiniMax через браузерный OAuth и используй модели MiniMax-M2.7 в Hermes Agent — ключ API не требуется"
---

# MiniMax OAuth

Hermes Agent поддерживает **MiniMax** через браузерный поток входа OAuth, используя те же учётные данные, что и [портал MiniMax](https://www.minimax.io). Ключ API или кредитная карта не требуются — войди один раз, и Hermes автоматически обновит твою сессию.

Транспорт повторно использует адаптер `anthropic_messages` (MiniMax предоставляет совместимую с Anthropic Messages конечную точку по адресу `/anthropic`), поэтому все существующие возможности вызова инструментов, потоковой передачи и контекста работают без изменений адаптера.

## Обзор

| Пункт | Значение |
|------|----------|
| Provider ID | `minimax-oauth` |
| Display name | MiniMax (OAuth) |
| Auth type | Browser OAuth (PKCE redirect flow) |
| Transport | Anthropic Messages-compatible (`anthropic_messages`) |
| Models | `MiniMax-M2.7`, `MiniMax-M2.7-highspeed` |
| Global endpoint | `https://api.minimax.io/anthropic` |
| China endpoint | `https://api.minimaxi.com/anthropic` |
| Requires env var | No (`MINIMAX_API_KEY` **не** используется для этого провайдера) |

## Предварительные требования

- Python 3.9+
- Установлен Hermes Agent
- Учётная запись MiniMax на [minimax.io](https://www.minimax.io) (глобальная) или [minimaxi.com](https://www.minimaxi.com) (Китай)
- Доступный браузер на локальном компьютере (или используй `--no-browser` для удалённых сессий)

## Быстрый старт

```bash
# Launch the provider and model picker
hermes model
# → Select "MiniMax (OAuth)" from the provider list
# → Hermes opens your browser to the MiniMax authorization page
# → Approve access in the browser
# → Select a model (MiniMax-M2.7 or MiniMax-M2.7-highspeed)
# → Start chatting

hermes
```

После первого входа учётные данные сохраняются в `~/.hermes/auth.json` и автоматически обновляются перед каждой сессией.

## Ручной вход

Можно инициировать вход без использования выбора модели:

```bash
hermes auth add minimax-oauth
```

### Регион Китай

Если твой аккаунт находится на китайской платформе (`minimaxi.com`), используй провайдер `minimax-cn`, основанный на ключе API — `minimax-cn` зарегистрирован только с `auth_type="api_key"` (без OAuth). Настрой `MINIMAX_CN_API_KEY` (и при желании `MINIMAX_CN_BASE_URL`) напрямую:

```bash
echo 'MINIMAX_CN_API_KEY=your-key' >> ~/.hermes/.env
```

### Удалённые / безголовые сессии

На серверах или в контейнерах, где нет браузера:

```bash
hermes auth add minimax-oauth --no-browser
```

Hermes выведет URL проверки и пользовательский код — открой URL на любом устройстве и введи код, когда будет предложено.

## Поток OAuth

Hermes реализует PKCE‑браузерный поток OAuth к конечным точкам MiniMax OAuth:

1. Hermes генерирует пару PKCE‑verifier / challenge и случайное значение `state`.
2. Выполняет POST к `{base_url}/oauth/code` с `challenge` и получает `user_code` и `verification_uri`.
3. Твой браузер открывает `verification_uri`. При необходимости введи `user_code`.
4. Hermes опрашивает `{base_url}/oauth/token`, пока не получит токен (или не истечёт срок).
5. Токены (`access_token`, `refresh_token`, срок действия) сохраняются в `~/.hermes/auth.json` под ключом `minimax-oauth`.

Обновление токена (стандартный грант `refresh_token` OAuth) запускается автоматически при каждом старте сессии, когда срок действия `access_token` меньше 60 секунд.

## Проверка статуса входа

```bash
hermes doctor
```

В разделе `◆ Auth Providers` будет отображено:

```
✓ MiniMax OAuth  (logged in, region=global)
```

или, если вход не выполнен:

```
⚠ MiniMax OAuth  (not logged in)
```

## Переключение моделей

```bash
hermes model
# → Select "MiniMax (OAuth)"
# → Pick from the model list
```

Или задать модель напрямую:

```bash
hermes config set model.default MiniMax-M2.7
hermes config set model.provider minimax-oauth
```

## Справочник конфигурации

После входа `~/.hermes/config.yaml` будет содержать записи, похожие на:

```yaml
model:
  default: MiniMax-M2.7
  provider: minimax-oauth
  base_url: https://api.minimax.io/anthropic
```

### Конечные точки регионов

| Provider id | Портал | Конечная точка инференса |
|-------------|--------|--------------------------|
| `minimax-oauth` (global) | `https://api.minimax.io` | `https://api.minimax.io/anthropic` |
| `minimax-cn` (China) | `https://api.minimaxi.com` | `https://api.minimaxi.com/anthropic` |

### Псевдонимы провайдера

Все нижеуказанные имена разрешаются в `minimax-oauth`:

```bash
hermes --provider minimax-oauth    # canonical
hermes --provider minimax-portal   # alias
hermes --provider minimax-global   # alias
hermes --provider minimax_oauth    # alias (underscore form)
```

## Переменные окружения

Провайдер `minimax-oauth` **не** использует `MINIMAX_API_KEY` или `MINIMAX_BASE_URL`. Эти переменные предназначены только для провайдеров `minimax` и `minimax-cn`, работающих по ключу API.

| Переменная | Описание |
|------------|----------|
| `MINIMAX_API_KEY` | Используется только провайдером `minimax` — игнорируется для `minimax-oauth` |
| `MINIMAX_CN_API_KEY` | Используется только провайдером `minimax-cn` — игнорируется для `minimax-oauth` |

Чтобы использовать `minimax-oauth` в качестве активного провайдера, задай `model.provider: minimax-oauth` в `config.yaml` (для пошагового процесса используй `hermes setup`), либо передай `--provider minimax-oauth` при одиночном вызове:

```bash
hermes --provider minimax-oauth
```

## Модели

| Модель | Наилучшее применение |
|--------|----------------------|
| `MiniMax-M2.7` | Длинный контекст, сложный вызов инструментов |
| `MiniMax-M2.7-highspeed` | Низкая задержка, лёгкие задачи, вспомогательные вызовы |

Обе модели поддерживают до 200 000 токенов контекста.

`MiniMax-M2.7-highspeed` также автоматически используется как вспомогательная модель для задач зрения и делегирования, когда `minimax-oauth` является основным провайдером.

## Устранение неполадок

### Токен истёк — автоматический повторный вход не сработал

Hermes обновляет токен при каждом старте сессии, если до истечения срока осталось менее 60 секунд. Если `access_token` уже истёк (например, после длительного офлайн‑периода), обновление происходит автоматически при следующем запросе. Если обновление завершается ошибкой `refresh_token_reused` или `invalid_grant`, Hermes помечает сессию как требующую повторного входа.

Когда ошибка обновления является окончательной (HTTP 4xx, `invalid_grant`, отозванный грант и т.п.), Hermes помечает `refresh_token` как недействительный и изолирует его локально, чтобы он больше не использовался. Агент выводит единственное сообщение «требуется повторная аутентификация» и не мешает работе, пока ты не войдёшь снова.

**Исправление:** выполните `hermes auth add minimax-oauth` заново, чтобы начать новый вход. Карантин снимается после следующего успешного обмена.

### Истечение времени ожидания авторизации

Поток device‑code имеет ограниченный срок действия. Если ты не одобришь вход вовремя, Hermes выдаст ошибку тайм‑аута.

**Исправление:** повторно запусти `hermes auth add minimax-oauth` (или `hermes model`). Поток начнётся заново.

### Несоответствие `state` (возможный CSRF)

Hermes обнаружил, что значение `state`, полученное от сервера авторизации, не совпадает с отправленным.

**Исправление:** повторно выполни вход. Если проблема сохраняется, проверь наличие прокси или перенаправления, изменяющего ответ OAuth.

### Вход с удалённого сервера

Если `hermes` не может открыть окно браузера, используй `--no-browser`:

```bash
hermes auth add minimax-oauth --no-browser
```

Hermes выводит URL и код. Открой URL на любом устройстве и завершите процесс там.

### Ошибка «Not logged into MiniMax OAuth» во время выполнения

В хранилище аутентификации нет учётных данных для `minimax-oauth`. Ты ещё не вошёл, либо файл учётных данных был удалён.

**Исправление:** выполни `hermes model` и выбери MiniMax (OAuth), либо запусти `hermes auth add minimax-oauth`.

## Выход из системы

Чтобы удалить сохранённые учётные данные MiniMax OAuth:

```bash
hermes auth remove minimax-oauth
```

## Смотрите также

- [AI Providers reference](../integrations/providers.md)
- [Environment Variables](../reference/environment-variables.md)
- [Configuration](../user-guide/configuration.md)
- [hermes doctor](../reference/cli-commands.md)