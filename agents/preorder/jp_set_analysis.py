"""JP set analysis using Yuyutei data."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib import yuyutei

JPY_TO_USD = 0.0067  # approximate — update as needed


def analyze_jp_sets(jp_equivalent_sets: list[dict], expected_en_preorder_usd: float = 90.0) -> dict:
    """
    Analyze JP equivalent sets. For each, fetch from Yuyutei using the Bushiroad set code.
    Focus extra analysis on the current JP set (is_current_jp_set=True).
    """
    results = []
    current_set_analysis = None

    for jp_set in jp_equivalent_sets:
        set_code = jp_set.get("set_code")
        is_current = jp_set.get("is_current_jp_set", False)

        entry = {
            "name": jp_set["name"],
            "set_code": set_code,
            "jp_release_date": jp_set.get("jp_release_date"),
            "is_current": is_current,
        }

        if set_code:
            try:
                summary = yuyutei.get_set_summary(set_code)
                entry["summary"] = summary
                entry["box_ev_jpy"] = summary.get("estimated_box_ev_jpy")
                entry["box_ev_usd"] = (
                    round(summary["estimated_box_ev_jpy"] * JPY_TO_USD, 2)
                    if summary.get("estimated_box_ev_jpy")
                    else None
                )
                entry["total_cards"] = summary.get("total_cards", 0)
                entry["sp_stats"] = _extract_sp_stats(summary, JPY_TO_USD)
            except Exception as e:
                entry["summary_error"] = str(e)
        else:
            entry["note"] = "No set code configured"

        results.append(entry)
        if is_current:
            current_set_analysis = entry

    # EV signal for the current JP set vs expected EN preorder
    ev_signal = None
    if current_set_analysis and current_set_analysis.get("box_ev_usd"):
        ev_usd = current_set_analysis["box_ev_usd"]
        diff = ev_usd - expected_en_preorder_usd
        if diff > 20:
            ev_signal = {
                "rating": "positive",
                "description": f"JP box EV ${ev_usd:.0f} is ${diff:.0f} above expected EN preorder (${expected_en_preorder_usd:.0f}). Strong EV signal.",
            }
        elif diff > 0:
            ev_signal = {
                "rating": "neutral",
                "description": f"JP box EV ${ev_usd:.0f} slightly above expected EN preorder. Modest EV signal.",
            }
        elif diff > -20:
            ev_signal = {
                "rating": "caution",
                "description": f"JP box EV ${ev_usd:.0f} is below expected EN preorder by ${abs(diff):.0f}. Weak EV signal.",
            }
        else:
            ev_signal = {
                "rating": "negative",
                "description": f"JP box EV ${ev_usd:.0f} is significantly below expected EN preorder. EV does not support preorder.",
            }

    return {
        "sets": results,
        "current_jp_set": current_set_analysis,
        "expected_en_preorder_usd": expected_en_preorder_usd,
        "ev_signal": ev_signal,
        "jpy_to_usd_rate": JPY_TO_USD,
        "note": "EV uses heuristic pull rates based on rarity tier. Signed cards (AGR-equivalent) excluded.",
    }


def _extract_sp_stats(summary: dict, jpy_to_usd: float) -> dict:
    """
    From a Yuyutei set summary, extract EX-rarity (EN-eligible SP/SSP) stats.
    EX = non-signed SP/SSP in Yuyutei terminology — the main pull targets that appear in EN.
    """
    rarity_breakdown = summary.get("rarity_breakdown", [])
    ex_entry = next((r for r in rarity_breakdown if r["rarity"] == "EX"), None)

    if not ex_entry:
        return {"available": False, "note": "No EX rarity found in set"}

    avg_jpy = ex_entry.get("avg_sell_price_jpy", 0)
    count = ex_entry.get("card_count", 0)

    # Top EX cards from the full top-10 list
    top10 = summary.get("top_10_by_price", [])
    ex_cards = [c for c in top10 if c.get("rarity") == "EX"]

    return {
        "available": True,
        "card_count": count,
        "avg_price_jpy": avg_jpy,
        "avg_price_usd": round(avg_jpy * jpy_to_usd, 2),
        "top_ex_cards": ex_cards[:3],
    }
