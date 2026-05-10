"""Yuyutei JP Weiss Schwarz card price scraper.

URL pattern:
  Title page:  https://yuyu-tei.jp/sell/ws/s/<title_slug>
  Set search:  https://yuyu-tei.jp/sell/ws/s/search?search_word=<set_code>
  Card detail: https://yuyu-tei.jp/sell/ws/card/<title_slug>/<internal_id>

Title slugs for common IPs (discovered empirically):
  Re:Zero   = rz
  SAO       = sao
  (others discovered via /top/ws links)

Yuyutei rarity codes vs Bushiroad:
  Yuyutei SP  = signed SP (Bushiroad AGR) — EXCLUDED from EN EV
  Yuyutei EX  = non-signed SP/SSP — EN-eligible, main pull targets
  Yuyutei A   = ultra-rare autograph — EXCLUDED
  Yuyutei R   = standard Rare
  Yuyutei S   = Common/Uncommon
  Yuyutei PR  = Promo (P-series with no rarity suffix)
"""

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# Rarities to exclude from EN EV — signed cards that never appear in English prints
# Yuyutei "SP" (signed SP) and "A" (ultra-rare autograph) are both AGR-equivalent
EXCLUDED_RARITIES = {"SP", "A"}

CACHE_DIR = Path(__file__).parent.parent / "seed-data" / "jp-sets"
CACHE_TTL_HOURS = 24

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
}

BASE = "https://yuyu-tei.jp"

# Known title slug mappings for WS IPs (add more as discovered)
TITLE_SLUGS = {
    "rz": "Re:Zero",
    "sao": "Sword Art Online",
    "rsab": "Rascal Does Not Dream",
}


def _cache_path(set_code: str) -> Path:
    slug = re.sub(r"[^a-zA-Z0-9_-]", "_", set_code)
    return CACHE_DIR / f"{slug}.json"


def _load_cache(set_code: str) -> dict | None:
    path = _cache_path(set_code)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    cached_at = datetime.fromisoformat(data.get("cached_at", "2000-01-01T00:00:00+00:00"))
    age_hours = (datetime.now(timezone.utc) - cached_at).total_seconds() / 3600
    if age_hours > CACHE_TTL_HOURS:
        return None
    return data


def _save_cache(set_code: str, data: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    data["cached_at"] = datetime.now(timezone.utc).isoformat()
    _cache_path(set_code).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _fetch_html(url: str, params: dict | None = None) -> BeautifulSoup:
    time.sleep(0.5)
    resp = requests.get(url, headers=HEADERS, params=params, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def _parse_rarity(card_no: str, name: str) -> str:
    """
    Extract rarity from card number.
    Examples:
      RZ/S116-026SP → SP
      RZ/S116-098EX → EX
      RZ/S116-P09EX → EX
      RZ/S116-029S  → S
      RZ/S116-098R  → R
      RZ/S116-P10   → PR (promo with no rarity suffix)
    """
    # Match the trailing uppercase letters (1-3 chars)
    m = re.search(r"([A-Z]{1,3})$", card_no)
    if m:
        rarity = m.group(1)
        # "P" alone at the end of card number means promo with no explicit rarity
        if rarity == "P":
            return "PR"
        return rarity
    # Card number ends with a digit (promo format)
    if re.search(r"\d$", card_no):
        return "PR"
    return "?"


def _parse_cards_from_page(soup: BeautifulSoup) -> list[dict]:
    """Parse all .card-product elements from a Yuyutei listing page."""
    cards = []
    for item in soup.select(".card-product"):
        img = item.find("img", class_="card")
        alt = img.get("alt", "") if img else ""

        span = item.find("span", class_="d-block")
        card_no = span.get_text(strip=True) if span else ""

        h4 = item.find("h4")
        name = h4.get_text(strip=True) if h4 else ""

        strong = item.find("strong")
        price_text = strong.get_text(strip=True) if strong else ""
        price_digits = re.sub(r"[^\d]", "", price_text)
        price_jpy = int(price_digits) if price_digits else None

        is_sold_out = "sold-out" in item.get("class", [])
        is_signed = "サイン入り" in name or "サイン" in name

        rarity = _parse_rarity(card_no, name)

        # Cards with is_signed but rarity EX are still EN-eligible alternate art
        # Cards with is_signed AND rarity SP are the autographs (AGR-equivalent)
        excluded = (rarity in EXCLUDED_RARITIES) or is_signed

        cards.append({
            "card_no": card_no,
            "name": name,
            "rarity": rarity,
            "sell_price_jpy": price_jpy,
            "is_signed": is_signed,
            "is_sold_out": is_sold_out,
            "excluded_from_ev": excluded,
        })
    return cards


def get_set_cards(set_code: str) -> list[dict]:
    """
    Fetch all cards for a WS set by Bushiroad set code (e.g., 'RZ/S116').
    Uses 24h file cache. Results written to seed-data/jp-sets/<slug>.json.
    """
    cached = _load_cache(set_code)
    if cached and "cards" in cached:
        return cached["cards"]

    soup = _fetch_html(f"{BASE}/sell/ws/s/search", params={"search_word": set_code})
    cards = _parse_cards_from_page(soup)

    _save_cache(set_code, {"set_code": set_code, "cards": cards})
    return cards


def get_set_summary(set_code: str) -> dict:
    """
    Compute set EV summary for a JP WS set.
    Signed / AGR rarities are excluded from EV.
    Pull rates are heuristic — WS Vol.3 JP standard box = 8 packs, 8 cards each.
    """
    cards = get_set_cards(set_code)
    if not cards:
        return {"set_code": set_code, "error": "no cards found", "total_cards": 0}

    from collections import defaultdict
    by_rarity: dict[str, list] = defaultdict(list)
    for card in cards:
        by_rarity[card["rarity"]].append(card)

    rarity_summary = []
    total_ev = 0.0

    for rarity, rarity_cards in sorted(by_rarity.items()):
        prices = [c["sell_price_jpy"] for c in rarity_cards if c.get("sell_price_jpy")]
        avg_price = sum(prices) / len(prices) if prices else 0
        excluded = all(c["excluded_from_ev"] for c in rarity_cards)

        pull_rate = _estimate_pull_rate(rarity, len(rarity_cards))
        ev = (pull_rate * avg_price) if not excluded else 0.0
        total_ev += ev

        rarity_summary.append({
            "rarity": rarity,
            "card_count": len(rarity_cards),
            "avg_sell_price_jpy": round(avg_price),
            "estimated_pull_rate_per_box": pull_rate,
            "ev_contribution_jpy": round(ev),
            "excluded_from_ev": excluded,
            "exclusion_reason": "Signed/autograph — does not appear in EN prints" if excluded else None,
        })

    top_cards = sorted(
        [c for c in cards if not c["excluded_from_ev"] and c.get("sell_price_jpy")],
        key=lambda c: c["sell_price_jpy"],
        reverse=True,
    )[:10]

    return {
        "set_code": set_code,
        "total_cards": len(cards),
        "rarity_breakdown": rarity_summary,
        "top_10_by_price": top_cards,
        "estimated_box_ev_jpy": round(total_ev),
        "excluded_categories": ["Signed SP (AGR-equivalent)", "Ultra-rare autograph (A rarity)"],
        "note": "EV uses heuristic pull rates. Signed cards (SP, A rarities) excluded as they do not appear in EN prints.",
    }


def search_set(query: str) -> list[dict]:
    """
    Search Yuyutei for WS set pages matching a query.
    Returns list of {title_slug, name, url} from the WS top page navigation.
    """
    soup = _fetch_html(f"{BASE}/top/ws")
    results = []
    query_lower = query.lower()
    for a in soup.select("a[href*='/sell/ws/s/']"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if query_lower in text.lower() or query_lower in href.lower():
            slug_match = re.search(r"/sell/ws/s/([^#?/]+)", href)
            if slug_match:
                results.append({
                    "title_slug": slug_match.group(1),
                    "name": text,
                    "url": href,
                })
    return results


def _estimate_pull_rate(rarity: str, card_count: int) -> float:
    """
    Heuristic expected pulls per box for each Yuyutei rarity.
    WS standard box: 8 packs × 8 cards = 64 cards.
    EX = non-signed SP/SSP: guaranteed 1 per box divided among EX cards.
    """
    rates = {
        "EX": 1.0,   # non-signed SP/SSP — 1 guaranteed per box
        "R":  4.0,   # rares
        "S":  16.0,  # commons/uncommons
        "PR": 0.0,   # promos — not in retail packs
        "SP": 0.0,   # signed — excluded
        "A":  0.0,   # ultra-rare autograph — excluded
    }
    base = rates.get(rarity.upper(), 0.5)
    if card_count > 0 and base > 0:
        return round(base / card_count, 4)
    return 0.0
