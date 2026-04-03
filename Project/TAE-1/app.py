"""
gui/app.py
Main Tkinter GUI for the AI Voice Assistant.

Layout Overview:
    ┌─────────────────────────────────────────────────────┐
    │  HEADER: Assistant name + status indicator          │
    ├──────────────────────┬──────────────────────────────┤
    │  LEFT PANEL          │  RIGHT PANEL                 │
    │  • Waveform visual   │  • Response display          │
    │  • Status label      │  • Command history log       │
    │  • Control buttons   │                              │
    │  • System info       │                              │
    ├──────────────────────┴──────────────────────────────┤
    │  FOOTER: Command input bar + TTS toggle             │
    └─────────────────────────────────────────────────────┘
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import datetime

# Add parent directory to path
sys.path.insert(0, '.')

import config
from speech_engine import SpeechEngine
from tts_engine import TTSEngine
from command_processor import CommandProcessor
from logger import CommandLogger

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class VoiceAssistantApp:
    """Main application window for the AI Voice Assistant."""

    def __init__(self):
        self.root = tk.Tk()
        self._setup_window()
        self._setup_fonts()
        self._setup_variables()
        self._build_ui()
        self._init_modules()
        self._start_sys_monitor()

    # ─── Window Setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.minsize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)
        self.root.configure(bg=config.COLOR_BG_DARK)
        self.root.resizable(True, True)
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - config.WINDOW_WIDTH) // 2
        y = (self.root.winfo_screenheight() - config.WINDOW_HEIGHT) // 2
        self.root.geometry(f"+{x}+{y}")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_fonts(self):
        f = config.FONT_FAMILY_BODY
        self.font_header = (f, 20, "bold")
        self.font_subheader = (f, 13, "bold")
        self.font_body = (f, 11)
        self.font_small = (f, 9)
        self.font_mono = (f, 10)
        self.font_large = (f, 16, "bold")
        self.font_accent = (f, 12, "bold")

    def _setup_variables(self):
        self.is_listening = tk.BooleanVar(value=False)
        self.tts_enabled = tk.BooleanVar(value=True)
        self.status_text = tk.StringVar(value="Ready. Press START to begin.")
        self.last_command = tk.StringVar(value="—")
        self.last_response = tk.StringVar(value="Awaiting your command...")
        self._pulse_state = 0
        self._anim_job = None
        self._sysmon_job = None

    # ─── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_main_area()
        self._build_footer()

    def _build_header(self):
        header = tk.Frame(self.root, bg=config.COLOR_BG_PANEL, height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        header.pack_propagate(False)

        # Left: Logo + name
        left = tk.Frame(header, bg=config.COLOR_BG_PANEL)
        left.pack(side=tk.LEFT, padx=20, pady=10)

        tk.Label(
            left, text="◈", font=(config.FONT_FAMILY_BODY, 24),
            bg=config.COLOR_BG_PANEL, fg=config.COLOR_ACCENT
        ).pack(side=tk.LEFT, padx=(0, 8))

        tk.Label(
            left, text=config.ASSISTANT_NAME,
            font=(config.FONT_FAMILY_HEADER, 22, "bold"),
            bg=config.COLOR_BG_PANEL, fg=config.COLOR_ACCENT
        ).pack(side=tk.LEFT)

        tk.Label(
            left, text=f"  Voice Assistant v{config.ASSISTANT_VERSION}",
            font=self.font_small,
            bg=config.COLOR_BG_PANEL, fg=config.COLOR_TEXT_MUTED
        ).pack(side=tk.LEFT, pady=(8, 0))

        # Right: Status indicator
        right = tk.Frame(header, bg=config.COLOR_BG_PANEL)
        right.pack(side=tk.RIGHT, padx=20, pady=10)

        self._indicator_dot = tk.Label(
            right, text="●", font=(config.FONT_FAMILY_BODY, 18),
            bg=config.COLOR_BG_PANEL, fg=config.COLOR_TEXT_MUTED
        )
        self._indicator_dot.pack(side=tk.RIGHT, padx=(6, 0))

        self._indicator_text = tk.Label(
            right, textvariable=self.status_text,
            font=self.font_small, bg=config.COLOR_BG_PANEL,
            fg=config.COLOR_TEXT_SECONDARY
        )
        self._indicator_text.pack(side=tk.RIGHT)

        # Separator
        tk.Frame(self.root, bg=config.COLOR_ACCENT, height=2).pack(fill=tk.X)

    def _build_main_area(self):
        main = tk.Frame(self.root, bg=config.COLOR_BG_DARK)
        main.pack(fill=tk.BOTH, expand=True)

        # ── Left Panel ─────────────────────────────────────────────────────
        left_panel = tk.Frame(main, bg=config.COLOR_BG_PANEL, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=10)
        left_panel.pack_propagate(False)

        # Waveform canvas
        tk.Label(
            left_panel, text="AUDIO MONITOR",
            font=self.font_small, bg=config.COLOR_BG_PANEL,
            fg=config.COLOR_TEXT_MUTED
        ).pack(pady=(12, 4))

        self.canvas = tk.Canvas(
            left_panel, width=240, height=80,
            bg=config.COLOR_BG_DARK, highlightthickness=1,
            highlightbackground=config.COLOR_TEXT_MUTED
        )
        self.canvas.pack(padx=16)
        self._draw_idle_waveform()

        # Last command display
        tk.Frame(left_panel, bg=config.COLOR_TEXT_MUTED, height=1).pack(fill=tk.X, pady=12, padx=16)

        tk.Label(
            left_panel, text="LAST COMMAND",
            font=self.font_small, bg=config.COLOR_BG_PANEL,
            fg=config.COLOR_TEXT_MUTED
        ).pack(anchor=tk.W, padx=16)

        tk.Label(
            left_panel, textvariable=self.last_command,
            font=self.font_accent, bg=config.COLOR_BG_PANEL,
            fg=config.COLOR_ACCENT, wraplength=240, justify=tk.LEFT
        ).pack(anchor=tk.W, padx=16, pady=(2, 12))

        # Control Buttons
        tk.Label(
            left_panel, text="CONTROLS",
            font=self.font_small, bg=config.COLOR_BG_PANEL,
            fg=config.COLOR_TEXT_MUTED
        ).pack(anchor=tk.W, padx=16)

        btn_frame = tk.Frame(left_panel, bg=config.COLOR_BG_PANEL)
        btn_frame.pack(fill=tk.X, padx=16, pady=(4, 8))

        self.btn_start = self._make_button(
            btn_frame, "▶  START", config.COLOR_SUCCESS,
            command=self._start_listening
        )
        self.btn_start.pack(fill=tk.X, pady=2)

        self.btn_stop = self._make_button(
            btn_frame, "■  STOP", config.COLOR_ERROR,
            command=self._stop_listening, state=tk.DISABLED
        )
        self.btn_stop.pack(fill=tk.X, pady=2)

        self.btn_history = self._make_button(
            btn_frame, "≡  HISTORY", config.COLOR_ACCENT_2,
            command=self._show_history_window
        )
        self.btn_history.pack(fill=tk.X, pady=2)

        self.btn_clear = self._make_button(
            btn_frame, "✕  CLEAR LOG", config.COLOR_TEXT_MUTED,
            command=self._clear_history
        )
        self.btn_clear.pack(fill=tk.X, pady=2)

        # TTS Toggle
        tk.Frame(left_panel, bg=config.COLOR_TEXT_MUTED, height=1).pack(fill=tk.X, pady=8, padx=16)

        tts_frame = tk.Frame(left_panel, bg=config.COLOR_BG_PANEL)
        tts_frame.pack(fill=tk.X, padx=16)

        tk.Checkbutton(
            tts_frame, text="Voice Responses (TTS)",
            variable=self.tts_enabled,
            command=self._toggle_tts,
            bg=config.COLOR_BG_PANEL, fg=config.COLOR_TEXT_SECONDARY,
            selectcolor=config.COLOR_BG_DARK,
            activebackground=config.COLOR_BG_PANEL,
            font=self.font_small
        ).pack(anchor=tk.W)

        # System info mini-panel
        tk.Frame(left_panel, bg=config.COLOR_TEXT_MUTED, height=1).pack(fill=tk.X, pady=8, padx=16)

        tk.Label(
            left_panel, text="SYSTEM MONITOR",
            font=self.font_small, bg=config.COLOR_BG_PANEL,
            fg=config.COLOR_TEXT_MUTED
        ).pack(anchor=tk.W, padx=16)

        self.sysmon_frame = tk.Frame(left_panel, bg=config.COLOR_BG_PANEL)
        self.sysmon_frame.pack(fill=tk.X, padx=16, pady=4)
        self._build_sysmon_widgets()

        # ── Right Panel ────────────────────────────────────────────────────
        right_panel = tk.Frame(main, bg=config.COLOR_BG_DARK)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True,
                         padx=(5, 10), pady=10)

        # Response area
        resp_frame = tk.Frame(right_panel, bg=config.COLOR_BG_PANEL)
        resp_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            resp_frame, text="ASSISTANT RESPONSE",
            font=self.font_small, bg=config.COLOR_BG_PANEL,
            fg=config.COLOR_TEXT_MUTED
        ).pack(anchor=tk.W, padx=14, pady=(10, 2))

        self.response_label = tk.Label(
            resp_frame, textvariable=self.last_response,
            font=self.font_body, bg=config.COLOR_BG_PANEL,
            fg=config.COLOR_TEXT_PRIMARY,
            wraplength=480, justify=tk.LEFT, anchor=tk.W
        )
        self.response_label.pack(fill=tk.X, padx=14, pady=(0, 12))

        # Command log
        log_frame = tk.Frame(right_panel, bg=config.COLOR_BG_PANEL)
        log_frame.pack(fill=tk.BOTH, expand=True)

        log_header = tk.Frame(log_frame, bg=config.COLOR_BG_PANEL)
        log_header.pack(fill=tk.X)

        tk.Label(
            log_header, text="COMMAND LOG",
            font=self.font_small, bg=config.COLOR_BG_PANEL,
            fg=config.COLOR_TEXT_MUTED
        ).pack(side=tk.LEFT, padx=14, pady=(10, 2))

        self.log_box = scrolledtext.ScrolledText(
            log_frame,
            bg=config.COLOR_BG_DARK,
            fg=config.COLOR_TEXT_SECONDARY,
            font=self.font_mono,
            insertbackground=config.COLOR_ACCENT,
            relief=tk.FLAT,
            borderwidth=0,
            padx=8, pady=8,
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        # Configure text tags
        self.log_box.tag_configure("success", foreground=config.COLOR_SUCCESS)
        self.log_box.tag_configure("error",   foreground=config.COLOR_ERROR)
        self.log_box.tag_configure("info",    foreground=config.COLOR_ACCENT)
        self.log_box.tag_configure("muted",   foreground=config.COLOR_TEXT_MUTED)
        self.log_box.tag_configure("warn",    foreground=config.COLOR_WARNING)

    def _build_footer(self):
        tk.Frame(self.root, bg=config.COLOR_TEXT_MUTED, height=1).pack(fill=tk.X)

        footer = tk.Frame(self.root, bg=config.COLOR_BG_PANEL, height=50)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)

        tk.Label(
            footer, text="TYPE COMMAND:",
            font=self.font_small, bg=config.COLOR_BG_PANEL,
            fg=config.COLOR_TEXT_MUTED
        ).pack(side=tk.LEFT, padx=(14, 6), pady=14)

        self.text_input = tk.Entry(
            footer,
            bg=config.COLOR_BG_DARK, fg=config.COLOR_TEXT_PRIMARY,
            insertbackground=config.COLOR_ACCENT,
            font=self.font_body,
            relief=tk.FLAT,
            width=45
        )
        self.text_input.pack(side=tk.LEFT, ipady=5, pady=10)
        self.text_input.bind("<Return>", self._on_text_submit)

        self._make_button(
            footer, "SEND", config.COLOR_ACCENT,
            command=self._on_text_submit
        ).pack(side=tk.LEFT, padx=6, pady=10)

    def _build_sysmon_widgets(self):
        """Build CPU/RAM progress bar widgets in the left panel."""
        for widget in self.sysmon_frame.winfo_children():
            widget.destroy()

        metrics = [("CPU", "cpu"), ("RAM", "mem")]
        self._sysmon_bars = {}
        self._sysmon_labels = {}

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Sysmon.Horizontal.TProgressbar",
            background=config.COLOR_ACCENT,
            troughcolor=config.COLOR_BG_DARK,
            bordercolor=config.COLOR_BG_DARK,
            lightcolor=config.COLOR_ACCENT,
            darkcolor=config.COLOR_ACCENT,
        )

        for label, key in metrics:
            row = tk.Frame(self.sysmon_frame, bg=config.COLOR_BG_PANEL)
            row.pack(fill=tk.X, pady=1)

            tk.Label(
                row, text=f"{label}:", font=self.font_small,
                bg=config.COLOR_BG_PANEL, fg=config.COLOR_TEXT_MUTED,
                width=4, anchor=tk.W
            ).pack(side=tk.LEFT)

            bar = ttk.Progressbar(
                row, style="Sysmon.Horizontal.TProgressbar",
                orient=tk.HORIZONTAL, length=130, mode="determinate"
            )
            bar.pack(side=tk.LEFT, padx=4)
            self._sysmon_bars[key] = bar

            lbl = tk.Label(
                row, text="0%", font=self.font_small,
                bg=config.COLOR_BG_PANEL, fg=config.COLOR_TEXT_SECONDARY,
                width=4
            )
            lbl.pack(side=tk.LEFT)
            self._sysmon_labels[key] = lbl

    def _make_button(self, parent, text, color, command=None, state=tk.NORMAL):
        """Create a flat-style button with hover effect."""
        btn = tk.Button(
            parent, text=text,
            bg=config.COLOR_BG_MID, fg=color,
            activebackground=color, activeforeground=config.COLOR_BG_DARK,
            font=self.font_small, relief=tk.FLAT,
            cursor="hand2", state=state,
            padx=8, pady=5, command=command,
            borderwidth=1, highlightthickness=0
        )

        def on_enter(e):
            if btn["state"] != tk.DISABLED:
                btn.config(bg=color, fg=config.COLOR_BG_DARK)

        def on_leave(e):
            if btn["state"] != tk.DISABLED:
                btn.config(bg=config.COLOR_BG_MID, fg=color)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        return btn

    # ─── Module Initialization ─────────────────────────────────────────────────

    def _init_modules(self):
        self.logger = CommandLogger()
        self.tts = TTSEngine()

        self.processor = CommandProcessor(
            tts=self.tts,
            on_confirm=self._confirm_dialog
        )

        try:
            self.speech = SpeechEngine(
                on_result=self._on_speech_result,
                on_error=self._on_speech_error,
                on_status=self._on_status_update
            )
            self._log("System", "Voice assistant initialized. Ready!", "info")
        except ImportError as e:
            self.speech = None
            self._log("Warning", str(e), "warn")
            self._log("Info", "Text input is still available.", "info")

        self._append_welcome()

    def _append_welcome(self):
        self._log("AI", f"Hello! I'm {config.ASSISTANT_NAME}, your AI Voice Assistant.", "info")
        self._log("AI", "Click START or press Enter in the text box to give commands.", "info")
        self._log("AI", "Say 'help' for a list of available commands.", "muted")

    # ─── Event Handlers ────────────────────────────────────────────────────────

    def _start_listening(self):
        if not self.speech:
            messagebox.showwarning(
                "Unavailable",
                "SpeechRecognition/PyAudio not installed.\nUse the text input instead."
            )
            return

        self.speech.start()
        self.is_listening.set(True)
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self._start_pulse()
        self.status_text.set("Listening...")
        self._log("System", "Voice recognition started.", "success")

    def _stop_listening(self):
        if self.speech:
            self.speech.stop()
        self.is_listening.set(False)
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self._stop_pulse()
        self.status_text.set("Stopped. Press START to resume.")
        self._log("System", "Voice recognition stopped.", "warn")

    def _on_speech_result(self, text: str):
        """Called from speech thread when speech is recognized."""
        self.root.after(0, lambda: self._process_command(text))

    def _on_speech_error(self, msg: str):
        self.root.after(0, lambda: self._log("Error", msg, "error"))

    def _on_status_update(self, msg: str):
        self.root.after(0, lambda: self.status_text.set(msg))

    def _on_text_submit(self, event=None):
        text = self.text_input.get().strip()
        if text:
            self.text_input.delete(0, tk.END)
            self._process_command(text)

    def _process_command(self, text: str):
        """Process a command (from voice or text input) on the main thread."""
        if not text:
            return

        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.last_command.set(f'"{text}"')
        self._log("You", f'[{ts}] "{text}"', "info")

        # Run processor in background thread to avoid blocking GUI
        def run():
            result = self.processor.process(text)
            self.root.after(0, lambda: self._show_result(text, result))

        threading.Thread(target=run, daemon=True).start()

    def _show_result(self, command: str, result):
        """Display the command result in the GUI."""
        self.last_response.set(result.response)
        tag = "success" if result.success else "error"
        self._log("ARIA", result.response, tag)
        self.logger.log(command, result.response, result.success)

        # Special case: exit
        if result.action == "exit":
            self.root.after(2000, self._on_close)

        # Special case: stop listening
        if result.action == "stop" and self.is_listening.get():
            self._stop_listening()

    def _toggle_tts(self):
        enabled = self.tts_enabled.get()
        self.tts.set_enabled(enabled)
        state = "enabled" if enabled else "disabled"
        self._log("System", f"Voice responses {state}.", "muted")

    def _confirm_dialog(self, message: str) -> bool:
        return messagebox.askyesno("Confirm Action", message, parent=self.root)

    def _show_history_window(self):
        """Open a separate window showing full command history."""
        win = tk.Toplevel(self.root)
        win.title("Command History")
        win.geometry("600x450")
        win.configure(bg=config.COLOR_BG_DARK)

        tk.Label(
            win, text="COMMAND HISTORY",
            font=self.font_subheader,
            bg=config.COLOR_BG_DARK, fg=config.COLOR_ACCENT
        ).pack(pady=(12, 4))

        text = scrolledtext.ScrolledText(
            win, bg=config.COLOR_BG_MID, fg=config.COLOR_TEXT_SECONDARY,
            font=self.font_small, relief=tk.FLAT, padx=8, pady=8
        )
        text.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        history = self.logger.load_history()
        if history:
            for line in history[-config.MAX_HISTORY_DISPLAY:]:
                text.insert(tk.END, line)
        else:
            text.insert(tk.END, "No history recorded yet.")

        text.config(state=tk.DISABLED)

    def _clear_history(self):
        if messagebox.askyesno("Clear Log", "Clear the command log?", parent=self.root):
            self.logger.clear()
            self.log_box.config(state=tk.NORMAL)
            self.log_box.delete(1.0, tk.END)
            self.log_box.config(state=tk.DISABLED)
            self._log("System", "Log cleared.", "muted")

    # ─── Waveform Animation ────────────────────────────────────────────────────

    def _draw_idle_waveform(self):
        self.canvas.delete("all")
        w, h = 240, 80
        mid = h // 2
        # Draw flat line
        self.canvas.create_line(0, mid, w, mid, fill=config.COLOR_TEXT_MUTED, width=1)

    def _draw_active_waveform(self):
        """Draw animated waveform bars when listening."""
        import math, random
        self.canvas.delete("all")
        w, h = 240, 80
        mid = h // 2
        bars = 24
        bar_w = w // bars
        t = self._pulse_state * 0.3

        for i in range(bars):
            amp = (math.sin(t + i * 0.5) * 0.5 + 0.5) * 28 + 4
            amp += random.uniform(-3, 3)
            x = i * bar_w + bar_w // 2
            self.canvas.create_line(
                x, mid - amp, x, mid + amp,
                fill=config.COLOR_ACCENT, width=2
            )

    def _start_pulse(self):
        self._pulse_anim()

    def _pulse_anim(self):
        if self.is_listening.get():
            self._pulse_state += 1
            self._draw_active_waveform()
            # Also pulse the indicator dot
            colors = [config.COLOR_ACCENT, config.COLOR_SUCCESS, config.COLOR_ACCENT_2]
            self._indicator_dot.config(fg=colors[self._pulse_state % len(colors)])
            self._anim_job = self.root.after(120, self._pulse_anim)

    def _stop_pulse(self):
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None
        self._draw_idle_waveform()
        self._indicator_dot.config(fg=config.COLOR_TEXT_MUTED)

    # ─── System Monitor ────────────────────────────────────────────────────────

    def _start_sys_monitor(self):
        self._update_sysmon()

    def _update_sysmon(self):
        if PSUTIL_AVAILABLE:
            try:
                cpu = psutil.cpu_percent(interval=None)
                mem = psutil.virtual_memory().percent
                self._sysmon_bars["cpu"]["value"] = cpu
                self._sysmon_bars["mem"]["value"] = mem
                self._sysmon_labels["cpu"].config(text=f"{cpu:.0f}%")
                self._sysmon_labels["mem"].config(text=f"{mem:.0f}%")
            except Exception:
                pass
        self._sysmon_job = self.root.after(3000, self._update_sysmon)

    # ─── Log Helper ────────────────────────────────────────────────────────────

    def _log(self, sender: str, message: str, tag: str = ""):
        self.log_box.config(state=tk.NORMAL)
        prefix = f"[{sender}] "
        self.log_box.insert(tk.END, prefix, "muted")
        self.log_box.insert(tk.END, message + "\n", tag or "")
        self.log_box.see(tk.END)
        self.log_box.config(state=tk.DISABLED)

    # ─── Cleanup ───────────────────────────────────────────────────────────────

    def _on_close(self):
        if self.speech and self.speech.is_listening:
            self.speech.stop()
        self.tts.shutdown()
        if self._sysmon_job:
            self.root.after_cancel(self._sysmon_job)
        self.root.destroy()

    def run(self):
        self.root.mainloop()
