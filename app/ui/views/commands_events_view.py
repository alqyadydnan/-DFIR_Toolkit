"""Command execution and Windows Event Log investigation."""
from __future__ import annotations
import customtkinter as ctk
from app.ui import theme
from app.ui.widgets import ScreenHeader, SearchableTable
from app.ui.views.base_view import BaseView
from app.core.forensics.command_history import (
    get_powershell_history, get_running_shell_processes,
    get_process_creation_command_events, get_powershell_script_events,
)
from app.core.forensics.event_logs import get_security_events, get_system_events

class CommandsEventsView(BaseView):
    def __init__(self, master, status_bar=None, **kwargs):
        super().__init__(master, status_bar=status_bar, **kwargs)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)
        ScreenHeader(container, title="الأوامر وسجلات الأحداث", subtitle="تاريخ PowerShell، أوامر CMD/PowerShell التي أمكن إثباتها، Script Block Logging وسجلات Windows", on_refresh=self.refresh).pack(fill="x", pady=(0,14))
        self.tabs = ctk.CTkTabview(container, fg_color=theme.COLOR_BG_PANEL, segmented_button_selected_color=theme.COLOR_ACCENT)
        self.tabs.pack(fill="both", expand=True)
        self.ps_history = SearchableTable(self.tabs.add("PowerShell History"), columns=["#","الأمر","المصدر","آخر تعديل"], placeholder="ابحث في الأوامر...")
        self.ps_history.pack(fill="both", expand=True, padx=4, pady=4)
        self.detected = SearchableTable(self.tabs.add("أوامر مكتشفة"), columns=["الوقت","المصدر","Process","PID الأب","Record ID","الأمر / التفاصيل"], placeholder="cmd / powershell / script...")
        self.detected.pack(fill="both", expand=True, padx=4, pady=4)
        self.running = SearchableTable(self.tabs.add("Shells الحالية"), columns=["PID","PID الأب","الاسم","سطر التشغيل الكامل","وقت الإنشاء"], placeholder="ابحث في العملية...")
        self.running.pack(fill="both", expand=True, padx=4, pady=4)
        self.events = SearchableTable(self.tabs.add("Security Events"), columns=["رقم الحدث","الوصف","الوقت","التفاصيل"], placeholder="Event ID أو نص الرسالة...")
        self.events.pack(fill="both", expand=True, padx=4, pady=4)
        self.note = ctk.CTkLabel(container, text="ملاحظة: CMD لا يملك ملف History دائمًا مثل PowerShell. لذلك تعتمد أوامر CMD التاريخية على Event 4688 إذا كان تدقيق إنشاء العمليات مفعّلاً. أما PowerShell فيستفيد أيضاً من 4104 وPSReadLine.", anchor="e", justify="right", text_color=theme.COLOR_WARNING, wraplength=1050)
        self.note.pack(fill="x", pady=(8,0))

    def refresh(self):
        def worker():
            return {"history":get_powershell_history(),"detected":get_process_creation_command_events(),"ps4104":get_powershell_script_events(),"running":get_running_shell_processes(),"events":get_security_events(),"system_events":get_system_events()}
        def done(r):
            self.ps_history.load_rows([{"#":x["line"],"الأمر":x["command"],"المصدر":x["source"],"آخر تعديل":x["file_last_modified"]} for x in r["history"]])
            detected = [{"الوقت":x["time"],"المصدر":x["source"],"Process":x.get("process_name","N/A"),"PID الأب":x.get("parent_pid","N/A"),"Record ID":x["record_id"],"الأمر / التفاصيل":x["command"]} for x in r["detected"]]
            detected += [{"الوقت":x["time"],"المصدر":x["source"],"Process":"powershell.exe","PID الأب":"N/A","Record ID":x["record_id"],"الأمر / التفاصيل":x["script"]} for x in r["ps4104"]]
            detected.sort(key=lambda x: str(x["الوقت"]), reverse=True)
            self.detected.load_rows(detected)
            self.running.load_rows([{"PID":x["pid"],"PID الأب":x["parent_pid"],"الاسم":x["name"],"سطر التشغيل الكامل":x["command_line"],"وقت الإنشاء":x["created"]} for x in r["running"]])
            events = [{"رقم الحدث":x["event_id"],"الوصف":x["description"],"الوقت":x["time_created"],"التفاصيل":x["message"]} for x in r["events"]]
            events += [{"رقم الحدث":x["event_id"],"الوصف":x["description"],"الوقت":x["time_created"],"التفاصيل":x["message"]} for x in r["system_events"]]
            events.sort(key=lambda x: str(x["الوقت"]), reverse=True)
            self.events.load_rows(events)
        self.run_task("جاري تحليل أوامر CMD/PowerShell وسجلات الأحداث...", worker, done, "تم تحديث الأوامر والأحداث")
