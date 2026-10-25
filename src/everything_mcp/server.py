"""Everything MCP Server.

Exposes voidtools Everything search capabilities as Model Context Protocol (MCP) tools
for AI assistants like Claude Desktop, Cursor, Antigravity, and other MCP clients.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional

try:
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:
    from mcp.server.fastmcp import FastMCP

from everything_mcp.searcher import EverythingSearcher, format_bytes

# Initialize FastMCP Server
mcp = FastMCP("Everything Search")
searcher = EverythingSearcher()


def _format_results_markdown(results: List[Dict[str, Any]], query_desc: str) -> str:
    """Format search results into clean, token-efficient markdown for LLMs."""
    if not results:
        return f"No results found for {query_desc}."

    lines = [f"Found {len(results)} item(s) for {query_desc}:\n"]
    for i, item in enumerate(results, start=1):
        tag = "[DIR] " if item["is_directory"] else "[FILE]"
        size = item["size_formatted"]
        date = item["date_modified"] or "Unknown date"
        path = item["path"]
        lines.append(f"{i}. {tag} `{path}` ({size}, modified: {date})")

    return "\n".join(lines)


@mcp.tool()
def everything_search(
    query: str,
    max_results: int = 50,
    path: Optional[str] = None,
    files_only: bool = False,
    folders_only: bool = False,
    sort: str = "name",
    sort_descending: bool = False,
    case_sensitive: bool = False,
    regex: bool = False,
) -> str:
    """Search for files and directories across all indexed drives in milliseconds.

    Supports voidtools Everything search syntax:
      - Extensions: ext:py;ts or *.pdf
      - Size filters: size:>50mb, size:small (<100kb), size:empty
      - Date filters: dm:today, dm:yesterday, dm:thisweek, dm:2026-10
      - Attributes: folder: or file:
      - Boolean operators: AND (space), OR (|), NOT (!)

    Args:
        query: Search term or pattern (e.g. '*.py dm:today', 'ext:docx report').
        max_results: Maximum results to return (1-500, default 50).
        path: Optional directory path to restrict results to (e.g. 'C:\\Projects' or 'D:\\Data').
        files_only: Filter only files (exclude directories).
        folders_only: Filter only directories (exclude files).
        sort: Field to sort by ('name', 'path', 'size', 'extension', 'date-modified').
        sort_descending: Sort in descending order if True.
        case_sensitive: Match exact casing if True.
        regex: Treat query as a regular expression.
    """
    try:
        results = searcher.search(
            query=query,
            max_results=max_results,
            path=path,
            files_only=files_only,
            folders_only=folders_only,
            sort=sort,
            sort_descending=sort_descending,
            case_sensitive=case_sensitive,
            regex=regex,
        )
        desc = f"query '{query}'" + (f" in '{path}'" if path else "")
        return _format_results_markdown(results, desc)
    except Exception as e:
        return f"Error executing Everything search: {e}"


@mcp.tool()
def everything_find_file(
    filename: str,
    path: Optional[str] = None,
    max_results: int = 25,
) -> str:
    """Quick helper to find files matching a name or wildcard pattern.

    Args:
        filename: Name or wildcard pattern (e.g. 'package.json', '*.sqlite3', 'report*.xlsx').
        path: Optional directory path to search within.
        max_results: Maximum results to return (default 25).
    """
    try:
        results = searcher.search(
            query=filename,
            max_results=max_results,
            path=path,
            files_only=True,
            sort="name",
        )
        desc = f"file '{filename}'" + (f" in '{path}'" if path else "")
        return _format_results_markdown(results, desc)
    except Exception as e:
        return f"Error finding file: {e}"


@mcp.tool()
def everything_find_folder(
    folder_name: str,
    path: Optional[str] = None,
    max_results: int = 25,
) -> str:
    """Quick helper to find directories matching a name or pattern.

    Args:
        folder_name: Directory name or pattern (e.g. 'venv', 'skills', 'backup*').
        path: Optional parent path to search within.
        max_results: Maximum results to return (default 25).
    """
    try:
        results = searcher.search(
            query=folder_name,
            max_results=max_results,
            path=path,
            folders_only=True,
            sort="name",
        )
        desc = f"folder '{folder_name}'" + (f" in '{path}'" if path else "")
        return _format_results_markdown(results, desc)
    except Exception as e:
        return f"Error finding folder: {e}"


@mcp.tool()
def everything_recent_files(
    hours: int = 24,
    extension: Optional[str] = None,
    path: Optional[str] = None,
    max_results: int = 30,
) -> str:
    """Find files modified recently within the specified number of hours.

    Args:
        hours: How many hours back to look (default 24).
        extension: Optional extension filter (e.g. 'py', 'pdf', 'png').
        path: Optional root directory to limit search to.
        max_results: Maximum files to return (default 30).
    """
    try:
        query_parts = [f"dm:last{hours}hours"]
        if extension:
            ext = extension.strip().lstrip(".")
            query_parts.append(f"ext:{ext}")

        full_query = " ".join(query_parts)
        results = searcher.search(
            query=full_query,
            max_results=max_results,
            path=path,
            files_only=True,
            sort="date-modified",
            sort_descending=True,
        )
        desc = f"files modified in last {hours}h" + (f" (ext: {extension})" if extension else "")
        return _format_results_markdown(results, desc)
    except Exception as e:
        return f"Error retrieving recent files: {e}"


@mcp.tool()
def everything_status() -> str:
    """Check whether voidtools Everything is active and responding to IPC."""
    try:
        running, info = searcher.is_everything_running()
        if running:
            return f"Status: OK\nEngine: {info}\nIPC Interface: Active (WinSta0\\Default bridged)"
        else:
            return f"Status: OFFLINE\nDetail: {info}\nTip: Ensure Everything is running on this machine."
    except Exception as e:
        return f"Status: ERROR\nDetail: {e}"


def main():
    """Main entrypoint for MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
