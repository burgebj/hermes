---
sidebar_position: 9
---

# Додавання адаптера платформи

Цей посібник охоплює додавання нової платформи обміну повідомленнями до шлюзу Hermes. Адаптер платформи з’єднує Hermes із зовнішньою службою обміну повідомленнями (Telegram, Discord, WeCom тощо), щоб користувачі могли взаємодіяти з агентом через цю службу.

:::tip
Існує два способи додати платформу:
- **Plugin** (рекомендовано для спільноти/третьої сторони): Скопіюй каталог плагіна у `~/.hermes/plugins/` — без змін у коді ядра. Див. [Plugin Path](#plugin-path-recommended) нижче.
- **Built-in**: Змініть 20+ файлів у коді, конфігурації та документації. Використай [Built-in Checklist](#step-by-step-checklist-built-in-path) нижче.
:::
## Огляд архітектури

```
User ↔ Messaging Platform ↔ Platform Adapter ↔ Gateway Runner ↔ AIAgent
```

Кожен адаптер успадковується від `BasePlatformAdapter` у `gateway/platforms/base.py` і реалізує:

- **`connect()`** — Встановлення з’єднання (WebSocket, long‑poll, HTTP‑сервер тощо) *(abstract)*
- **`disconnect()`** — Чисте завершення роботи *(abstract)*
- **`send()`** — Надсилання текстового повідомлення в чат *(abstract)*
- **`send_typing()`** — Показ індикатора набору тексту (необов’язкове перевизначення)
- **`get_chat_info()`** — Повернення метаданих чату (необов’язкове перевизначення)

Вхідні повідомлення отримує адаптер і передає їх через `self.handle_message(event)`, який базовий клас маршрутизує до runner‑а шлюзу.
## Шлях плагіна (Рекомендовано)

Система плагінів дозволяє додати адаптер платформи без зміни будь‑якого коду ядра Hermes. Твій плагін — це каталог з двома файлами:

```
~/.hermes/plugins/my-platform/
  PLUGIN.yaml      # Plugin metadata
  adapter.py       # Adapter class + register() entry point
```

### PLUGIN.yaml

Метадані плагіна. Блоки `requires_env` і `optional_env` автоматично заповнюють записи інтерфейсу `hermes config` (див. [Surfacing Env Vars](#surfacing-env-vars-in-hermes-config) нижче).

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

### Конфігурація

Користувачі налаштовують платформу у `config.yaml`:

```yaml
gateway:
  platforms:
    my_platform:
      enabled: true
      extra:
        token: "..."
        channel: "#general"
```

Або через змінні середовища (які адаптер читає у `__init__`).

### Що система плагінів обробляє автоматично

Коли ти викликаєш `ctx.register_platform()`, наступні точки інтеграції обробляються за тебе — без потреби змінювати код ядра:

| Точка інтеграції | Як це працює |
|---|---|
| Створення шлюзу‑адаптера | Перевірка реєстру перед вбудованим ланцюжком `if/elif` |
| Парсинг конфігурації | `Platform._missing_()` приймає будь‑яку назву платформи |
| Перевірка підключеної платформи | Викликається `validate_config()` реєстру |
| Авторизація користувачів | Перевірка `allowed_users_env` / `allow_all_env` |
| Автоматичне ввімкнення лише за середовищем | `env_enablement_fn` заповнює `PlatformConfig.extra` + `home_channel` |
| Міст YAML‑конфігурації | `apply_yaml_config_fn` переводить ключі `config.yaml` у змінні середовища / extras |
| Доставка cron | `cron_deliver_env_var` робить можливим `deliver=<name>` |
| Записи UI `hermes config` | `requires_env` / `optional_env` у `plugin.yaml` автоматично заповнюються |
| Інструмент `send_message` | Маршрутизується через живий шлюз‑адаптер |
| Доставка webhook між платформами | Перевірка реєстру на відомі платформи |
| Доступ до команди `/update` | Прапорець `allow_update_command` |
| Каталог каналів | Платформи‑плагіни включені у перелік |
| Підказки системного запиту | `platform_hint` вставляється у контекст LLM |
| Розбиття повідомлень | `max_message_length` для розумного розділення |
| Видалення PII | Прапорець `pii_safe` |
| `hermes status` | Показує платформи‑плагіни з тегом `(plugin)` |
| `hermes gateway setup` | Платформи‑плагіни з’являються у меню налаштувань |
| `hermes tools` / `hermes skills` | Платформи‑плагіни у конфігурації кожної платформи |
| Блокування токену (мульти‑профіль) | Використовуй `acquire_scoped_lock()` у своєму `connect()` |
| Попередження про залишкову конфігурацію | Описовий лог, коли плагін відсутній |
## Автоконфігурація за допомогою змінних оточення

Більшість користувачів налаштовують платформу, додаючи змінні оточення у `~/.hermes/.env`, а не редагуючи `config.yaml`. Хук `env_enablement_fn` дозволяє твоєму плагіну підхопити ці змінні оточення **до** створення адаптера, тому `hermes gateway status`, `get_connected_platforms()` та доставка через cron бачать правильний стан без створення екземпляру SDK платформи.

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

Деякі користувачі віддають перевагу налаштуванню ключів `config.yaml` (`my_platform.require_mention`, `my_platform.allowed_channels` тощо) замість змінних середовища. Хук `apply_yaml_config_fn` дозволяє твоєму плагіну виконати цей переклад, не змушуючи ядро `gateway/config.py` знати схему YAML твоєї платформи.

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

Хук викликається під час `load_gateway_config()` після загального циклу обробки спільних ключів (наприклад `unauthorized_dm_behavior`, `notice_delivery`, `reply_prefix`, `require_mention` тощо) і перед `_apply_env_overrides()`, тому твій плагін лише потребує мосту **платформо‑специфічних** ключів.

Винятки, підняті хуком, поглинаються і записуються в журнал на рівні `debug` — погано працюючий плагін ніколи не перериває завантаження конфігурації шлюзу.
## Доставка за допомогою Cron

Щоб cron‑завдання `deliver=my_platform` маршрутизувалися до налаштованого домашнього каналу, встанови `cron_deliver_env_var` у назву змінної середовища, яка містить ідентифікатор типового чату/кімнати/каналу:

```python
ctx.register_platform(
    name="my_platform",
    ...
    cron_deliver_env_var="MY_PLATFORM_HOME_CHANNEL",
)
```

Планувальник читає цю змінну середовища під час визначення домашньої цілі для завдань `deliver=my_platform`, а також розглядає платформу як дійсний cron‑ціль у перевірках типу `_KNOWN_DELIVERY_PLATFORMS`. Якщо твоя `env_enablement_fn` створює словник `home_channel` (дивись вище), він має пріоритет — `cron_deliver_env_var` є запасним варіантом для cron‑завдань, які запускаються до ініціалізації середовища.

### Доставка cron поза процесом

`cron_deliver_env_var` робить твою платформу розпізнаним `deliver=`‑цільовим параметром. Щоб фактична відправка успішно виконувалась, коли cron‑завдання працює в окремому процесі від шлюзу (тобто `hermes cron run` окремо від `hermes gateway`), зареєструй `standalone_sender_fn`:

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

Навіщо потрібен цей хук: вбудовані платформи (Telegram, Discord, Slack тощо) постачають прямі REST‑утиліти у `tools/send_message_tool.py`, тому cron може доставляти без утримання шлюзу в тому ж процесі. Плагін‑платформи історично залежали від `_gateway_runner_ref()`, який повертає `None` поза процесом шлюзу, тому без `standalone_sender_fn` відправка з cron‑сторони завершується помилкою `No live adapter for platform '<name>'`.

Функція отримує ті ж `pconfig` і `chat_id`, що й живий адаптер, а також необов’язкові `thread_id`, `media_files` та `force_document` у вигляді ключових аргументів. Повернення `{"success": True, "message_id": ...}` розцінюється як успішна доставка; повернення `{"error": "..."}` виводить повідомлення в `delivery_errors` cron‑процесу. Виключення, підняті всередині функції, перехоплюються диспетчером і повідомляються як `Plugin standalone send failed: <reason>`. Приклади реалізацій знаходяться у `plugins/platforms/{irc,teams,google_chat}/adapter.py`.
## Відображення змінних середовища в `hermes config`

`hermes_cli/config.py` сканує `plugins/platforms/*/plugin.yaml` під час імпорту і автоматично заповнює `OPTIONAL_ENV_VARS` з блоків `requires_env` та (необов’язкових) `optional_env`. Використовуй форму **rich‑dict**, щоб надати правильні описи, підказки, прапорці паролів та URL‑и — інтерфейс налаштування CLI підхоплює їх автоматично.

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

**Підтримувані ключі словника:** `name` (обов’язковий), `description`, `prompt`, `url`, `password` (bool; автоматично визначається за суфіксами `*_TOKEN` / `*_SECRET` / `*_KEY` / `*_PASSWORD` / `*_JSON`, якщо не вказано), `category` (за замовчуванням `"messaging"`).

Записи у вигляді простих рядків (`- MY_PLATFORM_TOKEN`) також працюють — вони отримують загальний опис, автоматично сформований з `label` плагіна. Якщо ж жорстко заданий запис для тієї ж змінної вже існує в `OPTIONAL_ENV_VARS`, він має перевагу (зворотна сумісність); форма `plugin.yaml` діє як запасний (варіант).
## Специфічний для платформи повільний UX LLM

Деякі платформи мають обмеження, які змінюють спосіб представлення повільної відповіді LLM:

- **LINE** видає одноразовий *reply token*, термін дії якого закінчується приблизно через 60 секунд після вхідної події. Відповідати цим токеном безкоштовно; переходити на платний Push API — ні. Якщо LLM не завершився до дедлайну, вибір: «спалити платну квоту Push» або «зробити щось розумніше з reply token до його закінчення».
- **WhatsApp** позначає сесію як неактивну після 24 годин, після чого приймаються лише шаблонні повідомлення.
- **SMS** не має поняття індикаторів набору чи поступових оновлень — довгі відповіді виглядають так, ніби бот офлайн.

Це реальні обмеження, які базовий `BasePlatformAdapter` не може передбачити. Інтерфейс плагіна навмисно залишає простір для адаптера, щоб накласти специфічний для платформи UX поверх базового циклу набору, не розширюючи список `kwarg`.

### Патерн: успадкуй `_keep_typing`, щоб накласти UX під час польоту

`BasePlatformAdapter._keep_typing` — це heartbeat індикатора набору, який працює у фоні, доки LLM генерує, і скасовується, коли відповідь доставлена. Щоб накласти поведінку, специфічну для платформи, при певному порозі (наприклад, надіслати «ще думаю»‑бульбашку через 45 с), перевизнач `_keep_typing` у своєму адаптері, заплануй власне завдання поруч із `super()._keep_typing()`, і знищуй його у `finally`:

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

**Ключові моменти**

- **Завжди `await super()._keep_typing(...)`.** Heartbeat набору корисний сам по собі — не замінюй його, а накладай поверх.
- **Знищуй допоміжне завдання у `finally`.** Коли LLM завершується (або `/stop` скасовує запуск), шлюз скасовує завдання набору. Твоє допоміжне завдання має також помітити це скасування, інакше воно залишиться і може спрацювати після доставки відповіді.
- **Поєднуй з `interrupt_session_activity`**, щоб розв’язати будь‑який залишковий стан UX, коли користувач викликає `/stop`. Для LINE це означає перевести запис кешу postback з `PENDING` у `ERROR`, щоб постійна кнопка «Отримати відповідь» показала повідомлення «Run was interrupted» замість циклу.

### Патерн: успадкуй `send`, щоб маршрутизувати через кеш замість миттєвого надсилання

Якщо твій UX повільної відповіді кешує відповідь для подальшого отримання (flow postback у LINE), перевизначення `send` має розпізнавати три режими:

1. **Активний pending postback для цього чату** → кешуй відповідь під `request_id`, нічого не надсилай видимим.
2. **Системне busy‑ack** (`⚡ Interrupting`, `⏳ Queued`, `⏩ Steered`) → обійди кеш і надішли видимо, щоб користувач побачив відповідь шлюзу на свій ввід.
3. **Звичайна відповідь** → надсилай через reply‑token‑or‑push як зазвичай.

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

`_SYSTEM_BYPASS_PREFIXES` — це власні префікси busy‑acknowledgment шлюзу (`⚡`, `⏳`, `⏩`, `💾`). Завжди пропускай їх видимо, незалежно від стану кешованого UX.

### Коли цей патерн доречний

Використовуй перевизначення циклу набору, коли:

- У вихідного API платформи жорстке обмеження у вигляді вікна часу (одноразовий reply token, закінчення sticky‑session тощо) **І**
- *Видима bubble під час польоту* прийнятний UX на цій платформі.

Використовуй простіший шлях `slow_response_threshold = 0` (завжди Push), коли:

- Платформа не має суттєвого розмежування безкоштовного та платного, **АБО**
- Спільнота користувачів віддає перевагу «loading… loading… DONE» (тиша‑потім‑відповідь) замість інтерактивної проміжної bubble.

LINE підтримує обидва варіанти: поріг за замовчуванням 45 с для безкоштовного fetch postback, а `LINE_SLOW_RESPONSE_THRESHOLD=0` повертає до «завжди Push fallback».

### Реалізація‑зразок

Дивись `plugins/platforms/line/adapter.py` для повної реалізації postback у LINE — станова машина `RequestCache` (`PENDING → READY → DELIVERED`, плюс `ERROR` для `/stop`), перевизначення `_keep_typing`, яке надсилає bubble Template Buttons при порозі, перевизначення `send`, що маршрутизує через кеш, і перевизначення `interrupt_session_activity`, що розв’язує залишкові записи `PENDING`.

### Реалізації‑зразки (шляхи плагінів)

Дивись `plugins/platforms/irc/` у репозиторії для повного робочого прикладу — асинхронний IRC‑адаптер без зовнішніх залежностей. `plugins/platforms/teams/` охоплює Bot Framework / Adaptive Cards, `plugins/platforms/google_chat/` — OAuth‑базовані REST API, а `plugins/platforms/line/` — webhook‑орієнтовані Messaging API з платформо‑специфічним повільним UX LLM.
## Крок за кроком контрольний список (вбудований шлях)

:::note
Цей контрольний список призначений для додавання платформи безпосередньо до коду ядра Hermes — зазвичай це роблять core‑contributors для офіційно підтримуваних платформ. Платформи спільноти/третьої сторони мають використовувати [Шлях плагіна](#plugin-path-recommended) вище.
:::

### 1. Platform enum

Додай свою платформу до `Platform` enum у файлі `gateway/config.py`:

```python
class Platform(str, Enum):
    # ... existing platforms ...
    NEWPLAT = "newplat"
```

### 2. Файл адаптера

Створи `gateway/platforms/newplat.py`:

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

Для вхідних повідомлень створюй `MessageEvent` і викликай `self.handle_message(event)`:

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

### 3. Конфігурація шлюзу (`gateway/config.py`)

Три точки дотику:

1. **`get_connected_platforms()`** — додай перевірку необхідних облікових даних твоєї платформи
2. **`load_gateway_config()`** — додай запис у карту токенів середовища: `Platform.NEWPLAT: "NEWPLAT_TOKEN"`
3. **`_apply_env_overrides()`** — прив’яжи всі змінні середовища `NEWPLAT_*` до конфігурації

### 4. Запуск шлюзу (`gateway/run.py`)

Шість точок дотику:

1. **`_create_adapter()`** — додай гілку `elif platform == Platform.NEWPLAT:`
2. **`_is_user_authorized()` — карта `allowed_users`** — `Platform.NEWPLAT: "NEWPLAT_ALLOWED_USERS"`
3. **`_is_user_authorized()` — карта `allow_all`** — `Platform.NEWPLAT: "NEWPLAT_ALLOW_ALL_USERS"`
4. **Рання перевірка env `_any_allowlist` (кортеж)** — додай `"NEWPLAT_ALLOWED_USERS"`
5. **Рання перевірка env `_allow_all` (кортеж)** — додай `"NEWPLAT_ALLOW_ALL_USERS"`
6. **`_UPDATE_ALLOWED_PLATFORMS` (frozenset)** — додай `Platform.NEWPLAT`

### 5. Крос‑платформенна доставка

1. **`gateway/platforms/webhook.py`** — додай `"newplat"` до кортежу типу доставки
2. **`cron/scheduler.py`** — додай до `frozenset` `_KNOWN_DELIVERY_PLATFORMS` та до мапи платформ у `_deliver_result()`

### 6. Інтеграція CLI

1. **`hermes_cli/config.py`** — додай усі змінні `NEWPLAT_*` до `_EXTRA_ENV_KEYS`
2. **`hermes_cli/gateway.py`** — додай запис до списку `_PLATFORMS` з ключем, міткою, емодзі, `token_var`, `setup_instructions` та змінними
3. **`hermes_cli/platforms.py`** — додай `PlatformInfo` з міткою та `default_toolset` (використовується у TUI `skills_config` та `tools_config`)
4. **`hermes_cli/setup.py`** — додай функцію `_setup_newplat()` (може делегувати до `gateway.py`) та додай кортеж до списку платформ обміну повідомленнями
5. **`hermes_cli/status.py`** — додай запис виявлення платформи: `"NewPlat": ("NEWPLAT_TOKEN", "NEWPLAT_HOME_CHANNEL")`
6. **`hermes_cli/dump.py`** — додай `"newplat": "NEWPLAT_TOKEN"` до словника виявлення платформ

### 7. Інструменти

1. **`tools/send_message_tool.py`** — додай `"newplat": Platform.NEWPLAT` до мапи платформ
2. **`tools/cronjob_tools.py`** — додай `newplat` до рядка опису цільової доставки

### 8. Набори інструментів

1. **`toolsets.py`** — додай визначення набору інструментів `"hermes-newplat"` з `_HERMES_CORE_TOOLS`
2. **`toolsets.py`** — додай `"hermes-newplat"` до списку включень `"hermes-gateway"`

### 9. Необов’язково: підказки платформи

**`agent/prompt_builder.py`** — якщо у твоєї платформи є специфічні обмеження рендерингу (відсутність markdown, обмеження довжини повідомлення тощо), додай запис до словника `_PLATFORM_HINTS`. Це вставляє платформо‑специфічні рекомендації у системний підказник:

```python
_PLATFORM_HINTS = {
    # ...
    "newplat": (
        "You are chatting via NewPlat. It supports markdown formatting "
        "but has a 4000-character message limit."
    ),
}
```

Не всі платформи потребують підказок — додавай їх лише тоді, коли поведінка агента має відрізнятись.

### 10. Тести

Створи `tests/gateway/test_newplat.py`, що охоплює:

- Конструювання адаптера з конфігурації
- Побудову події повідомлення
- Метод відправки (мокнеш зовнішнє API)
- Платформо‑специфічні функції (шифрування, маршрутизація тощо)

### 11. Документація

| Файл | Що додати |
|------|------------|
| `website/docs/user-guide/messaging/newplat.md` | Повна сторінка налаштування платформи |
| `website/docs/user-guide/messaging/index.md` | Таблиця порівняння платформ, діаграма архітектури, таблиця наборів інструментів, розділ безпеки, посилання на наступні кроки |
| `website/docs/reference/environment-variables.md` | Усі змінні середовища `NEWPLAT_*` |
| `website/docs/reference/toolsets-reference.md` | Набір інструментів `hermes-newplat` |
| `website/docs/integrations/index.md` | Посилання на платформу |
| `website/sidebars.ts` | Запис у боковій панелі для сторінки документації |
| `website/docs/developer-guide/architecture.md` | Кількість адаптерів + перелік |
| `website/docs/developer-guide/gateway-internals.md` | Перелік файлів адаптерів |
## Аудит паритету

Перш ніж позначати новий PR платформи як завершений, запусти аудит паритету проти встановленої платформи:

```bash
# Find every .py file mentioning the reference platform
search_files "bluebubbles" output_mode="files_only" file_glob="*.py"

# Find every .py file mentioning the new platform
search_files "newplat" output_mode="files_only" file_glob="*.py"

# Any file in the first set but not the second is a potential gap
```

Повтори для файлів `.md` та `.ts`. Досліджуй кожну розбіжність — це перелік платформ (потрібно оновити) чи специфічне посилання на платформу (пропусти).
## Common Patterns

### Long‑Poll адаптери

Якщо твій адаптер використовує long‑polling (наприклад, Telegram або Weixin), використай задачу циклу опитування:

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

### Callback/Webhook адаптери

Якщо платформа надсилає повідомлення на твій кінцевий пункт (наприклад, WeCom Callback), запусти HTTP‑сервер:

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

Для платформ із жорсткими обмеженнями часу відповіді (наприклад, 5‑секундний ліміт WeCom), завжди підтверджуй отримання одразу і надсилай відповідь агента проактивно через API пізніше. Сесії агента тривають 3–30 хвилин — відповіді в межах callback‑вікна не є реальними.

### Блокування токенів

Якщо адаптер підтримує постійне з’єднання з унікальними обліковими даними, додай scoped lock, щоб запобігти використанню одного і того ж облікового запису двома профілями:

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
## Референтні реалізації

| Адаптер | Патерн | Складність | Корисний приклад для |
|---------|---------|------------|----------------------|
| `bluebubbles.py` | REST + webhook | Середня | Проста інтеграція REST API |
| `weixin.py` | Long-poll + CDN | Висока | Обробка медіа, шифрування |
| `wecom_callback.py` | Callback/webhook | Середня | HTTP‑сервер, AES‑крипто, мульти‑додаток |
| `telegram.py` | Long-poll + Bot API | Висока | Повнофункціональний адаптер з групами, потоками |