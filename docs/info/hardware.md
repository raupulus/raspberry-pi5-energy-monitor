# Especificación de Hardware y Telemetría (`docs/info/hardware.md`)

Este documento detalla la arquitectura eléctrica, los sensores de hardware, las fórmulas de cálculo de energía y las particularidades de monitorización en **Raspberry Pi 5** y el acelerador **Hailo-8 M.2**.

---

## 1. Arquitectura de Hardware Eléctrico

- **Alimentación de Entrada**: Cargador Oficial Raspberry Pi 27W USB-C PD (5.1V / 5.0A).
- **Controlador de Energía (PMIC)**: Renesas DA9091.
- **Capacidad de Medición**: El PMIC DA9091 incorpora un convertidor analógico-digital (ADC) multicanal que muestrea de manera continua voltaje ($V$) y corriente ($A$) de forma independiente en 12 líneas de alimentación internas.
- **Aceleradora Hailo-8 M.2 (26 TOPS)**:
  - Conectada vía HAT M.2 PCIe.
  - No dispone de sensor shunt (DVM) dedicado en la placa M.2.
  - Se alimenta de los raíles `3V3_SYS` y `1V8_SYS` de la Raspberry Pi.
  - Consumo dinámico: ~0.5 W en reposo hasta ~3.5–5.0 W en inferencias de visión artificial, reflejado directamente en dichos raíles.

---

## 2. Raíles de Alimentación Monitoreados

Comando de lectura del firmware:
```bash
vcgencmd pmic_read_adc
```

| Raíl | Tipo | Componente Alimentado | Valores Típicos en Reposo |
| :--- | :--- | :--- | :--- |
| `VDD_CORE` | Voltaje / Corriente | Núcleos CPU Cortex-A76 y GPU VideoCore VII | ~0.90 V / ~1.45 A (~1.31 W) |
| `3V3_SYS` | Voltaje / Corriente | Bus 3.3V, pines GPIO y módulo M.2 Hailo-8 | ~3.30 V / ~0.07 A (~0.24 W) |
| `1V8_SYS` | Voltaje / Corriente | Bus 1.8V del sistema y lógica PCIe | ~1.80 V / ~0.17 A (~0.31 W) |
| `1V1_SYS` | Voltaje / Corriente | Lógica de conmutación interna 1.1V | ~1.10 V / ~0.24 A (~0.27 W) |
| `0V8_SW` | Voltaje / Corriente | Lógica de conmutación interna 0.8V | ~0.80 V / ~0.32 A (~0.25 W) |
| `3V7_WL_SW` | Voltaje / Corriente | Radio Wi-Fi 802.11ac y Bluetooth 5.0 | ~3.70 V / ~0.10 A (~0.39 W) |
| `DDR_VDD2` | Voltaje / Corriente | Memoria RAM física LPDDR4X (8 GB) | ~1.10 V / ~0.01 A (~0.01 W) |
| `DDR_VDDQ` | Voltaje / Corriente | Líneas I/O de memoria LPDDR4X | ~0.60 V / ~0.00 A |
| `HDMI` | Voltaje / Corriente | Puertos micro-HDMI | ~5.08 V / ~0.02 A (~0.10 W) |
| `EXT5V` | Solo Voltaje | Voltaje de entrada real desde USB-C | **~5.06 V a 5.08 V** |
| `0V8_AON` | Voltaje / Corriente | Dominio Always-On / Standby | ~0.80 V / ~3.4 mA |

---

## 3. Fórmulas de Cálculo de Potencia

1. **Potencia individual por raíl**:
   $$P_{\text{raíl}} = V_{\text{raíl}} \times I_{\text{raíl}} \quad (\text{Vatios})$$

2. **Potencia total interna disipada**:
   $$P_{\text{total}} = \sum P_{\text{raíles}} \quad (\text{Vatios})$$
   *(En reposo oscila entre 2.6 W y 2.9 W)*.

3. **Corriente equivalente consumida en la entrada USB-C**:
   $$I_{\text{USB-C}} = \left(\frac{P_{\text{total}}}{V_{\text{EXT5V}}}\right) \times 1000 \quad (\text{mA})$$
   *(En reposo oscila entre 520 mA y 570 mA a 5.08 V)*.

---

## 4. Sensores Térmicos Multizona

1. **SoC CPU (BCM2712 Cortex-A76)**:
   - Firmware: `vcgencmd measure_temp`
   - Sysfs: `/sys/class/hwmon/hwmon0/temp1_input` (en miligrados Celsius, dividir entre 1000).
2. **Southbridge RP1 (Controlador de I/O, Ethernet, USB)**:
   - Sysfs: `/sys/class/hwmon/hwmon1/temp1_input` (en miligrados Celsius, dividir entre 1000).
3. **Acelerador NPU Hailo-8 (Sensores internos TS0 y TS1)**:
   - Vía SDK oficial `hailo_platform`:
     ```python
     from hailo_platform import Device

     with Device("0001:01:00.0") as target:
         t = target.control.get_chip_temperature()
         ts0 = t.ts0_temperature
         ts1 = t.ts1_temperature
     ```
4. **Ventilador del Sistema (Raspberry Pi 5 Active Cooler / Case Fan)**:
   - Nivel PWM / Estado de refrigeración (0 a 4): `/sys/class/thermal/cooling_device0/cur_state`
   - Tacómetro en tiempo real (RPM): `/sys/devices/platform/cooling_fan/hwmon/hwmon2/fan1_input` (verificado en hardware físico: ~3785 RPM).
   - Nivel de modulación PWM: `/sys/devices/platform/cooling_fan/hwmon/hwmon2/pwm1` (0 a 255).
   - Mapeo en API: Campo `fan` en Canal 0 (`loads[0]`).
   *(Nota: La monitorización de un ventilador secundario para el HAT Hailo-8 queda aplazada; ver `docs/future/hailo8-fan.md`)*.

---

## 5. Diagnóstico de Salud Eléctrica (`get_throttled`)

El comando `vcgencmd get_throttled` devuelve una máscara de bits hexadecimal con el estado de subvoltaje y estrangulamiento térmico:

### Máscara de Bits
- **Bits 0..3 (Estado Actual en Tiempo Real)**:
  - `0x1` (bit 0): Subvoltaje activo actualmente ($< 4.63\text{ V}$).
  - `0x2` (bit 1): Frecuencia ARM limitada activamente.
  - `0x4` (bit 2): Throttling por temperatura activo.
  - `0x8` (bit 3): Límite térmico alcanzado actualmente.
- **Bits 16..19 (Registro Histórico desde el Arranque)**:
  - `0x10000` (bit 16): Ha ocurrido subvoltaje desde el arranque.
  - `0x20000` (bit 17): Se ha limitado frecuencia ARM desde el arranque.
  - `0x40000` (bit 18): Ha ocurrido throttling desde el arranque.
  - `0x80000` (bit 19): Se ha alcanzado límite térmico desde el arranque.

> **Trampa de este nodo (TR-005)**: Durante el encendido, el pico de arranque concurrente del disco SSD USB 3.0 de 1TB junto con la Hailo-8 y la CPU genera un evento transitorio que fija las banderas históricas en `0x50000`. Mientras los bits 0..3 permanezcan en `0`, la salud en régimen estacionario es 100% óptima.

---

## 6. Política de Almacenamiento Zero-Disk Wear

- **Memoria RAM exclusiva**: El servicio recolector retiene las muestras y cálculos únicamente en estructuras en memoria (`collections.deque` o memoria compartida `/dev/shm`).
- **Prohibición de I/O en disco durante muestreo**: No se escribirán registros de depuración ni lecturas crudas en el disco SSD ni en tarjeta MicroSD para evitar desgaste del almacenamiento.
- **Ventana de agregación**: Se toman muestras cada 5–15 segundos y se calcula el resumen estadístico (`avg`, `min`, `max`) en ventanas de 5 a 10 minutos antes de enviar a la API.

---

## 7. Estado de Verificación contra Entorno Actual

- Pruebas contra Raspberry Pi 5 física: `⚠️ sin verificar en entorno local` (este repositorio se desarrolla con soporte de mocks / abstracción para entornos de desarrollo macOS / Linux x86_64).

---
> Creado: 2026-09-13 · Última revisión: 2026-09-14

