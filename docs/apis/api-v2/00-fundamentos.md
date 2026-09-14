# Fundamentos de API V2 (00-fundamentos.md)

Este documento detalla las convenciones globales aplicables a todos los módulos y endpoints de la API V2.

---

## 1. Convenciones Globales

- **Base URL**: `/api/v2`
- **Formato de Petición / Respuesta**: `application/json`.
- **Estructura del Envoltorio (Envelope)**:
  - Todas las respuestas siguen la estructura estándar de `ApiResponseTrait`:

```json
// Éxito (HTTP 200 / 201)
{
  "success": true,
  "message": "Operación exitosa",
  "data": { ... }
}

// Error (HTTP 4xx / 5xx)
{
  "success": false,
  "message": "Descripción del error",
  "errors": {
    "campo": ["detalle"]
  }
}
```

- **Respuestas 204 (No Content)**: No contienen cuerpo de respuesta.
- **Colecciones Paginadas**: Incluyen adicionalmente el bloque `meta`:
  ```json
  "meta": {
    "total": 3,
    "per_page": 25,
    "current_page": 1,
    "last_page": 1,
    "from": 1,
    "to": 3
  }
  ```

---

## 2. Autenticación y Autorización (Laravel Sanctum)

- **Cabecera HTTP requerida**: `Authorization: Bearer <token>`
- **Abilities del token**:
  - `hardware:read`: Permite consultar el inventario de dispositivos (`GET /hardware/devices*`).
  - `hardware:write`: Permite actualizar el estado de salud del dispositivo (`PUT /hardware/devices/{device}/status`).
  - `device:{id}`: Restringe el alcance del token exclusivamente al dispositivo especificado por `{id}`.
- **Rutas Inexistentes**:
  Cualquier método o ruta no implementada responde con `404` y cuerpo:
  ```json
  { "success": false, "message": "API V2 - Endpoint no encontrado" }
  ```
  *(No se emiten respuestas 405 Method Not Allowed; el contrato es el par exacto método + ruta).*

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13
