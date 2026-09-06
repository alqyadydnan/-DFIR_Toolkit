"""Read-only Windows Registry explorer helpers."""
from __future__ import annotations

from typing import Dict, List, Tuple

try:
    import winreg
except ImportError:
    winreg = None

HIVES = {
    "HKLM": ("HKEY_LOCAL_MACHINE", lambda: winreg.HKEY_LOCAL_MACHINE),
    "HKCU": ("HKEY_CURRENT_USER", lambda: winreg.HKEY_CURRENT_USER),
    "HKCR": ("HKEY_CLASSES_ROOT", lambda: winreg.HKEY_CLASSES_ROOT),
    "HKU": ("HKEY_USERS", lambda: winreg.HKEY_USERS),
    "HKCC": ("HKEY_CURRENT_CONFIG", lambda: winreg.HKEY_CURRENT_CONFIG),
}


def _root_for(label: str):
    if winreg is None or label not in HIVES:
        return None
    return HIVES[label][1]()


def _type_name(kind: int) -> str:
    mapping = {
        getattr(winreg, "REG_SZ", -1): "REG_SZ",
        getattr(winreg, "REG_EXPAND_SZ", -1): "REG_EXPAND_SZ",
        getattr(winreg, "REG_BINARY", -1): "REG_BINARY",
        getattr(winreg, "REG_DWORD", -1): "REG_DWORD",
        getattr(winreg, "REG_QWORD", -1): "REG_QWORD",
        getattr(winreg, "REG_MULTI_SZ", -1): "REG_MULTI_SZ",
        getattr(winreg, "REG_NONE", -1): "REG_NONE",
    }
    return mapping.get(kind, str(kind))


def _format_value(value, kind: int) -> str:
    if isinstance(value, bytes):
        preview = value[:64].hex(" ")
        suffix = " ..." if len(value) > 64 else ""
        return f"{preview}{suffix}"
    if isinstance(value, list):
        return " | ".join(str(v) for v in value)
    return str(value)


def read_registry_key(hive_label: str, sub_path: str = "") -> Dict:
    """Read a registry key without changing it."""
    if winreg is None:
        return {"error": "هذه الوظيفة متاحة على Windows فقط."}
    root = _root_for(hive_label)
    if root is None:
        return {"error": "Hive غير صالح."}
    clean = sub_path.strip("\\")
    try:
        key = winreg.OpenKey(root, clean, 0, winreg.KEY_READ)
    except Exception as exc:
        return {"error": f"تعذر فتح المفتاح: {exc}"}
    values: List[Dict] = []
    subkeys: List[Dict] = []
    try:
        info = winreg.QueryInfoKey(key)
        last_write = info[2]
        for i in range(info[1]):
            try:
                name, value, kind = winreg.EnumValue(key, i)
                values.append({
                    "name": name or "(Default)",
                    "type": _type_name(kind),
                    "data": _format_value(value, kind),
                })
            except Exception:
                continue
        for i in range(info[0]):
            try:
                subkeys.append({"name": winreg.EnumKey(key, i)})
            except Exception:
                continue
    finally:
        key.Close()
    return {"hive": hive_label, "path": clean, "values": values, "subkeys": subkeys, "last_write_raw": last_write}
