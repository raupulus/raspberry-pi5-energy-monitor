# Instrucciones para Agentes de IA

Este repositorio contiene el sistema de monitorización continua de energía, consumo y métricas de sistema para **Raspberry Pi 5**, con envío periódico a una API propia y soporte modular (p. ej., módulo Hailo-8 AI NPU).

---

## 1. Directrices de Desarrollo

1. **Entorno y Versión de Python**:
   - Python 3.14 (`.venv/`).
   - Usar tipado estricto (`typing`) y código limpio/modular.

2. **Convenciones de Idioma**:
   - **Español**: Documentación, comentarios y textos de cara al usuario.
   - **Inglés**: Identificadores de código (clases, funciones, variables), nombres de ficheros, rutas y mensajes de log. Excepción: campos que devuelva una API externa, que se leen tal como vengan.

3. **Atribución y Firmas**:
   - Atribución cuando aplique: nick `@raupulus`, email `public@raupulus.dev`.
   - **Sin firmas de agente**: Prohibido añadir firmas de IA en commits, PRs o documentación (nada de `Co-Authored-By`, «Generated with…» ni identificadores de sesión).

4. **Configuración y Secretos**:
   - La configuración sensible y flags de entorno se gestionan a través de `src/env.py` (ignorado por git).
   - Mantener siempre actualizado `src/env.example.py` con las variables requeridas (URLs de API, tokens, frecuencia de muestreo, `ENABLE_HAILO8`, etc.).
   - No comitear credenciales, tokens ni archivos de configuración con datos reales.

5. **Compatibilidad y Hardware**:
   - El código principal correrá en una **Raspberry Pi 5**.
   - Lectura de sensores mediante interfaces del kernel (`/sys/class/hwmon/`, `/sys/devices/platform/`), PMIC DA9091 de Raspberry Pi 5.
   - Soporte opcional para acelerador de IA Hailo-8 (M.2 PCIe), controlado mediante el flag `ENABLE_HAILO8` en `src/env.py`.

---

## 2. Estructura Real del Repositorio

```text
.
├── .agentes -> .agents
├── .agents/                      # Instrucciones y prompts para agentes
├── .claude -> .agents            # Enlace simbólico de compatibilidad
├── .env.example                  # Plantilla de variables de entorno generales
├── .gitignore                    # Exclusiones de git (incluye src/env.py, planning y auditorias)
├── .python-version               # Versión de Python fijada (3.14)
├── AGENTS.md                     # Este archivo (fuente de directrices residentes)
├── CLAUDE.md -> AGENTS.md        # Enlace simbólico hacia AGENTS.md
├── LICENSE                       # Licencia GNU GPLv3
├── README.md                     # Presentación del proyecto
├── docs/
│   ├── apis/                     # Documentación oficial destilada de APIs externas
│   │   └── api-v2/               # Backend API V2 (contrato oficial y fuentes originales)
│   │       ├── 00-fundamentos.md
│   │       ├── ERRATAS.md
│   │       ├── LIMITACIONES.md
│   │       ├── README.md
│   │       ├── energy.md
│   │       ├── hardware.md
│   │       └── src/
│   └── info/                     # Documentación técnica VIVA del proyecto
│       ├── _MODULE_TEMPLATE.md   # Plantilla obligatoria para documentar módulos
│       ├── COMPONENTS.md         # Catálogo de componentes del sistema
│       ├── DESIGN.md             # Principios y arquitectura del sistema
│       ├── README.md             # Índice maestro de documentación técnica
│       ├── apis/                 # Integración interna de APIs
│       │   └── api-v2.md
│       ├── commands.md           # Comandos de entorno y ejecución
│       ├── decisiones-tecnicas.md# Registro de decisiones deliberadas
│       └── hardware.md           # Especificación técnica de hardware y telemetría
├── src/                          # Código fuente de la aplicación
│   └── env.example.py            # Plantilla de configuración y secretos locales
└── tests/                        # Pruebas unitarias y de integración
```

---

## 3. Protocolo Residente de Documentación (`docs/`)

Cualquier agente o desarrollador que trabaje en este repositorio debe aplicar estrictamente estas reglas:

### Jerarquía de Verdad
$$\text{Código Real} > \text{docs/info/} > \text{AGENTS.md} > \text{el resto}$$
*(Nota: `docs/planning/`, `docs/future/` y `docs/auditorias/` NUNCA son fuente de verdad del estado actual).*

### Reglas Permanentes
1. **Documentar es parte de la tarea**: Ninguna tarea se considera finalizada si su documentación no se actualiza **en el mismo commit que el código**.
2. **Inspección previa (Paso 0)**: Antes de escribir documentación, inspeccionar el código real. Lo no comprobado contra código o hardware se marca como `⚠️ sin verificar`. Prohibido inventar apartados para rellenar plantillas.
3. **Discrepancia detectada**: Si hay contradicción entre documentación y código, se subsana en el commit en que se detecte.
4. **Ciclo de vida de módulos**:
   - Modificas un módulo $\rightarrow$ actualizas su `.md`.
   - Creas un módulo $\rightarrow$ lo creas a partir de `_MODULE_TEMPLATE.md` e indexas en `docs/info/README.md` y en este `AGENTS.md`.
   - Eliminas un módulo $\rightarrow$ eliminas su `.md` y lo remueves de todos los índices.
5. **Pie de página obligatorio**: Todo archivo bajo `docs/` finaliza con:
   ```markdown
   ---
   > Creado: YYYY-MM-DD · Última revisión: YYYY-MM-DD
   ```
   *(La fecha de creación no se modifica; la de revisión se actualiza con cada edición).*
6. **Planificación y auditorías efímeras ([NO GIT])**:
   - `docs/planning/` y `docs/auditorias/` son locales de un único desarrollador y están en `.gitignore`.
   - Nada versionado puede enlazar a estas rutas.
   - Ciclo: crear $\rightarrow$ trabajar $\rightarrow$ verificar $\rightarrow$ promocionar lo duradero $\rightarrow$ borrar archivo efímero.
   - Promociones: lógica de módulo a `docs/info/<modulo>.md`, decisiones a `decisiones-tecnicas.md`, trampas duraderas a la tabla de `AGENTS.md`, ideas aplazadas a `docs/future/`.
7. **Lectura dirigida**:
   - Al tocar un módulo, leer únicamente su `docs/info/<modulo>.md`.
   - Si se toca frontend/UI, añadir `DESIGN.md` y `COMPONENTS.md`.
   - Si se toca una API externa, consultar `docs/apis/<api>/` (`README.md` $\rightarrow$ `00-fundamentos.md` + `ERRATAS.md` + `LIMITACIONES.md` $\rightarrow$ dominio).
   - No leer innecesariamente otros módulos ni carpetas efímeras.
8. **Sin carpetas vacías**: Solo se crean directorios cuando contengan archivos reales.

### Índice Maestro de `docs/info/`
- [README.md](docs/info/README.md): Índice maestro de módulos y estado.
- [_MODULE_TEMPLATE.md](docs/info/_MODULE_TEMPLATE.md): Plantilla oficial de documentación de módulo.
- [DESIGN.md](docs/info/DESIGN.md): Arquitectura y modelo de datos conceptual.
- [COMPONENTS.md](docs/info/COMPONENTS.md): Catálogo y estado de implementación de componentes.
- [hardware.md](docs/info/hardware.md): Especificación técnica de hardware, PMIC DA9091, 12 raíles, Hailo-8, fórmulas y sensores térmicos.
- [commands.md](docs/info/commands.md): Catálogo de comandos verificados.
- [decisiones-tecnicas.md](docs/info/decisiones-tecnicas.md): Registro histórico de decisiones técnicas.

---

## 4. Tabla de Trampas Conocidas

| ID | Componente / Hardware | Trampa / Particularidad | Mitigación / Solución |
| :--- | :--- | :--- | :--- |
| **TR-001** | Raspberry Pi 5 PMIC | Las lecturas de consumo del PMIC DA9091 dependen de rutas `/sys/class/hwmon/` específicas de Pi 5 que no existen en Pi 4 ni en macOS. | No asumir rutas fijas; implementar autodetección de rutas hwmon y mocks para desarrollo fuera de la RPi 5. |
| **TR-002** | Módulo Hailo-8 | Los drivers y la utilidad `hailort` pueden no estar instalados o fallar si el módulo M.2 no tiene alimentación o el firmware no está actualizado. | Proteger cualquier llamada con el flag `ENABLE_HAILO8 = False` por defecto y manejo de excepciones de hardware. |
| **TR-003** | Documentación efímera | Enlazar accidentalmente desde `docs/info/` o `README.md` hacia `docs/planning/` o `docs/auditorias/` romperá enlaces en clones limpios. | Mantener ambas rutas en `.gitignore` y no enlazar nunca desde archivos versionados. |
| **TR-004** | API V2 Hardware Auth | En `PUT /hardware/devices/{device}/status`, la documentación oficial exige `hardware:write` en el encabezado pero lista `403 token sin la ability energy:write` en los errores. Además, `device:{id}` responde 422 en PUT en lugar de 403. | Emitir tokens con ambas abilities (`hardware:write` y `energy:write`) y manejar 422 como rechazo por pertenencia o validación. |
| **TR-005** | Throttling Boot Bitmask | En el arranque simultáneo de SSD USB 3.0 + Hailo-8 + CPU, `get_throttled` registra la bandera transitoria `0x50000` (bits históricos 16 y 18), pero el estado en régimen permanente es 0. | Distinguir bits 0..3 (estado activo en tiempo real) de los bits 16..19 (histórico de arranque). No alarmar si los bits 0..3 son 0. |
| **TR-006** | Shunt de Hailo-8 | La plaquita M.2 de Hailo-8 no incorpora sensor de derivación (shunt DVM) dedicado. | Monitorear el incremento de potencia en los raíles `3V3_SYS` y `1V8_SYS` del PMIC, junto con la temperatura interna de silicio TS0/TS1 vía `hailo_platform`. |


---

## 5. Checklist Obligatorio Antes de Terminar Cualquier Tarea

- [ ] Documentación del módulo tocado actualizada en el MISMO commit.
- [ ] Fechas de «Última revisión» al día en todos los archivos modificados bajo `docs/`.
- [ ] Módulos nuevos indexados en `docs/info/README.md` y en `AGENTS.md`.
- [ ] Módulos eliminados fuera de TODOS los índices.
- [ ] Ningún archivo versionado enlaza a `docs/planning/` ni a `docs/auditorias/`.
- [ ] `docs/planning/` y `docs/auditorias/` siguen en `.gitignore`.
- [ ] Lo duradero de planificaciones o auditorías cerradas promocionado, y el archivo efímero borrado.
- [ ] Checklists `[x]` verificados funcionando y cumpliendo contra código real (no asumidos).
- [ ] Árbol de estructura de `AGENTS.md` refleja fielmente los directorios reales.
