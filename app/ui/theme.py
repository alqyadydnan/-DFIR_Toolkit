"""
إعدادات المظهر الموحد (Modern Dark Theme) لتطبيق التحقيق الجنائي الرقمي.
كل الألوان والخطوط المستخدمة في الشاشات تُسحب من هنا حتى يبقى الشكل متناسقاً.
"""

import customtkinter as ctk

# ---------------------------------------------------------------------------
# لوحة الألوان الرئيسية
# ---------------------------------------------------------------------------
COLOR_BG_DARKEST = "#0d1117"       # خلفية النافذة الرئيسية
COLOR_BG_SIDEBAR = "#111826"       # خلفية الشريط الجانبي
COLOR_BG_PANEL = "#161d2b"         # خلفية البطاقات واللوحات
COLOR_BG_PANEL_ALT = "#1c2333"     # خلفية بديلة (صفوف الجداول الفردية مثلاً)
COLOR_BORDER = "#242c3d"           # لون الحدود الخفيفة

COLOR_ACCENT = "#3b82f6"           # اللون الأساسي (أزرق)
COLOR_ACCENT_HOVER = "#2563eb"
COLOR_ACCENT_SOFT = "#1e293b"

COLOR_SUCCESS = "#22c55e"
COLOR_WARNING = "#f59e0b"
COLOR_DANGER = "#ef4444"
COLOR_INFO = "#38bdf8"

COLOR_TEXT_PRIMARY = "#e5e7eb"
COLOR_TEXT_SECONDARY = "#9ca3af"
COLOR_TEXT_MUTED = "#6b7280"

FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"


def apply_global_theme():
    """يضبط وضع الألوان العام لمكتبة CustomTkinter قبل إنشاء أي نافذة."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


def title_font(size: int = 20, weight: str = "bold"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def body_font(size: int = 13, weight: str = "normal"):
    return ctk.CTkFont(family=FONT_FAMILY, size=size, weight=weight)


def mono_font(size: int = 12):
    return ctk.CTkFont(family=FONT_FAMILY_MONO, size=size)


def severity_color(level: str) -> str:
    """يعيد لوناً مناسباً لمستوى الخطورة المستخدم في مركز التهديدات."""
    level = (level or "").lower()
    mapping = {
        "critical": COLOR_DANGER,
        "high": COLOR_DANGER,
        "medium": COLOR_WARNING,
        "low": COLOR_INFO,
        "info": COLOR_TEXT_SECONDARY,
    }
    return mapping.get(level, COLOR_TEXT_SECONDARY)
