<p align="center">
  <a href="README.es.md">Español</a> | <b>English</b>
</p>

# ⚡ Everything MCP Server

> A Windows **Model Context Protocol (MCP)** server connecting AI assistants (**Claude Desktop**, **Antigravity**, **Cursor**, etc.) to the ultra-fast indexing engine of **voidtools Everything**.

Search across millions of files and folders in **milliseconds** by leveraging Everything's in-memory index via native Windows IPC, **without exposing network ports or compromising private data**.

---

## 🌟 Key Features

- ⚡ **Extreme Speed (NTFS IPC)**: Instant searches across local and external drives indexed by Everything (< 20 ms).
- 🚀 **Silent Auto-Launch**: If Everything is closed when a search is triggered, the server detects it and launches it automatically in the background (`-startup`).
- 🔒 **Total Privacy & Zero-Leak**:
  - No external APIs, secret keys, or `.env` files required.
  - No open HTTP servers or local network exposure.
  - Clean source code: **zero `.exe` or `.dll` binaries tracked in version control**.
  - No hardcoded absolute local paths in the codebase.
- 🛡️ **Win32 Desktop Bridging**: Automatically resolves window/desktop isolation in autonomous agent sandboxes (`WinSta0\Default`), ensuring compatibility in both interactive desktops and agent runner environments.
- 🧰 **LLM-Optimized Tools**:
  - Concise, token-efficient Markdown output with rich metadata (human-readable size, ISO dates, directory indicator).
  - Full support for voidtools advanced search syntax (multiple extensions, date ranges, size filters, regex, and boolean operators).

---

## 🛠️ Exposed MCP Tools

| Tool | Description | Key Parameters |
| :--- | :--- | :--- |
| `everything_search` | General search with full voidtools query syntax support | `query`, `max_results`, `path`, `files_only`, `folders_only`, `sort` |
| `everything_find_file` | Fast file finder matching names or wildcard patterns | `filename`, `path`, `max_results` |
| `everything_find_folder` | Fast directory finder | `folder_name`, `path`, `max_results` |
| `everything_recent_files` | Retrieve files modified in the last N hours | `hours`, `extension`, `path`, `max_results` |
| `everything_status` | Health check and engine version diagnostics | None |

---

## 🚀 Prerequisites

1. **Windows 10/11 (64-bit)**.
2. **voidtools Everything** installed on the machine ([download from voidtools.com](https://www.voidtools.com/)).
3. **Python 3.10+** (or the **uv** package manager).

---

## 📦 Installation & Setup

### Option 1: With `uv` (Recommended)

```powershell
# Clone the repository
git clone <REPOSITORY_URL>
cd everything-mcp

# Create virtual environment and install dependencies
uv venv
uv pip install --system-certs "mcp[cli]>=1.0.0"
```

### Option 2: Standard Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "mcp[cli]>=1.0.0"
```

---

## ⚙️ MCP Client Configuration

> [!NOTE]
> Replace `<PATH_TO_YOUR_REPOSITORY>` with the absolute path where you cloned this repository (e.g., `C:\\dev\\everything-mcp` or `D:\\repos\\everything-mcp`).

### 1. Claude Desktop (`%APPDATA%\Claude\claude_desktop_config.json`)

Add the server to your `mcpServers` block:

```json
{
  "mcpServers": {
    "everything": {
      "command": "uv",
      "args": [
        "--directory",
        "<PATH_TO_YOUR_REPOSITORY>",
        "run",
        "python",
        "-m",
        "everything_mcp.server"
      ]
    }
  }
}
```

*(Using direct virtual environment without global `uv`):*

```json
{
  "mcpServers": {
    "everything": {
      "command": "<PATH_TO_YOUR_REPOSITORY>\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "everything_mcp.server"
      ],
      "env": {
        "PYTHONPATH": "<PATH_TO_YOUR_REPOSITORY>\\src"
      }
    }
  }
}
```

### 2. Antigravity / Cursor / VS Code (`mcp.json`)

```json
{
  "servers": {
    "everything": {
      "command": "<PATH_TO_YOUR_REPOSITORY>\\.venv\\Scripts\\python.exe",
      "args": ["-m", "everything_mcp.server"],
      "env": {
        "PYTHONPATH": "<PATH_TO_YOUR_REPOSITORY>\\src"
      }
    }
  }
}
```

---

## 💡 Useful Query Examples for AI Agents

- **By extension**: `ext:pdf;docx invoice`
- **By size**: `size:>500MB` or `size:small` (<100 KB)
- **By modification date**: `dm:today` or `dm:last2hours`
- **Restricted to a specific folder**: `path:"C:\My Documents" *.py`
- **Exclusions**: `*.log !temp`
- **Regular expressions**: `regex:^IMG_[0-9]{4}\.png`

---

## 🧪 Quick Test

To verify local functionality:

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe tests\test_searcher.py
```

---

## 📄 License

- **Everything MCP Server**: MIT License &copy; 2026 JaviRTX. Free for personal, commercial use, modification, and distribution.
- **voidtools Everything**: MIT License &copy; voidtools. Free for personal and commercial use.
