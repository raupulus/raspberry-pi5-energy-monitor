"""Cliente HTTP para transmisión de telemetría hacia API V2."""

import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any
from src.models import EnergyPayload

logger = logging.getLogger("energy_monitor.api")


class EnergyApiClient:
    """Cliente HTTP para el envío del contrato universal de energía a API V2."""

    def __init__(
        self,
        base_url: str,
        auth_token: str,
        timeout_seconds: float = 10.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url: str = base_url.rstrip("/")
        self.auth_token: str = auth_token
        self.timeout_seconds: float = timeout_seconds
        self.max_retries: int = max_retries

    def send_energy_readings(
        self, payload: EnergyPayload
    ) -> tuple[bool, dict[str, Any] | str]:
        """Envía el payload de energía a POST /energy/readings con reintentos."""
        endpoint = f"{self.base_url}/energy/readings"
        data_dict = payload.to_api_dict()
        data_bytes = json.dumps(data_dict).encode("utf-8")

        headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "RPi5-Energy-Monitor/1.0",
        }

        req = urllib.request.Request(
            endpoint, data=data_bytes, headers=headers, method="POST"
        )

        last_error = ""
        for attempt in range(1, self.max_retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    resp_bytes = resp.read()
                    status_code = resp.status
                    resp_json = json.loads(resp_bytes.decode("utf-8"))

                    if status_code == 201 and resp_json.get("success"):
                        warnings = resp_json.get("warnings")
                        if warnings:
                            logger.warning(
                                "API V2 warnings recibidos: %s", warnings
                            )
                        logger.info(
                            "Telemetría enviada con éxito (201 Created). Message: %s",
                            resp_json.get("message"),
                        )
                        return True, resp_json

                    return False, resp_json

            except urllib.error.HTTPError as e:
                error_body = ""
                try:
                    error_body = e.read().decode("utf-8")
                    error_json = json.loads(error_body)
                    error_msg = error_json.get("message", error_body)
                except Exception:
                    error_msg = error_body or str(e)

                logger.error(
                    "HTTP %d en intento %d/%d: %s",
                    e.code,
                    attempt,
                    self.max_retries,
                    error_msg,
                )

                # Errores 4xx (excepto 429) no se reintentan
                if 400 <= e.code < 500 and e.code != 429:
                    return False, f"HTTP {e.code}: {error_msg}"

                last_error = f"HTTP {e.code}: {error_msg}"

            except (urllib.error.URLError, TimeoutError, OSError) as e:
                logger.warning(
                    "Fallo de conexión en intento %d/%d: %s",
                    attempt,
                    self.max_retries,
                    e,
                )
                last_error = str(e)

            if attempt < self.max_retries:
                sleep_time = 2.0**attempt
                time.sleep(sleep_time)

        return False, last_error
