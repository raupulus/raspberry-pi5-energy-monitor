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
  - PMIC (Energía / Voltaje / Corriente) [⚠️ sin verificar]
  - Sistema (CPU, Temp, RAM) [⚠️ sin verificar]
  - Hailo-8 (Opcional) [⚠️ sin verificar]
             │
             ▼
[ Agregador y Búfer Local ]
             │
             ▼
[ Cliente de API / Despachador ]
             │
             ▼
    ( API Remota Propia )
```

### 2.2. Aislamiento de Módulos Opcionales
- El colector del módulo Hailo-8 se inicializa de forma condicional evaluando la variable de entorno `ENABLE_HAILO8` en `src/env.py`.
- Si `ENABLE_HAILO8 = False` o el hardware/driver no está presente, el sistema funciona de manera autónoma sin degradar la monitorización principal.

### 2.4. Política Zero-Disk Wear y Ventanas de Agregación
- Las muestras de energía y salud se almacenan **únicamente en memoria RAM** (`collections.deque`).
- Frecuencia de muestreo: cada 5–15 segundos.
- Agregación estadística: cálculo de métricas (`avg`, `min`, `max`) en ventanas de 5–10 minutos antes de la transmisión HTTP a la API.
- Se prohíbe la persistencia recurrente en SSD o tarjeta SD para evitar degradación prematura del almacenamiento flash.

---

## 3. Estado de Verificación contra Hardware Real

- **PMIC de Raspberry Pi 5 (DA9091)**: `⚠️ sin verificar en este entorno` (especificado en [`hardware.md`](hardware.md)).
- **Hailo-8 PCIe driver / SDK**: `⚠️ sin verificar en este entorno` (especificado en [`hardware.md`](hardware.md)).
- **API Externa**: `⚠️ sin verificar con petición real` (especificado en [`apis/api-v2.md`](apis/api-v2.md)).

---
> Creado: 2026-09-13 · Última revisión: 2026-09-13

