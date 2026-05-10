import asyncio
import re
import sys
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

async def get_box_price(set_name: str) -> dict:
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
        )
        await ctx.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        page = await ctx.new_page()
        query = f"{set_name} booster box sealed"
        url = f"https://www.tcgplayer.com/search/weiss-schwarz/product?q={query.replace(' ', '+')}&productLineName=weiss-schwarz"
        await page.goto(url, timeout=30000, wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)

        # Get product card elements
        content = await page.content()
        body = await page.evaluate("() => document.body.innerText")
        lines = [l.strip() for l in body.split('\n') if l.strip()]
        print("All lines with prices or product names:")
        for line in lines:
            if '$' in line or 'Booster' in line or 'Vol' in line or 'box' in line.lower():
                print(repr(line[:120]))

        await browser.close()

asyncio.run(get_box_price("Re:Zero Vol.1"))
