"""Network, DNS, ARP, routing and Wi-Fi evidence."""
from __future__ import annotations
import customtkinter as ctk
from app.ui import theme
from app.ui.widgets import ScreenHeader, SearchableTable
from app.ui.views.base_view import BaseView
from app.core.forensics.network import (
    get_active_connections, get_dns_cache, get_network_interfaces,
    get_arp_table, get_routes, get_wifi_profiles, get_wifi_interfaces,
)
from app.core.forensics.browser_history import get_all_browser_history

class NetworkView(BaseView):
    def __init__(self, master, status_bar=None, **kwargs):
        super().__init__(master, status_bar=status_bar, **kwargs)
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=24, pady=20)
        ScreenHeader(container, title="الشبكة والاتصال اللاسلكي", subtitle="اتصالات حية، DNS، واجهات الشبكة، ARP، Routing، Wi-Fi وسجل المواقع", on_refresh=self.refresh).pack(fill="x", pady=(0,14))
        self.tabs = ctk.CTkTabview(container, fg_color=theme.COLOR_BG_PANEL, segmented_button_selected_color=theme.COLOR_ACCENT, segmented_button_selected_hover_color=theme.COLOR_ACCENT_HOVER)
        self.tabs.pack(fill="both", expand=True)
        self.conn = SearchableTable(self.tabs.add("الاتصالات الحية"), columns=["البروتوكول","العنوان المحلي","العنوان البعيد","الحالة","PID","اسم العملية"], placeholder="IP / PID / Process...")
        self.conn.pack(fill="both", expand=True, padx=4, pady=4)
        self.dns = SearchableTable(self.tabs.add("DNS Cache"), columns=["النطاق","نوع السجل","البيانات"], placeholder="ابحث عن نطاق...")
        self.dns.pack(fill="both", expand=True, padx=4, pady=4)
        self.interfaces = SearchableTable(self.tabs.add("واجهات الشبكة"), columns=["الواجهة","Index","Network Profile","IPv4","IPv6","DNS"], placeholder="اسم الواجهة أو IP...")
        self.interfaces.pack(fill="both", expand=True, padx=4, pady=4)
        self.arp = SearchableTable(self.tabs.add("ARP"), columns=["IP","MAC","النوع"], placeholder="IP أو MAC...")
        self.arp.pack(fill="both", expand=True, padx=4, pady=4)
        self.routes = SearchableTable(self.tabs.add("Routing"), columns=["Destination","Mask","Gateway","Interface","Metric"], placeholder="ابحث في جدول التوجيه...")
        self.routes.pack(fill="both", expand=True, padx=4, pady=4)
        wifi_tab = self.tabs.add("Wi-Fi")
        wifi_tabs = ctk.CTkTabview(wifi_tab, fg_color="transparent", segmented_button_selected_color=theme.COLOR_ACCENT)
        wifi_tabs.pack(fill="both", expand=True)
        self.wifi_current = SearchableTable(wifi_tabs.add("الاتصال الحالي"), columns=["الواجهة","SSID","BSSID","الحالة","التوثيق","القناة","الإشارة","Profile"], placeholder="SSID / BSSID...")
        self.wifi_current.pack(fill="both", expand=True, padx=4, pady=4)
        self.wifi_profiles = SearchableTable(wifi_tabs.add("الشبكات المحفوظة"), columns=["SSID","المصدر"], placeholder="ابحث باسم الشبكة...")
        self.wifi_profiles.pack(fill="both", expand=True, padx=4, pady=4)
        self.history = SearchableTable(self.tabs.add("سجل المواقع"), columns=["المتصفح","الملف الشخصي","URL","العنوان","الزيارات","آخر زيارة"], placeholder="ابحث في المواقع...")
        self.history.pack(fill="both", expand=True, padx=4, pady=4)

    def refresh(self):
        def worker():
            return {"conn":get_active_connections(),"dns":get_dns_cache(),"interfaces":get_network_interfaces(),"arp":get_arp_table(),"routes":get_routes(),"wifi":get_wifi_interfaces(),"profiles":get_wifi_profiles(),"history":get_all_browser_history()}
        def done(r):
            self.conn.load_rows([{"البروتوكول":x["protocol"],"العنوان المحلي":x["local_address"],"العنوان البعيد":x["remote_address"],"الحالة":x["state"],"PID":x["pid"],"اسم العملية":x["process_name"]} for x in r["conn"]])
            self.dns.load_rows([{"النطاق":x["hostname"],"نوع السجل":x["record_type"],"البيانات":x["data"]} for x in r["dns"]])
            self.interfaces.load_rows([{"الواجهة":x["name"],"Index":x["index"],"Network Profile":x["profile"],"IPv4":x["ipv4"],"IPv6":x["ipv6"],"DNS":x["dns"]} for x in r["interfaces"]])
            self.arp.load_rows([{"IP":x["ip"],"MAC":x["mac"],"النوع":x["type"]} for x in r["arp"]])
            self.routes.load_rows([{"Destination":x["destination"],"Mask":x["mask"],"Gateway":x["gateway"],"Interface":x["interface"],"Metric":x["metric"]} for x in r["routes"]])
            self.wifi_current.load_rows([{"الواجهة":x.get("interface","N/A"),"SSID":x.get("ssid","N/A"),"BSSID":x.get("bssid","N/A"),"الحالة":x.get("state","N/A"),"التوثيق":x.get("authentication","N/A"),"القناة":x.get("channel","N/A"),"الإشارة":x.get("signal","N/A"),"Profile":x.get("profile","N/A")} for x in r["wifi"]])
            self.wifi_profiles.load_rows([{"SSID":x["ssid"],"المصدر":x["source"]} for x in r["profiles"]])
            self.history.load_rows([{"المتصفح":x["browser"],"الملف الشخصي":x["profile"],"URL":x["url"],"العنوان":x["title"],"الزيارات":x["visit_count"],"آخر زيارة":x["last_visit"]} for x in r["history"]])
        self.run_task("جاري جمع أدلة الشبكة والـWi-Fi...", worker, done, "تم تحديث أدلة الشبكة والـWi-Fi")
