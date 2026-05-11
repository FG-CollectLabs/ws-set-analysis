"""
Goldstar Collectibles preorder price scraper.
Source: Reddit u/th8596 (r/WeissSchwarz posts)
"""

import re
import time
from datetime import datetime, timezone
from typing import Optional

import httpx

REDDIT_USER = "th8596"
REDDIT_JSON_URL = f"https://www.reddit.com/user/{REDDIT_USER}/submitted.json"
HEADERS = {"User-Agent": "WSSetAnalysis/1.0 (preorder price research tool)"}
REQUEST_DELAY = 0.5


def fetch_posts(limit: int = 100) -> list[dict]:
    """Fetch submitted posts from u/th8596 via Reddit JSON API."""
    posts = []
    after = None

    while len(posts) < limit:
        params = {"limit": min(100, limit - len(posts)), "sort": "new"}
        if after:
            params["after"] = after

        time.sleep(REQUEST_DELAY)
        resp = httpx.get(REDDIT_JSON_URL, headers=HEADERS, params=params, timeout=15, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json().get("data", {})
        children = data.get("children", [])
        if not children:
            break

        for child in children:
            d = child["data"]
            posts.append({
                "title": d.get("title", ""),
                "selftext": d.get("selftext", ""),
                "url": f"https://reddit.com{d.get('permalink', '')}",
                "created_utc": d.get("created_utc", 0),
                "subreddit": d.get("subreddit", ""),
            })

        after = data.get("after")
        if not after:
            break

    return posts


def _normalize(s: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation for fuzzy matching."""
    s = s.lower()
    s = re.sub(r"[:\-–—!?.,]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# Aliases for fuzzy set name matching
_ALIASES: list[tuple[list[str], str]] = [
    (["oshi no ko", "oshinoko", "oshi noko"], "Oshi no Ko"),
    (["re:zero", "rezero", "re zero"], "Re:Zero"),
    (["nikke", "goddess of victory"], "NIKKE"),
    (["quintessential quintuplets", "quints", "5 toubun", "gotoubun"], "Quintessential Quintuplets"),
    (["bang dream", "bangdream", "bd/w"], "BanG Dream!"),
    (["fujimi", "fujimi bunko", "fujimi vol"], "Fujimi Bunko"),
    (["eminence in shadow", "eminence"], "Eminence in Shadow"),
    (["blue archive"], "Blue Archive"),
    (["umamusume", "uma musume"], "Umamusume"),
    (["frieren"], "Frieren"),
    (["azur lane"], "Azur Lane"),
    (["bocchi", "bocchi the rock"], "Bocchi the Rock"),
    (["dandadan"], "DanDaDan"),
    (["makeine", "too many losing heroines"], "Makeine"),
    (["fairy tail 100", "fairy tail"], "Fairy Tail 100 Years Quest"),
    (["nazarick"], "Nazarick"),
    (["hololive"], "Hololive"),
    (["chainsaw man"], "Chainsaw Man"),
    (["lycoris recoil", "lycoris"], "Lycoris Recoil"),
    (["sword art online", "sao"], "Sword Art Online"),
    (["kono suba", "konosuba"], "KonoSuba"),
    (["ayakashi triangle"], "Ayakashi Triangle"),
]


def _match_ip(text: str) -> Optional[str]:
    t = _normalize(text)
    for aliases, canonical in _ALIASES:
        for alias in aliases:
            if alias in t:
                return canonical
    return None


def _extract_volume(text: str) -> Optional[str]:
    """Try to extract vol/season indicator from text."""
    m = re.search(r"vol\.?\s*(\d+)|v(\d+)\b|season\s*(\d+)|s(\d+)\b", text.lower())
    if m:
        n = m.group(1) or m.group(2) or m.group(3) or m.group(4)
        return f"Vol.{n}"
    return None


def _is_en(text: str) -> bool:
    t = text.lower()
    # Explicitly JP if "japanese weiss" or "jp " without "en" context
    if re.search(r"\bjapanese\s+weiss\b|\bws\s+jp\b|\bjp\s+\w", t):
        return False
    if re.search(r"\benglish\b|\bws\s+en\b|\ben\s+\w", t):
        return True
    # Default ambiguous posts to EN if the post is in r/WeissSchwarz without explicit JP flag
    return True


_PRICE_RE = re.compile(
    r"(extra\s+booster|booster|premium\s+booster)?\s*box\s+\$?([\d,]+\.?\d*)\s*(?:shipped)?(?:\s*/\s*(?:booster\s+)?case\s+\$?([\d,]+\.?\d*)\s*(?:shipped)?)?",
    re.IGNORECASE,
)

# Per-line EN/JP markers — a line is EN if it contains any of these prefixes
_EN_LINE_MARKERS = [
    r"\ben(?:glish)?\s+weiss", r"\bws\s+en\b", r"\benglish\b", r"\ben\s+\w",
]
_JP_LINE_MARKERS = [
    r"\bjapanese\s+weiss", r"\bws\s+jp\b", r"\bjapanese\b", r"\bjp\s+\w",
]
_EN_LINE_RE = re.compile("|".join(_EN_LINE_MARKERS), re.IGNORECASE)
_JP_LINE_RE = re.compile("|".join(_JP_LINE_MARKERS), re.IGNORECASE)


def _line_language(line: str, post_default_en: bool) -> Optional[str]:
    """Return 'EN', 'JP', or None (unknown) for a single line."""
    if _JP_LINE_RE.search(line):
        return "JP"
    if _EN_LINE_RE.search(line):
        return "EN"
    return "EN" if post_default_en else None


def _parse_lines(title: str, body: str) -> list[dict]:
    """
    Parse price records at line granularity so mixed JP+EN posts are handled correctly.
    Each record includes: ip, volume, language, box_price_usd, case_price_usd, product_type.
    """
    # Determine the post's default language from title
    post_en = not bool(_JP_LINE_RE.search(title)) or bool(_EN_LINE_RE.search(title))

    records = []
    lines = (title + "\n" + body).split("\n")
    # Use a small sliding window: look at current line ±2 for set name + language context
    for i, line in enumerate(lines):
        m = _PRICE_RE.search(line)
        if not m or not m.group(2):
            continue

        # Determine language from this line and surrounding context
        context = " ".join(lines[max(0, i - 2): i + 3])
        lang = _line_language(context, post_en)
        if lang is None:
            continue

        ip = _match_ip(context)
        vol = _extract_volume(context)
        product_type = "extra_booster" if m.group(1) and "extra" in m.group(1).lower() else "booster"
        box_price = float(m.group(2).replace(",", ""))
        case_price = float(m.group(3).replace(",", "")) if m.group(3) else None

        # Skip implausibly low prices (probably not WS boxes)
        if box_price < 10:
            continue

        records.append({
            "ip": ip,
            "volume": vol,
            "language": lang,
            "box_price_usd": box_price,
            "case_price_usd": case_price,
            "product_type": product_type,
        })

    return records


def parse_all_prices(posts: list[dict]) -> list[dict]:
    """
    Parse all WS preorder pricing from a list of Reddit posts.
    Returns a flat list of price records, most recent first.
    """
    records = []
    for post in posts:
        for rec in _parse_lines(post["title"], post["selftext"]):
            records.append({
                **rec,
                "title": post["title"],
                "post_url": post["url"],
                "post_date": datetime.fromtimestamp(post["created_utc"], tz=timezone.utc).date().isoformat(),
                "subreddit": post["subreddit"],
            })
    return records


def find_preorder_price(
    set_name: str,
    volume: Optional[str] = None,
    language: str = "EN",
    prefer: str = "newest",
) -> dict:
    """
    Find Goldstar preorder price for a given set.

    Args:
        set_name: Set or IP name, e.g. 'Oshi no Ko Vol.2'
        volume: Optional volume qualifier, e.g. 'Vol.2'
        language: 'EN' or 'JP'
        prefer: 'newest' (most recent post) or 'oldest' (original preorder, best for historical cost basis)
    """
    posts = fetch_posts(limit=100)
    records = parse_all_prices(posts)

    # Extract volume from set_name if not provided separately
    if not volume:
        volume = _extract_volume(set_name)

    ip_target = _match_ip(set_name)
    set_name_norm = _normalize(set_name)

    candidates = []
    for r in records:
        if r["language"] != language:
            continue

        # Language-matched records need IP match
        if ip_target and r["ip"] != ip_target:
            continue
        if not ip_target and set_name_norm not in _normalize(r["title"]):
            continue

        # Volume match: if a volume is specified, the post must mention that volume
        if volume:
            vol_norm = _normalize(volume)  # e.g. "vol 2"
            title_norm = _normalize(r["title"])
            # Accept if post title contains the volume token
            if vol_norm not in title_norm:
                # Also accept if record's extracted volume matches
                if not r["volume"] or _normalize(r["volume"]) != vol_norm:
                    continue

        candidates.append(r)

    if not candidates:
        return {"found": False, "set_name": set_name, "volume": volume}

    chosen = candidates[0] if prefer == "newest" else candidates[-1]
    return {
        "found": True,
        "set_name": set_name,
        "ip": chosen["ip"],
        "volume": chosen["volume"],
        "language": chosen["language"],
        "box_price_usd": chosen["box_price_usd"],
        "case_price_usd": chosen["case_price_usd"],
        "product_type": chosen["product_type"],
        "post_url": chosen["post_url"],
        "post_date": chosen["post_date"],
        "source": f"Goldstar Collectibles (u/{REDDIT_USER})",
    }


def list_recent_en_preorders(limit: int = 50) -> list[dict]:
    """List recent EN WS preorder prices from Goldstar, deduplicated by (ip, volume, product_type)."""
    posts = fetch_posts(limit=100)
    records = parse_all_prices(posts)
    en = [r for r in records if r["language"] == "EN"]
    seen: set = set()
    deduped = []
    for r in en:
        key = (r["ip"], r["volume"], r["product_type"])
        if key not in seen:
            seen.add(key)
            deduped.append(r)
        if len(deduped) >= limit:
            break
    return deduped
