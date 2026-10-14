# Desktop Voice Assistant for Windows (Jenny)

A modular, high-performance Python-based desktop voice assistant engineered for Windows.

## Features
- **Voice Triggering**: Activated by wake words ("Jenny", "Darling", "Babe") or global Push-to-Talk hotkey (`Ctrl+Shift+A`).
- **Text Mode Fallback**: Interactive console mode (`--text`) for silent usage or testing without a microphone.
- **Windows System Controls**:
  - Master volume adjustments (exact %, mute/unmute, volume up/down) via Windows Core Audio API (`pycaw`).
  - Media controls (play/pause, next track, previous track).
  - Security & Power (screen lock, sleep, battery stats, CPU/RAM/Disk stats).
  - High-res screenshots saved to `Pictures/Screenshots`.
- **Application Management**:
  - Open & Close desktop apps, Windows store apps, browser, calculator, etc.
- **Productivity & Web Automation**:
  - YouTube search & instant playback.
  - Google web search.
  - Wikipedia summaries.
  - Voice notes saved with timestamps.
  - Active window typing emulation & clipboard reader.
- **AI Reasoning**:
  - Dual intelligence: Open-ended conversational query answering via Google Gemini API with smart offline fallback (instant Wikipedia/factual calculations).
- **Rich Terminal UI**:
  - Live animated visual state, command history logs, and status dashboards.

## Quick Start
```bash
# Run continuous wake-word listening
uv run python main.py

# Run Push-to-Talk mode (Ctrl+Shift+A or Space)
uv run python main.py --push-to-talk

# Run Interactive Text mode (no mic needed)
uv run python main.py --text

# Run System & Audio Diagnostics
uv run python main.py --diagnostics
```
