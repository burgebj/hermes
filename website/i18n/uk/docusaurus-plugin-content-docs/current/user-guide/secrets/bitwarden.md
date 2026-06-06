# Bitwarden Secrets Manager

Отримуй API‑ключі з [Bitwarden Secrets Manager](https://bitwarden.com/products/secrets-manager/) під час запуску процесу замість зберігання їх у відкритому вигляді у `~/.hermes/.env`. Один bootstrap‑секрет (токен доступу машинного облікового запису) замінює N ключів для кожного провайдера, а обертання облікових даних стає єдиною зміною у веб‑додатку Bitwarden.

## Як це працює

1. Ти створюєш **machine account** у Bitwarden Secrets Manager, надаєш йому доступ на читання до проєкту та генеруєш **access token**.
2. Hermes зберігає цей один токен у `~/.hermes/.env` як `BWS_ACCESS_TOKEN`.
3. Кожного разу, коли `hermes` (або шлюз, чи cron‑завдання) стартує, після завантаження `~/.hermes/.env`, Hermes викликає `bws secret list <project_id>` і встановлює отримані ключі у `os.environ`.
4. За замовчуванням Hermes **перевизначає** значення, які вже є у твоєму середовищі, тому Bitwarden є джерелом правди — оберни ключ один раз у веб‑додатку, і кожен процес Hermes підхопить його під час наступного запуску. Встанови `override_existing: false` у конфігурації, якщо хочеш, щоб переміг `.env`.

Бінарник `bws` автоматично завантажується у `~/.hermes/bin/` при першому використанні — без `apt`, без `brew`, без `sudo`.

## Чому машинні облікові записи (і чому без запиту 2FA)

Bitwarden Secrets Manager розроблений для не‑інтерактивних навантажень: машинні облікові записи не можуть бути захищені 2FA, бо в процесі немає людини. Токен доступу є обліковими даними. Будь‑хто, хто його має, може читати всі секрети, до яких має доступ машинний обліковий запис, тому став його як високовартісний bearer‑токен — зберігай у `.env` (не у `config.yaml`) і відклич + згенеруй новий у веб‑додатку Bitwarden, якщо він коли‑небудь витече.

Ти налаштовуєш машинний обліковий запис *у веб‑додатку*, де діє твоя звичайна 2FA. Після цього токен працює автономно.

## Налаштування

### 1. Створити машинний обліковий запис і токен доступу

У [Bitwarden web app](https://vault.bitwarden.com) (або [vault.bitwarden.eu](https://vault.bitwarden.eu) для EU‑акаунтів):

1. Перемкнись на **Secrets Manager** у перемикачі продуктів.
2. Створи або вибери **Project** (наприклад, “Hermes keys”).
3. Додай свої провайдер‑ключі як секрети. Ім’я секрету (**Name**) стає назвою змінної середовища — використовуй `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY` тощо.
4. **Machine accounts → New machine account → My Hermes machine → Projects** — надай Read‑доступ до свого проєкту.
5. **Access tokens** → **Create access token** → **Never** expires (або вкажи дату) → скопіюй токен (починається з `0.`). Bitwarden не зможе його знову отримати — збережи копію.

Secrets Manager включений у безкоштовний тариф Bitwarden з обмеженнями; платний план не потрібен.

### 2. Запустити майстер

```bash
hermes secrets bitwarden setup
```

Він:

1. Завантажить і перевірить `bws v2.0.0` у `~/.hermes/bin/bws`.
2. Запитає токен доступу (ввід прихований). Збереже у `~/.hermes/.env` як `BWS_ACCESS_TOKEN`.
3. Запитає, до якого Bitwarden‑регіону належить твій машинний обліковий запис — **US Cloud**, **EU Cloud** або **self-hosted / custom URL**. Збереже у `config.yaml` як `secrets.bitwarden.server_url` і передасть `bws` як `BWS_SERVER_URL`.
4. Показує проєкти, які бачить машинний обліковий запис; вибери один. Збереже у `config.yaml` як `secrets.bitwarden.project_id`.
5. Перевірить отримання секретів проєкту і покаже, які змінні середовища будуть заповнені.
6. Встановить `secrets.bitwarden.enabled: true`.

Неперервна (non‑interactive) установка також підтримується через прапорці:

```bash
hermes secrets bitwarden setup \
  --access-token "$BWS_ACCESS_TOKEN" \
  --server-url https://vault.bitwarden.eu \
  --project-id <project-uuid>
```

### 3. Підтвердження

```bash
hermes secrets bitwarden status
```

Відтепер кожен виклик `hermes` буде отримувати свіжі секрети під час старту. Перший раз, коли секрети застосовуються у процесі, у `stderr` з’явиться однорядковий підсумок.

## CLI

| Command | What it does |
|---|---|
| `hermes secrets bitwarden setup` | Interactive wizard (install binary, prompt for token, pick project, test fetch) |
| `hermes secrets bitwarden status` | Show config + binary version + token presence |
| `hermes secrets bitwarden sync` | Dry-run: pull secrets now and show what would be applied |
| `hermes secrets bitwarden sync --apply` | Pull and export into the current shell's environment |
| `hermes secrets bitwarden install` | Just download the pinned `bws` binary (no auth required) |
| `hermes secrets bitwarden disable` | Flip `enabled: false`; leaves token + project id in place |

## Конфігурація

Типові значення у `~/.hermes/config.yaml`:

```yaml
secrets:
  bitwarden:
    enabled: false
    access_token_env: BWS_ACCESS_TOKEN
    project_id: ""
    server_url: ""
    cache_ttl_seconds: 300
    override_existing: true
    auto_install: true
```

| Key | Default | What it does |
|---|---|---|
| `enabled` | `false` | Master switch. When false, Bitwarden is never contacted. |
| `access_token_env` | `BWS_ACCESS_TOKEN` | Env var name that holds the bootstrap token. Change this if you already use `BWS_ACCESS_TOKEN` for something else. |
| `project_id` | `""` | UUID of the project to sync from. |
| `server_url` | `""` | Bitwarden region or self-hosted endpoint. Empty = `bws` default (US Cloud, `https://vault.bitwarden.com`). Set to `https://vault.bitwarden.eu` for EU Cloud, or your own URL for self-hosted. Plumbed into the `bws` subprocess as `BWS_SERVER_URL`. |
| `cache_ttl_seconds` | `300` | How long an in-process fetch result is reused. Set to `0` to disable caching. Cache is per-process; new `hermes` invocations start fresh. |
| `override_existing` | `true` | When true, Bitwarden values overwrite anything already in env (so rotation in the web app actually takes effect). Flip to `false` if you want `.env` / shell exports to win locally. |
| `auto_install` | `true` | When true, `bws` is auto-downloaded into `~/.hermes/bin/` on first use. |

## Сценарії збоїв

Bitwarden ніколи не блокує запуск Hermes. Якщо щось пішло не так, ти побачиш однорядкове попередження у `stderr`, а Hermes продовжить роботу з тими обліковими даними, які вже були у `.env`:

| Symptom | Cause | Fix |
|---|---|---|
| `BWS_ACCESS_TOKEN is not set` | Enabled in config but token cleared from `.env` | Re-run `hermes secrets bitwarden setup` |
| `bws exited 1: invalid access token` | Token revoked or wrong | Generate a new token, re-run setup |
| `[400 Bad Request] {"error":"invalid_client"}` | Token is for a Bitwarden region other than the one `bws` is calling (e.g. EU token hitting the US identity endpoint) | Re-run setup and pick the right region, or set `secrets.bitwarden.server_url` to `https://vault.bitwarden.eu` (or your self-hosted URL) |
| `bws timed out` | Network blocked or Bitwarden API slow | Check connectivity to `api.bitwarden.com` (or your `server_url`) |
| `bws binary not available` | `auto_install: false` and `bws` not on PATH | Install manually from [github.com/bitwarden/sdk-sm/releases](https://github.com/bitwarden/sdk-sm/releases) or flip `auto_install` back on |
| `Checksum mismatch` | Download corrupted or tampered | Re-run, will retry; if it persists, file an issue |

## Зауваження щодо безпеки

- Bootstrap‑токен (`BWS_ACCESS_TOKEN`) сам по собі чутливий — будь‑хто, хто його має, може читати всі секрети, до яких має доступ машинний обліковий запис. Обробляй його так само, як будь‑який інший API‑ключ.
- Hermes не дозволить Bitwarden перезаписати сам bootstrap‑токен, навіть якщо `override_existing: true`. Якщо ти зберігаєш `BWS_ACCESS_TOKEN` як секрет у проєкті, він буде пропущений під час застосування.
- Завантаження бінарника `bws` перевіряється за SHA‑256 чек‑сумою, опублікованою в тому ж релізі на GitHub. Невідповідність перериває інсталяцію.
- Закріплена версія (`bws v2.0.0` на момент написання) оновлюється через PR у цьому репозиторії — Hermes не оновлює `bws` автоматично до «latest», бо upstream‑релізи можуть змінюватися.

## Коли НЕ варто використовувати

- **Одномашинні персональні налаштування**, де підходить просте зберігання у `~/.hermes/.env`. Ти просто міняєш один credential на інший і додаєш мережеву залежність при старті.
- **Air‑gapped середовища**, які не можуть дістатися `api.bitwarden.com`.
- **CI/CD**, де вже налаштований інший механізм інжекції секретів (GitHub Actions secrets, Vault тощо) — обери один шлях, а не два.

Добрий випадок для цього — флот багатьох машин, спільні dev‑бокси, шлюзові VPS або будь‑яке середовище, де потрібна централізована ротація та відкликання секретів у кількох інсталяціях Hermes.