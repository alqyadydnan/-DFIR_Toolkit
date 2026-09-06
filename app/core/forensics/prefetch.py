"""
استخراج أدلة "البرامج التي تم تشغيلها" من مجلد Prefetch الخاص بويندوز.

ملاحظة منهجية مهمة:
ملفات Prefetch (.pf) مضغوطة بصيغة خاصة (MAM/XPRESS) يختلف تنسيقها الداخلي
باختلاف إصدار ويندوز. لتفادي الاعتماد على مكتبات تفكيك ضغط خارجية غير
مضمونة التوفر في كل بيئة، تعتمد هذه الوحدة على البيانات الوصفية الموثوقة
والمتاحة دائماً من نظام الملفات نفسه لكل ملف .pf:

  - اسم التنفيذي الأصلي (من اسم ملف الـ Prefetch نفسه، مثل NOTEPAD.EXE-XXXXXXXX.pf)
  - تاريخ الإنشاء لملف الـ Prefetch  -> يقارب "أول مرة شوهد فيها البرنamج يعمل"
  - تاريخ آخر تعديل لملف الـ Prefetch -> "آخر مرة تم تشغيل البرنامج فيها"
  - حجم الملف كمؤشر تقريبي، ورقم الهاش اللاحق للاسم

هذا أسلوب معتمد وشائع في أدوات DFIR الخفيفة عندما لا تتوفر مكتبة تفكيك
مخصصة، ويبقى النظام قابلاً للتوسعة لاحقاً بربط محلل .pf كامل إن رغب المحقق.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import List, Dict

PREFETCH_DIR = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Prefetch")

_NAME_HASH_RE = re.compile(r"^(?P<name>.+)-(?P<hash>[0-9A-Fa-f]{8})\.pf$")


def _fmt(ts: float) -> str:
    try:
        return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"


def get_prefetch_executions() -> List[Dict]:
    """يعيد قائمة بكل ملفات Prefetch الموجودة مع البيانات الوصفية المستخرجة منها."""
    results: List[Dict] = []

    if not os.path.isdir(PREFETCH_DIR):
        return results

    try:
        entries = os.listdir(PREFETCH_DIR)
    except PermissionError:
        return results
    except Exception:
        return results

    for filename in entries:
        if not filename.lower().endswith(".pf"):
            continue

        full_path = os.path.join(PREFETCH_DIR, filename)
        match = _NAME_HASH_RE.match(filename)
        exe_name = match.group("name") if match else filename
        pf_hash = match.group("hash") if match else "N/A"

        try:
            stat = os.stat(full_path)
        except Exception:
            continue

        results.append(
            {
                "executable": exe_name,
                "prefetch_hash": pf_hash,
                "prefetch_file": filename,
                "first_seen": _fmt(stat.st_ctime),
                "last_run": _fmt(stat.st_mtime),
                "size_kb": round(stat.st_size / 1024, 1),
                "full_path": full_path,
            }
        )

    # الأحدث تشغيلاً أولاً
    results.sort(key=lambda r: r["last_run"], reverse=True)
    return results
