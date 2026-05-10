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
        anime_lines = [
            f"- **Title:** {anime.get('title_english') or anime.get('title')}",
            f"- **MAL Rank:** #{anime.get('rank', 'N/A')}",
            f"- **Score:** {anime.get('score', 'N/A')} / 10",
            f"- **Members:** {anime.get('members', 0):,}",
            f"- **Favorites:** {anime.get('favorites', 0):,}",
            f"- **Popularity Rank:** #{anime.get('popularity', 'N/A')}",
            f"- **Status:** {anime.get('status', 'N/A')} ({anime.get('episodes', '?')} episodes)",
        ]

    manga_lines = []
    if manga and "error" not in manga:
        manga_lines = [
            f"- **Title:** {manga.get('title_english') or manga.get('title')}",
            f"- **MAL Rank:** #{manga.get('rank', 'N/A')}",
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

    # Table
    rows = []
    for s in sets:
        name = s["name"]
        ptype = "Extra" if s.get("product_type") == "extra_booster" else "Standard"
        preorder = f"${s['preorder_price_usd']:.0f}" if s.get("preorder_price_usd") else "N/A"
        current = f"${s['current_box_price_usd']:.0f}" if s.get("current_box_price_usd") else "N/A"
        change = f"{s['price_change_pct']:+.0f}%" if s.get("price_change_pct") is not None else "N/A"
        days = f"{s['days_elapsed']:,}d" if s.get("days_elapsed") else "N/A"
        comp = (s.get("competitive_standing") or "—").title()
        rows.append(f"| {name} | {ptype} | {preorder} | {current} | {change} | {days} | {comp} |")

    table = "\n".join(rows) if rows else "_No historical data available_"

    trend_pat = trend.get("pattern", "unknown").replace("_", " ").title()
    trend_desc = trend.get("description", "")
    avg_chg = trend.get("avg_change_pct")
    avg_str = f"{avg_chg:+.1f}%" if avg_chg is not None else "N/A"

    return f"""## Historical EN Performance

**Trend:** {trend_pat} (avg {avg_str} vs preorder)

{trend_desc}

| Set | Type | Preorder | Current Box | Change | Age | Competitive |
|-----|------|----------|-------------|--------|-----|-------------|
{table}

> _Note: Extra Booster sets are not directly comparable to standard boosters due to different price points and pack configurations._"""


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
{top_block}"""


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
    jp_code = set_config.get("set_code_jp", "")

    return f"""## Data Sources & Methodology

_All prices are point-in-time snapshots taken {today}. Not financial advice._

- **IP Data:** [MyAnimeList](https://myanimelist.net) via Jikan v4 API
  - Anime: [MAL #{mal_anime}](https://myanimelist.net/anime/{mal_anime})
  - Manga: [MAL #{mal_manga}](https://myanimelist.net/manga/{mal_manga})
- **JP Card Prices:** [Yuyutei](https://yuyu-tei.jp) (scraped)
- **EN Card Prices:** [TCGPlayer](https://www.tcgplayer.com/search/weiss-schwarz/product) (scraped)
- **Pull Rates:** Bushiroad official product pages + community records
- **Methodology:** [How we analyze sets →](/methodology/)"""
