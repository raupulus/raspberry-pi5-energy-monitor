# Registro de Erratas e Inconsistencias de API V2 (ERRATAS.md)

Este documento registra discrepancias, ambigüedades y comportamientos asimétricos detectados en la especificación oficial de la API V2.

---

### ERR-001: Discrepancia en Ability para `PUT /hardware/devices/{device}/status`
- **Ubicación**: Contrato oficial, sección `PUT /hardware/devices/{device}/status`.
- **Descripción**: En la cabecera de autenticación del endpoint se exige `ability:hardware:write`. Sin embargo, en el apartado de errores se indica literalmente:
  > `403 token sin la ability energy:write.`
- **Impacto**: Confusión sobre si el backend valida `hardware:write` o `energy:write`.
- **Mitigación recomendada**: Hasta verificar con petición real (`⚠️ sin verificar`), emitir tokens con ambas abilities (`hardware:write` y `energy:write`), o verificar el middleware exacto en el backend.

---

### ERR-002: Asimetría en el Código HTTP ante Dispositivos Fuera del Token (`device:{id}`)
- **Ubicación**: Reglas de autorización en endpoints de dispositivos.
- **Descripción**: Cuando un token ligado a un dispositivo específico (`device:X`) intenta acceder a un dispositivo diferente (`device:Y`):
  - `GET /hardware/devices/{device}`: Responde con código **`404`** ("Dispositivo no encontrado") para no filtrar la existencia del recurso.
  - `PUT /hardware/devices/{device}/status`: Responde con código **`422`** ("Unprocessable Content"), debido a que la regla `OwnedHardwareDevice` se ejecuta en la capa de validación del `FormRequest`.
- **Impacto**: El cliente no debe asumir un único código HTTP (como 403) para identificar accesos no autorizados por alcance de dispositivo.

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13
