# Catálogo de Comandos (commands.md)

Este documento contiene los comandos verificados disponibles en el entorno del repositorio, así como los comandos previstos para las siguientes fases.

---

## 1. Gestión del Entorno Virtual (Python 3.14)

### Comprobar versión de Python activa
```bash
.venv/bin/python --version
# Salida verificada: Python 3.14.7
```

### Activar el entorno virtual
```bash
source .venv/bin/activate
```

---

## 2. Configuración Local

### Inicializar archivo de variables de entorno
```bash
cp src/env.example.py src/env.py
```

---

## 3. Comandos de Inspección de Hardware (Raspberry Pi 5)

> ⚠️ Nota: Comandos dependientes de hardware físico Raspberry Pi 5 y utilidades `libraspberrypi-bin` (`vcgencmd`). En entornos de desarrollo ajenos requieren mocks.

### Lectura ADC del PMIC DA9091 (Voltajes y Corrientes por Raíl)
```bash
vcgencmd pmic_read_adc
```

### Temperatura de SoC y Southbridge RP1
```bash
# Vía firmware (CPU SoC)
vcgencmd measure_temp

# Vía sysfs (CPU SoC en miligrados)
cat /sys/class/hwmon/hwmon0/temp1_input

# Vía sysfs (RP1 Southbridge en miligrados)
cat /sys/class/hwmon/hwmon1/temp1_input
```

### Diagnóstico de Subvoltaje y Throttling
```bash
vcgencmd get_throttled
```

---

## 4. Comandos de Desarrollo y Verificación (Pendientes de Implementación)

Los siguientes comandos corresponden al flujo de desarrollo futuro y se encuentran actualmente en estado `⚠️ sin verificar` hasta que se implementen sus scripts/módulos correspondientes:

### Ejecución de Pruebas Unitarias
```bash
# Previsto: Ejecución de la suite de tests
.venv/bin/python -m unittest discover tests
```

### Ejecución del Servicio de Monitorización
```bash
# Previsto: Entrada principal del demonio / servicio
.venv/bin/python -m src.main
```

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13

