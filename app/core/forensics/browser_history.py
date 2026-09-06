"""
استخراج سجل زيارات المواقع من متصفحات Chrome وEdge وFirefox.

ملاحظة: أثناء عمل المتصفح تكون قاعدة بيانات السجل (History / places.sqlite)
مقفلة، لذا يتم نسخها إلى ملف مؤقت قبل فتحها للقراءة فقط دون التأثير على
المتصفح أو تعديل الدليل الأصلي إطلاقاً (مبدأ عدم المساس بالدليل).
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict

CHROMIUM_EPOCH = datetime(1601, 1, 1)


def _chromium_time_to_str(value: int) -> str:
    if not value:
        return "N/A"
    try:
        return (CHROMIUM_EPOCH + timedelta(microseconds=value)).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"


def _firefox_time_to_str(value: int) -> str:
    if not value:
        return "N/A"
    try:
        return datetime.utcfromtimestamp(value / 1_000_000).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "N/A"


def _copy_and_query(db_path: str, query: str) -> List[tuple]:
    if not os.path.isfile(db_path):
        return []
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".sqlite")
    os.close(tmp_fd)
    try:
        shutil.copy2(db_path, tmp_path)
        conn = sqlite3.connect(f"file:{tmp_path}?mode=ro", uri=True)
        try:
            cursor = conn.execute(query)
            rows = cursor.fetchall()
        finally:
            conn.close()
        return rows
    except Exception:
        return []
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def _chromium_history(base_profile_dir: str, browser_label: str) -> List[Dict]:
    entries: List[Dict] = []
    if not os.path.isdir(base_profile_dir):
        return entries

    for profile in os.listdir(base_profile_dir):
        history_path = os.path.join(base_profile_dir, profile, "History")
        if not os.path.isfile(history_path):
            continue
        rows = _copy_and_query(
            history_path,
            "SELECT url, title, visit_count, last_visit_time "
            "FROM urls ORDER BY last_visit_time DESC LIMIT 300",
        )
        for url, title, visit_count, last_visit_time in rows:
            entries.append(
                {
                    "browser": browser_label,
                    "profile": profile,
                    "url": url,
                    "title": title or "",
                    "visit_count": visit_count,
                    "last_visit": _chromium_time_to_str(last_visit_time),
                }
            )
    return entries


def _get_chrome_history() -> List[Dict]:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    base_dir = os.path.join(local_app_data, "Google", "Chrome", "User Data")
    return _chromium_history(base_dir, "Chrome")


def _get_edge_history() -> List[Dict]:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    base_dir = os.path.join(local_app_data, "Microsoft", "Edge", "User Data")
    return _chromium_history(base_dir, "Edge")


def _get_firefox_history() -> List[Dict]:
    entries: List[Dict] = []
    app_data = os.environ.get("APPDATA", "")
    profiles_dir = os.path.join(app_data, "Mozilla", "Firefox", "Profiles")
    if not os.path.isdir(profiles_dir):
        return entries

    for profile in os.listdir(profiles_dir):
        places_path = os.path.join(profiles_dir, profile, "places.sqlite")
        if not os.path.isfile(places_path):
            continue
        rows = _copy_and_query(
            places_path,
            "SELECT url, title, visit_count, last_visit_date "
            "FROM moz_places ORDER BY last_visit_date DESC LIMIT 300",
        )
        for url, title, visit_count, last_visit_date in rows:
            entries.append(
                {
                    "browser": "Firefox",
                    "profile": profile,
                    "url": url,
                    "title": title or "",
                    "visit_count": visit_count or 0,
                    "last_visit": _firefox_time_to_str(last_visit_date),
                }
            )
    return entries


def get_all_browser_history() -> List[Dict]:
    """يجمع سجل التصفح من كل المتصفحات المدعومة ويرتبه من الأحدث إلى الأقدم."""
    all_entries = _get_chrome_history() + _get_edge_history() + _get_firefox_history()
    all_entries.sort(key=lambda e: e["last_visit"], reverse=True)
    return all_entries
