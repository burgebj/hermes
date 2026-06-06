#!/usr/bin/env bash
# discover.sh — Query live AntSeed network for models and best peer+model
# Usage:
#   bash discover.sh models [--json]       List models grouped by category
#   bash discover.sh best <task> [--json]  Find best peer+model for task
#   <task>: code | research | vision | chat | cheap | any
set -uo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ANTSEED_BIN="$(command -v antseed 2>/dev/null || true)"
PROXY_URL="http://127.0.0.1:8377"
CMD="${1:-models}"
shift 2>/dev/null || true
JSON_ONLY=false
TASK="any"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --json) JSON_ONLY=true; shift ;;
    code|research|vision|chat|cheap|any) TASK="$1"; shift ;;
    *) shift ;;
  esac
done

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

cat > "$TMPDIR/run.py" << 'PYEOF'
import subprocess, json, sys, re, os, urllib.request

antseed = os.environ.get("ANTSEED_BIN", "")
proxy_url = os.environ.get("PROXY_URL", "http://127.0.0.1:8377")
cmd = os.environ.get("CMD", "models")
task = os.environ.get("TASK", "any")
json_only = os.environ.get("JSON_ONLY", "0") == "1"

# --- Tag→category mapping (generic, NOT model-specific) ---
TAG_CATEGORIES = [
    (["reasoning", "research"], "Reasoning"),
    (["coding", "code"],        "Coding"),
    (["vision", "multimodal"],  "Vision"),
    (["fast"],                  "Fast"),
    (["cheap", "free", "anon"], "Cheap"),
    (["privacy", "tee"],        "Privacy"),
    (["web-search"],            "WebSearch"),
    (["translate", "math"],     "Specialist"),
    (["premium", "agents"],     "Premium"),
]

TASK_TAGS = {
    "research": ["reasoning", "research"],
    "code":     ["coding", "code", "reasoning"],
    "vision":   ["vision", "multimodal"],
    "chat":     ["chat", "fast"],
    "cheap":    ["cheap", "free", "anon"],
    "any":      [],
}

def categorize(tags_str):
    tset = set(t.strip().lower() for t in tags_str.split(",") if t.strip())
    for tag_list, label in TAG_CATEGORIES:
        if any(t in tset for t in tag_list):
            return label
    return "General"

def fetch_peers():
    if not antseed:
        return []
    try:
        raw = subprocess.run([antseed, "network", "browse", "--top", "30"],
                             capture_output=True, text=True, timeout=30).stdout
    except Exception:
        return []
    peers = []
    for line in raw.split("\n"):
        m = re.search(r"([0-9a-fA-F]{40,})", line)
        if m:
            parts = re.split(r"[│┃]", line)
            name = parts[2].strip() if len(parts) >= 3 else "unknown"
            peers.append((m.group(1), name))
    return peers

def fetch_services(pid, pname):
    if not antseed:
        return []
    try:
        raw = subprocess.run([antseed, "network", "peer", pid],
                             capture_output=True, text=True, timeout=15).stdout
    except Exception:
        return []
    services = []
    for line in raw.split("\n"):
        line = line.strip()
        if ("protocols:" not in line and "tags:" not in line) or " in " not in line:
            continue
        tokens = line.split()
        if not tokens:
            continue
        model = tokens[0]
        in_m = re.search(r"\bin\s+\$?([\d.]+)", line)
        out_m = re.search(r"\bout\s+\$?([\d.]+)", line)
        pin = float(in_m.group(1)) if in_m else 999.0
        pout = float(out_m.group(1)) if out_m else 999.0
        proto_m = re.search(r"protocols?:\s*([\w-]+)", line)
        proto = proto_m.group(1) if proto_m else "openai-chat-completions"
        tag_m = re.search(r"tags?:\s*([\w,\-./ ]+?)(?:\s{2,}|$)", line)
        tags_str = tag_m.group(1).strip().replace(" ", "") if tag_m else ""
        tags_set = set(t.strip().lower() for t in tags_str.split(",") if t.strip())
        services.append({
            "peer_id": pid, "peer_name": pname, "model": model,
            "price_in": pin, "price_out": pout, "protocol": proto,
            "tags_str": tags_str, "tags_set": tags_set,
            "is_free": (pin == 0 and pout == 0) or "free" in tags_set
        })
    return services

def fetch_proxy_models():
    try:
        req = urllib.request.Request(f"{proxy_url}/v1/models",
                                     headers={"Authorization": "Bearer antseed-p2p"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read())
        return [{"peer_id": "proxy", "peer_name": "Proxy", "model": m["id"],
                 "price_in": 0, "price_out": 0, "protocol": "openai-chat-completions",
                 "tags_str": "", "tags_set": set(), "is_free": False}
                for m in data.get("data", [])]
    except Exception:
        return []

# --- Collect all services from network ---
all = []
for pid, pname in fetch_peers():
    all.extend(fetch_services(pid, pname))
if not all:
    all = fetch_proxy_models()
if not all:
    print(json.dumps({"error": "No models found"}))
    sys.exit(2)

# Deduplicate (cheapest per model)
seen = {}
for s in all:
    mid = s["model"]
    if mid not in seen or s["price_in"] < seen[mid]["price_in"]:
        seen[mid] = s
unique = list(seen.values())

# --- MODELS subcommand ---
if cmd == "models":
    cats = {}
    for s in unique:
        cat = categorize(s["tags_str"])
        cats.setdefault(cat, []).append({
            "model": s["model"], "peer": s["peer_name"],
            "in": s["price_in"], "out": s["price_out"],
            "proto": s["protocol"], "tags": s["tags_str"]
        })
    output = {"total": len(unique), "peers": len(set(s["peer_id"] for s in all)), "categories": cats}
    print(json.dumps(output, indent=2 if not json_only else None))
    if not json_only:
        print(f"\n📦 {len(unique)} models, {output['peers']} peers", file=sys.stderr)
        for cat, models in sorted(cats.items(), key=lambda x: -len(x[1])):
            print(f"  {cat}: {len(models)}", file=sys.stderr)

# --- BEST subcommand ---
elif cmd == "best":
    desired = set(TASK_TAGS.get(task, []))
    def score(s):
        sc = 0
        if desired:
            sc += len(s["tags_set"] & desired) * 15
        else:
            sc += min(len(s["tags_set"]), 5) * 3
        if s["is_free"]:
            sc += 20
            if "cheap" in desired:
                sc += 30
        if "chat-completions" in s["protocol"]:
            sc += 10
        sc -= int(min(s["price_in"], 20))
        return max(sc, 0)

    for s in unique:
        s["score"] = score(s)
    unique.sort(key=lambda x: (-x["score"], x["price_in"]))

    best = unique[0]
    alts = unique[1:6]
    chain = list(dict.fromkeys(s["peer_id"] for s in unique))[:5]

    def ft(tags):
        return ",".join(sorted(tags)) if isinstance(tags, set) else str(tags)

    output = {
        "task": task,
        "recommended": {
            "peer_id": best["peer_id"], "peer_name": best["peer_name"],
            "model": best["model"],
            "price_in": f"${best['price_in']}/1M", "price_out": f"${best['price_out']}/1M",
            "protocol": best["protocol"], "tags": ft(best["tags_set"]),
            "free": best["is_free"], "score": best["score"]
        },
        "alternatives": [{"peer_id": a["peer_id"], "model": a["model"],
                          "tags": ft(a["tags_set"]), "free": a["is_free"]} for a in alts],
        "fallback_chain": chain
    }
    print(json.dumps(output, indent=2 if not json_only else None))
    if not json_only:
        free = " ✨ FREE!" if best["is_free"] else ""
        print(f'\n🐝 {task}: {best["peer_name"]} / {best["model"]} (${best["price_in"]}/${best["price_out"]}){free}', file=sys.stderr)
PYEOF

ANTSEED_BIN="$ANTSEED_BIN" PROXY_URL="$PROXY_URL" CMD="$CMD" TASK="$TASK" \
  JSON_ONLY=$( [[ "$JSON_ONLY" == true ]] && echo 1 || echo 0 ) \
  python3 "$TMPDIR/run.py"
