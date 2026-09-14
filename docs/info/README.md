# Índice Maestro de Documentación Técnica (`docs/info/`)

Documentación técnica **viva** del monitor de energía y consumo para Raspberry Pi 5. Cualquier cambio en código que afecte a la arquitectura, componentes o comandos debe reflejarse aquí en el mismo commit.

---

## 1. Documentos Principales del Sistema

- [DESIGN.md](DESIGN.md): Principios arquitectónicos, objetivos y modelo conceptual del monitor.
- [COMPONENTS.md](COMPONENTS.md): Catálogo detallado de los componentes del sistema y su estado actual.
- [hardware.md](hardware.md): Especificación técnica de hardware, PMIC DA9091, 12 raíles, Hailo-8, fórmulas y sensores térmicos.
- [commands.md](commands.md): Comandos verificados del entorno y catálogo de comandos de desarrollo.
- [decisiones-tecnicas.md](decisiones-tecnicas.md): Registro histórico de decisiones deliberadas de diseño y arquitectura.
- [_MODULE_TEMPLATE.md](_MODULE_TEMPLATE.md): Plantilla obligatoria para la creación de nuevos documentos de módulo.


---

## 2. Estado de Módulos (`src/`)

| Módulo | Documento | Estado | Descripción |
| :--- | :--- | :--- | :--- |
| `src/env.example.py` | *(Documentado en [COMPONENTS.md](COMPONENTS.md))* | ✅ Verificado | Plantilla de configuración y secretos. |
| Colectores (`src/collectors/`) | *(Pendiente)* | ⚠️ Sin verificar | Módulos de lectura de PMIC, métricas y Hailo-8. |
| Búfer (`src/buffer/`) | *(Pendiente)* | ⚠️ Sin verificar | Acumulador y caché de telemetría local. |
| Cliente API (`src/api/`) | *(Pendiente)* | ⚠️ Sin verificar | Transmisión HTTP hacia la API receptora. |
| Servicio (`src/main.py`) | *(Pendiente)* | ⚠️ Sin verificar | Demonio y orquestador principal. |

---

## 3. Integración de APIs (`docs/info/apis/`)

| API / Servicio | Documentación Interna | Especificación Oficial | Estado |
| :--- | :--- | :--- | :--- |
| **API V2 (Backend Propio)** | [apis/api-v2.md](apis/api-v2.md) | [docs/apis/api-v2/README.md](../apis/api-v2/README.md) | ⚠️ Sin verificar con petición real |

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13

