"""الشريط العلوي (Header) الذي يظهر في كل شاشات التطبيق."""

from __future__ import annotations

import customtkinter as ctk

from app.ui import theme
from app.core.system_info import get_system_summary


class HeaderBar(ctk.CTkFrame):
    def __init__(self, master, case_name: str = "قضية بدون اسم", **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG_SIDEBAR, corner_radius=0, height=64, **kwargs)
        self.pack_propagate(False)

        summary = get_system_summary()

        # --- الجانب الأيمن: اسم التطبيق واسم القضية ---
        right_frame = ctk.CTkFrame(self, fg_color="transparent")
        right_frame.pack(side="right", padx=20, pady=8)

        ctk.CTkLabel(
            right_frame, text="🛡️ منصة التحقيق الجنائي الرقمي", font=theme.title_font(17),
            text_color=theme.COLOR_TEXT_PRIMARY, anchor="e",
        ).pack(anchor="e")

        self.case_label = ctk.CTkLabel(
            right_frame, text=f"القضية: {case_name}", font=theme.body_font(12),
            text_color=theme.COLOR_TEXT_SECONDARY, anchor="e",
        )
        self.case_label.pack(anchor="e", pady=(2, 0))

        # --- الوسط: معلومات الجهاز ---
        mid_frame = ctk.CTkFrame(self, fg_color="transparent")
        mid_frame.pack(side="right", padx=30, pady=8)

        ctk.CTkLabel(
            mid_frame, text=f"💻 الجهاز: {summary['hostname']}", font=theme.body_font(12),
            text_color=theme.COLOR_TEXT_SECONDARY, anchor="e",
        ).pack(anchor="e")
        ctk.CTkLabel(
            mid_frame, text=f"👤 المستخدم: {summary['username']}", font=theme.body_font(12),
            text_color=theme.COLOR_TEXT_SECONDARY, anchor="e",
        ).pack(anchor="e", pady=(2, 0))

        # --- الجانب الأيسر: شارة صلاحيات المسؤول ---
        badge_color = theme.COLOR_SUCCESS if summary["is_admin"] else theme.COLOR_DANGER
        badge_text = "✔ صلاحيات مسؤول مفعّلة" if summary["is_admin"] else "⚠ بدون صلاحيات مسؤول"

        self.admin_badge = ctk.CTkLabel(
            self, text=badge_text, font=theme.body_font(12, "bold"),
            text_color="#ffffff", fg_color=badge_color, corner_radius=8,
            padx=12, pady=6,
        )
        self.admin_badge.pack(side="left", padx=20)

        if not summary["is_admin"]:
            note = ctk.CTkLabel(
                self, text="بعض الأدلة (سجلات الأحداث، بعض مفاتيح الريجستري) تتطلب التشغيل كمسؤول",
                font=theme.body_font(10), text_color=theme.COLOR_WARNING,
            )
            note.pack(side="left", padx=(0, 10))

    def set_case_name(self, case_name: str):
        self.case_label.configure(text=f"القضية: {case_name}")
