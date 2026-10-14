"""
Interactive Rich Terminal Interface for Jenny Voice Assistant.
Displays live status banners, animated listening indicators, and formatted command logs.
"""

from __future__ import annotations
import os
import sys
from datetime import datetime
from typing import Optional

# Reconfigure Windows stdout to UTF-8
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from config import config

console = Console(force_terminal=True, legacy_windows=False)

class AssistantUI:
    """Rich console user interface and visual logging."""

    def __init__(self):
        self.console = console
        self._history: list[dict] = []

    def clear(self) -> None:
        """Clear the console screen."""
        os.system("cls" if os.name == "nt" else "clear")

    def print_banner(self, trigger_mode: str = "wake_word") -> None:
        """Render the welcome banner and system status header."""
        title_text = Text()
        title_text.append("✨ JENNY ✨\n", style="bold magenta")
        title_text.append("Modular Desktop Voice Assistant for Windows\n", style="bold cyan")
        title_text.append("System Automation • Productivity • AI Reasoning\n\n", style="italic white")
        
        wake_list = ", ".join([f'"{w.capitalize()}"' for w in config.WAKE_WORDS[:3]])
        title_text.append(f"🎙️  Voice Wake Words: ", style="bold green")
        title_text.append(f"{wake_list}\n", style="bright_yellow")
        
        title_text.append(f"⌨️  Push-to-Talk Hotkey: ", style="bold green")
        title_text.append(f"{config.PUSH_TO_TALK_HOTKEY.upper()}\n", style="bright_yellow")
        
        title_text.append(f"⚡ Active Mode: ", style="bold green")
        title_text.append(f"{trigger_mode.replace('_', ' ').title()}\n", style="bold bright_blue")

        banner = Panel(
            title_text,
            box=box.ROUNDED,
            border_style="magenta",
            padding=(1, 2)
        )
        self.console.print(banner)

    def print_cheat_sheet(self) -> None:
        """Render an organized table of sample commands."""
        table = Table(title="💡 Quick Voice Command Cheat Sheet", box=box.SIMPLE_HEAVY)
        table.add_column("Category", style="bold cyan", width=16)
        table.add_column("Sample Spoken Commands", style="white")

        table.add_row(
            "🔊 Volume",
            '"Set volume to 40%", "Volume up", "Volume down", "Mute", "Unmute"'
        )
        table.add_row(
            "⏯️ Media",
            '"Pause music", "Resume", "Next track", "Previous track"'
        )
        table.add_row(
            "💻 Windows Apps",
            '"Open Chrome", "Launch Calculator", "Open Notepad", "Close Chrome", "Open Settings"'
        )
        table.add_row(
            "🔒 Security & Power",
            '"Lock computer", "Battery status", "Check hardware status"'
        )
        table.add_row(
            "📸 Visual",
            '"Take a screenshot"'
        )
        table.add_row(
            "🌐 Web & Search",
            '"Play jazz on YouTube", "Search Google for space news", "Who is Alan Turing", "Weather in London"'
        )
        table.add_row(
            "📝 Productivity",
            '"What is the time", "What\'s today\'s date", "Take a note: Meeting at 3pm", "Read notes", "Type Hello World"'
        )
        table.add_row(
            "🧠 AI & Knowledge",
            '"Tell me a joke", "Explain quantum computing", "What is 45 times 12", "Who are you"'
        )

        self.console.print(table)
        self.console.print()

    def show_status(self, status: str, style: str = "bold yellow") -> None:
        """Display a status notification badge."""
        self.console.print(f"[{style}]► {status}[/{style}]")

    def log_command(
        self,
        query: str,
        response: str,
        action_type: str,
        success: bool = True,
        trigger: str = "Voice"
    ) -> None:
        """
        Record and display an executed command card.
        """
        timestamp = datetime.now().strftime("%I:%M:%S %p")
        status_symbol = "✅" if success else "❌"
        border_color = "green" if success else "red"

        card_content = Text()
        card_content.append(f"User: ", style="bold cyan")
        card_content.append(f'"{query}"\n', style="italic bright_white")
        card_content.append(f"Jenny: ", style="bold magenta")
        card_content.append(f"{response}\n\n", style="white")
        card_content.append(f"Action: {action_type}  |  Trigger: {trigger}  |  Time: {timestamp}", style="dim")

        panel = Panel(
            card_content,
            title=f"{status_symbol} Command Result",
            border_style=border_color,
            box=box.ROUNDED,
            padding=(0, 2)
        )
        self.console.print(panel)


# Global singleton UI instance
ui = AssistantUI()
