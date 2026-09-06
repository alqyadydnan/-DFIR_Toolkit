"""الشريط الجانبي (Sidebar) للتنقل بين الشاشات الرئيسية للتطبيق."""

from __future__ import annotations

from typing import Callable, List, Tuple

import customtkinter as ctk

from app.ui import theme

# (المفتاح الداخلي, النص الظاهر مع الأيقونة)
NAV_ITEMS: List[Tuple[str, str]] = [
    ("dashboard", "🏠  لوحة التحكم"),
    ("apps", "📂  البرامج وسجل التشغيل"),
    ("network", "🌐  الشبكة والمواقع"),
    ("system_changes", "🛠️  تغييرات النظام والثبات"),
    ("usb", "💾  أجهزة USB الخارجية"),
    ("commands_events", "⌨️  الأوامر وسجلات الأحداث"),
    ("threats", "🚨  مركز التهديدات"),
    ("user_activity", "🕵️  نشاط المستخدم"),
    ("registry", "🗃️  مستعرض Registry"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, master, on_navigate: Callable[[str], None], **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG_SIDEBAR, corner_radius=0, width=230, **kwargs)
        self.pack_propagate(False)

        self._on_navigate = on_navigate
        self._buttons = {}
        self._active_key = None

        ctk.CTkLabel(
            self, text="القوائم الرئيسية", font=theme.body_font(11, "bold"),
            text_color=theme.COLOR_TEXT_MUTED, anchor="e",
        ).pack(fill="x", padx=18, pady=(20, 8))

        for key, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                self, text=label, anchor="e", height=42,
                font=theme.body_font(13), corner_radius=8,
                fg_color="transparent", hover_color=theme.COLOR_ACCENT_SOFT,
                text_color=theme.COLOR_TEXT_SECONDARY,
                command=lambda k=key: self._handle_click(k),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self._buttons[key] = btn

        spacer = ctk.CTkFrame(self, fg_color="transparent")
        spacer.pack(fill="both", expand=True)

        version_label = ctk.CTkLabel(
            self, text="DFIR Toolkit  v2.0", font=theme.body_font(10),
            text_color=theme.COLOR_TEXT_MUTED,
        )
        version_label.pack(pady=14)

    def _handle_click(self, key: str):
        if self._active_key == key:
            return
        self.set_active(key)
        self._on_navigate(key)

    def set_active(self, key: str):
        """يحدّث تظليل الزر النشط فقط دون استدعاء دالة التنقل (تُستخدم عند التهيئة الأولى)."""
        self._active_key = key
        for btn_key, btn in self._buttons.items():
            if btn_key == key:
                btn.configure(fg_color=theme.COLOR_ACCENT, text_color="#ffffff")
            else:
                btn.configure(fg_color="transparent", text_color=theme.COLOR_TEXT_SECONDARY)
