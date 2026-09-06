"""
استخراج سجل UserAssist من الريجستري: يحفظه ويندوز لكل برنامج تم تشغيله
من سطح المكتب أو قائمة ابدأ، ويشمل عدد مرات التشغيل وآخر وقت تشغيل.

المسار:
HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\UserAssist\\{GUID}\\Count

أسماء المفاتيح مُشفّرة بـ ROT13، والقيمة الثنائية تحتوي (حسب الإصدار) على
عداد التشغيل ووقت آخر تشغيل (FILETIME) ضمن أوفستات معروفة توثيقياً.
"""

from __future__ import annotations

import codecs
import struct
from datetime import datetime, timedelta
from typing import List, Dict

try:
    import winreg
except ImportError:  # بيئة غير ويندوز (تطوير فقط)
    winreg = None

USERASSIST_PATH = (
    r"Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist"
)


def _rot13(value: str) -> str:
    return codecs.decode(value, "rot_13")


def _filetime_to_datetime(filetime: int) -> str:
    if filetime <= 0:
        return "N/A"
    try:
        # فاصل 1601-01-01 حتى 1970-01-01 بوحدة 100 نانوثانية
        EPOCH_AS_FILETIME = 116444736000000000
        HUNDREDS_OF_NS = 10000000
        unix_time = (filetime - EPOCH_AS_FILETIME) / HUNDREDS_OF_NS
        return datetime.utcfromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return "N/A"


def get_userassist_entries() -> List[Dict]:
    """يعيد قائمة بمدخلات UserAssist المفكوكة مع عدد التشغيل وآخر وقت تشغيل إن توفر."""
    results: List[Dict] = []

    if winreg is None:
        return results

    try:
        root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, USERASSIST_PATH)
    except Exception:
        return results

    try:
        guid_index = 0
        while True:
            try:
                guid = winreg.EnumKey(root, guid_index)
            except OSError:
                break
            guid_index += 1

            count_path = f"{USERASSIST_PATH}\\{guid}\\Count"
            try:
                count_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, count_path)
            except Exception:
                continue

            try:
                value_index = 0
                while True:
                    try:
                        name, raw_value, _ = winreg.EnumValue(count_key, value_index)
                    except OSError:
                        break
                    value_index += 1

                    try:
                        decoded_name = _rot13(name)
                    except Exception:
                        decoded_name = name

                    # تجاهل مفاتيح الفولدر/الحاويات غير المفيدة للتحقيق
                    if decoded_name.startswith("{") or "\\" not in decoded_name:
                        continue

                    run_count = "N/A"
                    last_run = "N/A"
                    try:
                        if len(raw_value) >= 16:
                            # التنسيق الحديث (Vista وما بعده): عداد التشغيل عند الأوفست 4
                            # ووقت آخر تشغيل (FILETIME 8 بايت) عند الأوفست 60 تقريباً
                            run_count = struct.unpack("<I", raw_value[4:8])[0]
                            if len(raw_value) >= 68:
                                filetime = struct.unpack("<Q", raw_value[60:68])[0]
                                last_run = _filetime_to_datetime(filetime)
                    except Exception:
                        pass

                    results.append(
                        {
                            "program_path": decoded_name,
                            "run_count": run_count,
                            "last_run": last_run,
                            "source": f"UserAssist\\{guid}",
                        }
                    )
            finally:
                count_key.Close()
    finally:
        root.Close()

    return results
