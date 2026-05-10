"""MCP server exposing English WS card prices via TCGPlayer scraping."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import mcp.server.stdio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
import json

from lib import ws_prices

server = Server("mcp-ws-prices")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_box_price",
            description="Get current sealed booster box market price from TCGPlayer for a WS EN set.",
            inputSchema={
                "type": "object",
                "properties": {
                    "set_name": {"type": "string", "description": "EN set name, e.g. 'Re:Zero Vol.1'"}
                },
                "required": ["set_name"],
            },
        ),
        Tool(
            name="get_card_price",
            description="Get market price for a specific WS card on TCGPlayer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "card_name": {"type": "string", "description": "Card name"},
                    "set_name": {"type": "string", "description": "Set name"},
                },
                "required": ["card_name", "set_name"],
            },
        ),
        Tool(
            name="get_set_summary",
            description="Get top singles by price for a WS EN set from TCGPlayer, including SP/SSP averages.",
            inputSchema={
                "type": "object",
                "properties": {
                    "set_name": {"type": "string", "description": "EN set name"}
                },
                "required": ["set_name"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_box_price":
        result = ws_prices.get_box_price(arguments["set_name"])
    elif name == "get_card_price":
        result = ws_prices.get_card_price(arguments["card_name"], arguments["set_name"])
    elif name == "get_set_summary":
        result = ws_prices.get_set_summary(arguments["set_name"])
    else:
        result = {"error": f"unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-ws-prices",
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
