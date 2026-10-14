"""
Jenny Desktop Voice Assistant for Windows.
Main application runner supporting simultaneous Wake Words ("Jenny", "Darling", "Babe"),
Push-to-Talk Hotkey (Ctrl+Shift+A), and Interactive Console Fallback.
"""

from __future__ import annotations
import argparse
import os
import sys
import threading
import time
import signal
import logging

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.panel import Panel
from rich.table import Table
from rich import box
from config import config
from tts import tts
from stt import stt
from commander import CommandEngine, CommandResult
from ui import ui
from actions.system_actions import SystemActions

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(config.BASE_DIR / "assistant.log", encoding="utf-8"),
    ]
)
logger = logging.getLogger("jenny.main")

class AssistantApp:
    """Core controller orchestrating STT, TTS, hotkeys, and command execution."""

    def __init__(self, mode: str = "wake_word"):
        self.mode = mode
        self.commander = CommandEngine()
        self.running = False
        self._processing_lock = threading.Lock()
        self._hotkey_registered = False

    def setup_hotkey(self) -> None:
        """Register global push-to-talk hotkey."""
        try:
            import keyboard
            keyboard.add_hotkey(
                config.PUSH_TO_TALK_HOTKEY,
                self._on_hotkey_pressed,
                suppress=False
            )
            self._hotkey_registered = True
            logger.info(f"Registered global hotkey: {config.PUSH_TO_TALK_HOTKEY}")
        except Exception as e:
            logger.warning(f"Could not register global hotkey ({config.PUSH_TO_TALK_HOTKEY}): {e}")
            ui.show_status(f"Notice: Global hotkey could not be bound ({e}). Microphone voice trigger remains active.", "dim yellow")

    def _on_hotkey_pressed(self) -> None:
        """Handler triggered when the push-to-talk hotkey is pressed."""
        if not self._processing_lock.acquire(blocking=False):
            # Already busy processing
            return

        try:
            ui.show_status(f"Hotkey [{config.PUSH_TO_TALK_HOTKEY.upper()}] detected! Listening...", "bold magenta")
            tts.stop()
            # Capture speech
            spoken_text = stt.listen_phrase(timeout=4.0, phrase_time_limit=7.0)
            if spoken_text:
                self.process_utterance(spoken_text, trigger_source="Hotkey")
            else:
                ui.show_status("No speech detected after hotkey press.", "dim")
        finally:
            self._processing_lock.release()

    def process_utterance(self, text: str, trigger_source: str = "Voice") -> CommandResult:
        """
        Execute command from speech or text input, render visual card, and speak response.
        """
        ui.show_status(f"Processing: \"{text}\"...", "bold cyan")
        
        # Execute command
        result = self.commander.execute(text)
        
        # Log to UI
        ui.log_command(
            query=text,
            response=result.response,
            action_type=result.action_type,
            success=result.success,
            trigger=trigger_source
        )

        # Spoken audio feedback
        if config.ENABLE_SPOKEN_FEEDBACK:
            tts.speak(result.response)

        return result

    def run_text_loop(self) -> None:
        """Interactive console loop for silent typing / test mode."""
        ui.clear()
        ui.print_banner(trigger_mode="Interactive Text Mode")
        ui.print_cheat_sheet()
        ui.console.print("[bold green]Type your commands below. Type 'exit' or 'quit' to close.[/bold green]\n")

        while self.running:
            try:
                user_input = ui.console.input("[bold cyan]You > [/bold cyan]")
                if not user_input or not user_input.strip():
                    continue

                if user_input.strip().lower() in ["exit", "quit", "q"]:
                    ui.console.print("[bold magenta]Goodbye, darling![/bold magenta]")
                    tts.speak("Goodbye darling!", block=True)
                    break

                self.process_utterance(user_input.strip(), trigger_source="Text Console")

            except (KeyboardInterrupt, EOFError):
                break

    def run_continuous_voice_loop(self) -> None:
        """
        Continuous listening loop detecting wake words and hotkey presses concurrently.
        """
        ui.clear()
        ui.print_banner(trigger_mode="Voice & Hotkey Combined")
        ui.print_cheat_sheet()

        # Check microphone
        mic = stt.get_microphone()
        if not mic:
            ui.show_status("Microphone not detected! Falling back to interactive text mode.", "bold red")
            self.run_text_loop()
            return

        ui.show_status("Calibrating microphone for ambient room noise...", "bold yellow")
        stt.calibrate(duration=1.2)
        ui.show_status("Microphone calibrated and ready!", "bold green")

        # Register hotkey
        self.setup_hotkey()

        wake_words_display = " / ".join([f'"{w.title()}"' for w in config.WAKE_WORDS[:3]])
        ui.console.print(
            f"\n[bold green]🎧 Listening in background... "
            f"Say {wake_words_display} or press [bold yellow]{config.PUSH_TO_TALK_HOTKEY.upper()}[/bold yellow] to speak![/bold green]\n"
        )
        tts.speak("Jenny is online and ready.", block=False)

        while self.running:
            try:
                # If currently processing hotkey or busy, skip
                if self._processing_lock.locked() or tts.is_speaking:
                    time.sleep(0.2)
                    continue

                # Listen for speech phrase
                phrase = stt.listen_phrase(timeout=2.0, phrase_time_limit=6.0)
                if not phrase:
                    continue

                # Check if phrase contains wake word or if mode is direct push-to-talk
                if stt.contains_wake_word(phrase):
                    with self._processing_lock:
                        self.process_utterance(phrase, trigger_source="Wake Word")

            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                logger.error(f"Error in main listening loop: {e}")
                time.sleep(0.5)

    def start(self) -> None:
        """Start the assistant application in the requested mode."""
        self.running = True

        def _signal_handler(sig, frame):
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, _signal_handler)

        if self.mode == "text":
            self.run_text_loop()
        else:
            self.run_continuous_voice_loop()

    def stop(self) -> None:
        """Clean shutdown."""
        self.running = False
        tts.stop()
        tts.shutdown()
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass


def run_diagnostics() -> None:
    """Run comprehensive system, audio, and hardware diagnostics."""
    ui.clear()
    ui.console.print(Panel("[bold cyan]Jenny Voice Assistant - System Diagnostics[/bold cyan]", box=box.ROUNDED))
    
    # 1. Microphone Check
    mic_status = "❌ Unavailable"
    try:
        import speech_recognition as sr
        mics = sr.Microphone.list_microphone_names()
        if mics:
            mic_status = f"✅ Available ({len(mics)} audio inputs found, default: {mics[0]})"
    except Exception as e:
        mic_status = f"❌ Error: {e}"
        
    # 2. Text-to-Speech Check
    tts_status = "❌ Unavailable"
    try:
        import pyttsx3
        eng = pyttsx3.init("sapi5")
        voices = eng.getProperty("voices")
        voice_names = ", ".join([v.name for v in voices[:2]])
        tts_status = f"✅ SAPI5 Online ({len(voices)} voices: {voice_names})"
    except Exception as e:
        tts_status = f"❌ Error: {e}"

    # 3. Audio Volume Control Check
    vol_status = "❌ Unavailable"
    try:
        vol = SystemActions.get_volume()
        vol_status = f"✅ pycaw Audio Endpoint Active (Master Volume: {vol}%)"
    except Exception as e:
        vol_status = f"❌ Error: {e}"

    # 4. Hardware Stats
    hw_success, hw_info = SystemActions.get_hardware_status()
    hw_status = f"✅ {hw_info}" if hw_success else f"❌ {hw_info}"

    # 5. Battery Status
    bat_success, bat_info = SystemActions.get_battery_status()
    bat_status = f"✅ {bat_info}" if bat_success else f"❌ {bat_info}"

    table = Table(box=box.ROUNDED)
    table.add_column("Component", style="bold yellow")
    table.add_column("Status / Details", style="white")

    table.add_row("Microphone (STT)", mic_status)
    table.add_row("Speech Engine (TTS)", tts_status)
    table.add_row("Windows Audio Endpoint", vol_status)
    table.add_row("System Hardware", hw_status)
    table.add_row("Battery / Power", bat_status)

    ui.console.print(table)
    ui.console.print("\n[bold green]Diagnostics complete! All essential subsystems operational.[/bold green]\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Jenny Windows Desktop Voice Assistant")
    parser.add_argument("--text", action="store_true", help="Launch in interactive text console mode (no mic needed)")
    parser.add_argument("--push-to-talk", action="store_true", help="Launch in push-to-talk hotkey mode")
    parser.add_argument("--diagnostics", action="store_true", help="Run hardware & subsystem diagnostics")
    args = parser.parse_args()

    if args.diagnostics:
        run_diagnostics()
        return

    mode = "text" if args.text else ("push_to_talk" if args.push_to_talk else "wake_word")
    app = AssistantApp(mode=mode)
    try:
        app.start()
    except (KeyboardInterrupt, SystemExit):
        app.stop()


if __name__ == "__main__":
    main()
