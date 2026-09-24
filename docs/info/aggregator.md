# Módulo: Agregador y Búfer en RAM (`src/buffer/aggregator.py`)

> Documentación técnica del acumulador de telemetría en memoria volátil (Zero-Disk Wear) y generador de payloads agregados según el contrato API V2.

---

## 1. Qué hace y qué NO hace

### Qué hace
- Retiene muestras instantáneas de PMIC, métricas de sistema y telemetría de Hailo-8 en una cola circular acotada en memoria RAM (`collections.deque(maxlen=max_samples)`).
- Aplica la directiva estricta de **Zero-Disk Wear**: no escribe archivos temporales, logs en disco ni bases de datos locales durante la agregación continua.
- Evalúa si ha transcurrido la ventana de reporte configurada (`report_interval_seconds`) con respecto al inicio de la ventana actual (`_window_start_time`).
- En el momento de reporte (`flush()`), calcula la media aritmética de todas las magnitudes eléctricas continuas:
  - **Canal 0 (Raspberry Pi 5 base)**: Tensión media (`EXT5V_V`), potencia neta (`P_total_pmic - P_hailo`), corriente neta equivalente, temperatura media del SoC, y último estado del ventilador.
  - **Canal 1 (Hailo-8 M.2)**: Si existen muestras de Hailo-8, asigna su potencia estimada en PCIe (~0.50 W en reposo), corriente equivalente a 3.30 V y temperatura media del chip.
  - La suma de `loads[0].power + loads[1].power` equivale exactamente al consumo total real del PMIC DA9091 sin duplicidad (DT-011).
- Calcula el valor exacto y continuo de `duration` como el tiempo transcurrido desde el inicio de la ventana actual (`duration = max(1, int(round(current_time - self._window_start_time)))`), garantizando una integración continua de energía sin huecos ni solapes temporales (DT-010).
- Construye el bloque anidado `hardware_device_info` con promedios de CPU y RAM, último valor de disco, uptime, IP local, y bloque `extra` con la máscara de estrangulamiento, temperatura RP1, RPM del ventilador y temperatura de Hailo-8 (`hailo8_temp`).
- Resetea el búfer en memoria y reinicia el temporizador de ventana (`_window_start_time = current_time`).

### Qué NO hace
- No gestiona conexiones de red ni realiza peticiones HTTP (delegado en `EnergyApiClient`).
- No almacena datos en disco ante caídas de la API (por política de protección de tarjetas microSD/SSDs).

---

## 2. Modelo de datos

### Tipos exportados / utilizados (`src/models.py`)

```python
@dataclass(frozen=True)
class LoadReading:
    channel: int
    voltage: float
    amperage: float
    power: float
    temperature: float
    fan: int | None = None

    def to_dict(self) -> dict[str, Any]: ...

@dataclass(frozen=True)
class EnergyPayload:
    hardware_device_id: int
    duration: int
    read_at: str
    loads: list[LoadReading]
    device_info: dict[str, Any] = field(default_factory=dict)

    def to_api_dict(self) -> dict[str, Any]: ...
```

- Salida: `EnergyPayload` listo para serialización a JSON para la API.

---

## 3. Flujos principales

### Ingesta de Muestra
1. `add_sample(pmic, system, hailo, timestamp)` inserta una tupla `(pmic, system, hailo, timestamp)` al final del `deque`.

### Comprobación de Ventana
1. `should_report(now)` comprueba si `(now - _window_start_time) >= report_interval_seconds` y si hay al menos una muestra en memoria.

### Emisión de Ventana (`flush`)
1. Verifica que el búfer no esté vacío (si está vacío, lanza `ValueError`).
2. Itera sobre las muestras acumuladas calculando sumatorias de voltajes, amperajes, potencias, CPU, RAM y temperaturas.
3. Extrae la duración temporal real: `duration = max(1, int(round(current_time - self._window_start_time)))`.
4. Si hay muestras de Hailo-8:
   - Añade `loads[0]` (Canal 0, RPi neta = `P_pmic - P_hailo`).
   - Añade `loads[1]` (Canal 1, Hailo-8 = `P_hailo`).
   - Copia la temperatura media a `device_info["extra"]["hailo8_temp"]`.
5. Si no hay muestras de Hailo-8:
   - Añade `loads[0]` (Canal 0 con el 100% de la potencia PMIC).
6. Genera la marca de tiempo `read_at` en formato ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`).
7. Vacía la cola (`_samples.clear()`) y actualiza `_window_start_time = current_time`.
8. Retorna la instancia de `EnergyPayload`.

---

## 4. Puntos de entrada

- `TelemetryAggregator(hardware_device_id: int, report_interval_seconds: float = 300.0, max_samples: int = 3600)`: Constructor.
- `TelemetryAggregator.add_sample(...)`: Inserción de muestra.
- `TelemetryAggregator.should_report(...) -> bool`: Evaluación de expiración de ventana.
- `TelemetryAggregator.flush(...) -> EnergyPayload`: Cierre de ventana y generación de datos.
- `TelemetryAggregator.sample_count -> int`: Propiedad de conteo de muestras en memoria.

---

## 5. Dependencias

### Dependencias entrantes
- `src/main.py`: Demonio orquestador que gestiona la cola y programa los envíos.
- `tests/test_aggregator.py`: Pruebas unitarias de agregación y cálculo estadístico.

### Dependencias salientes
- Librería estándar de Python: `collections.deque`, `datetime`, `time`, `typing`.
- `src/models.py`: Dataclasses del modelo de datos.

---

## 6. Configuración

| Parámetro | Valor por defecto | Efecto / Comportamiento |
| :--- | :--- | :--- |
| `hardware_device_id` | *(Requerido)* | Identificador numérico del dispositivo físico en la API V2. |
| `report_interval_seconds` | `300.0` (5 min) | Duración de la ventana de agregación de métricas. |
| `max_samples` | `3600` | Límite máximo de muestras en RAM para evitar consumo de memoria ilimitado. |

---

## 7. Trampas conocidas

- **Cálculo de `duration` (DT-010)**: La duración se computa con respecto a `_window_start_time`. Esto garantiza que cubre la ventana completa transcurrida entre envíos reales sin el sesgo del 3,3 % que provocaba la resta de primera a última muestra.
- **Desacoplamiento de Cargas (DT-011)**: El Canal 0 descuenta la potencia del Canal 1 (`P_rpi = P_total - P_hailo`). Esto permite que la API mantenga las dos entidades individuales sin duplicar la energía del sistema en el acumulador global.

---

## 8. Tests que lo cubren

- [x] `tests/test_aggregator.py::TestTelemetryAggregator.test_empty_buffer_flush_raises`: Valida que llamar a `flush()` en vacío genera excepción controlada.
- [x] `tests/test_aggregator.py::TestTelemetryAggregator.test_should_report_logic`: Valida la temporización de apertura y cierre de ventanas.
- [x] `tests/test_aggregator.py::TestTelemetryAggregator.test_flush_without_hailo`: Verifica el cálculo de Canal 0 con el total de potencia cuando no hay acelerador.
- [x] `tests/test_aggregator.py::TestTelemetryAggregator.test_flush_with_hailo_two_channels_no_duplication`: Valida el desglose exacto entre Canal 0 (neta) y Canal 1 (Hailo-8), sumando la potencia total sin duplicar.
- [x] `tests/test_aggregator.py::TestTelemetryAggregator.test_duration_flush_at_305s_from_previous_window`: Comprueba que una ventana de 305 s con muestras cada 10 s computa `duration=305`.
- [x] `tests/test_aggregator.py::TestTelemetryAggregator.test_first_window_duration_from_startup`: Verifica que la primera ventana computa la duración exacta desde el inicio del demonio.

---

## 9. Pendiente real

- [ ] Ninguna tarea pendiente en este módulo.

---
> Creado: 2026-09-14 · Última revisión: 2026-09-24
