"""English WS card and sealed product price scraper via TCGPlayer (Playwright)."""

import asyncio
import re
import time
from typing import Optional

from playwright.async_api import async_playwright, Browser

_browser: Optional[Browser] = None


async def _get_browser() -> Browser:
    global _browser
    if _browser is None or not _browser.is_connected():
        p = await async_playwright().start()
        _browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
    return _browser


async def _fetch_page_text(url: str, wait_ms: int = 6000) -> str:
    browser = await _get_browser()
    ctx = await browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        locale="en-US",
    )
    await ctx.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    page = await ctx.new_page()
    await page.goto(url, timeout=30000, wait_until="domcontentloaded")
    await page.wait_for_timeout(wait_ms)
    text = await page.evaluate("() => document.body.innerText")
    await ctx.close()
    return text


def _run(coro):
    """Run a coroutine from sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _parse_price(text: str) -> float | None:
    text = text.strip().replace(",", "")
    m = re.search(r"\$?([\d]+\.[\d]{2})", text)
    return float(m.group(1)) if m else None


def _search_tcgplayer(query: str) -> str:
    url = (
        "https://www.tcgplayer.com/search/weiss-schwarz/product"
        f"?q={query.replace(' ', '+')}&productLineName=weiss-schwarz"
    )
    return _run(_fetch_page_text(url))


def get_box_price(set_name: str) -> dict:
    """Return current sealed booster box market price from TCGPlayer."""
    try:
        text = _search_tcgplayer(f"{set_name} booster box sealed")
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        results = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Look for "Booster Box" lines
            if "Booster Box" in line and "Case" not in line:
                product_name = line
                market_price = None
                list_price = None
                # Scan next few lines for prices
                for j in range(i + 1, min(i + 5, len(lines))):
                    if "Market Price:" in lines[j]:
                        market_price = _parse_price(lines[j].replace("Market Price:", ""))
                    elif lines[j].startswith("$"):
                        if list_price is None:
                            list_price = _parse_price(lines[j])
                if market_price or list_price:
                    results.append({
                        "title": product_name,
                        "market_price_usd": market_price or list_price,
                        "list_price_usd": list_price,
                    })
            i += 1

        # Find the best match for the set_name
        set_lower = set_name.lower()
        best = None
        for r in results:
            if set_lower.split("vol")[0].strip() in r["title"].lower() or set_lower in r["title"].lower():
                best = r
                break
        if best is None and results:
            best = results[0]

        return {
            "set_name": set_name,
            "results": results[:5],
            "top": best,
        }
    except Exception as e:
        return {"set_name": set_name, "results": [], "top": None, "error": str(e)}


def get_set_summary(set_name: str) -> dict:
    """Get top singles and SP/SSP averages for an EN WS set from TCGPlayer."""
    try:
        text = _search_tcgplayer(f"{set_name} singles cards")
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        cards = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if "Market Price:" in line:
                price = _parse_price(line.replace("Market Price:", ""))
                if price and i > 0:
                    title = lines[i - 1] if not lines[i - 1].startswith("$") else (lines[i - 2] if i >= 2 else "")
                    if title and not any(w in title for w in ["Booster Box", "Case", "Deck"]):
                        cards.append({"title": title, "market_price_usd": price})
            i += 1

        cards.sort(key=lambda c: c["market_price_usd"], reverse=True)
        sp_cards = [c for c in cards if "SP" in c["title"]]
        ssp_cards = [c for c in cards if "SSP" in c["title"]]

        return {
            "set_name": set_name,
            "top_10_by_price": cards[:10],
            "sp_average_usd": (
                round(sum(c["market_price_usd"] for c in sp_cards) / len(sp_cards), 2)
                if sp_cards else None
            ),
            "ssp_average_usd": (
                round(sum(c["market_price_usd"] for c in ssp_cards) / len(ssp_cards), 2)
                if ssp_cards else None
            ),
        }
    except Exception as e:
        return {"set_name": set_name, "top_10_by_price": [], "error": str(e)}


def get_card_price(card_name: str, set_name: str) -> dict:
    try:
        text = _search_tcgplayer(f"{card_name} {set_name}")
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for i, line in enumerate(lines):
            if card_name.lower() in line.lower() and i + 2 < len(lines):
                price = None
                for j in range(i + 1, min(i + 4, len(lines))):
                    if "Market Price:" in lines[j]:
                        price = _parse_price(lines[j].replace("Market Price:", ""))
                        break
                return {"card_name": card_name, "set_name": set_name, "title": line, "market_price_usd": price}
        return {"card_name": card_name, "set_name": set_name, "market_price_usd": None, "note": "not found"}
    except Exception as e:
        return {"card_name": card_name, "set_name": set_name, "error": str(e)}
