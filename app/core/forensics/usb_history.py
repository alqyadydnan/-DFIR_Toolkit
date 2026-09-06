"""Historical USB storage/device artifacts for Windows.

The collector intentionally uses several read-only sources instead of relying
only on USBSTOR.  USBSTOR is the primary artifact for USB mass-storage
history; MountedDevices, device-enumeration keys and SetupAPI are used as
additional corroboration when available.
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Dict, List

try:
    import winreg
except ImportError:  # pragma: no cover - non-Windows development
    winreg = None

USBSTOR_PATH = r"SYSTEM\CurrentControlSet\Enum\USBSTOR"
USB_PATH = r"SYSTEM\CurrentControlSet\Enum\USB"
MOUNTED_DEVICES = r"SYSTEM\MountedDevices"


def _filetime_to_str(filetime: int) -> str:
    if not filetime:
        return "N/A"
    try:
        unix_time = (filetime - 116444736000000000) / 10000000
        return datetime.fromtimestamp(unix_time, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return "N/A"


def _key_last_write_time(key) -> str:
    try:
        _, _, last_write = winreg.QueryInfoKey(key)
        return _filetime_to_str(last_write)
    except Exception:
        return "N/A"


def _enum_subkeys(key):
    index = 0
    while True:
        try:
            yield winreg.EnumKey(key, index)
            index += 1
        except OSError:
            break


def _open_control_set(path: str):
    """Open CurrentControlSet first, then ControlSet001/002 as fallbacks."""
    candidates = [path,
                  path.replace("SYSTEM\\CurrentControlSet\\", "SYSTEM\\ControlSet001\\", 1),
                  path.replace("SYSTEM\\CurrentControlSet\\", "SYSTEM\\ControlSet002\\", 1)]
    for candidate in candidates:
        try:
            return winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, candidate), candidate
        except Exception:
            continue
    return None, None


def _clean_serial(serial: str) -> str:
    # USBSTOR instance IDs may end with &0 or &1. Only remove the known suffix.
    return re.sub(r"&\d+$", "", serial)


def _read_value(key, name: str, default="N/A"):
    try:
        return winreg.QueryValueEx(key, name)[0]
    except Exception:
        return default


def get_usb_history() -> List[Dict]:
    """Return USB storage/device history from multiple Windows artifacts."""
    results: List[Dict] = []
    if winreg is None:
        return results

    seen = set()
    root, source_path = _open_control_set(USBSTOR_PATH)
    if root is not None:
        try:
            for device_class in _enum_subkeys(root):
                try:
                    device_key = winreg.OpenKey(root, device_class)
                except Exception:
                    continue
                try:
                    class_last = _key_last_write_time(device_key)
                    for instance in _enum_subkeys(device_key):
                        try:
                            inst_key = winreg.OpenKey(device_key, instance)
                        except Exception:
                            continue
                        try:
                            friendly = _read_value(inst_key, "FriendlyName", "N/A")
                            device_desc = _read_value(inst_key, "DeviceDesc", "N/A")
                            manufacturer = _read_value(inst_key, "Mfg", "N/A")
                            last_seen = _key_last_write_time(inst_key)
                            key_id = (device_class, instance)
                            if key_id in seen:
                                continue
                            seen.add(key_id)
                            results.append({
                                "device_class": device_class,
                                "friendly_name": friendly if friendly != "N/A" else device_desc,
                                "device_description": device_desc,
                                "manufacturer": manufacturer,
                                "serial_number": _clean_serial(instance),
                                "instance_id": instance,
                                "last_connected": last_seen if last_seen != "N/A" else class_last,
                                "source": "USBSTOR",
                                "evidence_note": "وقت آخر تعديل لمفتاح الجهاز؛ مؤشر زمني وليس إثباتاً قطعياً للاتصال.",
                            })
                        finally:
                            inst_key.Close()
                finally:
                    device_key.Close()
        finally:
            root.Close()

    # Additional generic USB enumeration. This catches devices that are not
    # represented as USB mass storage while keeping the source explicit.
    root, _ = _open_control_set(USB_PATH)
    if root is not None:
        try:
            for vendor in _enum_subkeys(root):
                try:
                    vendor_key = winreg.OpenKey(root, vendor)
                except Exception:
                    continue
                try:
                    for instance in _enum_subkeys(vendor_key):
                        try:
                            inst_key = winreg.OpenKey(vendor_key, instance)
                        except Exception:
                            continue
                        try:
                            friendly = _read_value(inst_key, "FriendlyName", "N/A")
                            desc = _read_value(inst_key, "DeviceDesc", "N/A")
                            if friendly == "N/A" and desc == "N/A":
                                continue
                            key_id = (vendor, instance)
                            if key_id in seen:
                                continue
                            seen.add(key_id)
                            results.append({
                                "device_class": vendor,
                                "friendly_name": friendly if friendly != "N/A" else desc,
                                "device_description": desc,
                                "manufacturer": _read_value(inst_key, "Mfg", "N/A"),
                                "serial_number": instance,
                                "instance_id": instance,
                                "last_connected": _key_last_write_time(inst_key),
                                "source": "USB device enumeration",
                                "evidence_note": "مفتاح تعداد USB؛ التوقيت مبني على Last Write Key.",
                            })
                        finally:
                            inst_key.Close()
                finally:
                    vendor_key.Close()
        finally:
            root.Close()

    # SetupAPI is a useful corroborating source for device-install activity.
    setup_log = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "inf", "setupapi.dev.log")
    if os.path.isfile(setup_log):
        try:
            with open(setup_log, "r", encoding="utf-8", errors="ignore") as handle:
                recent_lines = []
                for line in handle:
                    if "USBSTOR" in line.upper() or "USB\\" in line.upper():
                        recent_lines.append(line.strip())
                for line in recent_lines[-100:]:
                    results.append({
                        "device_class": "SetupAPI",
                        "friendly_name": "Device installation evidence",
                        "device_description": line[:260],
                        "manufacturer": "N/A",
                        "serial_number": "N/A",
                        "instance_id": "N/A",
                        "last_connected": "N/A",
                        "source": "setupapi.dev.log",
                        "evidence_note": "سطر من سجل تثبيت الأجهزة؛ لا يُفسر كتاريخ اتصال دقيق دون سياقه.",
                    })
        except Exception:
            pass

    # Stable ordering: known USBSTOR records first, then corroborating entries.
    results.sort(key=lambda r: (r.get("source") != "USBSTOR", r.get("friendly_name", "")))
    return results


def get_mounted_device_mappings() -> List[Dict]:
    """Read historical drive-letter mappings from MountedDevices."""
    results = []
    if winreg is None:
        return results
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, MOUNTED_DEVICES)
    except Exception:
        return results
    try:
        for i in range(winreg.QueryInfoKey(key)[1]):
            try:
                name, value, kind = winreg.EnumValue(key, i)
                if not str(name).startswith("\\DosDevices\\"):
                    continue
                # Preserve the raw binary identifier; it can be correlated with
                # USB/storage artifacts without pretending it is a serial number.
                raw = value.hex(" ") if isinstance(value, bytes) else str(value)
                results.append({"drive_letter": str(name).split("\\")[-1], "device_data": raw[:180], "source": "MountedDevices"})
            except Exception:
                continue
    finally:
        key.Close()
    return results
