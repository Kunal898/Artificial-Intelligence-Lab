"""
AI-Based Voice Assistant with GUI for System Control
Entry Point - main.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import VoiceAssistantApp


def main():
    """Launch the Voice Assistant application."""
    print("=" * 60)
    print("  AI Voice Assistant v1.0")
    print("  Starting application...")
    print("=" * 60)
    app = VoiceAssistantApp()
    app.run()


if __name__ == "__main__":
    main()
