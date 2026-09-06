"""
تسجيل الأخطاء الداخلية في ملف نصي بجانب البرنامج بدلاً من طباعتها على
الطرفية (Console)، حفاظاً على مبدأ "100% واجهة رسومية" للتطبيق بالكامل.
"""

from __future__ import annotations

import os
from datetime import datetime

_LOG_DIR = os.path.join(os.path.expanduser("~"), "DFIR_Toolkit_Logs")
_LOG_FILE = os.path.join(_LOG_DIR, "errors.log")


def log_error(message: str) -> None:
    try:
        os.makedirs(_LOG_DIR, exist_ok=True)
        with open(_LOG_FILE, "a", encoding="utf-8") as handle:
            handle.write(f"\n----- {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} -----\n")
            handle.write(message)
            handle.write("\n")
    except Exception:
        # حتى لو فشل التسجيل نفسه، لا يجب أن يوقف هذا أي جزء من واجهة المستخدم
        pass


def get_log_file_path() -> str:
    return _LOG_FILE
