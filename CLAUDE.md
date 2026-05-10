# ws-set-analysis — Claude Code conventions

## Project overview

Weiss Schwarz booster set investment analysis blog + agent system. See `.github/projects/weiss-schwarz-analysis/ARCHITECTURE.md` for full design.

## Directory structure

```
ws-set-analysis/
├── blog/                  Hugo site → GitHub Pages
├── agents/preorder/       Main analysis agent
│   └── run.py             Entry point: python agents/preorder/run.py <slug>
├── agents/sets/           Per-set config JSON files
├── mcp/jikan/             MCP server: MyAnimeList via Jikan v4
├── mcp/yuyutei/           MCP server: Yuyutei JP card prices
├── mcp/ws-prices/         MCP server: TCGPlayer EN card prices
├── lib/                   Shared library: jikan.py, yuyutei.py, ws_prices.py
└── seed-data/en-sets/     Historical EN set data (manual JSON)
```

## Running the analysis

```bash
# From repo root
python agents/preorder/run.py rezero-vol3
```

Output: `blog/content/sets/rezero-vol3/preorder.md`
Debug dump: `agents/sets/rezero-vol3-analysis-debug.json`

## Adding a new set

1. Create `agents/sets/<slug>.json` with set config (copy rezero-vol3.json as template)
2. Add seed data files to `seed-data/en-sets/` for any prior EN sets of the IP
3. Run: `python agents/preorder/run.py <slug>`

## Hugo blog

```bash
cd blog
hugo server -D          # local preview
hugo                     # production build → blog/public/
```

Theme: PaperMod (git submodule at `blog/themes/PaperMod`).
GH Pages: auto-deployed by `.github/workflows/hugo.yml` on push to `main`.

## MCP servers (for Claude Code interactive use)

Each MCP server can be run standalone and added to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jikan": {
      "command": "python",
      "args": ["C:/Users/nguye/VSCode/FG-CollectLabs/ws-set-analysis/mcp/jikan/server.py"]
    },
    "yuyutei": {
      "command": "python",
      "args": ["C:/Users/nguye/VSCode/FG-CollectLabs/ws-set-analysis/mcp/yuyutei/server.py"]
    },
    "ws-prices": {
      "command": "python",
      "args": ["C:/Users/nguye/VSCode/FG-CollectLabs/ws-set-analysis/mcp/ws-prices/server.py"]
    }
  }
}
```

## Code conventions

- Python 3.13+. No type: ignore comments — fix the types.
- lib/ modules are pure functions — no side effects except yuyutei.py caching.
- Seed data JSON files are the source of truth for historical EN prices/pull rates.
- Do not commit analysis debug JSON files (they're in .gitignore).
- All prices in USD unless suffixed `_jpy`.
