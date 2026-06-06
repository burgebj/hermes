---
title: "Зарегистрировать приложение Microsoft Graph"
description: "Пошаговое руководство по Azure portal для создания регистрации приложения, которая управляет конвейером встреч Teams"
---

# Зарегистрировать приложение Microsoft Graph

Конвейер встреч Teams читает стенограммы, записи и связанные артефакты из Microsoft Graph, используя **app‑only** (демон)‑аутентификацию — без входа пользователя и без интерактивного согласия для каждой встречи. Для этого требуется регистрация приложения Azure AD с разрешениями, согласованными администратором.

В этом руководстве рассматриваются:

1. Создание регистрации приложения
2. Создание клиентского секрета
3. Предоставление разрешений Graph API, необходимых конвейеру
4. Административное согласие этим разрешениям
5. (Опционально) Ограничение приложения конкретными пользователями с помощью политики доступа к приложению

Тебе нужны **права администратора арендатора** (или администратор, который даст согласие от твоего имени), чтобы завершить процесс. Сохрани собранные значения — они понадобятся в `~/.hermes/.env` в конце.

## Предварительные требования

- Арендатор Microsoft 365 с Teams Premium или лицензиями Teams, которые генерируют стенограммы и записи встреч
- Доступ администратора к порталу Azure по адресу [entra.microsoft.com](https://entra.microsoft.com)
- Публично доступный HTTPS‑endpoint для уведомлений об изменениях Graph (будет настроен позже, на этапе слушателя веб‑хуков)

## Шаг 1: Создать регистрацию приложения

1. Войди в [entra.microsoft.com](https://entra.microsoft.com) как администратор арендатора.
2. Перейди в **Identity → Applications → App registrations**.
3. Нажми **New registration**.
4. Заполни:
   - **Name:** `Hermes Teams Meeting Pipeline` (или любое имя, которое ты сможешь распознать).
   - **Supported account types:** *Accounts in this organizational directory only (Single tenant)*.
   - **Redirect URI:** оставь пустым — для app‑only‑auth URI не нужен.
5. Нажми **Register**.

Ты окажешься на странице обзора приложения. Скопируй два значения:

- **Application (client) ID** → `MSGRAPH_CLIENT_ID`
- **Directory (tenant) ID** → `MSGRAPH_TENANT_ID`

## Шаг 2: Создать клиентский секрет

1. В левом меню открой **Certificates & secrets**.
2. Нажми **New client secret**.
3. **Description:** `hermes-graph-secret`. **Expires:** выбери срок, соответствующий твоей политике ротации (обычно 6–24 мес.).
4. Нажми **Add**.
5. Сразу скопируй столбец **Value** — он отображается только один раз. Это значение `MSGRAPH_CLIENT_SECRET`.

> Столбец **Secret ID** — это не секрет. Тебе нужен столбец **Value**.

## Шаг 3: Предоставить разрешения Graph API

Конвейер использует минимальный набор разрешений приложения. Добавляй только то, что действительно нужно; каждое разрешение расширяет область чтения по всему арендатору.

1. В левом меню открой **API permissions**.
2. Нажми **Add a permission → Microsoft Graph → Application permissions**.
3. Добавь разрешения из таблицы ниже, соответствующие требуемым действиям конвейера.
4. После добавления нажми **Grant admin consent for `<your tenant>`**. Столбец **Status** должен стать зелёной галочкой для каждого разрешения.

### Требуется для резюмирования на основе стенограммы

| Permission | Что позволяет приложению |
|------------|--------------------------|
| `OnlineMeetings.Read.All` | Читать метаданные онлайн‑встреч Teams (тема, участники, URL присоединения). |
| `OnlineMeetingTranscript.Read.All` | Читать стенограммы встреч, генерируемые Teams. |

### Требуется для резервного варианта записи (когда стенограмма недоступна)

| Permission | Что позволяет приложению |
|------------|--------------------------|
| `OnlineMeetingRecording.Read.All` | Скачивать записи встреч Teams для офлайн‑обработки STT. |
| `CallRecords.Read.All` | Выявлять встречи из записей звонков, когда известен только URL присоединения. |

### Требуется для исходящей доставки резюме (только режим Graph)

Если `platforms.teams.extra.delivery_mode` установлен в `graph`, конвейер публикует резюме в канал или чат Teams через Graph API. Пропусти эти разрешения, если используешь режим доставки `incoming_webhook`.

| Permission | Что позволяет приложению |
|------------|--------------------------|
| `ChannelMessage.Send` | Отправлять сообщения в каналы Teams от имени приложения. |
| `Chat.ReadWrite.All` | Отправлять сообщения в личные и групповые чаты (только если `chat_id` указан как цель доставки). |

### Не рекомендуется

- `OnlineMeetings.ReadWrite.All` / `Chat.ReadWrite` без `.All` — слишком широкие права.
- Делегированные разрешения — конвейер использует только поток **app‑only** (client‑credentials); делегированные разрешения не работают без входа пользователя.

## Шаг 4: (Рекомендуется) Ограничить приложение политикой доступа к приложению

По умолчанию разрешения приложения, такие как `OnlineMeetings.Read.All`, дают приложению доступ **к каждой** встрече в арендаторе. Для демонстраций партнёров и тестовых арендаторов это приемлемо; для продакшна почти всегда требуется ограничить, чьи встречи приложение может читать.

Microsoft предоставляет **Application Access Policies** именно для Teams. Политика управляется только через PowerShell; в портале UI её нет.

Из администраторского PowerShell с установленным модулем `MicrosoftTeams` и подключённым (`Connect-MicrosoftTeams`):

```powershell
# Create a policy scoped to the Hermes app
New-CsApplicationAccessPolicy `
  -Identity "Hermes-Meeting-Pipeline-Policy" `
  -AppIds "<MSGRAPH_CLIENT_ID>" `
  -Description "Restrict Hermes meeting pipeline to allow-listed users"

# Grant the policy to specific users whose meetings the pipeline may read
Grant-CsApplicationAccessPolicy `
  -PolicyName "Hermes-Meeting-Pipeline-Policy" `
  -Identity "alice@example.com"

Grant-CsApplicationAccessPolicy `
  -PolicyName "Hermes-Meeting-Pipeline-Policy" `
  -Identity "bob@example.com"
```

Распространение может занять до 30 минут после предоставления согласия. Проверить можно командой:

```powershell
Test-CsApplicationAccessPolicy -Identity "alice@example.com" -AppId "<MSGRAPH_CLIENT_ID>"
```

Без политики **любые** встречи пользователей доступны для чтения — именно таково действие разрешения. Не пропускай этот шаг в продакшн‑арендаторе.

## Шаг 5: Записать учётные данные в файл `.env`

Помести три собранных значения в `~/.hermes/.env`:

```bash
MSGRAPH_TENANT_ID=<directory-tenant-id>
MSGRAPH_CLIENT_ID=<application-client-id>
MSGRAPH_CLIENT_SECRET=<client-secret-value>
```

Установи права доступа к файлу так, чтобы только ты мог читать секрет:

```bash
chmod 600 ~/.hermes/.env
```

## Шаг 6: Проверить поток токенов

Hermes поставляется с тестом‑пробойкой аутентификации Graph. Из установки Hermes запусти:

```python
python -c "
import asyncio
from tools.microsoft_graph_auth import MicrosoftGraphTokenProvider
provider = MicrosoftGraphTokenProvider.from_env()
token = asyncio.run(provider.get_access_token())
print('Token acquired, length:', len(token))
print(provider.inspect_token_health())
"
```

Успешный запуск выводит длинную строку токена и словарь состояния, где `cached: True` и `expires_in_seconds` около 3600. При ошибках появляется `MicrosoftGraphTokenError` с кодом Azure — самые частые:

| Ошибка Azure | Что означает | Как исправить |
|--------------|--------------|---------------|
| `AADSTS7000215: Invalid client secret` | Неправильное или просроченное значение секрета. | Сгенерировать новый секрет в шаге 2; обновить `.env`. |
| `AADSTS700016: Application not found` | Неправильный `MSGRAPH_CLIENT_ID` или неверный арендатор. | Перепроверить, что значения из шага 1 относятся к одному приложению. |
| `AADSTS90002: Tenant not found` | Ошибка в `MSGRAPH_TENANT_ID`. | Снова скопировать Directory (tenant) ID из обзора приложения. |
| `insufficient_claims` при вызове (не при получении токена) | Токен получен, но Graph возвращает 401/403. | Пропущен шаг 3 с администраторским согласием, либо добавлены разрешения без повторного согласия. Открой **API permissions** и снова нажми **Grant admin consent**. |

## Ротация клиентского секрета

Секреты Azure имеют жёсткий срок истечения. До истечения срока:

1. Создай второй клиентский секрет в шаге 2, не удаляя первый.
2. Обнови `MSGRAPH_CLIENT_SECRET` в `~/.hermes/.env` новым значением.
3. Перезапусти шлюз, чтобы он подхватил новый секрет: `hermes gateway restart`.
4. Проверь работу с помощью теста‑пробойки выше.
5. Удали старый секрет в портале Azure.

## Следующие шаги

После успешной проверки учётных данных продолжай:

- **Настройка слушателя веб‑хуков** — развернуть платформу шлюза `msgraph_webhook`, получающую уведомления об изменениях Graph.
- **Конфигурация конвейера** — настроить параметры выполнения конвейера встреч Teams и CLI оператора.
- **Исходящая доставка** — подключить отправку резюме обратно в канал или чат Teams.

Эти страницы появятся рядом с PR, добавляющими соответствующий runtime. Настройка учётных данных — отдельное требование, её можно выполнить заранее.