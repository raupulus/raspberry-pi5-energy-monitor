"""Agregador de telemetría en memoria RAM (Zero-Disk Wear) para Raspberry Pi 5."""

from collections import deque
from datetime import datetime, timezone
import time
from typing import Any
from src.models import EnergyPayload, HailoHealth, LoadReading, PmicReading, SystemHealth


class TelemetryAggregator:
    """Acumula muestras en memoria RAM y genera resúmenes estadísticos para la API."""

    def __init__(
        self,
        hardware_device_id: int,
        report_interval_seconds: float = 300.0,
        max_samples: int = 3600,
    ) -> None:
        self.hardware_device_id: int = hardware_device_id
        self.report_interval_seconds: float = report_interval_seconds
        self._samples: deque[tuple[PmicReading, SystemHealth, HailoHealth | None, float]] = (
            deque(maxlen=max_samples)
        )
        self._window_start_time: float = time.time()

    @property
    def sample_count(self) -> int:
        """Número de muestras actualmente en el búfer."""
        return len(self._samples)

    def add_sample(
        self,
        pmic: PmicReading,
        system: SystemHealth,
        hailo: HailoHealth | None = None,
        timestamp: float | None = None,
    ) -> None:
        """Añade una muestra instantánea al búfer en RAM."""
        ts = timestamp if timestamp is not None else time.time()
        self._samples.append((pmic, system, hailo, ts))

    def should_report(self, now: float | None = None) -> bool:
        """Comprueba si se ha alcanzado la ventana de tiempo para emitir el reporte."""
        if not self._samples:
            return False
        current_time = now if now is not None else time.time()
        return (current_time - self._window_start_time) >= self.report_interval_seconds

    def flush(self, now: float | None = None) -> EnergyPayload:
        """Calcula las medias de la ventana, resetea el búfer y genera el EnergyPayload."""
        if not self._samples:
            raise ValueError("No hay muestras en el agregador para generar payload.")

        current_time = now if now is not None else time.time()
        sample_count = len(self._samples)

        # Magnitud de tiempo: duración real continua desde el inicio de la ventana / reporte anterior
        duration = max(1, int(round(current_time - self._window_start_time)))

        read_at_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Acumuladores de magnitudes del PMIC (alimentación total del nodo)
        sum_v_ext5v = 0.0
        sum_i_ext5v_a = 0.0
        sum_p_total = 0.0
        sum_temp_soc = 0.0
        last_fan_state: int | None = None
        last_fan_rpm: int | None = None

        # Acumuladores de Salud del Sistema
        sum_cpu = 0.0
        sum_ram = 0.0
        last_disk = 0.0
        last_uptime = 0
        last_ip_local: str | None = None
        last_throttle_hex: str = "0x0"
        sum_rp1_temp = 0.0
        rp1_count = 0

        # Acumuladores Canal 1 (Hailo-8 M.2 PCIe)
        hailo_samples_count = 0
        sum_hailo_power = 0.0
        sum_hailo_temp = 0.0

        for pmic, system, hailo, _ in self._samples:
            sum_v_ext5v += pmic.input_voltage_v
            sum_i_ext5v_a += pmic.estimated_current_ma / 1000.0
            sum_p_total += pmic.total_power_w
            sum_temp_soc += system.temp_soc_c

            if system.fan_state is not None:
                last_fan_state = system.fan_state
            if system.fan_rpm is not None:
                last_fan_rpm = system.fan_rpm

            sum_cpu += system.cpu_pct
            sum_ram += system.ram_pct
            last_disk = system.disk_pct
            last_uptime = system.uptime_s
            last_ip_local = system.ip_local
            last_throttle_hex = system.throttle_hex

            if system.temp_rp1_c is not None:
                sum_rp1_temp += system.temp_rp1_c
                rp1_count += 1

            if hailo is not None:
                hailo_samples_count += 1
                sum_hailo_power += hailo.estimated_power_w
                sum_hailo_temp += hailo.avg_temp_c

        # Medias globales
        avg_v = sum_v_ext5v / sample_count
        avg_p_total = sum_p_total / sample_count
        avg_soc_temp = sum_temp_soc / sample_count

        loads: list[LoadReading] = []
        avg_hailo_temp: float | None = None

        if hailo_samples_count > 0:
            # Canal 1 (Hailo-8 M.2): estimación de consumo en PCIe
            avg_hailo_p = sum_hailo_power / hailo_samples_count
            avg_hailo_temp = sum_hailo_temp / hailo_samples_count
            hailo_v = 3.30
            hailo_i = (avg_hailo_p / hailo_v) if hailo_v > 0 else 0.0

            # Canal 0 (Raspberry Pi 5): Consumo neto descontando el Hailo-8 para evitar duplicidad
            rpi_power = max(0.0, avg_p_total - avg_hailo_p)
            rpi_i = (rpi_power / avg_v) if avg_v > 0 else 0.0

            loads.append(
                LoadReading(
                    channel=0,
                    voltage=avg_v,
                    amperage=rpi_i,
                    power=rpi_power,
                    temperature=avg_soc_temp,
                    fan=last_fan_state,
                )
            )
            loads.append(
                LoadReading(
                    channel=1,
                    voltage=hailo_v,
                    amperage=hailo_i,
                    power=avg_hailo_p,
                    temperature=avg_hailo_temp,
                    fan=None,
                )
            )
        else:
            # Sin Hailo-8: Canal 0 absorbe la totalidad de la potencia del PMIC
            avg_i_total = sum_i_ext5v_a / sample_count
            loads.append(
                LoadReading(
                    channel=0,
                    voltage=avg_v,
                    amperage=avg_i_total,
                    power=avg_p_total,
                    temperature=avg_soc_temp,
                    fan=last_fan_state,
                )
            )

        # Construir bloque de salud del dispositivo (hardware_device_info)
        device_extra: dict[str, Any] = {
            "throttle_state": last_throttle_hex,
            "samples_count": sample_count,
        }
        if rp1_count > 0:
            device_extra["rp1_temp"] = round(sum_rp1_temp / rp1_count, 1)
        if last_fan_rpm is not None:
            device_extra["fan_rpm"] = last_fan_rpm
        if avg_hailo_temp is not None:
            device_extra["hailo8_temp"] = round(avg_hailo_temp, 1)

        device_info: dict[str, Any] = {
            "temp": round(avg_soc_temp, 1),
            "voltage": round(avg_v, 2),
            "cpu": round(sum_cpu / sample_count, 1),
            "ram": round(sum_ram / sample_count, 1),
            "disk": round(last_disk, 1),
            "uptime": last_uptime,
            "ip_local": last_ip_local,
            "extra": device_extra,
        }

        # Resetear búfer y tiempo de inicio de ventana
        self._samples.clear()
        self._window_start_time = current_time

        return EnergyPayload(
            hardware_device_id=self.hardware_device_id,
            duration=duration,
            read_at=read_at_iso,
            loads=loads,
            device_info=device_info,
        )
