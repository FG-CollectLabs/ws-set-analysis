"""EN historical set performance analysis."""

import json
import sys
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib import ws_prices

ROOT = Path(__file__).parent.parent.parent

# TCGPlayer seller fee (10.25%) + payment processing (1.5%) = 11.75%
TCGPLAYER_FEE_RATE = 0.1175


def analyze_en_history(en_historical_sets: list[dict]) -> dict:
    """
    For each prior EN set, load seed data and fetch current box price.
    Returns structured history with price change % and trend assessment.
    Only compares standard boosters for trend; extra boosters noted separately.
    """
    results = []
    standard_boosters = []

    for set_cfg in en_historical_sets:
        seed_path = ROOT / set_cfg["seed"]
        if not seed_path.exists():
            results.append({"name": set_cfg["name"], "error": f"seed file not found: {seed_path}"})
            continue

        seed = json.loads(seed_path.read_text(encoding="utf-8"))
        preorder_price = seed.get("preorder_price_usd")
        release_date_str = seed.get("release_date")
        product_type = seed.get("product_type", "booster")

        # Days elapsed since release
        days_elapsed = None
        if release_date_str:
            release_dt = datetime.strptime(release_date_str, "%Y-%m-%d").date()
            days_elapsed = (date.today() - release_dt).days

        # Current box price from TCGPlayer
        box_result = None
        current_price = None
        tcgplayer_url = None
        try:
            box_result = ws_prices.get_box_price(set_cfg["name"])
            top = box_result.get("top")
            tcgplayer_url = box_result.get("search_url")
            if top:
                current_price = top.get("market_price_usd")
        except Exception as e:
            box_result = {"error": str(e)}

        # Price change, ROI, and annualized XIRR
        price_change_pct = None
        roi_pct = None
        post_fee_roi_pct = None
        post_fee_xirr_pct = None
        if preorder_price and current_price:
            price_change_pct = round(((current_price - preorder_price) / preorder_price) * 100, 1)
            roi_pct = price_change_pct
            net_after_fees = current_price * (1 - TCGPLAYER_FEE_RATE)
            post_fee_roi_pct = round(((net_after_fees - preorder_price) / preorder_price) * 100, 1)
            if days_elapsed and days_elapsed > 0:
                years = days_elapsed / 365.25
                post_fee_xirr_pct = round(((net_after_fees / preorder_price) ** (1 / years) - 1) * 100, 1)

        # SP pull rate for quick reference
        sp_rate = next(
            (pr for pr in seed.get("pull_rates", []) if pr["rarity"] == "SP"), None
        )

        entry = {
            "name": set_cfg["name"],
            "slug": set_cfg["slug"],
            "set_code": set_cfg.get("set_code"),
            "product_type": product_type,
            "release_date": release_date_str,
            "days_elapsed": days_elapsed,
            "preorder_price_usd": preorder_price,
            "current_box_price_usd": current_price,
            "tcgplayer_url": tcgplayer_url,
            "price_change_pct": price_change_pct,
            "roi_pct": roi_pct,
            "post_fee_roi_pct": post_fee_roi_pct,
            "post_fee_xirr_pct": post_fee_xirr_pct,
            "sp_rate": sp_rate,
            "pull_rates": seed.get("pull_rates", []),
            "competitive_standing": seed.get("competitive_standing"),
            "box_price_lookup": box_result,
            "data_confidence": seed.get("data_confidence", "unknown"),
        }
        results.append(entry)
        if product_type == "booster":
            standard_boosters.append(entry)

    trend = _assess_trend(standard_boosters)

    return {
        "sets": results,
        "standard_booster_count": len(standard_boosters),
        "trend": trend,
    }


def _assess_trend(standard_boosters: list[dict]) -> dict:
    """
    Assess the price trend across standard booster sets.
    Returns: pattern name, description, dip_depth_pct (worst observed), recovery observed.
    """
    changes = [s["price_change_pct"] for s in standard_boosters if s.get("price_change_pct") is not None]

    if not changes:
        return {
            "pattern": "unknown",
            "description": "Insufficient price data to assess trend.",
            "avg_change_pct": None,
            "min_change_pct": None,
        }

    avg = round(sum(changes) / len(changes), 1)
    min_chg = round(min(changes), 1)

    if avg >= 10:
        pattern = "appreciating"
        desc = f"Prior EN sets average +{avg}% vs preorder. Strong appreciation — demand holds post-release."
    elif avg >= -10:
        pattern = "stable"
        desc = f"Prior EN sets average {avg:+}% vs preorder. Relatively stable — minimal dip risk."
    elif avg >= -25:
        pattern = "mild_dip"
        desc = f"Prior EN sets average {avg:+}% vs preorder. Moderate dip — waiting 30–60 days post-release typically yields a better entry."
    else:
        pattern = "significant_dip"
        desc = f"Prior EN sets average {avg:+}% vs preorder. Significant depreciation — wait for market stabilization."

    return {
        "pattern": pattern,
        "description": desc,
        "avg_change_pct": avg,
        "min_change_pct": min_chg,
        "data_points": len(changes),
    }
