# Módulo: Colector de Sistema y Salud (`src/collectors/system.py`)

> Documentación técnica del colector de métricas de salud del sistema operativo, sensores térmicos, tacómetro de ventilador y estado de estrangulamiento (*throttling*) para Raspberry Pi 5.

---

## 1. Qué hace y qué NO hace

### Qué hace
- Calcula el porcentaje de uso de CPU analizando el incremento relativo de `/proc/stat` entre ticks consecutivos.
- Calcula el porcentaje de ocupación de memoria RAM a partir de `MemTotal` y `MemAvailable` en `/proc/meminfo`.
- Calcula el uso de disco de la partición raíz `/` mediante llamada POSIX `os.statvfs("/")`.
- Adquiere la temperatura en tiempo real del SoC principal BCM2712 desde `/sys/class/thermal/thermal_zone0/temp` (con fallback a `/sys/class/hwmon/hwmon0/temp1_input` o `vcgencmd measure_temp`).
- Adquiere la temperatura del Southbridge RP1 desde `/sys/class/hwmon/hwmon1/temp1_input`.
- Lee el tacómetro en tiempo real (RPM) del ventilador oficial Active Cooler desde `/sys/devices/platform/cooling_fan/hwmon/hwmon2/fan1_input`.
- Lee el estado de refrigeración PWM del ventilador (nivel 0 a 4) desde `/sys/class/thermal/cooling_device0/cur_state`.
- Adquiere la máscara hexadecimal de estrangulamiento térmico y subtensión mediante `vcgencmd get_throttled`.
- Obtiene el tiempo de actividad del sistema (*uptime* en segundos) desde `/proc/uptime`.
- Obtiene la dirección IPv4 local de salida de la interfaz de red activa mediante apertura de socket UDP no bloqueante hacia DNS público.
- Implementa modo mock automático o forzado (`force_mock=True`) si se ejecuta fuera de Linux o sin acceso a `/proc/stat`.

### Qué NO hace
- No gestiona ni altera las curvas del ventilador ni la frecuencia del procesador (solo lectura de telemetría).
- No realiza agregaciones temporales (delegado en `aggregator.py`).

---

## 2. Modelo de datos

### Tipos exportados / utilizados (`src/models.py`)

```python
@dataclass(frozen=True)
class SystemHealth:
    cpu_pct: float
    ram_pct: float
    disk_pct: float
    temp_soc_c: float
    temp_rp1_c: float | None
    fan_rpm: int | None
    fan_state: int | None
    throttle_hex: str
    uptime_s: int
    ip_local: str | None
    timestamp: float
```

- Temperaturas en grados Celsius (°C).
- Porcentajes acotados entre 0.0 y 100.0%.
- Tiempos en segundos enteros.
- Modelo inmutable (`frozen=True`).

---

## 3. Flujos principales

### Flujo de Recolección de Telemetría
1. `collect()` verifica si `force_mock` está activo o si el sistema carece de `/proc/stat`.
2. Ejecuta secuencialmente la lectura de CPU, RAM, disco, temperaturas SoC y RP1, tacómetro RPM, nivel térmico del ventilador, throttling, uptime e IP.
3. Devuelve una instancia inmutable de `SystemHealth`.

### Recuperación ante fallos
- Cada lector individual encapsula su acceso con bloques `try/except` específicos para `OSError`, `ValueError`, etc. Si una métrica opcional (como el ventilador o la sonda RP1) no está presente, devuelve `None` en lugar de abortar la ejecución completa.

---

## 4. Puntos de entrada

- `SystemCollector(force_mock: bool = False)`: Inicialización del colector.
- `SystemCollector.collect() -> SystemHealth`: Muestreo instantáneo de todas las variables del sistema.

---

## 5. Dependencias

### Dependencias entrantes
- `src/main.py`: Demonio orquestador.
- `tests/test_system.py`: Pruebas unitarias de adquisición y modo mock.

### Dependencias salientes
- Librería estándar de Python: `os`, `re`, `socket`, `subprocess`, `time`.
- `src/collectors/base.py`: Clase abstracta base.
- `src/models.py`: Dataclass `SystemHealth`.
- Sistema de archivos virtual Linux: `/proc/stat`, `/proc/meminfo`, `/proc/uptime`, `/sys/class/thermal/`, `/sys/devices/platform/cooling_fan/hwmon/hwmon2/`.

---

## 6. Configuración

| Parámetro | Valor por defecto | Efecto / Comportamiento |
| :--- | :--- | :--- |
| `force_mock` | `False` | Fuerza la emisión de métricas sintetizadas sin consultar `/proc` ni sysfs. |

---

## 7. Trampas conocidas

- **TR-005 (Throttling Boot Bitmask)**: En arranques de Raspberry Pi 5 con SSD USB 3.0 y Hailo-8, `vcgencmd get_throttled` reporta `0x50000` indicando eventos pasados durante el arranque (bits 16 y 18), mientras que los bits activos (0 a 3) permanecen a 0. El colector reporta la máscara exacta para evaluación histórica en backend.
- La lectura de RPM del ventilador sólo devuelve datos si el ventilador está girando activamente; a 0 RPM o apagado, el sensor puede retornar 0 o no responder.

---

## 8. Tests que lo cubren

- [x] `tests/test_system.py::TestSystemCollector.test_collect_auto`: Ejecuta el colector en el entorno actual verificando que no lanza excepciones no controladas.
- [x] `tests/test_system.py::TestSystemCollector.test_collect_mock`: Valida que los datos simulados cumplan las restricciones de rango de temperatura, CPU, RAM y disco.

---

## 9. Pendiente real

- [ ] Ninguna tarea pendiente en este colector.

---
> Creado: 2026-09-14 · Última revisión: 2026-09-14
