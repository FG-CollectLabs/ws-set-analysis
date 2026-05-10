# WS Set Analysis

Weiss Schwarz booster set investment analysis — preorder signals, JP set data, and historical EN performance.

**Live blog:** https://fg-collectlabs.github.io/ws-set-analysis/

## What this does

Answers one question: **should I preorder this WS set, or wait for the post-release dip?**

Each analysis covers:
1. **IP Strength** — anime/manga rankings from MyAnimeList
2. **Historical EN Performance** — how prior sets in the same IP behaved after release
3. **JP Set Analysis** — current card values on Yuyutei (excluding AGR/signed rarities)
4. **Competitive Standing** — EN tournament relevance
5. **Recommendation** — Strong Buy / Buy / Wait for Dip / Pass

## Running an analysis

```bash
pip install -r requirements.txt
python agents/preorder/run.py rezero-vol3
```

Output: `blog/content/sets/rezero-vol3/preorder.md`

## MCP servers

Three MCP servers for Claude Code interactive use:
- `mcp/jikan/` — MyAnimeList data via Jikan v4 API
- `mcp/yuyutei/` — JP card prices from Yuyutei
- `mcp/ws-prices/` — EN card prices from TCGPlayer

See `CLAUDE.md` for configuration instructions.

## Adding a new set

1. Add `agents/sets/<slug>.json` (use `rezero-vol3.json` as template)
2. Add seed data for prior EN sets in `seed-data/en-sets/`
3. Run `python agents/preorder/run.py <slug>`

## Architecture

Full design doc: [`.github/projects/weiss-schwarz-analysis/ARCHITECTURE.md`](https://github.com/FG-CollectLabs/.github/blob/main/projects/weiss-schwarz-analysis/ARCHITECTURE.md)
