"""
Productivity and Utility Actions for Jenny Voice Assistant.
Handles time, date, note-taking, clipboard reading, math calculation, and active window typing.
"""

from __future__ import annotations
import ast
import math
import operator
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple, Union
import logging
import pyautogui
import pyperclip
from config import config

logger = logging.getLogger("jenny.utility_actions")

# Safe math operators for AST evaluation
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

class UtilityActions:
    """Productivity and helper utilities."""

    @classmethod
    def get_time_date(cls) -> Tuple[bool, str]:
        """Return the current time and full formatted date."""
        now = datetime.now()
        # Formats: e.g. "7:15 PM, Wednesday, October 14, 2026"
        time_str = now.strftime("%I:%M %p").lstrip("0")
        date_str = now.strftime("%A, %B %d, %Y")
        return True, f"It is {time_str} on {date_str}."

    @classmethod
    def get_time(cls) -> Tuple[bool, str]:
        """Return current time only."""
        time_str = datetime.now().strftime("%I:%M %p").lstrip("0")
        return True, f"The time is {time_str}."

    @classmethod
    def get_date(cls) -> Tuple[bool, str]:
        """Return current date only."""
        date_str = datetime.now().strftime("%A, %B %d, %Y")
        return True, f"Today is {date_str}."

    @classmethod
    def take_note(cls, note_text: str) -> Tuple[bool, str]:
        """
        Append a timestamped voice note to the user's notes markdown file.
        
        Args:
            note_text: The note content.
        """
        if not note_text or not note_text.strip():
            return False, "What note would you like me to write down?"
            
        try:
            config.ensure_directories()
            timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
            entry = f"- **[{timestamp}]**: {note_text.strip()}\n"
            
            with open(config.NOTES_FILE, "a", encoding="utf-8") as f:
                f.write(entry)
                
            return True, f"Note saved: {note_text.strip()}"
        except Exception as e:
            logger.error(f"Error saving note: {e}")
            return False, f"Failed to save note: {e}"

    @classmethod
    def read_notes(cls, count: int = 3) -> Tuple[bool, str]:
        """Read back the most recent notes."""
        try:
            if not config.NOTES_FILE.exists():
                return True, "You don't have any saved notes yet."
                
            with open(config.NOTES_FILE, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]
                
            if not lines:
                return True, "Your notes file is currently empty."
                
            recent = lines[-count:]
            # Clean markdown formatting for speech
            cleaned = []
            for item in recent:
                clean_item = item.replace("- **[", "On ").replace("]**:", " -")
                cleaned.append(clean_item)
                
            return True, "Here are your recent notes: " + " ; ".join(cleaned)
        except Exception as e:
            logger.error(f"Error reading notes: {e}")
            return False, f"Failed to read notes: {e}"

    @classmethod
    def read_clipboard(cls) -> Tuple[bool, str]:
        """Read and speak the text currently on the Windows clipboard."""
        try:
            content = pyperclip.paste()
            if not content or not content.strip():
                return True, "The clipboard is currently empty."
                
            trimmed = content.strip()
            if len(trimmed) > 300:
                trimmed = trimmed[:300] + "... and more."
            return True, f"Clipboard content: {trimmed}"
        except Exception as e:
            logger.error(f"Error reading clipboard: {e}")
            return False, "Unable to read from clipboard."

    @classmethod
    def type_text(cls, text: str) -> Tuple[bool, str]:
        """
        Emulate keyboard typing into the currently focused window.
        
        Args:
            text: The text string to type.
        """
        if not text:
            return False, "No text provided to type."
            
        try:
            # Short grace period for window focus
            time.sleep(0.3)
            pyautogui.write(text, interval=0.02)
            return True, "Text typed."
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return False, f"Failed to type text: {e}"

    @classmethod
    def calculate(cls, expression: str) -> Tuple[bool, str]:
        """
        Safely evaluate a math expression or natural language calculation.
        
        Args:
            expression: Math expression (e.g., '45 * 12', '25 percent of 800', 'sqrt 144').
        """
        try:
            cleaned = expression.lower()
            # Natural language conversions
            cleaned = cleaned.replace("times", "*").replace("multiplied by", "*")
            cleaned = cleaned.replace("divided by", "/").replace("over", "/")
            cleaned = cleaned.replace("plus", "+").replace("add", "+")
            cleaned = cleaned.replace("minus", "-")
            cleaned = cleaned.replace("to the power of", "**")
            cleaned = cleaned.replace("x", "*")  # e.g., 5 x 5

            # Handle percentage: "X percent of Y" -> (X / 100) * Y
            if "percent of" in cleaned:
                parts = cleaned.split("percent of")
                if len(parts) == 2:
                    p = float(parts[0].strip().replace("%", ""))
                    total = float(parts[1].strip())
                    res = (p / 100.0) * total
                    return True, f"{p}% of {total} is {res:g}."

            # Parse AST safely
            tree = ast.parse(cleaned.strip(), mode="eval")
            
            def _eval_node(node: ast.AST) -> Union[int, float]:
                if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                    return node.value
                elif isinstance(node, ast.BinOp):
                    op_type = type(node.op)
                    if op_type in SAFE_OPERATORS:
                        left = _eval_node(node.left)
                        right = _eval_node(node.right)
                        return SAFE_OPERATORS[op_type](left, right)
                elif isinstance(node, ast.UnaryOp):
                    op_type = type(node.op)
                    if op_type in SAFE_OPERATORS:
                        operand = _eval_node(node.operand)
                        return SAFE_OPERATORS[op_type](operand)
                raise ValueError(f"Unsupported operation in calculation: {node}")

            result = _eval_node(tree.body)
            # Format nicely
            formatted_res = f"{result:g}"
            return True, f"The answer is {formatted_res}."

        except Exception as e:
            logger.debug(f"Math evaluation failed for '{expression}': {e}")
            return False, f"I couldn't calculate that: {expression}"
