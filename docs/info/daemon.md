# Módulo: Demonio Orquestador Principal (`src/main.py`)

> Documentación técnica del servicio principal de monitorización continua, orquestación de colectores, búfer en memoria y transmisión periódica.

---

## 1. Qué hace y qué NO hace

### Qué hace
- Carga de forma segura y tipada la configuración desde `src/env.py` con fallback a `src/env.example.py` si no existe el archivo local.
- Instancia y orquesta los componentes del sistema: `PmicCollector`, `SystemCollector`, `HailoCollector`, `TelemetryAggregator` y `EnergyApiClient`.
- Gestiona el ciclo de vida continuo mediante captura limpia de señales POSIX de terminación (`SIGINT` y `SIGTERM`).
- Ejecuta el bucle temporal sincronizado respetando el intervalo de muestreo (`SAMPLING_INTERVAL_SECONDS`) y calculando la compensación del tiempo de ejecución de cada lectura.
- Evalúa periódicamente si debe vaciar el búfer de agregación y transmitir el paquete a la API.
- Expone argumentos de línea de comandos para facilitar el despliegue, diagnóstico y pruebas automatizadas:
  - `--once`: Realiza una única lectura y agregación y finaliza.
  - `--dry-run`: Genera y muestra en el log el payload JSON sin enviarlo a la red.
  - `--mock`: Fuerza el uso de datos simulados en todos los colectores.

### Qué NO hace
- No reinicia la máquina ni ejecuta acciones de apagado ante alertas de temperatura.
- No utiliza hilos concurrentes innecesarios; toda la secuencia de lectura es síncrona y determinista, reduciendo el consumo de CPU al mínimo.

---

## 2. Modelo de datos

- Orquesta los tipos definidos en `src/models.py`.

---

## 3. Flujos principales

### Bucle Principal
1. Carga la configuración con `load_config()`.
2. Registra manejadores de señal `signal.signal(SIGINT, daemon.handle_signal)` y `SIGTERM`.
3. Inicia el bucle `while self.running`:
   a. Mide el tiempo inicial `start_tick = time.time()`.
   b. Invoca `pmic = pmic_collector.collect()`, `system = system_collector.collect()` y `hailo = hailo_collector.collect(pmic)`.
   c. Añade la muestra al agregador si las lecturas base fueron válidas.
   d. Comprueba si `once` está activo o si `aggregator.should_report()` es verdadero.
   e. Si se debe reportar, llama a `payload = aggregator.flush()`.
   f. Si `dry_run` está activo, imprime el payload en el log; de lo contrario, envía con `api_client.send_energy_readings(payload)`.
   g. Calcula el tiempo restante para cumplir el ciclo de muestreo y duerme con `time.sleep(sleep_time)`.
4. Al recibir `SIGINT`/`SIGTERM`, sale del bucle y registra la parada limpia del servicio.

---

## 4. Puntos de entrada

- CLI: `python3 -m src.main [--once] [--dry-run] [--mock]`
- Servicio systemd: `systemd/energy-monitor.service`
- Clases y funciones:
  - `load_config() -> dict[str, Any]`
  - `EnergyMonitorDaemon(config: dict[str, Any], force_mock: bool = False)`
  - `EnergyMonitorDaemon.run(once: bool = False, dry_run: bool = False) -> None`

---

## 5. Dependencias

### Dependencias entrantes
- `systemd/energy-monitor.service`: Unidad de servicio de inicio automático.
- `tests/test_main.py`: Pruebas de integración del demonio.

### Dependencias salientes
- Librería estándar de Python: `argparse`, `importlib.util`, `logging`, `os`, `signal`, `sys`, `time`.
- `src/collectors/pmic.py`
- `src/collectors/system.py`
- `src/collectors/hailo.py`
- `src/buffer/aggregator.py`
- `src/api/client.py`

---

## 6. Configuración

| Parámetro | Valor por defecto | Efecto / Comportamiento |
| :--- | :--- | :--- |
| `API_BASE_URL` | `https://api.tu-servidor.com/api/v2` | URL del endpoint de la API. |
| `API_AUTH_TOKEN` | `""` | Token Sanctum para autorización Bearer. |
| `HARDWARE_DEVICE_ID` | `7` | ID asignado a la Raspberry Pi 5 en la API. |
| `SAMPLING_INTERVAL_SECONDS` | `10.0` | Frecuencia de lectura de sensores físicos. |
| `REPORT_INTERVAL_SECONDS` | `300.0` | Ventana de agregación y periodicidad de envíos. |
| `ENABLE_HAILO8` | `False` | Habilitación de recolección en Canal 1. |

---

## 7. Trampas conocidas

- Al ejecutar como servicio systemd con `DynamicUser=yes`, el servicio no tiene acceso de escritura en el sistema de archivos raíz, lo cual encaja perfectamente con el principio Zero-Disk Wear. Debe tener permisos para ejecutar `vcgencmd` (acceso a `/dev/vchiq`).

---

## 8. Tests que lo cubren

- [x] `tests/test_main.py::TestMainOrchestrator.test_load_config_defaults`: Comprueba la extracción y valores predeterminados de configuración.
- [x] `tests/test_main.py::TestMainOrchestrator.test_daemon_run_once_dry_run_mock`: Valida la orquestación completa de un ciclo de lectura, agregación y dry-run sin errores.
- [x] `tests/test_main.py::TestMainOrchestrator.test_daemon_signal_handling`: Valida que la captura de señales detiene el bucle de ejecución.

---

## 9. Pendiente real

- [ ] Ninguna tarea pendiente en este orquestador.

---
> Creado: 2026-09-14 · Última revisión: 2026-09-14
