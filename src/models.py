"""Modelos de datos fuertemente tipados para el monitor de energía de Raspberry Pi 5."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RailMeasurement:
    """Medición instantánea de un raíl del PMIC DA9091."""

    name: str
    volts: float
    current_a: float
    power_w: float


@dataclass(frozen=True)
class PmicReading:
    """Conjunto de lecturas de los 12 raíles del PMIC DA9091 y magnitudes globales."""

    input_voltage_v: float
    total_power_w: float
    estimated_current_ma: float
    cpu_gpu_power_w: float
    rails: dict[str, RailMeasurement]
    timestamp: float


@dataclass(frozen=True)
class SystemHealth:
    """Métricas de salud, rendimiento y sensores térmicos del sistema."""

    cpu_pct: float
    ram_pct: float
    disk_pct: float
    temp_soc_c: float
    temp_rp1_c: float | None
    fan_rpm: int | None
    fan_state: int | None
    throttle_hex: str
    uptime_s: int
    ip_local: str | None
    timestamp: float


@dataclass(frozen=True)
class HailoHealth:
    """Telemetría del acelerador de inferencia Hailo-8 M.2."""

    temp_ts0_c: float
    temp_ts1_c: float
    avg_temp_c: float
    is_throttling: bool
    estimated_power_w: float
    timestamp: float


@dataclass(frozen=True)
class LoadReading:
    """Lectura de consumo para un canal específico (loads[] en API V2)."""

    channel: int
    voltage: float
    amperage: float
    power: float
    temperature: float
    fan: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serializa a diccionario JSON para la API."""
        data: dict[str, Any] = {
            "channel": self.channel,
            "voltage": round(self.voltage, 3),
            "amperage": round(self.amperage, 3),
            "power": round(self.power, 3),
            "temperature": round(self.temperature, 2),
        }
        if self.fan is not None:
            data["fan"] = self.fan
        return data


@dataclass(frozen=True)
class EnergyPayload:
    """Payload completo formateado según el contrato API V2 de energía."""

    hardware_device_id: int
    duration: int
    read_at: str
    loads: list[LoadReading]
    device_info: dict[str, Any] = field(default_factory=dict)

    def to_api_dict(self) -> dict[str, Any]:
        """Genera el JSON final para POST /api/v2/energy/readings."""
        payload: dict[str, Any] = {
            "hardware_device_id": self.hardware_device_id,
            "duration": self.duration,
            "read_at": self.read_at,
            "energy": {
                "loads": [load.to_dict() for load in self.loads],
            },
        }
        if self.device_info:
            payload["hardware_device_info"] = self.device_info
        return payload
