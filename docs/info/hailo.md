# Módulo: Colector Hailo-8 AI NPU (`src/collectors/hailo.py`)

> Documentación técnica del módulo colector opcional para la NPU de aceleración neuronal Hailo-8 en formato M.2 PCIe.

---

## 1. Qué hace y qué NO hace

### Qué hace
- Consulta las temperaturas internas del silicio de la NPU (sensores `ts0` y `ts1`) y el estado de estrangulamiento térmico utilizando el SDK oficial `hailo_platform.Device`.
- Calcula la temperatura media del chip Hailo-8 (`avg_temp = (ts0 + ts1) / 2.0`).
- Estima la potencia consumida en vatios por el módulo M.2 calculando la potencia disipada en los raíles de 3.3V y 1.8V del PMIC DA9091 (`3V3_SYS` y `1V8_SYS`).
- Aplica importación perezosa (*lazy import*) de la librería `hailo_platform` para evitar que la aplicación falle si el módulo de hardware o el driver PCIe no están instalados.
- Retorna `None` inmediatamente si `ENABLE_HAILO8` está desactivado (`False`), provocando que el Canal 1 se omita por completo en el payload de energía.
- Proporciona modo simulado (`force_mock=True` o fallback si no está el SDK instalado) con métricas realistas verificadas en hardware real.

### Qué NO hace
- No intenta controlar el firmware, modelos de inferencia o memoria de la Hailo-8.
- No monitorea el ventilador del HAT Hailo-8 (aplazado a `docs/future/hailo8-fan.md` al carecer el HAT de tacómetro accesible por Device Tree).

---

## 2. Modelo de datos

### Tipos exportados / utilizados (`src/models.py`)

```python
@dataclass(frozen=True)
class HailoHealth:
    temp_ts0_c: float
    temp_ts1_c: float
    avg_temp_c: float
    is_throttling: bool
    estimated_power_w: float
    timestamp: float
```

- Temperaturas en grados Celsius (°C).
- Potencia estimada en vatios (`estimated_power_w`).
- Modelo inmutable (`frozen=True`).

---

## 3. Flujos principales

### Flujo de Inicialización y Muestreo
1. Al instanciar `HailoCollector(enabled, force_mock)`:
   - Si `enabled=True` y `force_mock=False`, intenta importar `from hailo_platform import Device`. Si no está disponible, almacena `None`.
2. Al ejecutar `collect(pmic)`:
   - Si `enabled=False`: Retorna inmediatamente `None`.
   - Si `force_mock=True` o `device_cls is None`: Retorna `_mock_hailo(pmic)`.
   - En hardware real: Abre el contexto `with self._device_cls() as target`, invoca `target.control.get_chip_temperature()` y `target.control.get_throttling_state()`, extrae `ts0` y `ts1`, estima la potencia mediante `_estimate_power(pmic)` y retorna `HailoHealth`.
   - Ante cualquier excepción en la comunicación PCIe o driver: Captura el error y retorna `None`.

---

## 4. Puntos de entrada

- `HailoCollector(enabled: bool = False, force_mock: bool = False)`: Constructor.
- `HailoCollector.collect(pmic: PmicReading | None = None) -> HailoHealth | None`: Muestreo de salud de la NPU.

---

## 5. Dependencias

### Dependencias entrantes
- `src/main.py`: Orquestador principal.
- `tests/test_hailo.py`: Suite de pruebas unitarias.

### Dependencias salientes
- Librería estándar de Python: `time`, `typing`.
- `src/collectors/base.py`: Clase abstracta base.
- `src/models.py`: Dataclasses `HailoHealth` y `PmicReading`.
- Driver y SDK oficial (opcional, en Raspberry Pi OS): `hailo_platform` (paquete `hailort`).

---

## 6. Configuración

| Parámetro | Valor por defecto | Efecto / Comportamiento |
| :--- | :--- | :--- |
| `enabled` | `False` | Habilita o deshabilita la recolección del Canal 1. |
| `force_mock` | `False` | Fuerza la generación de telemetría simulada sin invocar `hailo_platform`. |

---

## 7. Trampas conocidas

- **TR-002 (Control de Hailo-8)**: Si el módulo PCIe entra en suspensión o el driver `hailort` no está compilado para el kernel en ejecución, la llamada a `Device()` puede fallar. Se mitiga capturando todas las excepciones y retornando `None`.
- **TR-006 (Ausencia de shunt DVM dedicado)**: La tarjeta M.2 de Hailo-8 no tiene shunt propio; su potencia se estima cruzando el consumo diferencial en los raíles `3V3_SYS` y `1V8_SYS` del PMIC DA9091.

---

## 8. Tests que lo cubren

- [x] `tests/test_hailo.py::TestHailoCollector.test_hailo_disabled_returns_none`: Comprueba que cuando `enabled=False` no se genera ningún dato (`None`).
- [x] `tests/test_hailo.py::TestHailoCollector.test_hailo_mock_returns_health_metrics`: Verifica temperaturas y potencia estimada en modo simulado.
- [x] `tests/test_hailo.py::TestHailoCollector.test_estimate_power_with_pmic_rails`: Comprueba el algoritmo de estimación eléctrica a partir de los raíles del PMIC.
- [x] `tests/test_hailo.py::TestHailoCollector.test_hailo_exception_fallback`: Asegura que excepciones de hardware en tiempo de ejecución devuelven `None` limpiamente.

---

## 9. Pendiente real

- [ ] Ninguna tarea pendiente en este colector.

---
> Creado: 2026-09-14 · Última revisión: 2026-09-14
