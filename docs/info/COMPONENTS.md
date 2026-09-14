# Catálogo de Componentes (COMPONENTS.md)

Este documento cataloga los componentes del sistema, su estado de implementación en el repositorio y sus responsabilidades.

---

## Estado General de Componentes

| Componente | Archivo / Módulo | Estado | Responsabilidad |
| :--- | :--- | :--- | :--- |
| **Config Loader** | `src/env.example.py` | ✅ Plantilla verificada (`src/env.py` ignorado) | Carga de credenciales, URLs de API y flags (`ENABLE_HAILO8`). |
| **Hardware Metric Collector** | `src/collectors/` | ⚠️ Sin verificar (pendiente de implementación) | Lectura de sysfs/hwmon para voltajes, amperajes, vatios y temperaturas de RPi 5. |
| **Hailo-8 AI Collector** | `src/collectors/` | ⚠️ Sin verificar (pendiente de implementación) | Recolección opcional de métricas de uso y estado del acelerador NPU Hailo-8. |
| **Data Aggregator & Buffer** | `src/buffer/` | ⚠️ Sin verificar (pendiente de implementación) | Acumulación periódica y almacenamiento temporal ante caídas de red. |
| **API Dispatcher** | `src/api/` | ⚠️ Sin verificar (pendiente de implementación) | Serialización de métricas y transmisión HTTP/REST a la API propia. |
| **Service Entrypoint** | `src/main.py` | ⚠️ Sin verificar (pendiente de implementación) | Bucle principal de ejecución y orquestación del servicio. |

---

## Detalle de Componentes

### 1. Config Loader
- **Ubicación**: `src/env.example.py` (código de producción en `src/env.py`).
- **Estado**: Definida la plantilla de variables base con soporte para API y flag de Hailo-8.
- **Entradas**: Variables en archivo Python local ignorado por git.
- **Salidas**: Constantes tipadas consumibles por el resto de la aplicación.

### 2. Colectores de Hardware (Pendiente)
- **Estado**: `⚠️ sin verificar` (no implementado en código).
- **Alcance previsto**: Colectores desacoplados con interfaz común (`CollectorInterface`) que produzcan muestras homogéneas de telemetría.

### 3. Agregador y Búfer (Pendiente)
- **Estado**: `⚠️ sin verificar` (no implementado en código).
- **Alcance previsto**: Agrupar muestras recogidas en intervalos configurables antes de transmitirlas.

### 4. Cliente API / Despachador (Pendiente)
- **Estado**: `⚠️ sin verificar` (no implementado en código).
- **Alcance previsto**: Cliente HTTP con autenticación por token y reintentos exponenciales.

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13
