"""
modules/speech_engine.py
Handles microphone input and speech-to-text conversion.
"""

import threading
import queue
import time
import sys

try:
    import speech_recognition as sr
except ImportError:
    sr = None

import config


class SpeechEngine:
    """
    Captures audio from the microphone and converts speech to text.

    Architecture:
        - Runs a background thread that continuously listens for audio.
        - Recognized text is placed into a thread-safe queue.
        - The main thread (or GUI) pulls results from the queue.
    """

    def __init__(self, on_result=None, on_error=None, on_status=None):
        """
        Args:
            on_result  : Callback(text: str) — called when speech is recognized.
            on_error   : Callback(msg: str)  — called on recognition error.
            on_status  : Callback(msg: str)  — called for status updates.
        """
        if sr is None:
            raise ImportError(
                "SpeechRecognition library not installed.\n"
                "Run: pip install SpeechRecognition pyaudio"
            )

        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_listening = False
        self._thread = None
        self._stop_event = threading.Event()

        # Callbacks
        self.on_result = on_result or (lambda text: None)
        self.on_error = on_error or (lambda msg: None)
        self.on_status = on_status or (lambda msg: None)

        # Configure recognizer sensitivity
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

    def _initialize_microphone(self):
        """Initialize and calibrate the microphone."""
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.on_status("Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.on_status("Microphone ready.")
            return True
        except Exception as e:
            self.on_error(f"Microphone initialization failed: {e}")
            return False

    def _listen_loop(self):
        """Background thread: continuously listens and recognizes speech."""
        if not self._initialize_microphone():
            self.is_listening = False
            return

        self.on_status("Listening... Speak a command.")

        while not self._stop_event.is_set():
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=config.RECOGNITION_TIMEOUT,
                        phrase_time_limit=config.RECOGNITION_PHRASE_LIMIT
                    )

                self.on_status("Processing speech...")
                text = self._recognize(audio)

                if text:
                    self.on_result(text.lower().strip())
                    self.on_status("Listening... Speak a command.")

            except sr.WaitTimeoutError:
                # No speech detected — just keep looping
                continue
            except sr.UnknownValueError:
                # Silently ignore unknown audio - no spam
                self.on_status("Listening... Speak a command.")
            except sr.RequestError as e:
                self.on_error(f"Speech Recognition service error: {e}")
                time.sleep(2)
            except Exception as e:
                if not self._stop_event.is_set():
                    self.on_error(f"Listening error: {e}")
                break

        self.is_listening = False
        self.on_status("Assistant stopped.")

    def _recognize(self, audio) -> str:
        """
        Convert audio to text using the configured recognition engine.

        Pattern Recognition Note:
            Google's API performs acoustic modeling + language modeling
            to produce the most probable transcription. This is the
            "speech feature processing" step — converting raw waveforms
            into symbolic text that our command processor can analyze.
        """
        engine = config.RECOGNITION_ENGINE.lower()

        if engine == "google":
            return self.recognizer.recognize_google(
                audio,
                language=config.RECOGNITION_LANGUAGE
            )
        elif engine == "sphinx":
            # Offline recognition (less accurate)
            return self.recognizer.recognize_sphinx(audio)
        else:
            return self.recognizer.recognize_google(audio)

    def start(self):
        """Start the listening thread."""
        if self.is_listening:
            return
        self._stop_event.clear()
        self.is_listening = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the listening thread gracefully."""
        self._stop_event.set()
        self.is_listening = False
        self.on_status("Stopping listener...")
