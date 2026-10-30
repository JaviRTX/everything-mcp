"""Unit tests for EverythingSearcher."""

from everything_mcp.searcher import EverythingSearcher, escape_switches, format_bytes


def _running_searcher():
    """Return a searcher if Everything is available, else None (tests that need it are skipped)."""
    try:
        searcher = EverythingSearcher()
    except FileNotFoundError:
        return None
    running, _ = searcher.is_everything_running()
    if not running:
        print("SKIP: Everything is not running on this machine")
        return None
    return searcher


def test_format_bytes():
    assert format_bytes(None) == "<DIR>"
    assert format_bytes(500) == "500 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(1048576) == "1.00 MB"


def test_escape_switches():
    assert escape_switches("ext:pdf;docx invoice") == "ext:pdf;docx invoice"
    assert escape_switches('path:"C:\\My Documents" *.py') == 'path:"C:\\My Documents" *.py'
    assert escape_switches("my-file !temp") == "my-file !temp"
    assert escape_switches("foo -export-txt C:\\out.txt") == 'foo "-export-txt" C:\\out.txt'
    assert escape_switches('x "-n" /ad') == 'x "-n" "/ad"'


def test_searcher_status():
    searcher = _running_searcher()
    if searcher is None:
        return
    running, info = searcher.is_everything_running()
    print(f"Everything running: {running}, info: {info}")
    assert running is True
    assert "Everything" in info


def test_searcher_query():
    searcher = _running_searcher()
    if searcher is None:
        return
    # Search for an inevitable file on Windows
    results = searcher.search("Everything.ini", max_results=5)
    print(f"Results found: {len(results)}")
    assert len(results) > 0
    assert any("Everything.ini" in r["name"] for r in results)


if __name__ == "__main__":
    test_format_bytes()
    test_escape_switches()
    test_searcher_status()
    test_searcher_query()
    print("All tests passed successfully!")
