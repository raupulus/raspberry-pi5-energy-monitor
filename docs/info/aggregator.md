# Módulo: Agregador y Búfer en RAM (`src/buffer/aggregator.py`)

> Documentación técnica del acumulador de telemetría en memoria volátil (Zero-Disk Wear) y generador de payloads agregados según el contrato API V2.

---

## 1. Qué hace y qué NO hace

### Qué hace
- Retiene muestras instantáneas de PMIC, métricas de sistema y telemetría de Hailo-8 en una cola circular acotada en memoria RAM (`collections.deque(maxlen=max_samples)`).
- Aplica la directiva estricta de **Zero-Disk Wear**: no escribe archivos temporales, logs en disco ni bases de datos locales durante la agregación continua.
- Evalúa si ha transcurrido la ventana de reporte configurada (`report_interval_seconds`) con respecto al inicio de la ventana actual (`_window_start_time`).
- En el momento de reporte (`flush()`), calcula la media aritmética de todas las magnitudes eléctricas continuas:
  - **Canal 0 (Raspberry Pi 5)**: Tensión media (`EXT5V_V`), corriente media estimada, potencia disipada media, temperatura media del SoC, y último estado del ventilador.
  - **Canal 1 (Hailo-8)**: Si existen muestras válidas durante la ventana, calcula potencia media, temperatura media y deriva la corriente a 3.30V. Si no hay muestras, omite Canal 1 de la lista de cargas (`loads`).
- Calcula el valor exacto de `duration` (segundos entre la primera y la última muestra de la ventana, o `report_interval_seconds` como valor por defecto).
- Construye el bloque anidado `hardware_device_info` con promedios de CPU y RAM, último valor de disco, uptime, IP local, y bloque `extra` con la máscara de estrangulamiento, temperatura RP1, RPM del ventilador y temperatura de Hailo-8.
- Resetea el búfer en memoria y reinicia el temporizador de ventana.

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
3. Extrae la duración temporal real: `duration = max(1, int(round(last_ts - first_ts)))`.
4. Construye `loads[0]` (Canal 0, obligatorio) y opcionalmente `loads[1]` (Canal 1, solo si `hailo_samples_count > 0`).
5. Genera la marca de tiempo `read_at` en formato ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SSZ`).
6. Vacía la cola (`_samples.clear()`) y actualiza `_window_start_time`.
7. Retorna la instancia de `EnergyPayload`.

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

- Si se recolecta una única muestra (p. ej. ejecución única `--once`), la diferencia entre `last_sample_time` y `first_sample_time` es cero. El agregador detecta esta condición y asigna por defecto `duration = max(1, int(round(report_interval_seconds)))` para cumplir la restricción del contrato de API V2 (`duration >= 1`).
- Canal 1 sólo se añade a `loads` si durante la ventana hubo lecturas activas de Hailo-8. Si el flag `ENABLE_HAILO8` está desactivado, Canal 1 desaparece limpiamente del JSON.

---

## 8. Tests que lo cubren

- [x] `tests/test_aggregator.py::TestTelemetryAggregator.test_empty_buffer_flush_raises`: Valida que llamar a `flush()` en vacío genera excepción controlada.
- [x] `tests/test_aggregator.py::TestTelemetryAggregator.test_should_report_logic`: Valida la temporización de apertura y cierre de ventanas.
- [x] `tests/test_aggregator.py::TestTelemetryAggregator.test_flush_without_hailo`: Verifica la omisión del Canal 1 y el cálculo de Canal 0 y salud del sistema.
- [x] `tests/test_aggregator.py::TestTelemetryAggregator.test_flush_with_hailo`: Valida el cálculo combinado de Canal 0 y Canal 1 con temperaturas e indicadores extra.

---

## 9. Pendiente real

- [ ] Ninguna tarea pendiente en este módulo.

---
> Creado: 2026-09-14 · Última revisión: 2026-09-14
