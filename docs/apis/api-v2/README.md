# API V2 — Documentación de Terceros / Backend Propio

Documentación oficial destilada del backend API V2 consumido por el monitor de energía de Raspberry Pi 5.

---

## Metadatos de la Especificación

- **Fuente**: Especificación técnica proporcionada por el usuario (ver archivo original en [`src/hardware-contract.md`](src/hardware-contract.md)).
- **Fecha de descarga**: 2026-09-13
- **Fecha de verificación real**: `⚠️ sin verificar con petición real` (pendiente de realizar peticiones HTTP de prueba contra un servidor activo).
- **Base URL**: `/api/v2`

---

## Estructura de Documentación

1. [00-fundamentos.md](00-fundamentos.md): Convenciones transversales, formato de envoltorio (envelope), autenticación Sanctum y manejo de códigos HTTP.
2. [ERRATAS.md](ERRATAS.md): Inconsistencias detectadas en la documentación de la API y discrepancias de autorización.
3. [LIMITACIONES.md](LIMITACIONES.md): Límites de rate limit, restricciones de payload, campos ignorados por el servidor (`ip_public`) y límites de validación.
4. [hardware.md](hardware.md): Especificación detallada de endpoints del dominio `/hardware` (dispositivos y estado de salud).
5. `src/`: Fuentes originales sin editar (consulta no rutinaria).

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13
