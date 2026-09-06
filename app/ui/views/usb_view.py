"""شاشة سجل أجهزة الـ USB الخارجية التي وُصلت بالجهاز تاريخياً."""

from __future__ import annotations

import customtkinter as ctk

from app.ui import theme
from app.ui.widgets import ScreenHeader, SearchableTable
from app.ui.views.base_view import BaseView

from app.core.forensics.usb_history import get_usb_history, get_mounted_device_mappings
from app.core.forensics.deleted_files import get_recycle_bin_contents


class UsbView(BaseView):
    def __init__(self, master, status_bar=None, **kwargs):
        super().__init__(master, status_bar=status_bar, **kwargs)

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        header = ScreenHeader(
            container, title="أجهزة USB والملفات المحذوفة",
            subtitle="سجل USB من عدة مصادر Windows + سلة المحذوفات الحالية؛ مع توضيح مصدر كل دليل ودرجة دلالته الزمنية",
            on_refresh=self.refresh,
        )
        header.pack(fill="x", pady=(0, 14))

        self.tabs = ctk.CTkTabview(
            container, fg_color=theme.COLOR_BG_PANEL, segmented_button_selected_color=theme.COLOR_ACCENT,
            segmented_button_selected_hover_color=theme.COLOR_ACCENT_HOVER,
        )
        self.tabs.pack(fill="both", expand=True)

        tab_usb = self.tabs.add("سجل أجهزة USB")
        tab_mount = self.tabs.add("Mounted Devices")
        tab_deleted = self.tabs.add("الملفات المحذوفة (سلة المحذوفات)")

        self.usb_table = SearchableTable(
            tab_usb,
            columns=["الاسم الودّي", "فئة الجهاز", "الرقم التسلسلي", "آخر اتصال/مؤشر زمني", "المصدر", "ملاحظة الدليل"],
            placeholder="ابحث باسم الجهاز أو الرقم التسلسلي...",
        )
        self.usb_table.pack(fill="both", expand=True, padx=4, pady=4)

        self.mount_table = SearchableTable(
            tab_mount,
            columns=["حرف القرص", "بيانات جهاز MountedDevices", "المصدر"],
            placeholder="ابحث بحرف القرص...",
        )
        self.mount_table.pack(fill="both", expand=True, padx=4, pady=4)

        self.deleted_table = SearchableTable(
            tab_deleted,
            columns=["القرص", "المسار الأصلي", "وقت الحذف", "الحجم (كيلوبايت)", "قابل للاسترجاع؟"],
            placeholder="ابحث باسم الملف المحذوف...",
        )
        self.deleted_table.pack(fill="both", expand=True, padx=4, pady=4)

    def refresh(self):
        def worker():
            return {
                "usb": get_usb_history(),
                "mounts": get_mounted_device_mappings(),
                "deleted": get_recycle_bin_contents(),
            }

        def on_done(result):
            usb_rows = [
                {
                    "الاسم الودّي": r["friendly_name"],
                    "فئة الجهاز": r["device_class"],
                    "الرقم التسلسلي": r["serial_number"],
                    "آخر اتصال/مؤشر زمني": r["last_connected"],
                    "المصدر": r.get("source", "N/A"),
                    "ملاحظة الدليل": r.get("evidence_note", ""),
                }
                for r in result["usb"]
            ]
            self.usb_table.load_rows(usb_rows)

            self.mount_table.load_rows([
                {"حرف القرص": r["drive_letter"], "بيانات جهاز MountedDevices": r["device_data"], "المصدر": r["source"]}
                for r in result["mounts"]
            ])

            deleted_rows = [
                {
                    "القرص": r["drive"],
                    "المسار الأصلي": r["original_path"],
                    "وقت الحذف": r["deleted_at"],
                    "الحجم (كيلوبايت)": r["size_kb"],
                    "قابل للاسترجاع؟": r["recoverable"],
                }
                for r in result["deleted"]
            ]
            self.deleted_table.load_rows(deleted_rows)

        self.run_task("جاري جلب سجل USB والملفات المحذوفة...", worker, on_done, "تم تحديث السجل")
