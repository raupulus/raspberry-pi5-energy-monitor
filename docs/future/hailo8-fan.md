# Propuesta Aplazada: Telemetría de Ventilador para Módulo Hailo-8

Idea decidida pero aplazada para futuras versiones del monitor.

---

## 1. Contexto y Estado Actual

- En la revisión de hardware del 2026-09-14, se verificó en la Raspberry Pi 5 que el único ventilador registrado en el kernel es el *Active Cooler* principal (`/sys/devices/platform/cooling_fan/hwmon/hwmon2`), mapeado en el Canal 0.
- El módulo Hailo-8 M.2 no dispone de tacómetro ni pines de ventilador en el chip PCIe.
- Cualquier ventilador montado en el HAT actual opera por alimentación directa sin señal de retorno al sistema operativo o sin overlay cargado en el Device Tree.

---

## 2. Requisitos para Reactivar en el Futuro

1. Conexión de la señal del tacómetro (hilo azul/amarillo) a un pin GPIO libre (ej. GPIO 14, 18).
2. Declarar en `/boot/firmware/config.txt` el overlay correspondiente:
   ```ini
   dtoverlay=gpio-fan,gpiopin=<GPIO_NUM>,temp=...
   ```
3. Verificar la aparición del nuevo dispositivo en `/sys/class/thermal/cooling_device1` o en `/sys/class/hwmon/`.
4. Incorporar la lectura en el colector de Hailo-8 y reportar el campo `fan` en el Canal 1 (`loads[1]`).

---
> Creado: 2026-09-14 · Última revisión: 2026-09-14
