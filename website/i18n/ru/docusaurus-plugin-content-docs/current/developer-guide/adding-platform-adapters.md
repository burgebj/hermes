---
sidebar_position: 9
---

# Добавление адаптера платформы

Это руководство описывает добавление новой платформы обмена сообщениями в шлюз Hermes. Адаптер платформы подключает Hermes к внешнему сервису обмена сообщениями (Telegram, Discord, WeCom и т.д.), позволяя пользователям взаимодействовать с агентом через этот сервис.

:::tip
Существует два способа добавить платформу:
- **Plugin** (рекомендовано для сообщества/сторонних разработчиков): помести каталог плагина в `~/.hermes/plugins/` — изменения в ядре не требуются. См. [Plugin Path](#plugin-path-recommended) ниже.
- **Built-in**: измени более 20 файлов в коде, конфигурации и документации. См. [Built-in Checklist](#step-by-step-checklist-built-in-path) ниже.
:::
## Обзор архитектуры

```
User ↔ Messaging Platform ↔ Platform Adapter ↔ Gateway Runner ↔ AIAgent
```

Каждый адаптер наследует `BasePlatformAdapter` из `gateway/platforms/base.py` и реализует:

- **`connect()`** — Устанавливает соединение (WebSocket, long‑poll, HTTP‑сервер и т.д.) *(abstract)*
- **`disconnect()`** — Чистое завершение работы *(abstract)*
- **`send()`** — Отправляет текстовое сообщение в чат *(abstract)*
- **`send_typing()`** — Показывает индикатор набора текста (опциональное переопределение)
- **`get_chat_info()`** — Возвращает метаданные чата (опциональное переопределение)

Входящие сообщения получает адаптер и передаёт их через `self.handle_message(event)`, который базовый класс маршрутизирует к runner‑у шлюза.
## Путь к плагину (рекомендовано)

The plugin system lets you add a platform adapter without modifying any core Hermes code. Your plugin is a directory with two files:

```
~/.hermes/plugins/my-platform/
  PLUGIN.yaml      # Plugin metadata
  adapter.py       # Adapter class + register() entry point
```

### PLUGIN.yaml

Метаданные плагина. Блоки `requires_env` и `optional_env` автоматически заполняют элементы UI `hermes config` (см. [Отображение переменных окружения](#surfacing-env-vars-in-hermes-config) ниже).

```yaml
name: my-platform
label: My Platform
kind: platform
version: 1.0.0
description: My custom messaging platform adapter
author: Your Name
requires_env:
  - MY_PLATFORM_TOKEN          # bare string works
  - name: MY_PLATFORM_CHANNEL  # or rich dict for better UX
    description: "Channel to join"
    prompt: "Channel"
    password: false
optional_env:
  - name: MY_PLATFORM_HOME_CHANNEL
    description: "Default channel for cron delivery"
    password: false
```

### adapter.py

```python
import os
from gateway.platforms.base import (
    BasePlatformAdapter, SendResult, MessageEvent, MessageType,
)
from gateway.config import Platform, PlatformConfig


class MyPlatformAdapter(BasePlatformAdapter):
    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform("my_platform"))
        extra = config.extra or {}
        self.token = os.getenv("MY_PLATFORM_TOKEN") or extra.get("token", "")

    async def connect(self) -> bool:
        # Connect to the platform API, start listeners
        self._mark_connected()
        return True

    async def disconnect(self) -> None:
        self._mark_disconnected()

    async def send(self, chat_id, content, reply_to=None, metadata=None):
        # Send message via platform API
        return SendResult(success=True, message_id="...")

    async def get_chat_info(self, chat_id):
        return {"name": chat_id, "type": "dm"}


def check_requirements() -> bool:
    return bool(os.getenv("MY_PLATFORM_TOKEN"))


def validate_config(config) -> bool:
    extra = getattr(config, "extra", {}) or {}
    return bool(os.getenv("MY_PLATFORM_TOKEN") or extra.get("token"))


def _env_enablement() -> dict | None:
    token = os.getenv("MY_PLATFORM_TOKEN", "").strip()
    channel = os.getenv("MY_PLATFORM_CHANNEL", "").strip()
    if not (token and channel):
        return None
    seed = {"token": token, "channel": channel}
    home = os.getenv("MY_PLATFORM_HOME_CHANNEL")
    if home:
        seed["home_channel"] = {"chat_id": home, "name": "Home"}
    return seed


def register(ctx):
    """Plugin entry point — called by the Hermes plugin system."""
    ctx.register_platform(
        name="my_platform",
        label="My Platform",
        adapter_factory=lambda cfg: MyPlatformAdapter(cfg),
        check_fn=check_requirements,
        validate_config=validate_config,
        required_env=["MY_PLATFORM_TOKEN"],
        install_hint="pip install my-platform-sdk",
        # Env-driven auto-configuration — seeds PlatformConfig.extra from
        # env vars before adapter construction. See "Env-Driven Auto-
        # Configuration" section below.
        env_enablement_fn=_env_enablement,
        # Cron home-channel delivery support. Lets deliver=my_platform cron
        # jobs route without editing cron/scheduler.py. See "Cron Delivery"
        # section below.
        cron_deliver_env_var="MY_PLATFORM_HOME_CHANNEL",
        # Per-platform user authorization env vars
        allowed_users_env="MY_PLATFORM_ALLOWED_USERS",
        allow_all_env="MY_PLATFORM_ALLOW_ALL_USERS",
        # Message length limit for smart chunking (0 = no limit)
        max_message_length=4000,
        # LLM guidance injected into system prompt
        platform_hint=(
            "You are chatting via My Platform. "
            "It supports markdown formatting."
        ),
        # Display
        emoji="💬",
    )

    # Optional: register platform-specific tools
    ctx.register_tool(
        name="my_platform_search",
        toolset="my_platform",
        schema={...},
        handler=my_search_handler,
    )
```

### Конфигурация

Пользователи настраивают платформу в `config.yaml`:

```yaml
gateway:
  platforms:
    my_platform:
      enabled: true
      extra:
        token: "..."
        channel: "#general"
```

Или через переменные окружения (которые адаптер читает в `__init__`).

### Что система плагинов обрабатывает автоматически

When you call `ctx.register_platform()`, the following integration points are handled for you — no core code changes needed:

| Точка интеграции | Как работает |
|---|---|
| Создание адаптера шлюза | Registry проверяется до встроенной цепочки `if/elif` |
| Разбор конфигурации | `Platform._missing_()` принимает любое имя платформы |
| Проверка подключённой платформы | Вызывается `validate_config()` из реестра |
| Авторизация пользователя | Проверяются `allowed_users_env` / `allow_all_env` |
| Автоматическое включение только по окружению | `env_enablement_fn` заполняет `PlatformConfig.extra` + `home_channel` |
| Мост YAML‑конфигурации | `apply_yaml_config_fn` переводит ключи `config.yaml` в переменные окружения / extras |
| Доставка через cron | `cron_deliver_env_var` делает возможным `deliver=<name>` |
| Элементы UI `hermes config` | `requires_env` / `optional_env` в `plugin.yaml` автоматически заполняют поля |
| Инструмент `send_message` | Маршрутизируется через живой адаптер шлюза |
| Кроссплатформенная доставка Webhook | Реестр проверяется на известные платформы |
| Доступ к команде `/update` | Флаг `allow_update_command` |
| Каталог каналов | Платформы‑плагины включаются в перечисление |
| Подсказки системного приглашения | `platform_hint` внедряется в контекст LLM |
| Разбиение сообщений | `max_message_length` для умного разбиения |
| Редакция персональных данных (PII) | Флаг `pii_safe` |
| `hermes status` | Показывает платформы‑плагины с пометкой `(plugin)` |
| `hermes gateway setup` | Платформы‑плагины появляются в меню настройки |
| `hermes tools` / `hermes skills` | Платформы‑плагины в конфигурации каждой платформы |
| Блокировка токена (мультипрофиль) | Используй `acquire_scoped_lock()` в своём `connect()` |
| Предупреждение о потерянной конфигурации | Выводится описательное сообщение, когда плагин отсутствует |
## Автоконфигурация через переменные окружения

Большинство пользователей настраивают платформу, помещая переменные окружения в `~/.hermes/.env`, вместо редактирования `config.yaml`. Хук `env_enablement_fn` позволяет твоему плагину захватывать эти переменные **до** создания адаптера, так что `hermes gateway status`, `get_connected_platforms()` и cron‑доставка видят корректное состояние без инициализации SDK платформы.

```python
def _env_enablement() -> dict | None:
    """Seed PlatformConfig.extra from env vars.

    Called by the platform registry during load_gateway_config().
    Return None when the platform isn't minimally configured — the
    caller then skips auto-enabling. Return a dict to seed extras.

    The special 'home_channel' key is extracted and becomes a proper
    HomeChannel dataclass on the PlatformConfig; every other key is
    merged into PlatformConfig.extra.
    """
    token = os.getenv("MY_PLATFORM_TOKEN", "").strip()
    channel = os.getenv("MY_PLATFORM_CHANNEL", "").strip()
    if not (token and channel):
        return None
    seed = {"token": token, "channel": channel}
    home = os.getenv("MY_PLATFORM_HOME_CHANNEL")
    if home:
        seed["home_channel"] = {
            "chat_id": home,
            "name": os.getenv("MY_PLATFORM_HOME_CHANNEL_NAME", "Home"),
        }
    return seed


def register(ctx):
    ctx.register_platform(
        name="my_platform",
        label="My Platform",
        adapter_factory=lambda cfg: MyPlatformAdapter(cfg),
        check_fn=check_requirements,
        validate_config=validate_config,
        env_enablement_fn=_env_enablement,
        # ... other fields
    )
```
## YAML→env Config Bridge

Некоторые пользователи предпочитают задавать ключи `config.yaml` (`my_platform.require_mention`, `my_platform.allowed_channels` и т.д.) вместо переменных окружения. Хук `apply_yaml_config_fn` позволяет твоему плагину выполнять этот перевод, вместо того чтобы заставлять ядро `gateway/config.py` знать схему YAML твоей платформы.

```python
import os

def _apply_yaml_config(yaml_cfg: dict, platform_cfg: dict) -> dict | None:
    """Translate config.yaml `my_platform:` keys into env vars / extras.

    yaml_cfg     — the full top-level parsed config.yaml dict
    platform_cfg — the platform's own sub-dict (yaml_cfg.get("my_platform", {}))

    May mutate os.environ directly (use `not os.getenv(...)` guards to
    preserve env > YAML precedence) and/or return a dict to merge into
    PlatformConfig.extra. Return None or {} for no extras.
    """
    if "require_mention" in platform_cfg and not os.getenv("MY_PLATFORM_REQUIRE_MENTION"):
        os.environ["MY_PLATFORM_REQUIRE_MENTION"] = str(platform_cfg["require_mention"]).lower()
    allowed = platform_cfg.get("allowed_channels")
    if allowed is not None and not os.getenv("MY_PLATFORM_ALLOWED_CHANNELS"):
        if isinstance(allowed, list):
            allowed = ",".join(str(v) for v in allowed)
        os.environ["MY_PLATFORM_ALLOWED_CHANNELS"] = str(allowed)
    return None  # nothing extra to merge into PlatformConfig.extra

def register(ctx):
    ctx.register_platform(
        name="my_platform",
        ...,
        apply_yaml_config_fn=_apply_yaml_config,
    )
```

Хук вызывается в процессе `load_gateway_config()` после общего цикла обработки общих ключей (которые охватывают такие ключи, как `unauthorized_dm_behavior`, `notice_delivery`, `reply_prefix`, `require_mention` и т.п.) и перед `_apply_env_overrides()`, поэтому твоему плагину нужно лишь **мостить платформенно‑специфичные** ключи.

Исключения, выбрасываемые хуком, подавляются и записываются в журнал на уровне `debug` — неправильно работающий плагин никогда не прерывает загрузку конфигурации шлюза.
## Доставка по расписанию (Cron Delivery)

Чтобы задачи `deliver=my_platform` в cron направлялись в настроенный домашний канал, установи `cron_deliver_env_var` в имя переменной окружения, содержащей идентификатор чата/комнаты/канала по умолчанию:

```python
ctx.register_platform(
    name="my_platform",
    ...
    cron_deliver_env_var="MY_PLATFORM_HOME_CHANNEL",
)
```

Планировщик читает эту переменную окружения при определении домашней цели для задач `deliver=my_platform`, а также рассматривает платформу как допустимую цель cron в проверках в стиле `_KNOWN_DELIVERY_PLATFORMS`. Если твоя `env_enablement_fn` заполняет словарь `home_channel` (см. выше), он имеет приоритет — `cron_deliver_env_var` служит запасным вариантом для cron‑задач, которые запускаются до заполнения окружения.

### Доставка cron вне процесса

`cron_deliver_env_var` делает твою платформу распознаваемой целью `deliver=`. Чтобы фактическая отправка прошла успешно, когда cron‑задача запускается в отдельном процессе от шлюза (т.е. `hermes cron run` отдельно от `hermes gateway`), зарегистрируй `standalone_sender_fn`:

```python
async def _standalone_send(
    pconfig,
    chat_id,
    message,
    *,
    thread_id=None,
    media_files=None,
    force_document=False,
):
    """Open an ephemeral connection / acquire a fresh token, send, and close."""
    # ... open connection, send message, return result ...
    return {"success": True, "message_id": "..."}
    # or {"error": "..."}

ctx.register_platform(
    name="my_platform",
    ...
    cron_deliver_env_var="MY_PLATFORM_HOME_CHANNEL",
    standalone_sender_fn=_standalone_send,
)
```

Зачем нужен этот хук: встроенные платформы (Telegram, Discord, Slack и др.) поставляются с прямыми REST‑помощниками в `tools/send_message_tool.py`, поэтому cron может доставлять сообщения без удержания шлюза в том же процессе. Плагин‑платформы исторически зависели от `_gateway_runner_ref()`, который возвращает `None` вне процесса шлюза, поэтому без `standalone_sender_fn` отправка со стороны cron завершается ошибкой `No live adapter for platform '<name>'`.

Функция получает те же `pconfig` и `chat_id`, что и живой адаптер, плюс необязательные аргументы `thread_id`, `media_files` и `force_document`. Возврат `{"success": True, "message_id": ...}` считается успешной доставкой; возврат `{"error": "..."}` отображает сообщение в `delivery_errors` cron‑процесса. Исключения, возникшие внутри функции, перехватываются диспетчером и сообщаются как `Plugin standalone send failed: <reason>`. Реализации‑пример находятся в `plugins/platforms/{irc,teams,google_chat}/adapter.py`.
## Вывод переменных окружения в `hermes config`

`hermes_cli/config.py` сканирует `plugins/platforms/*/plugin.yaml` при импорте и автоматически заполняет `OPTIONAL_ENV_VARS` из блоков `requires_env` и (опционального) `optional_env`. Используй форму **rich‑dict**, чтобы добавить корректные описания, подсказки, флаги пароля и URL — интерфейс настройки CLI подхватывает их автоматически.

```yaml
# plugins/platforms/my_platform/plugin.yaml
name: my_platform-platform
label: My Platform
kind: platform
version: 1.0.0
description: >
  My Platform gateway adapter for Hermes Agent.
author: Your Name
requires_env:
  - name: MY_PLATFORM_TOKEN
    description: "Bot API token from the My Platform console"
    prompt: "My Platform bot token"
    url: "https://my-platform.example.com/bots"
    password: true
  - name: MY_PLATFORM_CHANNEL
    description: "Channel to join (e.g. #hermes)"
    prompt: "Channel"
    password: false
optional_env:
  - name: MY_PLATFORM_HOME_CHANNEL
    description: "Default channel for cron delivery (defaults to MY_PLATFORM_CHANNEL)"
    prompt: "Home channel (or empty)"
    password: false
  - name: MY_PLATFORM_ALLOWED_USERS
    description: "Comma-separated user IDs allowed to talk to the bot"
    prompt: "Allowed users (comma-separated)"
    password: false
```

**Поддерживаемые ключи словаря:** `name` (обязательно), `description`, `prompt`, `url`, `password` (bool; автоматически определяется из суффиксов `*_TOKEN` / `*_SECRET` / `*_KEY` / `*_PASSWORD` / `*_JSON`, если не указано), `category` (по умолчанию `"messaging"`).

Записи в виде простых строк (`- MY_PLATFORM_TOKEN`) также работают — для них генерируется общее описание, получаемое из `label` плагина. Если для той же переменной уже существует жёстко заданная запись в `OPTIONAL_ENV_VARS`, она имеет приоритет (обратная совместимость); форма `plugin.yaml` выступает как запасной вариант.
## Платформенно‑специфичный UX медленного LLM

Некоторые платформы имеют ограничения, которые меняют способ представления медленного ответа LLM:

- **LINE** выдаёт одноразовый *reply token*, который истекает примерно через 60 секунд после входящего события. Ответ с использованием этого токена бесплатен; переход к измеряемому Push API платный. Если LLM не успеет завершить работу к сроку, выбор стоит между «сжечь оплаченную квоту Push» и «сделать что‑то более хитрое с reply token до его истечения».
- **WhatsApp** помечает сессию как неактивную после 24 ч, после чего принимаются только шаблонные сообщения.
- **SMS** не имеет понятия индикаторов печати или прогрессивных обновлений — длинные ответы выглядят так, будто бот офлайн.

Это реальные ограничения, которые базовый `BasePlatformAdapter` не может предвидеть. Поверхностный API плагина намеренно оставляет место для адаптера, который может добавить платформенно‑специфичный UX поверх базового цикла печати без расширения списка kwarg.

### Шаблон: наследовать `_keep_typing`, чтобы добавить UX «на лету»

`BasePlatformAdapter._keep_typing` — это heartbeat индикатора печати; он работает как фоновая задача, пока LLM генерирует ответ, и отменяется, когда ответ доставлен. Чтобы добавить платформенно‑специфичное поведение при достижении порога (например, отправить пузырёк «ещё думаю» через 45 с), переопределите `_keep_typing` в своём адаптере, запланируйте свою задачу рядом с `super()._keep_typing()`, и завершите её в `finally`:

```python
class LineAdapter(BasePlatformAdapter):
    async def _keep_typing(self, chat_id: str, *args, **kwargs) -> None:
        if self.slow_response_threshold <= 0:
            await super()._keep_typing(chat_id, *args, **kwargs)
            return

        async def _fire_at_threshold() -> None:
            try:
                await asyncio.sleep(self.slow_response_threshold)
            except asyncio.CancelledError:
                raise
            # Platform-specific work here — for LINE, send a Template
            # Buttons "Get answer" bubble using the cached reply token
            # so the user can fetch the cached response later via a
            # fresh (free) reply token from the postback callback.
            await self._send_slow_response_button(chat_id)

        side_task = asyncio.create_task(_fire_at_threshold())
        try:
            await super()._keep_typing(chat_id, *args, **kwargs)
        finally:
            if not side_task.done():
                side_task.cancel()
                try:
                    await side_task
                except (asyncio.CancelledError, Exception):
                    pass
```

**Ключевые моменты**

- **Всегда `await super()._keep_typing(...)`.** Heartbeat печати полезен сам по себе — не заменяй его, а накладывай поверх.
- **Заверши вспомогательную задачу в `finally`.** Когда LLM заканчивает работу (или `/stop` отменяет запуск), шлюз отменяет задачу печати. Твоя вспомогательная задача должна тоже отреагировать на отмену, иначе она будет висеть и может сработать после того, как ответ уже доставлен.
- **Сочетай с `interrupt_session_activity`**, чтобы очистить любой «осиротевший» UX‑состояние, когда пользователь вызывает `/stop`. Для LINE это означает переход записи кэша postback из `PENDING` в `ERROR`, чтобы постоянная кнопка «Get answer» отдавала сообщение «Run was interrupted» вместо зацикливания.

### Шаблон: наследовать `send`, чтобы маршрутизировать через кэш вместо мгновенной отправки

Если твой UX медленного ответа кэширует ответ для последующего получения (поток postback в LINE), переопределённый `send` должен распознавать три режима:

1. **Активный отложенный postback для этого чата** → кэшировать ответ под `request_id`, ничего не отправлять визуально.
2. **Системное подтверждение занятости** (`⚡ Interrupting`, `⏳ Queued`, `⏩ Steered`) → обойти кэш и отправить визуально, чтобы пользователь увидел ответ шлюза на свой ввод.
3. **Обычный ответ** → отправлять обычным способом через reply‑token‑or‑push.

```python
async def send(self, chat_id: str, content: str, **kw) -> SendResult:
    if _is_system_bypass(content):
        return await self._send_text_chunks(chat_id, content, force_push=False)
    pending_rid = self._pending_buttons.get(chat_id)
    if pending_rid:
        self._cache.set_ready(pending_rid, content)
        return SendResult(success=True, message_id=pending_rid)
    return await self._send_text_chunks(chat_id, content, force_push=False)
```

`_SYSTEM_BYPASS_PREFIXES` — это собственные префиксы подтверждения занятости шлюза (`⚡`, `⏳`, `⏩`, `💾`). Всегда пропускай их визуально, независимо от состояния кэшированного UX.

### Когда уместен этот шаблон

Используй переопределение цикла печати, когда:

- У исходящего API платформы есть жёсткое ограничение по времени окна (одноразовый reply token, истекающая «липкая» сессия и т.п.) **И**
- *Видимый пузырёк «на лету»* приемлемый UX на этой платформе.

Используй более простой путь `slow_response_threshold = 0` → всегда Push, когда:

- Платформа не имеет значимого различия между бесплатным и платным, **ИЛИ**
- Сообщество пользователей предпочитает «загрузка… загрузка… ГОТОВО» — тишина‑затем‑ответ вместо интерактивного промежуточного пузырька.

LINE поддерживает оба варианта: порог по умолчанию — 45 с для бесплатного получения postback, а `LINE_SLOW_RESPONSE_THRESHOLD=0` переключает на «всегда Push fallback».

### Ссылка на реализацию

См. `plugins/platforms/line/adapter.py` для полной реализации postback в LINE — машина состояний `RequestCache` (`PENDING → READY → DELIVERED`, плюс `ERROR` для `/stop`), переопределение `_keep_typing`, которое отправляет пузырёк Template Buttons при достижении порога, переопределение `send`, которое маршрутизирует через кэш, и переопределение `interrupt_session_activity`, которое решает проблему осиротевших записей `PENDING`.

### Ссылки на реализации (путь плагина)

См. `plugins/platforms/irc/` в репозитории для полного рабочего примера — полный асинхронный IRC‑адаптер без внешних зависимостей. `plugins/platforms/teams/` покрывает Bot Framework / Adaptive Cards, `plugins/platforms/google_chat/` покрывает OAuth‑базированные REST‑API, а `plugins/platforms/line/` покрывает webhook‑ориентированные Messaging API с платформенно‑специфичным UX медленного LLM.
## Step-by-Step Checklist (Built-in Path)

:::note
Этот чеклист предназначен для добавления платформы напрямую в кодовую базу ядра Hermes — обычно это делают основные контрибьюторы для официально поддерживаемых платформ. Платформы сообщества/третьих сторон должны использовать [Plugin Path](#plugin-path-recommended), указанный выше.
:::

### 1. Platform Enum

Добавь свою платформу в перечисление `Platform` в файле `gateway/config.py`:

```python
class Platform(str, Enum):
    # ... existing platforms ...
    NEWPLAT = "newplat"
```

### 2. Adapter File

Создай `gateway/platforms/newplat.py`:

```python
from gateway.config import Platform, PlatformConfig
from gateway.platforms.base import (
    BasePlatformAdapter, MessageEvent, MessageType, SendResult,
)

def check_newplat_requirements() -> bool:
    """Return True if dependencies are available."""
    return SOME_SDK_AVAILABLE

class NewPlatAdapter(BasePlatformAdapter):
    def __init__(self, config: PlatformConfig):
        super().__init__(config, Platform.NEWPLAT)
        # Read config from config.extra dict
        extra = config.extra or {}
        self._api_key = extra.get("api_key") or os.getenv("NEWPLAT_API_KEY", "")

    async def connect(self) -> bool:
        # Set up connection, start polling/webhook
        self._mark_connected()
        return True

    async def disconnect(self) -> None:
        self._running = False
        self._mark_disconnected()

    async def send(self, chat_id, content, reply_to=None, metadata=None):
        # Send message via platform API
        return SendResult(success=True, message_id="...")

    async def get_chat_info(self, chat_id):
        return {"name": chat_id, "type": "dm"}
```

Для входящих сообщений создай `MessageEvent` и вызови `self.handle_message(event)`:

```python
source = self.build_source(
    chat_id=chat_id,
    chat_name=name,
    chat_type="dm",  # or "group"
    user_id=user_id,
    user_name=user_name,
)
event = MessageEvent(
    text=content,
    message_type=MessageType.TEXT,
    source=source,
    message_id=msg_id,
)
await self.handle_message(event)
```

### 3. Gateway Config (`gateway/config.py`)

Три точки касания:

1. **`get_connected_platforms()`** — добавь проверку требуемых учётных данных для своей платформы
2. **`load_gateway_config()`** — добавь запись в карту токенов окружения: `Platform.NEWPLAT: "NEWPLAT_TOKEN"`
3. **`_apply_env_overrides()`** — сопоставь все переменные окружения `NEWPLAT_*` с конфигурацией

### 4. Gateway Runner (`gateway/run.py`)

Шесть точек касания:

1. **`_create_adapter()`** — добавь ветку `elif platform == Platform.NEWPLAT:`
2. **`_is_user_authorized()` — карта `allowed_users`** — `Platform.NEWPLAT: "NEWPLAT_ALLOWED_USERS"`
3. **`_is_user_authorized()` — карта `allow_all`** — `Platform.NEWPLAT: "NEWPLAT_ALLOW_ALL_USERS"`
4. **Ранняя проверка окружения `_any_allowlist` (кортеж)** — добавь `"NEWPLAT_ALLOWED_USERS"`
5. **Ранняя проверка окружения `_allow_all` (кортеж)** — добавь `"NEWPLAT_ALLOW_ALL_USERS"`
6. **`_UPDATE_ALLOWED_PLATFORMS` — frozenset** — добавь `Platform.NEWPLAT`

### 5. Cross-Platform Delivery

1. **`gateway/platforms/webhook.py`** — добавь `"newplat"` в кортеж типов доставки
2. **`cron/scheduler.py`** — добавь в `frozenset` `_KNOWN_DELIVERY_PLATFORMS` и в карту платформ функции `_deliver_result()`

### 6. CLI Integration

1. **`hermes_cli/config.py`** — добавь все переменные `NEWPLAT_*` в `_EXTRA_ENV_KEYS`
2. **`hermes_cli/gateway.py`** — добавь запись в список `_PLATFORMS` с ключом, меткой, эмоджи, `token_var`, `setup_instructions` и переменными
3. **`hermes_cli/platforms.py`** — добавь запись `PlatformInfo` с меткой и `default_toolset` (используется в TUI `skills_config` и `tools_config`)
4. **`hermes_cli/setup.py`** — добавь функцию `_setup_newplat()` (можно делегировать в `gateway.py`) и добавь кортеж в список платформ обмена сообщениями
5. **`hermes_cli/status.py`** — добавь запись обнаружения платформы: `"NewPlat": ("NEWPLAT_TOKEN", "NEWPLAT_HOME_CHANNEL")`
6. **`hermes_cli/dump.py`** — добавь `"newplat": "NEWPLAT_TOKEN"` в словарь обнаружения платформ

### 7. Tools

1. **`tools/send_message_tool.py`** — добавь `"newplat": Platform.NEWPLAT` в карту платформ
2. **`tools/cronjob_tools.py`** — добавь `newplat` в строку описания цели доставки

### 8. Toolsets

1. **`toolsets.py`** — добавь определение набора инструментов `"hermes-newplat"` с `_HERMES_CORE_TOOLS`
2. **`toolsets.py`** — добавь `"hermes-newplat"` в список включений `"hermes-gateway"`

### 9. Optional: Platform Hints

**`agent/prompt_builder.py`** — если у твоей платформы есть специфические ограничения рендеринга (отсутствие markdown, ограничения длины сообщения и т.п.), добавь запись в словарь `_PLATFORM_HINTS`. Это внедрит подсказки, специфичные для платформы, в системный промпт:

```python
_PLATFORM_HINTS = {
    # ...
    "newplat": (
        "You are chatting via NewPlat. It supports markdown formatting "
        "but has a 4000-character message limit."
    ),
}
```

Не все платформы нуждаются в подсказках — добавляй их только если поведение агента должно отличаться.

### 10. Tests

Создай `tests/gateway/test_newplat.py`, покрывающий:

- Конструирование адаптера из конфигурации
- Формирование события сообщения
- Метод отправки (замокай внешний API)
- Платформо‑специфичные функции (шифрование, маршрутизация и т.д.)

### 11. Documentation

| File | Что добавить |
|------|--------------|
| `website/docs/user-guide/messaging/newplat.md` | Полная страница настройки платформы |
| `website/docs/user-guide/messaging/index.md` | Таблица сравнения платформ, диаграмма архитектуры, таблица наборов инструментов, раздел безопасности, ссылка на дальнейшие шаги |
| `website/docs/reference/environment-variables.md` | Все переменные окружения `NEWPLAT_*` |
| `website/docs/reference/toolsets-reference.md` | Набор инструментов `hermes-newplat` |
| `website/docs/integrations/index.md` | Ссылка на платформу |
| `website/sidebars.ts` | Запись в боковое меню для страницы документации |
| `website/docs/developer-guide/architecture.md` | Количество адаптеров + их список |
| `website/docs/developer-guide/gateway-internals.md` | Список файлов адаптеров |
## Аудит паритета

Прежде чем помечать новый PR платформы как завершённый, проведи аудит паритета относительно уже существующей платформы:

```bash
# Find every .py file mentioning the reference platform
search_files "bluebubbles" output_mode="files_only" file_glob="*.py"

# Find every .py file mentioning the new platform
search_files "newplat" output_mode="files_only" file_glob="*.py"

# Any file in the first set but not the second is a potential gap
```

Повтори проверку для файлов `.md` и `.ts`. Исследуй каждую разницу — это перечисление платформ (требует обновления) или ссылка, специфичная для платформы (пропускай).
## Общие шаблоны

### Адаптеры с длительным опросом (Long‑Poll)

Если твой адаптер использует long‑polling (например, Telegram или Weixin), используй задачу цикла опроса:

```python
async def connect(self):
    self._poll_task = asyncio.create_task(self._poll_loop())
    self._mark_connected()

async def _poll_loop(self):
    while self._running:
        messages = await self._fetch_updates()
        for msg in messages:
            await self.handle_message(self._build_event(msg))
```

### Адаптеры Callback/Webhook

Если платформа отправляет сообщения на твой эндпоинт (например, WeCom Callback), запусти HTTP‑сервер:

```python
async def connect(self):
    self._app = web.Application()
    self._app.router.add_post("/callback", self._handle_callback)
    # ... start aiohttp server
    self._mark_connected()

async def _handle_callback(self, request):
    event = self._build_event(await request.text())
    await self._message_queue.put(event)
    return web.Response(text="success")  # Acknowledge immediately
```

Для платформ с жёсткими ограничениями по времени ответа (например, 5‑секундный лимит у WeCom) всегда сразу отправляй подтверждение и позже проактивно доставляй ответ агента через API. Сессии агента работают 3–30 минут — ответы в рамках окна ответа callback невозможны.

### Блокировки токенов

Если адаптер удерживает постоянное соединение с уникальными учётными данными, добавь scoped‑lock, чтобы предотвратить использование одних и тех же учётных данных двумя профилями:

```python
from gateway.status import acquire_scoped_lock, release_scoped_lock

async def connect(self):
    if not acquire_scoped_lock("newplat", self._token):
        logger.error("Token already in use by another profile")
        return False
    # ... connect

async def disconnect(self):
    release_scoped_lock("newplat", self._token)
```
## Справочные реализации

| Адаптер | Паттерн | Сложность | Полезно как пример для |
|--------|---------|-----------|------------------------|
| `bluebubbles.py` | REST + webhook | Средняя | Простая интеграция REST API |
| `weixin.py` | Long-poll + CDN | Высокая | Обработка медиа, шифрование |
| `wecom_callback.py` | Callback/webhook | Средняя | HTTP‑сервер, AES‑крипто, мульти‑приложения |
| `telegram.py` | Long-poll + Bot API | Высокая | Полнофункциональный адаптер с группами, ветками |