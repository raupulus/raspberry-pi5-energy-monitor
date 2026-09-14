"""Colector de telemetría y sensores térmicos para el acelerador NPU Hailo-8 M.2."""

import time
from typing import Any
from src.collectors.base import BaseCollector
from src.models import HailoHealth, PmicReading


class HailoCollector(BaseCollector[HailoHealth]):
    """Recolecta métricas del acelerador Hailo-8 M.2 mediante el SDK oficial."""

    def __init__(self, enabled: bool = False, force_mock: bool = False) -> None:
        self._enabled: bool = enabled
        self._force_mock: bool = force_mock
        self._device_cls: Any = None

        if self._enabled and not self._force_mock:
            self._init_hailo_driver()

    def _init_hailo_driver(self) -> None:
        """Carga perezosa del SDK oficial hailo_platform."""
        try:
            from hailo_platform import Device  # type: ignore

            self._device_cls = Device
        except ImportError:
            self._device_cls = None

    def collect(self, pmic: PmicReading | None = None) -> HailoHealth | None:
        """Lee temperaturas internas TS0/TS1 y estima la potencia consumida.

        Retorna None si el módulo está desactivado o no disponible.
        """
        if not self._enabled:
            return None

        if self._force_mock or (self._device_cls is None):
            return self._mock_hailo(pmic)

        try:
            with self._device_cls() as target:
                t = target.control.get_chip_temperature()
                ts0 = float(t.ts0_temperature)
                ts1 = float(t.ts1_temperature)
                throttling = bool(target.control.get_throttling_state())

            avg_temp = (ts0 + ts1) / 2.0
            power_w = self._estimate_power(pmic)

            return HailoHealth(
                temp_ts0_c=round(ts0, 2),
                temp_ts1_c=round(ts1, 2),
                avg_temp_c=round(avg_temp, 2),
                is_throttling=throttling,
                estimated_power_w=round(power_w, 3),
                timestamp=time.time(),
            )
        except Exception:
            return None

    @staticmethod
    def _estimate_power(pmic: PmicReading | None) -> float:
        """Estima la potencia disipada en los raíles 3V3_SYS y 1V8_SYS."""
        if not pmic:
            return 0.55

        power_3v3 = (
            pmic.rails["3V3_SYS"].power_w if "3V3_SYS" in pmic.rails else 0.24
        )
        power_1v8 = (
            pmic.rails["1V8_SYS"].power_w if "1V8_SYS" in pmic.rails else 0.31
        )
        # La potencia de los buses 3.3V y 1.8V alimenta el socket PCIe M.2 y lógica
        return max(0.50, power_3v3 + power_1v8)

    def _mock_hailo(self, pmic: PmicReading | None) -> HailoHealth:
        """Genera telemetría simulada para pruebas."""
        power_w = self._estimate_power(pmic)
        return HailoHealth(
            temp_ts0_c=36.8,
            temp_ts1_c=36.2,
            avg_temp_c=36.5,
            is_throttling=False,
            estimated_power_w=round(power_w, 3),
            timestamp=time.time(),
        )
