"""
config.py - Central configuration for the Voice Assistant
"""

import os

# ─── Assistant Identity ────────────────────────────────────────────────────────
ASSISTANT_NAME = "AI"          # AI Voice Assistant
ASSISTANT_VERSION = "1.0"
WAKE_PHRASE = "hey AI"

# ─── Speech Recognition Settings ──────────────────────────────────────────────
RECOGNITION_ENGINE = "google"    # Options: "google", "sphinx" (offline)
RECOGNITION_TIMEOUT = 5          # Seconds to wait for speech to begin
RECOGNITION_PHRASE_LIMIT = 10    # Max seconds per phrase
RECOGNITION_LANGUAGE = "en-US"

# ─── Text-to-Speech Settings ──────────────────────────────────────────────────
TTS_RATE = 175           # Words per minute
TTS_VOLUME = 0.9         # 0.0 to 1.0
TTS_VOICE_GENDER = "female"  # "male" or "female"

# ─── GUI Settings ─────────────────────────────────────────────────────────────
WINDOW_TITLE = f"{ASSISTANT_NAME} — Voice Assistant"
WINDOW_WIDTH = 820
WINDOW_HEIGHT = 620
WINDOW_MIN_WIDTH = 700
WINDOW_MIN_HEIGHT = 500

# Colors (Dark Cyberpunk Theme)
COLOR_BG_DARK = "#0a0e1a"
COLOR_BG_MID = "#111827"
COLOR_BG_PANEL = "#1a2035"
COLOR_ACCENT = "#00d4ff"
COLOR_ACCENT_2 = "#7c3aed"
COLOR_SUCCESS = "#10b981"
COLOR_WARNING = "#f59e0b"
COLOR_ERROR = "#ef4444"
COLOR_TEXT_PRIMARY = "#e2e8f0"
COLOR_TEXT_SECONDARY = "#94a3b8"
COLOR_TEXT_MUTED = "#475569"

# Fonts
FONT_FAMILY_HEADER = "Consolas"
FONT_FAMILY_BODY = "Consolas"
FONT_SIZE_HEADER = 18
FONT_SIZE_BODY = 11
FONT_SIZE_SMALL = 9

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
COMMAND_LOG_FILE = os.path.join(LOG_DIR, "command_history.log")

# ─── System Settings ──────────────────────────────────────────────────────────
MAX_HISTORY_DISPLAY = 50     # Lines shown in command history
CONFIRM_DANGEROUS_COMMANDS = True   # Require confirmation for shutdown/restart

# ─── Command Confidence ───────────────────────────────────────────────────────
MIN_CONFIDENCE_THRESHOLD = 0.3   # Fuzzy matching minimum score (0–1)
