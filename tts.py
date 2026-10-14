"""
Text-to-Speech (TTS) Manager for Jenny Voice Assistant.
Thread-safe, non-blocking audio output using native Windows SAPI5 (pyttsx3).
"""

from __future__ import annotations
import queue
import threading
import logging
from typing import Optional
import pythoncom
import pyttsx3
from config import config

logger = logging.getLogger("jenny.tts")

class TTSManager:
    """Thread-safe Windows SAPI5 Text-to-Speech engine."""

    def __init__(self, rate: Optional[int] = None, volume: Optional[float] = None, voice_preference: Optional[str] = None):
        self.rate = rate or config.VOICE_RATE
        self.volume = volume if volume is not None else config.VOICE_VOLUME
        self.voice_preference = (voice_preference or config.VOICE_PREFERENCE).lower()
        
        self._queue: queue.Queue[Optional[tuple[str, threading.Event]]] = queue.Queue()
        self._is_speaking = False
        self._shutdown_event = threading.Event()
        self._worker_thread = threading.Thread(target=self._speech_worker, daemon=True, name="TTS-Worker")
        self._worker_thread.start()

    def _speech_worker(self) -> None:
        """Background thread worker to process speech tasks sequentially with COM initialized."""
        # Initialize COM in this dedicated worker thread
        pythoncom.CoInitialize()
        try:
            engine = pyttsx3.init("sapi5")
            engine.setProperty("rate", self.rate)
            engine.setProperty("volume", self.volume)
            
            # Select preferred voice
            voices = engine.getProperty("voices")
            selected_voice_id = None
            
            for voice in voices:
                v_name = voice.name.lower()
                v_id = voice.id.lower()
                if self.voice_preference in v_name or self.voice_preference in v_id:
                    selected_voice_id = voice.id
                    break
            
            if not selected_voice_id and voices:
                # Default to first available voice
                selected_voice_id = voices[0].id
                
            if selected_voice_id:
                engine.setProperty("voice", selected_voice_id)
                logger.info(f"TTS voice set to: {selected_voice_id}")

            while not self._shutdown_event.is_set():
                try:
                    item = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if item is None:
                    # Shutdown sentinel
                    break

                text, done_event = item
                if not text or not config.ENABLE_SPOKEN_FEEDBACK:
                    done_event.set()
                    self._queue.task_done()
                    continue

                self._is_speaking = True
                try:
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    logger.error(f"Error during speech playback: {e}")
                finally:
                    self._is_speaking = False
                    done_event.set()
                    self._queue.task_done()

        except Exception as e:
            logger.error(f"Failed to initialize SAPI5 TTS engine: {e}")
        finally:
            pythoncom.CoUninitialize()

    def speak(self, text: str, block: bool = False) -> None:
        """
        Speak the given text.
        
        Args:
            text: Text to speak.
            block: If True, waits until speech has completed before returning.
        """
        if not text or not text.strip():
            return
            
        done_event = threading.Event()
        self._queue.put((text.strip(), done_event))
        
        if block:
            done_event.wait()

    def stop(self) -> None:
        """Clear queued speech items."""
        while not self._queue.empty():
            try:
                item = self._queue.get_nowait()
                if item:
                    _, done_event = item
                    done_event.set()
                self._queue.task_done()
            except queue.Empty:
                break

    @property
    def is_speaking(self) -> bool:
        """Returns True if the assistant is currently speaking."""
        return self._is_speaking or not self._queue.empty()

    def shutdown(self) -> None:
        """Cleanly shutdown the worker thread."""
        self._shutdown_event.set()
        self._queue.put(None)
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=1.0)


# Global singleton instance
tts = TTSManager()
