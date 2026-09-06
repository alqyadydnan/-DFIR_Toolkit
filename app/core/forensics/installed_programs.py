"""
استخراج قائمة البرامج المثبتة من مفاتيح Uninstall في الريجستري
(HKLM لكل من 32/64-بت + HKCU للبرامج المثبتة للمستخدم الحالي فقط)
مع تاريخ التثبيت الظاهر واسم الناشر.
"""

from __future__ import annotations

from typing import List, Dict

try:
    import winreg
except ImportError:
    winreg = None

_UNINSTALL_LOCATIONS = [
    (winreg.HKEY_LOCAL_MACHINE if winreg else None,
     r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_LOCAL_MACHINE if winreg else None,
     r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    (winreg.HKEY_CURRENT_USER if winreg else None,
     r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
]


def _fmt_install_date(raw: str) -> str:
    if not raw or len(raw) != 8 or not raw.isdigit():
        return raw or "N/A"
    return f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"


def get_installed_programs() -> List[Dict]:
    """يعيد قائمة البرامج المثبتة مع اسم الناشر وتاريخ التثبيت وإصدار البرنامج."""
    results: List[Dict] = []
    if winreg is None:
        return results

    seen_names = set()

    for hive, sub_path in _UNINSTALL_LOCATIONS:
        try:
            root = winreg.OpenKey(hive, sub_path)
        except Exception:
            continue

        try:
            index = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(root, index)
                except OSError:
                    break
                index += 1

                try:
                    subkey = winreg.OpenKey(root, subkey_name)
                except Exception:
                    continue

                try:
                    def get_val(name, default="N/A"):
                        try:
                            value, _ = winreg.QueryValueEx(subkey, name)
                            return value
                        except Exception:
                            return default

                    display_name = get_val("DisplayName", None)
                    if not display_name:
                        continue
                    if display_name in seen_names:
                        continue
                    seen_names.add(display_name)

                    results.append(
                        {
                            "name": display_name,
                            "publisher": get_val("Publisher"),
                            "version": get_val("DisplayVersion"),
                            "install_date": _fmt_install_date(get_val("InstallDate", "")),
                            "install_location": get_val("InstallLocation"),
                        }
                    )
                finally:
                    subkey.Close()
        finally:
            root.Close()

    results.sort(key=lambda r: r["install_date"], reverse=True)
    return results
