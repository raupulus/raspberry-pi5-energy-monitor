# Dominio: Hardware (`docs/apis/api-v2/hardware.md`)

Este documento destila las operaciones del dominio `/hardware` en la API V2 para la consulta y actualización de dispositivos y su estado de salud.

---

## 1. Endpoints Disponibles

| Método | Ruta | Ability Requerida | Propósito |
| :--- | :--- | :--- | :--- |
| `GET` | `/hardware/devices` | `hardware:read` | Listar dispositivos del usuario autenticado con filtros y paginación. |
| `GET` | `/hardware/devices/{device}` | `hardware:read` | Obtener detalle de un dispositivo (soporta `?include=status`). |
| `PUT` | `/hardware/devices/{device}/status` | `hardware:write` | Sobrescribir el último estado de salud conocido del dispositivo. |

---

## 2. Endpoints de Consulta

### 2.1. `GET /hardware/devices`
- **Filtros aceptados**:
  - `type`: Slugs de `hardware_types` (p. ej. `micro-pc`, `monitor-de-energia`).
  - `name`, `created_at`, `last_seen_at`: Igualdad, listas o rangos (`gte`, `lte`, `gt`, `lt`, `ne`).
  - `from`, `to`: Alias de rango sobre `created_at`.
  - `sort`: `name`, `created_at`, `last_seen_at` (prefijo `-` para descendente).
  - `page` (int, default 1), `per_page` (int, default 25, máx 100).
- **Respuesta 200**: Array paginado de objetos `HardwareDeviceResource`.

### 2.2. `GET /hardware/devices/{device}`
- **Parámetro opcional**: `?include=status` (agrega el objeto de salud `status` a la respuesta).
- **Respuesta 200**: Objeto `HardwareDeviceResource` individual. Si se solicita `include=status`, incluye las métricas actuales del dispositivo.

---

## 3. Endpoint de Estado: `PUT /hardware/devices/{device}/status`

Sobrescribe el último estado conocido del dispositivo de forma idempotente.

### 3.1. Estructura del Payload (Request Body)
Los campos pueden enviarse sueltos en la raíz del JSON o agrupados bajo el objeto `hardware_device_info` (para envíos conjuntos con otros dominios):

| Campo | Tipo | Requerido | Restricciones / Reglas |
| :--- | :--- | :--- | :--- |
| `temp` | `float` \| `null` | No | Temperatura en grados Celsius (°C). |
| `voltage` | `float` \| `null` | No | Voltaje de alimentación en voltios (V). |
| `battery_level` | `int` \| `null` | No | Porcentaje entero de 0 a 100. |
| `cpu` | `float` \| `null` | No | Porcentaje de uso de CPU de 0 a 100. |
| `disk` | `float` \| `null` | No | Porcentaje de uso de disco de 0 a 100. |
| `ram` | `float` \| `null` | No | Porcentaje de uso de memoria RAM de 0 a 100. |
| `uptime` | `int` \| `null` | No | Segundos de actividad continuada ($\ge 0$). |
| `ip_local` | `string` \| `null` | No | Dirección IPv4/IPv6 de la interfaz de red local. |
| `extra` | `dict` \| `null` | No | Diccionario plano, máx. 30 claves, valores simples (texto $\le 255$ caracteres). |

> **Aviso de campo excluido**: `ip_public` no debe enviarse; el servidor lo calcula y descarta cualquier valor enviado por el cliente.
> **Aviso de ID**: `hardware_device_id` no se incluye en el cuerpo de la petición.

### 3.2. Payload de Ejemplo

```json
{
  "temp": 42.5,
  "voltage": 5.08,
  "cpu": 14.2,
  "ram": 38.4,
  "disk": 22.1,
  "uptime": 12450,
  "ip_local": "192.168.1.150",
  "extra": {
    "hailo8_temp": 46.0,
    "throttle_state": "0x0"
  }
}
```

O agrupado en `hardware_device_info`:

```json
{
  "hardware_device_info": {
    "temp": 42.5,
    "voltage": 5.08,
    "cpu": 14.2,
    "ram": 38.4,
    "disk": 22.1,
    "uptime": 12450,
    "ip_local": "192.168.1.150",
    "extra": {
      "hailo8_temp": 46.0
    }
  }
}
```

### 3.3. Respuesta Exitosa 200

```json
{
  "success": true,
  "message": "Estado del dispositivo actualizado",
  "data": {
    "hardware_device_id": 7,
    "temp": 42.5,
    "voltage": 5.08,
    "battery_level": null,
    "cpu": 14.2,
    "disk": 22.1,
    "ram": 38.4,
    "uptime": 12450,
    "ip_local": "192.168.1.150",
    "extra": {
      "hailo8_temp": 46.0
    },
    "last_seen_at": "2026-09-13T19:35:00.000000Z"
  }
}
```

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13
