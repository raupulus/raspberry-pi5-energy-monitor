"""Pruebas unitarias para el colector del PMIC DA9091."""

import unittest
from src.collectors.pmic import MOCK_PMIC_OUTPUT, PmicCollector


class TestPmicCollector(unittest.TestCase):
    """Verifica el parseo de ADC del PMIC y las fórmulas de potencia."""

    def test_parse_real_hardware_output(self) -> None:
        """Comprueba el parseo de la salida real capturada del firmware de la Pi 5."""
        reading = PmicCollector.parse_raw_adc(MOCK_PMIC_OUTPUT)

        self.assertIsNotNone(reading)
        self.assertAlmostEqual(reading.input_voltage_v, 5.0572, places=3)
        self.assertGreater(reading.total_power_w, 2.0)
        self.assertLess(reading.total_power_w, 4.0)
        self.assertGreater(reading.estimated_current_ma, 400.0)
        self.assertLess(reading.estimated_current_ma, 700.0)

        # Raíles clave
        self.assertIn("VDD_CORE", reading.rails)
        self.assertIn("3V3_SYS", reading.rails)
        self.assertIn("1V8_SYS", reading.rails)

        vdd_core = reading.rails["VDD_CORE"]
        self.assertAlmostEqual(vdd_core.volts, 0.9066, places=3)
        self.assertAlmostEqual(vdd_core.current_a, 1.4288, places=3)
        self.assertAlmostEqual(vdd_core.power_w, vdd_core.volts * vdd_core.current_a, places=3)

    def test_collector_mock_mode(self) -> None:
        """Verifica que el colector en modo forzado genera lecturas coherentes."""
        collector = PmicCollector(force_mock=True)
        reading = collector.collect()

        self.assertIsNotNone(reading)
        self.assertEqual(reading.input_voltage_v, 5.0572)
        self.assertIn("3V3_SYS", reading.rails)


if __name__ == "__main__":
    unittest.main()
