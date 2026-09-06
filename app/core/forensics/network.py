"""Windows network and Wi-Fi forensic collectors (read-only)."""
from __future__ import annotations

import csv
import io
import json
import re
import subprocess
from typing import Dict, List

_NETSTAT_LINE_RE = re.compile(
    r"^\s*(?P<proto>TCP|TCP6|UDP|UDP6)\s+"
    r"(?P<local>[\[\]0-9a-fA-F\.\:]+)\s+"
    r"(?P<remote>[\[\]0-9a-fA-F\.\:\*]+)\s+"
    r"(?:(?P<state>\S+)\s+)?(?P<pid>\d+)\s*$"
)


def _run(cmd: list, timeout: int = 25) -> str:
    try:
        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        completed = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                                   creationflags=flags, encoding="utf-8", errors="replace")
        return completed.stdout or ""
    except Exception:
        return ""


def _process_map() -> Dict[str, str]:
    out = _run(["powershell", "-NoProfile", "-Command",
                "Get-CimInstance Win32_Process | Select-Object ProcessId,Name | ConvertTo-Csv -NoTypeInformation"])
    result = {}
    lines = [x for x in out.splitlines() if x.strip()]
    if len(lines) < 2:
        return result
    try:
        for row in csv.DictReader(io.StringIO("\n".join(lines))):
            result[str(row.get("ProcessId", ""))] = row.get("Name", "N/A") or "N/A"
    except Exception:
        pass
    return result


def get_active_connections() -> List[Dict]:
    output = _run(["netstat", "-ano"])
    process_map = _process_map()
    connections: List[Dict] = []
    for line in output.splitlines():
        match = _NETSTAT_LINE_RE.match(line)
        if not match:
            continue
        pid = match.group("pid")
        connections.append({
            "protocol": match.group("proto"),
            "local_address": match.group("local"),
            "remote_address": match.group("remote"),
            "state": match.group("state") or "-",
            "pid": pid,
            "process_name": process_map.get(pid, "N/A"),
        })
    return connections


def get_dns_cache() -> List[Dict]:
    output = _run(["ipconfig", "/displaydns"])
    entries: List[Dict] = []
    current_host = None
    current_type = "N/A"
    for raw_line in output.splitlines():
        line = raw_line.strip()
        low = line.lower()
        if not line:
            continue
        if low.startswith("record name"):
            current_host = line.split(":", 1)[1].strip() if ":" in line else line
        elif low.startswith("record type"):
            current_type = line.split(":", 1)[1].strip() if ":" in line else current_type
        elif current_host and (re.match(r"^\d+\.\d+\.\d+\.\d+$", line) or "record" in low and "name" not in low):
            entries.append({"hostname": current_host, "record_type": current_type, "data": line})
    return entries


def get_network_interfaces() -> List[Dict]:
    script = (
        "Get-NetIPConfiguration | ForEach-Object { [pscustomobject]@{"
        "InterfaceAlias=$_.InterfaceAlias; InterfaceIndex=$_.InterfaceIndex; "
        "Profile=if ($_.NetProfile) {$_.NetProfile.Name} else {'N/A'}; "
        "IPv4=(@($_.IPv4Address | ForEach-Object {$_.IPAddress}) -join ' | '); "
        "IPv6=(@($_.IPv6Address | ForEach-Object {$_.IPAddress}) -join ' | '); "
        "DNS=(@($_.DNSServer.ServerAddresses) -join ' | ') } } | ConvertTo-Json -Compress"
    )
    out = _run(["powershell", "-NoProfile", "-Command", script])
    try:
        parsed = json.loads(out)
        if isinstance(parsed, dict): parsed = [parsed]
    except Exception:
        return []
    return [{"name": str(x.get("InterfaceAlias", "N/A")), "index": str(x.get("InterfaceIndex", "N/A")),
             "profile": str(x.get("Profile", "N/A")), "ipv4": str(x.get("IPv4", "N/A")),
             "ipv6": str(x.get("IPv6", "N/A")), "dns": str(x.get("DNS", "N/A"))} for x in parsed]


def get_arp_table() -> List[Dict]:
    out = _run(["arp", "-a"])
    rows = []
    for line in out.splitlines():
        m = re.match(r"\s*(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{11,17})\s+(\w+)", line)
        if m:
            rows.append({"ip": m.group(1), "mac": m.group(2), "type": m.group(3)})
    return rows


def get_routes() -> List[Dict]:
    out = _run(["route", "print", "-4"])
    rows = []
    in_table = False
    for line in out.splitlines():
        if "Active Routes" in line or "الشبكات النشطة" in line:
            in_table = True
            continue
        if not in_table:
            continue
        m = re.match(r"\s*(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+)\s*$", line)
        if m and re.match(r"\d+\.\d+\.\d+\.\d+", m.group(1)):
            rows.append({"destination": m.group(1), "mask": m.group(2), "gateway": m.group(3), "interface": m.group(4), "metric": m.group(5)})
    return rows


def get_wifi_profiles() -> List[Dict]:
    out = _run(["netsh", "wlan", "show", "profiles"])
    rows = []
    seen = set()
    for line in out.splitlines():
        m = re.search(r":\s*(.+)$", line)
        if not m or "profile" not in line.lower() and "profil" not in line.lower():
            continue
        name = m.group(1).strip().strip('"')
        if name and name not in seen and name.lower() not in {"profiles", "profile"}:
            seen.add(name)
            rows.append({"ssid": name, "source": "netsh wlan show profiles"})
    return rows


def get_wifi_interfaces() -> List[Dict]:
    out = _run(["netsh", "wlan", "show", "interfaces"])
    rows = []
    current = {}
    for raw in out.splitlines():
        line = raw.strip()
        if not line:
            if current:
                rows.append(current); current = {}
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        mapping = {
            "name": "interface", "description": "description", "guid": "guid",
            "physical address": "mac", "state": "state", "ssid": "ssid",
            "bssid": "bssid", "network type": "network_type", "radio type": "radio",
            "authentication": "authentication", "channel": "channel", "signal": "signal",
            "receive rate (mbps)": "receive_rate", "transmit rate (mbps)": "transmit_rate",
            "profile": "profile",
        }
        for needle, dest in mapping.items():
            if needle in key:
                current[dest] = value
                break
    if current:
        rows.append(current)
    return rows
