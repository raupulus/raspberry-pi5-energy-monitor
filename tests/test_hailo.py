"""Pruebas unitarias para el colector de telemetría de Hailo-8."""

import unittest
from src.collectors.hailo import HailoCollector
from src.models import PmicReading, RailMeasurement


class TestHailoCollector(unittest.TestCase):
    """Conjunto de pruebas para HailoCollector."""

    def test_hailo_disabled_returns_none(self) -> None:
        """Verifica que si Hailo-8 está desactivado, collect() retorna None."""
        collector = HailoCollector(enabled=False, force_mock=True)
        result = collector.collect()
        self.assertIsNone(result)

    def test_hailo_mock_returns_health_metrics(self) -> None:
        """Verifica que en modo simulado devuelva métricas con temperaturas esperadas."""
        collector = HailoCollector(enabled=True, force_mock=True)
        result = collector.collect()
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.temp_ts0_c, 36.8)
        self.assertEqual(result.temp_ts1_c, 36.2)
        self.assertEqual(result.avg_temp_c, 36.5)
        self.assertFalse(result.is_throttling)
        self.assertGreaterEqual(result.estimated_power_w, 0.5)

    def test_estimate_power_with_pmic_rails(self) -> None:
        """Comprueba el cálculo de potencia estimada basado en 3V3_SYS y 1V8_SYS."""
        rails = {
            "3V3_SYS": RailMeasurement("3V3_SYS", 3.3, 0.1, 0.33),
            "1V8_SYS": RailMeasurement("1V8_SYS", 1.8, 0.2, 0.36),
        }
        pmic = PmicReading(
            input_voltage_v=5.1,
            total_power_w=3.5,
            estimated_current_ma=686.0,
            cpu_gpu_power_w=1.2,
            rails=rails,
            timestamp=1000.0,
        )

        collector = HailoCollector(enabled=True, force_mock=True)
        result = collector.collect(pmic=pmic)
        self.assertIsNotNone(result)
        assert result is not None
        # 0.33 + 0.36 = 0.69 W
        self.assertAlmostEqual(result.estimated_power_w, 0.69, places=2)

    def test_hailo_exception_fallback(self) -> None:
        """Comprueba que si ocurre una excepción en la lectura del hardware retorna None."""
        collector = HailoCollector(enabled=True, force_mock=False)

        class CrashingDevice:
            def __enter__(self):
                raise RuntimeError("PCIe communication error")

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        collector._device_cls = CrashingDevice
        result = collector.collect()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
