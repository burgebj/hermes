import argparse
import asyncio
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional
from urllib.parse import urljoin, urlparse

import aiosqlite
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS listings (
    platform TEXT NOT NULL,
    listing_id TEXT NOT NULL,
    title TEXT,
    model TEXT,
    battery_plan TEXT,
    price_wan REAL,
    mileage_km INTEGER,
    claim_count INTEGER,
    city TEXT,
    first_license_date TEXT,
    transfer_count INTEGER,
    seller_type TEXT,
    seller_name TEXT,
    seller_address TEXT,
    url TEXT NOT NULL,
    raw_text TEXT,
    fetched_at TEXT NOT NULL,
    PRIMARY KEY (platform, listing_id)
);

CREATE TABLE IF NOT EXISTS listings_history (
    platform TEXT NOT NULL,
    listing_id TEXT NOT NULL,
    title TEXT,
    model TEXT,
    battery_plan TEXT,
    price_wan REAL,
    mileage_km INTEGER,
    claim_count INTEGER,
    city TEXT,
    first_license_date TEXT,
    transfer_count INTEGER,
    seller_type TEXT,
    seller_name TEXT,
    seller_address TEXT,
    url TEXT NOT NULL,
    raw_text TEXT,
    fetched_at TEXT NOT NULL
);
"""


@dataclass
class Listing:
    platform: str
    listing_id: str
    title: Optional[str]
    model: str
    battery_plan: Optional[str]
    price_wan: Optional[float]
    mileage_km: Optional[int]
    claim_count: Optional[int]
    city: Optional[str]
    first_license_date: Optional[str]
    transfer_count: Optional[int]
    seller_type: Optional[str]
    seller_name: Optional[str]
    seller_address: Optional[str]
    url: str
    raw_text: str
    fetched_at: str


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(s: str) -> str:
    s = re.sub(r"\u00a0", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{2,}", "\n", s)
    return s.strip()


def first_group(patterns: Iterable[str], text: str, flags=re.I | re.S) -> Optional[str]:
    for pat in patterns:
        m = re.search(pat, text, flags)
        if m:
            return m.group(1).strip()
    return None


def extract_block(text: str, patterns: Iterable[str]) -> str:
    return first_group(patterns, text) or ""


def extract_pricing_block(text: str) -> str:
    return extract_block(
        text,
        [
            r"(?s)(#\s*[^\n]*乐道\s*L?90[^\n]*\n.*?)(?:\n客服咨询立即购买|\n##\s*询底价|\Z)",
        ],
    )


def extract_inquiry_block(text: str) -> str:
    return extract_block(
        text,
        [
            r"(?s)(##\s*询底价.*?)(?:\n提交即表示同意|\n!\[app\]|\Z)",
        ],
    )


def extract_vehicle_detail_block(text: str) -> str:
    return extract_block(
        text,
        [
            r"(?s)(##\s*车况详解.*?)(?:\n##\s*本车卖点|\n##\s*瓜子官方检测报告|\Z)",
        ],
    )


def compact_output(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: compact_output(v) for k, v in obj.items() if k != "raw_text"}
    if isinstance(obj, list):
        return [compact_output(v) for v in obj]
    return obj


def normalize_city(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    value = value.strip().strip(":：")
    if value.endswith("车源"):
        value = value[:-2]
    false_positives = {
        "黑色",
        "白色",
        "灰色",
        "深灰色",
        "浅灰色",
        "银色",
        "红色",
        "蓝色",
        "绿色",
        "紫色",
        "棕色",
        "橙色",
        "米色",
        "香槟色",
        "金色",
    }
    return None if value in false_positives else value


def parse_price_wan(text: str) -> Optional[float]:
    # 优先匹配详情页主报价，避免把“xx万公里”误识别成价格。
    x = first_group([
        r"#\s*[^\n]*乐道\s*L?90[^\n]*\n([0-9]+(?:\.[0-9]+)?)\s*万(?!公里)",
        r"([0-9]+(?:\.[0-9]+)?)\s*万(?!公里)\s*\n新车指导价",
        r"(?:售价|价格|车价|现价|成交价)\s*([0-9]+(?:\.[0-9]+)?)\s*万(?!公里)",
    ], text)
    return float(x) if x else None


def parse_mileage_km(text: str) -> Optional[int]:
    # 优先匹配询底价区块的“2025年上牌/2.32万公里/上海车源”结构。
    x = first_group([
        r"[0-9]{4}年上牌/([0-9]+(?:\.[0-9]+)?)\s*万公里/[^\n/]+车源",
        r"[0-9]{4}年上牌/([0-9]{3,7})\s*公里/[^\n/]+车源",
        r"[0-9]{4}年\s*\|\s*([0-9]+(?:\.[0-9]+)?)\s*万公里\s*\|",
        r"[0-9]{4}年\s*\|\s*([0-9]{3,7})\s*公里\s*\|",
        r"(?:里程|表显里程)\s*([0-9]+(?:\.[0-9]+)?)\s*万公里",
        r"(?:里程|表显里程)\s*([0-9]{3,7})\s*公里",
    ], text)
    if not x:
        return None
    if "." in x:
        return int(float(x) * 10000)
    return int(x)


def parse_claim_count(text: str) -> Optional[int]:
    x = first_group([
        r"理赔\s*([0-9]+)\s*次",
        r"理赔次数\s*([0-9]+)",
        r"出险\s*([0-9]+)\s*次",
    ], text)
    return int(x) if x else None


def parse_city(text: str) -> Optional[str]:
    city = first_group([
        r"[0-9]{4}年上牌/[0-9]+(?:\.[0-9]+)?(?:万)?公里/([^\n/]+)车源",
        r"([^\n，,；; ]+)\s*车源地",
        r"车源地\s*([^\n，,；; ]+)",
        r"所在城市\s*([^\n，,；; ]+)",
        r"车辆所在地\s*([^\n，,；; ]+)",
    ], text)
    return normalize_city(city)


def parse_first_license_date(text: str) -> Optional[str]:
    return first_group([
        r"首次上牌\s*([0-9]{4}[-/.年][0-9]{1,2})",
        r"上牌时间\s*([0-9]{4}[-/.年][0-9]{1,2})",
        r"([0-9]{4})年上牌",
    ], text)


def parse_transfer_count(text: str) -> Optional[int]:
    x = first_group([
        r"过户\s*([0-9]+)\s*次",
        r"过户次数\s*([0-9]+)",
    ], text)
    return int(x) if x else None


def parse_seller_type(text: str) -> Optional[str]:
    # 可按页面实际文案扩展
    if "个人车源" in text:
        return "个人"
    if "商家" in text:
        return "商家"
    if "严选" in text:
        return "严选"
    return None


def parse_battery_plan(text: str) -> Optional[str]:
    if re.search(r"(电池计划|电池方案|电池模式|电池)\s*(?:[:：]|\s*)\s*电池买断", text):
        return "电池买断"
    if "电池买断" in text:
        return "电池买断"
    if re.search(r"(电池计划|电池方案|电池模式|电池)\s*(?:[:：]|\s*)\s*电池租赁", text):
        return "电池租赁"
    if "电池租赁" in text or "租电" in text:
        return "电池租赁"
    return None


def parse_title(text: str) -> Optional[str]:
    return first_group(
        [
            r"#\s*([^\n]*乐道\s*L?90[^\n]*)",
            r"([^\n]{0,30}乐道\s*L?90[^\n]{0,80})",
        ],
        text,
    )


def listing_id_from_url(url: str) -> str:
    # 例如 /car-detail/c161513795298176.html -> c161513795298176
    m = re.search(r"/car-detail/([^/?#]+?)(?:\.html)?$", url)
    if m:
        return m.group(1)
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1] or url

def looks_like_verification_page(text: str) -> bool:
    t = (text or "").lower()
    probes = [
        "验证码",
        "安全验证",
        "请完成验证",
        "访问受限",
        "异常访问",
        "verify",
        "verification",
        "captcha",
        "security check",
        "robot",
    ]
    hit = sum(1 for p in probes if p in t)
    return hit >= 2


def extract_text_candidate(result: Any) -> str:
    text_candidate = ""
    markdown = getattr(result, "markdown", None)
    if isinstance(markdown, str):
        text_candidate = markdown
    elif markdown and hasattr(markdown, "raw_markdown"):
        text_candidate = markdown.raw_markdown
    if not text_candidate:
        text_candidate = getattr(result, "cleaned_html", None) or getattr(result, "html", None) or ""
    return text_candidate


def dump_debug_snapshot(stage: str, url: str, content: str) -> Path:
    out_dir = Path("data/debug")
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_stage = re.sub(r"[^a-zA-Z0-9_-]+", "_", stage)
    path = out_dir / f"{safe_stage}.html"
    path.write_text(content or "", encoding="utf-8")
    return path

def extract_detail_links_from_links_obj(base_url: str, links_obj: dict) -> list[str]:
    urls = set()

    def visit(items):
        if not items:
            return
        for item in items:
            href = item.get("href")
            if not href:
                continue
            full = urljoin(base_url, href)
            if "/car-detail/" in full and "guazi.com" in full:
                urls.add(full)

    if isinstance(links_obj, dict):
        visit(links_obj.get("internal", []))
        visit(links_obj.get("external", []))

    return sorted(urls)


def extract_detail_links_from_html(base_url: str, html: str) -> list[str]:
    urls = set(re.findall(r'href=["\']([^"\']+/car-detail/[^"\']+)["\']', html, re.I))
    out = set()
    for href in urls:
        full = urljoin(base_url, href)
        if "guazi.com" in full:
            out.add(full)
    return sorted(out)


def looks_like_no_results_page(text: str) -> bool:
    t = clean_text(text)
    probes = [
        "暂无车源",
        "暂无结果",
        "未找到",
        "没有找到",
        "抱歉，没有找到",
        "换个条件试试",
    ]
    return any(p in t for p in probes)


def parse_listing_from_text(url: str, text: str) -> Listing:
    raw_text = clean_text(text)
    pricing_block = extract_pricing_block(raw_text)
    inquiry_block = extract_inquiry_block(raw_text)
    detail_block = extract_vehicle_detail_block(raw_text)

    title_text = "\n".join(x for x in [pricing_block, inquiry_block, detail_block, raw_text] if x)
    price_text = "\n".join(x for x in [pricing_block, inquiry_block] if x)
    detail_text = "\n".join(x for x in [detail_block, inquiry_block] if x)
    location_text = "\n".join(x for x in [inquiry_block, detail_block, raw_text] if x)

    return Listing(
        platform="guazi",
        listing_id=listing_id_from_url(url),
        title=parse_title(title_text),
        model="乐道L90",
        battery_plan=parse_battery_plan(detail_text or raw_text),
        price_wan=parse_price_wan(price_text or raw_text),
        mileage_km=parse_mileage_km(location_text),
        claim_count=parse_claim_count(detail_text or raw_text),
        city=parse_city(location_text),
        first_license_date=parse_first_license_date(detail_text or location_text or raw_text),
        transfer_count=parse_transfer_count(detail_text or raw_text),
        seller_type=parse_seller_type(detail_text or raw_text),
        url=url,
        raw_text=raw_text[:30000],  # 避免无限膨胀
        fetched_at=now_iso(),
    )


async def fetch_page_with_verification_support(
    crawler: AsyncWebCrawler,
    url: str,
    session_id: str,
    *,
    stage_label: str,
    stage_key: str,
    delay_before_return_html: float,
    verbose: bool,
    headless: bool,
    js_code: Optional[str] = None,
) -> tuple[Any, str]:
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        session_id=session_id,
        wait_for="css:body",
        delay_before_return_html=delay_before_return_html,
        page_timeout=60000,
        js_code=js_code,
        verbose=verbose,
    )
    result = await crawler.arun(url=url, config=config)
    if not result.success:
        raise RuntimeError(f"{stage_label}抓取失败: {url} :: {result.error_message}")

    text_candidate = extract_text_candidate(result)
    if not looks_like_verification_page(text_candidate):
        return result, text_candidate

    snap = dump_debug_snapshot(f"{stage_key}_verify_page", url, text_candidate)
    if headless:
        raise RuntimeError(
            f"{stage_label}命中验证页，当前为 headless 模式，无法人工继续。调试快照已保存: {snap}"
        )

    print(f"\n[INFO] {stage_label}命中验证页，请在当前浏览器窗口完成验证。")
    print(f"[INFO] 验证完成后回到终端按回车，脚本会在同一个浏览器会话里继续。")
    input("\n[INPUT] 完成验证后按回车继续...")

    retry_result = await crawler.arun(url=url, config=config)
    if not retry_result.success:
        raise RuntimeError(f"{stage_label}验证后重试失败: {url} :: {retry_result.error_message}")

    retry_text_candidate = extract_text_candidate(retry_result)
    if looks_like_verification_page(retry_text_candidate):
        snap = dump_debug_snapshot(f"{stage_key}_verify_page_after_retry", url, retry_text_candidate)
        raise RuntimeError(f"{stage_label}验证后仍停留在验证页: {url}，调试快照已保存: {snap}")

    print(f"[INFO] {stage_label}验证通过，继续抓取。")
    return retry_result, retry_text_candidate


async def fetch_list_page(
    crawler: AsyncWebCrawler,
    url: str,
    session_id: str,
    *,
    headless: bool,
) -> tuple[list[str], str]:
    async def _fetch_once() -> tuple[Any, str, str, list[str]]:
        result, text_candidate = await fetch_page_with_verification_support(
            crawler,
            url,
            session_id,
            stage_label="列表页",
            stage_key="list",
            delay_before_return_html=3.0,
            verbose=True,
            headless=headless,
            js_code="window.scrollTo(0, document.body.scrollHeight);",
        )

        html = result.cleaned_html or result.html or ""

        links = extract_detail_links_from_links_obj(url, result.links or {})
        if not links:
            links = extract_detail_links_from_html(url, html)

        return result, text_candidate, html, links

    _, text_candidate, html, links = await _fetch_once()
    if links:
        return links, html

    if looks_like_no_results_page(text_candidate):
        return links, html

    snap = dump_debug_snapshot("list_empty_links", url, html or text_candidate)
    if headless:
        raise RuntimeError(
            f"列表页未解析到任何详情链接，可能命中验证页或页面未加载完整。调试快照已保存: {snap}"
        )

    print("\n[INFO] 列表页没有解析到任何详情链接。")
    print("[INFO] 如果浏览器里正显示二维码、登录框或验证页，请先完成它。")
    print("[INFO] 完成后回到终端按回车，脚本会在同一个浏览器会话里重试列表页。")
    input("\n[INPUT] 完成检查后按回车继续...")

    _, retry_text_candidate, retry_html, retry_links = await _fetch_once()
    if retry_links or looks_like_no_results_page(retry_text_candidate):
        return retry_links, retry_html

    snap = dump_debug_snapshot("list_empty_links_after_retry", url, retry_html or retry_text_candidate)
    raise RuntimeError(f"列表页重试后仍未解析到详情链接。调试快照已保存: {snap}")

async def fetch_detail_page(
    crawler: AsyncWebCrawler,
    url: str,
    session_id: str,
    *,
    headless: bool,
) -> Listing:
    _, text_candidate = await fetch_page_with_verification_support(
        crawler,
        url,
        session_id,
        stage_label="详情页",
        stage_key="detail",
        delay_before_return_html=2.0,
        verbose=False,
        headless=headless,
    )

    return parse_listing_from_text(url, text_candidate)


async def init_db(db_path: Path):
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(DB_SCHEMA)
        await db.commit()

async def manual_verify_once(crawler: AsyncWebCrawler, url: str, session_id: str):
    print("\n[INFO] 即将打开浏览器，请在窗口中手工完成验证。")
    print("[INFO] 完成后，回到终端按回车。")

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        session_id=session_id,
        wait_for="css:body",
        delay_before_return_html=2.0,
        page_timeout=60000,
        js_code="window.scrollTo(0, document.body.scrollHeight * 0.3);",
        verbose=True,
    )

    result = await crawler.arun(url=url, config=config)
    if not result.success:
        raise RuntimeError(f"打开验证页失败: {result.error_message}")

    input("\n[INPUT] 请在浏览器中完成验证，完成后按回车继续...")

    # 再访问一次确认 profile/cookies 已生效
    result2 = await crawler.arun(url=url, config=config)
    text_candidate = ""
    if isinstance(result2.markdown, str):
        text_candidate = result2.markdown
    elif result2.markdown and hasattr(result2.markdown, "raw_markdown"):
        text_candidate = result2.markdown.raw_markdown
    if not text_candidate:
        text_candidate = result2.cleaned_html or result2.html or ""

    if looks_like_verification_page(text_candidate):
        snap = dump_debug_snapshot("manual_verify_failed", url, text_candidate)
        raise RuntimeError(f"仍然停留在验证页，调试快照已保存: {snap}")

    print("[INFO] 验证通过，profile 已保存。")

async def upsert_listing(db_path: Path, item: Listing):
    async with aiosqlite.connect(db_path) as db:
        row = asdict(item)
        cols = ",".join(row.keys())
        qmarks = ",".join(["?"] * len(row))
        values = list(row.values())

        await db.execute(
            f"""
            INSERT OR REPLACE INTO listings ({cols})
            VALUES ({qmarks})
            """,
            values,
        )
        await db.execute(
            f"""
            INSERT INTO listings_history ({cols})
            VALUES ({qmarks})
            """,
            values,
        )
        await db.commit()


async def load_previous_snapshot(db_path: Path) -> dict[str, dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall("SELECT * FROM listings WHERE platform = 'guazi'")
        return {row["listing_id"]: dict(row) for row in rows}


def diff_snapshots(prev: dict[str, dict], curr: dict[str, Listing]) -> dict:
    prev_ids = set(prev.keys())
    curr_ids = set(curr.keys())

    new_ids = sorted(curr_ids - prev_ids)
    removed_ids = sorted(prev_ids - curr_ids)

    changed = []
    for lid in sorted(curr_ids & prev_ids):
        p = prev[lid]
        c = asdict(curr[lid])
        delta = {}
        for key in ["price_wan", "mileage_km", "claim_count", "city", "battery_plan"]:
            if p.get(key) != c.get(key):
                delta[key] = {"old": p.get(key), "new": c.get(key)}
        if delta:
            changed.append({"listing_id": lid, "changes": delta, "url": c["url"]})

    return {
        "new": [asdict(curr[x]) for x in new_ids],
        "removed": [{"listing_id": x, "url": prev[x].get("url")} for x in removed_ids],
        "changed": changed,
    }

async def run(
    list_url: str,
    db_path: Path,
    max_details: int,
    headless: bool,
    profile_dir: Path,
    manual_verify_only: bool,
    include_raw_text: bool,
):
    await init_db(db_path)
    prev = await load_previous_snapshot(db_path)

    profile_dir = profile_dir.expanduser().resolve()
    profile_dir.mkdir(parents=True, exist_ok=True)

    browser_cfg = BrowserConfig(
        browser_type="chromium",
        headless=headless,
        use_persistent_context=True,
        user_data_dir=str(profile_dir),
        verbose=True,
    )

    curr: dict[str, Listing] = {}
    session_id = "guazi_l90_session"

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        if manual_verify_only:
            await manual_verify_once(crawler, list_url, session_id=session_id)
            summary = {
                "mode": "manual_verify_only",
                "profile_dir": str(profile_dir),
                "status": "ok",
            }
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return

        links, _ = await fetch_list_page(
            crawler,
            list_url,
            session_id=session_id,
            headless=headless,
        )
        print(f"[INFO] 列表页抽到详情链接数量: {len(links)}")

        links = list(dict.fromkeys(links))[:max_details]

        for url in links:
            try:
                item = await fetch_detail_page(
                    crawler,
                    url,
                    session_id=session_id,
                    headless=headless,
                )
                if item.battery_plan != "电池买断":
                    continue
                curr[item.listing_id] = item
            except Exception as e:
                print(f"[WARN] 详情页失败: {url} :: {e}")

    for item in curr.values():
        await upsert_listing(db_path, item)

    delta = diff_snapshots(prev, curr)

    summary = {
        "run_at": now_iso(),
        "list_url": list_url,
        "profile_dir": str(profile_dir),
        "matched_count": len(curr),
        "new_count": len(delta["new"]),
        "removed_count": len(delta["removed"]),
        "changed_count": len(delta["changed"]),
        "items": [asdict(x) for x in curr.values()],
        "delta": delta,
    }
    print(json.dumps(summary if include_raw_text else compact_output(summary), ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--list-url",
        required=True,
        help="瓜子车型列表页或搜索结果页 URL",
    )
    parser.add_argument(
        "--db",
        default="data/guazi_l90.sqlite",
        help="SQLite 路径",
    )
    parser.add_argument(
        "--max-details",
        type=int,
        default=30,
        help="最多抓多少个详情页",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="显示浏览器窗口，便于人工验证",
    )
    parser.add_argument(
        "--profile-dir",
        default="~/.crawl4ai/profiles/guazi_profile",
        help="持久化 profile 路径",
    )
    parser.add_argument(
        "--manual-verify-only",
        action="store_true",
        help="只打开页面让你手工完成验证并保存 profile，不抓数据",
    )
    parser.add_argument(
        "--include-raw-text",
        action="store_true",
        help="在终端 JSON 中包含详情页原始文本，默认关闭",
    )
    args = parser.parse_args()

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    asyncio.run(
        run(
            list_url=args.list_url,
            db_path=db_path,
            max_details=args.max_details,
            headless=not args.headed,
            profile_dir=Path(args.profile_dir),
            manual_verify_only=args.manual_verify_only,
            include_raw_text=args.include_raw_text,
        )
    )


if __name__ == "__main__":
    main()
