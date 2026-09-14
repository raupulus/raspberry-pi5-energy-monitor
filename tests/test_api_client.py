"""Pruebas unitarias para el cliente HTTP de la API V2 (EnergyApiClient)."""

import io
import json
import unittest
import urllib.error
from unittest.mock import MagicMock, patch
from src.api.client import EnergyApiClient
from src.models import EnergyPayload, LoadReading


class TestEnergyApiClient(unittest.TestCase):
    """Pruebas para EnergyApiClient."""

    def setUp(self) -> None:
        self.base_url = "https://mock-api.local/api/v2"
        self.token = "test_bearer_token_12345"
        self.client = EnergyApiClient(
            base_url=self.base_url,
            auth_token=self.token,
            timeout_seconds=2.0,
            max_retries=2,
        )

        self.payload = EnergyPayload(
            hardware_device_id=7,
            duration=300,
            read_at="2026-09-14T08:00:00Z",
            loads=[
                LoadReading(
                    channel=0,
                    voltage=5.12,
                    amperage=0.85,
                    power=4.35,
                    temperature=42.5,
                    fan=1,
                )
            ],
            device_info={"temp": 42.5, "cpu": 12.0},
        )

    @patch("urllib.request.urlopen")
    def test_send_success_201(self, mock_urlopen: MagicMock) -> None:
        """Verifica el envío exitoso con respuesta 201 Created."""
        mock_response = MagicMock()
        mock_response.status = 201
        resp_data = {
            "success": True,
            "message": "Lectura registrada correctamente",
            "warnings": ["Warning simulado"],
            "data": {"id": 999},
        }
        mock_response.read.return_value = json.dumps(resp_data).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        success, result = self.client.send_energy_readings(self.payload)

        self.assertTrue(success)
        self.assertIsInstance(result, dict)
        assert isinstance(result, dict)
        self.assertEqual(result["message"], "Lectura registrada correctamente")
        self.assertIn("warnings", result)

        # Verificar headers y endpoint
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        self.assertEqual(req.full_url, "https://mock-api.local/api/v2/energy/readings")
        self.assertEqual(req.headers["Authorization"], f"Bearer {self.token}")
        self.assertEqual(req.headers["Content-type"], "application/json")

    @patch("urllib.request.urlopen")
    def test_client_error_4xx_no_retry(self, mock_urlopen: MagicMock) -> None:
        """Verifica que errores 4xx (como 422 Unprocessable) no se reintenten."""
        fp = io.BytesIO(json.dumps({"message": "Validación fallida"}).encode("utf-8"))
        http_err = urllib.error.HTTPError(
            url="https://mock-api.local/api/v2/energy/readings",
            code=422,
            msg="Unprocessable Entity",
            hdrs={},  # type: ignore
            fp=fp,
        )
        mock_urlopen.side_effect = http_err

        success, result = self.client.send_energy_readings(self.payload)

        self.assertFalse(success)
        self.assertIn("HTTP 422: Validación fallida", result)
        # Solo debe intentarlo 1 vez sin reintentos
        self.assertEqual(mock_urlopen.call_count, 1)

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_server_error_500_retries_and_fails(
        self, mock_urlopen: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Verifica que un error 500 se reintenta hasta agotar max_retries."""
        def create_http_error(*args, **kwargs):
            fp = io.BytesIO(b'{"message": "Internal Server Error"}')
            raise urllib.error.HTTPError(
                url="https://mock-api.local/api/v2/energy/readings",
                code=500,
                msg="Server Error",
                hdrs={},  # type: ignore
                fp=fp,
            )

        mock_urlopen.side_effect = create_http_error

        success, result = self.client.send_energy_readings(self.payload)

        self.assertFalse(success)
        self.assertIn("HTTP 500: Internal Server Error", result)
        self.assertEqual(mock_urlopen.call_count, 2)
        mock_sleep.assert_called_once()

    @patch("time.sleep")
    @patch("urllib.request.urlopen")
    def test_network_urlerror_retries(
        self, mock_urlopen: MagicMock, mock_sleep: MagicMock
    ) -> None:
        """Verifica el reintento ante URLError (caída de conexión de red)."""
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        success, result = self.client.send_energy_readings(self.payload)

        self.assertFalse(success)
        self.assertIn("Connection refused", result)
        self.assertEqual(mock_urlopen.call_count, 2)
        mock_sleep.assert_called_once()


if __name__ == "__main__":
    unittest.main()
