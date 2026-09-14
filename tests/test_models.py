"""Pruebas unitarias para los modelos de datos y serialización de payloads."""

import unittest
from src.models import EnergyPayload, LoadReading, PmicReading, RailMeasurement, SystemHealth


class TestModels(unittest.TestCase):
    """Verifica la integridad de las dataclasses y el formateo JSON de la API."""

    def test_load_reading_to_dict(self) -> None:
        """Comprueba que LoadReading serializa los campos con el redondeo esperado."""
        load = LoadReading(
            channel=0,
            voltage=5.05716,
            amperage=0.54321,
            power=2.74712,
            temperature=48.24,
            fan=2,
        )
        data = load.to_dict()
        self.assertEqual(data["channel"], 0)
        self.assertEqual(data["voltage"], 5.057)
        self.assertEqual(data["amperage"], 0.543)
        self.assertEqual(data["power"], 2.747)
        self.assertEqual(data["temperature"], 48.24)
        self.assertEqual(data["fan"], 2)

    def test_load_reading_without_fan(self) -> None:
        """Verifica que el campo fan se omite si es None."""
        load = LoadReading(
            channel=1,
            voltage=3.3,
            amperage=0.1,
            power=0.33,
            temperature=36.5,
            fan=None,
        )
        data = load.to_dict()
        self.assertNotIn("fan", data)

    def test_energy_payload_to_api_dict(self) -> None:
        """Verifica la envoltura final del payload para POST /energy/readings."""
        loads = [
            LoadReading(channel=0, voltage=5.08, amperage=0.5, power=2.54, temperature=45.0, fan=1),
            LoadReading(channel=1, voltage=3.30, amperage=0.2, power=0.66, temperature=36.8),
        ]
        device_info = {
            "cpu": 12.0,
            "ram": 35.0,
            "disk": 22.0,
            "temp": 45.0,
            "voltage": 5.08,
            "uptime": 1000,
            "ip_local": "192.168.1.121",
            "extra": {"throttle_state": "0x0"},
        }
        payload = EnergyPayload(
            hardware_device_id=7,
            duration=300,
            read_at="2026-09-14T07:00:00Z",
            loads=loads,
            device_info=device_info,
        )
        api_dict = payload.to_api_dict()

        self.assertEqual(api_dict["hardware_device_id"], 7)
        self.assertEqual(api_dict["duration"], 300)
        self.assertEqual(api_dict["read_at"], "2026-09-14T07:00:00Z")
        self.assertIn("energy", api_dict)
        self.assertEqual(len(api_dict["energy"]["loads"]), 2)
        self.assertIn("hardware_device_info", api_dict)
        self.assertEqual(api_dict["hardware_device_info"]["cpu"], 12.0)


if __name__ == "__main__":
    unittest.main()
