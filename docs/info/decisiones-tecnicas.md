# Decisiones Técnicas (decisiones-tecnicas.md)

Registro histórico de decisiones deliberadas de arquitectura y diseño. Si una decisión se modifica, se añade una nueva entrada justificando el cambio; nunca se borran las decisiones pasadas sin dejar constancia.

---

### DT-001: Adopción de Python 3.14
- **Fecha**: 2026-09-13
- **Estado**: Aprobada y verificada
- **Contexto**: Se requiere un entorno moderno con soporte de tipado avanzado y rendimiento óptimo en Raspberry Pi 5.
- **Decisión**: Fijar la versión del entorno en Python 3.14 mediante `.python-version` y `.venv/`.
- **Consecuencias**: Todo el código debe ceñirse a la sintaxis y características soportadas por Python 3.14+.

---

### DT-002: Licenciamiento bajo GNU GPLv3
- **Fecha**: 2026-09-13
- **Estado**: Aprobada
- **Contexto**: Establecer los términos de distribución y modificación del software.
- **Decisión**: Utilizar la licencia GNU General Public License v3.0 (GPLv3).
- **Consecuencias**: Cualquier trabajo derivado distribuido debe mantener el carácter libre y de código abierto bajo la misma licencia.

---

### DT-003: Aislamiento de Secretos y Configuración en `src/env.py`
- **Fecha**: 2026-09-13
- **Estado**: Aprobada y verificada
- **Contexto**: El monitor se conectará a una API privada con tokens de autenticación y variará sus parámetros según el nodo.
- **Decisión**: Excluir `src/env.py` del control de versiones (`.gitignore`) y proveer `src/env.example.py` como plantilla de referencia commitada.
- **Consecuencias**: Ningún secreto, URL privada ni credencial debe commitearse. El repositorio se mantiene portable y seguro.

---

### DT-004: Soporte Modular Condicional para Acelerador Hailo-8
- **Fecha**: 2026-09-13
- **Estado**: Aprobada (Pendiente de implementación de hardware)
- **Contexto**: Algunas unidades de Raspberry Pi 5 contarán con el HAT M.2 y el módulo NPU Hailo-8, mientras que otras operarán de manera independiente.
- **Decisión**: Aislar las métricas del módulo Hailo-8 bajo el flag `ENABLE_HAILO8` en `src/env.py`. Si es `False`, el recolector no intentará inicializar drivers ni librerías del acelerador.
- **Consecuencias**: El núcleo del monitor de energía funcionará en cualquier Raspberry Pi 5 estándar sin requerir dependencias obligatorias de hardware extra.

---

### DT-005: Adopción del Protocolo de Documentación Técnica Viva `docs/`
- **Fecha**: 2026-09-13
- **Estado**: Aprobada y aplicada
- **Contexto**: Evitar desincronización entre código y documentación, carpetas vacías y enlaces rotos en clones limpios.
- **Decisión**: Estructurar la documentación viva en `docs/info/`, prohibir carpetas vacías, excluir del control de versiones el trabajo efímero (`/docs/planning/` y `/docs/auditorias/`), y exigir actualización de documentación en el mismo commit que el código.
- **Consecuencias**: Todo agente o desarrollador debe consultar y actualizar `docs/info/` y registrar el pie de versión y fecha correspondiente.

---

### DT-006: Política Zero-Disk Wear para Telemetría Continua
- **Fecha**: 2026-09-13
- **Estado**: Aprobada
- **Contexto**: El muestreo continuo de métricas (cada 5–15 segundos) escribiendo registros en SSD o MicroSD acorta drásticamente la vida útil del medio de almacenamiento flash.
- **Decisión**: Mantener el búfer de muestras y agregaciones estadísticas estrictamente en memoria RAM (`collections.deque` o memoria compartida `/dev/shm`). Queda prohibida la escritura en disco en los bucles periódicos de recolección.
- **Consecuencias**: El sistema preserva el almacenamiento físico de la RPi 5. Si ocurre un apagón repentino, solo se pierden las muestras no enviadas de la ventana de agregación en curso.

---

### DT-007: Medición Indirecta de Potencia para Acelerador Hailo-8
- **Fecha**: 2026-09-13
- **Estado**: Modificada por DT-011
- **Contexto**: El módulo M.2 de Hailo-8 carece de sensor de derivación (shunt resistor DVM) propio en su PCB.
- **Decisión**: Estimar el impacto energético del acelerador mediante el incremento diferencial de potencia en los raíles `3V3_SYS` y `1V8_SYS` del PMIC DA9091 (que pasa de ~0.5 W en reposo a ~3.5–5.0 W en inferencia), complementado con la lectura de temperatura interna del chip (sensores TS0 y TS1 vía `hailo_platform`).
- **Consecuencias**: Provee una magnitud continua para el módulo M.2 sin requerir hardware externo de medición.

---

### DT-008: Cero Dependencias de Terceros en Tiempo de Ejecución (Pure Python Standard Library)
- **Fecha**: 2026-09-14
- **Estado**: Aprobada y verificada
- **Contexto**: Minimizar el footprint de memoria en Raspberry Pi 5 y evitar incompatibilidades de paquetes o necesidad de compilar ruedas C en Raspberry Pi OS.
- **Decisión**: Implementar toda la lógica del demonio, colectores, búfer y cliente HTTP utilizando exclusivamente la biblioteca estándar de Python (`urllib.request`, `collections`, `dataclasses`, `subprocess`, `os`, `socket`, `time`). El SDK opcional `hailo_platform` se carga de forma perezosa mediante `importlib`/`try-except`.
- **Consecuencias**: El monitor es inmediatamente portable, arranca al instante y tiene un consumo de memoria inferior a 15 MB de RAM.

---

### DT-009: Aplazamiento de Monitorización de Ventilador para HAT Hailo-8
- **Fecha**: 2026-09-14
- **Estado**: Aprobada
- **Contexto**: La inspección física en hardware real reveló que el HAT portador del módulo Hailo-8 M.2 carece de sensor tacómetro expuesto en el Device Tree (`cooling_device` o `hwmon`). El único ventilador controlado por el kernel es el Active Cooler de la Raspberry Pi 5 (`hwmon2`).
- **Decisión**: Reportar el ventilador únicamente en el Canal 0 (`loads[0].fan`). Omitir el campo `fan` en el Canal 1 (`loads[1]`) y aplazar su monitorización a `docs/future/hailo8-fan.md` hasta que se incorpore un HAT con tacómetro o control GPIO mapeado.
- **Consecuencias**: El payload cumple estrictamente con el contrato de API V2 sin inventar lecturas ficticias.

---

### DT-010: Cómputo de Duración Continua de Ventana (`duration`)
- **Fecha**: 2026-09-24
- **Estado**: Aprobada y verificada
- **Contexto**: El cálculo original `duration = last_sample_time - first_sample_time` (~290–295 s) ignoraba el intervalo de tiempo entre la última muestra de una ventana y la primera de la siguiente (~10 s por subida). En producción real el día acumulaba 83.540 s de duración en vez de 86.400 s (~48 minutos de consumo perdidos diariamente), ocasionando una subestimación del 3,3 % en la energía calculada por la API (`power × duration`).
- **Decisión**: Calcular la duración como el tiempo continuo transcurrido desde el inicio de la ventana actual (`duration = max(1, int(round(current_time - self._window_start_time)))`), actualizando `_window_start_time = current_time` en cada `flush()`.
- **Consecuencias**: Cobertura temporal exacta de 86.400 s/día sin huecos ni solapes entre ventanas contiguas. Se elimina la lógica frágil dependiente de muestras individuales.

---

### DT-011: Desacoplamiento de Cargas entre Canal 0 (RPi Neta) y Canal 1 (Hailo-8) sin Duplicidad
- **Fecha**: 2026-09-24
- **Estado**: Aprobada y verificada
- **Contexto**: La API V2 cuenta con dos entidades de hardware independientes dadas de alta: Canal 0 (Raspberry Pi 5) y Canal 1 (Hailo-8 M.2). Anteriormente, el Canal 0 incluía la suma de todos los 12 raíles del PMIC (~2.78 W) y el Canal 1 reportaba de nuevo los raíles `3V3_SYS` + `1V8_SYS` (~0.50 W). Al sumarse ambas cargas en la API, se producía una doble contabilidad (+15% de energía fantasma).
- **Decisión**: Mantener ambas entidades activas en el array `loads` mediante desacoplamiento complementario:
  - **Canal 1 (Hailo-8)**: Reporta la potencia estimada en PCIe (~0.50 W en reposo) y temperatura del silicio.
  - **Canal 0 (Raspberry Pi 5)**: Reporta la potencia neta de la placa deduciendo el consumo del Hailo (`P_rpi = max(0.0, P_total_pmic - P_hailo)`).
- **Consecuencias**: Ambas entidades en la API se mantienen vivas y alimentadas con métricas individuales. La suma agregada de ambas cargas (`P_rpi + P_hailo`) coincide exactamente con el consumo físico total medido por el PMIC DA9091, eliminando la duplicidad.

---
> Creado: 2026-09-13 · Última revisión: 2026-09-24
