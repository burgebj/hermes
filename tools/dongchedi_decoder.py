"""
懂车帝 icon font decoder & auxiliary data extractor.
懂车帝 uses a custom icon font (PUA codepoints) to render digits.
This module extracts structured data from __NEXT_DATA__ and the
HTML meta description, which contain clean text without icon font issues.
"""

import json
import re
from typing import Optional


def extract_next_data(html: str) -> Optional[dict]:
    """Extract __NEXT_DATA__ JSON from page HTML."""
    m = re.search(
        r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        html, re.DOTALL
    )
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except json.JSONDecodeError:
        return None


def extract_car_info(html: str) -> Optional[dict]:
    """Extract car_info dict from __NEXT_DATA__ skuDetail."""
    nd = extract_next_data(html)
    if nd is None:
        return None
    try:
        return nd["props"]["pageProps"]["skuDetail"]["car_info"]
    except (KeyError, TypeError):
        return None


def extract_sku_list(html: str) -> Optional[dict]:
    """Extract skuList from __NEXT_DATA__ (list page)."""
    nd = extract_next_data(html)
    if nd is None:
        return None
    try:
        return nd["props"]["pageProps"]["skuList"]
    except (KeyError, TypeError):
        return None


def get_pagination_info(html: str) -> dict:
    """Extract pagination info from __NEXT_DATA__ skuList."""
    sl = extract_sku_list(html)
    if not sl:
        return {"total": 0, "page": 1, "page_size": 20, "total_page": 1}
    return {
        "total": sl.get("total", 0),
        "page": sl.get("page", 1),
        "page_size": sl.get("page_size", 20),
        "total_page": sl.get("total_page", 1),
    }


def extract_mileage_from_meta(html: str) -> Optional[int]:
    """Extract mileage in km from HTML meta description tag (clean text)."""
    m = re.search(
        r'<meta[^>]*name="description"[^>]*content="([^"]*)"',
        html, re.I
    )
    if not m:
        return None
    desc = m.group(1)
    mm = re.search(r'行驶里程[:：]\s*([0-9]+(?:\.[0-9]+)?)\s*万', desc)
    if mm:
        return int(float(mm.group(1)) * 10000)
    mm = re.search(r'行驶里程[:：]\s*([0-9]+)\s*公里', desc)
    if mm:
        return int(mm.group(1))
    return None


def extract_price_from_text(markdown: str) -> Optional[float]:
    """Extract price by computing guide_price - save_price (plain text)."""
    gp = re.search(r"新车指导价[：:]\s*([0-9]+(?:\.[0-9]+)?)万", markdown)
    sp = re.search(r"比新车省[：:]\s*([0-9]+(?:\.[0-9]+)?)万", markdown)
    if gp and sp:
        return round(float(gp.group(1)) - float(sp.group(1)), 2)
    return None
