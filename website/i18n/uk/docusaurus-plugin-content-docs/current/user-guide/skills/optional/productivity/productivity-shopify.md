---
title: "Shopify — API GraphQL адміністратора та Storefront Shopify через curl"
sidebar_label: "Shopify"
description: "Shopify Admin та Storefront GraphQL API через curl"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Shopify

Shopify Admin & Storefront GraphQL API за допомогою `curl`. Продукти, замовлення, клієнти, інвентар, метаполя.
## Метадані навички

| | |
|---|---|
| Джерело | Необов’язково — встановити за допомогою `hermes skills install official/productivity/shopify` |
| Шлях | `optional-skills/productivity/shopify` |
| Версія | `1.0.0` |
| Автор | спільнота |
| Ліцензія | MIT |
| Платформи | linux, macos, windows |
| Теги | `Shopify`, `E-commerce`, `Commerce`, `API`, `GraphQL` |
| Пов’язані навички | [`airtable`](/docs/user-guide/skills/bundled/productivity/productivity-airtable), [`xurl`](/docs/user-guide/skills/bundled/social-media/social-media-xurl) |
:::info
Наступне — повне визначення **skill**, яке Hermes завантажує, коли цей **skill** активовано. Це те, що агент бачить як інструкції під час активної **сесії** **skill**.
:::

# Shopify — Admin & Storefront GraphQL APIs

Працюй з магазинами Shopify безпосередньо через `curl`: отримуй список продуктів, керуй інвентарем, витягай замовлення, оновлюй клієнтів, читай metafields. Без SDK, без фреймворку додатків — лише GraphQL‑endpoint і токен доступу custom‑app.

REST Admin API є застарілим з 2024‑04 і отримує лише виправлення безпеки. **Використовуй GraphQL Admin** для всіх адміністративних завдань. Використовуй **Storefront GraphQL** для запитів лише для читання, орієнтованих на клієнта (продукти, колекції, кошик).
## Prerequisites

1. У адмінці Shopify: **Settings → Apps and sales channels → Develop apps → Create an app**.
2. Натисни **Configure Admin API scopes**, вибери потрібні (приклади нижче) та збережи.
3. **Install app** → токен доступу до Admin API з’явиться ОДИН РАЗ. Скопіюй його одразу — Shopify більше ніколи не покаже його. Токени починаються з `shpat_`.
4. Збережи у `~/.hermes/.env`:
   ```
   SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxx
   SHOPIFY_STORE_DOMAIN=my-store.myshopify.com
   SHOPIFY_API_VERSION=2026-01
   ```

> **Heads up:** З 1 січня 2026 року нові «legacy custom apps», створені в адмінці Shopify, більше не доступні. Нові налаштування слід виконувати через **Dev Dashboard** (`shopify.dev/docs/apps/build/dev-dashboard`). Існуючі додатки, створені в адмінці, продовжують працювати. Якщо у магазину користувача немає існуючого кастомного додатку і дата після 2026‑01‑01, перенаправ його до Dev Dashboard замість адмін‑процесу.

Загальні області доступу за завданням:
- Продукти / колекції: `read_products`, `write_products`
- Інвентар: `read_inventory`, `write_inventory`, `read_locations`
- Замовлення: `read_orders`, `write_orders` (30 останніх без `read_all_orders`)
- Клієнти: `read_customers`, `write_customers`
- Чернетки замовлень: `read_draft_orders`, `write_draft_orders`
- Виконання: `read_fulfillments`, `write_fulfillments`
- Метаполя / метаоб’єкти: покриваються відповідними областями ресурсів
## Основи API

- **Endpoint:** `https://$SHOPIFY_STORE_DOMAIN/admin/api/$SHOPIFY_API_VERSION/graphql.json`
- **Auth header:** `X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN` (НЕ `Authorization: Bearer`)
- **Method:** завжди `POST`, завжди `Content-Type: application/json`, тіло – `{"query": "...", "variables": {...}}`
- **HTTP 200 не означає успіх.** GraphQL повертає помилки у верхньорівневому масиві `errors` та у полях `userErrors`. Завжди перевіряй обидва.
- **ID – це рядки GID:** `gid://shopify/Product/10079467700516`, `gid://shopify/Variant/...`, `gid://shopify/Order/...`. Передавай їх дослівно — не видаляй префікс.
- **Rate limit:** розраховується за вартістю запиту (leaky bucket). Кожна відповідь містить `extensions.cost` з `requestedQueryCost`, `actualQueryCost`, `throttleStatus.{currentlyAvailable, maximumAvailable, restoreRate}`. Зменшуй навантаження, коли `currentlyAvailable` падає нижче вартості наступного запиту. Стандартні магазини = 100‑очковий bucket, 50 / s відновлення; Plus = 1000/100.

Базовий шаблон curl (повторно використовуваний):

```bash
shop_gql() {
  local query="$1"
  local variables="${2:-{}}"
  curl -sS -X POST \
    "https://${SHOPIFY_STORE_DOMAIN}/admin/api/${SHOPIFY_API_VERSION:-2026-01}/graphql.json" \
    -H "Content-Type: application/json" \
    -H "X-Shopify-Access-Token: ${SHOPIFY_ACCESS_TOKEN}" \
    --data "$(jq -nc --arg q "$query" --argjson v "$variables" '{query: $q, variables: $v}')"
}
```

Пропусти через `jq` для зручного виводу. `-sS` залишає помилки видимими, але приховує індикатор прогресу.
## Виявлення

### Інформація про магазин + поточна версія API
```bash
shop_gql '{ shop { name myshopifyDomain primaryDomain { url } currencyCode plan { displayName } } }' | jq
```

### Перелік усіх підтримуваних версій API
```bash
shop_gql '{ publicApiVersions { handle supported } }' | jq '.data.publicApiVersions[] | select(.supported)'
```
## Продукти

### Пошук продуктів (перші 20, що відповідають запиту)
```bash
shop_gql '
query($q: String!) {
  products(first: 20, query: $q) {
    edges { node { id title handle status totalInventory variants(first: 5) { edges { node { id sku price inventoryQuantity } } } } }
    pageInfo { hasNextPage endCursor }
  }
}' '{"q":"hoodie status:active"}' | jq
```

Синтаксис запиту підтримує `title:`, `sku:`, `vendor:`, `product_type:`, `status:active`, `tag:`, `created_at:>2025-01-01`. Повна граматика: https://shopify.dev/docs/api/usage/search-syntax

### Пагінація продуктів (курсор)
```bash
shop_gql '
query($cursor: String) {
  products(first: 100, after: $cursor) {
    edges { cursor node { id handle } }
    pageInfo { hasNextPage endCursor }
  }
}' '{"cursor":null}'
# subsequent calls: pass the previous endCursor
```

### Отримати продукт з варіантами + метаполями
```bash
shop_gql '
query($id: ID!) {
  product(id: $id) {
    id title handle descriptionHtml tags status
    variants(first: 20) { edges { node { id sku price compareAtPrice inventoryQuantity selectedOptions { name value } } } }
    metafields(first: 20) { edges { node { namespace key type value } } }
  }
}' '{"id":"gid://shopify/Product/10079467700516"}' | jq
```

### Створити продукт з одним варіантом
```bash
shop_gql '
mutation($input: ProductCreateInput!) {
  productCreate(product: $input) {
    product { id handle }
    userErrors { field message }
  }
}' '{"input":{"title":"Test Hoodie","status":"DRAFT","vendor":"Hermes","productType":"Apparel","tags":["test"]}}'
```

Варіанти тепер мають власні мутації у останніх версіях:

```bash
# Add variants after creating the product
shop_gql '
mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkCreate(productId: $productId, variants: $variants) {
    productVariants { id sku price }
    userErrors { field message }
  }
}' '{"productId":"gid://shopify/Product/...","variants":[{"optionValues":[{"optionName":"Size","name":"M"}],"price":"49.00","inventoryItem":{"sku":"HD-M","tracked":true}}]}'
```

### Оновити ціну / SKU
```bash
shop_gql '
mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
    productVariants { id sku price }
    userErrors { field message }
  }
}' '{"productId":"gid://shopify/Product/...","variants":[{"id":"gid://shopify/ProductVariant/...","price":"55.00"}]}'
```
## Замовлення

### Список недавніх замовлень (за замовчуванням останні 30 без `read_all_orders`)
```bash
shop_gql '
{
  orders(first: 20, reverse: true, query: "financial_status:paid") {
    edges { node {
      id name createdAt displayFinancialStatus displayFulfillmentStatus
      totalPriceSet { shopMoney { amount currencyCode } }
      customer { id displayName email }
      lineItems(first: 10) { edges { node { title quantity sku } } }
    } }
  }
}' | jq
```

Корисні фільтри запитів замовлень: `financial_status:paid|pending|refunded`, `fulfillment_status:unfulfilled|fulfilled`, `created_at:>2025-01-01`, `tag:gift`, `email:foo@example.com`.

### Отримати окреме замовлення разом з адресою доставки
```bash
shop_gql '
query($id: ID!) {
  order(id: $id) {
    id name email
    shippingAddress { name address1 address2 city province country zip phone }
    lineItems(first: 50) { edges { node { title quantity variant { sku } originalUnitPriceSet { shopMoney { amount currencyCode } } } } }
    transactions { id kind status amountSet { shopMoney { amount currencyCode } } }
  }
}' '{"id":"gid://shopify/Order/...."}' | jq
```
## Клієнти

```bash
# Search
shop_gql '
{
  customers(first: 10, query: "email:*@example.com") {
    edges { node { id email displayName numberOfOrders amountSpent { amount currencyCode } } }
  }
}'

# Create
shop_gql '
mutation($input: CustomerInput!) {
  customerCreate(input: $input) {
    customer { id email }
    userErrors { field message }
  }
}' '{"input":{"email":"test@example.com","firstName":"Test","lastName":"User","tags":["api-created"]}}'
```
## Інвентар

Інвентар зберігається у **inventory items**, пов’язаних з варіантами, кількості відстежуються за **місцями**.

```bash
# Get inventory for a variant across all locations
shop_gql '
query($id: ID!) {
  productVariant(id: $id) {
    id sku
    inventoryItem {
      id tracked
      inventoryLevels(first: 10) {
        edges { node { location { id name } quantities(names: ["available","on_hand","committed"]) { name quantity } } }
      }
    }
  }
}' '{"id":"gid://shopify/ProductVariant/..."}'
```

Коригувати запас (дельта) — використовується `inventoryAdjustQuantities`:

```bash
shop_gql '
mutation($input: InventoryAdjustQuantitiesInput!) {
  inventoryAdjustQuantities(input: $input) {
    inventoryAdjustmentGroup { reason changes { name delta } }
    userErrors { field message }
  }
}' '{
  "input": {
    "reason": "correction",
    "name": "available",
    "changes": [{"delta": 5, "inventoryItemId": "gid://shopify/InventoryItem/...", "locationId": "gid://shopify/Location/..."}]
  }
}'
```

Встановити абсолютний запас (не дельта) — `inventorySetQuantities`:

```bash
shop_gql '
mutation($input: InventorySetQuantitiesInput!) {
  inventorySetQuantities(input: $input) {
    inventoryAdjustmentGroup { id }
    userErrors { field message }
  }
}' '{"input":{"reason":"correction","name":"available","ignoreCompareQuantity":true,"quantities":[{"inventoryItemId":"gid://shopify/InventoryItem/...","locationId":"gid://shopify/Location/...","quantity":100}]}}'
```
## Метаполя та Метапредмети

Метаполя додають користувацькі дані до ресурсів (products, customers, orders, shop).
## Storefront API (public read-only)

Різний кінцевий пункт, різний токен, використовується для клієнтських додатків/наборів типу hydrogen‑style headless. Заголовки відрізняються:

- **Endpoint:** `https://$SHOPIFY_STORE_DOMAIN/api/$SHOPIFY_API_VERSION/graphql.json`
- **Auth header (public):** `X-Shopify-Storefront-Access-Token: <public token>` — можна вбудовувати у браузер
- **Auth header (private):** `Shopify-Storefront-Private-Token: <private token>` — лише для сервера

```bash
curl -sS -X POST \
  "https://${SHOPIFY_STORE_DOMAIN}/api/${SHOPIFY_API_VERSION:-2026-01}/graphql.json" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Storefront-Access-Token: ${SHOPIFY_STOREFRONT_TOKEN}" \
  -d '{"query":"{ shop { name } products(first: 5) { edges { node { id title handle } } } }"}' | jq
```
## Масові операції

Для дампів, які перевищують обмеження швидкості (повний каталог продуктів, всі замовлення за рік):

```bash
# 1. Start bulk query
shop_gql '
mutation {
  bulkOperationRunQuery(query: """
    { products { edges { node { id title handle variants { edges { node { sku price } } } } } } }
  """) {
    bulkOperation { id status }
    userErrors { field message }
  }
}'

# 2. Poll status
shop_gql '{ currentBulkOperation { id status errorCode objectCount fileSize url partialDataUrl } }'

# 3. When status=COMPLETED, download the JSONL file
curl -sS "$URL" > products.jsonl
```

Кожен рядок у форматі JSONL — це вузол, а вкладені зв’язки виводяться як окремі рядки з `__parentId`. За потреби зберіть їх знову на боці клієнта.
## Вебхуки

Підписуйся на події, щоб не доводилося опитувати:

```bash
shop_gql '
mutation($topic: WebhookSubscriptionTopic!, $sub: WebhookSubscriptionInput!) {
  webhookSubscriptionCreate(topic: $topic, webhookSubscription: $sub) {
    webhookSubscription { id topic endpoint { __typename ... on WebhookHttpEndpoint { callbackUrl } } }
    userErrors { field message }
  }
}' '{"topic":"ORDERS_CREATE","sub":{"callbackUrl":"https://example.com/webhook","format":"JSON"}}'
```

Перевір вхідний HMAC вебхука, використовуючи клієнтський секрет застосунка (а не токен доступу):

```bash
echo -n "$REQUEST_BODY" | openssl dgst -sha256 -hmac "$APP_SECRET" -binary | base64
# Compare to X-Shopify-Hmac-Sha256 header
```
## Підводні камені

- **REST‑ендпоінти все ще існують, але заморожені.** Не створюй нових інтеграцій проти `/admin/api/.../products.json`. Використовуй GraphQL.
- **Перевірка формату токену.** Токени адміністратора починаються з `shpat_`. Публічні токени Storefront – з `shpua_`. Якщо у тебе є токен, але неправильний заголовок, кожен запит поверне 401 без корисного тіла помилки.
- **403 з дійсним токеном = відсутній scope.** Shopify повертає `{"errors":[{"message":"Access denied for ..."}]}`. Переналаштуй scopes Admin API у додатку, потім переустанови, щоб згенерувати новий токен.
- **`userErrors` порожній ≠ успіх.** Також перевіряй, що `data.<mutation>.<resource>` не `null`. Деякі помилки не заповнюють жодне поле — проаналізуй всю відповідь.
- **GID vs числовий ID.** Старий REST повертав числові ID; GraphQL вимагає повні рядки GID. Для конвертації: `gid://shopify/Product/<numeric>`.
- **Неочікуване обмеження швидкості.** Один запит `products(first: 250)` з глибоким вкладенням може коштувати 1000+ пунктів і одразу викликати throttle у магазині зі стандартним планом. Починай з вузького запиту, читай `extensions.cost`, коригуй.
- **Порядок пагінації.** `products(first: N, reverse: true)` сортує за `id DESC`, а не за `created_at`. Використовуй `sortKey: CREATED_AT, reverse: true` для «новіші першими».
- **`read_all_orders` для історичних даних.** Без цього scope `orders(...)` тихо обмежується 60‑денним вікном. Помилки не буде, просто менше результатів, ніж очікувалося. Для Shopify Plus‑мерчантів з великою кількістю замовлень запитай цей scope у налаштуваннях захищених даних додатку.
- **Валюти – це рядки.** Суми повертаються як `"49.00"`, а не `49.0`. Не використовуйте `jq tonumber` бездумно, якщо важливе збереження нульових знаків.
- **Поля Money у мультивалюті** мають `shopMoney` (валюта магазину) і `presentmentMoney` (валюта клієнта). Вибирай один варіант і використовуйте його послідовно.
## Безпека

Мутації в Shopify реальні — вони створюють продукти, створюють повернення, скасовують замовлення, виконують відправку. Перед запуском `productDelete`, `orderCancel`, `refundCreate` або будь‑якої масової мутації чітко вкажи, яку зміну ти вносиш, в якому магазині, і підтверди це з користувачем. Клонування продакшн‑даних у середовищі staging недоступне, якщо у користувача немає окремого dev‑магазину.