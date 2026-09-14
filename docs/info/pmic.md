# Módulo: Colector de PMIC DA9091 (`src/collectors/pmic.py`)

> Documentación técnica del módulo de adquisición eléctrica de los raíles y magnitudes globales del PMIC Renesas DA9091 en Raspberry Pi 5.

---

## 1. Qué hace y qué NO hace

### Qué hace
- Ejecuta la utilidad del firmware oficial de Raspberry Pi 5 `vcgencmd pmic_read_adc` para obtener lecturas en tiempo real de los 12 raíles internos de alimentación.
- Parsea voltajes (mV o V) y corrientes (mA o A) de cada raíl individual, calculando su potencia disipada instantánea en vatios (`power_w`).
- Extrae la tensión de alimentación externa de entrada de 5V (`EXT5V_V`).
- Calcula la potencia combinada consumida por la CPU y la GPU a partir de los raíles específicos `VDD_CORE`, `VDD_CORE_A` y `VDD_CPU`.
- Suma la potencia total disipada por todos los raíles activos para obtener `total_power_w`.
- Estima la corriente global instantánea demandada a la fuente de alimentación (`estimated_current_ma = (total_power_w / input_voltage_v) * 1000`).
- Incorpora un modo de simulación (`force_mock=True` o fallback si no existe `vcgencmd` en el PATH) para desarrollo y testing sin hardware físico.

### Qué NO hace
- No guarda histórico de muestras en disco ni en base de datos.
- No envía datos a la API ni realiza agregaciones temporales (delegado en `aggregator.py`).
- No altera tensiones ni interactúa con la configuración del PMIC (modo de solo lectura).

---

## 2. Modelo de datos

### Tipos exportados / utilizados (`src/models.py`)

```python
@dataclass(frozen=True)
class RailMeasurement:
    name: str
    volts: float
    current_a: float
    power_w: float

@dataclass(frozen=True)
class PmicReading:
    input_voltage_v: float
    total_power_w: float
    estimated_current_ma: float
    cpu_gpu_power_w: float
    rails: dict[str, RailMeasurement]
    timestamp: float
```

- Todas las magnitudes se devuelven en unidades base del SI (Voltios, Amperios, Vatios).
- Los modelos son inmutables (`frozen=True`).

---

## 3. Flujos principales

### Flujo de Adquisición
1. `collect()` verifica si `force_mock` está activado o si el comando `vcgencmd` no está disponible en el sistema.
2. Si `vcgencmd` está presente, ejecuta `vcgencmd pmic_read_adc` con un timeout de 2.0 segundos.
3. El stdout es analizado línea a línea con expresiones regulares identificando nombres de raíl, voltajes y amperajes.
4. Para cada raíl se calculan voltios, amperios y vatios (`V * A`).
5. Se identifican el raíl de entrada `EXT5V_V` (o similar) y los raíles del subsistema de procesamiento (`VDD_CORE`, `VDD_CORE_A`, `VDD_CPU`).
6. Se devuelve una instancia estructurada de `PmicReading`.

### Recuperación ante errores
- Si la ejecución de `vcgencmd` falla (código de retorno distinto de cero, timeout o excepción de E/S), se captura la excepción y se recurre a `_mock_reading()` registrando un aviso en el log.

---

## 4. Puntos de entrada

- `PmicCollector(force_mock: bool = False)`: Constructor de la clase.
- `PmicCollector.collect() -> PmicReading | None`: Método principal de muestreo periódico.

---

## 5. Dependencias

### Dependencias entrantes
- `src/main.py`: Demonio orquestador que invoca `collect()` en cada tick del bucle principal.
- `tests/test_pmic.py`: Suite de pruebas unitarias.

### Dependencias salientes
- Librería estándar de Python: `re`, `shutil`, `subprocess`, `time`, `logging`.
- `src/collectors/base.py`: Clase abstracta `BaseCollector`.
- `src/models.py`: Modelos `PmicReading` y `RailMeasurement`.
- Binario del sistema en Raspberry Pi OS: `/usr/bin/vcgencmd`.

---

## 6. Configuración

| Parámetro | Valor por defecto | Efecto / Comportamiento |
| :--- | :--- | :--- |
| `force_mock` | `False` | Si es `True`, omite llamadas al binario `vcgencmd` y genera telemetría simulada. |

---

## 7. Trampas conocidas

- **TR-001 (vcgencmd vs sysfs)**: Leer directamente los ADC del DA9091 mediante `/sys/class/hwmon/` en Raspberry Pi 5 no proporciona nombres legibles de los 12 raíles sin cruzar esquemáticos de la placa. `vcgencmd pmic_read_adc` es la interfaz oficial recomendada por Raspberry Pi Ltd.
- La ejecución de `vcgencmd` requiere que el usuario pertenezca al grupo `video` o tenga permisos de acceso a `/dev/vchiq`.

---

## 8. Tests que lo cubren

- [x] `tests/test_pmic.py::TestPmicCollector.test_collector_mock_mode`: Verifica que en modo mock se devuelvan lecturas coherentes dentro de los rangos válidos.
- [x] `tests/test_pmic.py::TestPmicCollector.test_parse_real_hardware_output`: Verifica el parseo exacto de la salida capturada del hardware físico real de la RPi 5.

---

## 9. Pendiente real

- [ ] Ninguna tarea pendiente en este colector.

---
> Creado: 2026-09-14 · Última revisión: 2026-09-14
