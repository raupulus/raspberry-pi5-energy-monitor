# Raspberry Pi 5 Energy & Consumption Monitor

Sistema de monitorización continua de energía, consumo eléctrico y salud de hardware para **Raspberry Pi 5**, con soporte modular para aceleradores de inferencia neuronal **Hailo-8 M.2 (26 TOPS)** y transmisión periódica agregada a backend propio (**API V2**).

Diseñado bajo la premisa de **desgaste cero de disco (*Zero-Disk Wear*)** y **cero dependencias de terceros en tiempo de ejecución (*Pure Python Standard Library*)**, garantizando un impacto despreciable en CPU (< 0.2%) y memoria (< 15 MB).

---

## ⚡ Capacidades del Sistema

- **Telemetría Eléctrica de Alta Precisión (PMIC Renesas DA9091)**:
  - Muestreo directo vía firmware de los 12 raíles internos de alimentación mediante el ADC multicanal integrado.
  - Cálculo instantáneo de voltajes, amperajes y vatios disipados por raíl, potencia combinada de CPU/GPU y tensión real de entrada USB-C (`EXT5V_V`).
- **Métricas de Salud del Sistema y Sensores Térmicos**:
  - Carga de CPU evaluada por delta de tiempos en `/proc/stat`.
  - Uso de memoria RAM real desde `/proc/meminfo` (`MemTotal` vs `MemAvailable`).
  - Ocupación del sistema de archivos raíz (`/`) mediante llamadas POSIX `statvfs`.
  - Sondas térmicas: Temperatura del procesador BCM2712 (Cortex-A76) y del Southbridge RP1.
  - Tacómetro del ventilador oficial *Active Cooler*: Lectura de revoluciones por minuto (RPM) en `/sys/devices/platform/cooling_fan/hwmon/hwmon2/fan1_input` y nivel PWM de refrigeración (0 a 4).
  - Diagnóstico de subvoltaje y *throttling*: Captura continua de la máscara de bits de `vcgencmd get_throttled`.
- **Soporte Modular Opcional para Hailo-8 M.2 AI NPU**:
  - Lectura de temperaturas internas de silicio (sensores térmicos TS0 y TS1) y estado de estrangulamiento térmico mediante el SDK oficial `hailo_platform.Device`.
  - Estimación de consumo eléctrico a partir del incremento de potencia en los raíles `3V3_SYS` y `1V8_SYS` del PMIC.
  - Canal condicional: Si `ENABLE_HAILO8 = False` o el módulo no está conectado, el Canal 1 se omite limpiamente del payload.
- **Búfer en RAM (Zero-Disk Wear)**:
  - Retención de muestras exclusivamente en memoria volátil mediante colas circulares (`collections.deque`).
  - Cero operaciones de I/O en disco durante la recolección continua, preservando la vida útil de tarjetas MicroSD y discos SSD NVMe.
- **Agregación Estadística y Duración Exacta**:
  - Muestreo raw cada 10 segundos en memoria y agregación en ventanas periódicas (por defecto 300 s / 5 min).
  - Cálculo de promedios aritméticos exactos y parámetro `duration` para que el backend integre automáticamente los vatios-hora ($Wh = \frac{P_{\text{avg}} \times \text{duration}}{3600}$).
- **Cliente HTTP Resiliente**:
  - Construido exclusivamente con `urllib.request` de la biblioteca estándar de Python.
  - Autenticación mediante Bearer Token Sanctum.
  - Reintentos automáticos con retroceso exponencial (*exponential backoff*: $2^n$ segundos) ante caídas de red o errores 5xx/429.
  - Detección y registro de advertencias no bloqueantes devueltas por la API (`warnings`).
- **Servicio Systemd de Producción**:
  - Configurado con reinicio automático ante fallos (`Restart=always`) e inicio sincronizado con la red (`network-online.target`).

---

## 🏗️ Estructura del Repositorio

```text
.
├── .agents/                      # Instrucciones y directrices para agentes
├── .claude -> .agents            # Enlace simbólico de compatibilidad
├── .env.example                  # Plantilla de variables de entorno generales
├── .gitignore                    # Exclusiones de git (incluye src/env.py, planning y auditorias)
├── .python-version               # Versión de Python fijada (3.14)
├── AGENTS.md                     # Guía técnica y directrices residentes
├── CLAUDE.md -> AGENTS.md        # Enlace simbólico hacia AGENTS.md
├── LICENSE                       # Licencia GNU GPLv3
├── README.md                     # Este archivo
├── docs/
│   ├── apis/                     # Documentación oficial de APIs externas
│   │   └── api-v2/               # Backend API V2 (contrato oficial y especificaciones)
│   ├── future/                   # Funcionalidades y propuestas aplazadas
│   │   └── hailo8-fan.md         # Monitorización de ventilador secundario HAT Hailo-8
│   └── info/                     # Documentación técnica VIVA del proyecto
│       ├── _MODULE_TEMPLATE.md   # Plantilla obligatoria para documentar módulos
│       ├── COMPONENTS.md         # Catálogo de componentes y estado de implementación
│       ├── DESIGN.md             # Principios y arquitectura del sistema
│       ├── README.md             # Índice maestro de documentación técnica
│       ├── aggregator.md         # Agregador y búfer de telemetría en RAM
│       ├── api-client.md         # Cliente HTTP hacia API V2
│       ├── apis/                 # Integración interna de APIs
│       │   └── api-v2.md
│       ├── commands.md           # Catálogo de comandos verificados
│       ├── daemon.md             # Demonio síncrono y orquestador CLI/systemd
│       ├── decisiones-tecnicas.md# Registro de decisiones deliberadas
│       ├── hailo.md              # Colector opcional Hailo-8 M.2 AI NPU
│       ├── hardware.md           # Especificación técnica de hardware y telemetría
│       ├── pmic.md               # Colector de 12 raíles del PMIC DA9091
│       └── system.md             # Colector de métricas de sistema y salud
├── src/                          # Código fuente de la aplicación
│   ├── __init__.py
│   ├── api/                      # Cliente de transmisión API V2
│   │   ├── __init__.py
│   │   └── client.py
│   ├── buffer/                   # Búfer en memoria RAM y agregación
│   │   ├── __init__.py
│   │   └── aggregator.py
│   ├── collectors/               # Colectores de telemetría y sensores
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── hailo.py
│   │   ├── pmic.py
│   │   └── system.py
│   ├── env.example.py            # Plantilla de configuración y secretos locales
│   ├── main.py                   # Punto de entrada y demonio del servicio
│   └── models.py                 # Dataclasses y modelos de datos tipados
├── systemd/                      # Configuración de servicio del sistema
│   └── energy-monitor.service    # Unidad systemd para Raspberry Pi OS
└── tests/                        # Suite completa de pruebas unitarias (22 tests)
    ├── test_aggregator.py
    ├── test_api_client.py
    ├── test_hailo.py
    ├── test_main.py
    ├── test_models.py
    ├── test_pmic.py
    └── test_system.py
```

---

## 🚀 Despliegue e Instalación

### 1. Requisitos Previos

- **Hardware**: Raspberry Pi 5 (recomendada fuente oficial USB-C PD 27W). Opcional: Acelerador M.2 PCIe Hailo-8.
- **Sistema Operativo**: Raspberry Pi OS Oficial (64-bit, Debian-based) actualizado.
- **Python**: Python 3.13 o Python 3.14 (utiliza exclusivamente la biblioteca estándar sin requerir dependencias `pip` adicionales).

### 2. Clonar el Repositorio

Conéctate por SSH a tu Raspberry Pi 5 y clona el proyecto en el directorio recomendado:

```bash
cd ~/git
git clone https://gitlab.com/raupulus/raspberry-pi5-energy-monitor.git
cd raspberry-pi5-energy-monitor
```

### 3. Configuración Local (`src/env.py`)

Copia la plantilla de variables de entorno y ajusta tus credenciales:

```bash
cp src/env.example.py src/env.py
nano src/env.py
```

Configura las variables correspondientes a tu infraestructura:

```python
# Configuración de API V2
API_BASE_URL: str = "https://api.tu-servidor.com/api/v2"
API_AUTH_TOKEN: str = "tu_token_sanctum_aqui"

# Identificador numérico del dispositivo en el backend (hardware_device_id)
HARDWARE_DEVICE_ID: int = 21

# Frecuencias de muestreo (segundos)
SAMPLING_INTERVAL_SECONDS: float = 10.0   # Muestreo raw en RAM
REPORT_INTERVAL_SECONDS: float = 300.0     # Ventana de envío a la API (5 minutos)

# Habilitación de módulo acelerador Hailo-8 M.2 AI
ENABLE_HAILO8: bool = True
```

> 🔒 **Nota de Seguridad**: `src/env.py` se encuentra excluido del control de versiones (`.gitignore`) para evitar la filtración accidental de tokens o URLs privadas.

### 4. Prueba en Vivo (CLI)

Antes de activar el servicio del sistema, ejecuta una pasada única para verificar que los colectores leen correctamente el hardware físico y que la API acepta la telemetría:

```bash
# Prueba simulada (sin enviar a la API)
python3 -m src.main --once --dry-run

# Prueba real transmitiendo una muestra a la API
python3 -m src.main --once
```

Deberás observar en la salida la confirmación del envío con código HTTP 201:
```text
[INFO] energy_monitor.api: Telemetría enviada con éxito (201 Created). Message: Telemetría de energía almacenada correctamente.
```

### 5. Instalación como Servicio Systemd

Para que el monitor se inicie automáticamente tras el arranque de la Raspberry Pi 5 y se mantenga en ejecución continua con autorecuperación:

```bash
# Copiar el archivo de servicio al directorio de systemd
sudo cp systemd/energy-monitor.service /etc/systemd/system/

# Recargar la configuración de systemd
sudo systemctl daemon-reload

# Habilitar e iniciar el servicio inmediatamente
sudo systemctl enable --now energy-monitor.service
```

### 6. Monitorización y Diagnóstico

Comprueba el estado del servicio y consulta los logs de ejecución en tiempo real:

```bash
# Estado del servicio
sudo systemctl status energy-monitor.service

# Seguimiento de logs en vivo
sudo journalctl -u energy-monitor.service -f
```

---

## 🧪 Pruebas Automatizadas

El proyecto incluye 22 pruebas unitarias que validan la serialización de modelos, el parseo de salidas de firmware de 12 raíles, los cálculos de deltas de CPU, el búfer de agregación y el manejo de reintentos HTTP:

```bash
# Ejecutar la suite completa de pruebas unitarias
python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## 📊 Formato del Payload de Telemetría (`POST /energy/readings`)

El payload enviado a la API cumple estrictamente con el contrato universal:

```json
{
  "hardware_device_id": 21,
  "duration": 300,
  "read_at": "2026-09-14T10:39:43Z",
  "energy": {
    "loads": [
      {
        "channel": 0,
        "voltage": 5.06,
        "amperage": 0.551,
        "power": 2.786,
        "temperature": 48.5,
        "fan": 1
      },
      {
        "channel": 1,
        "voltage": 3.30,
        "amperage": 0.152,
        "power": 0.500,
        "temperature": 35.87
      }
    ]
  },
  "hardware_device_info": {
    "temp": 48.5,
    "voltage": 5.06,
    "cpu": 1.2,
    "ram": 52.2,
    "disk": 10.2,
    "uptime": 404520,
    "ip_local": "172.18.1.121",
    "extra": {
      "throttle_state": "0x0",
      "samples_count": 30,
      "rp1_temp": 50.8,
      "fan_rpm": 3784,
      "hailo8_temp": 35.87
    }
  }
}
```

---

## 📖 Documentación Adicional

- [docs/info/DESIGN.md](docs/info/DESIGN.md): Arquitectura y principios de diseño.
- [docs/info/hardware.md](docs/info/hardware.md): Especificación técnica del hardware PMIC DA9091, 12 raíles y Hailo-8.
- [docs/info/COMPONENTS.md](docs/info/COMPONENTS.md): Catálogo detallado de módulos y componentes.
- [docs/info/commands.md](docs/info/commands.md): Catálogo de comandos verificados de desarrollo y mantenimiento.
- [docs/info/decisiones-tecnicas.md](docs/info/decisiones-tecnicas.md): Registro deliberado de decisiones técnicas y de arquitectura.
- [docs/apis/api-v2/](docs/apis/api-v2/): Especificaciones de la API V2 receptora.

---

## 📄 Licencia y Autoría

- **Autor**: Raúl Caro Pastorino ([@raupulus](https://github.com/raupulus) / [@raupulus](https://gitlab.com/raupulus) · `public@raupulus.dev`)
- **Licencia**: Distribuido bajo licencia **GNU General Public License v3.0 (GPLv3)**. Consulta [LICENSE](LICENSE) para más información.
