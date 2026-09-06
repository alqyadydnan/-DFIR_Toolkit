"""شاشة مركز التهديدات (Threat Center): كشف العمليات المشبوهة وتظليلها حسب الخطورة."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import customtkinter as ctk

from app.ui import theme
from app.ui.widgets import ScreenHeader, SearchableTable
from app.ui.views.base_view import BaseView

from app.core.forensics.threat_detection import scan_for_threats

_SEVERITY_LABELS = {
    "critical": "🔴 حرجة",
    "high": "🟠 عالية",
    "medium": "🟡 متوسطة",
    "low": "🔵 منخفضة",
    "info": "⚪ معلومة",
}


class ThreatCenterView(BaseView):
    def __init__(self, master, status_bar=None, **kwargs):
        super().__init__(master, status_bar=status_bar, **kwargs)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        header = ScreenHeader(
            container, title="مركز التهديدات",
            subtitle="فحص استدلالي للعمليات النشطة: مسارات مشبوهة، توقيعات غير صالحة، ومحاكاة أسماء النظام",
            on_refresh=self.refresh,
        )
        header.pack(fill="x", pady=(0, 10))

        self.deep_scan_var = tk.BooleanVar(value=False)
        options_frame = ctk.CTkFrame(container, fg_color="transparent")
        options_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkCheckBox(
            options_frame, text="تفعيل فحص التوقيع الرقمي (أدق لكنه أبطأ)", variable=self.deep_scan_var,
            font=theme.body_font(12), text_color=theme.COLOR_TEXT_SECONDARY,
            onvalue=True, offvalue=False,
        ).pack(side="right")

        self.summary_banner = ctk.CTkLabel(
            container, text="اضغط تحديث لبدء الفحص الاستدلالي...", font=theme.body_font(13, "bold"),
            text_color=theme.COLOR_TEXT_SECONDARY, anchor="e",
            fg_color=theme.COLOR_BG_PANEL, corner_radius=10,
        )
        self.summary_banner.pack(fill="x", pady=(0, 10), ipady=10)

        self.table = SearchableTable(
            container,
            columns=["الخطورة", "اسم العملية", "PID", "المسار", "سطر التشغيل", "سبب التنبيه"],
            placeholder="ابحث باسم العملية أو السبب...",
        )
        self.table.pack(fill="both", expand=True)

        # ألوان تظليل الصفوف حسب الخطورة
        for tag, color in [
            ("critical", theme.COLOR_DANGER),
            ("high", "#7c2d12"),
            ("medium", "#78350f"),
            ("low", theme.COLOR_BG_PANEL_ALT),
        ]:
            self.table.tree.tag_configure(tag, background=color, foreground="#ffffff")

    def refresh(self):
        check_signatures = self.deep_scan_var.get()

        def worker():
            return scan_for_threats(check_signatures=check_signatures)

        def on_done(findings):
            rows = []
            for f in findings:
                rows.append(
                    {
                        "الخطورة": _SEVERITY_LABELS.get(f["severity"], f["severity"]),
                        "اسم العملية": f["process_name"],
                        "PID": f["pid"],
                        "المسار": f["path"],
                        "سطر التشغيل": f["command_line"],
                        "سبب التنبيه": f["reasons"],
                        "_severity": f["severity"],
                    }
                )
            self.table.load_rows(rows)
            self._colorize_rows(rows)

            if not findings:
                self.summary_banner.configure(
                    text="✅ لم يتم رصد أي مؤشرات مشبوهة واضحة في العمليات الحالية.",
                    text_color=theme.COLOR_SUCCESS,
                )
            else:
                critical_count = sum(1 for f in findings if f["severity"] == "critical")
                self.summary_banner.configure(
                    text=f"⚠ تم رصد {len(findings)} عنصراً يستحق المراجعة، منها {critical_count} بخطورة حرجة.",
                    text_color=theme.COLOR_DANGER if critical_count else theme.COLOR_WARNING,
                )

        self.run_task("جاري فحص العمليات النشطة استدلالياً...", worker, on_done, "اكتمل فحص التهديدات")

    def _colorize_rows(self, rows):
        """يعيد تلوين صفوف الجدول بعد التحميل حسب مستوى الخطورة."""
        children = self.table.tree.get_children()
        # نطابق الصفوف بالترتيب لأن load_rows لا تفلتر افتراضياً عند التحميل الأول
        visible_rows = [r for r in rows]
        for item_id, row in zip(children, visible_rows):
            severity = row.get("_severity", "info")
            if severity in ("critical", "high", "medium", "low"):
                self.table.tree.item(item_id, tags=(severity,))
