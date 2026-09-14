"""Colector de energía y raíles del PMIC Renesas DA9091 para Raspberry Pi 5."""

import re
import shutil
import subprocess
import time
from src.collectors.base import BaseCollector
from src.models import PmicReading, RailMeasurement

# Salida de ejemplo real verificada en hardware físico para pruebas y mock fallback
MOCK_PMIC_OUTPUT: str = """
 3V7_WL_SW_A current(0)=0.10247270A
   3V3_SYS_A current(1)=0.10832820A
   1V8_SYS_A current(2)=0.15712470A
  DDR_VDD2_A current(3)=0.00585558A
  DDR_VDDQ_A current(4)=0.00000000A
   1V1_SYS_A current(5)=0.24105470A
    0V8_SW_A current(6)=0.31424950A
  VDD_CORE_A current(7)=1.42880000A
   3V3_DAC_A current(17)=0.00000000A
   3V3_ADC_A current(18)=0.00006105A
   0V8_AON_A current(16)=0.00354090A
      HDMI_A current(22)=0.02002440A
 3V7_WL_SW_V volt(8)=3.71091200V
   3V3_SYS_V volt(9)=3.30910500V
   1V8_SYS_V volt(10)=1.80073100V
  DDR_VDD2_V volt(11)=1.10439400V
  DDR_VDDQ_V volt(12)=0.60439500V
   1V1_SYS_V volt(13)=1.10805800V
    0V8_SW_V volt(14)=0.80402850V
  VDD_CORE_V volt(15)=0.90659250V
   3V3_DAC_V volt(20)=3.31135200V
   3V3_ADC_V volt(21)=3.31867800V
   0V8_AON_V volt(19)=0.79882700V
      HDMI_V volt(23)=5.07860000V
     EXT5V_V volt(24)=5.05716000V
      BATT_V volt(25)=0.00000000V
"""


class PmicCollector(BaseCollector[PmicReading]):
    """Recolecta métricas analógicas del ADC del PMIC DA9091."""

    def __init__(self, force_mock: bool = False) -> None:
        self._force_mock: bool = force_mock
        self._has_vcgencmd: bool = bool(shutil.which("vcgencmd")) and not force_mock

    def collect(self) -> PmicReading | None:
        """Obtiene una lectura instantánea de los raíles y potencias."""
        raw_text = self._read_raw_adc()
        if not raw_text:
            return None
        return self.parse_raw_adc(raw_text)

    def _read_raw_adc(self) -> str:
        """Ejecuta el comando de firmware o devuelve el mock si no está disponible."""
        if self._has_vcgencmd:
            try:
                proc = subprocess.run(
                    ["vcgencmd", "pmic_read_adc"],
                    capture_output=True,
                    text=True,
                    timeout=2.0,
                    check=False,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    return proc.stdout
            except (subprocess.SubprocessError, OSError):
                pass
        return MOCK_PMIC_OUTPUT

    @staticmethod
    def parse_raw_adc(raw_text: str) -> PmicReading:
        """Parsea la salida textual de vcgencmd pmic_read_adc y calcula magnitudes."""
        currents: dict[str, float] = {
            match[0]: float(match[1])
            for match in re.findall(r"(\S+)_A\s+current\(\d+\)=([\d\.]+)A", raw_text)
        }
        volts: dict[str, float] = {
            match[0]: float(match[1])
            for match in re.findall(r"(\S+)_V\s+volt\(\d+\)=([\d\.]+)V", raw_text)
        }

        ext5v_v = volts.get("EXT5V", 5.0)
        rails: dict[str, RailMeasurement] = {}
        total_power_w = 0.0

        for rail, curr_a in currents.items():
            volt_v = volts.get(rail, 0.0)
            power_w = volt_v * curr_a
            total_power_w += power_w
            rails[rail] = RailMeasurement(
                name=rail,
                volts=round(volt_v, 4),
                current_a=round(curr_a, 4),
                power_w=round(power_w, 4),
            )

        estimated_current_ma = (
            (total_power_w / ext5v_v * 1000.0) if ext5v_v > 0.0 else 0.0
        )
        cpu_gpu_power_w = rails.get("VDD_CORE").power_w if "VDD_CORE" in rails else 0.0

        return PmicReading(
            input_voltage_v=round(ext5v_v, 4),
            total_power_w=round(total_power_w, 4),
            estimated_current_ma=round(estimated_current_ma, 2),
            cpu_gpu_power_w=round(cpu_gpu_power_w, 4),
            rails=rails,
            timestamp=time.time(),
        )
