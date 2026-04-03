"""
modules/command_processor.py

The brain of the assistant.

Pattern Recognition Strategy:
    1. Keyword Matching   — fast O(1) dictionary lookup for exact/partial matches
    2. Intent Parsing     — extract action + target from command strings
    3. Fuzzy Matching     — difflib.SequenceMatcher for near-miss recovery
    4. Regex Extraction   — pull out URLs, filenames, search terms

This layered approach mirrors a simplified NLU (Natural Language Understanding)
pipeline without requiring a large language model.
"""

import re
import difflib
import webbrowser
import os
import subprocess
import platform
import sys
import psutil

import config
from system_controller import SystemController
from system_info import SystemInfo

# ─── Command Intent Definitions ───────────────────────────────────────────────
# Structure: { "intent_name": [trigger_phrases...] }
# The processor checks if ANY trigger phrase is a substring of the input.

COMMAND_INTENTS = {
    # ── Web & Search ────────────────────────────────────────────────────
    "open_youtube":       ["open youtube", "go to youtube", "play youtube"],
    "open_google":        ["open google", "go to google"],
    "open_github":        ["open github", "go to github"],
    "open_wikipedia":     ["open wikipedia", "go to wikipedia"],
    "open_gmail":         ["open gmail", "go to gmail", "check email"],
    "open_maps":          ["open maps", "google maps", "open google maps"],
    "search_google":      ["search for", "google", "look up", "search the web"],
    "search_youtube":     ["search youtube", "search on youtube", "youtube search", "play on youtube", "play song", "play music", "play "],
    "open_website":       ["open website", "open site", "go to", "visit"],

    # ── Applications ────────────────────────────────────────────────────
    "open_calculator":    ["open calculator", "launch calculator", "calculator"],
    "open_notepad":       ["open notepad", "launch notepad", "open text editor"],
    "open_browser":       ["open browser", "open chrome", "open firefox", "open edge"],
    "open_file_manager":  ["file", "files", "explorer", "file explorer", "open file manager", "open explorer", "open finder", "file manager"],
    "open_terminal":      ["terminal", "cmd", "open terminal", "open command prompt", "open cmd", "open powershell"],
    "open_vscode":        ["open vscode", "open visual studio code", "open code editor"],
    "open_task_manager":  ["open task manager", "open activity monitor"],
    "open_settings":      ["open settings", "system settings", "open preferences"],
    "open_camera":        ["camera", "open camera", "camera app", "webcam"],
    "open_app":           ["open ", "launch ", "start "],  # generic fallback
    "close_app":          ["close ", "stop ", "terminate ", "kill ", "quit "],
    "close_all_apps":     ["close all apps", "close all applications", "close everything", "terminate all apps"],
    "list_tasks":         ["list tasks", "show tasks", "show running", "what is running", "running apps", "running processes"],

    # ── File Operations ─────────────────────────────────────────────────
    "create_file":        ["create file", "make file", "new file", "create a file", "create one file", "make a file"],
    "delete_file":        ["delete file", "remove file", "delete a file", "delete one file", "remove a file"],
    "rename_file":        ["rename file", "rename a file", "rename one file"],

    # ── System Information ───────────────────────────────────────────────
    "cpu_usage":          ["cpu usage", "processor usage", "how is my cpu", "check cpu"],
    "memory_usage":       ["memory usage", "ram usage", "how much ram", "check memory"],
    "battery_status":     ["battery", "battery status", "battery level", "how much battery"],
    "disk_usage":         ["disk usage", "storage", "disk space", "hard drive"],
    "system_info":        ["system info", "system information", "about my computer"],
    "ip_address":         ["ip address", "my ip", "what is my ip"],

    # ── System Control ───────────────────────────────────────────────────
    "shutdown":           ["shutdown", "shut down", "turn off computer", "power off"],
    "restart":            ["restart", "reboot", "restart computer"],
    "sleep":              ["sleep", "sleep mode", "hibernate", "put to sleep"],
    "lock_screen":        ["lock screen", "lock computer", "lock the screen"],
    "take_screenshot":    ["screenshot", "take a screenshot", "capture screen"],
    "increase_volume":    ["increase volume", "volume up", "louder"],
    "decrease_volume":    ["decrease volume", "volume down", "quieter"],
    "mute":               ["mute", "mute volume", "silence"],
    "increase_brightness": ["increase brightness", "brightness up", "brighter", "more light", "increase light"],
    "decrease_brightness": ["decrease brightness", "brightness down", "dimmer", "less light", "decrease light"],

    # ── Assistant Control ────────────────────────────────────────────────
    "stop_listening":     ["stop listening", "stop assistant", "go to sleep", "pause"],
    "help":               ["help", "what can you do", "commands", "list commands"],
    "greet":              ["hello", "hi aria", "hey", "good morning", "good afternoon", "good evening"],
    "tell_time":          ["what time", "current time", "tell me the time", "time"],
    "tell_date":          ["what date", "today's date", "what day", "date today", "date"],
    "joke":               ["tell me a joke", "joke", "make me laugh"],
    "thank":              ["thank you", "thanks", "appreciate it"],
    "bye":                ["goodbye", "bye", "see you", "exit", "quit"],
}

# ─── Common Application Paths by Platform ─────────────────────────────────────
APP_PATHS = {
    "Windows": {
        "calculator":    "calc.exe",
        "notepad":       "notepad.exe",
        "paint":         "mspaint.exe",
        "chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "firefox":       r"C:\Program Files\Mozilla Firefox\firefox.exe",
        "edge":          "msedge.exe",
        "word":          r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
        "excel":         r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
        "vscode":        r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "explorer":      "explorer.exe",
        "file manager":  "explorer.exe",
        "cmd":           "cmd.exe",
        "camera":        "microsoft.windows.camera:",
        "powershell":    "powershell.exe",
        "terminal":      "powershell.exe",
        "task manager":  "taskmgr.exe",
        "settings":      "ms-settings:",
    },
    "Linux": {
        "calculator":    "gnome-calculator",
        "notepad":       "gedit",
        "chrome":        "google-chrome",
        "firefox":       "firefox",
        "vscode":        "code",
        "file manager":  "nautilus",
        "terminal":      "gnome-terminal",
        "settings":      "gnome-control-center",
    },
    "Darwin": {  # macOS
        "calculator":    "open -a Calculator",
        "notepad":       "open -a TextEdit",
        "chrome":        "open -a 'Google Chrome'",
        "firefox":       "open -a Firefox",
        "vscode":        "open -a 'Visual Studio Code'",
        "file manager":  "open ~",
        "terminal":      "open -a Terminal",
        "settings":      "open -a 'System Preferences'",
    }
}

JOKES = [
    "Why do programmers prefer dark mode? Because light attracts bugs!",
    "I asked my AI assistant a question. It said 'I cannot answer that.' So I asked it again in a different voice.",
    "Why was the computer cold? Because it left its Windows open!",
    "What do you call a computer that sings? A Dell.",
    "Why do Java developers wear glasses? Because they don't C sharp!",
]


class CommandResult:
    """Encapsulates the result of processing a command."""

    def __init__(self, success: bool, response: str, action: str = ""):
        self.success = success
        self.response = response
        self.action = action  # Human-readable action description

    def __repr__(self):
        return f"CommandResult(success={self.success}, action={self.action!r})"


class CommandProcessor:
    """
    Analyzes recognized speech text and dispatches system actions.

    Pattern Recognition Pipeline:
        Input text → Normalize → Intent Match → Parameter Extract → Execute
    """

    def __init__(self, tts=None, on_confirm=None):
        """
        Args:
            tts        : TTSEngine instance for spoken responses.
            on_confirm : Callable(message) -> bool for dangerous command confirmation.
        """
        self.tts = tts
        self.on_confirm = on_confirm
        self.sys_ctrl = SystemController()
        self.sys_info = SystemInfo()
        self._platform = platform.system()
        self._joke_index = 0

    def process(self, text: str) -> CommandResult:
        """
        Main entry point. Takes raw recognized speech text, returns a CommandResult.

        Step 1: Normalize text (lowercase, strip punctuation)
        Step 2: Match against known intents using keyword scanning
        Step 3: If no direct match, attempt fuzzy matching
        Step 4: Execute matched intent handler
        """
        if not text or not text.strip():
            return CommandResult(False, "No command detected.", "none")

        text = self._normalize(text)

        # ── Step 2: Direct Intent Matching ────────────────────────────────
        intent = self._match_intent(text)

        # ── Step 3: Fuzzy Fallback ─────────────────────────────────────────
        if not intent:
            intent = self._fuzzy_match(text)

        if not intent:
            return CommandResult(
                False,
                'I didn\'t understand: "' + text + '". Say "help" for available commands.',
                "unrecognized"
            )

        # ── Step 4: Execute handler ────────────────────────────────────────
        return self._dispatch(intent, text)

    # ─── Normalization ─────────────────────────────────────────────────────────

    def _normalize(self, text: str) -> str:
        """Clean and normalize input text for matching."""
        text = text.lower().strip()
        # Remove filler words
        for filler in ["please", "can you", "could you", "i want to", "i need to", "aria"]:
            text = text.replace(filler, "").strip()
        return text

    # ─── Intent Matching ───────────────────────────────────────────────────────

    def _match_intent(self, text: str) -> str | None:
        """
        Keyword scanning: check each intent's trigger phrases against the input.
        Returns the intent with the highest score (length + prefix boost) to avoid overlapping captures.
        """
        best_intent = None
        best_score = 0
        for intent, phrases in COMMAND_INTENTS.items():
            # Prevent generic actions from overriding specific explicit targets
            if "youtube" in text and intent in ["search_google", "open_website", "open_app"]:
                continue
                
            for phrase in phrases:
                if phrase in text:
                    score = len(phrase)
                    # Boost score massively if the command starts with the trigger phrase
                    # This ensures action verbs ("close ", "open ") beat out target nouns ("google")
                    if text.startswith(phrase):
                        score += 100
                        
                    if score > best_score:
                        best_score = score
                        best_intent = intent
        return best_intent

    def _fuzzy_match(self, text: str) -> str | None:
        """
        Use difflib to find the closest intent trigger phrase.
        Returns intent name if similarity >= threshold, else None.
        """
        all_phrases = []
        phrase_to_intent = {}
        for intent, phrases in COMMAND_INTENTS.items():
            for phrase in phrases:
                all_phrases.append(phrase)
                phrase_to_intent[phrase] = intent

        matches = difflib.get_close_matches(
            text, all_phrases,
            n=1,
            cutoff=config.MIN_CONFIDENCE_THRESHOLD
        )

        if matches:
            return phrase_to_intent[matches[0]]
        return None

    # ─── Parameter Extraction ──────────────────────────────────────────────────

    def _extract_search_query(self, text: str) -> str:
        """Extract search term from command text."""
        for prefix in ["search for", "google", "look up", "search"]:
            if prefix in text:
                return text.split(prefix, 1)[-1].strip()
        return text.strip()

    def _extract_website(self, text: str) -> str:
        """Extract a website name or URL from command text."""
        for prefix in ["open website", "open site", "go to", "visit", "open"]:
            if prefix in text:
                target = text.split(prefix, 1)[-1].strip()
                if target:
                    if not target.startswith("http"):
                        if "." not in target:
                            target = f"www.{target}.com"
                        else:
                            target = f"https://{target}"
                    return target
        return ""

    def _extract_app_name(self, text: str) -> str:
        """Extract application name from a generic open/launch/close command."""
        for prefix in ["open ", "launch ", "start ", "close ", "stop ", "terminate ", "kill ", "quit "]:
            if text.startswith(prefix):
                return text[len(prefix):].strip()
            elif prefix in text:
                return text.split(prefix, 1)[-1].strip()
        return text.strip()

    # ─── Intent Dispatcher ─────────────────────────────────────────────────────

    def _dispatch(self, intent: str, text: str) -> CommandResult:
        """Route intent to its handler method."""
        handlers = {
            # Web
            "open_youtube":      lambda: self._open_url("https://www.youtube.com", "YouTube"),
            "open_google":       lambda: self._open_url("https://www.google.com", "Google"),
            "open_github":       lambda: self._open_url("https://www.github.com", "GitHub"),
            "open_wikipedia":    lambda: self._open_url("https://www.wikipedia.org", "Wikipedia"),
            "open_gmail":        lambda: self._open_url("https://mail.google.com", "Gmail"),
            "open_maps":         lambda: self._open_url("https://maps.google.com", "Google Maps"),
            "search_google":     lambda: self._search_google(text),
            "search_youtube":    lambda: self._search_youtube(text),
            "open_website":      lambda: self._open_website(text),

            # File Operations
            "create_file":       lambda: self._create_file(text),
            "delete_file":       lambda: self._delete_file(text),
            "rename_file":       lambda: self._rename_file(text),

            # Apps
            "open_calculator":   lambda: self._open_app("calculator"),
            "open_notepad":      lambda: self._open_app("notepad"),
            "open_browser":      lambda: self._open_app("chrome"),
            "open_file_manager": lambda: self._open_app("file manager"),
            "open_terminal":     lambda: self._open_app("terminal"),
            "open_vscode":       lambda: self._open_app("vscode"),
            "open_task_manager": lambda: self._open_app("task manager"),
            "open_settings":     lambda: self._open_app("settings"),
            "open_camera":       lambda: self._open_app("camera"),
            "close_app":         lambda: self._close_app(text),
            "close_all_apps":    lambda: self._close_all_apps(),
            "open_app":          lambda: self._open_generic_app(text),
            "list_tasks":        lambda: self._list_tasks(),

            # Sysinfo
            "cpu_usage":         lambda: self._get_cpu(),
            "memory_usage":      lambda: self._get_memory(),
            "battery_status":    lambda: self._get_battery(),
            "disk_usage":        lambda: self._get_disk(),
            "system_info":       lambda: self._get_system_info(),
            "ip_address":        lambda: self._get_ip(),

            # System Control
            "shutdown":          lambda: self._shutdown(),
            "restart":           lambda: self._restart(),
            "sleep":             lambda: self._sleep(),
            "lock_screen":       lambda: self._lock_screen(),
            "take_screenshot":   lambda: self._screenshot(),
            "increase_volume":   lambda: self._volume("up"),
            "decrease_volume":   lambda: self._volume("down"),
            "mute":              lambda: self._volume("mute"),
            "increase_brightness": lambda: self._brightness("up"),
            "decrease_brightness": lambda: self._brightness("down"),

            # Assistant
            "stop_listening":    lambda: CommandResult(True, "Going to sleep. Say my name to wake me!", "stop"),
            "help":              lambda: self._help(),
            "greet":             lambda: self._greet(),
            "tell_time":         lambda: self._tell_time(),
            "tell_date":         lambda: self._tell_date(),
            "joke":              lambda: self._tell_joke(),
            "thank":             lambda: CommandResult(True, "You're welcome! Anything else I can help with?", "thank"),
            "bye":               lambda: CommandResult(True, "Goodbye! Have a great day!", "exit"),
        }

        handler = handlers.get(intent)
        if handler:
            try:
                result = handler()
                if self.tts and result.success:
                    self.tts.speak(result.response)
                return result
            except Exception as e:
                msg = f"Error executing command: {e}"
                return CommandResult(False, msg, intent)

        return CommandResult(False, "Command handler not implemented.", intent)

    # ─── Handler Implementations ───────────────────────────────────────────────

    def _proc_names_for_app(self, app_key: str, cmd: str | None) -> list[str]:
        """
        Best-effort mapping from an app key/command to likely process names.
        Used to decide whether an app is already running and to close it.
        """
        app_key = (app_key or "").strip().lower()
        platform_name = self._platform

        names: list[str] = []

        if platform_name == "Windows":
            # Prefer executable basename when available
            if cmd:
                base = os.path.basename(os.path.expandvars(cmd)).strip().strip('"').lower()
                if base.endswith(".exe"):
                    names.append(base)
                elif base:
                    names.append(base + ".exe")

            # Known Windows app process names / special cases
            special = {
                "calculator": ["calc.exe", "calculatorapp.exe"],
                "task manager": ["taskmgr.exe"],
                "file manager": ["explorer.exe"],
                "explorer": ["explorer.exe"],
                "terminal": ["windowsterminal.exe", "wt.exe"],
                "powershell": ["powershell.exe", "pwsh.exe"],
                "cmd": ["cmd.exe"],
                "vscode": ["code.exe"],
                "chrome": ["chrome.exe"],
                "edge": ["msedge.exe"],
                "firefox": ["firefox.exe"],
                "notepad": ["notepad.exe"],
                "camera": ["windowscamera.exe"],
                "settings": ["systemsettings.exe"],
            }
            names.extend(special.get(app_key, []))

        elif platform_name == "Linux":
            if cmd:
                names.append(os.path.basename(cmd.split()[0]).lower())
            special = {
                "terminal": ["gnome-terminal", "konsole", "xterm"],
                "file manager": ["nautilus", "dolphin", "thunar"],
                "vscode": ["code"],
                "chrome": ["google-chrome", "chrome"],
                "firefox": ["firefox"],
                "calculator": ["gnome-calculator"],
                "notepad": ["gedit"],
                "settings": ["gnome-control-center"],
            }
            names.extend(special.get(app_key, []))

        elif platform_name == "Darwin":
            # On macOS we mostly rely on app name matching
            if app_key:
                names.append(app_key)
            if cmd and "open -a" in cmd:
                # extract "open -a <App>"
                try:
                    after = cmd.split("open -a", 1)[1].strip().strip("'").strip('"')
                    if after:
                        names.append(after.lower())
                except Exception:
                    pass

        # De-duplicate while preserving order
        out: list[str] = []
        seen = set()
        for n in names:
            n = (n or "").strip().lower()
            if n and n not in seen:
                out.append(n)
                seen.add(n)
        return out

    def _toggle_close_allowed(self, app_name: str) -> bool:
        """
        Some Windows apps should NOT be auto-closed when you say "open <app>"
        because closing them is disruptive or ambiguous.
        """
        name = (app_name or "").strip().lower()
        if self._platform == "Windows":
            # Avoid closing the shell/UI or system UIs via the toggle behavior
            blocked = {"file manager", "explorer", "task manager", "settings", "terminal"}
            return name not in blocked
        return True

    def _find_processes_by_names(self, names: list[str]) -> list[psutil.Process]:
        """Return processes whose name matches any of `names` (case-insensitive)."""
        want = {n.lower() for n in (names or []) if n}
        if not want:
            return []
        procs: list[psutil.Process] = []
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pname = (proc.info.get("name") or "").lower()
                if pname and pname in want:
                    procs.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return procs

    def _close_processes(self, procs: list[psutil.Process]) -> tuple[int, int]:
        """
        Try graceful terminate first, then force kill.
        Returns (terminated_count, killed_count).
        """
        terminated = 0
        killed = 0
        if not procs:
            return (0, 0)

        # Attempt graceful termination
        for p in procs:
            try:
                p.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        gone, alive = psutil.wait_procs(procs, timeout=2)
        terminated += len(gone)

        # Force kill remaining
        for p in alive:
            try:
                p.kill()
                killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        return (terminated, killed)

    def _open_url(self, url: str, name: str) -> CommandResult:
        webbrowser.open(url)
        return CommandResult(True, f"Opening {name} in your browser.", f"open_url:{url}")

    def _search_google(self, text: str) -> CommandResult:
        query = self._extract_search_query(text)
        if not query:
            return CommandResult(False, "What would you like me to search for?", "search")
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return CommandResult(True, f"Searching Google for: {query}", f"search:{query}")

    def _search_youtube(self, text: str) -> CommandResult:
        import re
        query = text
        for prefix in ["search youtube for", "search for", "search youtube", "search on youtube", "youtube search", "play song on youtube", "play song", "play music", "play on youtube", "play "]:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
                break
        
        query = re.sub(r'\s+(on|in)\s+youtube$', '', query).strip()
        
        if query:
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            webbrowser.open(url)
            return CommandResult(True, f"Searching YouTube for: {query}", f"search_youtube:{query}")
        return CommandResult(False, "What would you like to search on YouTube?", "search_youtube")

    def _open_website(self, text: str) -> CommandResult:
        url = self._extract_website(text)
        if not url:
            return CommandResult(False, "Please specify a website to open.", "open_website")
        webbrowser.open(url)
        return CommandResult(True, f"Opening {url}", f"open_website:{url}")

    def _extract_filename(self, text: str, prefixes: list[str]) -> str:
        for prefix in prefixes:
            if prefix in text:
                return text.split(prefix, 1)[-1].strip()
        return ""

    def _create_file(self, text: str) -> CommandResult:
        filename = self._extract_filename(text, ["create a file", "create one file", "create file", "make a file", "make file", "new file"])
        import re
        filename = re.sub(r'^(named|name|called)\s+', '', filename).strip()
        if not filename:
            return CommandResult(False, "Please specify a file name to create.", "create_file")
        try:
            with open(filename, 'w') as f:
                f.write('')
            return CommandResult(True, f"Created file {filename}.", f"create_file:{filename}")
        except Exception as e:
            return CommandResult(False, f"Could not create file: {e}", "create_file")

    def _delete_file(self, text: str) -> CommandResult:
        filename = self._extract_filename(text, ["delete a file", "delete one file", "delete file", "remove a file", "remove file"])
        import re
        filename = re.sub(r'^(named|name|called)\s+', '', filename).strip()
        if not filename:
            return CommandResult(False, "Please specify a file name to delete.", "delete_file")
        try:
            if os.path.exists(filename):
                os.remove(filename)
                return CommandResult(True, f"Deleted file {filename}.", f"delete_file:{filename}")
            else:
                return CommandResult(False, f"File {filename} does not exist.", "delete_file")
        except Exception as e:
            return CommandResult(False, f"Could not delete file: {e}", "delete_file")

    def _rename_file(self, text: str) -> CommandResult:
        import re
        text = re.sub(r'rename (one |a )?file (named |name |called )?', 'rename file ', text)
        match = re.search(r'rename file (.*?) to (.*)', text)
        if not match:
             return CommandResult(False, "Please specify old and new file names using 'rename file <old> to <new>'.", "rename_file")
        old_name = match.group(1).strip()
        new_name = match.group(2).strip()
        try:
            if os.path.exists(old_name):
                os.rename(old_name, new_name)
                return CommandResult(True, f"Renamed {old_name} to {new_name}.", "rename_file")
            else:
                return CommandResult(False, f"File {old_name} does not exist.", "rename_file")
        except Exception as e:
            return CommandResult(False, f"Could not rename file: {e}", "rename_file")

    def _open_app(self, app_name: str) -> CommandResult:
        apps = APP_PATHS.get(self._platform, {})
        cmd = apps.get(app_name.lower())

        if not cmd:
            return self._open_generic_app(app_name)

        try:
            # Smart behavior: if already running, close it (toggle)
            if self._toggle_close_allowed(app_name):
                proc_names = self._proc_names_for_app(app_name, cmd)
                running = self._find_processes_by_names(proc_names)
                if running:
                    terminated, killed = self._close_processes(running)
                    total = terminated + killed
                    return CommandResult(True, f"{app_name} is already open - closed {total} process(es).", f"close_app:{app_name}")

            if self._platform == "Windows":
                if os.path.isfile(cmd):
                    os.startfile(cmd)
                else:
                    subprocess.Popen('start "" "' + cmd + '"', shell=True)
            elif self._platform == "Darwin":
                subprocess.Popen(cmd, shell=True)
            else:
                subprocess.Popen(cmd.split(), shell=True)
            return CommandResult(True, f"Opening {app_name}.", f"open_app:{app_name}")
        except Exception as e:
            return CommandResult(False, f"Could not open {app_name}: {e}", f"open_app:{app_name}")

    def _close_app(self, text: str) -> CommandResult:
        app_name = self._extract_app_name(text).lower()
        if not app_name:
            return CommandResult(False, "Which app to close?", "close_app")

        # Alias common website terms to browser processes
        if app_name in ["youtube", "google", "browser", "internet"]:
            app_name = "chrome"

        killed_pids = []
        killed = 0
        CRITICAL_KEYWORDS = {'system idle process', 'system', 'registry', 'smss', 'csrss', 'winlogon', 'lsass'}
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                if any(crit in proc_name for crit in CRITICAL_KEYWORDS):
                    continue
                # Normalize app_name for better matching
                norm_app = re.sub(r'\\s+', ' ', app_name).strip()
                match_ratio = difflib.SequenceMatcher(None, norm_app, proc_name).ratio()
                if match_ratio > 0.5 or norm_app in proc_name or proc_name in norm_app:
                    proc.kill()
                    killed_pids.append(proc.info['pid'])
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        if killed:
            s = 'es' if killed > 1 else ''
            pids_str = ', '.join(map(str, killed_pids))
            return CommandResult(True, f"Closed {killed} {app_name} process{s} (PIDs: {pids_str}).", "close_app")
        return CommandResult(False, f"No matching {app_name} processes found. Try 'list tasks'.", "close_app")

    def _close_all_apps(self) -> CommandResult:
        apps_to_close = [
            "chrome.exe", "firefox.exe", "msedge.exe", "notepad.exe", "calc.exe", 
            "code.exe", "taskmgr.exe", "winword.exe", "excel.exe", "mspaint.exe", 
            "vlc.exe", "spotify.exe", "discord.exe", "slack.exe"
        ]
        killed = 0
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                proc_name = proc.info['name'].lower()
                if proc_name in apps_to_close:
                    proc.kill()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        if killed > 0:
            return CommandResult(True, f"Closed {killed} applications.", "close_all_apps")
        return CommandResult(False, "No recognizable applications were open.", "close_all_apps")

    def _open_generic_app(self, text: str) -> CommandResult:
        app_name = self._extract_app_name(text)
        if not app_name:
            return CommandResult(False, "Which application should I open?", "open_app")
        try:
            # Smart toggle: if process name matches, close it instead of opening again
            if self._toggle_close_allowed(app_name):
                proc_names = self._proc_names_for_app(app_name, app_name)
                running = self._find_processes_by_names(proc_names)
                if running:
                    terminated, killed = self._close_processes(running)
                    total = terminated + killed
                    return CommandResult(True, f"{app_name} is already open - closed {total} process(es).", f"close_app:{app_name}")

            if self._platform == "Windows":
                subprocess.Popen(app_name, shell=True)
            elif self._platform == "Darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([app_name])
            return CommandResult(True, f"Attempting to open {app_name}.", f"open_app:{app_name}")
        except Exception as e:
            return CommandResult(False, f"Could not launch {app_name}: {e}", f"open_app:{app_name}")

    def _list_tasks(self) -> CommandResult:
        """
        List running processes (top N by memory) in a human-friendly way.
        This is a safe, read-only command.
        """
        try:
            items = []
            for p in psutil.process_iter(["pid", "name", "memory_info"]):
                try:
                    name = p.info.get("name") or ""
                    mem = getattr(p.info.get("memory_info"), "rss", 0) or 0
                    if name:
                        items.append((mem, name, p.info.get("pid")))
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            items.sort(reverse=True, key=lambda t: t[0])
            top = items[:12]
            if not top:
                return CommandResult(True, "No running tasks found.", "list_tasks")

            def fmt_bytes(n: int) -> str:
                for unit in ["B", "KB", "MB", "GB", "TB"]:
                    if n < 1024:
                        return f"{n:.0f}{unit}"
                    n /= 1024
                return f"{n:.0f}PB"

            lines = [f"- {name} (PID {pid}, {fmt_bytes(mem)})" for mem, name, pid in top]
            msg = "Here are some running tasks (top by memory):\n" + "\n".join(lines)
            return CommandResult(True, msg, "list_tasks")
        except Exception as e:
            return CommandResult(False, f"Could not list tasks: {e}", "list_tasks")

    def _get_cpu(self) -> CommandResult:
        info = self.sys_info.get_cpu()
        return CommandResult(True, info, "cpu_info")

    def _get_memory(self) -> CommandResult:
        info = self.sys_info.get_memory()
        return CommandResult(True, info, "memory_info")

    def _get_battery(self) -> CommandResult:
        info = self.sys_info.get_battery()
        return CommandResult(True, info, "battery_info")

    def _get_disk(self) -> CommandResult:
        info = self.sys_info.get_disk()
        return CommandResult(True, info, "disk_info")

    def _get_system_info(self) -> CommandResult:
        info = self.sys_info.get_all()
        return CommandResult(True, info, "system_info")

    def _get_ip(self) -> CommandResult:
        info = self.sys_info.get_ip()
        return CommandResult(True, info, "ip_info")

    def _shutdown(self) -> CommandResult:
        if config.CONFIRM_DANGEROUS_COMMANDS:
            if self.on_confirm and not self.on_confirm("Are you sure you want to shut down?"):
                return CommandResult(False, "Shutdown cancelled.", "shutdown")
        self.sys_ctrl.shutdown()
        return CommandResult(True, "Shutting down. Goodbye!", "shutdown")

    def _restart(self) -> CommandResult:
        if config.CONFIRM_DANGEROUS_COMMANDS:
            if self.on_confirm and not self.on_confirm("Are you sure you want to restart?"):
                return CommandResult(False, "Restart cancelled.", "restart")
        self.sys_ctrl.restart()
        return CommandResult(True, "Restarting the computer.", "restart")

    def _sleep(self) -> CommandResult:
        self.sys_ctrl.sleep()
        return CommandResult(True, "Putting the computer to sleep.", "sleep")

    def _lock_screen(self) -> CommandResult:
        self.sys_ctrl.lock_screen()
        return CommandResult(True, "Locking the screen.", "lock_screen")

    def _screenshot(self) -> CommandResult:
        path = self.sys_ctrl.screenshot()
        if path:
            return CommandResult(True, f"Screenshot saved to {path}", "screenshot")
        return CommandResult(False, "Could not take screenshot.", "screenshot")

    def _volume(self, action: str) -> CommandResult:
        self.sys_ctrl.volume_control(action)
        actions = {"up": "Increasing volume.", "down": "Decreasing volume.", "mute": "Muting audio."}
        return CommandResult(True, actions.get(action, "Volume adjusted."), f"volume_{action}")

    def _brightness(self, action: str) -> CommandResult:
        self.sys_ctrl.brightness_control(action)
        actions = {"up": "Increasing brightness.", "down": "Decreasing brightness."}
        return CommandResult(True, actions.get(action, "Brightness adjusted."), f"brightness_{action}")

    def _help(self) -> CommandResult:
        msg = (
            "I can help you with: opening/closing apps (calculator, notepad, chrome, file, terminal, camera), "
            "websites (youtube, google), system info (cpu, memory), controls (shutdown, lock, volume), "
            "task management (list tasks), time/jokes/help. Tip: saying 'open <app>' will close it if it's already open."
        )
        return CommandResult(True, msg, "help")

    def _greet(self) -> CommandResult:
        import datetime
        hour = datetime.datetime.now().hour
        if hour < 12:
            greeting = "Good morning!"
        elif hour < 17:
            greeting = "Good afternoon!"
        else:
            greeting = "Good evening!"
        return CommandResult(True, f"{greeting} I'm ARIA, your AI assistant. How can I help?", "greet")

    def _tell_time(self) -> CommandResult:
        import datetime
        now = datetime.datetime.now().strftime("%I:%M %p")
        return CommandResult(True, f"The current time is {now}.", "time")

    def _tell_date(self) -> CommandResult:
        import datetime
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        return CommandResult(True, f"Today is {today}.", "date")

    def _tell_joke(self) -> CommandResult:
        joke = JOKES[self._joke_index % len(JOKES)]
        self._joke_index += 1
        return CommandResult(True, joke, "joke")

