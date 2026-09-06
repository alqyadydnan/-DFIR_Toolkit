"""
أدوات مساعدة لتشغيل عمليات جمع الأدلة الجنائية في خيوط (threads) منفصلة
حتى لا تتجمد واجهة المستخدم أبداً أثناء تنفيذ استعلامات النظام الثقيلة.

الفكرة: كل شاشة تستدعي run_in_background(func, on_done, on_error)
فيتم تنفيذ func() في Thread منفصل، ثم تُستدعى on_done(result) داخل
الخيط الرئيسي للواجهة عبر after() لضمان أمان تحديث عناصر Tkinter.
"""

from __future__ import annotations

import threading
import traceback
from typing import Callable, Any


def run_in_background(
    widget,
    target: Callable[[], Any],
    on_done: Callable[[Any], None] | None = None,
    on_error: Callable[[str], None] | None = None,
) -> threading.Thread:
    """
    ينفذ target() في خيط منفصل.
    widget: أي عنصر CTk يملك .after() (تُستخدم لجدولة النتيجة في الخيط الرئيسي).
    """

    def worker():
        try:
            result = target()
        except Exception:
            err_text = traceback.format_exc()
            if on_error is not None:
                widget.after(0, lambda: on_error(err_text))
            return
        if on_done is not None:
            widget.after(0, lambda: on_done(result))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread


class Debouncer:
    """يمنع تكرار تنفيذ استعلام البحث مع كل ضغطة حرف في مربعات الفلترة."""

    def __init__(self, widget, delay_ms: int = 300):
        self.widget = widget
        self.delay_ms = delay_ms
        self._after_id = None

    def call(self, func: Callable[[], None]):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = self.widget.after(self.delay_ms, func)
