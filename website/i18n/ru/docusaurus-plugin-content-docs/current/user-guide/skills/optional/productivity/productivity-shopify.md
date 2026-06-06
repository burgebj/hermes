---
title: "Shopify — API GraphQL админки и витрины Shopify через curl"
sidebar_label: "Shopify"
description: "Shopify Admin и Storefront GraphQL API через curl"
---

\{/* This page is auto-generated from the skill's SKILL.md by website/scripts/generate-skill-docs.py. Edit the source SKILL.md, not this page. */\}

# Shopify

Shopify Admin и Storefront GraphQL API через curl. Товары, заказы, клиенты, запасы, метаполя.
## Метаданные навыка

| | |
|---|---|
| Источник | Необязательно — установить с помощью `hermes skills install official/productivity/shopify` |
| Путь | `optional-skills/productivity/shopify` |
| Версия | `1.0.0` |
| Автор | community |
| Лицензия | MIT |
| Платформы | linux, macos, windows |
| Теги | `Shopify`, `E-commerce`, `Commerce`, `API`, `GraphQL` |
| Связанные навыки | [`airtable`](/docs/user-guide/skills/bundled/productivity/productivity-airtable), [`xurl`](/docs/user-guide/skills/bundled/social-media/social-media-xurl) |
:::info
Следующее — полное определение навыка, которое Hermes загружает, когда этот навык активируется. Это то, что агент видит как инструкции, когда навык включён.
:::

# Shopify — Admin & Storefront GraphQL APIs

Работай с магазинами Shopify напрямую через `curl`: получай список товаров, управляй инвентарём, получай заказы, обновляй данные клиентов, читай metafields. Без SDK, без фреймворка приложений — только GraphQL‑endpoint и токен доступа custom‑app.

REST Admin API является устаревшим с 2024‑04 и получает только исправления безопасности. **Используй GraphQL Admin** для всей администраторской работы. Используй **Storefront GraphQL** для запросов только для чтения, ориентированных на клиента (товары, коллекции, корзина).
## Предварительные требования

1. В админке Shopify: **Settings → Apps and sales channels → Develop apps → Create an app**.
2. Нажми **Configure Admin API scopes**, выбери нужные (см. примеры ниже), сохрани.
3. **Install app** → токен доступа к Admin API появляется ОДИН РАЗ. Скопируй его сразу — Shopify больше никогда не покажет его. Токены начинаются с `shpat_`.
4. Сохрани в `~/.hermes/.env`:
   ```
   SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxx
   SHOPIFY_STORE_DOMAIN=my-store.myshopify.com
   SHOPIFY_API_VERSION=2026-01
   ```

> **Обрати внимание:** Начиная с 1 января 2026 г., новые «legacy custom apps», создаваемые в админке Shopify, больше недоступны. Новые настройки должны использовать **Dev Dashboard** (`shopify.dev/docs/apps/build/dev-dashboard`). Существующие приложения, созданные в админке, продолжают работать. Если у магазина пользователя нет существующего кастомного приложения и сейчас после 2026‑01‑01, направляй его к Dev Dashboard вместо административного процесса.

Типичные области доступа по задачам:
- Товары / коллекции: `read_products`, `write_products`
- Запасы: `read_inventory`, `write_inventory`, `read_locations`
- Заказы: `read_orders`, `write_orders` (30 самых последних без `read_all_orders`)
- Клиенты: `read_customers`, `write_customers`
- Черновики заказов: `read_draft_orders`, `write_draft_orders`
- Исполнения: `read_fulfillments`, `write_fulfillments`
- Метаполя / метаобъекты: покрываются соответствующими областями доступа ресурсов
## Основы API

- **Endpoint:** `https://$SHOPIFY_STORE_DOMAIN/admin/api/$SHOPIFY_API_VERSION/graphql.json`
- **Auth header:** `X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN` (НЕ `Authorization: Bearer`)
- **Method:** всегда `POST`, всегда `Content-Type: application/json`, тело — `{"query": "...", "variables": {...}}`
- **HTTP 200 не означает успех.** GraphQL возвращает ошибки в массиве верхнего уровня `errors` и в поле `userErrors`. Всегда проверяй оба.
- **ID — это строки GID:** `gid://shopify/Product/10079467700516`, `gid://shopify/Variant/...`, `gid://shopify/Order/...`. Передавай их дословно — не удаляй префикс.
- **Ограничение запросов:** рассчитывается по стоимости запроса (leaky bucket). Каждый ответ содержит `extensions.cost` с полями `requestedQueryCost`, `actualQueryCost`, `throttleStatus.{currentlyAvailable, maximumAvailable, restoreRate}`. Замедляй запросы, когда `currentlyAvailable` падает ниже стоимости следующего запроса. Стандартные магазины — ведро в 100 очков, восстановление — 50 / сек; Plus — 1000 / 100.

Базовый шаблон `curl` (можно переиспользовать):

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

Передавай вывод через `jq` для читаемого формата. `-sS` сохраняет ошибки видимыми, но скрывает индикатор прогресса.
## Обнаружение

### Информация о магазине и текущая версия API
```bash
shop_gql '{ shop { name myshopifyDomain primaryDomain { url } currencyCode plan { displayName } } }' | jq
```

### Список всех поддерживаемых версий API
```bash
shop_gql '{ publicApiVersions { handle supported } }' | jq '.data.publicApiVersions[] | select(.supported)'
```
## Продукты

### Поиск продуктов (первые 20, соответствующих запросу)
```bash
shop_gql '
query($q: String!) {
  products(first: 20, query: $q) {
    edges { node { id title handle status totalInventory variants(first: 5) { edges { node { id sku price inventoryQuantity } } } } }
    pageInfo { hasNextPage endCursor }
  }
}' '{"q":"hoodie status:active"}' | jq
```

Синтаксис запроса поддерживает `title:`, `sku:`, `vendor:`, `product_type:`, `status:active`, `tag:`, `created_at:>2025-01-01`. Полная грамматика: https://shopify.dev/docs/api/usage/search-syntax

### Пагинация продуктов (cursor)
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

### Получить продукт с вариантами + метаполя
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

### Создать продукт с одним вариантом
```bash
shop_gql '
mutation($input: ProductCreateInput!) {
  productCreate(product: $input) {
    product { id handle }
    userErrors { field message }
  }
}' '{"input":{"title":"Test Hoodie","status":"DRAFT","vendor":"Hermes","productType":"Apparel","tags":["test"]}}'
```

Варианты теперь имеют собственные мутации в последних версиях:

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

### Обновить цену / SKU
```bash
shop_gql '
mutation($productId: ID!, $variants: [ProductVariantsBulkInput!]!) {
  productVariantsBulkUpdate(productId: $productId, variants: $variants) {
    productVariants { id sku price }
    userErrors { field message }
  }
}' '{"productId":"gid://shopify/Product/...","variants":[{"id":"gid://shopify/ProductVariant/...","price":"55.00"}]}'
```
## Заказы

### Список недавних заказов (по умолчанию выводятся последние 30 без `read_all_orders`)
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

Полезные фильтры запросов заказов: `financial_status:paid|pending|refunded`, `fulfillment_status:unfulfilled|fulfilled`, `created_at:>2025-01-01`, `tag:gift`, `email:foo@example.com`.

### Получить отдельный заказ с адресом доставки
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
## Клиенты

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
## Инвентарь

Инвентарь хранится в **элементах инвентаря**, привязанных к вариантам; количества отслеживаются по **локациям**.

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

Регулировать запас (дельта) — использует `inventoryAdjustQuantities`:

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

Установить абсолютный запас (не дельта) — `inventorySetQuantities`:

```bash
shop_gql '
mutation($input: InventorySetQuantitiesInput!) {
  inventorySetQuantities(input: $input) {
    inventoryAdjustmentGroup { id }
    userErrors { field message }
  }
}' '{"input":{"reason":"correction","name":"available","ignoreCompareQuantity":true,"quantities":[{"inventoryItemId":"gid://shopify/InventoryItem/...","locationId":"gid://shopify/Location/...","quantity":100}]}}'
```
## Метаполя и Метаобъекты

Метаполя позволяют прикреплять пользовательские данные к ресурсам (products, customers, orders, shop).

```bash
# Read
shop_gql '
query($id: ID!) {
  product(id: $id) {
    metafields(first: 10, namespace: "custom") {
      edges { node { key type value } }
    }
  }
}' '{"id":"gid://shopify/Product/..."}'

# Write (works for any owner type)
shop_gql '
mutation($metafields: [MetafieldsSetInput!]!) {
  metafieldsSet(metafields: $metafields) {
    metafields { id key namespace }
    userErrors { field message code }
  }
}' '{"metafields":[{"ownerId":"gid://shopify/Product/...","namespace":"custom","key":"care_instructions","type":"multi_line_text_field","value":"Wash cold. Tumble dry low."}]}'
```
## Storefront API (public read-only)

Разный конечный URL, разный токен, используется для клиентских приложений и безголовых (headless) настроек в стиле hydrogen. Заголовки отличаются:

- **Endpoint:** `https://$SHOPIFY_STORE_DOMAIN/api/$SHOPIFY_API_VERSION/graphql.json`
- **Auth header (public):** `X-Shopify-Storefront-Access-Token: <public token>` — можно использовать в браузере
- **Auth header (private):** `Shopify-Storefront-Private-Token: <private token>` — только на сервере

```bash
curl -sS -X POST \
  "https://${SHOPIFY_STORE_DOMAIN}/api/${SHOPIFY_API_VERSION:-2026-01}/graphql.json" \
  -H "Content-Type: application/json" \
  -H "X-Shopify-Storefront-Access-Token: ${SHOPIFY_STOREFRONT_TOKEN}" \
  -d '{"query":"{ shop { name } products(first: 5) { edges { node { id title handle } } } }"}' | jq
```
## Пакетные операции

Для дампов, превышающих лимиты скорости (полный каталог продуктов, все заказы за год):

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

Каждая строка JSONL — это узел, а вложенные связи выводятся отдельными строками с полем `__parentId`. При необходимости собери их на клиенте.
## Вебхуки

Подписывайся на события, чтобы не опрашивать их вручную:

```bash
shop_gql '
mutation($topic: WebhookSubscriptionTopic!, $sub: WebhookSubscriptionInput!) {
  webhookSubscriptionCreate(topic: $topic, webhookSubscription: $sub) {
    webhookSubscription { id topic endpoint { __typename ... on WebhookHttpEndpoint { callbackUrl } } }
    userErrors { field message }
  }
}' '{"topic":"ORDERS_CREATE","sub":{"callbackUrl":"https://example.com/webhook","format":"JSON"}}'
```

Проверь входящий HMAC веб‑хука, используя клиентский секрет приложения (а не токен доступа):

```bash
echo -n "$REQUEST_BODY" | openssl dgst -sha256 -hmac "$APP_SECRET" -binary | base64
# Compare to X-Shopify-Hmac-Sha256 header
```
## Подводные камни

- **REST‑конечные точки всё ещё существуют, но заморожены.** Не пишите новые интеграции к `/admin/api/.../products.json`. Используйте GraphQL.
- **Проверка формата токена.** Токены администратора начинаются с `shpat_`. Публичные токены витрины — с `shpua_`. Если у тебя есть токен, но неверный заголовок, каждый запрос возвращает 401 без полезного тела ошибки.
- **403 с валидным токеном = отсутствует область доступа.** Shopify возвращает `{"errors":[{"message":"Access denied for ..."}]}`. Перенастрой области доступа Admin API в приложении, затем переустанови, чтобы сгенерировать новый токен.
- **`userErrors` пустой ≠ успех.** Также проверяй, что `data.<mutation>.<resource>` не `null`. Некоторые ошибки не заполняют ни то, ни другое — изучи весь ответ.
- **GID vs числовой ID.** Устаревший REST отдавал числовые ID; GraphQL требует полные строки GID. Для конвертации: `gid://shopify/Product/<numeric>`.
- **Неожиданные ограничения скорости.** Один запрос `products(first: 250)` с глубокой вложенностью может стоить 1000+ пунктов и сразу ограничить запросы в магазине со стандартным планом. Начинай с узкого набора, читай `extensions.cost`, корректируй запрос.
- **Порядок пагинации.** `products(first: N, reverse: true)` сортирует по `id DESC`, а не по `created_at`. Используй `sortKey: CREATED_AT, reverse: true` для «новые первыми».
- **`read_all_orders` для исторических данных.** Без этой области `orders(...)` тихо ограничивает результаты 60‑дневным окном. Ошибки не будет, просто будет меньше результатов, чем ожидалось. Для мерчантов Shopify Plus с большим количеством заказов запроси эту область в настройках защищённых данных приложения.
- **Валюты — строки.** Суммы приходят как `"49.00"`, а не `49.0`. Не используй слепо `jq tonumber`, если важна сохранность нулей.
- **Поля Money с несколькими валютами** имеют `shopMoney` (валюта магазина) и `presentmentMoney` (валюта клиента). Выбирай одну из них и используй её последовательно.
## Безопасность

Мутации в Shopify реальны — они создают товары, оформляют возвраты средств, отменяют заказы, отправляют отгрузки. Перед запуском `productDelete`, `orderCancel`, `refundCreate` или любой массовой мутации чётко укажи, что изменяется, в каком магазине, и получи подтверждение от пользователя. Клона данных продакшн‑окружения для тестирования нет, если только пользователь не имеет отдельного dev‑магазина.