"""
Speech-to-Text (STT) and Audio Input Layer for Jenny Voice Assistant.
Manages microphone capture, noise calibration, wake-word detection, and hotkey push-to-talk.
"""

from __future__ import annotations
import threading
import time
import logging
from typing import Optional, Callable
import speech_recognition as sr
from config import config

logger = logging.getLogger("jenny.stt")

class STTListener:
    """Manages audio capture, microphone calibration, and speech recognition."""

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = config.STT_ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = config.STT_DYNAMIC_ENERGY
        self.recognizer.pause_threshold = config.STT_PAUSE_THRESHOLD
        self._microphone: Optional[sr.Microphone] = None
        self._calibrated = False

    def get_microphone(self) -> Optional[sr.Microphone]:
        """Lazy initialization of the default microphone."""
        if self._microphone is None:
            try:
                self._microphone = sr.Microphone()
            except Exception as e:
                logger.error(f"Failed to access microphone: {e}")
                self._microphone = None
        return self._microphone

    def calibrate(self, duration: float = 1.0) -> bool:
        """
        Calibrate energy threshold for ambient room noise.
        
        Args:
            duration: Seconds to sample room noise.
        """
        mic = self.get_microphone()
        if not mic:
            logger.warning("Microphone not available for calibration.")
            return False

        try:
            with mic as source:
                logger.info(f"Calibrating for ambient noise ({duration}s)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                self._calibrated = True
                logger.info(f"Microphone calibrated. Energy threshold: {self.recognizer.energy_threshold:.1f}")
                return True
        except Exception as e:
            logger.error(f"Error during noise calibration: {e}")
            return False

    def listen_phrase(self, timeout: Optional[float] = None, phrase_time_limit: Optional[float] = None) -> Optional[str]:
        """
        Listen for a single spoken phrase from the microphone.
        
        Args:
            timeout: Max seconds to wait for speech to start.
            phrase_time_limit: Max seconds for a single phrase.
            
        Returns:
            Recognized text as string, or None if timed out/unintelligible.
        """
        mic = self.get_microphone()
        if not mic:
            return None

        if not self._calibrated:
            self.calibrate(duration=0.5)

        timeout = timeout or config.STT_TIMEOUT
        phrase_time_limit = phrase_time_limit or config.STT_PHRASE_TIME_LIMIT

        try:
            with mic as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            # Recognize speech using Google Web Speech API (standard, reliable, zero setup)
            text = self.recognizer.recognize_google(audio)
            logger.info(f"Recognized speech: '{text}'")
            return text.strip()

        except sr.WaitTimeoutError:
            logger.debug("Listening timed out waiting for speech.")
            return None
        except sr.UnknownValueError:
            logger.debug("Speech was unintelligible.")
            return None
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            return None
        except Exception as e:
            logger.error(f"Audio capture error: {e}")
            return None

    def contains_wake_word(self, text: Optional[str]) -> bool:
        """Check if recognized phrase includes any configured wake word."""
        if not text:
            return False
        lower = text.lower()
        return any(w.lower() in lower for w in config.WAKE_WORDS)


# Global singleton listener instance
stt = STTListener()
