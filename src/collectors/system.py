"""Colector de salud del sistema, métricas de rendimiento y sensores térmicos."""

import os
import re
import socket
import subprocess
import time
from src.collectors.base import BaseCollector
from src.models import SystemHealth


class SystemCollector(BaseCollector[SystemHealth]):
    """Recolecta telemetría de CPU, RAM, disco, temperaturas, ventilador y red."""

    def __init__(self, force_mock: bool = False) -> None:
        self._force_mock: bool = force_mock
        self._prev_cpu_total: int | None = None
        self._prev_cpu_idle: int | None = None

    def collect(self) -> SystemHealth:
        """Obtiene una instantánea completa de la salud del sistema."""
        if self._force_mock or not os.path.exists("/proc/stat"):
            return self._mock_health()

        cpu_pct = self._read_cpu_usage()
        ram_pct = self._read_ram_usage()
        disk_pct = self._read_disk_usage()
        temp_soc_c = self._read_soc_temp()
        temp_rp1_c = self._read_rp1_temp()
        fan_rpm = self._read_fan_rpm()
        fan_state = self._read_fan_state()
        throttle_hex = self._read_throttle_state()
        uptime_s = self._read_uptime()
        ip_local = self._read_local_ip()

        return SystemHealth(
            cpu_pct=round(cpu_pct, 1),
            ram_pct=round(ram_pct, 1),
            disk_pct=round(disk_pct, 1),
            temp_soc_c=round(temp_soc_c, 1),
            temp_rp1_c=round(temp_rp1_c, 1) if temp_rp1_c is not None else None,
            fan_rpm=fan_rpm,
            fan_state=fan_state,
            throttle_hex=throttle_hex,
            uptime_s=uptime_s,
            ip_local=ip_local,
            timestamp=time.time(),
        )

    def _read_cpu_usage(self) -> float:
        """Calcula el porcentaje de CPU evaluando la delta de /proc/stat."""
        try:
            with open("/proc/stat", "r", encoding="utf-8") as f:
                fields = [int(x) for x in f.readline().split()[1:]]
            idle = fields[3] + fields[4]
            total = sum(fields)

            if self._prev_cpu_total is None or self._prev_cpu_idle is None:
                self._prev_cpu_total = total
                self._prev_cpu_idle = idle
                time.sleep(0.05)
                return self._read_cpu_usage()

            delta_total = total - self._prev_cpu_total
            delta_idle = idle - self._prev_cpu_idle
            self._prev_cpu_total = total
            self._prev_cpu_idle = idle

            if delta_total <= 0:
                return 0.0
            usage = 100.0 * (1.0 - (delta_idle / delta_total))
            return max(0.0, min(100.0, usage))
        except (OSError, ValueError, IndexError):
            return 5.0

    @staticmethod
    def _read_ram_usage() -> float:
        """Calcula el porcentaje de RAM ocupada desde /proc/meminfo."""
        try:
            total_kb = 0
            avail_kb = 0
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        total_kb = int(line.split()[1])
                    elif line.startswith("MemAvailable:"):
                        avail_kb = int(line.split()[1])
            if total_kb > 0:
                used_kb = total_kb - avail_kb
                return (used_kb / total_kb) * 100.0
        except (OSError, ValueError, IndexError):
            pass
        return 35.0

    @staticmethod
    def _read_disk_usage() -> float:
        """Calcula el porcentaje de uso de la partición raíz /."""
        try:
            stat = os.statvfs("/")
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            if total > 0:
                return ((total - free) / total) * 100.0
        except OSError:
            pass
        return 20.0

    @staticmethod
    def _read_soc_temp() -> float:
        """Lee la temperatura del SoC Cortex-A76 desde sysfs o vcgencmd."""
        for path in (
            "/sys/class/thermal/thermal_zone0/temp",
            "/sys/class/hwmon/hwmon0/temp1_input",
        ):
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return float(f.read().strip()) / 1000.0
                except (OSError, ValueError):
                    pass
        # Fallback a vcgencmd measure_temp
        try:
            proc = subprocess.run(
                ["vcgencmd", "measure_temp"],
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
            match = re.search(r"temp=([\d\.]+)", proc.stdout)
            if match:
                return float(match.group(1))
        except (subprocess.SubprocessError, OSError):
            pass
        return 45.0

    @staticmethod
    def _read_rp1_temp() -> float | None:
        """Lee la temperatura del Southbridge RP1 desde sysfs."""
        path = "/sys/class/hwmon/hwmon1/temp1_input"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return float(f.read().strip()) / 1000.0
            except (OSError, ValueError):
                pass
        return None

    @staticmethod
    def _read_fan_rpm() -> int | None:
        """Lee la velocidad de giro en RPM del ventilador pwmfan."""
        candidate_paths = [
            "/sys/devices/platform/cooling_fan/hwmon/hwmon2/fan1_input",
            "/sys/class/hwmon/hwmon2/fan1_input",
        ]
        for path in candidate_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        return int(f.read().strip())
                except (OSError, ValueError):
                    pass
        return None

    @staticmethod
    def _read_fan_state() -> int | None:
        """Lee el estado térmico de enfriamiento del ventilador (0 a 4)."""
        path = "/sys/class/thermal/cooling_device0/cur_state"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return int(f.read().strip())
            except (OSError, ValueError):
                pass
        return None

    @staticmethod
    def _read_throttle_state() -> str:
        """Obtiene la máscara de bits de vcgencmd get_throttled."""
        try:
            proc = subprocess.run(
                ["vcgencmd", "get_throttled"],
                capture_output=True,
                text=True,
                timeout=1.0,
                check=False,
            )
            match = re.search(r"throttled=(0x[0-9a-fA-F]+)", proc.stdout)
            if match:
                return match.group(1)
        except (subprocess.SubprocessError, OSError):
            pass
        return "0x0"

    @staticmethod
    def _read_uptime() -> int:
        """Lee los segundos acumulados de uptime del sistema."""
        try:
            with open("/proc/uptime", "r", encoding="utf-8") as f:
                return int(float(f.readline().split()[0]))
        except (OSError, ValueError, IndexError):
            return 86400

    @staticmethod
    def _read_local_ip() -> str | None:
        """Detecta la IP local de salida mediante conexión UDP rápida."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.settimeout(0.5)
                s.connect(("1.1.1.1", 80))
                return str(s.getsockname()[0])
        except OSError:
            return None

    @staticmethod
    def _mock_health() -> SystemHealth:
        """Genera datos de prueba coherentes para entornos sin Linux/sysfs."""
        return SystemHealth(
            cpu_pct=12.4,
            ram_pct=38.2,
            disk_pct=22.5,
            temp_soc_c=47.5,
            temp_rp1_c=44.1,
            fan_rpm=3750,
            fan_state=1,
            throttle_hex="0x0",
            uptime_s=12400,
            ip_local="192.168.1.121",
            timestamp=time.time(),
        )
