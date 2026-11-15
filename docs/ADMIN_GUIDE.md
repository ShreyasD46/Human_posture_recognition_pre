# Gym Owner & Facility Admin Guide

---

## 1. Device Setup & Initial Configuration
1. Connect Raspberry Pi 4B to the HDMI Touch Display and official 5V/3A USB-C power supply.
2. Connect Raspberry Pi Camera Module 3 to the CSI port or plug in a standard 1080p USB webcam.
3. Boot the device. Run the automated installer:
   ```bash
   sudo chmod +x deploy/install.sh
   sudo ./deploy/install.sh
   ```
4. Verify system service status:
   ```bash
   sudo systemctl status ai-coach-backend
   sudo systemctl status ai-coach-kiosk
   ```

---

## 2. Diagnostics & Benchmarking
Run the built-in system profiler:
```bash
make benchmark
```
Expected output on Raspberry Pi 4B:
- Pipeline Latency: $< 5$ ms
- Throughput: $\ge 20$ FPS
- Resident Memory: $< 150$ MB
- SoC Temperature: $< 65^\circ\text{C}$ (with active cooling)

---

## 3. Member Management & Data Privacy
- **Zero Video Storage:** The appliance processes camera frames in RAM and discards them immediately. No video recordings are ever written to disk or sent to the cloud.
- **Data Export & Erasure:** Members can export their session metrics or request complete deletion in accordance with GDPR / CCPA.
