"""
نقطة تشغيل التطبيق.

التطبيق مصمم ليعمل بالكامل عبر الواجهة الرسومية (100% GUI-driven):
لا توجد أي مدخلات أو مخرجات عبر الطرفية (Console/CLI) في أي مرحلة،
بما في ذلك اسم القضية عند بدء التشغيل الذي يُطلب عبر نافذة منبثقة.

طريقة التشغيل:
    python main.py
(يُفضّل تشغيله بصلاحيات "مسؤول" على ويندوز للحصول على كل الأدلة الممكنة،
لكنه يعمل أيضاً بدون تلك الصلاحيات مع تقليص بعض المصادر فقط)
"""

from __future__ import annotations

import sys

import customtkinter as ctk

from app.ui import theme
from app.ui.main_window import MainWindow
from app.core.system_info import is_admin


class StartupDialog(ctk.CTk):
    """نافذة بدء صغيرة لطلب اسم القضية قبل فتح التطبيق الرئيسي (بديل GUI عن input())."""

    def __init__(self):
        super().__init__()
        self.title("بدء تحقيق جديد - DFIR Toolkit")
        self.geometry("460x300")
        self.resizable(False, False)
        self.configure(fg_color=theme.COLOR_BG_DARKEST)

        self.case_name_result: str | None = None

        ctk.CTkLabel(
            self, text="🛡️ منصة التحقيق الجنائي الرقمي", font=theme.title_font(19),
            text_color=theme.COLOR_TEXT_PRIMARY,
        ).pack(pady=(28, 4))

        ctk.CTkLabel(
            self, text="أدخل اسم أو رقم القضية لبدء جلسة التحقيق", font=theme.body_font(12),
            text_color=theme.COLOR_TEXT_SECONDARY,
        ).pack(pady=(0, 18))

        self.case_entry = ctk.CTkEntry(
            self, width=320, height=40, justify="center",
            placeholder_text="مثال: CASE-2026-0904",
        )
        self.case_entry.pack(pady=(0, 10))
        self.case_entry.bind("<Return>", lambda _e: self._on_start())

        admin_status = is_admin()
        badge_color = theme.COLOR_SUCCESS if admin_status else theme.COLOR_WARNING
        badge_text = (
            "✔ يعمل التطبيق حالياً بصلاحيات مسؤول"
            if admin_status
            else "⚠ يعمل التطبيق بدون صلاحيات مسؤول (بعض الأدلة قد لا تظهر)"
        )
        ctk.CTkLabel(
            self, text=badge_text, font=theme.body_font(11, "bold"),
            text_color=badge_color,
        ).pack(pady=(4, 18))

        ctk.CTkButton(
            self, text="بدء التحقيق  ▶", width=200, height=42,
            font=theme.body_font(14, "bold"), fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER, command=self._on_start,
        ).pack()

        self.case_entry.focus_set()

    def _on_start(self):
        entered = self.case_entry.get().strip()
        self.case_name_result = entered if entered else "قضية بدون اسم"
        self.destroy()


def main():
    theme.apply_global_theme()

    startup = StartupDialog()
    startup.mainloop()

    case_name = startup.case_name_result or "قضية بدون اسم"

    app = MainWindow(case_name=case_name)
    app.mainloop()


if __name__ == "__main__":
    main()
