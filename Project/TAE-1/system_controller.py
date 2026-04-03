"""
modules/system_controller.py
Handles OS-level operations: shutdown, restart, sleep, screenshot, volume.
"""

import os
import platform
import subprocess
import datetime


class SystemController:
    """Cross-platform system control operations."""

    def __init__(self):
        self._platform = platform.system()

    def shutdown(self):
        """Initiate system shutdown."""
        cmds = {
            "Windows": "shutdown /s /t 5",
            "Linux":   "shutdown -h now",
            "Darwin":  "sudo shutdown -h now",
        }
        self._run(cmds)

    def restart(self):
        """Initiate system restart."""
        cmds = {
            "Windows": "shutdown /r /t 5",
            "Linux":   "sudo reboot",
            "Darwin":  "sudo shutdown -r now",
        }
        self._run(cmds)

    def sleep(self):
        """Put system into sleep/suspend mode."""
        cmds = {
            "Windows": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0",
            "Linux":   "systemctl suspend",
            "Darwin":  "pmset sleepnow",
        }
        self._run(cmds)

    def lock_screen(self):
        """Lock the user session screen."""
        cmds = {
            "Windows": "rundll32.exe user32.dll,LockWorkStation",
            "Linux":   "gnome-screensaver-command -l",
            "Darwin":  '/System/Library/CoreServices/Menu\\ Extras/User.menu/Contents/Resources/CGSession -suspend',
        }
        self._run(cmds)

    def screenshot(self) -> str:
        """
        Take a screenshot and save it.
        Returns the saved file path, or empty string on failure.
        """
        try:
            import pyautogui
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            save_path = os.path.join(os.path.expanduser("~"), "Pictures", filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            return save_path
        except ImportError:
            # Try platform-native methods
            try:
                if self._platform == "Darwin":
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    path = os.path.expanduser(f"~/Desktop/screenshot_{timestamp}.png")
                    subprocess.run(["screencapture", path])
                    return path
                elif self._platform == "Linux":
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    path = os.path.expanduser(f"~/Desktop/screenshot_{timestamp}.png")
                    subprocess.run(["scrot", path])
                    return path
            except Exception:
                pass
            return ""
        except Exception as e:
            print(f"[Screenshot Error] {e}")
            return ""

    def volume_control(self, action: str):
        """
        Adjust system volume.
        action: "up", "down", or "mute"
        """
        try:
            import pyautogui
            key_map = {
                "up":   "volumeup",
                "down": "volumedown",
                "mute": "volumemute",
            }
            key = key_map.get(action)
            if key:
                pyautogui.press(key)
        except ImportError:
            # Platform fallbacks
            if self._platform == "Linux":
                cmd_map = {
                    "up":   "amixer -D pulse sset Master 10%+",
                    "down": "amixer -D pulse sset Master 10%-",
                    "mute": "amixer -D pulse sset Master toggle",
                }
                cmd = cmd_map.get(action)
                if cmd:
                    subprocess.run(cmd.split())

    def brightness_control(self, action: str):
        """
        Adjust screen brightness.
        action: "up" or "down"
        """
        try:
            import screen_brightness_control as sbc
            if action == "up":
                sbc.set_brightness('+15')
            else:
                sbc.set_brightness('-15')
            return
        except ImportError:
            pass

        if self._platform == "Windows":
            bound_func = "[math]::min(100, $b + 15)" if action == "up" else "[math]::max(0, $b - 15)"
            ps_script = f"$b = (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightness -ErrorAction Stop).CurrentBrightness; $new = {bound_func}; (Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, [byte]$new)"
            subprocess.run(["powershell", "-Command", ps_script], shell=False)
        elif self._platform == "Linux":
            cmd = "xbacklight -inc 15" if action == "up" else "xbacklight -dec 15"
            subprocess.run(cmd.split(), check=False)

    def _run(self, cmd_map: dict):
        """Execute the platform-appropriate command."""
        cmd = cmd_map.get(self._platform)
        if cmd:
            try:
                subprocess.run(cmd, shell=True, check=False)
            except Exception as e:
                print(f"[SystemController Error] {e}")
        else:
            print(f"[SystemController] Platform '{self._platform}' not supported for this action.")
