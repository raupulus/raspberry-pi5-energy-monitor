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
- [docs/apis/api-v2/energy.md](../../apis/api-v2/energy.md)

---

## 2. Estrategia de Envío de Telemetría

El cliente implementará el **Modo Conjunto Universal** como mecanismo principal:
- Envío continuo cada `REPORT_INTERVAL_SECONDS` (por defecto 300 s / 5 min) mediante:
  `POST /api/v2/energy/readings`
- Agrupa en una sola transacción HTTP:
  1. **Consumos por canal** (`energy.loads`):
     - **Canal 0 (Raspberry Pi 5 base)**: Potencia, voltaje, corriente y temperatura promediados.
     - **Canal 1 (Hailo-8 M.2)**: Potencia y temperatura del acelerador. **Si `ENABLE_HAILO8 = False`, este canal se omite por completo del array**.
  2. **Salud del nodo** (`hardware_device_info`): CPU, RAM, disco, temperatura, voltaje, IP local y extras (throttling, temperaturas multizona).
  3. **Metadatos de ventana**: `duration` (segundos reales transcurridos para cálculo exacto de Wh en el backend) y `read_at` (timestamp UTC ISO-8601).

---

## 3. Estructura Exacta del Payload Generado

```json
{
  "hardware_device_id": 7,
  "duration": 300,
  "read_at": "2026-09-14T06:35:00Z",
  "energy": {
    "loads": [
      {
        "channel": 0,
        "voltage": 5.08,
        "amperage": 0.54,
        "power": 2.74,
        "temperature": 48.2
      },
      {
        "channel": 1,
        "voltage": 3.30,
        "amperage": 0.35,
        "power": 1.15,
        "temperature": 41.0
      }
    ]
  },
  "hardware_device_info": {
    "cpu": 8.5,
    "ram": 36.2,
    "disk": 24.1,
    "temp": 48.2,
    "voltage": 5.08,
    "uptime": 86400,
    "ip_local": "192.168.1.150",
    "extra": {
      "throttle_state": "0x0",
      "hailo8_temp": 41.0
    }
  }
}
```

---

## 4. Mapeo de Métricas del Hardware (RPi 5)

| Campo API | Fuente en Raspberry Pi 5 | Estado |
| :--- | :--- | :--- |
| `temp` | `/sys/class/thermal/thermal_zone0/temp` (dividido entre 1000) | ⚠️ Sin verificar |
| `voltage` | Lectura PMIC DA9091 (rail de entrada `EXT5V` o 5V) | ⚠️ Sin verificar |
| `battery_level` | `null` (alimentación por red eléctrica habitual) | ⚠️ Sin verificar |
| `cpu` | Cálculo de porcentaje de uso de CPU (`/proc/stat` o `psutil`) | ⚠️ Sin verificar |
| `disk` | Porcentaje de uso del sistema de ficheros raíz `/` | ⚠️ Sin verificar |
| `ram` | Porcentaje de uso de memoria RAM (`/proc/meminfo`) | ⚠️ Sin verificar |
| `uptime` | Segundos desde arranque (`/proc/uptime`) | ⚠️ Sin verificar |
| `ip_local` | Detección de IP en interfaz activa (`eth0` / `wlan0`) | ⚠️ Sin verificar |
| `extra` | Diccionario con estado del acelerador Hailo-8 (`hailo8_temp`), estado de estrangulamiento (`throttle_state`) | ⚠️ Sin verificar |

---

## 5. Configuración Asociada

Variables gestionadas en `src/env.py`:
- `API_BASE_URL`: URL base del servidor (ej. `https://api.tu-servidor.com/api/v2`).
- `API_AUTH_TOKEN`: Token de autenticación Sanctum con ability `energy:write` (y `hardware:write`).
- `HARDWARE_DEVICE_ID`: ID numérico del dispositivo en el backend.
- `SAMPLING_INTERVAL_SECONDS`: Intervalo en segundos entre muestras raw (ej. 5.0 a 10.0 s).
- `REPORT_INTERVAL_SECONDS`: Duración en segundos de la ventana de agregación (ej. 300.0 s = 5 min).
- `ENABLE_HAILO8`: Booleano para activar o desactivar la monitorización y canal de Hailo-8.

---
> Creado: 2026-09-13 · Última revisión: 2026-09-14

