import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

# Create output directory
out_dir = Path(r"c:\Users\User\yabatech-traffic-poc\outputs\figures")
out_dir.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9

def generate_figure_3_1():
    """Figure 3.1: High-Level System Architecture"""
    fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 7.5)
    ax.axis('off')

    # Title
    ax.text(5.5, 7.15, "Figure 3.1: High-Level System Architecture", 
            ha='center', va='center', fontsize=12, fontweight='bold', color='#111827')

    # Architecture Layers (Containers)
    layers = [
        {"y": 5.4, "h": 1.4, "title": "LAYER 1: DATA ACQUISITION & BUFFERING", "bg": "#F0FDF4", "border": "#16A34A"},
        {"y": 3.7, "h": 1.4, "title": "LAYER 2: COMPUTER VISION & PERCEPTION ENGINE", "bg": "#EFF6FF", "border": "#2563EB"},
        {"y": 2.0, "h": 1.4, "title": "LAYER 3: ADAPTIVE TRAFFIC SIGNAL CONTROLLER", "bg": "#FEFCE8", "border": "#CA8A04"},
        {"y": 0.3, "h": 1.4, "title": "LAYER 4: VISUALIZATION, TELEMETRY & LOGGING", "bg": "#FAF5FF", "border": "#9333EA"},
    ]

    for lay in layers:
        rect = patches.FancyBboxPatch((0.5, lay["y"]), 10.0, lay["h"],
                                      boxstyle="round,pad=0.08,rounding_size=0.15",
                                      facecolor=lay["bg"], edgecolor=lay["border"], linewidth=1.5)
        ax.add_patch(rect)
        ax.text(0.7, lay["y"] + lay["h"] - 0.22, lay["title"],
                ha='left', va='center', fontsize=9, fontweight='bold', color=lay["border"])

    # Layer 1 Components
    boxes_l1 = [
        ("Mobile Camera Stream\n(RTSP / HTTP MJPEG @ 1080p)", 0.8, 5.55, 2.7, 0.85),
        ("Threaded Frame Grabber\n(LiveStreamCapture Worker)", 3.9, 5.55, 2.8, 0.85),
        ("Decoupled Buffer Queue\n(Zero-Latency Frame Cache)", 7.1, 5.55, 3.1, 0.85),
    ]

    # Layer 2 Components
    boxes_l2 = [
        ("YOLO11n Neural Detector\n(PyTorch CPU, COCO Classes)", 0.8, 3.85, 2.7, 0.85),
        ("Base-Centroid Extractor\n(C_x = (x1+x2)/2, C_y = y2)", 3.9, 3.85, 2.8, 0.85),
        ("Polygonal ROI Manager\n(cv2.pointPolygonTest Queue)", 7.1, 3.85, 3.1, 0.85),
    ]

    # Layer 3 Components
    boxes_l3 = [
        ("Queue Aggregator\n(Approach Q_k & PCU Weight)", 0.8, 2.15, 2.7, 0.85),
        ("Dynamic Green Calculator\nT_green = clip(T_min + Q*T_car)", 3.9, 2.15, 2.8, 0.85),
        ("Signal State Machine\n(GREEN -> YELLOW -> ALL-RED)", 7.1, 2.15, 3.1, 0.85),
    ]

    # Layer 4 Components
    boxes_l4 = [
        ("High-Visibility Traffic HUD\n(3-Lamp Signal Pods, Badges)", 0.8, 0.45, 2.7, 0.85),
        ("Viewpoint Simulator\n(Synthetic & Replay Engine)", 3.9, 0.45, 2.8, 0.85),
        ("Telemetry & CSV Logger\n(Phase Switched, Avg Queues)", 7.1, 0.45, 3.1, 0.85),
    ]

    for bgroup in [boxes_l1, boxes_l2, boxes_l3, boxes_l4]:
        for text, bx, by, bw, bh in bgroup:
            box = patches.FancyBboxPatch((bx, by), bw, bh,
                                         boxstyle="round,pad=0.04,rounding_size=0.08",
                                         facecolor="#FFFFFF", edgecolor="#4B5563", linewidth=1.0)
            ax.add_patch(box)
            ax.text(bx + bw/2, by + bh/2, text, ha='center', va='center',
                    fontsize=8, color="#1F2937", multialignment='center')

    # Draw Inter-Layer Connecting Arrows
    arrow_props = dict(arrowstyle="->,head_width=0.3,head_length=0.3", color="#374151", lw=1.5)
    
    # Internal flow arrows in L1
    ax.annotate("", xy=(3.9, 5.97), xytext=(3.5, 5.97), arrowprops=arrow_props)
    ax.annotate("", xy=(7.1, 5.97), xytext=(6.7, 5.97), arrowprops=arrow_props)

    # L1 to L2
    ax.annotate("", xy=(2.15, 4.7), xytext=(8.65, 5.55),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.15", color="#1E40AF", lw=1.5))

    # Internal flow arrows in L2
    ax.annotate("", xy=(3.9, 4.27), xytext=(3.5, 4.27), arrowprops=arrow_props)
    ax.annotate("", xy=(7.1, 4.27), xytext=(6.7, 4.27), arrowprops=arrow_props)

    # L2 to L3
    ax.annotate("", xy=(2.15, 3.0), xytext=(8.65, 3.85),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.15", color="#854D0E", lw=1.5))

    # Internal flow arrows in L3
    ax.annotate("", xy=(3.9, 2.57), xytext=(3.5, 2.57), arrowprops=arrow_props)
    ax.annotate("", xy=(7.1, 2.57), xytext=(6.7, 2.57), arrowprops=arrow_props)

    # L3 to L4
    ax.annotate("", xy=(2.15, 1.3), xytext=(8.65, 2.15),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=-0.15", color="#6B21A8", lw=1.5))
    ax.annotate("", xy=(5.3, 1.3), xytext=(5.3, 2.15), arrowprops=arrow_props)
    ax.annotate("", xy=(8.65, 1.3), xytext=(8.65, 2.15), arrowprops=arrow_props)

    plt.tight_layout()
    fig_path = out_dir / "Figure_3_1_System_Architecture.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated: {fig_path}")

def generate_figure_3_2():
    """Figure 3.2: Level 0 Context Diagram"""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # Title
    ax.text(5.0, 5.7, "Figure 3.2: Level 0 Context Diagram of the Adaptive Traffic Signal Control System", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#111827')

    # Central System Circle / Rounded Box
    center_box = patches.FancyBboxPatch((3.4, 2.0), 3.2, 1.8,
                                        boxstyle="round,pad=0.1,rounding_size=0.3",
                                        facecolor="#EFF6FF", edgecolor="#1D4ED8", linewidth=2.0)
    ax.add_patch(center_box)
    ax.text(5.0, 3.1, "0.0\nADAPTIVE TRAFFIC\nSIGNAL CONTROL\nSYSTEM",
            ha='center', va='center', fontsize=9.5, fontweight='bold', color="#1E3A8A")

    # External Entities (Square Boxes)
    entities = [
        ("Smartphone Camera /\nVideo Stream", 0.6, 3.8, 2.2, 1.1, "#FEF3C7", "#D97706"),
        ("Approaching Traffic\n(YABATECH Junction)", 0.6, 0.9, 2.2, 1.1, "#FEE2E2", "#DC2626"),
        ("Signal Hardware /\nVirtual HUD Display", 7.2, 3.8, 2.2, 1.1, "#DCFCE7", "#16A34A"),
        ("Traffic Officer /\nSystem Evaluator", 7.2, 0.9, 2.2, 1.1, "#F3E8FF", "#9333EA"),
    ]

    for name, ex, ey, ew, eh, bg, bd in entities:
        box = patches.Rectangle((ex, ey), ew, eh, facecolor=bg, edgecolor=bd, linewidth=1.5)
        ax.add_patch(box)
        ax.text(ex + ew/2, ey + eh/2, name, ha='center', va='center',
                fontsize=8.5, fontweight='bold', color="#1F2937", multialignment='center')

    # Arrows and Data Flows
    arrow_props = dict(arrowstyle="->,head_width=0.25,head_length=0.25", color="#1F2937", lw=1.3)

    # 1. Camera to System
    ax.annotate("", xy=(3.4, 3.3), xytext=(2.8, 4.3), arrowprops=arrow_props)
    ax.text(3.1, 4.0, "Live RTSP / MJPEG\nVideo Frames", fontsize=7.5, color="#1F2937", ha='right', va='center')

    # 2. Traffic to Camera (Physical optical capture)
    ax.annotate("", xy=(1.7, 3.8), xytext=(1.7, 2.0), arrowprops=arrow_props)
    ax.text(1.8, 2.9, "Optical Vehicle\nMovements", fontsize=7.5, color="#1F2937", ha='left', va='center')

    # 3. System to Signal / HUD
    ax.annotate("", xy=(7.2, 4.3), xytext=(6.6, 3.3), arrowprops=arrow_props)
    ax.text(6.9, 4.0, "Signal Phase Commands\n(Green, Yellow, Red)", fontsize=7.5, color="#1F2937", ha='left', va='center')

    # 4. System to Officer / Evaluator
    ax.annotate("", xy=(7.2, 1.6), xytext=(6.6, 2.5), arrowprops=arrow_props)
    ax.text(6.9, 2.2, "Real-Time Telemetry\n& CSV Diagnostics", fontsize=7.5, color="#1F2937", ha='left', va='center')

    # 5. Officer to System (ROI & Config inputs)
    ax.annotate("", xy=(5.0, 2.0), xytext=(7.2, 1.3), arrowprops=arrow_props)
    ax.text(6.1, 1.5, "ROI Polygon & Timing Config", fontsize=7.5, color="#1F2937", ha='center', va='top')

    plt.tight_layout()
    fig_path = out_dir / "Figure_3_2_Context_Diagram.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated: {fig_path}")

def generate_figure_3_3():
    """Figure 3.3: Level 1 Data Flow Diagram (DFD)"""
    fig, ax = plt.subplots(figsize=(11, 8), dpi=300)
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 8)
    ax.axis('off')

    # Title
    ax.text(5.5, 7.7, "Figure 3.3: Level 1 Data Flow Diagram of the Adaptive Traffic Signal Control System", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#111827')

    # Processes (Circles/Rounded rects)
    processes = [
        ("1.0\nCapture & Buffer\nVideo Frames", 1.8, 6.0, 1.8, 1.0),
        ("2.0\nDetect & Classify\nVehicles (YOLO)", 5.5, 6.0, 1.8, 1.0),
        ("3.0\nEstimate Approach\nQueues (ROIs)", 8.5, 4.4, 1.8, 1.0),
        ("4.0\nCompute Green Time\n& State Machine", 4.8, 2.6, 2.2, 1.0),
        ("5.0\nRender HUD &\nExport Telemetry", 1.5, 2.6, 1.8, 1.0),
    ]

    for pnum_title, px, py, pw, ph in processes:
        proc_box = patches.FancyBboxPatch((px - pw/2, py - ph/2), pw, ph,
                                          boxstyle="round,pad=0.08,rounding_size=0.25",
                                          facecolor="#EFF6FF", edgecolor="#1D4ED8", linewidth=1.5)
        ax.add_patch(proc_box)
        ax.text(px, py, pnum_title, ha='center', va='center',
                fontsize=8, fontweight='bold', color="#1E3A8A", multialignment='center')

    # Data Stores (Open-ended rects / parallel lines)
    stores = [
        ("D1: Approach ROI Polygon Store", 8.5, 6.4, 2.2, 0.6),
        ("D2: Real-Time Queue Store", 8.5, 2.8, 2.2, 0.6),
        ("D3: Controller Timing Parameters", 5.0, 1.0, 2.4, 0.6),
        ("D4: Simulation Telemetry Log (CSV)", 1.5, 1.0, 2.4, 0.6),
    ]

    for sname, sx, sy, sw, sh in stores:
        # draw top line and bottom line for DFD store
        x1, x2 = sx - sw/2, sx + sw/2
        y1, y2 = sy - sh/2, sy + sh/2
        ax.plot([x1, x2], [y1, y1], color="#4B5563", lw=1.4)
        ax.plot([x1, x2], [y2, y2], color="#4B5563", lw=1.4)
        ax.plot([x1, x1], [y1, y2], color="#4B5563", lw=1.4)
        rect = patches.Rectangle((x1, y1), sw, sh, facecolor="#F3F4F6", edgecolor="none")
        ax.add_patch(rect)
        ax.text(sx, sy, sname, ha='center', va='center', fontsize=7.5, fontweight='bold', color="#374151")

    # External Entities
    ent_cam = patches.Rectangle((0.2, 5.5), 0.9, 1.0, facecolor="#FEF3C7", edgecolor="#D97706", lw=1.4)
    ax.add_patch(ent_cam)
    ax.text(0.65, 6.0, "Mobile\nCamera", ha='center', va='center', fontsize=7.5, fontweight='bold', color="#92400E")

    ent_sig = patches.Rectangle((0.2, 2.1), 0.9, 1.0, facecolor="#DCFCE7", edgecolor="#16A34A", lw=1.4)
    ax.add_patch(ent_sig)
    ax.text(0.65, 2.6, "Signal\nPODs", ha='center', va='center', fontsize=7.5, fontweight='bold', color="#166534")

    # Arrows & Data Flows
    arrow_props = dict(arrowstyle="->,head_width=0.25,head_length=0.25", color="#1F2937", lw=1.3)

    # Cam -> 1.0
    ax.annotate("", xy=(0.9, 6.0), xytext=(1.1, 6.0), arrowprops=arrow_props)
    ax.text(1.0, 6.2, "RTSP Stream", fontsize=7, ha='center')

    # 1.0 -> 2.0
    ax.annotate("", xy=(4.6, 6.0), xytext=(2.7, 6.0), arrowprops=arrow_props)
    ax.text(3.65, 6.2, "Latest Decoupled Frame", fontsize=7, ha='center')

    # 2.0 -> 3.0
    ax.annotate("", xy=(7.6, 4.8), xytext=(6.4, 5.7), arrowprops=arrow_props)
    ax.text(7.2, 5.5, "Vehicle Centroids\n& Class Labels", fontsize=7, ha='center')

    # D1 -> 3.0
    ax.annotate("", xy=(8.5, 4.9), xytext=(8.5, 6.1), arrowprops=arrow_props)
    ax.text(8.6, 5.5, "ROI Coordinates", fontsize=7, ha='left')

    # 3.0 -> D2
    ax.annotate("", xy=(8.5, 3.1), xytext=(8.5, 3.9), arrowprops=arrow_props)
    ax.text(8.6, 3.5, "Approach Queue Q_k", fontsize=7, ha='left')

    # D2 -> 4.0
    ax.annotate("", xy=(5.9, 2.8), xytext=(7.4, 2.8), arrowprops=arrow_props)
    ax.text(6.6, 3.0, "Active / Competing Queues", fontsize=7, ha='center')

    # D3 -> 4.0
    ax.annotate("", xy=(5.0, 2.1), xytext=(5.0, 1.3), arrowprops=arrow_props)
    ax.text(5.1, 1.7, "T_min, T_max, T_car", fontsize=7, ha='left')

    # 4.0 -> 5.0
    ax.annotate("", xy=(2.4, 2.6), xytext=(3.7, 2.6), arrowprops=arrow_props)
    ax.text(3.05, 2.8, "Signal Phase State &\nTimers", fontsize=7, ha='center')

    # 1.0 -> 5.0
    ax.annotate("", xy=(1.5, 3.1), xytext=(1.8, 5.5), arrowprops=arrow_props)
    ax.text(1.4, 4.3, "Raw Frame\nfor Overlay", fontsize=7, ha='right')

    # 5.0 -> Signal
    ax.annotate("", xy=(1.1, 2.6), xytext=(0.55, 2.6), arrowprops=arrow_props)
    ax.text(0.9, 2.8, "Phase State", fontsize=7, ha='center')

    # 5.0 -> D4
    ax.annotate("", xy=(1.5, 1.3), xytext=(1.5, 2.1), arrowprops=arrow_props)
    ax.text(1.6, 1.7, "Frame Logs", fontsize=7, ha='left')

    plt.tight_layout()
    fig_path = out_dir / "Figure_3_3_Data_Flow_Diagram.png"
    plt.savefig(fig_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Generated: {fig_path}")

if __name__ == "__main__":
    generate_figure_3_1()
    generate_figure_3_2()
    generate_figure_3_3()
    print("All methodology diagrams successfully generated.")
