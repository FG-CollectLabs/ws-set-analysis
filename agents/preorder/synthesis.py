"""Synthesize IP strength, EN history, JP EV, and competitive standing into a recommendation."""


TIER_SCORES = {"Strong": 3, "Moderate": 2, "Niche": 1}
COMP_SCORES = {"high": 2, "moderate": 1, "low": 0, "niche": 0}


def synthesize(
    ip_data: dict,
    en_history: dict,
    jp_analysis: dict,
    competitive_standing: str,
    simultaneous_release: bool = False,
) -> dict:
    """
    Apply V1 heuristic scoring to produce a recommendation.

    Scoring dimensions (each 0-3):
      1. IP tier:       Strong=3, Moderate=2, Niche=1
      2. EN trend:      appreciating=3, stable=2, mild_dip=1, significant_dip=0, unknown=1
      3. JP EV signal:  positive=2, neutral=1, caution=0, negative=-1
      4. Competitive:   high=2, moderate=1, low/niche=0

    Total → recommendation:
      8-9:  strong-buy
      6-7:  buy
      4-5:  wait-for-dip
      0-3:  pass
    """
    ip_tier = ip_data.get("tier", "Niche")
    ip_score = TIER_SCORES.get(ip_tier, 1)

    trend = en_history.get("trend", {})
    trend_pattern = trend.get("pattern", "unknown")
    trend_scores = {
        "appreciating": 3,
        "stable": 2,
        "mild_dip": 1,
        "significant_dip": 0,
        "unknown": 1,
    }
    trend_score = trend_scores.get(trend_pattern, 1)

    ev_signal = jp_analysis.get("ev_signal") or {}
    if simultaneous_release:
        # JP and EN release at the same time — JP pricing has no predictive value
        ev_rating = "simultaneous"
        ev_score = 1  # neutral default; no signal either way
        ev_description = "EN and JP release simultaneously — JP market prices cannot be used as a forward indicator."
    else:
        ev_rating = ev_signal.get("rating", "neutral")
        ev_scores = {"positive": 2, "neutral": 1, "caution": 0, "negative": -1}
        ev_score = ev_scores.get(ev_rating, 1)
        ev_description = ev_signal.get("description", "")

    comp_score = COMP_SCORES.get(competitive_standing.lower(), 0)

    total = ip_score + trend_score + ev_score + comp_score

    if total >= 8:
        recommendation = "strong-buy"
        summary = "Multiple strong positive signals across IP strength, EN history, JP EV, and competitive standing. Preorder confidently."
    elif total >= 6:
        recommendation = "buy"
        summary = "Solid signals overall. Preorder is reasonable. Minor risk factors present but not deal-breakers."
    elif total >= 4:
        recommendation = "wait-for-dip"
        summary = "Mixed signals. Historical EN performance suggests a post-release dip is likely. Wait 30–60 days after release for a better entry price."
    else:
        recommendation = "pass"
        summary = "Weak IP signals, unfavorable EN trend, or poor JP EV. Not worth the preorder risk at current expected pricing."

    return {
        "recommendation": recommendation,
        "summary": summary,
        "total_score": total,
        "max_score": 10,
        "score_breakdown": {
            "ip_tier": {"score": ip_score, "tier": ip_tier, "reason": ip_data.get("tier_reason")},
            "en_trend": {"score": trend_score, "pattern": trend_pattern, "description": trend.get("description")},
            "jp_ev": {"score": ev_score, "rating": ev_rating, "description": ev_description},
            "competitive": {"score": comp_score, "standing": competitive_standing},
        },
    }
