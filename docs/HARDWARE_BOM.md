# Hardware Bill of Materials (BOM) & Mounting Guide
**Commercial Edge AI Fitness Coaching Appliance**  
**Target Platform:** Raspberry Pi 4B (4GB or 8GB)

---

## 1. Bill of Materials (BOM)

| Item # | Component | Recommended Model / Spec | Purpose | Est. Cost (USD) |
| :---: | :--- | :--- | :--- | :---: |
| 1 | **Single Board Computer** | Raspberry Pi 4 Model B (4GB or 8GB RAM) | Core application processor & inference engine | $55 - $75 |
| 2 | **Primary Camera** | Raspberry Pi Camera Module 3 (Wide-angle, 12MP, Sony IMX708, PDAF) | Zero-copy CSI-2 capture with hardware ISP autofocus | $35 |
| 3 | **Alternative Camera** | Logitech C920 / C922 USB 1080p Webcam | Standard UVC plug-and-play USB capture | $60 |
| 4 | **Touch Display** | 10.1" or 15.6" Capacitive Touchscreen (1080p / 720p, HDMI + USB touch) | Gym member kiosk interface & mirror feedback | $90 - $140 |
| 5 | **Thermal Management** | Aluminum Armor Heatsink Case with Dual 5V Fans or Pimoroni Fan SHIM | Sustains $<65^\circ\text{C}$ under 100% multi-core load | $15 |
| 6 | **Power Supply** | Official Raspberry Pi 15W USB-C Power Supply (5.1V / 3.0A) | Prevents undervoltage under peak CPU/GPU bursts | $12 |
| 7 | **Storage** | SanDisk Extreme Pro 64GB MicroSD (A2, V30, U3) or M.2 NVMe SSD via USB3 | Fast boot (<30s) and high-durability SQLite WAL logging | $18 - $35 |
| 8 | **Audio Output** | Waveshare USB Speaker / 3.5mm Powered Mini Soundbar | Local text-to-speech coaching cues | $15 |
| 9 | **Hardware Accelerator** *(Optional)* | Google Coral USB Accelerator (Edge TPU, 4 TOPS) | Offloads pose inference to 50+ FPS | $60 |
| **Total** | | | **Complete Standalone Commercial Kiosk Unit** | **~$280 - $370** |

---

## 2. Mounting & Installation Guidelines

### 2.1 Camera Placement
- **Mounting Height:** 1.2 to 1.4 meters (4 to 4.5 feet) from the gym floor.
- **Tilt Angle:** $0^\circ$ (level) or tilted slightly downward ($3^\circ$ to $5^\circ$) depending on floor distance.
- **User Distance:**
  - For standing Yoga poses & Lateral Raises: **2.0 to 2.8 meters** from lens.
  - For Push-ups & floor exercises: **1.8 to 2.4 meters** with camera oriented sideways.

### 2.2 Gym Lighting Requirements
- **Luminance:** Minimum 250 lux (standard gym lighting). Avoid direct backlighting from bright outdoor windows directly behind the user.
- **Contrast:** Maintain even ambient lighting so key body joints (knees, ankles, shoulders) are distinctly visible against background gym equipment.
