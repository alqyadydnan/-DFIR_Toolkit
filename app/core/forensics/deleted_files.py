"""
استخراج قائمة الملفات الموجودة حالياً في سلة المحذوفات (Recycle Bin) لكل
الأقراص المتاحة، من خلال ملفات $I (البيانات الوصفية: الاسم الأصلي، تاريخ
الحذف، الحجم) المرتبطة بكل ملف $R (المحتوى الفعلي) داخل $Recycle.Bin.
"""

from __future__ import annotations

import os
import struct
import string
from datetime import datetime
from typing import List, Dict


def _filetime_to_str(filetime: int) -> str:
    if not filetime:
        return "N/A"
    try:
        EPOCH_AS_FILETIME = 116444736000000000
        HUNDREDS_OF_NS = 10000000
        unix_time = (filetime - EPOCH_AS_FILETIME) / HUNDREDS_OF_NS
        return datetime.utcfromtimestamp(unix_time).strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        return "N/A"


def _parse_index_file(index_path: str) -> Dict:
    """يحلل ملف $I لاستخراج الاسم الأصلي وتاريخ الحذف والحجم قبل الحذف."""
    try:
        with open(index_path, "rb") as handle:
            data = handle.read()
    except Exception:
        return {}

    if len(data) < 24:
        return {}

    try:
        # الإصدار 2 (ويندوز 10+): هيدر 8 بايت، حجم 8 بايت، وقت حذف 8 بايت،
        # طول اسم الملف (4 بايت) ثم الاسم نفسه بترميز UTF-16LE
        file_size = struct.unpack("<q", data[8:16])[0]
        deleted_time = struct.unpack("<q", data[16:24])[0]
        name_length = struct.unpack("<i", data[24:28])[0]
        raw_name = data[28:28 + (name_length * 2)]
        original_name = raw_name.decode("utf-16le", errors="ignore").rstrip("\x00")
    except Exception:
        return {}

    return {
        "original_path": original_name,
        "deleted_at": _filetime_to_str(deleted_time),
        "size_kb": round(file_size / 1024, 1) if file_size else 0,
    }


def get_recycle_bin_contents() -> List[Dict]:
    """يفحص $Recycle.Bin على كل الأقراص المتاحة ويعيد قائمة الملفات المحذوفة الحالية."""
    results: List[Dict] = []

    available_drives = [
        f"{letter}:\\" for letter in string.ascii_uppercase
        if os.path.exists(f"{letter}:\\")
    ]

    for drive in available_drives:
        recycle_root = os.path.join(drive, "$Recycle.Bin")
        if not os.path.isdir(recycle_root):
            continue

        try:
            sid_folders = os.listdir(recycle_root)
        except Exception:
            continue

        for sid_folder in sid_folders:
            folder_path = os.path.join(recycle_root, sid_folder)
            if not os.path.isdir(folder_path):
                continue
            try:
                files = os.listdir(folder_path)
            except Exception:
                continue

            for filename in files:
                if not filename.startswith("$I"):
                    continue
                index_path = os.path.join(folder_path, filename)
                meta = _parse_index_file(index_path)
                if not meta:
                    continue

                data_filename = "$R" + filename[2:]
                data_path = os.path.join(folder_path, data_filename)
                still_recoverable = os.path.exists(data_path)

                results.append(
                    {
                        "drive": drive,
                        "owner_sid": sid_folder,
                        "original_path": meta.get("original_path", "N/A"),
                        "deleted_at": meta.get("deleted_at", "N/A"),
                        "size_kb": meta.get("size_kb", 0),
                        "recoverable": "نعم" if still_recoverable else "لا (تم الإفراغ)",
                    }
                )

    results.sort(key=lambda r: r["deleted_at"], reverse=True)
    return results
