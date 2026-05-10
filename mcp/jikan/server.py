"""MCP server exposing MyAnimeList data via the Jikan v4 API."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import mcp.server.stdio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
import mcp.types as types
import json

from lib import jikan

server = Server("mcp-jikan")


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_anime",
            description="Fetch anime details from MyAnimeList by MAL ID. Returns rank, score, members, favorites, popularity, status, episodes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mal_id": {"type": "integer", "description": "MyAnimeList anime ID"}
                },
                "required": ["mal_id"],
            },
        ),
        Tool(
            name="get_manga",
            description="Fetch manga details from MyAnimeList by MAL ID. Returns rank, score, members, favorites, popularity, status, volumes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "mal_id": {"type": "integer", "description": "MyAnimeList manga ID"}
                },
                "required": ["mal_id"],
            },
        ),
        Tool(
            name="search_anime",
            description="Search for anime on MyAnimeList by title query. Returns top 5 matches with ID, score, and rank.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Anime title to search for"},
                    "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="search_manga",
            description="Search for manga on MyAnimeList by title query. Returns top 5 matches.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Manga title to search for"},
                    "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
                },
                "required": ["query"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_anime":
        result = jikan.get_anime(arguments["mal_id"])
    elif name == "get_manga":
        result = jikan.get_manga(arguments["mal_id"])
    elif name == "search_anime":
        result = jikan.search_anime(arguments["query"], arguments.get("limit", 5))
    elif name == "search_manga":
        result = jikan.search_manga(arguments["query"], arguments.get("limit", 5))
    else:
        result = {"error": f"unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]


async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mcp-jikan",
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
