"""
Configuration settings for Jenny Desktop Voice Assistant.
Centralized typed settings supporting environment variables and custom user preferences.
"""

from __future__ import annotations
import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

# Base project directory
BASE_DIR = Path(__file__).resolve().parent

@dataclass
class AssistantConfig:
    # Base directory
    BASE_DIR: Path = BASE_DIR
    
    # Assistant Identity
    NAME: str = "Jenny"
    WAKE_WORDS: list[str] = field(default_factory=lambda: [
        "jenny",
        "darling",
        "babe",
        "hey jenny",
        "ok jenny",
        "hi jenny",
        "assistant",
        "computer",
    ])
    
    # Trigger & Input Configuration
    PUSH_TO_TALK_HOTKEY: str = os.getenv("PUSH_TO_TALK_HOTKEY", "ctrl+shift+a")
    DEFAULT_TRIGGER_MODE: str = os.getenv("TRIGGER_MODE", "wake_word")  # 'wake_word', 'push_to_talk', 'text'
    
    # Speech-to-Text Settings
    STT_ENERGY_THRESHOLD: int = int(os.getenv("STT_ENERGY_THRESHOLD", "300"))
    STT_DYNAMIC_ENERGY: bool = True
    STT_PAUSE_THRESHOLD: float = float(os.getenv("STT_PAUSE_THRESHOLD", "0.8"))
    STT_PHRASE_TIME_LIMIT: float = float(os.getenv("STT_PHRASE_TIME_LIMIT", "8.0"))
    STT_TIMEOUT: float = float(os.getenv("STT_TIMEOUT", "5.0"))
    
    # Text-to-Speech Settings
    VOICE_RATE: int = int(os.getenv("VOICE_RATE", "185"))  # Words per minute
    VOICE_VOLUME: float = float(os.getenv("VOICE_VOLUME", "1.0"))  # 0.0 to 1.0
    VOICE_PREFERENCE: str = os.getenv("VOICE_PREFERENCE", "zira")  # 'zira' (female) or 'david' (male)
    ENABLE_SPOKEN_FEEDBACK: bool = True
    
    # Storage Paths
    SCREENSHOT_DIR: Path = Path(os.getenv(
        "SCREENSHOT_DIR",
        str(Path.home() / "Pictures" / "Screenshots")
    ))
    NOTES_DIR: Path = BASE_DIR / "notes"
    NOTES_FILE: Path = BASE_DIR / "notes" / "voice_notes.md"
    
    # AI Brain (Gemini)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # Application Registry: Natural language aliases -> Windows command / URI / exe
    APP_REGISTRY: dict[str, str] = field(default_factory=lambda: {
        # Browsers
        "chrome": "chrome",
        "google chrome": "chrome",
        "edge": "msedge",
        "microsoft edge": "msedge",
        "browser": "chrome",
        "firefox": "firefox",
        "brave": "brave",
        
        # Productivity & Office
        "notepad": "notepad",
        "calculator": "calc",
        "calc": "calc",
        "vscode": "code",
        "vs code": "code",
        "visual studio code": "code",
        "word": "winword",
        "ms word": "winword",
        "excel": "excel",
        "ms excel": "excel",
        "powerpoint": "powerpnt",
        
        # System Utilities
        "file explorer": "explorer",
        "explorer": "explorer",
        "my computer": "explorer",
        "files": "explorer",
        "settings": "ms-settings:",
        "control panel": "control",
        "task manager": "taskmgr",
        "terminal": "wt",
        "command prompt": "cmd",
        "cmd": "cmd",
        "powershell": "powershell",
        
        # Media & Entertainment
        "spotify": "spotify",
        "vlc": "vlc",
        "paint": "mspaint",
        "snipping tool": "snippingtool",
    })

    def ensure_directories(self) -> None:
        """Create necessary directories if they do not exist."""
        self.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        self.NOTES_DIR.mkdir(parents=True, exist_ok=True)


# Global singleton configuration instance
config = AssistantConfig()
config.ensure_directories()
