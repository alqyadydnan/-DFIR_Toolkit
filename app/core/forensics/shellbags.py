"""Best-effort ShellBags registry collection.

ShellBags contain shell-item binary data. This collector preserves the raw
registry location and last-write timestamp and extracts readable path-like
strings from binary values. It is deliberately labelled best-effort rather
than pretending to be a complete Shell Item parser.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Dict, List

try:
    import winreg
except ImportError:
    winreg = None

ROOT = r"Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\BagMRU"
ROOT_ALT = r"Software\Microsoft\Windows\Shell\BagMRU"


def _filetime_to_str(filetime: int) -> str:
    try:
        return datetime.fromtimestamp((filetime - 116444736000000000) / 10000000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return "N/A"


def _last_write(key) -> str:
    try:
        return _filetime_to_str(winreg.QueryInfoKey(key)[2])
    except Exception:
        return "N/A"


def _readable_strings(data: bytes) -> List[str]:
    found = []
    for raw in re.findall(rb"[ -~]{4,160}", data):
        text = raw.decode("ascii", errors="ignore")
        if any(x in text.lower() for x in ("\\", ".lnk", ".exe", ".doc", ".pdf", ".zip")):
            found.append(text)
    for raw in re.findall(rb"(?:[ -~]\x00){4,160}", data):
        text = raw.decode("utf-16le", errors="ignore")
        if "\\" in text or ":" in text:
            found.append(text)
    unique, seen = [], set()
    for s in found:
        s = s.strip("\x00 ")
        if s and s not in seen:
            seen.add(s)
            unique.append(s)
    return unique[:20]


def get_shellbags(max_keys: int = 2000) -> List[Dict]:
    results: List[Dict] = []
    if winreg is None:
        return results
    try:
        root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ROOT)
        root_path = ROOT
    except Exception:
        try:
            root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, ROOT_ALT)
            root_path = ROOT_ALT
        except Exception:
            return results

    count = 0
    stack = [(root, root_path)]
    try:
        while stack and count < max_keys:
            key, path = stack.pop()
            try:
                last_write = _last_write(key)
                values = []
                for i in range(winreg.QueryInfoKey(key)[1]):
                    try:
                        name, value, kind = winreg.EnumValue(key, i)
                        if isinstance(value, bytes):
                            decoded = _readable_strings(value)
                            if decoded:
                                values.extend(decoded)
                        elif isinstance(value, str) and value:
                            values.append(value)
                    except Exception:
                        continue
                results.append({
                    "registry_key": path,
                    "last_write": last_write,
                    "mru_values": " | ".join(values) if values else "N/A",
                    "source": "ShellBags / BagMRU",
                })
                count += 1
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        name = winreg.EnumKey(key, i)
                        child = winreg.OpenKey(key, name)
                        stack.append((child, f"{path}\\{name}"))
                    except Exception:
                        continue
            finally:
                key.Close()
    finally:
        # Root may already have been closed if it was popped; avoid double-close errors.
        try:
            root.Close()
        except Exception:
            pass
    return results
