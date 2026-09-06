"""Command execution evidence on Windows.

Sources are intentionally separated because there is no universal persistent
history file for classic CMD. When auditing is enabled, Security 4688 can
provide process creation command lines; PowerShell 4104 can provide script
block contents; PSReadLine provides the user's interactive PowerShell history.
"""
from __future__ import annotations

import csv
import io
import json
import os
import subprocess
from typing import Dict, List


def _ps(script: str, timeout: int = 40) -> str:
    try:
        flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        completed = subprocess.run(["powershell", "-NoProfile", "-Command", script],
                                   capture_output=True, text=True, timeout=timeout,
                                   creationflags=flags, encoding="utf-8", errors="replace")
        return completed.stdout or ""
    except Exception:
        return ""


def get_powershell_history() -> List[Dict]:
    results: List[Dict] = []
    app_data = os.environ.get("APPDATA", "")
    history_path = os.path.join(app_data, "Microsoft", "Windows", "PowerShell", "PSReadLine", "ConsoleHost_history.txt")
    if not os.path.isfile(history_path):
        return results
    try:
        with open(history_path, "r", encoding="utf-8", errors="ignore") as handle:
            lines = handle.readlines()
        mtime = os.path.getmtime(history_path)
    except Exception:
        return results
    for line_number, raw in enumerate(lines, 1):
        command = raw.strip()
        if command:
            results.append({"line": line_number, "command": command, "source_file": history_path,
                            "file_last_modified": mtime, "source": "PSReadLine"})
    results.reverse()
    return results


def get_running_shell_processes() -> List[Dict]:
    script = ("Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(cmd|powershell|pwsh)\\.exe$' } | "
              "Select-Object ProcessId,ParentProcessId,Name,CommandLine,CreationDate | ConvertTo-Csv -NoTypeInformation")
    output = _ps(script)
    lines = [l for l in output.splitlines() if l.strip()]
    if len(lines) < 2:
        return []
    rows = []
    try:
        for row in csv.DictReader(io.StringIO("\n".join(lines))):
            rows.append({"pid": row.get("ProcessId", ""), "parent_pid": row.get("ParentProcessId", ""),
                         "name": row.get("Name", ""), "command_line": row.get("CommandLine", ""),
                         "created": row.get("CreationDate", "")})
    except Exception:
        pass
    return rows


def get_process_creation_command_events(max_events: int = 300) -> List[Dict]:
    """Extract command lines from Security 4688 when process auditing is enabled."""
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"Get-WinEvent -FilterHashtable @{{LogName='Security';Id=4688}} -MaxEvents {max_events} | "
        "ForEach-Object { $p=$_.Properties; [pscustomobject]@{TimeCreated=$_.TimeCreated; "
        "Message=($_.Message -replace \"`r`n\",' '); RecordId=$_.RecordId} } | ConvertTo-Json -Compress"
    )
    out = _ps(script)
    try:
        parsed = json.loads(out)
        if isinstance(parsed, dict): parsed = [parsed]
    except Exception:
        return []
    results = []
    for item in parsed:
        msg = item.get("Message") or ""
        low = msg.lower()
        if not any(x in low for x in ("cmd.exe", "powershell.exe", "pwsh.exe")):
            continue
        process_name = "N/A"
        command_line = ""
        parent_pid = "N/A"
        for label in ("New Process Name:", "اسم العملية الجديدة:"):
            marker = label.lower()
            pos = low.find(marker.lower())
            if pos >= 0:
                tail = msg[pos + len(label):].splitlines()[0].strip()
                process_name = tail
                break
        for label in ("Process Command Line:", "سطر أوامر العملية:"):
            pos = low.find(label.lower())
            if pos >= 0:
                command_line = msg[pos + len(label):].splitlines()[0].strip()
                break
        for label in ("Creator Process ID:", "معرف عملية المنشئ:"):
            pos = low.find(label.lower())
            if pos >= 0:
                parent_pid = msg[pos + len(label):].splitlines()[0].strip()
                break
        display = command_line or process_name or msg[:1000]
        results.append({"time": item.get("TimeCreated", "N/A"), "record_id": item.get("RecordId", "N/A"),
                        "process_name": process_name, "parent_pid": parent_pid,
                        "command": display[:2000], "source": "Security 4688"})
    return results


def get_powershell_script_events(max_events: int = 300) -> List[Dict]:
    """Read PowerShell Script Block Logging (4104), if it is enabled."""
    script = (
        "$ErrorActionPreference='SilentlyContinue';"
        f"Get-WinEvent -FilterHashtable @{{LogName='Microsoft-Windows-PowerShell/Operational';Id=4104}} -MaxEvents {max_events} | "
        "Select-Object Id,RecordId,TimeCreated,@{N='Message';E={$_.Message -replace \"`r`n\",' '}} | "
        "ConvertTo-Json -Compress"
    )
    out = _ps(script)
    try:
        parsed = json.loads(out)
        if isinstance(parsed, dict): parsed = [parsed]
    except Exception:
        return []
    return [{"event_id": x.get("Id"), "record_id": x.get("RecordId"),
             "time": x.get("TimeCreated"), "script": (x.get("Message") or "")[:2000],
             "source": "PowerShell 4104"} for x in parsed]
