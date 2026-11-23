# YABATECH Adaptive Traffic Management System (PoC)

An intelligent, computer-vision-driven adaptive traffic signal control system developed as a Proof-of-Concept (PoC) for the intersection in front of **Yaba College of Technology (YABATECH) Front Gate** on **Hussey Road, Yaba, Lagos**.

---

## 1. Project Background & Problem Context

The intersection directly in front of the YABATECH Main Gate is one of the most congested bottleneck points in the Yaba academic belt:
* **Complex Geometry**: An irregular 4-leg / offset T-junction along **Hussey Road**:
  * **WAEC / FSTC Leg (West)**: Travels past the **WAEC Building** and the **68 Nigerian Army Reference Hospital (Military Hospital, Yaba)**, terminating at the entrance gate of the **Federal Science and Technical College (FSTC), Yaba** (with a branching road to the left).
  * **Higher College Road / Jibowu Leg (East)**: Connects to **Higher College Road**, directly linking traffic to and from the major junction at the **Jibowu Pedestrian Bridge** (Herbert Macaulay Way / Ikorodu Road corridor).
  * **YABATECH Front Gate (North)**: The main entrance and exit gatehouse for college vehicles, shuttles, and pedestrian crowds.
  * **Alakija Street (South)**: Commercial/feeder street intersecting directly opposite/adjacent to the gate.
* **Mixed Traffic & Small Vehicles**: High proportions of tricycles (*Keke Marwa / Napep*), motorcycles (*Okada*), commercial minibuses (*Danfo*), and private vehicles.
* **Informal Curb Stoppages**: Tricycles frequently stop at the mouth of the gate and along road shoulders to pick up/drop off passengers, constricting traffic to an alternating single lane.
* **Heavy Pedestrian Crossings**: Periodic surges of thousands of students walking across Hussey Road.

### Evolution of the System
1. **Phase 1 (Recorded Video Analytics)**: Counted vehicles per frame, assigned persistent IDs via ByteTrack, and logged directional crossings over virtual tripwires (`track_and_count.py`).
2. **Phase 2 (Current - Real-Time Livestream Adaptive Control)**: Ingests live video feeds directly from a **mobile phone camera**, estimates real-time approach queue densities, and dynamically allocates traffic light timings (`GREEN`, `YELLOW`, `ALL-RED`) in real time.

---

## 2. System Architecture

```
[ Phone Camera Stream (IP Webcam / DroidCam / RTSP) ]
                         │
                         ▼
          [ Threaded Zero-Latency Reader ] ──► (Discards stale buffer frames; guarantees real-time)
                         │
                         ▼
             [ YOLO11n Object Detector ]   ──► (Detects cars, tricycles, buses, trucks, motorcycles)
                         │
                         ▼
         [ Approach Zone (ROI) Polygons ]  ──► (Calculates instantaneous queue occupancy per approach)
                         │
                         ▼
        [ Adaptive Traffic Light Controller ] ──► (Dynamic green allocation + gap-out clearance)
                         │
                         ▼
       [ High-Visibility Visual HUD Overlay ] ──► (Prominent traffic light pods, countdowns, lane badges)
```

---

## 3. Core Features

* **Zero-Latency Livestream Ingestion (`LiveStreamCapture`)**:
  OpenCV's default frame buffer causes network streams (HTTP/RTSP) to lag behind real time by 5–10 seconds when running CPU inference. The custom threaded grabber continuously flushes stale frames so YOLO always operates on the exact current real-time frame, with automatic stream reconnection.
* **Instantaneous Queue Estimation (`ApproachZone`)**:
  Instead of measuring throughput after vehicles cross a line, the system measures **queue occupancy** (vehicles currently waiting/stopped inside an approach polygon).
* **Adaptive Signal Controller (`AdaptiveTrafficController`)**:
  * **Dynamic Green Time**: Proportional to queue length:
    $$T_{\text{green}} = \text{clamp}\left(T_{\min} + (Q \times T_{\text{car}}),\; T_{\min},\; T_{\max}\right)$$
  * **Gap-Out Early Termination**: When an approach queue clears early ($Q = 0$) while another approach has waiting traffic, the green terminates early, avoiding empty green phases.
  * **Safety Clearances**: Every phase transition strictly observes yellow clearance ($3\text{s}$) and all-red intersection clearance ($2\text{s}$).
* **High-Visibility Visual HUD (`traffic_ui.py`)**:
  * Large, prominent 3-lamp traffic signal heads with ambient glow effects and specular highlights.
  * Solid-color status badges with bold countdown timers (`[ 🟢 GREEN 14s ]`, `[ 🔴 STOP ]`).
  * On-road floating lane badges right over the approach zones (`GO` / `STOP`).
  * Real-time decision diagnostics and FPS overlay.

---

## 4. Installation & Setup

### Prerequisites
* Windows 10/11 (or Linux/macOS)
* Python 3.10+ (Project environment configured with Python 3.13)
* Pre-installed dependencies in `venv/`:
  * `ultralytics` (YOLO11)
  * `opencv-python` (`cv2`)
  * `torch`, `torchvision`
  * `numpy`, `pandas`

### Activating Environment
In PowerShell:
```powershell
.\venv\Scripts\Activate.ps1
```
*(Or in Command Prompt: `venv\Scripts\activate.bat`)*

---

## 5. How to Run

### Mode A: Live Phone Camera Stream

Connect your phone and PC to the **same Wi-Fi network** (or connect your PC to your phone's personal hotspot).

#### 1. Android via "IP Webcam" App (Recommended)
1. Install **IP Webcam** (by Pavel Khlebovich) from Google Play Store.
2. Open the app, scroll to the bottom, and tap **"Start server"**.
3. Note the IP displayed on your phone screen (e.g. `http://192.168.43.10:8080`).
4. Run:
   ```powershell
   .\venv\Scripts\python adaptive_traffic_controller.py --source http://192.168.43.10:8080/video
   ```

#### 2. DroidCam (Android / iOS)
1. Install **DroidCam** on your phone.
2. Note the Wi-Fi IP and Port (e.g. `http://192.168.43.10:4747`).
3. Run:
   ```powershell
   .\venv\Scripts\python adaptive_traffic_controller.py --source http://192.168.43.10:4747/video
   ```

#### 3. USB / Virtual Webcam (Iriun / Camo / OBS)
```powershell
.\venv\Scripts\python adaptive_traffic_controller.py --source 0
```

#### 4. Calibrating Approach Zones (`--setup`)
To redraw the approach polygons to match your phone's camera angle:
```powershell
.\venv\Scripts\python adaptive_traffic_controller.py --source http://<PHONE_IP>:8080/video --setup
```
* Click 4 corner points for each approach.
* Press `ENTER` to accept, `R` to redraw.
* Polygons are saved to `outputs/approach_zones.json` in normalized coordinates (auto-scaling to any resolution).

#### On-Screen Keyboard Controls:
* `s`: Save a high-resolution snapshot to `outputs/snapshot_<timestamp>.jpg`.
* `r`: Reconfigure / redraw approach zones on the fly without stopping.
* `q` / `ESC`: Safe shutdown.

---

### Mode B: Multi-Viewpoint Simulation Suite

To test and benchmark the adaptive controller against recorded intersection footage from various angles:

```powershell
# Run simulation on the main intersection footage (e.g. 6-minute duration)
.\venv\Scripts\python simulate_viewpoints.py --videos videos/main_intersection.mp4 --duration 360 --skip 3

# Run batch simulation across multiple street-level viewpoints
.\venv\Scripts\python simulate_viewpoints.py --videos videos/view_WA0033.mp4 videos/view_WA0029.mp4 videos/aerial_reference.mp4 --skip 2
```

Outputs generated:
* Annotated videos saved to `outputs/simulations/sim_<name>.mp4`
* Detailed second-by-second decision and queue CSV logs saved to `outputs/simulations/sim_<name>_stats.csv`
* Global summary in `outputs/simulations/simulation_summary.json`

---

## 6. Configurable Parameters

| CLI Flag | Default | Description |
| :--- | :---: | :--- |
| `--source` | `http://...` | Stream URL (HTTP/RTSP), device index (`0`), or video path |
| `--min-green` | `8.0` | Minimum green time (seconds) to allow vehicles to react and start |
| `--max-green` | `35.0` | Maximum green ceiling (seconds) to prevent starvation |
| `--yellow` | `3.0` | Yellow light duration (seconds) |
| `--all-red` | `2.0` | All-red intersection clearance interval (seconds) |
| `--time-per-car` | `2.0` | Additional green seconds allocated per detected vehicle |
| `--skip` | `1` (or `2`) | Process inference every Nth frame for higher FPS on CPU |
| `--conf` | `0.25` | YOLO detection confidence threshold |
| `--imgsz` | `640` | Inference resolution |

---

## 7. Benchmark Results on YABATECH Intersection Footage

During a 6-minute (360-second) test on the main intersection footage (`main_intersection.mp4`):
* **Total Frames Processed**: 2,371 frames
* **Dynamic Signal Transitions**: 20 phase changes
* **Approach 1 (Hussey Rd Inbound)**: Average queue = 2.83 vehicles; Peak queue = 8 vehicles
* **Approach 2 (Gate Outbound)**: Average queue = 0.32 vehicles; Peak queue = 4 vehicles
* **Adaptive Behavior Demonstrated**:
  * Light queues (0–1 vehicle): Assigned crisp 8–10s green to clear quickly without holding opposing traffic.
  * Surge periods (7 vehicles at $t = 290.8\text{s}$): Dynamically scaled green to 22.0s to completely flush the arterial backlog.

---

## 8. Repository Structure

```
yabatech-traffic-poc/
├── adaptive_traffic_controller.py  # Main real-time phone livestream controller
├── simulate_viewpoints.py          # Multi-viewpoint simulation & benchmarking engine
├── traffic_ui.py                   # High-visibility traffic lights & HUD module
├── track_and_count.py              # Offline video tripwire tracking & counting script
├── yolo11n.pt                      # YOLO11 nano pre-trained detection weights
├── README.md                       # Comprehensive system documentation
│
├── outputs/                        # Generated snapshots, zones, and data logs
│   ├── approach_zones.json         # Normalized approach ROI coordinates
│   ├── high_vis_preview.jpg        # Visual HUD preview sample
│   └── simulations/                # Annotated simulation MP4s and CSV stats
│
└── videos/                         # Reference footage from various intersection angles
    ├── main_intersection.mp4       # Primary 1080x1920 intersection footage (~11.5 mins)
    ├── aerial_reference.mp4        # Aerial bird's-eye footage
    ├── view_WA0033.mp4             # Landscape wide street perspective
    ├── view_WA0029.mp4             # Inbound Hussey Road perspective
    └── view_WA0025.mp4             # Front gate perimeter perspective
```
