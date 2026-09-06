"""
معلومات عامة عن النظام + التحقق من صلاحيات المسؤول (Admin / Elevated).
هذه المعلومات تظهر في الشريط العلوي (Header) للتطبيق.
"""

from __future__ import annotations

import os
import platform
import socket
import getpass
from datetime import datetime


def is_admin() -> bool:
    """يتحقق ما إذا كان التطبيق يعمل بصلاحيات مسؤول على ويندوز."""
    try:
        import ctypes  # noqa: WPS433 (مسموح هنا لأننا نحتاجه فقط عند الفحص)

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        # في حال لم تكن المكتبة متاحة (مثلاً أثناء التطوير على غير ويندوز)
        return False


def get_system_summary() -> dict:
    """يجمع معلومات أساسية عن الجهاز والنظام لعرضها في الهيدر ولوحة التحكم."""
    try:
        hostname = socket.gethostname()
    except Exception:
        hostname = "UNKNOWN-HOST"

    try:
        username = getpass.getuser()
    except Exception:
        username = "unknown"

    try:
        os_version = f"{platform.system()} {platform.release()} ({platform.version()})"
    except Exception:
        os_version = platform.platform()

    return {
        "hostname": hostname,
        "username": username,
        "os_version": os_version,
        "architecture": platform.machine(),
        "processor": platform.processor() or "N/A",
        "boot_scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "is_admin": is_admin(),
        "system_drive": os.environ.get("SystemDrive", "C:"),
        "windir": os.environ.get("WINDIR", r"C:\Windows"),
    }
