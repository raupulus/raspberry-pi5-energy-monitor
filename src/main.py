"""Servicio demonio principal de monitorización de energía para Raspberry Pi 5."""

import argparse
import importlib.util
import logging
import os
import signal
import sys
import time
from types import FrameType
from typing import Any
from src.api.client import EnergyApiClient
from src.buffer.aggregator import TelemetryAggregator
from src.collectors.hailo import HailoCollector
from src.collectors.pmic import PmicCollector
from src.collectors.system import SystemCollector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("energy_monitor")


def load_config() -> dict[str, Any]:
    """Carga la configuración desde src/env.py con fallback a src/env.example.py."""
    config_paths = ["src/env.py", "src/env.example.py"]
    for path in config_paths:
        if os.path.exists(path):
            spec = importlib.util.spec_from_file_location("env_module", path)
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return {
                    "API_BASE_URL": getattr(
                        mod, "API_BASE_URL", "https://api.tu-servidor.com/api/v2"
                    ),
                    "API_AUTH_TOKEN": getattr(mod, "API_AUTH_TOKEN", ""),
                    "HARDWARE_DEVICE_ID": getattr(
                        mod, "HARDWARE_DEVICE_ID", 7
                    ),
                    "SAMPLING_INTERVAL_SECONDS": float(
                        getattr(mod, "SAMPLING_INTERVAL_SECONDS", 10.0)
                    ),
                    "REPORT_INTERVAL_SECONDS": float(
                        getattr(mod, "REPORT_INTERVAL_SECONDS", 300.0)
                    ),
                    "ENABLE_HAILO8": bool(getattr(mod, "ENABLE_HAILO8", False)),
                }

    return {
        "API_BASE_URL": "https://api.tu-servidor.com/api/v2",
        "API_AUTH_TOKEN": "",
        "HARDWARE_DEVICE_ID": 7,
        "SAMPLING_INTERVAL_SECONDS": 10.0,
        "REPORT_INTERVAL_SECONDS": 300.0,
        "ENABLE_HAILO8": False,
    }


class EnergyMonitorDaemon:
    """Demonio de monitorización continua de energía y reporte a API V2."""

    def __init__(self, config: dict[str, Any], force_mock: bool = False) -> None:
        self.config = config
        self.running: bool = True

        self.pmic_collector = PmicCollector(force_mock=force_mock)
        self.system_collector = SystemCollector(force_mock=force_mock)
        self.hailo_collector = HailoCollector(
            enabled=config["ENABLE_HAILO8"], force_mock=force_mock
        )

        self.aggregator = TelemetryAggregator(
            hardware_device_id=config["HARDWARE_DEVICE_ID"],
            report_interval_seconds=config["REPORT_INTERVAL_SECONDS"],
        )

        self.api_client = EnergyApiClient(
            base_url=config["API_BASE_URL"],
            auth_token=config["API_AUTH_TOKEN"],
        )

    def handle_signal(self, signum: int, frame: FrameType | None) -> None:
        """Detiene el bucle principal ante señales de terminación."""
        signame = signal.Signals(signum).name
        logger.info("Señal recibida (%s). Finalizando servicio...", signame)
        self.running = False

    def run(self, once: bool = False, dry_run: bool = False) -> None:
        """Ejecuta el ciclo de monitorización continua o una sola pasada."""
        logger.info(
            "Iniciando servicio de monitorización (Dispositivo: %d, Muestreo: %.1fs, Reporte: %.1fs, Hailo-8: %s)",
            self.config["HARDWARE_DEVICE_ID"],
            self.config["SAMPLING_INTERVAL_SECONDS"],
            self.config["REPORT_INTERVAL_SECONDS"],
            "Activo" if self.config["ENABLE_HAILO8"] else "Desactivado",
        )

        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        while self.running:
            start_tick = time.time()

            pmic = self.pmic_collector.collect()
            system = self.system_collector.collect()
            hailo = self.hailo_collector.collect(pmic)

            if pmic and system:
                self.aggregator.add_sample(pmic, system, hailo)
                logger.debug(
                    "Muestra tomada: RPi=%.2fW, Temp=%.1f°C, Muestras en RAM=%d",
                    pmic.total_power_w,
                    system.temp_soc_c,
                    self.aggregator.sample_count,
                )

            if once or self.aggregator.should_report():
                if self.aggregator.sample_count > 0:
                    payload = self.aggregator.flush()
                    logger.info(
                        "Ventana de agregación completada (%d s, %d cargas)",
                        payload.duration,
                        len(payload.loads),
                    )

                    if dry_run:
                        logger.info("Modo dry-run: Payload generado:\n%s", payload.to_api_dict())
                    else:
                        success, resp = self.api_client.send_energy_readings(payload)
                        if not success:
                            logger.error("Error al transmitir telemetría: %s", resp)

                if once:
                    break

            elapsed = time.time() - start_tick
            sleep_time = max(0.1, self.config["SAMPLING_INTERVAL_SECONDS"] - elapsed)
            time.sleep(sleep_time)

        logger.info("Servicio de monitorización detenido.")


def main() -> None:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Raspberry Pi 5 Energy & Consumption Monitor Daemon"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Ejecuta una única lectura y agregación y finaliza",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra el payload generado sin enviar la petición HTTP a la API",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Fuerza el uso de mocks para pruebas fuera de hardware físico",
    )
    args = parser.parse_args()

    config = load_config()
    daemon = EnergyMonitorDaemon(config, force_mock=args.mock)
    daemon.run(once=args.once, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
