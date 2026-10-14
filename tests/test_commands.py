"""
Comprehensive Automated Test Suite for Jenny Voice Assistant.
Tests intent parsing, wake word detection, entity extraction, and command routing.
"""

import pytest
from unittest.mock import patch, MagicMock
from commander import CommandEngine, CommandResult
from actions.utility_actions import UtilityActions

@pytest.fixture
def engine():
    return CommandEngine()

# =========================================================================
# 1. Wake Word Stripping & Cleansing Tests
# =========================================================================

def test_wake_words_stripping(engine):
    assert engine.clean_utterance("Jenny, what time is it") == "what time is it"
    assert engine.clean_utterance("darling open calculator") == "open calculator"
    assert engine.clean_utterance("babe please set volume to 40") == "set volume to 40"
    assert engine.clean_utterance("hey jenny tell me a joke") == "tell me a joke"
    assert engine.clean_utterance("hi jenny could you check battery") == "check battery"

def test_has_wake_word(engine):
    assert engine.has_wake_word("Jenny can you hear me") is True
    assert engine.has_wake_word("Hey darling are you there") is True
    assert engine.has_wake_word("Yes babe do this") is True
    assert engine.has_wake_word("random sentence without triggers") is False

def test_only_wake_word_acknowledgement(engine):
    result = engine.execute("Jenny")
    assert result.action_type == "wake_ack"
    assert "Yes darling" in result.response

    result_babe = engine.execute("babe")
    assert result_babe.action_type == "wake_ack"

# =========================================================================
# 2. System: Volume Tests
# =========================================================================

@patch("actions.system_actions.SystemActions.set_volume", return_value=(True, "Volume set to 40%."))
def test_volume_set(mock_vol, engine):
    result = engine.execute("Jenny set volume to 40%")
    assert result.action_type == "system_volume_set"
    assert result.details["target_percent"] == 40
    mock_vol.assert_called_once_with(40)

@patch("actions.system_actions.SystemActions.volume_up", return_value=(True, "Volume set to 60%."))
def test_volume_up(mock_vol_up, engine):
    result = engine.execute("darling turn up the volume")
    assert result.action_type == "system_volume_up"
    mock_vol_up.assert_called_once()

@patch("actions.system_actions.SystemActions.volume_down", return_value=(True, "Volume set to 30%."))
def test_volume_down(mock_vol_down, engine):
    result = engine.execute("babe volume down")
    assert result.action_type == "system_volume_down"
    mock_vol_down.assert_called_once()

@patch("actions.system_actions.SystemActions.mute", return_value=(True, "Audio muted."))
def test_volume_mute(mock_mute, engine):
    result = engine.execute("Jenny mute audio")
    assert result.action_type == "system_volume_mute"
    mock_mute.assert_called_once()

@patch("actions.system_actions.SystemActions.unmute", return_value=(True, "Audio unmuted."))
def test_volume_unmute(mock_unmute, engine):
    result = engine.execute("unmute sound")
    assert result.action_type == "system_volume_unmute"
    mock_unmute.assert_called_once()

# =========================================================================
# 3. System: Media Controls Tests
# =========================================================================

@patch("actions.system_actions.SystemActions.play_pause_media", return_value=(True, "Media toggled."))
def test_media_play_pause(mock_media, engine):
    result = engine.execute("Jenny pause music")
    assert result.action_type == "system_media_toggle"
    mock_media.assert_called_once()

@patch("actions.system_actions.SystemActions.next_track", return_value=(True, "Skipped to next track."))
def test_media_next(mock_next, engine):
    result = engine.execute("darling next track")
    assert result.action_type == "system_media_next"
    mock_next.assert_called_once()

@patch("actions.system_actions.SystemActions.previous_track", return_value=(True, "Returned to previous track."))
def test_media_previous(mock_prev, engine):
    result = engine.execute("babe previous track")
    assert result.action_type == "system_media_previous"
    mock_prev.assert_called_once()

# =========================================================================
# 4. System: Security, Power, Hardware & Screenshot Tests
# =========================================================================

@patch("actions.system_actions.SystemActions.lock_screen", return_value=(True, "Computer locked."))
def test_lock_screen(mock_lock, engine):
    result = engine.execute("Jenny lock computer")
    assert result.action_type == "system_lock"
    mock_lock.assert_called_once()

@patch("actions.system_actions.SystemActions.get_battery_status", return_value=(True, "Battery is at 80%."))
def test_battery_status(mock_bat, engine):
    result = engine.execute("darling check battery status")
    assert result.action_type == "system_battery"
    mock_bat.assert_called_once()

@patch("actions.system_actions.SystemActions.get_hardware_status", return_value=(True, "CPU is at 15%."))
def test_hardware_status(mock_hw, engine):
    result = engine.execute("babe check system stats")
    assert result.action_type == "system_hardware_stats"
    mock_hw.assert_called_once()

@patch("actions.system_actions.SystemActions.take_screenshot", return_value=(True, "Screenshot captured."))
def test_screenshot(mock_shot, engine):
    result = engine.execute("Jenny take a screenshot")
    assert result.action_type == "system_screenshot"
    mock_shot.assert_called_once()

# =========================================================================
# 5. Apps: Launch & Termination Tests
# =========================================================================

@patch("actions.app_actions.AppActions.open_app", return_value=(True, "Opening calculator."))
def test_open_app(mock_open, engine):
    result = engine.execute("Jenny launch calculator")
    assert result.action_type == "app_open"
    assert result.details["app"] == "calculator"
    mock_open.assert_called_once_with("calculator")

@patch("actions.app_actions.AppActions.close_app", return_value=(True, "Closed chrome."))
def test_close_app(mock_close, engine):
    result = engine.execute("darling close chrome")
    assert result.action_type == "app_close"
    assert result.details["app"] == "chrome"
    mock_close.assert_called_once_with("chrome")

# =========================================================================
# 6. Web & Search Tests
# =========================================================================

@patch("actions.web_actions.WebActions.play_youtube", return_value=(True, "Playing jazz on YouTube."))
def test_youtube(mock_yt, engine):
    result = engine.execute("Jenny play lofi hip hop on youtube")
    assert result.action_type == "web_youtube"
    assert result.details["query"] == "lofi hip hop"
    mock_yt.assert_called_once_with("lofi hip hop")

@patch("actions.web_actions.WebActions.search_google", return_value=(True, "Searching Google."))
def test_google_search(mock_g, engine):
    result = engine.execute("darling search google for artificial intelligence")
    assert result.action_type == "web_google_search"
    assert result.details["query"] == "artificial intelligence"
    mock_g.assert_called_once_with("artificial intelligence")

@patch("actions.web_actions.WebActions.get_weather", return_value=(True, "Sunny 22C."))
def test_weather(mock_w, engine):
    result = engine.execute("babe what's the weather today")
    assert result.action_type == "web_weather"
    mock_w.assert_called_once()

# =========================================================================
# 7. Utilities & Productivity Tests
# =========================================================================

def test_time(engine):
    result = engine.execute("Jenny what time is it")
    assert result.action_type == "utility_time"
    assert "The time is" in result.response

def test_date(engine):
    result = engine.execute("darling what is today's date")
    assert result.action_type == "utility_date"
    assert "Today is" in result.response

@patch("actions.utility_actions.UtilityActions.take_note", return_value=(True, "Note saved."))
def test_take_note(mock_note, engine):
    result = engine.execute("babe take a note: call doctor at 5pm")
    assert result.action_type == "utility_note_save"
    assert result.details["note"] == "call doctor at 5pm"
    mock_note.assert_called_once_with("call doctor at 5pm")

def test_math_calculation_logic():
    success, res = UtilityActions.calculate("25 * 4")
    assert success is True
    assert "100" in res

    success, res = UtilityActions.calculate("10 plus 15")
    assert success is True
    assert "25" in res

    success, res = UtilityActions.calculate("20 percent of 500")
    assert success is True
    assert "100" in res

# =========================================================================
# 8. Conversational AI Fallback Tests
# =========================================================================

def test_ai_conversational_fallback(engine):
    result = engine.execute("Jenny who are you")
    assert result.action_type == "ai_conversational"
    assert "Jenny" in result.response
    assert "assistant" in result.response

def test_ai_joke(engine):
    result = engine.execute("darling tell me a joke")
    assert result.action_type == "ai_conversational"
    assert len(result.response) > 10
