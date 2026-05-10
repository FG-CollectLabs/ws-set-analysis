"""Generate a Hugo-compatible markdown post from structured analysis data."""

from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent

RECOMMENDATION_LABELS = {
    "strong-buy": "STRONG BUY",
    "buy": "BUY",
    "wait-for-dip": "WAIT FOR DIP",
    "pass": "PASS",
}

RECOMMENDATION_BADGES = {
    "strong-buy": "🟢 STRONG BUY",
    "buy": "🔵 BUY",
    "wait-for-dip": "🟡 WAIT FOR DIP",
    "pass": "🔴 PASS",
}


def generate_post(
    set_config: dict,
    ip_data: dict,
    en_history: dict,
    jp_analysis: dict,
    synthesis: dict,
    stage: str = "preorder",
) -> str:
    """Render a complete Hugo markdown post and write it to blog/content/sets/<slug>/<stage>.md"""
    slug = set_config["set_slug"]
    rec = synthesis["recommendation"]
    label = RECOMMENDATION_LABELS.get(rec, rec.upper())
    badge = RECOMMENDATION_BADGES.get(rec, rec.upper())
    today = date.today().isoformat()

    # Build front matter
    front_matter = f"""---
title: "{set_config['set_name']} — Preorder Analysis"
date: {today}
set_name: "{set_config['set_name']}"
set_slug: "{slug}"
ip: "{set_config['ip_name']}"
stage: "{stage}"
recommendation: "{rec}"
analyst: "claude-agent"
draft: false
summary: "{synthesis['summary']}"
---"""

    # Build sections
    sections = [
        front_matter,
        _tl_dr(synthesis, set_config),
        _ip_strength_section(ip_data, set_config),
        _en_history_section(en_history),
        _jp_section(jp_analysis, set_config),
        _competitive_section(set_config, synthesis),
        _series_outlook_section(set_config),
        _recommendation_section(synthesis, badge),
        _data_sources_section(set_config, today),
    ]

    content = "\n\n".join(s for s in sections if s)

    # Write to blog
    output_dir = ROOT / "blog" / "content" / "sets" / slug
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{stage}.md"
    output_path.write_text(content, encoding="utf-8")

    return str(output_path)


def _tl_dr(synthesis: dict, set_config: dict) -> str:
    rec = synthesis["recommendation"]
    badge = RECOMMENDATION_BADGES.get(rec, rec.upper())
    score = synthesis["total_score"]
    max_score = synthesis["max_score"]
    en_est = set_config.get("expected_en_preorder_price_usd", 90)
    en_date = set_config.get("en_release_date_estimate", "TBD")

    return f"""## TL;DR — {badge}

**Score:** {score}/{max_score} &nbsp;|&nbsp; **Expected EN preorder:** ~${en_est:.0f} &nbsp;|&nbsp; **Estimated EN release:** {en_date}

{synthesis['summary']}"""


def _ip_strength_section(ip_data: dict, set_config: dict) -> str:
    anime = ip_data.get("anime") or {}
    manga = ip_data.get("manga") or {}
    tier = ip_data.get("tier", "Unknown")
    reason = ip_data.get("tier_reason", "")

    anime_lines = []
    if anime and "error" not in anime:
        a_title = anime.get('title_english') or anime.get('title')
        a_url = anime.get('url')
        a_title_str = f"[{a_title}]({a_url})" if a_url else a_title
        a_rank = anime.get('rank')
        a_rank_str = f"[#{a_rank}](https://myanimelist.net/topanime.php)" if a_rank else "N/A"
        anime_lines = [
            f"- **Title:** {a_title_str}",
            f"- **MAL Rank:** {a_rank_str}",
            f"- **Score:** {anime.get('score', 'N/A')} / 10",
            f"- **Members:** {anime.get('members', 0):,}",
            f"- **Favorites:** {anime.get('favorites', 0):,}",
            f"- **Popularity Rank:** #{anime.get('popularity', 'N/A')}",
            f"- **Status:** {anime.get('status', 'N/A')} ({anime.get('episodes', '?')} episodes)",
        ]

    manga_lines = []
    if manga and "error" not in manga:
        m_title = manga.get('title_english') or manga.get('title')
        m_url = manga.get('url')
        m_title_str = f"[{m_title}]({m_url})" if m_url else m_title
        m_rank = manga.get('rank')
        m_rank_str = f"[#{m_rank}](https://myanimelist.net/topmanga.php)" if m_rank else "N/A"
        manga_lines = [
            f"- **Title:** {m_title_str}",
            f"- **MAL Rank:** {m_rank_str}",
            f"- **Score:** {manga.get('score', 'N/A')} / 10",
            f"- **Members:** {manga.get('members', 0):,}",
            f"- **Status:** {manga.get('status', 'N/A')}",
        ]

    anime_block = "\n".join(anime_lines) if anime_lines else "_MAL anime data unavailable_"
    manga_block = "\n".join(manga_lines) if manga_lines else "_MAL manga data unavailable_"

    return f"""## IP Strength — {tier}

**Assessment:** {reason}

### Anime

{anime_block}

### Manga / Light Novel

{manga_block}"""


def _en_history_section(en_history: dict) -> str:
    trend = en_history.get("trend", {})
    sets = en_history.get("sets", [])

    # Table with ROI columns
    rows = []
    for s in sets:
        name = s["name"]
        ptype = "Extra" if s.get("product_type") == "extra_booster" else "Standard"
        preorder = f"${s['preorder_price_usd']:.0f}" if s.get("preorder_price_usd") else "N/A"
        if s.get("current_box_price_usd"):
            price_str = f"${s['current_box_price_usd']:.0f}"
            tcg_url = s.get("tcgplayer_url")
            current = f"[{price_str}]({tcg_url})" if tcg_url else price_str
        else:
            current = "N/A"
        change = f"{s['price_change_pct']:+.0f}%" if s.get("price_change_pct") is not None else "N/A"
        roi = f"{s['roi_pct']:+.0f}%" if s.get("roi_pct") is not None else "N/A"
        post_fee_roi = f"{s['post_fee_roi_pct']:+.0f}%" if s.get("post_fee_roi_pct") is not None else "N/A"
        xirr = f"{s['post_fee_xirr_pct']:+.1f}%/yr" if s.get("post_fee_xirr_pct") is not None else "N/A"
        days = f"{s['days_elapsed']:,}d" if s.get("days_elapsed") else "N/A"
        comp = (s.get("competitive_standing") or "—").title()
        rows.append(f"| {name} | {ptype} | {preorder} | {current} | {change} | {roi} | {post_fee_roi} | {xirr} | {days} | {comp} |")

    table = "\n".join(rows) if rows else "_No historical data available_"

    trend_pat = trend.get("pattern", "unknown").replace("_", " ").title()
    trend_desc = trend.get("description", "")
    avg_chg = trend.get("avg_change_pct")
    avg_str = f"{avg_chg:+.1f}%" if avg_chg is not None else "N/A"

    return f"""## Historical EN Performance

**Trend:** {trend_pat} (avg {avg_str} vs preorder)

{trend_desc}

| Set | Type | Preorder | Current Box | Change | ROI | Post-Fee ROI | Post-Fee XIRR | Age | Competitive |
|-----|------|----------|-------------|--------|-----|--------------|---------------|-----|-------------|
{table}

> _Post-Fee ROI and XIRR assume TCGPlayer seller fees of 11.75% (10.25% marketplace + 1.5% payment processing). XIRR is the annualized return rate — what you'd earn per year if you bought at preorder and sold today. Extra Booster sets not directly comparable to standard boosters._"""


def _jp_section(jp_analysis: dict, set_config: dict) -> str:
    current = jp_analysis.get("current_jp_set") or {}
    ev_signal = jp_analysis.get("ev_signal") or {}
    ev_usd = current.get("box_ev_usd")
    en_pre = jp_analysis.get("expected_en_preorder_usd", 90)

    summary = current.get("summary") or {}
    top10 = summary.get("top_10_by_price", [])
    rarity_table = summary.get("rarity_breakdown", [])

    # Rarity breakdown table
    rarity_rows = []
    for r in rarity_table:
        rarity = r["rarity"]
        count = r["card_count"]
        avg_jpy = r["avg_sell_price_jpy"]
        avg_usd = round(avg_jpy * jp_analysis.get("jpy_to_usd_rate", 0.0067), 2)
        ev_jpy = r["ev_contribution_jpy"]
        excluded = "Yes (AGR/signed)" if r.get("excluded_from_ev") else "No"
        rarity_rows.append(
            f"| {rarity} | {count} | ¥{avg_jpy:,} (${avg_usd:.2f}) | ¥{ev_jpy:,} | {excluded} |"
        )

    rarity_block = "\n".join(rarity_rows) if rarity_rows else "_Card data not yet available_"

    # Top 10 cards
    top_rows = []
    for i, card in enumerate(top10[:10], 1):
        name = card.get("name", "—")
        rarity = card.get("rarity", "—")
        price_jpy = card.get("sell_price_jpy") or 0
        price_usd = round(price_jpy * jp_analysis.get("jpy_to_usd_rate", 0.0067), 2)
        top_rows.append(f"| {i} | {name} | {rarity} | ¥{price_jpy:,} (${price_usd:.2f}) |")

    top_block = "\n".join(top_rows) if top_rows else "_Data not yet fetched_"

    ev_line = f"**Estimated JP Box EV:** ¥{current.get('box_ev_jpy', 'N/A'):,} (~${ev_usd:.0f} USD)" if ev_usd else "**Estimated JP Box EV:** Data not available"
    ev_desc = ev_signal.get("description", "EV comparison data unavailable.")

    jp_code = current.get("set_code", set_config.get("set_code_jp", "—"))
    jp_date = current.get("jp_release_date", "—")

    # Prior JP sets comparison (SP avg and EV)
    prior_jp_rows = []
    for jp_set in jp_analysis.get("sets", []):
        if jp_set.get("is_current"):
            continue
        set_code_jp = jp_set.get("set_code", "—")
        jp_rel = jp_set.get("jp_release_date", "—")
        ev_jpy = jp_set.get("box_ev_jpy")
        ev_u = jp_set.get("box_ev_usd")
        ev_str = f"¥{ev_jpy:,} (${ev_u:.0f})" if ev_jpy and ev_u else "N/A"
        sp = jp_set.get("sp_stats") or {}
        if sp.get("available"):
            sp_str = f"¥{sp['avg_price_jpy']:,} (${sp['avg_price_usd']:.0f}) × {sp['card_count']}"
        else:
            sp_str = "N/A"
        prior_jp_rows.append(f"| {jp_set['name']} | {set_code_jp} | {jp_rel} | {ev_str} | {sp_str} |")

    prior_jp_block = "\n".join(prior_jp_rows) if prior_jp_rows else "_No prior JP set data available_"

    return f"""## Japanese Set Analysis ({jp_code})

**JP Release:** {jp_date} &nbsp;|&nbsp; {ev_line}

**EV vs EN Preorder:** {ev_desc}

> AGR (autograph/signed) rarities are **excluded** from EV — they do not appear in English prints.

### Rarity Breakdown

| Rarity | Cards | Avg Price | Box EV Contribution | Excluded from EV |
|--------|-------|-----------|---------------------|-----------------|
{rarity_block}

### Top 10 Cards by Price (EN-eligible)

| # | Card Name | Rarity | Price |
|---|-----------|--------|-------|
{top_block}

### Prior JP Sets — SP Avg & EV History

| Set | Code | JP Release | Box EV | EX/SP Avg (× cards) |
|-----|------|------------|--------|----------------------|
{prior_jp_block}

> _EX rarity on Yuyutei = EN-eligible SP/SSP equivalents. Helps gauge how this IP's SP values trend over time._"""


def _series_outlook_section(set_config: dict) -> str:
    outlook = set_config.get("series_continuation") or {}
    if not outlook:
        return ""

    status = outlook.get("status", "unknown").replace("_", " ").title()
    future_sets = outlook.get("future_en_sets_expected")
    reasoning = outlook.get("reasoning", "")
    notes = outlook.get("notes", "")
    demand_impact = outlook.get("demand_impact", "")
    simultaneous = set_config.get("simultaneous_jp_en_release", False)

    future_str = "Yes" if future_sets is True else ("No" if future_sets is False else "Unknown")

    simultaneous_note = ""
    if simultaneous:
        simultaneous_note = "\n\n> **Simultaneous EN/JP Release:** EN and JP versions release at the same time. JP market price cannot be used as a forward indicator for EN demand — both markets price discovery happens concurrently."

    return f"""## Series & Future Demand Outlook

**Series Status:** {status} &nbsp;|&nbsp; **Future EN Sets Expected:** {future_str}

{reasoning}

{notes}

**Demand impact:** {demand_impact}{simultaneous_note}"""


def _competitive_section(set_config: dict, synthesis: dict) -> str:
    standing = set_config.get("competitive_standing", "unknown").title()
    notes = set_config.get("competitive_notes", "No competitive data available.")
    score = synthesis["score_breakdown"]["competitive"]["score"]

    return f"""## Competitive Standing — {standing}

**Score contribution:** {score}/2

{notes}"""


def _recommendation_section(synthesis: dict, badge: str) -> str:
    breakdown = synthesis["score_breakdown"]
    score = synthesis["total_score"]
    max_score = synthesis["max_score"]

    ip_b = breakdown["ip_tier"]
    trend_b = breakdown["en_trend"]
    ev_b = breakdown["jp_ev"]
    comp_b = breakdown["competitive"]

    return f"""## Recommendation: {badge}

**Total Score: {score}/{max_score}**

| Dimension | Score | Detail |
|-----------|-------|--------|
| IP Strength | {ip_b['score']}/3 | {ip_b['tier']} — {ip_b.get('reason', '')} |
| EN Trend | {trend_b['score']}/3 | {trend_b['pattern'].replace('_',' ').title()} — {trend_b.get('description', '')[:80]}... |
| JP EV Signal | {ev_b['score']}/2 | {ev_b['rating'].title()} — {(ev_b.get('description') or '')[:80]}... |
| Competitive | {comp_b['score']}/2 | {comp_b['standing'].title()} |

{synthesis['summary']}"""


def _data_sources_section(set_config: dict, today: str) -> str:
    mal_anime = set_config.get("mal_anime_id")
    mal_manga = set_config.get("mal_manga_id")
    ip_type = set_config.get("ip_type", "anime")

    if ip_type == "game":
        ip_data_line = "- **IP Data:** Manual assessment — mobile game IP; MAL data unavailable"
    elif mal_anime or mal_manga:
        lines = ["- **IP Data:** [MyAnimeList](https://myanimelist.net) via Jikan v4 API"]
        if mal_anime:
            lines.append(f"  - Anime: [MAL #{mal_anime}](https://myanimelist.net/anime/{mal_anime})")
        if mal_manga:
            lines.append(f"  - Manga: [MAL #{mal_manga}](https://myanimelist.net/manga/{mal_manga})")
        ip_data_line = "\n".join(lines)
    else:
        ip_data_line = "- **IP Data:** MAL data unavailable for this IP"

    return f"""## Data Sources & Methodology

_All prices are point-in-time snapshots taken {today}. Not financial advice._

{ip_data_line}
- **JP Card Prices:** [Yuyutei](https://yuyu-tei.jp) (scraped)
- **EN Card Prices:** [TCGPlayer](https://www.tcgplayer.com/search/weiss-schwarz/product) (scraped)
- **Pull Rates:** Bushiroad official product pages + community records
- **Methodology:** [How we analyze sets →](/methodology/)"""
