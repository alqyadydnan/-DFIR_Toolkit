"""شريط الحالة السفلي (Status Bar): يعرض حالة العمليات الحية وشريط تقدم."""

from __future__ import annotations

import customtkinter as ctk

from app.ui import theme


class StatusBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=theme.COLOR_BG_SIDEBAR, corner_radius=0, height=32, **kwargs)
        self.pack_propagate(False)

        self.status_label = ctk.CTkLabel(
            self, text="جاهز", font=theme.body_font(11), text_color=theme.COLOR_TEXT_SECONDARY,
        )
        self.status_label.pack(side="right", padx=14)

        self.progress = ctk.CTkProgressBar(self, width=180, height=8, mode="indeterminate")
        self.progress.set(0)

        self.clock_label = ctk.CTkLabel(
            self, text="", font=theme.body_font(11), text_color=theme.COLOR_TEXT_MUTED,
        )
        self.clock_label.pack(side="left", padx=14)
        self._tick()

    def _tick(self):
        from datetime import datetime
        self.clock_label.configure(text=datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
        self.after(1000, self._tick)

    def set_busy(self, message: str):
        self.status_label.configure(text=message, text_color=theme.COLOR_INFO)
        if not self.progress.winfo_ismapped():
            self.progress.pack(side="right", padx=(0, 10))
        self.progress.start()

    def set_idle(self, message: str = "جاهز"):
        self.status_label.configure(text=message, text_color=theme.COLOR_TEXT_SECONDARY)
        self.progress.stop()
        self.progress.pack_forget()

    def set_error(self, message: str):
        self.status_label.configure(text=message, text_color=theme.COLOR_DANGER)
        self.progress.stop()
        self.progress.pack_forget()
