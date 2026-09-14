# Limitaciones y Restricciones de API V2 (LIMITACIONES.md)

Este documento detalla las restricciones duras, límites de tasa y particularidades de los endpoints de la API V2.

---

## 1. Límites de Frecuencia (Rate Limiting)

- **Política `api-store`**: Máximo **60 peticiones por minuto** por token de autenticación.
- **Respuesta al exceder el límite**: Código HTTP `429 Too Many Requests`.
- **Efecto en la RPi 5**: La frecuencia de reporte de estado no debe superar 1 petición por segundo en ráfagas, y debe promediar intervalos regulares de al menos 1 segundo (o sincronizarse con el reporte de energía para evitar saturar el límite).

---

## 2. Restricciones de Payload y Validación

### 2.1. Supresión de `ip_public` (Cambio 2026-09-06)
- El dispositivo **no debe enviar `ip_public`**. Si se envía en el body, el servidor lo ignora silenciosamente.
- El servidor calcula la IP pública automáticamente inspeccionando cabeceras de proxy (`CF-Connecting-IP`, `True-Client-IP`, `X-Forwarded-For`, `X-Real-IP`).
- El cliente debe enviar únicamente `ip_local` con la dirección IP válida de la interfaz de red local.

### 2.2. Exclusión de `hardware_device_id` en el Cuerpo
- El identificador del dispositivo **no se acepta en el body**. Se lee exclusivamente del segmento de ruta `{device}` en la URL (`PUT /hardware/devices/{device}/status`).
- Si se envía dentro de `hardware_device_info`, es ignorado por la lista blanca de campos de estado.

### 2.3. Restricciones del campo `extra`
- Tipo: Objeto JSON plano (`dict`).
- Máximo de claves: **30 claves**.
- Tipo de valores: Datos primitivos simples únicamente (`number`, `string`, `boolean`).
- Longitud máxima de texto: **255 caracteres** por valor.
- Prohibido: No admite arrays ni objetos anidados.

### 2.4. Rangos de Métricas Porcentuales (0 - 100)
- `cpu`, `disk`, `ram`: Valores numéricos de 0 a 100 (o `null`).
- `battery_level`: Entero de 0 a 100 (o `null`).
- `uptime`: Entero mayor o igual a 0 segundos (o `null`).

---

## 3. Comportamiento de Actualización (Idempotencia)

- `PUT /hardware/devices/{device}/status` actualiza el último estado conocido.
- **Actualización no destructiva**: Solo se sobrescriben las claves presentes en el payload. Los campos omitidos conservan el valor previamente almacenado en el servidor.
- `last_seen_at` se actualiza de forma automática en el servidor en cada petición.

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13
