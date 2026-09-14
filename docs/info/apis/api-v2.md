# Integración de API V2 (`docs/info/apis/api-v2.md`)

Este documento describe cómo el monitor de Raspberry Pi 5 se integra con el backend **API V2**, enlazando con la documentación oficial destilada sin duplicar sus especificaciones.

---

## 1. Referencia a la Documentación Oficial

La especificación completa del contrato y sus restricciones se encuentra documentada en:
- [docs/apis/api-v2/README.md](../../apis/api-v2/README.md)
- [docs/apis/api-v2/00-fundamentos.md](../../apis/api-v2/00-fundamentos.md)
- [docs/apis/api-v2/ERRATAS.md](../../apis/api-v2/ERRATAS.md)
- [docs/apis/api-v2/LIMITACIONES.md](../../apis/api-v2/LIMITACIONES.md)
- [docs/apis/api-v2/hardware.md](../../apis/api-v2/hardware.md)

---

## 2. Estrategia de Envío de Telemetría

El cliente implementará dos modalidades de transmisión:

1. **Modo Ping / Estado Periódico**:
   - Petición dedicada a `PUT /api/v2/hardware/devices/{device}/status`.
   - Utilizado cuando no hay métricas de consumo energético listas para transmitir o en el arranque del servicio.
2. **Modo Conjunto (Ping embebido en Energía)**:
   - Envío del bloque `hardware_device_info` dentro de la petición universal de energía (`POST /api/v2/energy/readings`).
   - Optimiza recursos de red en la Raspberry Pi 5 al consolidar estado de salud y lecturas de consumo en una sola llamada HTTP.

---

## 3. Mapeo de Métricas del Hardware (RPi 5)

| Campo API | Fuente en Raspberry Pi 5 | Estado |
| :--- | :--- | :--- |
| `temp` | `/sys/class/thermal/thermal_zone0/temp` (dividido entre 1000) | ⚠️ Sin verificar |
| `voltage` | Lectura PMIC DA9091 (rail de 5V) | ⚠️ Sin verificar |
| `battery_level` | `null` (alimentación por red eléctrica habitual) | ⚠️ Sin verificar |
| `cpu` | Cálculo de porcentaje de uso de CPU (`/proc/stat` o `psutil`) | ⚠️ Sin verificar |
| `disk` | Porcentaje de uso del sistema de ficheros raíz `/` | ⚠️ Sin verificar |
| `ram` | Porcentaje de uso de memoria RAM (`/proc/meminfo`) | ⚠️ Sin verificar |
| `uptime` | Segundos desde arranque (`/proc/uptime`) | ⚠️ Sin verificar |
| `ip_local` | Detección de IP en interfaz activa (`eth0` / `wlan0`) | ⚠️ Sin verificar |
| `extra` | Diccionario con estado del acelerador Hailo-8 (`hailo8_temp`), estado de estrangulamiento (`throttle_state`) | ⚠️ Sin verificar |

---

## 4. Configuración Asociada

Variables gestionadas en `src/env.py`:
- `API_BASE_URL`: URL base del servidor (ej. `https://api.tu-servidor.com/api/v2`).
- `API_AUTH_TOKEN`: Token de autenticación Sanctum con abilities requeridas.
- `HARDWARE_DEVICE_ID`: ID numérico del dispositivo en el backend.
- `REPORT_INTERVAL_SECONDS`: Intervalo en segundos entre transmisiones de estado.

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13
