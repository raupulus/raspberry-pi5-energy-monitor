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

## 4. Comandos de Desarrollo y Verificación (✅ Verificados)

### Ejecución de la Suite Completa de Pruebas Unitarias
```bash
.venv/bin/python -m unittest discover -s tests -p "test_*.py" -v
# 22 tests ejecutados con éxito
```

### Ejecución de Pruebas por Módulo
```bash
.venv/bin/python -m unittest tests/test_pmic.py -v
.venv/bin/python -m unittest tests/test_system.py -v
.venv/bin/python -m unittest tests/test_hailo.py -v
.venv/bin/python -m unittest tests/test_aggregator.py -v
.venv/bin/python -m unittest tests/test_api_client.py -v
.venv/bin/python -m unittest tests/test_main.py -v
```

### Ejecución Local con Mocks (Desarrollo fuera de la RPi 5)
```bash
.venv/bin/python -m src.main --once --dry-run --mock
```

### Ejecución en Raspberry Pi 5 (Prueba en vivo de una pasada)
```bash
python3 -m src.main --once --dry-run
```

---

## 5. Gestión del Servicio Systemd (Raspberry Pi 5)

### Instalación de la unidad de servicio
```bash
sudo cp systemd/energy-monitor.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### Habilitar e iniciar servicio continuo
```bash
sudo systemctl enable --now energy-monitor.service
```

### Comprobar estado e inspeccionar logs en tiempo real
```bash
sudo systemctl status energy-monitor.service
sudo journalctl -u energy-monitor.service -f
```

---
> Creado: 2026-09-13 · Última revisión: 2026-09-14

