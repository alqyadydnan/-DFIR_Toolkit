"""شاشة لوحة التحكم (Dashboard): ملخص عام لحالة الجهاز والتهديدات."""

from __future__ import annotations

import customtkinter as ctk

from app.ui import theme
from app.ui.widgets import ScreenHeader, KPICard
from app.ui.views.base_view import BaseView

from app.core.system_info import get_system_summary
from app.core.forensics.prefetch import get_prefetch_executions
from app.core.forensics.network import get_active_connections
from app.core.forensics.usb_history import get_usb_history
from app.core.forensics.threat_detection import scan_for_threats


class DashboardView(BaseView):
    def __init__(self, master, status_bar=None, on_open_threats=None, **kwargs):
        super().__init__(master, status_bar=status_bar, **kwargs)
        self._on_open_threats = on_open_threats

        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)

        header = ScreenHeader(
            container, title="لوحة التحكم", subtitle="نظرة عامة سريعة على حالة الجهاز والأدلة المجمّعة",
            on_refresh=self.refresh,
        )
        header.pack(fill="x", pady=(0, 16))

        # --- شبكة بطاقات KPI ---
        cards_frame = ctk.CTkFrame(container, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 16))
        for i in range(4):
            cards_frame.grid_columnconfigure(i, weight=1, uniform="kpi")

        self.card_processes = KPICard(cards_frame, "برامج ظهرت في Prefetch", accent=theme.COLOR_INFO)
        self.card_processes.grid(row=0, column=3, sticky="ew", padx=6)

        self.card_connections = KPICard(cards_frame, "اتصالات شبكية نشطة", accent=theme.COLOR_ACCENT)
        self.card_connections.grid(row=0, column=2, sticky="ew", padx=6)

        self.card_usb = KPICard(cards_frame, "أجهزة USB Storage مسجّلة", accent=theme.COLOR_WARNING)
        self.card_usb.grid(row=0, column=1, sticky="ew", padx=6)

        self.card_threats = KPICard(cards_frame, "تنبيهات مشبوهة حالية", accent=theme.COLOR_DANGER)
        self.card_threats.grid(row=0, column=0, sticky="ew", padx=6)

        # --- زر الفحص الشامل ---
        scan_frame = ctk.CTkFrame(container, fg_color=theme.COLOR_BG_PANEL, corner_radius=14,
                                   border_width=1, border_color=theme.COLOR_BORDER)
        scan_frame.pack(fill="x", pady=(0, 16))

        inner = ctk.CTkFrame(scan_frame, fg_color="transparent")
        inner.pack(fill="x", padx=18, pady=16)

        ctk.CTkButton(
            inner, text="🔍  بدء فحص سريع للجهاز", height=42, width=200,
            font=theme.body_font(14, "bold"), fg_color=theme.COLOR_ACCENT,
            hover_color=theme.COLOR_ACCENT_HOVER, command=self.refresh,
        ).pack(side="left")

        self.scan_summary_label = ctk.CTkLabel(
            inner, text="يفحص مؤشرات التشغيل والشبكة وUSB والتهديدات الحالية فقط؛ التفاصيل الكاملة في الشاشات المتخصصة.",
            font=theme.body_font(12), text_color=theme.COLOR_TEXT_SECONDARY, anchor="e",
        )
        self.scan_summary_label.pack(side="right", padx=10)

        # --- معلومات النظام ---
        info_frame = ctk.CTkFrame(container, fg_color=theme.COLOR_BG_PANEL, corner_radius=14,
                                   border_width=1, border_color=theme.COLOR_BORDER)
        info_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(
            info_frame, text="معلومات النظام قيد الفحص", font=theme.body_font(14, "bold"),
            text_color=theme.COLOR_TEXT_PRIMARY, anchor="e",
        ).pack(anchor="e", padx=18, pady=(16, 6))

        self.system_info_text = ctk.CTkLabel(
            info_frame, text="", font=theme.mono_font(12), text_color=theme.COLOR_TEXT_SECONDARY,
            justify="right", anchor="ne",
        )
        self.system_info_text.pack(fill="both", expand=True, padx=18, pady=(0, 16), anchor="ne")

        self._load_system_info()

    def _load_system_info(self):
        summary = get_system_summary()
        lines = [
            f"اسم الجهاز (Hostname):        {summary['hostname']}",
            f"المستخدم الحالي:               {summary['username']}",
            f"إصدار النظام:                  {summary['os_version']}",
            f"المعمارية:                     {summary['architecture']}",
            f"المعالج:                       {summary['processor']}",
            f"صلاحيات المسؤول:               {'مفعّلة' if summary['is_admin'] else 'غير مفعّلة'}",
            f"وقت بدء هذا الفحص:             {summary['boot_scan_time']}",
        ]
        self.system_info_text.configure(text="\n".join(lines))

    def refresh(self):
        def worker():
            return {
                "prefetch": get_prefetch_executions(),
                "connections": get_active_connections(),
                "usb": get_usb_history(),
                "threats": scan_for_threats(check_signatures=False),
            }

        def on_done(result):
            self.card_processes.set_value(str(len(result["prefetch"])))
            self.card_connections.set_value(str(len(result["connections"])))
            self.card_usb.set_value(str(sum(1 for x in result["usb"] if x.get("source") == "USBSTOR")))
            self.card_threats.set_value(str(len(result["threats"])))

            threat_count = len(result["threats"])
            if threat_count == 0:
                self.scan_summary_label.configure(
                    text="لم يتم رصد أنشطة مشبوهة واضحة في هذا الفحص السريع.",
                    text_color=theme.COLOR_SUCCESS,
                )
            else:
                self.scan_summary_label.configure(
                    text=f"تم رصد {threat_count} مؤشراً يستحق المراجعة — افتح مركز التهديدات لمزيد من التفاصيل.",
                    text_color=theme.COLOR_WARNING,
                )
            self._load_system_info()

        self.run_task("جاري إجراء الفحص السريع للجهاز...", worker, on_done, "اكتمل الفحص السريع")
