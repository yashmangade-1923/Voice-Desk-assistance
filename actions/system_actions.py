"""
System Actions for Jenny Voice Assistant.
Controls Windows Master Volume, Media playback, Power/Security, and Hardware statistics.
"""

from __future__ import annotations
import ctypes
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import logging
import psutil
import pyautogui
import pythoncom
from pycaw.pycaw import AudioUtilities
from config import config

logger = logging.getLogger("jenny.system_actions")

class SystemActions:
    """Windows system, audio, media, and hardware controllers."""

    @staticmethod
    def _get_volume_endpoint():
        """Retrieve the master volume COM endpoint with COM initialized."""
        pythoncom.CoInitialize()
        speakers = AudioUtilities.GetSpeakers()
        if hasattr(speakers, "EndpointVolume"):
            return speakers.EndpointVolume
        return None

    @classmethod
    def get_volume(cls) -> int:
        """Get current master volume as an integer percentage (0-100)."""
        try:
            vol = cls._get_volume_endpoint()
            if vol:
                scalar = vol.GetMasterVolumeLevelScalar()
                return round(scalar * 100)
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
        return 50

    @classmethod
    def set_volume(cls, percent: int) -> Tuple[bool, str]:
        """
        Set master volume to an exact percentage (0-100).
        
        Args:
            percent: Desired volume level from 0 to 100.
        """
        try:
            target = max(0, min(100, int(percent)))
            vol = cls._get_volume_endpoint()
            if not vol:
                return False, "Could not access Windows audio endpoint."
            
            # If muted, unmute when setting volume
            if vol.GetMute():
                vol.SetMute(0, None)
                
            scalar = target / 100.0
            vol.SetMasterVolumeLevelScalar(scalar, None)
            return True, f"Volume set to {target}%."
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False, f"Failed to set volume: {e}"

    @classmethod
    def volume_up(cls, step: int = 10) -> Tuple[bool, str]:
        """Increase master volume by given percentage step."""
        current = cls.get_volume()
        new_level = min(100, current + step)
        return cls.set_volume(new_level)

    @classmethod
    def volume_down(cls, step: int = 10) -> Tuple[bool, str]:
        """Decrease master volume by given percentage step."""
        current = cls.get_volume()
        new_level = max(0, current - step)
        return cls.set_volume(new_level)

    @classmethod
    def mute(cls) -> Tuple[bool, str]:
        """Mute master audio."""
        try:
            vol = cls._get_volume_endpoint()
            if vol:
                vol.SetMute(1, None)
                return True, "Audio muted."
        except Exception as e:
            logger.error(f"Error muting audio: {e}")
        return False, "Failed to mute audio."

    @classmethod
    def unmute(cls) -> Tuple[bool, str]:
        """Unmute master audio."""
        try:
            vol = cls._get_volume_endpoint()
            if vol:
                vol.SetMute(0, None)
                return True, "Audio unmuted."
        except Exception as e:
            logger.error(f"Error unmuting audio: {e}")
        return False, "Failed to unmute audio."

    @classmethod
    def play_pause_media(cls) -> Tuple[bool, str]:
        """Toggle media playback (play/pause)."""
        try:
            pyautogui.press("playpause")
            return True, "Media toggled."
        except Exception as e:
            logger.error(f"Error toggling media: {e}")
            return False, "Failed to toggle media."

    @classmethod
    def next_track(cls) -> Tuple[bool, str]:
        """Skip to next media track."""
        try:
            pyautogui.press("nexttrack")
            return True, "Skipped to next track."
        except Exception as e:
            logger.error(f"Error skipping track: {e}")
            return False, "Failed to skip track."

    @classmethod
    def previous_track(cls) -> Tuple[bool, str]:
        """Return to previous media track."""
        try:
            pyautogui.press("prevtrack")
            return True, "Returned to previous track."
        except Exception as e:
            logger.error(f"Error going to previous track: {e}")
            return False, "Failed to go to previous track."

    @classmethod
    def lock_screen(cls) -> Tuple[bool, str]:
        """Lock the Windows workstation immediately."""
        try:
            result = ctypes.windll.user32.LockWorkStation()
            if result != 0:
                return True, "Computer locked."
            return False, "Lock screen command failed."
        except Exception as e:
            logger.error(f"Error locking computer: {e}")
            return False, f"Failed to lock computer: {e}"

    @classmethod
    def get_battery_status(cls) -> Tuple[bool, str]:
        """Report battery percentage and charging state."""
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return True, "This device is running on AC power without a battery."
            
            percent = int(battery.percent)
            plugged = battery.power_plugged
            status = "plugged in and charging" if plugged else "running on battery"
            
            if plugged and percent >= 100:
                status = "plugged in and fully charged"
                
            return True, f"Battery is at {percent}%, currently {status}."
        except Exception as e:
            logger.error(f"Error checking battery: {e}")
            return False, "Unable to read battery status."

    @classmethod
    def get_hardware_status(cls) -> Tuple[bool, str]:
        """Report CPU usage, Memory (RAM) percentage, and C drive storage."""
        try:
            cpu = psutil.cpu_percent(interval=0.3)
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage("C:\\")
            
            used_gb = round(mem.used / (1024 ** 3), 1)
            total_gb = round(mem.total / (1024 ** 3), 1)
            free_disk_gb = round(disk.free / (1024 ** 3), 1)
            
            summary = (
                f"CPU usage is at {cpu}%. "
                f"RAM usage is {mem.percent}% ({used_gb} GB used of {total_gb} GB). "
                f"Free space on C drive is {free_disk_gb} GB."
            )
            return True, summary
        except Exception as e:
            logger.error(f"Error reading system statistics: {e}")
            return False, "Failed to retrieve system hardware statistics."

    @classmethod
    def take_screenshot(cls, filename: Optional[str] = None) -> Tuple[bool, str]:
        """Capture the screen and save to the configured Screenshots directory."""
        try:
            config.ensure_directories()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = filename or f"screenshot_{timestamp}.png"
            target_path = config.SCREENSHOT_DIR / fname
            
            img = pyautogui.screenshot()
            img.save(str(target_path))
            return True, f"Screenshot captured and saved to {target_path.name}."
        except Exception as e:
            logger.error(f"Error capturing screenshot: {e}")
            return False, f"Failed to capture screenshot: {e}"
