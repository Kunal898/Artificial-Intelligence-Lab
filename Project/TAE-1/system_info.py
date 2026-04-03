"""
modules/system_info.py
Retrieves system metrics using psutil.
"""

import platform
import socket

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class SystemInfo:
    """Provides human-readable system information strings."""

    def get_cpu(self) -> str:
        if not PSUTIL_AVAILABLE:
            return "psutil is not installed. Run: pip install psutil"
        usage = psutil.cpu_percent(interval=1)
        freq = psutil.cpu_freq()
        freq_str = f" at {freq.current:.0f} MHz" if freq else ""
        cores = psutil.cpu_count(logical=False)
        return f"CPU usage is {usage}%{freq_str} with {cores} physical cores."

    def get_memory(self) -> str:
        if not PSUTIL_AVAILABLE:
            return "psutil is not installed."
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024 ** 3)
        used_gb = mem.used / (1024 ** 3)
        return (
            f"Memory usage is {mem.percent}%. "
            f"Using {used_gb:.1f} GB of {total_gb:.1f} GB total RAM."
        )

    def get_battery(self) -> str:
        if not PSUTIL_AVAILABLE:
            return "psutil is not installed."
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return "No battery detected. This appears to be a desktop computer."
            status = "charging" if battery.power_plugged else "discharging"
            time_left = ""
            if battery.secsleft > 0 and not battery.power_plugged:
                mins = battery.secsleft // 60
                hours = mins // 60
                mins = mins % 60
                time_left = f" About {hours} hours and {mins} minutes remaining."
            return f"Battery is at {battery.percent:.0f}% and {status}.{time_left}"
        except Exception as e:
            return f"Could not read battery info: {e}"

    def get_disk(self) -> str:
        if not PSUTIL_AVAILABLE:
            return "psutil is not installed."
        disk = psutil.disk_usage("/")
        total_gb = disk.total / (1024 ** 3)
        used_gb = disk.used / (1024 ** 3)
        free_gb = disk.free / (1024 ** 3)
        return (
            f"Disk usage is {disk.percent}%. "
            f"{used_gb:.1f} GB used of {total_gb:.1f} GB. "
            f"{free_gb:.1f} GB free."
        )

    def get_ip(self) -> str:
        try:
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return f"Your local IP address is {local_ip} on host {hostname}."
        except Exception:
            return "Could not determine IP address."

    def get_all(self) -> str:
        system = platform.system()
        node = platform.node()
        release = platform.release()
        machine = platform.machine()
        python_ver = platform.python_version()

        info = (
            f"System: {system} {release} on {machine}. "
            f"Hostname: {node}. "
            f"Python version: {python_ver}."
        )
        if PSUTIL_AVAILABLE:
            cpu = psutil.cpu_percent(interval=0.5)
            mem = psutil.virtual_memory()
            info += f" CPU at {cpu}%, RAM at {mem.percent}%."
        return info
