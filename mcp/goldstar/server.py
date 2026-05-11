"""MCP server exposing Goldstar Collectibles preorder pricing via Reddit u/th8596."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
import mcp.server.stdio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent

from lib import goldstar

server = Server("mcp-goldstar")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="find_preorder_price",
            description=(
                "Find the most recent Goldstar Collectibles preorder price for a Weiss Schwarz set. "
                "Goldstar (Reddit u/th8596) is typically the lowest preorder price in the market. "
                "Returns box price, case price, post URL, and post date."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "set_name": {"type": "string", "description": "Set name, e.g. 'Oshi no Ko Vol.2'"},
                    "volume": {"type": "string", "description": "Volume hint, e.g. 'Vol.2'"},
                    "language": {"type": "string", "enum": ["EN", "JP"], "default": "EN"},
                },
                "required": ["set_name"],
            },
        ),
        Tool(
            name="list_recent_preorders",
            description="List all recent EN Weiss Schwarz preorder prices from Goldstar Collectibles.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 30, "description": "Max results to return"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "find_preorder_price":
        result = goldstar.find_preorder_price(
            set_name=arguments["set_name"],
            volume=arguments.get("volume"),
            language=arguments.get("language", "EN"),
        )
    elif name == "list_recent_preorders":
        result = goldstar.list_recent_en_preorders(limit=arguments.get("limit", 30))
    else:
        result = {"error": f"unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-goldstar",
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
