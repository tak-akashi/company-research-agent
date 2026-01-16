"""PDF Tools MCP Server."""

from __future__ import annotations

import json
import sys
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from . import handlers

# MCPサーバーインスタンス
server = Server("pdf-tools")


@server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
async def list_tools() -> list[Tool]:
    """利用可能なツール一覧を返す."""
    return [
        Tool(
            name="pdf_get_info",
            description="PDFファイルのメタデータを取得します（ページ数、目次など）。全体像の把握に使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "PDFファイルの絶対パス",
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="pdf_read_pages",
            description="PDFの指定ページ範囲のテキストを抽出します。部分的な読み込みに使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "PDFファイルの絶対パス",
                    },
                    "start_page": {
                        "type": "integer",
                        "description": "開始ページ番号（1始まり）",
                        "default": 1,
                    },
                    "end_page": {
                        "type": "integer",
                        "description": "終了ページ番号（省略時は最終ページまで）",
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="pdf_to_markdown",
            description="PDFをマークダウン形式に変換します。構造化された読み込みに使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "PDFファイルの絶対パス",
                    },
                    "start_page": {
                        "type": "integer",
                        "description": "開始ページ番号（1始まり、省略時は最初から）",
                    },
                    "end_page": {
                        "type": "integer",
                        "description": "終了ページ番号（省略時は最終ページまで）",
                    },
                },
                "required": ["pdf_path"],
            },
        ),
        Tool(
            name="pdf_extract_tables",
            description="PDFから表を抽出します。API仕様書の表データ取得に使用。",
            inputSchema={
                "type": "object",
                "properties": {
                    "pdf_path": {
                        "type": "string",
                        "description": "PDFファイルの絶対パス",
                    },
                    "page_number": {
                        "type": "integer",
                        "description": "特定ページのみ抽出（省略時は全ページ）",
                    },
                },
                "required": ["pdf_path"],
            },
        ),
    ]


@server.call_tool()  # type: ignore[untyped-decorator]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """ツールを実行する."""
    try:
        if name == "pdf_get_info":
            info = handlers.get_pdf_info(arguments["pdf_path"])
            return [TextContent(type="text", text=json.dumps(info, ensure_ascii=False, indent=2))]

        elif name == "pdf_read_pages":
            text = handlers.read_pages(
                arguments["pdf_path"],
                arguments.get("start_page", 1),
                arguments.get("end_page"),
            )
            return [TextContent(type="text", text=text)]

        elif name == "pdf_to_markdown":
            md_text = handlers.to_markdown(
                arguments["pdf_path"],
                arguments.get("start_page"),
                arguments.get("end_page"),
            )
            return [TextContent(type="text", text=md_text)]

        elif name == "pdf_extract_tables":
            tables_json = handlers.extract_tables(
                arguments["pdf_path"],
                arguments.get("page_number"),
            )
            return [TextContent(type="text", text=tables_json)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except FileNotFoundError as e:
        return [TextContent(type="text", text=f"Error: {e}")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {type(e).__name__}: {e}")]


async def main() -> None:
    """MCPサーバーを起動する."""
    print("Starting PDF Tools MCP Server...", file=sys.stderr)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
