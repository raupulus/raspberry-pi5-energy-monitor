"""Pruebas unitarias para el agregador de telemetría en memoria (TelemetryAggregator)."""

import unittest
from src.buffer.aggregator import TelemetryAggregator
from src.models import HailoHealth, PmicReading, RailMeasurement, SystemHealth


class TestTelemetryAggregator(unittest.TestCase):
    """Pruebas para el búfer y agregador de métricas en RAM."""

    def setUp(self) -> None:
        self.device_id = 7
        self.report_interval = 300.0
        self.aggregator = TelemetryAggregator(
            hardware_device_id=self.device_id,
            report_interval_seconds=self.report_interval,
        )

        self.mock_pmic = PmicReading(
            input_voltage_v=5.10,
            total_power_w=3.50,
            estimated_current_ma=686.0,
            cpu_gpu_power_w=1.20,
            rails={
                "EXT5V_V": RailMeasurement("EXT5V_V", 5.10, 0.686, 3.50),
                "3V3_SYS": RailMeasurement("3V3_SYS", 3.30, 0.100, 0.33),
            },
            timestamp=100.0,
        )

        self.mock_system = SystemHealth(
            cpu_pct=15.0,
            ram_pct=28.5,
            disk_pct=42.0,
            temp_soc_c=45.0,
            temp_rp1_c=48.0,
            fan_rpm=3800,
            fan_state=1,
            throttle_hex="0x0",
            uptime_s=3600,
            ip_local="192.168.1.100",
            timestamp=100.0,
        )

        self.mock_hailo = HailoHealth(
            temp_ts0_c=38.0,
            temp_ts1_c=37.0,
            avg_temp_c=37.5,
            is_throttling=False,
            estimated_power_w=0.85,
            timestamp=100.0,
        )

    def test_empty_buffer_flush_raises(self) -> None:
        """Verifica que flush() en un búfer vacío lance ValueError."""
        with self.assertRaises(ValueError):
            self.aggregator.flush()

    def test_should_report_logic(self) -> None:
        """Verifica la lógica temporal para determinar el momento de reporte."""
        self.assertFalse(self.aggregator.should_report(now=100.0))

        # Añadir muestra en t=100
        self.aggregator.add_sample(self.mock_pmic, self.mock_system, timestamp=100.0)

        # Si no ha pasado el intervalo
        self.assertFalse(self.aggregator.should_report(now=self.aggregator._window_start_time + 200.0))

        # Si ha pasado el intervalo
        self.assertTrue(self.aggregator.should_report(now=self.aggregator._window_start_time + 301.0))

    def test_flush_without_hailo(self) -> None:
        """Verifica agregación cuando Hailo-8 no está presente (Canal 1 omitido)."""
        self.aggregator._window_start_time = 100.0
        self.aggregator.add_sample(self.mock_pmic, self.mock_system, hailo=None, timestamp=100.0)
        self.aggregator.add_sample(self.mock_pmic, self.mock_system, hailo=None, timestamp=200.0)

        self.assertEqual(self.aggregator.sample_count, 2)
        payload = self.aggregator.flush(now=200.0)

        self.assertEqual(self.aggregator.sample_count, 0)
        self.assertEqual(payload.hardware_device_id, self.device_id)
        self.assertEqual(len(payload.loads), 1)
        self.assertEqual(payload.loads[0].channel, 0)
        self.assertEqual(payload.loads[0].fan, 1)
        self.assertAlmostEqual(payload.loads[0].voltage, 5.10, places=2)
        self.assertAlmostEqual(payload.loads[0].power, 3.50, places=2)
        self.assertEqual(payload.duration, 100)

        # Verificar device_info
        info = payload.device_info
        self.assertEqual(info["cpu"], 15.0)
        self.assertEqual(info["ram"], 28.5)
        self.assertEqual(info["disk"], 42.0)
        self.assertEqual(info["uptime"], 3600)
        self.assertEqual(info["ip_local"], "192.168.1.100")
        self.assertNotIn("hailo8_temp", info["extra"])
        self.assertEqual(info["extra"]["rp1_temp"], 48.0)
        self.assertEqual(info["extra"]["fan_rpm"], 3800)

    def test_flush_with_hailo_two_channels_no_duplication(self) -> None:
        """Verifica que se envían Canal 0 (RPi neta) y Canal 1 (Hailo-8) sumando el total exacto."""
        self.aggregator._window_start_time = 100.0
        self.aggregator.add_sample(
            self.mock_pmic, self.mock_system, hailo=self.mock_hailo, timestamp=100.0
        )

        payload = self.aggregator.flush(now=100.0)

        # Se envían dos canales
        self.assertEqual(len(payload.loads), 2)
        channel_0 = payload.loads[0]
        channel_1 = payload.loads[1]

        self.assertEqual(channel_0.channel, 0)
        self.assertEqual(channel_1.channel, 1)

        # Canal 1: Hailo-8 estimado a 0.85 W
        self.assertAlmostEqual(channel_1.power, 0.85, places=2)
        self.assertEqual(channel_1.voltage, 3.30)
        self.assertAlmostEqual(channel_1.temperature, 37.5, places=2)

        # Canal 0: Raspberry Pi neta = 3.50 W - 0.85 W = 2.65 W
        self.assertAlmostEqual(channel_0.power, 2.65, places=2)
        self.assertEqual(channel_0.voltage, 5.10)

        # La suma exacta de ambos canales es la potencia total del PMIC (3.50 W)
        self.assertAlmostEqual(channel_0.power + channel_1.power, 3.50, places=2)

        # device_info.extra.hailo8_temp también se incluye
        self.assertIn("hailo8_temp", payload.device_info["extra"])
        self.assertEqual(payload.device_info["extra"]["hailo8_temp"], 37.5)

    def test_duration_flush_at_305s_from_previous_window(self) -> None:
        """Verifica que muestras cada 10 s y flush a los 305 s computan duration=305."""
        self.aggregator._window_start_time = 1000.0
        for t in range(1000, 1301, 10):
            self.aggregator.add_sample(self.mock_pmic, self.mock_system, timestamp=float(t))

        payload = self.aggregator.flush(now=1305.0)
        self.assertEqual(payload.duration, 305)
        self.assertEqual(self.aggregator._window_start_time, 1305.0)

    def test_first_window_duration_from_startup(self) -> None:
        """Verifica que la primera ventana tras arrancar computa la duración exacta desde el arranque."""
        agg = TelemetryAggregator(hardware_device_id=self.device_id, report_interval_seconds=300.0)
        startup_time = agg._window_start_time
        now = startup_time + 45.0
        agg.add_sample(self.mock_pmic, self.mock_system, timestamp=now)

        payload = agg.flush(now=now)
        self.assertEqual(payload.duration, 45)


if __name__ == "__main__":
    unittest.main()
