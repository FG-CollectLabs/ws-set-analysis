"""
Preorder analysis agent entry point.

Usage:
    python agents/preorder/run.py <set-slug>

Example:
    python agents/preorder/run.py rezero-vol3
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from agents.preorder.ip_strength import score_ip
from agents.preorder.en_historical import analyze_en_history
from agents.preorder.jp_set_analysis import analyze_jp_sets
from agents.preorder.synthesis import synthesize
from agents.preorder.post_generator import generate_post


def load_set_config(slug: str) -> dict:
    config_path = ROOT / "agents" / "sets" / f"{slug}.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Set config not found: {config_path}")
    return json.loads(config_path.read_text(encoding="utf-8"))


def run(slug: str) -> None:
    print(f"\n{'='*60}")
    print(f"  WS Set Analysis — Preorder")
    print(f"  Set: {slug}")
    print(f"{'='*60}\n")

    # Load set config
    print("[1/5] Loading set config...")
    cfg = load_set_config(slug)
    print(f"      {cfg['set_name']} | JP code: {cfg.get('set_code_jp', 'N/A')}")

    # IP Strength
    print("\n[2/5] Fetching IP strength from MyAnimeList...")
    ip_data = score_ip(
        mal_anime_id=cfg.get("mal_anime_id"),
        mal_manga_id=cfg.get("mal_manga_id"),
        ip_tier_override=cfg.get("ip_tier_override"),
        ip_tier_reason_override=cfg.get("ip_tier_reason_override"),
        ip_type=cfg.get("ip_type", "anime"),
    )
    print(f"      Tier: {ip_data['tier']} — {ip_data['tier_reason']}")

    # EN Historical
    print("\n[3/5] Analyzing EN historical performance...")
    en_history = analyze_en_history(cfg.get("en_historical_sets", []))
    trend = en_history.get("trend", {})
    print(f"      Trend: {trend.get('pattern', 'unknown')} | avg {trend.get('avg_change_pct', 'N/A')}% vs preorder")

    # JP Set Analysis
    print("\n[4/5] Fetching JP set data from Yuyutei...")
    jp_analysis = analyze_jp_sets(
        cfg.get("jp_equivalent_sets", []),
        expected_en_preorder_usd=cfg.get("expected_en_preorder_price_usd", 90.0),
    )
    ev_signal = jp_analysis.get("ev_signal") or {}
    current = jp_analysis.get("current_jp_set") or {}
    ev_usd = current.get("box_ev_usd")
    print(f"      Current JP set EV: ${ev_usd:.0f} USD" if ev_usd else "      JP EV: data not available")
    print(f"      EV signal: {ev_signal.get('rating', 'unknown')}")

    # Synthesis
    print("\n[5/5] Synthesizing recommendation...")
    rec_data = synthesize(
        ip_data=ip_data,
        en_history=en_history,
        jp_analysis=jp_analysis,
        competitive_standing=cfg.get("competitive_standing", "unknown"),
        simultaneous_release=cfg.get("simultaneous_jp_en_release", False),
    )
    print(f"\n  *** RECOMMENDATION: {rec_data['recommendation'].upper()} ***")
    print(f"  Score: {rec_data['total_score']}/{rec_data['max_score']}")
    print(f"  {rec_data['summary']}")

    # Generate blog post
    print("\n[+] Generating Hugo blog post...")
    output_path = generate_post(
        set_config=cfg,
        ip_data=ip_data,
        en_history=en_history,
        jp_analysis=jp_analysis,
        synthesis=rec_data,
        stage="preorder",
    )
    print(f"    Written to: {output_path}")

    # Also dump full data as JSON for debugging
    debug_path = ROOT / "agents" / "sets" / f"{slug}-analysis-debug.json"
    debug_data = {
        "set_config": cfg,
        "ip_data": ip_data,
        "en_history": en_history,
        "jp_analysis": jp_analysis,
        "synthesis": rec_data,
    }
    debug_path.write_text(json.dumps(debug_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    Debug dump: {debug_path}")

    print(f"\n{'='*60}")
    print(f"  Done. Open {output_path} to review the post.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python agents/preorder/run.py <set-slug>")
        print("Example: python agents/preorder/run.py rezero-vol3")
        sys.exit(1)
    run(sys.argv[1])
