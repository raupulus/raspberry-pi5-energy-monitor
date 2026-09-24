# Dominio: Energía (`docs/apis/api-v2/energy.md`)

Este documento destila las operaciones del dominio `/energy` en la API V2 para la subida y consulta de telemetría de energía.

---

## 1. Endpoints Disponibles

| Método | Ruta | Ability Requerida | Propósito |
| :--- | :--- | :--- | :--- |
| `POST` | `/energy/readings` | `energy:write` | Subir una muestra de telemetría (admite cargas multicanal y bloque `hardware_device_info`). |
| `GET` | `/energy/readings` | `energy:read` | Consultar histórico de lecturas con filtros y paginación. |

---

## 2. Subida de Telemetría: `POST /energy/readings`

- **Rate Limit**: Política `api-store` (máximo 60 peticiones/minuto por token).
- **Respuesta de éxito**: `201 Created`.

### 2.1. Estructura del Cuerpo (JSON)

| Campo | Tipo | Requerido | Descripción |
| :--- | :--- | :--- | :--- |
| `hardware_device_id` | `int` | **Sí** | ID del dispositivo en la API (debe pertenecer al usuario del token). |
| `duration` | `int` | Recomendado ($\ge 1$) | Segundos reales del intervalo de muestreo promediado (clave para el cálculo de Wh: $\text{Wh} = V \cdot A \cdot \text{duration} / 3600$). |
| `read_at` | `string` | Opcional | Timestamp ISO-8601 en UTC (`YYYY-MM-DDTHH:MM:SSZ`). Si se omite, el servidor asigna el momento de recepción. |
| `energy` | `object` | **Sí** | Bloque de subsistemas energéticos. Debe contener al menos uno (`generator`, `battery` o `loads`). |
| `energy.loads` | `array` | Opcional | Lista de consumos, uno por canal (`sensor_position`). |
| `hardware_device_info` | `object` | Opcional | Bloque de estado de salud del dispositivo (alias `device`). |

*(Nota: `duration` y `read_at` se admiten en la raíz del payload o dentro del objeto `energy`)*.

### 2.2. Campos Aceptados en Cada Elemento de `loads[]`

| Campo | Tipo | Descripción |
| :--- | :--- | :--- |
| `channel` | `int` ($\ge 0$) | Canal del sensor (alias `sensor_position`). Por defecto 0. |
| `voltage` | `float` | Tensión medida del elemento en voltios ($V$). |
| `amperage` | `float` | Corriente medida en amperios ($A$). Debe ser positiva en cargas. |
| `power` | `float` | Potencia en vatios ($W$). Si se omite, el servidor calcula $V \cdot A$. |
| `temperature` | `float` | Temperatura en grados Celsius (°C). |
| `fan` | `int` ($\ge 0$) | Estado o velocidad del ventilador. |

### 2.3. Bloque Opcional de Salud (`hardware_device_info`)
Permite adjuntar la telemetría del sistema en la misma llamada:
- `temp`, `cpu`, `ram`, `disk`, `voltage`, `uptime`, `ip_local`, `extra`.
- `ip_public` no se envía (lo resuelve el servidor).

### 2.4. Resolución de Magnitudes en el Servidor
1. **Potencia ($W$)**: Toma `power` si se manda; si no, calcula $V \cdot A$.
2. **Vatios-hora ($\text{Wh}$)**: Si no se manda `energy_wh`, calcula $A \cdot V \cdot \text{duration} / 3600$ o $P \cdot \text{duration} / 3600$.
3. **Amperios-hora ($\text{Ah}$)**: Si no se manda `energy_ah`, calcula $A \cdot \text{duration} / 3600$.
4. **Tensión**: Si se manda `voltage`, se almacena con origen `sources.voltage: measured`; si no, usa la nominal configurada en el backend (`sources.voltage: nominal`).

---

## 3. Formato del Payload para Monitor Multicanal (Raspberry Pi 5)

Ejemplo con los dos canales activos desacoplados (Canal 0 = Raspberry Pi 5 base neta, Canal 1 = Hailo-8 M.2 en PCIe):

```json
{
  "hardware_device_id": 7,
  "duration": 300,
  "read_at": "2026-09-14T06:30:00Z",
  "energy": {
    "loads": [
      {
        "channel": 0,
        "voltage": 5.08,
        "amperage": 0.441,
        "power": 2.24,
        "temperature": 48.2
      },
      {
        "channel": 1,
        "voltage": 3.30,
        "amperage": 0.152,
        "power": 0.50,
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

*(Nota: De acuerdo con la decisión técnica DT-011, Canal 0 descuenta el consumo estimado del Canal 1 (`P_rpi = P_total_pmic - P_hailo`). Esto permite que la API mantenga las dos entidades individuales sin duplicar la energía del sistema en el acumulador global).*

---

## 4. Respuestas y Códigos HTTP

### Éxito `201 Created`
```json
{
  "success": true,
  "message": "Telemetría de energía almacenada correctamente.",
  "data": [
    {
      "id": 1025,
      "hardware_device_id": 7,
      "hardware_energy_id": 10,
      "role": "load",
      "measured": {
        "amperage": 0.54,
        "voltage": 5.08,
        "power": 2.74,
        "delta_seconds": 300,
        "temperature": 48.2
      },
      "derived": {
        "energy_wh": 0.2283,
        "energy_ah": 0.045
      },
      "sources": {
        "energy": "derived",
        "voltage": "measured"
      },
      "is_suspicious": false,
      "suspicious_reason": null,
      "created_at": "2026-09-14T06:30:00.000000Z"
    }
  ],
  "warnings": [
    "Opcional: avisos no bloqueantes del servidor"
  ]
}
```

### Códigos de Error
- `401 Unauthorized`: Token ausente o no válido.
- `403 Forbidden`: Token sin la ability `energy:write`.
- `422 Unprocessable Content`: Falla de validación en `energy`, dispositivo inexistente o no perteneciente al usuario del token.
- `429 Too Many Requests`: Excedido el límite de 60 peticiones/min.

---
> Creado: 2026-09-14 · Última revisión: 2026-09-24
