"""
modules/logger.py
Persistent command history logging.
"""

import os
import datetime
import config


class CommandLogger:
    """Logs commands and responses to a file for audit/history."""

    def __init__(self):
        os.makedirs(config.LOG_DIR, exist_ok=True)
        self._path = config.COMMAND_LOG_FILE

    def log(self, command: str, response: str, success: bool):
        """Append a command entry to the log file."""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "OK" if success else "FAIL"
        entry = f"[{timestamp}] [{status}] CMD: {command!r} | RESP: {response}\n"
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(entry)
        except Exception as e:
            print(f"[Logger Error] {e}")

    def load_history(self) -> list[str]:
        """Return all log entries as a list of strings."""
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return f.readlines()
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"[Logger Read Error] {e}")
            return []

    def clear(self):
        """Clear the log file."""
        try:
            open(self._path, "w").close()
        except Exception as e:
            print(f"[Logger Clear Error] {e}")
