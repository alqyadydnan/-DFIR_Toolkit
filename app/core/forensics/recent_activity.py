"""Recent Files and Jump Lists collection for Windows.

Recent .lnk files are resolved through the Windows Shell when pywin32 is
available. Jump Lists are treated as forensic metadata: the collector records
file metadata and extracts readable Windows paths/URLs from the binary files as
best-effort indicators without modifying them.
"""
from __future__ import annotations

import os
import re
import struct
from datetime import datetime
from typing import Dict, List


def _dt(path: str) -> str:
    try:
        return datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"


def _resolve_lnk(path: str) -> Dict[str, str]:
    result = {"target": "N/A", "arguments": "", "working_dir": ""}
    try:
        import win32com.client  # pywin32
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(path)
        result["target"] = shortcut.Targetpath or "N/A"
        result["arguments"] = shortcut.Arguments or ""
        result["working_dir"] = shortcut.WorkingDirectory or ""
    except Exception:
        pass
    return result


def get_recent_files(max_items: int = 1000) -> List[Dict]:
    root = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Recent")
    results: List[Dict] = []
    if not os.path.isdir(root):
        return results
    try:
        names = os.listdir(root)
    except Exception:
        return results
    links = [os.path.join(root, n) for n in names if n.lower().endswith(".lnk")]
    links.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
    for path in links[:max_items]:
        resolved = _resolve_lnk(path)
        results.append({
            "name": os.path.basename(path),
            "target": resolved["target"],
            "arguments": resolved["arguments"],
            "modified": _dt(path),
            "source": "Windows Recent (.lnk)",
            "evidence_path": path,
        })
    return results


def _extract_strings(data: bytes) -> List[str]:
    candidates: List[str] = []
    # UTF-16LE strings commonly contain paths in Jump Lists.
    for match in re.findall(rb"(?:[A-Za-z]:|\\\\)[^\x00\r\n]{4,300}\x00\x00", data):
        try:
            text = match.decode("utf-16le", errors="ignore").strip("\x00 ")
            if "\\" in text or "://" in text:
                candidates.append(text)
        except Exception:
            pass
    # ASCII URLs/paths as a fallback.
    for match in re.findall(rb"(?:https?://|[A-Za-z]:\\)[^\x00\r\n]{4,300}", data):
        try:
            text = match.decode("utf-8", errors="ignore").strip()
            candidates.append(text)
        except Exception:
            pass
    unique = []
    seen = set()
    for value in candidates:
        if value not in seen:
            seen.add(value)
            unique.append(value)
    return unique[:50]


def get_jump_lists(max_files: int = 500) -> List[Dict]:
    roots = [
        os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Recent", "AutomaticDestinations"),
        os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Recent", "CustomDestinations"),
    ]
    results: List[Dict] = []
    for root in roots:
        if not os.path.isdir(root):
            continue
        try:
            names = os.listdir(root)
        except Exception:
            continue
        files = [os.path.join(root, n) for n in names if n.lower().endswith((".automaticdestinations-ms", ".customdestinations-ms"))]
        files.sort(key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0, reverse=True)
        for path in files[:max_files]:
            try:
                with open(path, "rb") as handle:
                    data = handle.read()
                strings = _extract_strings(data)
                size = os.path.getsize(path)
            except Exception:
                continue
            results.append({
                "file": os.path.basename(path),
                "type": "Automatic Destinations" if ".automaticdestinations-" in path.lower() else "Custom Destinations",
                "modified": _dt(path),
                "size_kb": round(size / 1024, 1),
                "paths": " | ".join(strings) if strings else "لا توجد مسارات قابلة للاستخراج بشكل موثوق",
                "source": path,
            })
    return results
