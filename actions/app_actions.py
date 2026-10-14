"""
Application Launcher and Process Manager for Jenny Voice Assistant.
Handles opening, focusing, and terminating Windows desktop applications.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import time
from typing import Optional, Tuple
import logging
import psutil
from config import config

logger = logging.getLogger("jenny.app_actions")

# Process name mappings for clean termination
PROCESS_MAP: dict[str, list[str]] = {
    "chrome": ["chrome.exe"],
    "google chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "microsoft edge": ["msedge.exe"],
    "firefox": ["firefox.exe"],
    "brave": ["brave.exe"],
    "notepad": ["notepad.exe"],
    "calculator": ["CalculatorApp.exe", "calc.exe", "Calculator.exe"],
    "calc": ["CalculatorApp.exe", "calc.exe", "Calculator.exe"],
    "vscode": ["Code.exe"],
    "vs code": ["Code.exe"],
    "code": ["Code.exe"],
    "spotify": ["Spotify.exe"],
    "vlc": ["vlc.exe"],
    "word": ["WINWORD.EXE"],
    "excel": ["EXCEL.EXE"],
    "powerpoint": ["POWERPNT.EXE"],
    "task manager": ["Taskmgr.exe"],
    "paint": ["mspaint.exe"],
    "terminal": ["WindowsTerminal.exe", "wt.exe"],
    "command prompt": ["cmd.exe"],
    "cmd": ["cmd.exe"],
    "powershell": ["powershell.exe"],
}

class AppActions:
    """Controls Windows desktop applications."""

    @classmethod
    def open_app(cls, app_name: str) -> Tuple[bool, str]:
        """
        Launch an application by its natural language name or alias.
        
        Args:
            app_name: Name of the application (e.g., 'chrome', 'calculator', 'notepad').
        """
        cleaned_name = app_name.strip().lower()
        target = config.APP_REGISTRY.get(cleaned_name, cleaned_name)

        try:
            # 1. Check if it's a protocol URI or direct startfile candidate
            if ":" in target or target in ["explorer", "notepad", "calc", "taskmgr", "mspaint", "snippingtool", "wt", "cmd", "powershell"]:
                os.startfile(target)
                return True, f"Opening {cleaned_name}."

            # 2. Check if the command exists on PATH
            if shutil.which(target):
                subprocess.Popen([target], shell=True)
                return True, f"Opening {cleaned_name}."

            # 3. Try os.startfile directly (handles Windows registered app shortcuts)
            try:
                os.startfile(target)
                return True, f"Opening {cleaned_name}."
            except Exception:
                pass

            # 4. Fallback: try Windows 'start' command via shell
            cmd = f'start "" "{target}"'
            proc = subprocess.Popen(cmd, shell=True)
            return True, f"Opening {cleaned_name}."

        except Exception as e:
            logger.error(f"Error launching application '{app_name}': {e}")
            return False, f"Could not open {app_name}: {e}"

    @classmethod
    def close_app(cls, app_name: str) -> Tuple[bool, str]:
        """
        Close/terminate running instances of an application.
        
        Args:
            app_name: Name of the application (e.g., 'notepad', 'chrome', 'calculator').
        """
        cleaned_name = app_name.strip().lower()
        candidates = PROCESS_MAP.get(cleaned_name, [f"{cleaned_name}.exe"])
        candidates_lower = [c.lower() for c in candidates]

        terminated_count = 0
        try:
            for proc in psutil.process_iter(["pid", "name"]):
                try:
                    pname = proc.info["name"]
                    if pname and pname.lower() in candidates_lower:
                        proc.terminate()
                        terminated_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            if terminated_count > 0:
                return True, f"Closed {cleaned_name}."
            else:
                return False, f"{cleaned_name} does not appear to be running."

        except Exception as e:
            logger.error(f"Error closing application '{app_name}': {e}")
            return False, f"Failed to close {app_name}: {e}"

    @classmethod
    def list_supported_apps(cls) -> list[str]:
        """Return list of standard supported application aliases."""
        return sorted(list(config.APP_REGISTRY.keys()))
