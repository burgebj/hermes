#!/usr/bin/env python3
"""
Dataset Search CLI — search and discover open datasets via HuggingFace Datasets API.

Usage:
    python3 dataset_search.py search "chest xray"
    python3 dataset_search.py search "text classification" --task text-classification --limit 10
    python3 dataset_search.py popular --limit 10
    python3 dataset_search.py detail "keremberke/chest-xray-classification"

No API key required. Uses HuggingFace Datasets API.
"""

import json
import sys
import urllib.parse
import urllib.request

HF_API = "https://huggingface.co/api/datasets"
USER_AGENT = "Mozilla/5.0"


def api_request(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def search_datasets(params: dict) -> list:
    url = f"{HF_API}?{urllib.parse.urlencode(params)}"
    data = api_request(url)
    results = []
    for ds in data:
        results.append({
            "id": ds.get("id", ""),
            "likes": ds.get("likes", 0),
            "downloads": ds.get("downloads", 0),
            "tags": ds.get("tags", [])[:8],
            "siblings": len(ds.get("siblings", [])),
            "created_at": ds.get("createdAt", ""),
            "last_modified": ds.get("lastModified", ""),
        })
    return results


def cmd_search(args):
    params = {"search": args.query, "sort": "likes", "direction": -1, "limit": args.limit}
    if args.task:
        params["task_categories"] = args.task
    if args.modality:
        params["modality"] = args.modality
    if args.lang:
        params["language"] = args.lang
    
    results = search_datasets(params)
    output = {"query": args.query, "total": len(results), "results": results}
    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_popular(args):
    params = {"sort": "likes", "direction": -1, "limit": args.limit}
    results = search_datasets(params)
    output = {"popular": True, "results": results}
    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_detail(args):
    url = f"{HF_API}/{urllib.parse.quote(args.dataset_id, safe='')}"
    data = api_request(url)
    
    detail = {
        "id": data.get("id"),
        "description": (data.get("description") or "")[:2000],
        "likes": data.get("likes", 0),
        "downloads": data.get("downloads", 0),
        "tags": data.get("tags", []),
        "citation": (data.get("citation") or "")[:500] if data.get("citation") else "",
        "card_data": data.get("cardData", {}),
        "configs": [c.get("config_name") for c in data.get("configs", []) if c.get("config_name")],
        "siblings": len(data.get("siblings", [])),
        "paper_url": data.get("paperUrl"),
        "created_at": data.get("createdAt"),
        "last_modified": data.get("lastModified"),
    }
    
    # Extract useful cardData fields
    card = detail["card_data"] or {}
    detail["license"] = card.get("license", "")
    detail["size"] = card.get("size_categories", [])
    detail["task"] = card.get("task_categories", [])
    detail["modality"] = card.get("modality", [])
    detail["language"] = card.get("language", [])
    
    print(json.dumps(detail, indent=2, ensure_ascii=False))


def print_usage():
    print(__doc__)


def main():
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    command = sys.argv[1]

    if command == "search":
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument("query")
        p.add_argument("--task", help="Task category (e.g. image-classification, text-classification)")
        p.add_argument("--modality", help="Data modality (e.g. image, text, audio)")
        p.add_argument("--lang", help="Language code (e.g. en, tr)")
        p.add_argument("--limit", type=int, default=10)
        args = p.parse_args(sys.argv[2:])
        cmd_search(args)
    elif command == "popular":
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument("--limit", type=int, default=10)
        args = p.parse_args(sys.argv[2:])
        cmd_popular(args)
    elif command == "detail":
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument("dataset_id", help="Dataset ID (e.g. keremberke/chest-xray-classification)")
        args = p.parse_args(sys.argv[2:])
        cmd_detail(args)
    elif command in ("--help", "-h"):
        print_usage()
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        print_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()