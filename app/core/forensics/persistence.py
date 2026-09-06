"""
استخراج نقاط "الثبات" (Persistence) التي يستخدمها أي برنامج - أو برمجية
خبيثة - ليبقى يعمل تلقائياً بعد إعادة التشغيل:
  - مفاتيح Run / RunOnce في الريجستري (HKLM و HKCU)
  - الخدمات (Services) المسجلة على النظام
  - المهام المجدولة (Scheduled Tasks) عبر schtasks
"""

from __future__ import annotations

import subprocess
from typing import List, Dict

try:
    import winreg
except ImportError:
    winreg = None

RUN_KEYS = [
    (winreg.HKEY_LOCAL_MACHINE if winreg else None,
     r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_LOCAL_MACHINE if winreg else None,
     r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
    (winreg.HKEY_CURRENT_USER if winreg else None,
     r"Software\Microsoft\Windows\CurrentVersion\Run"),
    (winreg.HKEY_CURRENT_USER if winreg else None,
     r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
]

_HIVE_LABELS = {
    "HKEY_LOCAL_MACHINE": "HKLM",
    "HKEY_CURRENT_USER": "HKCU",
}


def _run(cmd: list) -> str:
    try:
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        return completed.stdout or ""
    except Exception:
        return ""


def get_registry_autoruns() -> List[Dict]:
    """يقرأ مفاتيح Run/RunOnce في HKLM وHKCU ويعيد قائمة ببرامج بدء التشغيل."""
    results: List[Dict] = []
    if winreg is None:
        return results

    for hive, sub_path in RUN_KEYS:
        hive_name = "HKEY_LOCAL_MACHINE" if hive == winreg.HKEY_LOCAL_MACHINE else "HKEY_CURRENT_USER"
        try:
            key = winreg.OpenKey(hive, sub_path)
        except Exception:
            continue
        try:
            index = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, index)
                except OSError:
                    break
                index += 1
                results.append(
                    {
                        "name": name,
                        "command": value,
                        "location": f"{_HIVE_LABELS.get(hive_name, hive_name)}\\{sub_path}",
                    }
                )
        finally:
            key.Close()

    return results


def get_services() -> List[Dict]:
    """يعيد قائمة خدمات ويندوز الحالية وحالتها (شغّالة/متوقفة) ونوع بدء التشغيل."""
    output = _run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Service | "
         "Select-Object Name,DisplayName,State,StartMode,PathName | "
         "ConvertTo-Csv -NoTypeInformation"]
    )
    results: List[Dict] = []
    lines = [l for l in output.splitlines() if l.strip()]
    if len(lines) < 2:
        return results

    import csv
    import io

    reader = csv.reader(io.StringIO("\n".join(lines)))
    header = next(reader, None)
    for row in reader:
        if len(row) < 5:
            continue
        results.append(
            {
                "name": row[0],
                "display_name": row[1],
                "state": row[2],
                "start_mode": row[3],
                "path": row[4],
            }
        )
    return results


def get_scheduled_tasks() -> List[Dict]:
    """يعيد قائمة المهام المجدولة عبر schtasks."""
    output = _run(["schtasks", "/query", "/fo", "CSV", "/v"])
    results: List[Dict] = []
    lines = [l for l in output.splitlines() if l.strip()]
    if len(lines) < 2:
        return results

    import csv
    import io

    reader = csv.reader(io.StringIO("\n".join(lines)))
    header = next(reader, None)
    if not header:
        return results

    def col(row, name, default=""):
        try:
            return row[header.index(name)]
        except (ValueError, IndexError):
            return default

    seen = set()
    for row in reader:
        task_name = col(row, "TaskName")
        if not task_name or task_name in seen:
            continue
        seen.add(task_name)
        results.append(
            {
                "task_name": task_name,
                "status": col(row, "Status"),
                "next_run": col(row, "Next Run Time"),
                "last_run": col(row, "Last Run Time"),
                "run_as": col(row, "Run As User"),
                "task_to_run": col(row, "Task To Run"),
            }
        )
    return results
