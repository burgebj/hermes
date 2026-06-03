#!/usr/bin/env python3
"""
Reference HAMT builder for the simplicio-prompt spec.

Generic enough to ingest:
  - A list of yool names (one per line, from stdin or --source path)
  - An AGENTS.md file with `yool_id:` fields
  - A PROJECTS.md / catalog markdown with `### name` blocks

Outputs:
  - JSON catalog at --output path
  - stderr: stats + ASCII tree visualization
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

BITS_PER_LEVEL = 5
BRANCH = 1 << BITS_PER_LEVEL
MAX_LEVELS = 6
HASH_BITS = BITS_PER_LEVEL * MAX_LEVELS


def yool_hash(name: str) -> int:
    h = hashlib.blake2b(name.encode("utf-8"), digest_size=8).digest()
    n = int.from_bytes(h, "big")
    return n & ((1 << HASH_BITS) - 1)


def slot_at(h: int, level: int) -> int:
    shift = (MAX_LEVELS - 1 - level) * BITS_PER_LEVEL
    return (h >> shift) & (BRANCH - 1)


@dataclass
class Leaf:
    key: str
    hash: int
    value: dict[str, Any]
    kind: str = "leaf"


@dataclass
class Collision:
    hash_prefix: int
    leaves: list[Leaf] = field(default_factory=list)
    kind: str = "collision"


@dataclass
class Node:
    bitmap: int = 0
    children: dict[int, Any] = field(default_factory=dict)
    kind: str = "node"


def insert(root: Node, leaf: Leaf, level: int = 0) -> None:
    if level >= MAX_LEVELS:
        slot = leaf.hash & (BRANCH - 1)
        existing = root.children.get(slot)
        if existing is None:
            root.bitmap |= 1 << slot
            root.children[slot] = Collision(hash_prefix=leaf.hash, leaves=[leaf])
        elif isinstance(existing, Collision):
            existing.leaves.append(leaf)
        else:
            raise RuntimeError("unexpected node at collision depth")
        return

    slot = slot_at(leaf.hash, level)
    existing = root.children.get(slot)

    if existing is None:
        root.bitmap |= 1 << slot
        root.children[slot] = leaf
        return

    if isinstance(existing, Leaf):
        if existing.hash == leaf.hash and existing.key == leaf.key:
            existing.value = leaf.value
            return
        sub = Node()
        insert(sub, existing, level + 1)
        insert(sub, leaf, level + 1)
        root.children[slot] = sub
        return

    if isinstance(existing, Node):
        insert(existing, leaf, level + 1)
        return

    raise RuntimeError(f"unexpected child kind: {type(existing)}")


def lookup(root: Node, key: str) -> Leaf | None:
    h = yool_hash(key)
    node: Any = root
    for lvl in range(MAX_LEVELS):
        if not isinstance(node, Node):
            break
        slot = slot_at(h, lvl)
        child = node.children.get(slot)
        if child is None:
            return None
        if isinstance(child, Leaf):
            return child if child.key == key else None
        if isinstance(child, Collision):
            for leaf in child.leaves:
                if leaf.key == key:
                    return leaf
            return None
        node = child
    return None


def to_json(node: Any) -> Any:
    if isinstance(node, Leaf):
        return {
            "kind": "leaf",
            "key": node.key,
            "hash": f"{node.hash:030b}",
            "value": node.value,
        }
    if isinstance(node, Collision):
        return {
            "kind": "collision",
            "hash_prefix": f"{node.hash_prefix:030b}",
            "leaves": [to_json(leaf) for leaf in node.leaves],
        }
    if isinstance(node, Node):
        return {
            "kind": "node",
            "bitmap": f"{node.bitmap:032b}",
            "popcount": bin(node.bitmap).count("1"),
            "children": {str(s): to_json(c) for s, c in sorted(node.children.items())},
        }
    raise TypeError(node)


def viz(
    node: Any, prefix: str = "", is_last: bool = True, label: str = "root"
) -> list[str]:
    connector = "+-- " if is_last else "|-- "
    lines: list[str] = []
    if isinstance(node, Leaf):
        lines.append(f"{prefix}{connector}[leaf] {label}: {node.key}")
        return lines
    if isinstance(node, Collision):
        lines.append(
            f"{prefix}{connector}[collision] {label} ({len(node.leaves)} leaves)"
        )
        new_prefix = prefix + ("    " if is_last else "|   ")
        for i, leaf in enumerate(node.leaves):
            lines.extend(viz(leaf, new_prefix, i == len(node.leaves) - 1, f"#{i}"))
        return lines
    if isinstance(node, Node):
        pop = bin(node.bitmap).count("1")
        lines.append(f"{prefix}{connector}[node] {label}  popcount={pop}/{BRANCH}")
        new_prefix = prefix + ("    " if is_last else "|   ")
        items = sorted(node.children.items())
        for i, (slot, child) in enumerate(items):
            lines.extend(
                viz(child, new_prefix, i == len(items) - 1, f"slot[{slot:02d}]")
            )
        return lines
    return lines


YOOL_ID = re.compile(r"^\s*-?\s*\*?\*?yool_id\*?\*?:\s*`?([^`\n]+?)`?\s*$", re.M | re.I)
LANE = re.compile(r"^\s*-?\s*\*?\*?lane\*?\*?:\s*`?([^`\n]+?)`?\s*$", re.M | re.I)
AUTHORITY = re.compile(r"^\s*-?\s*\*?\*?authority\*?\*?:\s*(.+)$", re.M | re.I)


def parse_agents_md(text: str) -> list[dict[str, Any]]:
    """Parse AGENTS.md-style blocks with ### header + yool_id/lane/authority fields."""
    blocks = re.split(r"^###\s+", text, flags=re.M)[1:]
    out: list[dict[str, Any]] = []
    for block in blocks:
        lines = block.splitlines()
        if not lines:
            continue
        name = lines[0].strip()
        m_yool = YOOL_ID.search(block)
        if not m_yool:
            continue
        m_lane = LANE.search(block)
        m_auth = AUTHORITY.search(block)
        out.append({
            "agent": name,
            "yool_id": m_yool.group(1).strip(),
            "lane": m_lane.group(1).strip() if m_lane else "",
            "authority": m_auth.group(1).strip() if m_auth else "",
        })
    return out


def parse_yool_list(text: str) -> list[dict[str, Any]]:
    """Parse one yool per line."""
    out: list[dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append({"yool_id": line})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Build HAMT catalog over yool names.")
    ap.add_argument(
        "--source",
        required=True,
        help="Path to source file (.md or .txt) or '-' for stdin",
    )
    ap.add_argument("--output", required=True, help="Output JSON path")
    ap.add_argument(
        "--format", choices=["auto", "agents-md", "yool-list"], default="auto"
    )
    args = ap.parse_args()

    if args.source == "-":
        text = sys.stdin.read()
        fmt = args.format if args.format != "auto" else "yool-list"
    else:
        path = Path(args.source).expanduser()
        text = path.read_text(encoding="utf-8")
        if args.format == "auto":
            fmt = "agents-md" if path.suffix.lower() == ".md" else "yool-list"
        else:
            fmt = args.format

    entries = parse_agents_md(text) if fmt == "agents-md" else parse_yool_list(text)
    if not entries:
        print("error: no yool entries parsed", file=sys.stderr)
        return 1

    root = Node()
    flat: dict[str, dict[str, Any]] = {}
    for e in entries:
        key = e["yool_id"]
        h = yool_hash(key)
        insert(root, Leaf(key=key, hash=h, value=e))
        flat[key] = {
            "hash": f"{h:030b}",
            "hash_hex": f"{h:08x}",
            "slots": [slot_at(h, lvl) for lvl in range(MAX_LEVELS)],
            "value": e,
        }

    catalog = {
        "meta": {
            "source": args.source,
            "format": fmt,
            "count": len(entries),
            "branching": BRANCH,
            "bits_per_level": BITS_PER_LEVEL,
            "max_levels": MAX_LEVELS,
            "hash_bits": HASH_BITS,
            "hash_algo": "blake2b-64bit-truncated-to-30bit",
        },
        "flat": flat,
        "trie": to_json(root),
    }

    out_path = Path(args.output).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(
        f"# HAMT catalog: {len(entries)} entries, branching={BRANCH}, max_levels={MAX_LEVELS}",
        file=sys.stderr,
    )
    print(f"# wrote: {out_path}", file=sys.stderr)
    print("", file=sys.stderr)
    print("\n".join(viz(root)), file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
