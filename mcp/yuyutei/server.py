"""MCP server exposing Yuyutei JP Weiss Schwarz card prices."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import mcp.server.stdio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
import json

from lib import yuyutei

server = Server("mcp-yuyutei")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_set",
            description="Search for Weiss Schwarz sets on Yuyutei by name. Returns set names and IDs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Set name to search (Japanese or romanized)"}
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_set_cards",
            description="Fetch all cards for a Yuyutei set ID. Returns card list with rarity, name, and prices.",
            inputSchema={
                "type": "object",
                "properties": {
                    "set_id": {"type": "string", "description": "Yuyutei set ID"}
                },
                "required": ["set_id"],
            },
        ),
        Tool(
            name="get_set_summary",
            description=(
                "Compute set summary with EV breakdown. AGR/signed rarities are excluded from EV "
                "as they do not appear in English prints. Returns rarity breakdown, top-10 cards by price, "
                "and estimated box EV in JPY."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "set_id": {"type": "string", "description": "Yuyutei set ID"},
                    "pulls_per_box": {
                        "type": "integer",
                        "description": "Rare+ slots per box (default 8 for standard WS)",
                        "default": 8,
                    },
                },
                "required": ["set_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "search_set":
        result = yuyutei.search_set(arguments["query"])
    elif name == "get_set_cards":
        result = yuyutei.get_set_cards(arguments["set_id"])
    elif name == "get_set_summary":
        result = yuyutei.get_set_summary(
            arguments["set_id"],
            arguments.get("pulls_per_box", 8),
        )
    else:
        result = {"error": f"unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-yuyutei",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
