"""شاشة تغييرات النظام والثبات (Persistence): Run keys، الخدمات، المهام المجدولة."""

from __future__ import annotations

import customtkinter as ctk

from app.ui import theme
from app.ui.widgets import ScreenHeader, SearchableTable
from app.ui.views.base_view import BaseView

from app.core.forensics.persistence import (
    get_registry_autoruns, get_services, get_scheduled_tasks,
)


class SystemChangesView(BaseView):
    def __init__(self, master, status_bar=None, **kwargs):
        super().__init__(master, status_bar=status_bar, **kwargs)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        header = ScreenHeader(
            container, title="تغييرات النظام والثبات",
            subtitle="برامج بدء التشغيل التلقائي، الخدمات المسجّلة، والمهام المجدولة",
            on_refresh=self.refresh,
        )
        header.pack(fill="x", pady=(0, 14))

        self.tabs = ctk.CTkTabview(
            container, fg_color=theme.COLOR_BG_PANEL, segmented_button_selected_color=theme.COLOR_ACCENT,
            segmented_button_selected_hover_color=theme.COLOR_ACCENT_HOVER,
        )
        self.tabs.pack(fill="both", expand=True)

        tab_autoruns = self.tabs.add("بدء التشغيل التلقائي")
        tab_services = self.tabs.add("الخدمات (Services)")
        tab_tasks = self.tabs.add("المهام المجدولة")

        self.autoruns_table = SearchableTable(
            tab_autoruns,
            columns=["اسم المفتاح", "الأمر / المسار", "موقعه في الريجستري"],
            placeholder="ابحث باسم البرنامج أو الأمر...",
        )
        self.autoruns_table.pack(fill="both", expand=True, padx=4, pady=4)

        self.services_table = SearchableTable(
            tab_services,
            columns=["اسم الخدمة", "الاسم الظاهر", "الحالة", "نوع بدء التشغيل", "المسار"],
            placeholder="ابحث باسم الخدمة...",
        )
        self.services_table.pack(fill="both", expand=True, padx=4, pady=4)

        self.tasks_table = SearchableTable(
            tab_tasks,
            columns=["اسم المهمة", "الحالة", "التشغيل القادم", "آخر تشغيل", "يعمل كـ", "الأمر المنفذ"],
            placeholder="ابحث باسم المهمة...",
        )
        self.tasks_table.pack(fill="both", expand=True, padx=4, pady=4)

    def refresh(self):
        def worker():
            return {
                "autoruns": get_registry_autoruns(),
                "services": get_services(),
                "tasks": get_scheduled_tasks(),
            }

        def on_done(result):
            autoruns_rows = [
                {"اسم المفتاح": r["name"], "الأمر / المسار": r["command"], "موقعه في الريجستري": r["location"]}
                for r in result["autoruns"]
            ]
            self.autoruns_table.load_rows(autoruns_rows)

            services_rows = [
                {
                    "اسم الخدمة": r["name"],
                    "الاسم الظاهر": r["display_name"],
                    "الحالة": r["state"],
                    "نوع بدء التشغيل": r["start_mode"],
                    "المسار": r["path"],
                }
                for r in result["services"]
            ]
            self.services_table.load_rows(services_rows)

            tasks_rows = [
                {
                    "اسم المهمة": r["task_name"],
                    "الحالة": r["status"],
                    "التشغيل القادم": r["next_run"],
                    "آخر تشغيل": r["last_run"],
                    "يعمل كـ": r["run_as"],
                    "الأمر المنفذ": r["task_to_run"],
                }
                for r in result["tasks"]
            ]
            self.tasks_table.load_rows(tasks_rows)

        self.run_task("جاري جلب بيانات الثبات والتغييرات...", worker, on_done, "تم تحديث بيانات النظام")
