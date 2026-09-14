"""Plantilla de configuración de entorno para el monitor de energía de Raspberry Pi 5.

Copia este archivo a 'src/env.py' y adapta los valores según tu infraestructura:
    cp src/env.example.py src/env.py
"""

# Configuración de API V2
API_BASE_URL: str = "https://api.tu-servidor.com/api/v2"
API_AUTH_TOKEN: str = "tu_token_sanctum_aqui"

# Identificador numérico del dispositivo en la API (hardware_device_id)
HARDWARE_DEVICE_ID: int = 7

# Intervalos de muestreo de hardware y reporte a la API (en segundos)
# SAMPLING_INTERVAL_SECONDS: Frecuencia de lectura en memoria RAM (Zero-Disk Wear)
# REPORT_INTERVAL_SECONDS: Ventana de agregación y envío a la API (ej. 300.0 = 5 min)
SAMPLING_INTERVAL_SECONDS: float = 10.0
REPORT_INTERVAL_SECONDS: float = 300.0

# Monitorización de módulos opcionales
ENABLE_HAILO8: bool = False  # Activar (True) si el módulo Hailo-8 M.2 AI está instalado y en uso

