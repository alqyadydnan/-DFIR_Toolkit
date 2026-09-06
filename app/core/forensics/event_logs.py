"""
استخراج سجلات الأحداث الأمنية المهمة للتحقيق الجنائي، أبرزها:
  - Event ID 4688: إنشاء عملية جديدة (Process Creation)
  - Event ID 4624/4625: تسجيل دخول ناجح/فاشل
  - Event ID 1102: مسح سجل الأحداث الأمني (دليل على محاولة إخفاء آثار)

يُستخدم PowerShell (Get-WinEvent) لتفادي أي متطلبات تثبيت إضافية،
مع قراءة فقط (لا يتم حذف أو تعديل أي سجل إطلاقاً).
"""

from __future__ import annotations

import json
import subprocess
from typing import List, Dict

_INTERESTING_EVENT_IDS = {
    4688: "إنشاء عملية جديدة",
    4624: "تسجيل دخول ناجح",
    4625: "محاولة تسجيل دخول فاشلة",
    1102: "تم مسح سجل الأحداث الأمني (مؤشر خطير)",
    4720: "إنشاء حساب مستخدم جديد",
}


def _run_powershell(script: str) -> str:
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=40,
        )
        return completed.stdout or ""
    except Exception:
        return ""


def get_security_events(max_events: int = 200) -> List[Dict]:
    """يجلب أحدث الأحداث الأمنية ذات الأهمية الجنائية من سجل Security."""
    ids_filter = ",".join(str(i) for i in _INTERESTING_EVENT_IDS)
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"Get-WinEvent -FilterHashtable @{{LogName='Security'; Id={ids_filter}}} "
        f"-MaxEvents {max_events} | "
        "Select-Object Id,TimeCreated,@{N='Message';E={$_.Message -replace \"`r`n\",' '}} | "
        "ConvertTo-Json -Compress"
    )
    output = _run_powershell(script)
    results: List[Dict] = []
    if not output.strip():
        return results

    try:
        parsed = json.loads(output)
    except Exception:
        return results

    if isinstance(parsed, dict):
        parsed = [parsed]

    for item in parsed:
        event_id = item.get("Id")
        message = (item.get("Message") or "")[:400]
        results.append(
            {
                "event_id": event_id,
                "description": _INTERESTING_EVENT_IDS.get(event_id, "حدث آخر"),
                "time_created": item.get("TimeCreated"),
                "message": message,
            }
        )
    return results


def get_application_errors(max_events: int = 100) -> List[Dict]:
    """يجلب أحدث أخطاء وتحذيرات سجل التطبيقات (Application) للمساعدة في تتبع الأعطال."""
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"Get-WinEvent -FilterHashtable @{{LogName='Application'; Level=1,2,3}} "
        f"-MaxEvents {max_events} | "
        "Select-Object Id,LevelDisplayName,ProviderName,TimeCreated,"
        "@{N='Message';E={$_.Message -replace \"`r`n\",' '}} | "
        "ConvertTo-Json -Compress"
    )
    output = _run_powershell(script)
    results: List[Dict] = []
    if not output.strip():
        return results

    try:
        parsed = json.loads(output)
    except Exception:
        return results

    if isinstance(parsed, dict):
        parsed = [parsed]

    for item in parsed:
        results.append(
            {
                "event_id": item.get("Id"),
                "level": item.get("LevelDisplayName"),
                "provider": item.get("ProviderName"),
                "time_created": item.get("TimeCreated"),
                "message": (item.get("Message") or "")[:400],
            }
        )
    return results


def get_system_events(max_events: int = 100) -> List[Dict]:
    """Read important System events such as service installation (7045)."""
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"Get-WinEvent -FilterHashtable @{{LogName='System';Id=7045}} -MaxEvents {max_events} | "
        "Select-Object Id,TimeCreated,ProviderName,@{N='Message';E={$_.Message -replace \"`r`n\",' '}} | "
        "ConvertTo-Json -Compress"
    )
    output = _run_powershell(script)
    if not output.strip():
        return []
    try:
        parsed = json.loads(output)
    except Exception:
        return []
    if isinstance(parsed, dict):
        parsed = [parsed]
    return [{
        "event_id": x.get("Id"),
        "description": "تثبيت خدمة جديدة",
        "time_created": x.get("TimeCreated"),
        "message": (x.get("Message") or "")[:400],
        "source": "System",
    } for x in parsed]
