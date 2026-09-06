"""Recent Files, Jump Lists and ShellBags view."""
from __future__ import annotations
import customtkinter as ctk
from app.ui import theme
from app.ui.widgets import ScreenHeader, SearchableTable
from app.ui.views.base_view import BaseView
from app.core.forensics.recent_activity import get_recent_files, get_jump_lists
from app.core.forensics.shellbags import get_shellbags

class UserActivityView(BaseView):
    def __init__(self, master, status_bar=None, **kwargs):
        super().__init__(master, status_bar=status_bar, **kwargs)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)
        ScreenHeader(container, title="نشاط المستخدم", subtitle="Recent Files وJump Lists وShellBags — أدلة على الملفات والمجلدات التي تم الوصول إليها", on_refresh=self.refresh).pack(fill="x", pady=(0,14))
        self.tabs = ctk.CTkTabview(container, fg_color=theme.COLOR_BG_PANEL, segmented_button_selected_color=theme.COLOR_ACCENT, segmented_button_selected_hover_color=theme.COLOR_ACCENT_HOVER)
        self.tabs.pack(fill="both", expand=True)
        recent = self.tabs.add("Recent Files")
        jumps = self.tabs.add("Jump Lists")
        bags = self.tabs.add("ShellBags")
        self.recent_table = SearchableTable(recent, columns=["اسم الاختصار","الهدف / الملف","المعاملات","آخر تعديل","المصدر"], placeholder="ابحث عن ملف أو مسار...")
        self.recent_table.pack(fill="both", expand=True, padx=4, pady=4)
        self.jumps_table = SearchableTable(jumps, columns=["الملف","النوع","آخر تعديل","الحجم KB","مسارات/روابط قابلة للاستخراج","المصدر"], placeholder="ابحث داخل Jump Lists...")
        self.jumps_table.pack(fill="both", expand=True, padx=4, pady=4)
        self.bags_table = SearchableTable(bags, columns=["مفتاح Registry","آخر تعديل","بيانات/مسارات مقروءة","المصدر"], placeholder="ابحث عن مجلد أو مفتاح...")
        self.bags_table.pack(fill="both", expand=True, padx=4, pady=4)

    def refresh(self):
        def worker():
            return {"recent": get_recent_files(), "jumps": get_jump_lists(), "bags": get_shellbags()}
        def done(r):
            self.recent_table.load_rows([{"اسم الاختصار":x["name"],"الهدف / الملف":x["target"],"المعاملات":x["arguments"],"آخر تعديل":x["modified"],"المصدر":x["source"]} for x in r["recent"]])
            self.jumps_table.load_rows([{"الملف":x["file"],"النوع":x["type"],"آخر تعديل":x["modified"],"الحجم KB":x["size_kb"],"مسارات/روابط قابلة للاستخراج":x["paths"],"المصدر":x["source"]} for x in r["jumps"]])
            self.bags_table.load_rows([{"مفتاح Registry":x["registry_key"],"آخر تعديل":x["last_write"],"بيانات/مسارات مقروءة":x["mru_values"],"المصدر":x["source"]} for x in r["bags"]])
        self.run_task("جاري تحليل Recent Files وJump Lists وShellBags...", worker, done, "تم تحديث نشاط المستخدم")
