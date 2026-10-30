"""Everything Searcher engine for Windows.

Interfaces with voidtools Everything using the official 'es.exe' CLI
and Win32 IPC desktop isolation handling, with auto-download and auto-launch support.
"""

from __future__ import annotations

import csv
import ctypes
from ctypes import wintypes
import io
import msvcrt
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional
import urllib.request
import winreg
import zipfile


def format_bytes(size: Optional[int]) -> str:
    """Format byte size into human readable string."""
    if size is None:
        return "<DIR>"
    if size < 1024:
        return f"{size} B"
    for unit in ["KB", "MB", "GB", "TB"]:
        size /= 1024.0
        if size < 1024.0:
            return f"{size:.2f} {unit}"
    return f"{size:.2f} PB"


def escape_switches(query: str) -> str:
    """Quote query tokens starting with '-' or '/' so es.exe reads them as search text, not options.

    Without this, a query like 'foo -export-txt C:\\out.txt' would make es.exe write a file.
    """
    tokens = re.findall(r'(?:[^\s"]+|"[^"]*")+', query)
    safe = [f'"{t.replace(chr(34), "")}"' if t[0] in "-/" else t for t in tokens]
    return " ".join(safe)


class WindowsProcessHelper:
    """Spawns processes on the interactive desktop (WinSta0\\Default) so es.exe can reach Everything's IPC window."""

    class STARTUPINFO(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.c_char_p),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", ctypes.c_void_p),
            ("bInheritHandle", wintypes.BOOL),
        ]

    @classmethod
    def launch_background_app(cls, cmd: str) -> bool:
        """Launch a GUI / background application on WinSta0\\Default without blocking."""
        kernel32 = ctypes.windll.kernel32
        si = cls.STARTUPINFO()
        si.cb = ctypes.sizeof(cls.STARTUPINFO)
        si.lpDesktop = "WinSta0\\Default"
        si.dwFlags = 0x00000001  # STARTF_USESHOWWINDOW
        si.wShowWindow = 0       # SW_HIDE
        pi = cls.PROCESS_INFORMATION()

        res = kernel32.CreateProcessW(None, cmd, None, None, False, 0, None, None, ctypes.byref(si), ctypes.byref(pi))
        if res:
            kernel32.CloseHandle(pi.hProcess)
            kernel32.CloseHandle(pi.hThread)
            return True
        return False

    @classmethod
    def run_cmd(cls, cmd: str, timeout_sec: int = 10) -> tuple[int, str, str]:
        """Run a command targeting WinSta0\\Default with stdout/stderr capture."""
        kernel32 = ctypes.windll.kernel32
        h_read_pipe = wintypes.HANDLE()
        h_write_pipe = wintypes.HANDLE()

        sa = cls.SECURITY_ATTRIBUTES()
        sa.nLength = ctypes.sizeof(cls.SECURITY_ATTRIBUTES)
        sa.bInheritHandle = True

        if not kernel32.CreatePipe(ctypes.byref(h_read_pipe), ctypes.byref(h_write_pipe), ctypes.byref(sa), 0):
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, shell=False)
            return proc.returncode, proc.stdout, proc.stderr

        kernel32.SetHandleInformation(h_read_pipe, 1, 0)

        si = cls.STARTUPINFO()
        si.cb = ctypes.sizeof(cls.STARTUPINFO)
        si.lpDesktop = "WinSta0\\Default"
        si.dwFlags = 0x00000101  # STARTF_USESTDHANDLES | STARTF_USESHOWWINDOW
        si.wShowWindow = 0       # SW_HIDE
        si.hStdOutput = h_write_pipe
        si.hStdError = h_write_pipe

        pi = cls.PROCESS_INFORMATION()

        res = kernel32.CreateProcessW(None, cmd, None, None, True, 0, None, None, ctypes.byref(si), ctypes.byref(pi))
        kernel32.CloseHandle(h_write_pipe)

        if not res:
            kernel32.CloseHandle(h_read_pipe)
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec, shell=False)
            return proc.returncode, proc.stdout, proc.stderr

        wait_res = kernel32.WaitForSingleObject(pi.hProcess, int(timeout_sec * 1000))
        if wait_res != 0:
            kernel32.TerminateProcess(pi.hProcess, 1)

        exit_code = wintypes.DWORD()
        kernel32.GetExitCodeProcess(pi.hProcess, ctypes.byref(exit_code))
        kernel32.CloseHandle(pi.hProcess)
        kernel32.CloseHandle(pi.hThread)

        fd = msvcrt.open_osfhandle(h_read_pipe.value, 0)
        with open(fd, "r", encoding="utf-8", errors="replace") as f:
            output = f.read()

        return exit_code.value, output, ""


class EverythingSearcher:
    """Main searcher querying voidtools Everything with auto-launch support."""

    def __init__(self, es_path: Optional[str] = None):
        self.es_path = self._resolve_es_path(es_path)
        self.everything_exe = self._resolve_everything_exe()

    @staticmethod
    def _resolve_es_path(custom_path: Optional[str] = None) -> str:
        """Find the path to es.exe binary, downloading to local cache if not found."""
        if custom_path and os.path.isfile(custom_path):
            return custom_path

        env_path = os.environ.get("EVERYTHING_ES_PATH")
        if env_path and os.path.isfile(env_path):
            return env_path

        # Check system PATH
        system_es = shutil.which("es.exe") or shutil.which("es")
        if system_es:
            return system_es

        # Check standard Everything directories
        defaults = [
            r"C:\Program Files\Everything\es.exe",
            r"C:\Program Files (x86)\Everything\es.exe",
        ]
        for p in defaults:
            if os.path.isfile(p):
                return p

        # Check user local appdata cache
        local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        cache_dir = os.path.join(local_appdata, "everything-mcp")
        cached_es = os.path.join(cache_dir, "es.exe")
        if os.path.isfile(cached_es):
            return cached_es

        # Download es.exe automatically to local cache on first use
        try:
            os.makedirs(cache_dir, exist_ok=True)
            url = "https://www.voidtools.com/es.zip"
            req = urllib.request.Request(url, headers={"User-Agent": "Everything-MCP/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                for name in z.namelist():
                    if name.lower().endswith("es.exe"):
                        with open(cached_es, "wb") as out_f:
                            out_f.write(z.read(name))
                        return cached_es
        except Exception as e:
            raise FileNotFoundError(
                f"Could not locate or automatically download 'es.exe': {e}. "
                "Please download es.exe from voidtools.com or set the EVERYTHING_ES_PATH environment variable."
            )

        raise FileNotFoundError(
            "Could not locate 'es.exe'. Please set the EVERYTHING_ES_PATH environment variable."
        )

    @staticmethod
    def _resolve_everything_exe() -> Optional[str]:
        """Detect the main Everything.exe application path."""
        env_exe = os.environ.get("EVERYTHING_EXE_PATH")
        if env_exe and os.path.isfile(env_exe):
            return env_exe

        candidates = [
            r"C:\Program Files\Everything\Everything.exe",
            r"C:\Program Files (x86)\Everything\Everything.exe",
            r"C:\Program Files\Everything 1.5a\Everything64.exe",
            r"C:\Program Files\Everything 1.5a\Everything.exe",
        ]
        for path in candidates:
            if os.path.isfile(path):
                return path

        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\voidtools\Everything") as key:
                install_loc, _ = winreg.QueryValueEx(key, "InstallLocation")
                cand = os.path.join(install_loc, "Everything.exe")
                if os.path.isfile(cand):
                    return cand
        except Exception:
            pass

        return None

    def is_everything_running(self) -> tuple[bool, str]:
        """Check if Everything desktop service is active and responding to IPC."""
        cmd = f'"{self.es_path}" -get-everything-version'
        code, out, err = WindowsProcessHelper.run_cmd(cmd, timeout_sec=3)
        if code == 0 and out.strip():
            return True, f"Everything v{out.strip()}"
        if "Error 8" in out or "IPC window not found" in out:
            return False, "Everything is not running or IPC window not found."
        return False, out.strip() or err.strip() or "Unknown status"

    def ensure_running(self) -> bool:
        """Ensure Everything is running. If not, auto-launch it in the background."""
        running, _ = self.is_everything_running()
        if running:
            return True

        if not self.everything_exe:
            return False

        # Launch silently minimized to tray
        cmd = f'"{self.everything_exe}" -startup'
        WindowsProcessHelper.launch_background_app(cmd)

        # Wait up to 3 seconds for IPC to initialize
        for _ in range(12):
            time.sleep(0.25)
            running, _ = self.is_everything_running()
            if running:
                return True

        return False

    def search(
        self,
        query: str,
        max_results: int = 50,
        path: Optional[str] = None,
        files_only: bool = False,
        folders_only: bool = False,
        sort: str = "name",
        sort_descending: bool = False,
        case_sensitive: bool = False,
        whole_word: bool = False,
        regex: bool = False,
    ) -> List[Dict[str, Any]]:
        """Execute a search query against Everything and return parsed records.

        If Everything is not running, attempts to auto-launch it in background.
        """
        # Ensure Everything is active (auto-launch if closed)
        if not self.ensure_running():
            raise RuntimeError(
                "Everything is not running and could not be auto-launched. "
                "Please verify that Everything is installed on this PC."
            )

        args = [
            f'"{self.es_path}"',
            "-csv",
            "-size",
            "-date-modified",
            "-date-format 1",  # ISO-8601
            "-size-format 1",  # Bytes
            f"-n {max(1, min(max_results, 500))}",
        ]

        if files_only and not folders_only:
            args.append("/a-d")
        elif folders_only and not files_only:
            args.append("/ad")

        if path:
            # Windows paths cannot contain quotes; removing them stops breaking out of the argument
            clean_path = str(path).replace('"', "").strip("' ")
            args.append(f'-path "{clean_path}"')

        if case_sensitive:
            args.append("-case")
        if whole_word:
            args.append("-whole-word")
        if regex:
            args.append("-regex")

        valid_sorts = ["name", "path", "size", "extension", "date-modified"]
        if sort and sort in valid_sorts:
            order = "-descending" if sort_descending else "-ascending"
            args.append(f"-sort {sort}{order}")

        clean_query = escape_switches(query.strip())
        if clean_query:
            args.append(clean_query)

        full_cmd = " ".join(args)
        code, out, _ = WindowsProcessHelper.run_cmd(full_cmd, timeout_sec=8)

        if "Error 8" in out or "IPC window not found" in out:
            raise RuntimeError("Everything IPC window not available.")

        results: List[Dict[str, Any]] = []
        if not out.strip():
            return results

        reader = csv.DictReader(io.StringIO(out.strip()))
        for row in reader:
            filename = row.get("Filename", "")
            raw_size = row.get("Size", "").strip()
            date_mod = row.get("Date Modified", "").strip()

            is_folder = raw_size == ""
            size_int = int(raw_size) if raw_size.isdigit() else None

            results.append({
                "path": filename,
                "name": os.path.basename(filename.rstrip("\\/")) if filename else "",
                "is_directory": is_folder,
                "size_bytes": size_int,
                "size_formatted": format_bytes(size_int),
                "date_modified": date_mod,
            })

        return results
