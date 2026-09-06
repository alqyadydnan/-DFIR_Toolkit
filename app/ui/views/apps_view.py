"""شاشة البرامج وسجل التشغيل: Prefetch، UserAssist، والبرامج المثبتة."""

from __future__ import annotations

import customtkinter as ctk

from app.ui import theme
from app.ui.widgets import ScreenHeader, SearchableTable
from app.ui.views.base_view import BaseView

from app.core.forensics.prefetch import get_prefetch_executions
from app.core.forensics.userassist import get_userassist_entries
from app.core.forensics.installed_programs import get_installed_programs


class AppsView(BaseView):
    def __init__(self, master, status_bar=None, **kwargs):
        super().__init__(master, status_bar=status_bar, **kwargs)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        header = ScreenHeader(
            container, title="البرامج وسجل التشغيل",
            subtitle="البرامج المفتوحة سابقاً (Prefetch/UserAssist) والبرامج المثبتة على الجهاز",
            on_refresh=self.refresh,
        )
        header.pack(fill="x", pady=(0, 14))

        self.tabs = ctk.CTkTabview(
            container, fg_color=theme.COLOR_BG_PANEL, segmented_button_selected_color=theme.COLOR_ACCENT,
            segmented_button_selected_hover_color=theme.COLOR_ACCENT_HOVER,
        )
        self.tabs.pack(fill="both", expand=True)

        tab_prefetch = self.tabs.add("سجل التشغيل (Prefetch)")
        tab_userassist = self.tabs.add("سجل UserAssist")
        tab_installed = self.tabs.add("البرامج المثبتة")

        self.prefetch_table = SearchableTable(
            tab_prefetch,
            columns=["الاسم التنفيذي", "آخر تشغيل", "أول ظهور", "عدد ملف Prefetch", "الحجم (كيلوبايت)"],
            placeholder="ابحث باسم البرنامج...",
        )
        self.prefetch_table.pack(fill="both", expand=True, padx=4, pady=4)

        self.userassist_table = SearchableTable(
            tab_userassist,
            columns=["مسار البرنامج", "عدد مرات التشغيل", "آخر تشغيل", "المصدر"],
            placeholder="ابحث باسم البرنامج أو المسار...",
        )
        self.userassist_table.pack(fill="both", expand=True, padx=4, pady=4)

        self.installed_table = SearchableTable(
            tab_installed,
            columns=["اسم البرنامج", "الناشر", "الإصدار", "تاريخ التثبيت", "مسار التثبيت"],
            placeholder="ابحث باسم البرنامج أو الناشر...",
        )
        self.installed_table.pack(fill="both", expand=True, padx=4, pady=4)

    def refresh(self):
        def worker():
            return {
                "prefetch": get_prefetch_executions(),
                "userassist": get_userassist_entries(),
                "installed": get_installed_programs(),
            }

        def on_done(result):
            prefetch_rows = [
                {
                    "الاسم التنفيذي": r["executable"],
                    "آخر تشغيل": r["last_run"],
                    "أول ظهور": r["first_seen"],
                    "عدد ملف Prefetch": r["prefetch_hash"],
                    "الحجم (كيلوبايت)": r["size_kb"],
                }
                for r in result["prefetch"]
            ]
            self.prefetch_table.load_rows(prefetch_rows)

            userassist_rows = [
                {
                    "مسار البرنامج": r["program_path"],
                    "عدد مرات التشغيل": r["run_count"],
                    "آخر تشغيل": r["last_run"],
                    "المصدر": r["source"],
                }
                for r in result["userassist"]
            ]
            self.userassist_table.load_rows(userassist_rows)

            installed_rows = [
                {
                    "اسم البرنامج": r["name"],
                    "الناشر": r["publisher"],
                    "الإصدار": r["version"],
                    "تاريخ التثبيت": r["install_date"],
                    "مسار التثبيت": r["install_location"],
                }
                for r in result["installed"]
            ]
            self.installed_table.load_rows(installed_rows)

        self.run_task("جاري جلب سجل البرامج والتطبيقات...", worker, on_done, "تم تحديث سجل البرامج")
