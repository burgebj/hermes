#!/usr/bin/env python3
"""Square API CLI for Hermes Agent.

Wraps the Square Python SDK with a convenient argparse interface.

Usage:
  python square_api.py inventory counts [--location LOC] [--catalog-object-id ID]
  python square_api.py inventory adjust --catalog-object-id ID --location LOC --quantity N --reason TEXT
  python square_api.py inventory changes --location LOC [--start-time DATETIME] [--end-time DATETIME]
  python square_api.py catalog list --types "item,variation"
  python square_api.py catalog search --query QUERY [--types TYPES]
  python square_api.py catalog get OBJECT_ID
  python square_api.py customers list [--max N]
  python square_api.py customers search --query QUERY
  python square_api.py customers create --given-name NAME [--family-name NAME] [--email EMAIL] [--phone PHONE]
  python square_api.py customers update CUSTOMER_ID [--phone PHONE] [--email EMAIL]
  python square_api.py customers get CUSTOMER_ID
  python square_api.py orders list --location LOC [--start-time DATETIME] [--end-time DATETIME]
  python square_api.py orders get ORDER_ID
  python square_api.py locations list
"""

import argparse
import json
import os
import sys
from pathlib import Path

try:
    from hermes_constants import get_hermes_home
except ModuleNotFoundError:
    HERMES_AGENT_ROOT = Path(__file__).resolve().parents[4]
    if HERMES_AGENT_ROOT.exists():
        sys.path.insert(0, str(HERMES_AGENT_ROOT))
    from hermes_constants import get_hermes_home

HERMES_HOME = get_hermes_home()
TOKEN_PATH = HERMES_HOME / "square_token.json"
CLIENT_SECRET_PATH = HERMES_HOME / "square_client_secret.json"

API_BASE = "https://connect.squareup.com/v2"


def _get_client():
    """Build an authenticated Square API client."""
    if not TOKEN_PATH.exists():
        print("ERROR: Not authenticated. Run setup.py --check first.")
        sys.exit(1)

    from squareup import Client
    from squareup.oauth2 import OAuth2

    token_data = json.loads(TOKEN_PATH.read_text())
    access_token = token_data.get("access_token")
    if not access_token:
        print("ERROR: No access token. Re-run OAuth setup.")
        sys.exit(1)

    client_id = ""
    if CLIENT_SECRET_PATH.exists():
        secret_data = json.loads(CLIENT_SECRET_PATH.read_text())
        client_id = secret_data.get("clientId", "")

    return Client(
        access_token=access_token,
        square_version="2026-01-22",
    )


def _api_request(method: str, path: str, body: dict | None = None, version: str = "v2") -> dict:
    """Make a direct REST API call. Used when SDK coverage is insufficient."""
    import urllib.request
    import urllib.error

    token_data = json.loads(TOKEN_PATH.read_text())
    access_token = token_data.get("access_token")

    url = f"{API_BASE}/{path}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Square-Version": "2026-01-22",
    }

    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = json.loads(e.read())
        print(f"ERROR {e.code}: {error_body}")
        sys.exit(1)


# -- Inventory --

def cmd_inventory_counts(args):
    client = _get_client()
    params = {}
    if args.catalog_object_id:
        params["catalog_object_ids"] = [args.catalog_object_id]
    if args.location:
        params["location_ids"] = [args.location]
    if args.start_time:
        params["start_time"] = args.start_time
    if args.end_time:
        params["end_time"] = args.end_time

    result = client.inventory.batch_retrieve_inventory_counts(**params)
    print(json.dumps(result.body, indent=2))


def cmd_inventory_adjust(args):
    body = {
        "idempotency_key": f"adjust-{args.catalog_object_id}-{args.location}",
        "changes": [
            {
                "type": "ADJUSTMENT",
                "physical_count": None,
                "adjustment": {
                    "catalog_object_id": args.catalog_object_id,
                    "location_id": args.location,
                    "quantity": str(args.quantity),
                    "reason": args.reason or "UNKNOWN",
                },
            }
        ],
    }
    result = _api_request("POST", "inventory/changes/batch-create", body)
    print(json.dumps(result, indent=2))


def cmd_inventory_changes(args):
    params = {}
    if args.location:
        params["location_ids"] = [args.location]
    if args.start_time:
        params["start_time"] = args.start_time
    if args.end_time:
        params["end_time"] = args.end_time

    client = _get_client()
    result = client.inventory.batch_retrieve_inventory_changes(**params)
    print(json.dumps(result.body, indent=2))


# -- Catalog --

def cmd_catalog_list(args):
    client = _get_client()
    types = args.types.split(",") if args.types else None
    result = client.catalog.list_catalog(types=types)
    print(json.dumps(result.body, indent=2))


def cmd_catalog_search(args):
    client = _get_client()
    body = {"text_query": {"attribute_name": "name", "text": args.query}}
    if args.types:
        body["object_types"] = args.types.split(",")
    result = client.catalog.search_catalog_objects(**body)
    print(json.dumps(result.body, indent=2))


def cmd_catalog_get(args):
    client = _get_client()
    result = client.catalog.retrieve_catalog_object(args.object_id, include_related_objects=True)
    print(json.dumps(result.body, indent=2))


# -- Customers --

def cmd_customers_list(args):
    client = _get_client()
    result = client.customers.list_customers(limit=args.max or 50)
    print(json.dumps(result.body, indent=2))


def cmd_customers_search(args):
    client = _get_client()
    body = {
        "query": {
            "text_query": {
                "attribute_name": "text",
                "text": args.query,
            }
        },
        "limit": args.max or 50,
    }
    result = client.customers.search_customers(**body)
    print(json.dumps(result.body, indent=2))


def cmd_customers_create(args):
    client = _get_client()
    import uuid
    body = {
        "idempotency_key": str(uuid.uuid4()),
        "given_name": args.given_name,
    }
    if args.family_name:
        body["family_name"] = args.family_name
    if args.email:
        body["email_address"] = args.email
    if args.phone:
        body["phone_number"] = args.phone

    result = client.customers.create_customer(**body)
    print(json.dumps(result.body, indent=2))


def cmd_customers_update(args):
    client = _get_client()
    body = {"customer_id": args.customer_id}
    if args.email:
        body["email_address"] = args.email
    if args.phone:
        body["phone_number"] = args.phone
    if args.given_name:
        body["given_name"] = args.given_name
    if args.family_name:
        body["family_name"] = args.family_name

    result = client.customers.update_customer(args.customer_id, **body)
    print(json.dumps(result.body, indent=2))


def cmd_customers_get(args):
    client = _get_client()
    result = client.customers.retrieve_customer(args.customer_id)
    print(json.dumps(result.body, indent=2))


# -- Orders --

def cmd_orders_list(args):
    client = _get_client()
    from datetime import datetime, timedelta, timezone as tz
    now = datetime.now(tz.utc)
    start_time = args.start_time or (now - timedelta(days=7)).isoformat()
    end_time = args.end_time or now.isoformat()

    result = client.orders.search_orders(
        location_ids=[args.location],
        query={
            "filter": {
                "date_time_filter": {
                    "created_at": {
                        "start_at": start_time,
                        "end_at": end_time,
                    }
                }
            }
        },
    )
    print(json.dumps(result.body, indent=2))


def cmd_orders_get(args):
    client = _get_client()
    result = client.orders.retrieve_order(args.order_id)
    print(json.dumps(result.body, indent=2))


# -- Locations --

def cmd_locations_list(args):
    client = _get_client()
    result = client.locations.list_locations()
    print(json.dumps(result.body, indent=2))


# -- CLI parser --

def main():
    parser = argparse.ArgumentParser(description="Square API for Hermes Agent")
    sub = parser.add_subparsers(dest="service", required=True)

    # --- Inventory ---
    inv = sub.add_parser("inventory")
    inv_sub = inv.add_subparsers(dest="action", required=True)

    p = inv_sub.add_parser("counts")
    p.add_argument("--location", default="", help="Location ID")
    p.add_argument("--catalog-object-id", default="", help="Catalog object ID")
    p.add_argument("--start-time", default="", help="ISO 8601 start time")
    p.add_argument("--end-time", default="", help="ISO 8601 end time")
    p.set_defaults(func=cmd_inventory_counts)

    p = inv_sub.add_parser("adjust")
    p.add_argument("--catalog-object-id", required=True, help="Catalog object ID")
    p.add_argument("--location", required=True, help="Location ID")
    p.add_argument("--quantity", type=int, required=True, help="Quantity to adjust (positive or negative)")
    p.add_argument("--reason", default="", help="Reason for adjustment")
    p.set_defaults(func=cmd_inventory_adjust)

    p = inv_sub.add_parser("changes")
    p.add_argument("--location", default="", help="Location ID")
    p.add_argument("--start-time", default="", help="ISO 8601 start time")
    p.add_argument("--end-time", default="", help="ISO 8601 end time")
    p.set_defaults(func=cmd_inventory_changes)

    # --- Catalog ---
    cat = sub.add_parser("catalog")
    cat_sub = cat.add_subparsers(dest="action", required=True)

    p = cat_sub.add_parser("list")
    p.add_argument("--types", default="", help="Comma-separated types (item,variation,category,etc.)")
    p.set_defaults(func=cmd_catalog_list)

    p = cat_sub.add_parser("search")
    p.add_argument("--query", required=True, help="Search query")
    p.add_argument("--types", default="", help="Comma-separated object types")
    p.set_defaults(func=cmd_catalog_search)

    p = cat_sub.add_parser("get")
    p.add_argument("object_id", help="Catalog object ID")
    p.set_defaults(func=cmd_catalog_get)

    # --- Customers ---
    cust = sub.add_parser("customers")
    cust_sub = cust.add_subparsers(dest="action", required=True)

    p = cust_sub.add_parser("list")
    p.add_argument("--max", type=int, default=50)
    p.set_defaults(func=cmd_customers_list)

    p = cust_sub.add_parser("search")
    p.add_argument("--query", required=True, help="Search query")
    p.add_argument("--max", type=int, default=50)
    p.set_defaults(func=cmd_customers_search)

    p = cust_sub.add_parser("create")
    p.add_argument("--given-name", required=True)
    p.add_argument("--family-name", default="")
    p.add_argument("--email", default="")
    p.add_argument("--phone", default="")
    p.set_defaults(func=cmd_customers_create)

    p = cust_sub.add_parser("update")
    p.add_argument("customer_id", help="Customer ID")
    p.add_argument("--given-name", default="")
    p.add_argument("--family-name", default="")
    p.add_argument("--email", default="")
    p.add_argument("--phone", default="")
    p.set_defaults(func=cmd_customers_update)

    p = cust_sub.add_parser("get")
    p.add_argument("customer_id", help="Customer ID")
    p.set_defaults(func=cmd_customers_get)

    # --- Orders ---
    ord_ = sub.add_parser("orders")
    ord_sub = ord_.add_subparsers(dest="action", required=True)

    p = ord_sub.add_parser("list")
    p.add_argument("--location", required=True, help="Location ID")
    p.add_argument("--start-time", default="", help="ISO 8601 start time")
    p.add_argument("--end-time", default="", help="ISO 8601 end time")
    p.set_defaults(func=cmd_orders_list)

    p = ord_sub.add_parser("get")
    p.add_argument("order_id", help="Order ID")
    p.set_defaults(func=cmd_orders_get)

    # --- Locations ---
    loc = sub.add_parser("locations")
    loc_sub = loc.add_subparsers(dest="action", required=True)

    p = loc_sub.add_parser("list")
    p.set_defaults(func=cmd_locations_list)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
