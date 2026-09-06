"""
فئة أساسية (Base Class) تشترك فيها كل شاشات التطبيق: توفر دالة موحدة
لتشغيل عمليات جلب الأدلة في الخلفية مع تحديث شريط الحالة تلقائياً،
وإظهار رسائل الخطأ بشكل موحد دون تجميد الواجهة أو انهيار البرنامج.
"""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from app.core.threading_utils import run_in_background
from app.core.error_log import log_error
from app.ui import theme


class BaseView(ctk.CTkFrame):
    def __init__(self, master, status_bar=None, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG_DARKEST, corner_radius=0, **kwargs)
        self.status_bar = status_bar
        self._loaded_once = False

    def on_show(self):
        """تُستدعى تلقائياً كل مرة يتم فيها عرض هذه الشاشة. يمكن تجاوزها."""
        if not self._loaded_once:
            self._loaded_once = True
            self.refresh()

    def refresh(self):
        """يجب تجاوزها في كل شاشة فرعية لتنفيذ منطق التحديث الخاص بها."""
        pass

    def run_task(self, busy_message: str, target: Callable, on_done: Callable, done_message: str = "تم التحديث"):
        """يشغل target() في الخلفية ويحدث شريط الحالة تلقائياً."""
        if self.status_bar is not None:
            self.status_bar.set_busy(busy_message)

        def _on_done(result):
            if self.status_bar is not None:
                self.status_bar.set_idle(done_message)
            on_done(result)

        def _on_error(error_text: str):
            if self.status_bar is not None:
                self.status_bar.set_error("حدث خطأ أثناء جلب البيانات (راجع التفاصيل)")
            self._show_error_banner(error_text)

        run_in_background(self, target, _on_done, _on_error)

    def _show_error_banner(self, error_text: str):
        # نطبع أول سطر فقط في شريط الحالة، والتفاصيل الكاملة تبقى متاحة للمطوّر
        first_line = error_text.strip().splitlines()[-1] if error_text.strip() else "خطأ غير معروف"
        log_error(error_text)  # يُسجَّل في ملف داخلي فقط، دون أي إخراج على الطرفية (Console)
        if self.status_bar is not None:
            self.status_bar.set_error(f"خطأ: {first_line}"[:120])
