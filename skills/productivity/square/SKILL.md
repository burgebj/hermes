---
name: square
description: Square API integration for inventory, catalog, customer, and order management. Uses OAuth2 with automatic token refresh.
version: 1.0.0
author: Nous Research
license: MIT
required_credential_files:
  - path: square_token.json
    description: Square OAuth2 token (created by setup script)
  - path: square_client_secret.json
    description: Square OAuth client credentials (downloaded from Square Developer Dashboard)
required_environment_variables:
  - name: SQUARE_APPLICATION_ID
    prompt: Square Application ID
    help: Found in your Square Developer Dashboard under Credentials
    required_for: full functionality
metadata:
  hermes:
    tags: [Square, Inventory, Catalog, Customers, Orders, Commerce, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [google-workspace]
---

# Square

Catalog, Inventory, Customers, and Orders management via the Square API. Use this skill to manage products, track stock levels, update customer profiles, and monitor sales.

## Architecture

```
setup.py  →  square_api.py  →  square SDK / REST API
(OAuth)       (argparse CLI)    (Catalog, Inventory, Customers, Orders)
```

## References

- `references/oauth-scopes.md` — Available OAuth scopes and permissions

## Scripts

- `scripts/setup.py` — OAuth2 setup (run once to authorize)
- `scripts/square_api.py` — API wrapper CLI

## First-Time Setup

The setup is fully non-interactive — you drive it step by step so it works
on CLI, Telegram, Discord, or any platform.

Define a shorthand first:

```bash
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SQUARE_SKILL_DIR="$HERMES_HOME/skills/productivity/square"
PYTHON_BIN="${HERMES_PYTHON:-python3}"
if [ -x "$HERMES_HOME/hermes-agent/venv/bin/python" ]; then
  PYTHON_BIN="$HERMES_HOME/hermes-agent/venv/bin/python"
fi
SSETUP="$PYTHON_BIN $SQUARE_SKILL_DIR/scripts/setup.py"
SAPI="$PYTHON_BIN $SQUARE_SKILL_DIR/scripts/square_api.py"
```

### Step 0: Check if already set up

```bash
$SSETUP --check
```

If it prints `AUTHENTICATED`, skip to Usage — setup is already done.

### Step 1: Create OAuth credentials (one-time, ~5 minutes)

Tell the user:

> You need a Square OAuth app. This is a one-time setup:
>
> 1. Go to https://developer.squareup.com/apps
> 2. Create or open an application
> 3. Under Credentials, copy your **Application ID** (also add it to your `~/.hermes/.env` as `SQUARE_APPLICATION_ID`)
> 4. Under Credentials → OAuth, set the **Redirect URL** to `http://localhost:1`
> 5. Click **Save**
> 6. Still in the OAuth section, click **View Secret** and copy the **Application Secret**
>
> Tell me the file path to your client secret JSON (or paste the Application ID and Application Secret directly).

The client secret JSON should look like:
```json
{
  "clientId": "sq0idp-...",
  "clientSecret": "sq0csp-..."
}
```

Or save as a simple JSON with the Application ID as `clientId` and Application Secret as `clientSecret`.

### Step 2: Store credentials

```bash
$SSETUP --client-secret /path/to/client_secret.json
```

### Step 3: Get authorization URL

```bash
$SSETUP --auth-url
```

Send the URL to the user. After authorizing, they paste back the redirect URL or code.

### Step 4: Exchange the code

```bash
$SSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED"
```

### Step 5: Verify

```bash
$SSETUP --check
```

Should print `AUTHENTICATED`. Token refreshes automatically from now on.

## Usage

All commands go through the API script:

```bash
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
SQUARE_SKILL_DIR="$HERMES_HOME/skills/productivity/square"
PYTHON_BIN="${HERMES_PYTHON:-python3}"
if [ -x "$HERMES_HOME/hermes-agent/venv/bin/python" ]; then
  PYTHON_BIN="$HERMES_HOME/hermes-agent/venv/bin/python"
fi
SAPI="$PYTHON_BIN $SQUARE_SKILL_DIR/scripts/square_api.py"
```

### Inventory

```bash
# Get current stock counts for catalog items
$SAPI inventory counts --location LOCATION_ID

# Adjust inventory (add/remove stock)
$SAPI inventory adjust --catalog-object-id OBJ_ID --location LOCATION_ID --quantity 10 --reason "received shipment"

# Get inventory changes history
$SAPI inventory changes --location LOCATION_ID
```

### Catalog

```bash
# List catalog items
$SAPI catalog list --types "item,variation"

# Search or list catalog
$SAPI catalog search --query "widget"

# Get a specific catalog object
$SAPI catalog get OBJECT_ID
```

### Customers

```bash
# List customers
$SAPI customers list --max 50

# Search customers
$SAPI customers search --query "John Smith"

# Create customer
$SAPI customers create --given-name "John" --family-name "Smith" --email "john@example.com"

# Update customer
$SAPI customers update CUSTOMER_ID --phone "+1555000000"

# Get customer
$SAPI customers get CUSTOMER_ID
```

### Orders

```bash
# List orders (defaults to last 7 days)
$SAPI orders list --location LOCATION_ID

# Get order
$SAPI orders get ORDER_ID
```

### Locations

```bash
# List all locations
$SAPI locations list
```

## Output Format

All commands return JSON. Key output shapes:

- **Inventory counts**: `{objects: [{catalog_object_id, location_id, quantity, calculated_at}]}`
- **Inventory adjust**: `{inventory_adjustment: {...}}`
- **Catalog list**: `{objects: [...]}` with type hints
- **Customers list/search**: `{customers: [...]}`
- **Orders list**: `{orders: [...]}`
- **Locations list**: `{locations: [...]}`

Parse output with `jq` or read JSON directly.

## Rules

1. **Never modify inventory, customer data, or orders without confirming with the user first.** Show the intended change and ask for approval.
2. **Check auth before first use** — run `setup.py --check`.
3. **Use location IDs** — most catalog/inventory/order calls require a location ID. Use `locations list` to find them first.
4. **Respect rate limits** — Square API has rate limits. Batch operations when possible.
5. **All monetary amounts are in smallest unit** — Square uses cents/smallest currency unit (e.g., $10.00 = 1000).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `NOT_AUTHENTICATED` | Run setup Steps 2-5 |
| `REFRESH_FAILED` | Token revoked — redo Steps 3-5 |
| `HttpError 403` | Missing scope — `$SSETUP --revoke` then redo Steps 3-5 |
| `HttpError 404` | Invalid ID — verify with list/search first |
| `HttpError 429` | Rate limited — wait and retry with backoff |

## Revoking Access

```bash
$SSETUP --revoke
```
