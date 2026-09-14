"""Pruebas unitarias para el colector de métricas del sistema."""

import unittest
from src.collectors.system import SystemCollector


class TestSystemCollector(unittest.TestCase):
    """Verifica la recolección de métricas de CPU, RAM, disco y temperaturas."""

    def test_collect_mock(self) -> None:
        """Verifica que el colector en modo mock devuelve métricas válidas en rango."""
        collector = SystemCollector(force_mock=True)
        health = collector.collect()

        self.assertIsNotNone(health)
        self.assertTrue(0.0 <= health.cpu_pct <= 100.0)
        self.assertTrue(0.0 <= health.ram_pct <= 100.0)
        self.assertTrue(0.0 <= health.disk_pct <= 100.0)
        self.assertGreater(health.temp_soc_c, 20.0)
        self.assertLess(health.temp_soc_c, 90.0)
        self.assertEqual(health.fan_rpm, 3750)
        self.assertEqual(health.fan_state, 1)
        self.assertTrue(health.throttle_hex.startswith("0x"))

    def test_collect_auto(self) -> None:
        """Verifica la ejecución en el entorno actual sin lanzar excepciones."""
        collector = SystemCollector()
        health = collector.collect()

        self.assertIsNotNone(health)
        self.assertTrue(0.0 <= health.cpu_pct <= 100.0)
        self.assertTrue(0.0 <= health.ram_pct <= 100.0)


if __name__ == "__main__":
    unittest.main()
