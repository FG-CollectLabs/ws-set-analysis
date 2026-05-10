"""MyAnimeList data via the Jikan v4 unofficial REST API."""

import time
import httpx

BASE_URL = "https://api.jikan.moe/v4"
_last_request_at: float = 0.0


def _get(path: str) -> dict:
    global _last_request_at
    elapsed = time.monotonic() - _last_request_at
    if elapsed < 0.4:
        time.sleep(0.4 - elapsed)
    resp = httpx.get(f"{BASE_URL}{path}", timeout=15)
    _last_request_at = time.monotonic()
    resp.raise_for_status()
    return resp.json()


def get_anime(mal_id: int) -> dict:
    data = _get(f"/anime/{mal_id}")["data"]
    return {
        "mal_id": data["mal_id"],
        "title": data["title"],
        "title_english": data.get("title_english"),
        "rank": data.get("rank"),
        "score": data.get("score"),
        "scored_by": data.get("scored_by"),
        "members": data.get("members"),
        "favorites": data.get("favorites"),
        "popularity": data.get("popularity"),
        "status": data.get("status"),
        "episodes": data.get("episodes"),
        "year": data.get("year"),
        "url": data.get("url"),
    }


def get_manga(mal_id: int) -> dict:
    data = _get(f"/manga/{mal_id}")["data"]
    return {
        "mal_id": data["mal_id"],
        "title": data["title"],
        "title_english": data.get("title_english"),
        "rank": data.get("rank"),
        "score": data.get("score"),
        "scored_by": data.get("scored_by"),
        "members": data.get("members"),
        "favorites": data.get("favorites"),
        "popularity": data.get("popularity"),
        "status": data.get("status"),
        "volumes": data.get("volumes"),
        "chapters": data.get("chapters"),
        "url": data.get("url"),
    }


def search_anime(query: str, limit: int = 5) -> list[dict]:
    data = _get(f"/anime?q={query}&limit={limit}")["data"]
    return [
        {
            "mal_id": a["mal_id"],
            "title": a["title"],
            "score": a.get("score"),
            "rank": a.get("rank"),
            "members": a.get("members"),
            "year": a.get("year"),
        }
        for a in data
    ]


def search_manga(query: str, limit: int = 5) -> list[dict]:
    data = _get(f"/manga?q={query}&limit={limit}")["data"]
    return [
        {
            "mal_id": a["mal_id"],
            "title": a["title"],
            "score": a.get("score"),
            "rank": a.get("rank"),
            "members": a.get("members"),
        }
        for a in data
    ]
