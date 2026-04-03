"""
modules/tts_engine.py
Text-to-Speech engine using pyttsx3.
Runs speech synthesis in a background thread to avoid blocking the GUI.
"""

import threading
import queue

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

import config


class TTSEngine:
    """
    Manages text-to-speech synthesis.

    Why a separate thread?
        pyttsx3.runAndWait() blocks the calling thread.
        By running synthesis in a dedicated thread with a task queue,
        the GUI remains responsive during speech output.
    """

    def __init__(self):
        self._queue = queue.Queue()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        self._enabled = True

    def _init_engine(self):
        """Initialize pyttsx3 engine with configured settings."""
        if not PYTTSX3_AVAILABLE:
            return None

        engine = pyttsx3.init()
        engine.setProperty('rate', config.TTS_RATE)
        engine.setProperty('volume', config.TTS_VOLUME)

        # Select voice by gender preference
        voices = engine.getProperty('voices')
        if voices:
            gender = config.TTS_VOICE_GENDER.lower()
            selected = None
            for voice in voices:
                name = voice.name.lower()
                if gender == "female" and any(w in name for w in ["female", "zira", "hazel", "susan", "eva"]):
                    selected = voice.id
                    break
                elif gender == "male" and any(w in name for w in ["male", "david", "mark", "james"]):
                    selected = voice.id
                    break
            if selected:
                engine.setProperty('voice', selected)

        return engine

    def _worker(self):
        """Background worker that processes the TTS queue."""
        # Each worker iteration creates a fresh engine instance
        # to avoid threading conflicts with pyttsx3.
        while True:
            text = self._queue.get()
            if text is None:
                break
            if self._enabled and PYTTSX3_AVAILABLE:
                try:
                    engine = self._init_engine()
                    if engine:
                        engine.say(text)
                        engine.runAndWait()
                        engine.stop()
                except Exception as e:
                    print(f"[TTS Error] {e}")
            self._queue.task_done()

    def speak(self, text: str):
        """Queue text for speech output."""
        if text and self._enabled:
            # Clear queue to avoid speaking stale responses
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    break
            self._queue.put(text)

    def toggle(self):
        """Enable/disable TTS."""
        self._enabled = not self._enabled
        return self._enabled

    def set_enabled(self, value: bool):
        self._enabled = value

    def shutdown(self):
        """Stop the TTS worker thread."""
        self._queue.put(None)
