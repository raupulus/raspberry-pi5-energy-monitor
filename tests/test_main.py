"""Pruebas unitarias para el orquestador principal (main.py)."""

import unittest
from unittest.mock import patch
from src.main import EnergyMonitorDaemon, load_config


class TestMainOrchestrator(unittest.TestCase):
    """Pruebas para el ciclo del demonio y carga de configuración."""

    def test_load_config_defaults(self) -> None:
        """Verifica que load_config retorna un diccionario con claves requeridas."""
        config = load_config()
        self.assertIn("API_BASE_URL", config)
        self.assertIn("API_AUTH_TOKEN", config)
        self.assertIn("HARDWARE_DEVICE_ID", config)
        self.assertIn("SAMPLING_INTERVAL_SECONDS", config)
        self.assertIn("REPORT_INTERVAL_SECONDS", config)
        self.assertIn("ENABLE_HAILO8", config)

    def test_daemon_run_once_dry_run_mock(self) -> None:
        """Verifica que el ciclo completo con --once, --dry-run y --mock se ejecuta sin error."""
        config = {
            "API_BASE_URL": "https://fake-api.local/api/v2",
            "API_AUTH_TOKEN": "token_abc",
            "HARDWARE_DEVICE_ID": 7,
            "SAMPLING_INTERVAL_SECONDS": 0.01,
            "REPORT_INTERVAL_SECONDS": 0.01,
            "ENABLE_HAILO8": True,
        }

        daemon = EnergyMonitorDaemon(config=config, force_mock=True)
        # Ejecutar 1 pasada en dry-run
        daemon.run(once=True, dry_run=True)

        # El buffer se procesa y se vacía
        self.assertEqual(daemon.aggregator.sample_count, 0)

    def test_daemon_signal_handling(self) -> None:
        """Comprueba que la captura de señales detiene el bucle."""
        config = load_config()
        daemon = EnergyMonitorDaemon(config=config, force_mock=True)
        self.assertTrue(daemon.running)
        daemon.handle_signal(2, None)  # SIGINT = 2
        self.assertFalse(daemon.running)


if __name__ == "__main__":
    unittest.main()
