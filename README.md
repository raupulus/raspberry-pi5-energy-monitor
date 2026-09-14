# Raspberry Pi 5 Energy & Consumption Monitor

Sistema de monitorización continua de energía, consumo eléctrico y métricas de rendimiento para **Raspberry Pi 5**, diseñado para recopilar telemetría del hardware y transmitirla de forma periódica a una API personalizada.

## Características

- **Monitorización de Energía**: Lectura y cálculo continuo de consumo eléctrico (voltaje, corriente, potencia y métricas térmicas/PMIC de Raspberry Pi 5).
- **Envío Periódico a API**: Transmisión estructurada de telemetría a una API propia mediante endpoints configurables.
- **Soporte Modular Opcional**:
  - Módulo **Hailo-8 AI NPU** (conmutable mediante variable en `src/env.py`).
  - Extensible a otros sensores y periféricos IoT.
- **Base Moderna**: Diseñado y probado para **Python 3.14**.

---

## Estructura del Repositorio

```text
.
├── .agents/             # Instrucciones y configuración para agentes de IA
├── .claude -> .agents   # Enlace simbólico de compatibilidad
├── docs/                # Documentación técnica, esquemas y contratos de API
├── src/                 # Código fuente del monitor y módulos
│   └── env.example.py   # Plantilla de configuración de entorno
├── tests/               # Pruebas unitarias e integración
├── AGENTS.md            # Guía para agentes de IA
├── CLAUDE.md -> AGENTS.md
├── LICENSE              # Licencia GNU GPLv3
└── README.md            # Este archivo
```

---

## Requisitos y Configuración

### 1. Requisitos Previos

- **Hardware**: Raspberry Pi 5 (con Raspberry Pi OS o compatible). Opcional: HAT / módulo M.2 Hailo-8.
- **Software**: Python 3.14+.

### 2. Entorno Virtual

El proyecto está preparado para Python 3.14:

```bash
# Crear el entorno virtual si no existe
python3.14 -m venv .venv

# Activar el entorno virtual
source .venv/bin/activate
```

### 3. Variables de Entorno y Configuración

Copia la plantilla `src/env.example.py` a `src/env.py` (este archivo está ignorado por git para evitar fugas de secretos):

```bash
cp src/env.example.py src/env.py
```

Edita `src/env.py` con tus credenciales y preferencias:
- `API_BASE_URL`: URL de tu API receptora.
- `API_AUTH_TOKEN`: Token de autenticación de tu API.
- `REPORT_INTERVAL_SECONDS`: Frecuencia de envío de métricas.
- `ENABLE_HAILO8`: Establecer en `True` si deseas monitorizar el módulo de aceleración Hailo-8 AI.

---

## Próximos Pasos

1. Definición del contrato y especificación de la API receptora.
2. Implementación de los colectores de métricas para Raspberry Pi 5 (PMIC, temperatura, CPU/GPU, Hailo-8).
3. Servicio de transmisión resiliente con reintentos y caché local.

---

## Licencia

Este proyecto está distribuido bajo la licencia **GNU General Public License v3.0 (GPLv3)**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
