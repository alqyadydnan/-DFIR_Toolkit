"""
النافذة الرئيسية (Main Window) التي تجمع كل مكونات الواجهة:
الهيدر العلوي، الشريط الجانبي، منطقة المحتوى المتغيرة حسب الشاشة
المختارة، وشريط الحالة السفلي.
"""

from __future__ import annotations

import customtkinter as ctk

from app.ui import theme
from app.ui.header import HeaderBar
from app.ui.sidebar import Sidebar
from app.ui.statusbar import StatusBar

from app.ui.views.dashboard_view import DashboardView
from app.ui.views.apps_view import AppsView
from app.ui.views.network_view import NetworkView
from app.ui.views.system_changes_view import SystemChangesView
from app.ui.views.usb_view import UsbView
from app.ui.views.commands_events_view import CommandsEventsView
from app.ui.views.threat_center_view import ThreatCenterView
from app.ui.views.user_activity_view import UserActivityView
from app.ui.views.registry_view import RegistryView


class MainWindow(ctk.CTk):
    def __init__(self, case_name: str = "قضية بدون اسم"):
        super().__init__()

        self.title("منصة التحقيق الجنائي الرقمي - DFIR Toolkit")
        self.geometry("1360x820")
        self.minsize(1100, 680)
        self.configure(fg_color=theme.COLOR_BG_DARKEST)

        # --- التخطيط العام: هيدر بالأعلى، ثم (سايدبار + محتوى)، ثم شريط حالة ---
        self.header = HeaderBar(self, case_name=case_name)
        self.header.pack(side="top", fill="x")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="top", fill="both", expand=True)

        self.status_bar = StatusBar(self)
        self.status_bar.pack(side="bottom", fill="x")

        self.content_area = ctk.CTkFrame(body, fg_color=theme.COLOR_BG_DARKEST, corner_radius=0)
        self.content_area.pack(side="right", fill="both", expand=True)

        self.sidebar = Sidebar(body, on_navigate=self._navigate)
        self.sidebar.pack(side="left", fill="y")

        self._views: dict[str, ctk.CTkFrame] = {}
        self._current_view_key: str | None = None
        self._build_views()
        self.sidebar.set_active("dashboard")
        self._navigate("dashboard")

    def _build_views(self):
        self._views["dashboard"] = DashboardView(self.content_area, status_bar=self.status_bar)
        self._views["apps"] = AppsView(self.content_area, status_bar=self.status_bar)
        self._views["network"] = NetworkView(self.content_area, status_bar=self.status_bar)
        self._views["system_changes"] = SystemChangesView(self.content_area, status_bar=self.status_bar)
        self._views["usb"] = UsbView(self.content_area, status_bar=self.status_bar)
        self._views["commands_events"] = CommandsEventsView(self.content_area, status_bar=self.status_bar)
        self._views["threats"] = ThreatCenterView(self.content_area, status_bar=self.status_bar)
        self._views["user_activity"] = UserActivityView(self.content_area, status_bar=self.status_bar)
        self._views["registry"] = RegistryView(self.content_area, status_bar=self.status_bar)

        for view in self._views.values():
            view.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _navigate(self, key: str):
        if key not in self._views:
            return
        self._current_view_key = key
        view = self._views[key]
        view.tkraise()
        view.on_show()
