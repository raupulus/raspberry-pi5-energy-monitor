# Catálogo de Componentes (COMPONENTS.md)

Este documento cataloga los componentes del sistema, su estado de implementación en el repositorio y sus responsabilidades.

---

## Estado General de Componentes

| Componente | Archivo / Módulo | Estado | Responsabilidad |
| :--- | :--- | :--- | :--- |
| **Config Loader** | `src/env.py` / `src/env.example.py` | ✅ Verificado | Carga dinámica y tipada de credenciales, URLs de API y flags (`ENABLE_HAILO8`). |
| **PMIC DA9091 Collector** | `src/collectors/pmic.py` | ✅ Verificado | Adquisición ADC de 12 raíles, voltajes, potencias y corriente total vía `vcgencmd`. |
| **System & Health Collector** | `src/collectors/system.py` | ✅ Verificado | CPU, RAM, disco, temperaturas SoC/RP1, RPM y estado del ventilador, throttling. |
| **Hailo-8 AI Collector** | `src/collectors/hailo.py` | ✅ Verificado | Telemetría térmica de silicio TS0/TS1 y potencia estimada en Canal 1 (desacoplada de Canal 0). |
| **Data Aggregator & Buffer** | `src/buffer/aggregator.py` | ✅ Verificado | Acumulación en RAM (Zero-Disk Wear), cálculo de medias y armado de payload. |
| **API Client** | `src/api/client.py` | ✅ Verificado | Serialización JSON, cabeceras Bearer, POST con reintentos exponenciales a API V2. |
| **Daemon Orchestrator** | `src/main.py` | ✅ Verificado | Bucle principal síncrono, temporización, manejo de señales y flags CLI. |

---

## Detalle de Componentes

### 1. Config Loader
- **Ubicación**: `src/main.py` (`load_config()`), basado en `src/env.example.py` (código de producción en `src/env.py`).
- **Estado**: ✅ Verificado. Carga tolerante con valores por defecto seguros.
- **Entradas**: Variables en archivo Python local ignorado por git.
- **Salidas**: Diccionario fuertemente tipado de configuración.

### 2. Colectores de Hardware y Sensores (`src/collectors/`)
- **Estado**: ✅ Verificado.
- **Implementación**:
  - `PmicCollector`: Parsea voltajes y corrientes de los 12 raíles del PMIC DA9091.
  - `SystemCollector`: Lee `/proc/stat`, `/proc/meminfo`, `os.statvfs`, `/sys/class/thermal`, tacómetro fan RPM en `hwmon2` y throttling.
  - `HailoCollector`: Integración perezosa con `hailo_platform.Device` para temperaturas TS0/TS1 y estimación de potencia en bus PCIe (Canal 1).

### 3. Agregador y Búfer en Memoria (`src/buffer/`)
- **Estado**: ✅ Verificado.
- **Implementación**: `TelemetryAggregator` retiene muestras en `collections.deque` en RAM sin desgaste de disco. Calcula medias de la ventana (típicamente 300 s) y produce `EnergyPayload`.

### 4. Cliente API V2 (`src/api/`)
- **Estado**: ✅ Verificado.
- **Implementación**: `EnergyApiClient` utiliza la librería estándar `urllib.request`, manejando respuestas 201 Created con warnings, omisión de reintentos en 4xx y reintentos con backoff en 5xx/red.

### 5. Demonio de Servicio (`src/main.py`)
- **Estado**: ✅ Verificado.
- **Implementación**: `EnergyMonitorDaemon` orquesta el muestreo periódico y emisión. Soporta `--once`, `--dry-run` y `--mock`, integrándose con la unidad systemd `systemd/energy-monitor.service`.

---
> Creado: 2026-09-13 · Última revisión: 2026-09-24
