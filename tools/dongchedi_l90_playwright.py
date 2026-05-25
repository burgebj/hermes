#!/usr/bin/env python3
"""
懂车帝乐道L90二手车爬虫 — Playwright stealth 版本
绕过 headless 浏览器检测，直接获取渲染后的页面内容。
"""
import argparse
import asyncio
import json
import random
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

import aiosqlite
from playwright.async_api import async_playwright, Page, BrowserContext

LIST_URL = "https://www.dongchedi.com/usedcar/20,!1-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-x-918-25234-310000-1-x-x-x-x-x"
DB_PATH = Path("data/dongchedi_l90.sqlite")

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
    url TEXT,
    raw_text TEXT,
    fetched_at TEXT,
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
    url TEXT,
    raw_text TEXT,
    fetched_at TEXT,
    checked_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_history_checked ON listings_history(checked_at);
"""


@dataclass
class Listing:
    platform: str = "dongchedi"
    listing_id: str = ""
    title: str = ""
    model: str = ""
    battery_plan: str = ""
    price_wan: float = 0.0
    mileage_km: int = 0
    claim_count: int = 0
    city: str = ""
    first_license_date: str = ""
    transfer_count: int = 0
    seller_type: str = ""
    seller_name: str = ""
    seller_address: str = ""
    url: str = ""
    raw_text: str = ""
    fetched_at: str = ""


def now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip() if text else ""


async def init_db(db_path: Path):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(db_path) as db:
        # 先添加缺失的列（兼容旧数据库）
        for col, coltype in [("checked_at", "TEXT"), ("claim_count", "INTEGER"),
                             ("first_license_date", "TEXT"), ("transfer_count", "INTEGER")]:
            try:
                await db.execute(f"ALTER TABLE listings ADD COLUMN {col} {coltype}")
            except Exception:
                pass
            try:
                await db.execute(f"ALTER TABLE listings_history ADD COLUMN {col} {coltype}")
            except Exception:
                pass
        await db.execute(
            "CREATE INDEX IF NOT EXISTS idx_history_checked ON listings_history(checked_at)")
        await db.commit()


async def upsert_listing(db_path: Path, item: Listing):
    row = asdict(item)
    # 确保 NOT NULL 字段有值
    row.setdefault("platform", "dongchedi")
    row.setdefault("fetched_at", now_iso())
    if not row.get("url"):
        row["url"] = f"https://www.dongchedi.com/usedcar/{row.get('listing_id', '')}"
    cols = ",".join(row.keys())
    qmarks = ",".join(["?"] * len(row))
    values = list(row.values())
    async with aiosqlite.connect(db_path) as db:
        await db.execute(f"INSERT OR REPLACE INTO listings ({cols}) VALUES ({qmarks})", values)
        await db.execute(f"INSERT INTO listings_history ({cols},checked_at) VALUES ({qmarks},?)", values + [now_iso()])
        await db.commit()


async def load_prev(db_path: Path) -> dict[str, dict]:
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        rows = await db.execute_fetchall("SELECT * FROM listings WHERE platform='dongchedi'")
        return {r["listing_id"]: dict(r) for r in rows}


def diff(prev: dict[str, dict], curr: dict[str, Listing]) -> dict:
    curr_ids = set(curr.keys())
    prev_ids = set(prev.keys())
    changed = []
    for lid in curr_ids & prev_ids:
        p = prev[lid]
        c = asdict(curr[lid])
        delta = {}
        for key in ["price_wan", "mileage_km", "city", "seller_name", "seller_address"]:
            if p.get(key) != c.get(key):
                delta[key] = {"old": p.get(key), "new": c.get(key)}
        if delta:
            changed.append({"listing_id": lid, "changes": delta, "url": c["url"]})
    return {
        "new": [asdict(curr[x]) for x in sorted(curr_ids - prev_ids)],
        "removed": [{"listing_id": x, "url": prev[x].get("url")} for x in sorted(prev_ids - curr_ids)],
        "changed": changed,
    }


async def parse_listing_from_card(card, page_url: str) -> Optional[Listing]:
    """从卡片元素解析 Listing 对象"""
    try:
        # 提取车辆ID
        href = await card.get_attribute("href") or ""
        listing_id_match = re.search(r"/usedcar/(\d+)", href)
        if not listing_id_match:
            # 尝试从data-*属性获取
            listing_id = href.split("/")[-1] if href else ""
        else:
            listing_id = listing_id_match.group(1)

        if not listing_id:
            return None

        # 价格
        price_el = await card.query_selector(".dcw-price-text, .value, [class*='price'], [class*='Price']")
        price_text = clean(await price_el.inner_text() if price_el else "") if price_el else ""
        price_match = re.search(r"([\d.]+)", price_text.replace("万", ""))
        price_wan = float(price_match.group(1)) if price_match else 0.0

        # 里程
        mileage_el = await card.query_selector("[class*='mileage'], [class*='里程'], .mileage, [class*='km']")
        mileage_text = clean(await mileage_el.inner_text() if mileage_el else "") if mileage_el else ""
        km_match = re.search(r"([\d.]+)\s*[万萬]?\s*km", mileage_text)
        if not km_match:
            km_match = re.search(r"([\d.]+)", mileage_text)
        mileage_km = int(float(km_match.group(1)) * 10000) if km_match else 0

        # 城市
        city_el = await card.query_selector("[class*='city'], [class*='城市'], .city")
        city = clean(await city_el.inner_text() if city_el else "") if city_el else ""

        # 车型（从标题或标签）
        title_el = await card.query_selector("h3, h4, [class*='title'], [class*='name'], .title")
        title = clean(await title_el.inner_text() if title_el else "") if title_el else ""
        model = title

        # 卖家类型
        seller_type = "商家"  # 默认
        seller_el = await card.query_selector("[class*='personal'], [class*='个人']")
        if seller_el:
            seller_type = "个人"

        # 卖家名称
        seller_name_el = await card.query_selector("[class*='dealer'], [class*='shop'], [class*='name'], .seller")
        seller_name = clean(await seller_name_el.inner_text() if seller_name_el else "") if seller_el else ""

        # 商家地址
        addr_el = await card.query_selector("[class*='address'], [class*='地址'], .address")
        seller_address = clean(await addr_el.inner_text() if addr_el else "") if addr_el else ""

        # 构建URL
        url = f"https://www.dongchedi.com/usedcar/{listing_id}" if listing_id.isdigit() else page_url

        return Listing(
            listing_id=listing_id,
            title=title,
            model=model,
            battery_plan="电池买断",
            price_wan=price_wan,
            mileage_km=mileage_km,
            city=city,
            seller_type=seller_type,
            seller_name=seller_name,
            seller_address=seller_address,
            url=url,
            fetched_at=now_iso(),
        )
    except Exception as e:
        print(f"[WARN] 解析卡片失败: {e}")
        return None


def extract_listings_from_links(detail_links: list[str], page_text: str = "") -> list[Listing]:
    """从详情链接列表解析 Listing 对象（主要方法）"""
    listings = []
    seen_ids = set()
    for link in detail_links:
        # 跳过非详情页链接（如列表页URL、搜索页URL等）
        if not re.search(r"/usedcar/\d{6,}", link):
            continue
        listing_id = re.search(r"/usedcar/(\d+)", link)
        if not listing_id:
            continue
        lid = listing_id.group(1)
        if lid in seen_ids:
            continue
        seen_ids.add(lid)

        # 尝试从页面文本中提取该 listing 的信息
        price_wan = 0.0
        mileage_km = 0
        city = ""

        # 在页面文本中搜索该 listing_id 附近的结构化数据
        # 格式: "listingId": "23505188", ... "price": "22.59", ... "city": "上海"
        id_pattern = rf'"listingId":\s*"?{lid}"?'
        idx = page_text.find(lid)
        if idx >= 0:
            snippet = page_text[max(0, idx-50):idx+500]
            pm = re.search(r'"?price"?\s*:\s*"?([\d.]+)', snippet)
            if pm:
                price_wan = float(pm.group(1))
            mm = re.search(r'"mileage"\s*:\s*"?([\d.]+)', snippet)
            if mm:
                mileage_km = int(float(mm.group(1)) * 10000)
            cm = re.search(r'"city"\s*:\s*"?([^"]+)', snippet)
            if cm:
                city = cm.group(1).strip()

        listings.append(Listing(
            listing_id=lid,
            price_wan=price_wan,
            mileage_km=mileage_km,
            city=city,
            battery_plan="电池买断",
            url=f"https://www.dongchedi.com/usedcar/{lid}",
            fetched_at=now_iso(),
        ))
    return listings


def extract_listings_from_html_fallback(html: str, page_url: str) -> list[Listing]:
    """从页面HTML/text中解析 listing 列表（备用方法，使用正则找所有listingId）"""
    listings = []
    seen_ids = set()
    # 匹配 "listingId": "22104423" 或 listingId:22104423
    for id_match in re.finditer(r'["\']listingId["\']\s*:\s*"?(\d{6,})"?', html):
        lid = id_match.group(1)
        if lid in seen_ids:
            continue
        seen_ids.add(lid)
        snippet = html[id_match.start():id_match.start()+800]
        pm = re.search(r'["\']price["\']\s*:\s*"?([\d.]+)', snippet)
        mm = re.search(r'["\']mileage["\']\s*:\s*"?([\d.]+)', snippet)
        cm = re.search(r'["\']city["\']\s*:\s*"?([^"\']+)', snippet)
        sm = re.search(r'["\']sellerName["\']\s*:\s*"?([^"\']+)', snippet)
        am = re.search(r'["\']address["\']\s*:\s*"?([^"\']+)', snippet)
        price_wan = float(pm.group(1)) if pm else 0.0
        mileage_km = int(float(mm.group(1)) * 10000) if mm else 0
        city = cm.group(1).strip() if cm else ""
        seller_name = sm.group(1).strip() if sm else ""
        seller_address = am.group(1).strip() if am else ""
        listings.append(Listing(
            listing_id=lid,
            price_wan=price_wan,
            mileage_km=mileage_km,
            city=city,
            seller_name=seller_name,
            seller_address=seller_address,
            battery_plan="电池买断",
            url=f"https://www.dongchedi.com/usedcar/{lid}",
            fetched_at=now_iso(),
        ))
    return listings


async def fetch_with_stealth_browser(url: str, timeout: int = 60000) -> tuple[str, str, list[str]]:
    """
    用 Playwright stealth 模式打开懂车帝页面，返回 (page_text, page_html, listing_links)
    """
    UA = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    async with async_playwright() as p:
        context: BrowserContext = await p.chromium.launch_persistent_context(
            user_data_dir=str(Path.home() / ".dongchedi_playwright_profile"),
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-features=IsolateOrigins,site-per-process",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--window-size=1440,900",
                "--start-maximized",
            ],
            user_agent=UA,
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
            },
        )
        page: Page = context.pages[0] if context.pages else await context.new_page()

        # 注入 stealth JS
        await page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => false });
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                { name: 'Chrome PDF Plugin', description: 'Portable Document Format', filename: 'internal-pdf-viewer' },
                { name: 'Chrome PDF Viewer', description: '', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                { name: 'Native Client', description: '', filename: 'internal-nacl-plugin' }
            ]
        });
        Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN', 'zh', 'en-US', 'en'] });
        window.chrome = { runtime: {} };
        Object.defineProperty(navigator, 'permissions', { get: () => ({ query: (p) => Promise.resolve({ state: 'granted' }) }) });
        // Remove automation flags
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)

        print(f"[INFO] 正在加载: {url}")
        response = await page.goto(url, wait_until="networkidle", timeout=timeout)
        print(f"[INFO] 页面状态: {response.status if response else 'None'}")

        # 等待列表卡片加载
        try:
            await page.wait_for_selector("[class*='car'], [class*='listing'], [class*='item']", timeout=15000)
        except Exception:
            print("[WARN] 未找到车辆列表元素")

        # 滚动加载更多
        for _ in range(3):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)

        # 获取页面文本和HTML
        text = await page.inner_text("body")
        html_content = await page.content()

        # 提取详情链接
        links = await page.evaluate("""
        () => {
            const links = [];
            document.querySelectorAll('a[href*="/usedcar/"]').forEach(a => {
                const href = a.href;
                if (href.match(/\\/usedcar\\/\\d+/) && !href.includes('?')) {
                    links.push(href);
                }
            });
            return [...new Set(links)];
        }
        """)

        await context.close()
        return text, html_content, links


async def fetch_detail_listing(page: Page, url: str) -> Optional[Listing]:
    """抓取并解析单个详情页"""
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        # 价格
        price_text = await page.inner_text("body")
        price_match = re.search(r"(\d+\.?\d*)\s*万", price_text)
        price_wan = float(price_match.group(1)) if price_match else 0.0

        # 里程
        km_match = re.search(r"([\d.]+)\s*[万萬]?\s*公里", price_text)
        mileage_km = int(float(km_match.group(1)) * 10000) if km_match else 0

        # 城市
        city_match = re.search(r"([\\u4e00-\\u9fa5]{2,6})\\s*[市区县]", price_text)
        city = city_match.group(1) + "市" if city_match else ""

        # 卖家地址
        addr_match = re.search(r"[\\u4e00-\\u9fa5a-zA-Z0-9\\s,。、，]{10,50}(?:市|区|县|路|街|号)", price_text)
        seller_address = addr_match.group(0) if addr_match else ""

        # 卖家名称
        seller_match = re.search(r"([\\u4e00-\\u9fa5]{2,20})(?:二手车|车行|车城|展厅|店)", price_text)
        seller_name = seller_match.group(1) if seller_match else ""

        listing_id = url.split("/")[-1].split("?")[0]
        return Listing(
            listing_id=listing_id,
            price_wan=price_wan,
            mileage_km=mileage_km,
            city=city,
            seller_name=seller_name,
            seller_address=seller_address,
            seller_type="商家",
            battery_plan="电池买断",
            url=url,
            fetched_at=now_iso(),
        )
    except Exception as e:
        print(f"[WARN] 详情页失败: {url} :: {e}")
        return None


async def run(url: str, db_path: Path, max_details: int, include_raw_text: bool):
    await init_db(db_path)
    prev = await load_prev(db_path)

    print("[INFO] 使用 Playwright stealth 模式抓取...")
    try:
        page_text, detail_links = await fetch_with_stealth_browser(url)
    except Exception as e:
        print(f"[ERROR] 页面加载失败: {e}")
        # Fallback: 尝试从原始HTML提取
        page_text = ""
        detail_links = []

    curr: dict[str, Listing] = {}

    # 从列表页直接提取（如果浏览器成功）
    if detail_links:
        print(f"[INFO] 发现 {len(detail_links)} 个详情链接")
        for link in detail_links[:max_details]:
            listing_id = link.split("/")[-1].split("?")[0]
            # 从页面文本尝试解析
            item = extract_listings_from_html(page_text, link)
            if item:
                for i in item:
                    if i.listing_id == listing_id:
                        curr[listing_id] = i
                        break
            if listing_id not in curr:
                # 用ID和URL创建基础listing
                curr[listing_id] = Listing(
                    listing_id=listing_id,
                    url=link,
                    battery_plan="电池买断",
                    fetched_at=now_iso(),
                )

    # 如果没找到详情链接，尝试从页面HTML解析
    if not curr:
        print("[INFO] 尝试从页面HTML解析...")
        items = extract_listings_from_html_fallback(page_text, url)
        for item in items:
            curr[item.listing_id] = item
        if items:
            print(f"[INFO] 从HTML解析到 {len(items)} 条数据")

    # 从详情链接提取 listing 信息（优先级最高）
    if detail_links:
        items_from_links = extract_listings_from_links(detail_links, page_text)
        if items_from_links:
            print(f"[INFO] 从链接解析到 {len(items_from_links)} 条数据")
            for item in items_from_links:
                if item.listing_id not in curr or curr[item.listing_id].price_wan == 0:
                    curr[item.listing_id] = item

    # 保存到数据库
    for item in curr.values():
        await upsert_listing(db_path, item)

    # 计算差异
    delta = diff(prev, curr)
    summary = {
        "run_at": now_iso(),
        "list_url": url,
        "matched_count": len(curr),
        "new_count": len(delta["new"]),
        "removed_count": len(delta["removed"]),
        "changed_count": len(delta["changed"]),
        "items": [asdict(x) for x in curr.values()],
        "delta": delta,
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return summary


def main():
    parser = argparse.ArgumentParser(description="懂车帝乐道L90爬虫 - Playwright stealth版本")
    parser.add_argument("--list-url", default=LIST_URL)
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--max-details", type=int, default=30)
    parser.add_argument("--include-raw-text", action="store_true")
    args = parser.parse_args()

    asyncio.run(run(
        url=args.list_url,
        db_path=Path(args.db),
        max_details=args.max_details,
        include_raw_text=args.include_raw_text,
    ))


if __name__ == "__main__":
    main()