"""
Command Routing and Intent Classification Engine for Jenny Voice Assistant.
Parses natural language utterances, extracts entities, and routes to appropriate action handlers.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional, Any
import logging

from config import config
from actions.system_actions import SystemActions
from actions.app_actions import AppActions
from actions.web_actions import WebActions
from actions.utility_actions import UtilityActions
from actions.ai_actions import AIActions

logger = logging.getLogger("jenny.commander")

@dataclass
class CommandResult:
    """Structured result of an executed command."""
    success: bool
    response: str
    action_type: str
    raw_query: str
    details: dict[str, Any] = field(default_factory=dict)

class CommandEngine:
    """Natural language intent processor and dispatcher."""

    def __init__(self):
        # Compile wake word regex for efficient stripping
        wake_words_escaped = [re.escape(w) for w in config.WAKE_WORDS]
        self._wake_regex = re.compile(
            rf"^(?:hey\s+|ok\s+|hi\s+)?(?:{'|'.join(wake_words_escaped)})\b[,!\?\s]*",
            re.IGNORECASE
        )

    def clean_utterance(self, text: str) -> str:
        """Strip wake words, leading polite words, and extraneous whitespace."""
        cleaned = text.strip()
        # Remove wake word if prefixed
        cleaned = self._wake_regex.sub("", cleaned).strip()
        # Remove polite prefix
        cleaned = re.sub(r"^(?:please|could you|can you|would you)\s+", "", cleaned, flags=re.IGNORECASE).strip()
        # Remove punctuation at end
        cleaned = re.sub(r"[.!?]+$", "", cleaned).strip()
        return cleaned

    def has_wake_word(self, text: str) -> bool:
        """Check if the text contains any configured wake word."""
        lower = text.lower()
        return any(w.lower() in lower for w in config.WAKE_WORDS)

    def execute(self, raw_text: str) -> CommandResult:
        """
        Process and execute a voice or text command.
        
        Args:
            raw_text: The user's input phrase.
            
        Returns:
            CommandResult with execution status, spoken response, and metadata.
        """
        if not raw_text or not raw_text.strip():
            return CommandResult(
                success=False,
                response="I didn't catch that, darling.",
                action_type="empty",
                raw_query=raw_text
            )

        cleaned = self.clean_utterance(raw_text)
        lower = cleaned.lower()

        # If user only said the wake word ("Jenny" / "darling" / "babe")
        if not cleaned:
            return CommandResult(
                success=True,
                response="Yes darling? How can I help you?",
                action_type="wake_ack",
                raw_query=raw_text
            )

        logger.info(f"Processing command: '{cleaned}' (raw: '{raw_text}')")

        # ---------------------------------------------------------
        # 1. System: Volume Controls
        # ---------------------------------------------------------
        # Set exact volume (e.g., "set volume to 50%", "volume 30")
        vol_set_match = re.search(r"(?:set\s+)?(?:volume|sound)\s+(?:to\s+)?(\d{1,3})\s*%?", lower)
        if vol_set_match:
            pct = int(vol_set_match.group(1))
            success, resp = SystemActions.set_volume(pct)
            return CommandResult(success, resp, "system_volume_set", raw_text, {"target_percent": pct})

        if re.search(r"\b(?:volume|sound)\s+up\b|\b(?:turn\s+up|increase)\s+(?:the\s+)?(?:volume|sound)\b|\blouder\b", lower):
            success, resp = SystemActions.volume_up()
            return CommandResult(success, resp, "system_volume_up", raw_text)

        if re.search(r"\b(?:volume|sound)\s+down\b|\b(?:turn\s+down|decrease|lower)\s+(?:the\s+)?(?:volume|sound)\b|\bquieter\b", lower):
            success, resp = SystemActions.volume_down()
            return CommandResult(success, resp, "system_volume_down", raw_text)

        if re.search(r"\b(?:mute|silence|turn off sound)\b", lower):
            success, resp = SystemActions.mute()
            return CommandResult(success, resp, "system_volume_mute", raw_text)

        if re.search(r"\b(?:unmute|restore sound|turn on sound)\b", lower):
            success, resp = SystemActions.unmute()
            return CommandResult(success, resp, "system_volume_unmute", raw_text)

        if re.search(r"\b(?:what is|check)\s+(?:the\s+)?(?:current\s+)?(?:volume|sound)\b", lower):
            vol = SystemActions.get_volume()
            return CommandResult(True, f"The current volume is {vol}%.", "system_volume_query", raw_text, {"volume": vol})

        # ---------------------------------------------------------
        # 2. System: Media Controls
        # ---------------------------------------------------------
        if re.search(r"\b(?:pause|resume|toggle)\s+(?:music|playback|song|video|media)\b|^(?:pause|resume)$", lower):
            success, resp = SystemActions.play_pause_media()
            return CommandResult(success, resp, "system_media_toggle", raw_text)

        if re.search(r"\b(?:next\s+(?:track|song|video)|skip\s+(?:track|song|video))\b", lower):
            success, resp = SystemActions.next_track()
            return CommandResult(success, resp, "system_media_next", raw_text)

        if re.search(r"\b(?:previous\s+(?:track|song|video)|last\s+(?:track|song))\b", lower):
            success, resp = SystemActions.previous_track()
            return CommandResult(success, resp, "system_media_previous", raw_text)

        # ---------------------------------------------------------
        # 3. System: Power, Security & Hardware Stats
        # ---------------------------------------------------------
        if re.search(r"\b(?:lock\s+(?:computer|pc|screen|workstation)|lock\s+my\s+screen)\b", lower):
            success, resp = SystemActions.lock_screen()
            return CommandResult(success, resp, "system_lock", raw_text)

        if re.search(r"\b(?:battery|battery\s+status|check\s+battery|battery\s+percentage)\b", lower):
            success, resp = SystemActions.get_battery_status()
            return CommandResult(success, resp, "system_battery", raw_text)

        if re.search(r"\b(?:system\s+stats|cpu\s+usage|memory\s+status|hardware\s+status|ram\s+usage|pc\s+stats)\b", lower):
            success, resp = SystemActions.get_hardware_status()
            return CommandResult(success, resp, "system_hardware_stats", raw_text)

        # ---------------------------------------------------------
        # 4. System: Visual / Screenshot
        # ---------------------------------------------------------
        if re.search(r"\b(?:take\s+(?:a\s+)?screenshot|capture\s+(?:the\s+)?screen|screenshot)\b", lower):
            success, resp = SystemActions.take_screenshot()
            return CommandResult(success, resp, "system_screenshot", raw_text)

        # ---------------------------------------------------------
        # 5. Apps: Launching & Closing
        # ---------------------------------------------------------
        open_match = re.search(r"^(?:open|launch|start)\s+(.+)$", lower)
        if open_match:
            app_target = open_match.group(1).strip()
            # If target begins with youtube/google, route to web actions
            if "youtube" in app_target:
                success, resp = WebActions.play_youtube("")
                return CommandResult(success, resp, "web_youtube", raw_text)
            elif "google" in app_target:
                success, resp = WebActions.search_google("")
                return CommandResult(success, resp, "web_google", raw_text)
            else:
                success, resp = AppActions.open_app(app_target)
                return CommandResult(success, resp, "app_open", raw_text, {"app": app_target})

        close_match = re.search(r"^(?:close|quit|kill|terminate|exit)\s+(.+)$", lower)
        if close_match:
            app_target = close_match.group(1).strip()
            success, resp = AppActions.close_app(app_target)
            return CommandResult(success, resp, "app_close", raw_text, {"app": app_target})

        # ---------------------------------------------------------
        # 6. Web: YouTube, Search, Wikipedia, Weather
        # ---------------------------------------------------------
        yt_match = re.search(r"(?:play\s+)?(.+?)\s+(?:on\s+youtube|in\s+youtube)$|^(?:play\s+on\s+youtube\s+)(.+)$", lower)
        if yt_match:
            yt_query = (yt_match.group(1) or yt_match.group(2)).strip()
            # Clean "play " prefix if captured
            yt_query = re.sub(r"^play\s+", "", yt_query)
            success, resp = WebActions.play_youtube(yt_query)
            return CommandResult(success, resp, "web_youtube", raw_text, {"query": yt_query})

        if lower.startswith("youtube "):
            yt_query = lower[len("youtube "):].strip()
            success, resp = WebActions.play_youtube(yt_query)
            return CommandResult(success, resp, "web_youtube", raw_text, {"query": yt_query})

        google_match = re.search(r"(?:search\s+(?:google\s+)?(?:for\s+)?|google\s+)(.+)$", lower)
        if google_match and not lower.startswith(("who is", "what is", "where is", "how to")):
            g_query = google_match.group(1).strip()
            success, resp = WebActions.search_google(g_query)
            return CommandResult(success, resp, "web_google_search", raw_text, {"query": g_query})

        weather_match = re.search(r"\b(?:weather\s+in\s+|weather\s+for\s+)(.+)$", lower)
        if weather_match:
            loc = weather_match.group(1).strip()
            success, resp = WebActions.get_weather(loc)
            return CommandResult(success, resp, "web_weather", raw_text, {"location": loc})
        elif re.search(r"\b(?:what's\s+the\s+weather|how's\s+the\s+weather|weather\s+today|check\s+weather)\b", lower):
            success, resp = WebActions.get_weather("")
            return CommandResult(success, resp, "web_weather", raw_text)

        # ---------------------------------------------------------
        # 7. Utilities: Time, Date, Notes, Typing, Clipboard, Math
        # ---------------------------------------------------------
        if re.search(r"\b(?:what\s+time\s+is\s+it|what\s+is\s+the\s+time|current\s+time|tell\s+me\s+the\s+time)\b", lower):
            success, resp = UtilityActions.get_time()
            return CommandResult(success, resp, "utility_time", raw_text)

        if re.search(r"\b(?:what\s+is\s+today's\s+date|what's\s+the\s+date|what\s+is\s+the\s+date|what\s+day\s+is\s+it|today's\s+date)\b", lower):
            success, resp = UtilityActions.get_date()
            return CommandResult(success, resp, "utility_date", raw_text)

        # Notes
        note_match = re.search(r"^(?:take\s+a\s+note|note\s+that|save\s+note|write\s+down)\s*[:]?\s*(.+)$", lower)
        if note_match:
            note_content = note_match.group(1).strip()
            success, resp = UtilityActions.take_note(note_content)
            return CommandResult(success, resp, "utility_note_save", raw_text, {"note": note_content})

        if re.search(r"\b(?:read\s+(?:my\s+)?notes|show\s+(?:my\s+)?notes|what\s+are\s+my\s+notes)\b", lower):
            success, resp = UtilityActions.read_notes()
            return CommandResult(success, resp, "utility_notes_read", raw_text)

        # Typing into active window
        type_match = re.search(r"^type\s+(.+)$", lower)
        if type_match:
            text_to_type = cleaned[len("type "):].strip()
            success, resp = UtilityActions.type_text(text_to_type)
            return CommandResult(success, resp, "utility_type", raw_text, {"text": text_to_type})

        # Clipboard
        if re.search(r"\b(?:read\s+clipboard|what's\s+on\s+my\s+clipboard|clipboard\s+content)\b", lower):
            success, resp = UtilityActions.read_clipboard()
            return CommandResult(success, resp, "utility_clipboard", raw_text)

        # Math / Calculations
        calc_match = re.search(r"^(?:calculate|what\s+is|compute)\s+([\d\s\+\-\*\/\%\.\(\)]+|[\d\s]+(?:times|plus|minus|divided by|multiplied by|percent of)[\d\s\.]+)$", lower)
        if calc_match:
            expr = calc_match.group(1).strip()
            calc_success, calc_resp = UtilityActions.calculate(expr)
            if calc_success:
                return CommandResult(True, calc_resp, "utility_calculate", raw_text, {"expression": expr})

        # ---------------------------------------------------------
        # 8. AI Reasoning / Conversational Brain (Gemini + Offline)
        # ---------------------------------------------------------
        # For all open-ended questions, conversations, or unhandled commands:
        success, resp = AIActions.answer_query(cleaned)
        return CommandResult(success, resp, "ai_conversational", raw_text)
