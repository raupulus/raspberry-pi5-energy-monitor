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
- **Estado**: Aprobada
- **Contexto**: El módulo M.2 de Hailo-8 carece de sensor de derivación (shunt resistor DVM) propio en su PCB.
- **Decisión**: Estimar el impacto energético del acelerador mediante el incremento diferencial de potencia en los raíles `3V3_SYS` y `1V8_SYS` del PMIC DA9091 (que pasa de ~0.5 W en reposo a ~3.5–5.0 W en inferencia), complementado con la lectura de temperatura interna del chip (sensores TS0 y TS1 vía `hailo_platform`).
- **Consecuencias**: No se requiere hardware externo de medición para monitorear la NPU.

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13

