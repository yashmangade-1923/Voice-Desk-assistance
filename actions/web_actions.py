"""
Web and Online Actions for Jenny Voice Assistant.
Handles Google searches, YouTube playback, Wikipedia summaries, and weather lookups.
"""

from __future__ import annotations
import urllib.parse
import webbrowser
import logging
from typing import Tuple
import requests

logger = logging.getLogger("jenny.web_actions")

class WebActions:
    """Web and online information queries."""

    @classmethod
    def search_google(cls, query: str) -> Tuple[bool, str]:
        """
        Open default web browser and search Google for query.
        
        Args:
            query: The search term or question.
        """
        if not query or not query.strip():
            return False, "What would you like me to search for?"
            
        encoded = urllib.parse.quote_plus(query.strip())
        url = f"https://www.google.com/search?q={encoded}"
        try:
            webbrowser.open(url)
            return True, f"Searching Google for {query}."
        except Exception as e:
            logger.error(f"Error opening browser for search: {e}")
            return False, f"Could not open browser: {e}"

    @classmethod
    def play_youtube(cls, query: str) -> Tuple[bool, str]:
        """
        Search and play song or video on YouTube in default web browser.
        
        Args:
            query: Name of the video, artist, or song.
        """
        if not query or not query.strip():
            return False, "What song or video would you like to play on YouTube?"
            
        cleaned_query = query.strip()
        encoded = urllib.parse.quote_plus(cleaned_query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        try:
            webbrowser.open(url)
            return True, f"Playing {cleaned_query} on YouTube."
        except Exception as e:
            logger.error(f"Error opening YouTube: {e}")
            return False, f"Could not open YouTube: {e}"

    @classmethod
    def get_wikipedia_summary(cls, query: str, max_chars: int = 350) -> Tuple[bool, str]:
        """
        Fetch a concise Wikipedia summary for a topic or person.
        
        Args:
            query: Subject name.
            max_chars: Maximum characters to return for clean speech.
        """
        if not query or not query.strip():
            return False, "Who or what would you like me to look up?"
            
        topic = query.strip()
        encoded_topic = urllib.parse.quote(topic.replace(" ", "_"))
        api_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded_topic}"
        headers = {"User-Agent": "JennyDesktopVoiceAssistant/1.0 (Windows NT 10.0)"}
        
        try:
            resp = requests.get(api_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                extract = data.get("extract", "")
                if extract:
                    # Truncate cleanly to sentence boundary if too long
                    if len(extract) > max_chars:
                        sentences = extract.split(". ")
                        summary = sentences[0] + "."
                        if len(summary) < max_chars and len(sentences) > 1:
                            summary += " " + sentences[1] + "."
                    else:
                        summary = extract
                    return True, summary
            
            # Fallback search if exact page not found
            search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(topic)}&limit=1&namespace=0&format=json"
            search_resp = requests.get(search_url, headers=headers, timeout=5)
            if search_resp.status_code == 200:
                results = search_resp.json()
                if len(results) > 2 and results[2] and results[2][0]:
                    return True, results[2][0]

            return False, f"I couldn't find a Wikipedia article for '{topic}'."
        except Exception as e:
            logger.error(f"Error fetching Wikipedia summary: {e}")
            return False, f"Unable to reach Wikipedia right now."

    @classmethod
    def get_weather(cls, location: str = "") -> Tuple[bool, str]:
        """
        Fetch current weather conditions.
        
        Args:
            location: Optional city or location name. Defaults to current IP location.
        """
        loc_str = urllib.parse.quote(location.strip()) if location.strip() else ""
        url = f"https://wttr.in/{loc_str}?format=%C:+%t+(feels+like+%f),+humidity+%h,+wind+%w"
        headers = {"User-Agent": "curl/7.88.1"}
        
        try:
            resp = requests.get(url, headers=headers, timeout=5)
            if resp.status_code == 200 and resp.text and not resp.text.startswith("<"):
                report = resp.text.strip()
                target_name = location.strip() if location.strip() else "your area"
                return True, f"The weather in {target_name} is {report}."
            return False, "Could not retrieve weather report."
        except Exception as e:
            logger.error(f"Error retrieving weather: {e}")
            return False, "Unable to get weather information right now."
