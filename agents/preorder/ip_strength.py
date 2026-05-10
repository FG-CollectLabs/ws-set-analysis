"""IP strength scoring from MyAnimeList data."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib import jikan


def score_ip(
    mal_anime_id: int | None,
    mal_manga_id: int | None,
    ip_tier_override: str | None = None,
    ip_tier_reason_override: str | None = None,
    ip_type: str = "anime",
) -> dict:
    """
    Fetch MAL data for the anime and manga versions of an IP and compute a strength score.
    For non-anime IPs (games, etc.), pass ip_tier_override + ip_tier_reason_override
    to bypass MAL-based scoring when MAL data is insufficient.
    """
    anime_data = None
    manga_data = None

    if mal_anime_id:
        try:
            anime_data = jikan.get_anime(mal_anime_id)
        except Exception as e:
            anime_data = {"error": str(e), "mal_id": mal_anime_id}

    if mal_manga_id:
        try:
            manga_data = jikan.get_manga(mal_manga_id)
        except Exception as e:
            manga_data = {"error": str(e), "mal_id": mal_manga_id}

    if ip_tier_override:
        tier = ip_tier_override
        reason = ip_tier_reason_override or f"Manual override: {ip_tier_override}"
    else:
        tier, reason = _compute_tier(anime_data, manga_data)

    return {
        "anime": anime_data,
        "manga": manga_data,
        "ip_type": ip_type,
        "tier": tier,
        "tier_reason": reason,
    }


def _compute_tier(anime: dict | None, manga: dict | None) -> tuple[str, str]:
    """
    Tier rules:
      Strong   — anime rank ≤ 500, OR members > 500,000
      Moderate — anime rank 501–2000, OR members 100k–500k
      Niche    — anime rank > 2000 or no anime
    Manga boosts: manga rank ≤ 500 can upgrade Niche → Moderate, Moderate → Strong
    """
    anime_rank = anime.get("rank") if anime and "error" not in anime else None
    anime_members = anime.get("members") if anime and "error" not in anime else None
    manga_rank = manga.get("rank") if manga and "error" not in manga else None

    # Primary: anime signal
    if anime_rank and anime_rank <= 500:
        return "Strong", f"Anime MAL rank #{anime_rank} (top 500)"
    if anime_members and anime_members > 500_000:
        return "Strong", f"Anime member count {anime_members:,} > 500k"
    if anime_rank and anime_rank <= 2000:
        tier = "Moderate"
        reason = f"Anime MAL rank #{anime_rank} (rank 501–2000)"
        # Manga boost
        if manga_rank and manga_rank <= 500:
            return "Strong", f"{reason} + manga rank #{manga_rank} (top 500 → boosted to Strong)"
        return tier, reason
    if anime_members and anime_members > 100_000:
        tier = "Moderate"
        reason = f"Anime member count {anime_members:,} (100k–500k)"
        if manga_rank and manga_rank <= 500:
            return "Strong", f"{reason} + manga rank #{manga_rank} boost"
        return tier, reason

    # Fallback to manga if anime is weak or absent
    if manga_rank and manga_rank <= 500:
        return "Moderate", f"No strong anime signal; manga rank #{manga_rank} (top 500)"

    if anime_rank:
        return "Niche", f"Anime rank #{anime_rank} (> 2000)"

    return "Niche", "No anime rank data; insufficient signals"
