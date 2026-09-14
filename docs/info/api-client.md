# Módulo: Cliente API V2 (`src/api/client.py`)

> Documentación técnica del cliente HTTP para la transmisión segura y resiliente de telemetría hacia el backend propio API V2.

---

## 1. Qué hace y qué NO hace

### Qué hace
- Construye peticiones HTTP POST hacia el endpoint `{API_BASE_URL}/energy/readings`.
- Serializa el objeto fuertemente tipado `EnergyPayload` al formato JSON exacto esperado por el contrato de la API.
- Aplica autenticación Bearer Token en las cabeceras HTTP (`Authorization: Bearer <token>`).
- Define cabeceras estándar de contenido: `Content-Type: application/json`, `Accept: application/json` y un User-Agent identificativo (`RPi5-Energy-Monitor/1.0`).
- Procesa la respuesta HTTP 201 Created y detecta si el cuerpo contiene advertencias no bloqueantes (`warnings`), emitiendo logs de aviso para inspección.
- Implementa reintentos con retraso exponencial (*exponential backoff*: $2^n$ segundos) ante fallos transitorios de red (`URLError`, timeouts) o respuestas de servidor 5xx y 429 Too Many Requests.
- Descarta reintentos inmediatos ante errores de cliente 4xx definitivos (p. ej. 401 Unauthorized, 403 Forbidden, 422 Unprocessable Entity) para evitar sobrecargar la API.

### Qué NO hace
- No almacena localmente en disco las lecturas fallidas (política Zero-Disk Wear).
- No administra la renovación de tokens ni invoca endpoints de login (el token es un Personal Access Token estático configurado en `src/env.py`).

---

## 2. Modelo de datos

- Consume el modelo `EnergyPayload` (`src/models.py`), invocando su método `payload.to_api_dict()` para generar el esquema JSON.
- Retorna una tupla tipada `tuple[bool, dict[str, Any] | str]` donde el primer elemento indica éxito y el segundo contiene el cuerpo JSON parseado o la cadena descriptiva del error.

---

## 3. Flujos principales

### Flujo de Envío con Reintentos
1. `send_energy_readings(payload)` prepara la URL y serializa el payload a bytes UTF-8.
2. Inicia un bucle de reintento desde `attempt = 1` hasta `max_retries`.
3. Abre la conexión mediante `urllib.request.urlopen` con timeout configurado (`timeout_seconds`).
4. Si la API responde 201 Created y `"success": True`:
   - Comprueba si existe la clave `warnings`. Si existe, emite advertencia de log.
   - Retorna `(True, resp_json)`.
5. Si ocurre `urllib.error.HTTPError`:
   - Extrae el mensaje de error del cuerpo JSON.
   - Si el código está en el rango `[400..499]` (excepto 429), detiene el bucle de reintentos y retorna `(False, "HTTP <code>: <error>")`.
   - Si es 5xx o 429, aplica `time.sleep(2.0 ** attempt)` y reintenta.
6. Si ocurre `urllib.error.URLError` o `TimeoutError`:
   - Registra aviso y duerme con backoff exponencial antes del siguiente intento.
7. Al agotar todos los reintentos sin éxito, retorna `(False, last_error)`.

---

## 4. Puntos de entrada

- `EnergyApiClient(base_url: str, auth_token: str, timeout_seconds: float = 10.0, max_retries: int = 3)`: Constructor.
- `EnergyApiClient.send_energy_readings(payload: EnergyPayload) -> tuple[bool, dict[str, Any] | str]`: Transmisión de payload.

---

## 5. Dependencias

### Dependencias entrantes
- `src/main.py`: Demonio orquestador.
- `tests/test_api_client.py`: Suite de pruebas unitarias.

### Dependencias salientes
- Librería estándar de Python: `json`, `logging`, `time`, `urllib.error`, `urllib.request`.
- `src/models.py`: Modelo `EnergyPayload`.

---

## 6. Configuración

| Parámetro | Valor por defecto | Efecto / Comportamiento |
| :--- | :--- | :--- |
| `base_url` | *(Requerido)* | URL base de la API V2 (p. ej. `https://dominio.com/api/v2`). |
| `auth_token` | *(Requerido)* | Token Bearer Sanctum con ability `energy:write`. |
| `timeout_seconds` | `10.0` | Tiempo límite de espera de respuesta del socket HTTP. |
| `max_retries` | `3` | Número máximo de intentos ante fallos transitorios. |

---

## 7. Trampas conocidas

- **TR-004 (Abilities de autenticación)**: Asegurarse de que el token Sanctum emitido para el monitor contenga tanto la ability `energy:write` como `hardware:write` si en el futuro se reporta el estado del dispositivo por separado.
- El rate limit general del grupo de rutas `api-store` en la API receptora es de 60 peticiones/minuto por token. Dado que este demonio reporta por defecto cada 300 segundos (0.2 peticiones/minuto), se encuentra muy lejos de agotar la cuota disponible.

---

## 8. Tests que lo cubren

- [x] `tests/test_api_client.py::TestEnergyApiClient.test_send_success_201`: Transmisión exitosa con verificación de cabeceras, enrutamiento y captura de warnings.
- [x] `tests/test_api_client.py::TestEnergyApiClient.test_client_error_4xx_no_retry`: Confirmación de corte inmediato ante respuestas 4xx sin reintentos innecesarios.
- [x] `tests/test_api_client.py::TestEnergyApiClient.test_server_error_500_retries_and_fails`: Validación del bucle de reintentos exponenciales ante errores de servidor 500.
- [x] `tests/test_api_client.py::TestEnergyApiClient.test_network_urlerror_retries`: Reintento automático ante cortes de red física o caídas DNS.

---

## 9. Pendiente real

- [ ] Ninguna tarea pendiente en este módulo.

---
> Creado: 2026-09-14 · Última revisión: 2026-09-14
