# YABATECH Adaptive Traffic Management System (PoC)

Proof-of-Concept adaptive traffic signal management system for the intersection at Yaba College of Technology (YABATECH) front gate.

## Features
- **Phone Camera Livestream Ingestion**: Connects to phone camera streams via Wi-Fi (IP Webcam HTTP, DroidCam, RTSP, or USB/virtual webcam) with threaded, zero-latency frame dropping so CPU detection never lags behind real time.
- **YOLO11n Vehicle Detection**: Real-time identification of cars, buses, trucks, and motorcycles.
- **Approach Queue Estimation**: Multi-approach polygonal Regions of Interest (ROIs) that detect stopped/queuing vehicles in each lane.
- **Adaptive Signal Controller**:
  - Dynamically calculates green light duration based on vehicle density ($T_{\text{green}} = \text{clamp}(T_{\min} + k \times \text{queue},\; T_{\min},\; T_{\max})$).
  - Gap-out early clearance (if an approach empties early while another approach has waiting traffic, it transitions early to yellow).
  - Safe signal sequencing: `GREEN` $\rightarrow$ `YELLOW` (3s) $\rightarrow$ `ALL-RED` (2s) $\rightarrow$ Next Approach `GREEN`.
- **Live On-Screen Visual HUD**: Displays active traffic lights (🔴/🟡/🟢), remaining countdown timer, approach queue lengths, and decision diagnostics.

---

## Quick Start Guide

### 1. Connecting Your Phone Camera

Ensure your PC and Phone are connected to the **same Wi-Fi network** (or connect your PC to your phone's personal hotspot).

#### Option A: Android (IP Webcam - Recommended)
1. Install **IP Webcam** (by Pavel Khlebovich) from Google Play Store.
2. Open the app, scroll to the bottom, and tap **"Start server"**.
3. Note the IP displayed on your phone screen (e.g., `http://192.168.43.10:8080`).
4. Run:
   ```powershell
   .\venv\Scripts\python adaptive_traffic_controller.py --source http://192.168.43.10:8080/video
   ```

#### Option B: DroidCam (Android / iPhone)
1. Install **DroidCam** on your phone.
2. Open the app and note the WiFi IP (e.g., `192.168.43.10`) and Port (`4747`).
3. Run:
   ```powershell
   .\venv\Scripts\python adaptive_traffic_controller.py --source http://192.168.43.10:4747/video
   ```

#### Option C: USB / Virtual Webcam (Iriun / Camo)
If your phone is connected as a system webcam:
```powershell
.\venv\Scripts\python adaptive_traffic_controller.py --source 0
```

#### Option D: Testing with a Local Video File (Simulation Mode)
To simulate the phone stream using existing video footage:
```powershell
.\venv\Scripts\python adaptive_traffic_controller.py --source videos/test_clip.mp4 --loop
```

---

### 2. Calibrating Approach Zones (`--setup`)

To map out the intersection approaches (e.g. Approach 1: Hussey Rd / Jibowu Pedestrian Bridge side, Approach 2: Gate & WAEC/Military Hospital/FSTC side):
```powershell
.\venv\Scripts\python adaptive_traffic_controller.py --source http://<PHONE_IP>:8080/video --setup
```
1. Click 4 points on the window covering the queue lane for each approach.
2. Press **ENTER** to confirm each approach.
3. Coordinates are saved automatically to `outputs/approach_zones.json` (normalized so they adapt to any resolution).

---

### 3. Key Controls During Live Stream
- **q / ESC**: Quit the program safely.
- **s**: Take a snapshot of the annotated HUD and save to `outputs/snapshot_<timestamp>.jpg`.
- **r**: Reconfigure / redraw approach zones on the fly without restarting.

---

### 4. Adjusting Adaptive Parameters
```powershell
.\venv\Scripts\python adaptive_traffic_controller.py --source http://<PHONE_IP>:8080/video `
    --min-green 10 `
    --max-green 40 `
    --yellow 3 `
    --time-per-car 2.5 `
    --skip 2
```
- `--min-green`: Minimum green light duration (seconds).
- `--max-green`: Maximum green ceiling (seconds).
- `--time-per-car`: Green seconds added per waiting vehicle.
- `--skip 2`: Runs YOLO on every 2nd frame to boost FPS on CPU.
