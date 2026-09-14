# Diseño del Sistema (DESIGN.md)

Este documento describe los principios arquitectónicos, el modelo conceptual y las directrices técnicas del monitor de energía y consumo para Raspberry Pi 5.

---

## 1. Objetivos del Sistema

1. **Monitorización Continua y de Bajo Impacto**:
   - Recopilar métricas eléctricas y de rendimiento de la Raspberry Pi 5 con una huella mínima de CPU y memoria.
2. **Soporte Modular de Hardware**:
   - Soporte principal: PMIC y sensores nativos de la Raspberry Pi 5.
   - Soporte modular opcional: Acelerador de IA Hailo-8 (conectado vía PCIe / HAT M.2), integrable mediante variable de configuración.
3. **Transmisión Fiable a API Externa**:
   - Envío periódico estructurado de paquetes de telemetría hacia una API propia.
   - Resiliencia ante desconexiones de red (búfer local y reintentos sin pérdida descontrolada de datos).
4. **Seguridad y Aislamiento de Secretos**:
   - Separación estricta entre código base y credenciales/configuración local mediante `src/env.py`.

---

## 2. Principios Arquitectónicos

### 2.1. Arquitectura de Tubería (Pipeline) Unidireccional

El flujo de información sigue un pipeline lineal desacoplado:

```text
[ Colectores de Métricas ]
  - PMIC (Energía / Voltaje / Corriente) [✅ Verificado]
  - Sistema (CPU, Temp, RAM, RPM Fan) [✅ Verificado]
  - Hailo-8 (Opcional) [✅ Verificado]
             │
             ▼
[ Agregador y Búfer en RAM (Zero-Disk Wear) ] [✅ Verificado]
             │
             ▼
[ Cliente de API V2 / Transmisión Resiliente ] [✅ Verificado]
             │
             ▼
    ( API Remota Propia ) [✅ Verificado HTTP 201]
```

### 2.2. Aislamiento de Módulos Opcionales
- El colector del módulo Hailo-8 se inicializa de forma condicional evaluando la variable de entorno `ENABLE_HAILO8` en `src/env.py`.
- Si `ENABLE_HAILO8 = False` o el hardware/driver no está presente, el sistema funciona de manera autónoma sin degradar la monitorización principal (omitiendo el Canal 1 del array `loads`).

### 2.4. Política Zero-Disk Wear y Ventanas de Agregación
- Las muestras de energía y salud se almacenan **únicamente en memoria RAM** (`collections.deque`).
- Frecuencia de muestreo: cada 10 segundos.
- Agregación estadística: cálculo de promedios en ventanas de 300 segundos (5 minutos) antes de la transmisión HTTP a la API.
- Se prohíbe la persistencia recurrente en SSD o tarjeta SD para evitar degradación prematura del almacenamiento flash.

---

## 3. Estado de Verificación contra Hardware Real

- **PMIC de Raspberry Pi 5 (DA9091)**: `✅ Verificado` en nodo físico mediante `vcgencmd pmic_read_adc` (especificado en [`hardware.md`](hardware.md) y [`pmic.md`](pmic.md)).
- **Hailo-8 PCIe driver / SDK**: `✅ Verificado` en nodo físico con chip de silicio a ~36.6 °C (especificado en [`hardware.md`](hardware.md) y [`hailo.md`](hailo.md)).
- **API Externa**: `✅ Verificado` con peticiones reales continuas a `POST /energy/readings` recibiendo HTTP 201 Created (especificado en [`apis/api-v2.md`](apis/api-v2.md)).

---
> Creado: 2026-09-13 · Última revisión: 2026-09-14

