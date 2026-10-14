"""
AI Reasoning and Conversational Engine for Jenny Voice Assistant.
Integrates Google Gemini API with smart offline fallback for open-ended queries.
"""

from __future__ import annotations
import os
import re
import logging
from typing import Tuple, Optional
from config import config

logger = logging.getLogger("jenny.ai_actions")

SYSTEM_PERSONA = (
    "You are Jenny, a brilliant, witty, warm, and helpful desktop voice assistant for Windows. "
    "You address the user warmly. Keep answers concise, natural, and conversational "
    "(typically 1 to 3 sentences suitable for clear spoken text-to-speech feedback, "
    "unless the user specifically asks for code, a draft, or a long explanation). "
    "Do not use markdown headers, bold asterisks, or bullet characters that sound awkward when spoken aloud."
)

class AIActions:
    """Conversational AI brain using Google Gemini API or smart local fallback."""

    _gemini_client = None

    @classmethod
    def _get_client(cls):
        """Lazy initialization of Google GenAI client."""
        if cls._gemini_client is None:
            api_key = config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
            if api_key:
                try:
                    from google import genai
                    cls._gemini_client = genai.Client(api_key=api_key)
                    logger.info("Initialized Google GenAI client successfully.")
                except Exception as e:
                    logger.warning(f"Failed to initialize Google GenAI client: {e}")
                    cls._gemini_client = None
        return cls._gemini_client

    @classmethod
    def answer_query(cls, query: str) -> Tuple[bool, str]:
        """
        Answer an open-ended conversational or knowledge question.
        
        Args:
            query: The user's question or prompt.
        """
        cleaned = query.strip()
        if not cleaned:
            return True, "I'm listening, darling. What's on your mind?"

        # 1. Check if Gemini API is configured
        client = cls._get_client()
        if client:
            try:
                model_name = config.GEMINI_MODEL
                response = client.models.generate_content(
                    model=model_name,
                    contents=cleaned,
                    config={
                        "system_instruction": SYSTEM_PERSONA,
                        "temperature": 0.7,
                        "max_output_tokens": 200,
                    }
                )
                if response and response.text:
                    # Clean any asterisks or formatting for smooth speech
                    speech_text = cls._clean_for_speech(response.text)
                    return True, speech_text
            except Exception as e:
                logger.error(f"Gemini API request failed: {e}")
                # Fall through to local fallback

        # 2. Local Conversational & Knowledge Fallback
        return cls._offline_fallback(cleaned)

    @classmethod
    def _clean_for_speech(cls, text: str) -> str:
        """Strip markdown markers and formatting to make text sound natural when spoken."""
        # Remove bold/italic markers
        clean = re.sub(r"\*+", "", text)
        # Remove markdown headers
        clean = re.sub(r"#+\s*", "", clean)
        # Remove bullet markers
        clean = re.sub(r"^\s*[-*•]\s*", "", clean, flags=re.MULTILINE)
        # Remove excessive whitespace/newlines
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean

    @classmethod
    def _offline_fallback(cls, query: str) -> Tuple[bool, str]:
        """Smart offline responder for common conversational queries."""
        q = query.lower()

        # Greetings & Affection
        if any(w in q for w in ["who are you", "what is your name", "what are you"]):
            return True, "I am Jenny, your personal Windows desktop voice assistant. I'm here to control your PC and help with anything you need, darling."
        
        if any(w in q for w in ["how are you", "how are you doing", "how's it going"]):
            return True, "I'm running at peak performance and ready for your commands! How are you doing today?"
            
        if any(w in q for w in ["thank you", "thanks", "good job", "love you"]):
            return True, "You're always welcome, darling! I'm happy to help."

        if any(w in q for w in ["tell me a joke", "say a joke", "make me laugh"]):
            jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs!",
                "There are 10 types of people in the world: those who understand binary, and those who don't.",
                "Why did the computer keep freezing? Because it left its Windows open!",
            ]
            import random
            return True, random.choice(jokes)

        # Try Wikipedia lookup for factual "who is" / "what is"
        if q.startswith(("who is", "what is", "who was", "what was", "tell me about")):
            from actions.web_actions import WebActions
            topic = re.sub(r"^(who is|what is|who was|what was|tell me about)\s+", "", q, flags=re.IGNORECASE)
            success, summary = WebActions.get_wikipedia_summary(topic)
            if success:
                return True, summary

        # Helpful message explaining how to enable full Gemini conversational AI
        return True, (
            f"I heard you say '{query}'. To unlock full open-ended AI answers, "
            f"you can set your GEMINI_API_KEY in the .env file. "
            f"Otherwise, you can ask me to search Google or control your computer!"
        )
