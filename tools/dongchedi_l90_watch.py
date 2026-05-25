import argparse
import asyncio
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import aiosqlite
from crawl4ai import AsyncWebCrawler, BrowserConfig

from guazi_l90_watch import (
    DB_SCHEMA,
    Listing,
    compact_output,
    clean_text,
    dump_debug_snapshot,
    fetch_page_with_verification_support,
    first_group,
    manual_verify_once,
    normalize_city,
    now_iso,
)

from dongchedi_decoder import (
    extract_car_info,
    extract_sku_list,
    get_pagination_info,
    extract_mileage_from_meta,
    extract_price_from_text,
)


def normalize_year_month(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.replace("年", "-").replace("月", "").replace("/", "-").replace(".", "-")
    match = re.search(r"([0-9]{4})-([0-9]{1,2})", normalized)
    if not match:
        year_only = re.search(r"([0-9]{4})", normalized)
        return year_only.group(1) if year_only else None
    return f"{match.group(1)}-{int(match.group(2)):02d}"


def parse_chinese_ten_thousands(value: str) -> Optional[int]:
    mapping = {
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
        "十": 10,
    }
    if not value:
        return None
    if value in mapping:
        return mapping[value] * 10000
    if value.endswith("十") and value[:-1] in mapping:
        return mapping[value[:-1]] * 100000
    return None


def parse_price_wan(text: str, html: str = "") -> Optional[float]:
    """Parse price in wan. Uses extract_price_from_text which computes from plain text guide_price - save_price."""
    if html:
        price = extract_price_from_text(text)
        if price is not None:
            return price

    # Fallback: regex on rendered text
    value = first_group(
        [
            r"(?:现在仅售|仅售|一口价|售价|现价|车价|卖价|报价|到手价)\s*([0-9]+(?:\.[0-9]+)?)\s*万",
            r"(?:一口价|售价|现价|车价|卖价|报价)\s*([0-9]+(?:\.[0-9]+)?)\s*万",
            r"#\s*[^\n]*乐道\s*L?90[^\n]*\n(?:[^\n]*\n){0,2}?([0-9]+(?:\.[0-9]+)?)\s*万(?!公里)",
            r"([0-9]+(?:\.[0-9]+)?)\s*万(?!公里)\s*(?:包过户|可分期|首付|到手价|首付仅)",
        ],
        text,
    )
    if value:
        return float(value)

    guide_price = first_group([r"新车指导价[:：]\s*([0-9]+(?:\.[0-9]+)?)\s*万"], text)
    save_price = first_group([r"比新车省[:：]\s*([0-9]+(?:\.[0-9]+)?)\s*万"], text)
    if guide_price and save_price:
        return round(float(guide_price) - float(save_price), 2)

    return None


def parse_mileage_km(text: str, html: str = "") -> Optional[int]:
    """Parse mileage in km. Prioritizes meta description which has clean text."""
    # Method 1: meta description (has clean text with mileage, no icon font issues)
    if html:
        mileage = extract_mileage_from_meta(html)
        if mileage is not None:
            return mileage

    # Method 2: regex on rendered text (works when icon font numbers survived)
    value = first_group(
        [
            r"(?:表显里程|行驶里程|里程)\s*([0-9]+(?:\.[0-9]+)?)\s*万公里",
            r"(?:表显里程|行驶里程|里程)\s*([0-9]{3,7})\s*公里",
            r"([0-9]+(?:\.[0-9]+)?)\s*万多公里",
            r"([0-9]+(?:\.[0-9]+)?)\s*万公里",
            r"([0-9]{3,7})\s*公里",
        ],
        text,
    )
    if not value:
        chinese_value = first_group([r"([一二两三四五六七八九十]+)\s*万多公里"], text)
        return parse_chinese_ten_thousands(chinese_value) if chinese_value else None
    if "." in value:
        return int(float(value) * 10000)
    return int(value)


def parse_claim_count(text: str) -> Optional[int]:
    value = first_group(
        [
            r"理赔\s*([0-9]{1,2})\s*次",
            r"理赔次数\s*([0-9]{1,2})",
            r"出险\s*([0-9]{1,2})\s*次",
            r"出险次数\s*([0-9]{1,2})",
        ],
        text,
    )
    if value:
        return int(value)
    zero_probes = [
        "零出险",
        "零理赔",
        "没有出险",
        "无出险",
        "无理赔",
        "没有理赔",
        "未出险",
    ]
    return 0 if any(p in text for p in zero_probes) else None


def parse_city(text: str) -> Optional[str]:
    city = first_group(
        [
            r"(?:^|\n)([^\n，,；; ]{1,12})\n车源地(?:\n|$)",
            r"(?:^|\n)([^\n，,；; ]{1,12})\n上牌地(?:\n|$)",
            r"车源地[ :：]*([^\n，,；; ]+)",
            r"所在城市[ :：]*([^\n，,；; ]+)",
            r"车辆所在地[ :：]*([^\n，,；; ]+)",
            r"/([^\n/]+)车源",
        ],
        text,
    )
    return normalize_city(city)


def parse_first_license_date(text: str) -> Optional[str]:
    value = first_group(
        [
            r"首次上牌\s*([0-9]{4}[-/.年][0-9]{1,2}(?:月)?)",
            r"上牌时间\s*([0-9]{4}[-/.年][0-9]{1,2}(?:月)?)",
            r"([0-9]{4}年[0-9]{1,2}月)",
            r"([0-9]{4}-[0-9]{1,2})",
        ],
        text,
    )
    return normalize_year_month(value)


def parse_transfer_count(text: str) -> Optional[int]:
    value = first_group(
        [
            r"([0-9]{1,2})次\s*\n过户次数",
            r"过户\s*([0-9]{1,2})\s*次",
            r"过户次数\s*([0-9]{1,2})",
        ],
        text,
    )
    return int(value) if value else None


def parse_seller_type(text: str) -> Optional[str]:
    if "个人车源" in text or "个人卖家" in text:
        return "个人"
    if "商家" in text or "经销商" in text:
        return "商家"
    if "官方认证" in text:
        return "官方"
    return None


def parse_seller_name(text: str) -> Optional[str]:
    return first_group(
        [
            r"商家名称[ :：]*([^\n，,；;]{2,30})",
            r"店铺名称[ :：]*([^\n，,；;]{2,30})",
            r"卖家昵称[ :：]*([^\n，,；;]{1,20})",
            r"联系人[ :：]*([^\n，,；;]{1,20})",
            r"归属商家[ :：]*([^\n，,；;]{1,30})",
            r"认证商家[ :：]*([^\n，,；;]{1,30})",
        ],
        text,
    )


def parse_seller_address(text: str) -> Optional[str]:
    return first_group(
        [
            r"商家地址[ :：]*([^\n]{6,100})",
            r"门店地址[ :：]*([^\n]{6,100})",
            r"展厅地址[ :：]*([^\n]{6,100})",
            r"店铺地址[ :：]*([^\n]{6,100})",
            r"展厅[ :：]*([^\n，,；;]{6,100}路[^\n]{0,50})",
            r"地址[ :：]*([^\n]{6,100})",
            r"(\[[^\]]*市[^ \]]{2,20}区[^ \]]{2,40}\])",
            r"((?:浙江省|江苏省|上海市|北京市|广东省|四川省)[^\n]{5,60})",
        ],
        text,
    )


def parse_battery_plan(text: str) -> Optional[str]:
    if re.search(r"(电池方案|电池计划|电池模式|购车方式)\s*(?:[:：]|\s*)\s*(电池买断|买断电池)", text):
        return "电池买断"
    if "电池买断" in text or "买断电池" in text:
        return "电池买断"
    if re.search(r"(BaaS|租电|电池租赁|车电分离)", text, re.I):
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
    path = urlparse(url).path.rstrip("/")
    slug = path.split("/")[-1]
    return slug or url


def is_dongchedi_detail_url(base_url: str, candidate_url: str) -> bool:
    parsed = urlparse(candidate_url)
    if "dongchedi.com" not in parsed.netloc:
        return False
    path = parsed.path.rstrip("/")
    if not path.startswith("/usedcar/"):
        return False

    slug = path.split("/")[-1]
    base_slug = urlparse(base_url).path.rstrip("/").split("/")[-1]
    if not slug or slug == "usedcar" or slug == base_slug:
        return False
    if "," in slug:
        return False
    if slug.count("-") > 10:
        return False
    return bool(re.search(r"\d{5,}", slug))


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
            if is_dongchedi_detail_url(base_url, full):
                urls.add(full)

    if isinstance(links_obj, dict):
        visit(links_obj.get("internal", []))
        visit(links_obj.get("external", []))

    return sorted(urls)


def extract_detail_links_from_html(base_url: str, html: str) -> list[str]:
    urls = set(re.findall(r'href=["\']([^"\']+)["\']', html, re.I))
    out = set()
    for href in urls:
        full = urljoin(base_url, href)
        if is_dongchedi_detail_url(base_url, full):
            out.add(full)
    return sorted(out)


def looks_like_no_results_page(text: str) -> bool:
    t = clean_text(text)
    probes = [
        "暂无车源",
        "暂无结果",
        "暂无符合条件",
        "未找到",
        "没有找到",
        "换个条件试试",
        "清空筛选",
    ]
    return any(p in t for p in probes)


def parse_listing_from_text(url: str, text: str, html: str = "") -> Listing:
    raw_text = clean_text(text)
    title_text = raw_text
    detail_text = raw_text

    return Listing(
        platform="dongchedi",
        listing_id=listing_id_from_url(url),
        title=parse_title(title_text),
        model="乐道L90",
        battery_plan=parse_battery_plan(detail_text),
        price_wan=parse_price_wan(detail_text, html=html),
        mileage_km=parse_mileage_km(detail_text, html=html),
        claim_count=parse_claim_count(detail_text),
        city=parse_city(detail_text),
        first_license_date=parse_first_license_date(detail_text),
        transfer_count=parse_transfer_count(detail_text),
        seller_type=parse_seller_type(detail_text),
        seller_name=parse_seller_name(detail_text),
        seller_address=parse_seller_address(detail_text),
        url=url,
        raw_text=raw_text[:30000],
        fetched_at=now_iso(),
    )


async def fetch_list_page(
    crawler: AsyncWebCrawler,
    url: str,
    session_id: str,
    *,
    headless: bool,
) -> tuple[list[str], str]:
    """Fetch the list page and extract all detail links. Supports pagination."""
    async def _fetch_once(page_url: str) -> tuple[list[str], str, str]:
        result, text_candidate = await fetch_page_with_verification_support(
            crawler,
            page_url,
            session_id,
            stage_label="懂车帝列表页",
            stage_key="dongchedi_list",
            delay_before_return_html=3.0,
            verbose=True,
            headless=headless,
            js_code="window.scrollTo(0, document.body.scrollHeight);",
        )
        html = result.cleaned_html or result.html or ""
        links = extract_detail_links_from_links_obj(url, result.links or {})
        if not links:
            links = extract_detail_links_from_html(url, html)
        return text_candidate, html, links

    # Fetch page 1
    text_candidate, raw_html, links = await _fetch_once(url)
    if not links and not looks_like_no_results_page(text_candidate):
        snap = dump_debug_snapshot("dongchedi_list_empty_links", url, raw_html or text_candidate)
        if headless:
            raise RuntimeError(f"懂车帝列表页未解析到详情链接，调试快照已保存: {snap}")
        print("\n[INFO] 懂车帝列表页没有解析到任何详情链接。")
        print("[INFO] 如果浏览器里正显示二维码、登录框或验证页，请先完成它。")
        input("\n[INPUT] 完成检查后按回车继续...")
        text_candidate, raw_html, links = await _fetch_once(url)
        if not links or looks_like_no_results_page(text_candidate):
            snap = dump_debug_snapshot("dongchedi_list_empty_links_after_retry", url, raw_html or text_candidate)
            raise RuntimeError(f"懂车帝列表页重试后仍未解析到详情链接。调试快照已保存: {snap}")

    # Check pagination via __NEXT_DATA__
    all_links = list(links) if links else []
    pagination = get_pagination_info(raw_html)
    total_page = pagination.get("total_page", 1)
    current_page = pagination.get("page", 1)

    if total_page > 1 and current_page == 1:
        # Fetch subsequent pages
        for page_num in range(2, total_page + 1):
            page_url = re.sub(
                r'(310000-)1(-)',
                lambda m: f"{m.group(1)}{page_num}{m.group(2)}",
                url,
            )
            try:
                _, _, page_links = await _fetch_once(page_url)
                if page_links:
                    all_links.extend(page_links)
                print(f"[INFO] 列表页第{page_num}页: {len(page_links)}个链接")
            except Exception as e:
                print(f"[WARN] 列表页第{page_num}页获取失败: {e}")
                break

    return all_links, raw_html


async def fetch_detail_page(
    crawler: AsyncWebCrawler,
    url: str,
    session_id: str,
    *,
    headless: bool,
) -> Listing:
    result, text_candidate = await fetch_page_with_verification_support(
        crawler,
        url,
        session_id,
        stage_label="懂车帝详情页",
        stage_key="dongchedi_detail",
        delay_before_return_html=2.0,
        verbose=False,
        headless=headless,
    )
    html = (result.cleaned_html or result.html or "") if hasattr(result, "cleaned_html") else (result.html or "")
    return parse_listing_from_text(url, text_candidate, html=html)


async def init_db(db_path: Path):
    async with aiosqlite.connect(db_path) as db:
        await db.executescript(DB_SCHEMA)
        await db.commit()


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
        rows = await db.execute_fetchall("SELECT * FROM listings WHERE platform = 'dongchedi'")
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
        for key in ["price_wan", "mileage_km", "claim_count", "city", "battery_plan", "seller_name", "seller_address"]:
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
        enable_stealth=True,
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport_width=1920,
        viewport_height=1080,
        verbose=True,
    )

    curr: dict[str, Listing] = {}
    session_id = "dongchedi_l90_session"

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
                if item.battery_plan is None:
                    # 懂车帝L90默认为电池买断，只有明确标注BaaS/租电才是租赁
                    item.battery_plan = "电池买断"
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
        default="https://www.dongchedi.com/usedcar/20,!1-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-918-25234-310000-1-x-x-x-x-x",
        help="懂车帝二手车列表页 URL",
    )
    parser.add_argument(
        "--db",
        default="data/dongchedi_l90.sqlite",
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
        default=False,
        action="store_true",
        help="显示浏览器窗口，便于人工验证",
    )
    parser.add_argument(
        "--profile-dir",
        default="~/.crawl4ai/profiles/dongchedi_profile",
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
