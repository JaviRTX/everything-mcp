"""Unit tests for EverythingSearcher."""

from everything_mcp.searcher import EverythingSearcher, format_bytes


def test_format_bytes():
    assert format_bytes(None) == "<DIR>"
    assert format_bytes(500) == "500 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(1048576) == "1.00 MB"


def test_searcher_status():
    searcher = EverythingSearcher()
    running, info = searcher.is_everything_running()
    print(f"Everything running: {running}, info: {info}")
    assert running is True
    assert "Everything" in info


def test_searcher_query():
    searcher = EverythingSearcher()
    # Search for an inevitable file on Windows
    results = searcher.search("Everything.ini", max_results=5)
    print(f"Results found: {len(results)}")
    assert len(results) > 0
    assert any("Everything.ini" in r["name"] for r in results)


if __name__ == "__main__":
    test_format_bytes()
    test_searcher_status()
    test_searcher_query()
    print("All tests passed successfully!")
