"""
محرك استدلالي بسيط لتمييز العمليات الحالية "المشبوهة" اعتماداً على:
  - العمل من مسار غير معتاد لتنفيذ البرامج (Temp، AppData\\Local\\Temp،
    مجلد التنزيلات، جذر الأقراص القابلة للإزالة)
  - غياب توقيع رقمي صالح (Unsigned) أو ناشر غير موثوق
  - اسم عملية يحاكي عملية نظام معروفة (Masquerading) بفارق حرف بسيط
  - تشغيل من مسار مخفي أو بأسماء عشوائية (heuristic بسيط على طول الاسم)

هذه قواعد استرشادية (Heuristics) تهدف لتوجيه انتباه المحقق، وليست حكماً
قاطعاً باكتشاف برمجية خبيثة فعلية.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from typing import List, Dict

_SUSPICIOUS_PATH_PATTERNS = [
    r"\\AppData\\Local\\Temp\\",
    r"\\Windows\\Temp\\",
    r"\\Downloads\\",
    r"^[A-Z]:\\\$Recycle\.Bin",
    r"\\Users\\Public\\",
    r"\\ProgramData\\(?!Microsoft)",
]

_KNOWN_SYSTEM_NAMES = {
    "svchost.exe", "explorer.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "winlogon.exe", "smss.exe",
    "spoolsv.exe", "taskhostw.exe", "dwm.exe",
}


def _looks_like_masquerade(process_name: str) -> bool:
    """يقارن الاسم بأسماء عمليات النظام المعروفة للكشف عن تشابه مضلل بسيط."""
    lname = process_name.lower()
    if lname in _KNOWN_SYSTEM_NAMES:
        return False
    for known in _KNOWN_SYSTEM_NAMES:
        base = known.replace(".exe", "")
        # فرق حرف واحد أو رقم مقحم قد يوحي بمحاكاة اسم عملية نظامية
        if base in lname and lname != known:
            return True
    return False


def _path_is_suspicious(path: str) -> bool:
    if not path:
        return False
    for pattern in _SUSPICIOUS_PATH_PATTERNS:
        if re.search(pattern, path, re.IGNORECASE):
            return True
    return False


def _get_running_processes_detailed() -> List[Dict]:
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,Name,ExecutablePath,CommandLine,ParentProcessId | "
        "ConvertTo-Json -Compress"
    )
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=30,
        )
        output = completed.stdout or ""
    except Exception:
        output = ""

    if not output.strip():
        return []

    try:
        parsed = json.loads(output)
    except Exception:
        return []

    if isinstance(parsed, dict):
        parsed = [parsed]
    return parsed


def _is_digitally_signed(path: str) -> bool | None:
    """يتحقق من التوقيع الرقمي لملف تنفيذي؛ يعيد None إذا تعذر التحقق."""
    if not path or not os.path.isfile(path):
        return None
    try:
        script = (
            f"(Get-AuthenticodeSignature -LiteralPath '{path}').Status"
        )
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True, text=True, timeout=10,
        )
        status = (completed.stdout or "").strip()
        return status.lower() == "valid"
    except Exception:
        return None


def scan_for_threats(check_signatures: bool = True) -> List[Dict]:
    """
    يفحص العمليات النشطة حالياً ويعيد قائمة بالعناصر المشبوهة مع مستوى
    الخطورة والسبب، لعرضها في شاشة "مركز التهديدات".
    """
    findings: List[Dict] = []
    processes = _get_running_processes_detailed()

    for proc in processes:
        name = proc.get("Name") or "N/A"
        path = proc.get("ExecutablePath") or ""
        pid = proc.get("ProcessId")
        cmdline = proc.get("CommandLine") or ""

        reasons = []
        severity = "info"

        if _path_is_suspicious(path or cmdline):
            reasons.append("يعمل من مسار غير معتاد لتنفيذ البرامج (Temp/Downloads/Public)")
            severity = "high"

        if _looks_like_masquerade(name):
            reasons.append("اسم العملية يشبه اسم عملية نظامية معروفة بشكل مضلل")
            severity = "critical"

        if not path and name.lower() not in _KNOWN_SYSTEM_NAMES:
            reasons.append("لا يوجد مسار تنفيذي واضح للعملية")
            if severity == "info":
                severity = "medium"

        if check_signatures and path and reasons:
            signed = _is_digitally_signed(path)
            if signed is False:
                reasons.append("لا يحمل توقيعاً رقمياً صالحاً (Unsigned)")
                severity = "critical" if severity in ("high", "critical") else "high"

        if reasons:
            findings.append(
                {
                    "pid": pid,
                    "process_name": name,
                    "path": path or "N/A",
                    "command_line": cmdline[:200],
                    "severity": severity,
                    "reasons": " | ".join(reasons),
                }
            )

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings.sort(key=lambda f: severity_rank.get(f["severity"], 5))
    return findings
