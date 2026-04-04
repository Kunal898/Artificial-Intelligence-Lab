# ◈ AI Voice Assistant (ARIA)

![AI Assistant Branding](file:///C:/Users/Kunal/.gemini/antigravity/brain/4687df63-0bec-43ec-84ac-0c8ad9035a2f/ai_assistant_logo_1775272086757.png)

A high-performance, offline-first AI Voice Assistant built with Python. Designed for desktop management, home automation, and system control, featuring a premium **Cyberpunk-inspired GUI**.

### 🚀 Overview
The **AI Voice Assistant** (also known as ARIA) is a modular desktop companion. It uses advanced speech-to-text (STT) and text-to-speech (TTS) engines to process commands naturally, letting you control your computer via voice or a sleek, modern interface.

---

### ✨ Key Features
*   **🎙️ Smart Voice Recognition**: Offline-ready speech recognition (Vosk/Sphinx) or high-accuracy cloud processing (Google).
*   **🗣️ Dynamic TTS Engine**: Natural voice responses to confirm actions and interact with the user.
*   **🖥️ Dashboard Interface**: A custom-built Tkinter GUI with:
    *   **Live Waveform Animation**: Visual feedback when the assistant is listening.
    *   **System Monitor**: Real-time tracking of CPU and RAM performance.
    *   **Command History**: A persistent log of all interactions and status updates.
*   **⚙️ System Control**: Manage volume, brightness, and power states directly from the app.
*   **📂 App & Web Automation**: Launch your favorite apps (Google, YouTube, VS Code, etc.) using simple voice commands.
*   **🔒 Secure Operations**: Sensitive commands (like system restart) require a visual confirmation dialog.

---

### 🛠️ Tech Stack
*   **Python 3.x**: Core logic and command processing.
*   **Tkinter**: Modern, dark-themed GUI framework.
*   **SpeechRecognition**: Multi-engine speech capture.
*   **pyttsx3**: Cross-platform, offline text-to-speech engine.
*   **psutil**: Real-time hardware performance metrics.
*   **FuzzyWuzzy (or similar)**: Sophisticated command intent matching.

---

### 📦 Installation
1.  **Clone the Repository**:
    ```bash
    git clone [repository-url]
    cd "ai ok"
    ```

2.  **Set Up Virtual Environment** (Optional but recommended):
    ```bash
    python -m venv venv
    venv\Scripts\activate
    ```

3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

---

### 🚦 Quick Start
Simply run the `main.py` file to launch the assistant:
```bash
python main.py
```

### 💬 Sample Commands
*   *"What's the CPU usage?"* — Displays current system health.
*   *"Increase volume by 10"* — Adjusts the master volume.
*   *"Open Google"* — Launches your default browser.
*   *"Set brightness to 50%"* — Adjusts monitor brightness levels.
*   *"Help"* — Shows a list of all supported intents.

---

### 📂 Project Structure
*   `app.py`: The heart of the GUI and event handling.
*   `command_processor.py`: Intelligent routing of user intents to system actions.
*   `system_controller.py`: Low-level system operations (audio, brightness, etc.).
*   `speech_engine.py`: Audio capture and STT processing.
*   `tts_engine.py`: Voice feedback generation.
*   `config.py`: Centralized styling and behavior settings.

---

### 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.
