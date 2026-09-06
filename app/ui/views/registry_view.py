"""Read-only Registry explorer."""
from __future__ import annotations
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from app.ui import theme
from app.ui.widgets import ScreenHeader, SearchableTable
from app.ui.views.base_view import BaseView
from app.core.forensics.registry_explorer import read_registry_key

class RegistryView(BaseView):
    def __init__(self, master, status_bar=None, **kwargs):
        super().__init__(master, status_bar=status_bar, **kwargs)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)
        ScreenHeader(container, title="مستعرض Registry", subtitle="استكشاف قراءة فقط لمفاتيح Windows Registry وقيمها — لا توجد أي عمليات تعديل", on_refresh=self.read_key).pack(fill="x", pady=(0,12))
        bar = ctk.CTkFrame(container, fg_color=theme.COLOR_BG_PANEL, corner_radius=10)
        bar.pack(fill="x", pady=(0,10))
        self.hive_var = tk.StringVar(value="HKLM")
        ctk.CTkLabel(bar, text="Hive", text_color=theme.COLOR_TEXT_SECONDARY).pack(side="right", padx=(10,4), pady=10)
        ctk.CTkOptionMenu(bar, variable=self.hive_var, values=["HKLM","HKCU","HKCR","HKU","HKCC"], width=100).pack(side="right", padx=4)
        self.path_entry = ctk.CTkEntry(bar, placeholder_text=r"مثال: SOFTWARE\Microsoft\Windows\CurrentVersion\Run", justify="right")
        self.path_entry.pack(side="right", fill="x", expand=True, padx=8, pady=8)
        self.path_entry.bind("<Return>", lambda _: self.read_key())
        ctk.CTkButton(bar, text="قراءة المفتاح", command=self.read_key, width=130).pack(side="left", padx=8)
        self.info = ctk.CTkLabel(container, text="أدخل مسار المفتاح ثم اضغط قراءة المفتاح.", anchor="e", text_color=theme.COLOR_TEXT_SECONDARY)
        self.info.pack(fill="x", pady=(0,8))
        tabs = ctk.CTkTabview(container, fg_color=theme.COLOR_BG_PANEL, segmented_button_selected_color=theme.COLOR_ACCENT)
        tabs.pack(fill="both", expand=True)
        values_tab = tabs.add("Values")
        keys_tab = tabs.add("Subkeys")
        self.values_table = SearchableTable(values_tab, columns=["اسم القيمة","النوع","البيانات"], placeholder="ابحث في قيم Registry...")
        self.values_table.pack(fill="both", expand=True, padx=4, pady=4)
        self.keys_table = SearchableTable(keys_tab, columns=["المفتاح الفرعي"], placeholder="ابحث عن Subkey...")
        self.keys_table.pack(fill="both", expand=True, padx=4, pady=4)

    def read_key(self):
        hive, path = self.hive_var.get(), self.path_entry.get().strip()
        def worker(): return read_registry_key(hive, path)
        def done(result):
            if result.get("error"):
                self.info.configure(text=result["error"], text_color=theme.COLOR_DANGER); return
            self.info.configure(text=f"{hive}\\{result['path']}  |  عدد القيم: {len(result['values'])}  |  عدد المفاتيح الفرعية: {len(result['subkeys'])}", text_color=theme.COLOR_SUCCESS)
            self.values_table.load_rows([{"اسم القيمة":x["name"],"النوع":x["type"],"البيانات":x["data"]} for x in result["values"]])
            self.keys_table.load_rows([{"المفتاح الفرعي":x["name"]} for x in result["subkeys"]])
        self.run_task("جاري قراءة Registry بشكل آمن...", worker, done, "تمت قراءة Registry")
