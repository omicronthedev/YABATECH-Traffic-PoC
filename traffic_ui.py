"""High-Visibility Traffic Light HUD & Visual Overlay Module.

Provides bold, prominent traffic signal heads (Red, Yellow, Green),
dynamic glowing lamps, lane-level on-road indicators, and status telemetry.
"""

from typing import Dict, List, Optional
import cv2
import numpy as np


def draw_high_visibility_hud(
    frame: np.ndarray,
    approaches: List[Dict],
    queue_counts: Dict[str, int],
    controller_info: Dict[str, any],
    fps: float,
    detected_boxes: Optional[List] = None,
    sim_time: Optional[float] = None,
    title_prefix: str = "LIVE STREAM",
) -> np.ndarray:
    """Render high-contrast, bold traffic signals, approach ROIs, and decision overlays."""
    h, w = frame.shape[:2]
    canvas = frame.copy()

    # Dynamic scaling factor based on video resolution (adapts to 360p, 720p, 1080p)
    scale = max(0.75, min(w / 1100.0, 1.6))

    signals = controller_info.get("signals", {})
    active_approach = controller_info.get("active_approach", "")
    active_state = controller_info.get("state", "GREEN")
    remaining_sec = controller_info.get("remaining_time", 0.0)
    decision_reason = controller_info.get("reason", "")

    # ------------------------------------------------------------------------
    # 1. Approach ROI Polygons & On-Road Status Badges
    # ------------------------------------------------------------------------
    for app in approaches:
        name = app["name"]
        poly = app["poly"] if "poly" in app else app.get_pixel_polygon(w, h)
        app_color = app["color"] if isinstance(app, dict) else app.color
        q_count = queue_counts.get(name, 0)
        app_signal = signals.get(name, "RED")

        # Semi-transparent lane fill
        overlay = canvas.copy()
        cv2.fillPoly(overlay, [poly], app_color)
        cv2.addWeighted(overlay, 0.18, canvas, 0.82, 0, canvas)

        # Border color changes to Green if this approach currently has the green light!
        if app_signal == "GREEN":
            border_col = (0, 255, 0)
            thickness = max(2, int(4 * scale))
        elif app_signal == "YELLOW":
            border_col = (0, 255, 255)
            thickness = max(2, int(3 * scale))
        else:
            border_col = (0, 0, 255) if name == active_approach else app_color
            thickness = max(1, int(2 * scale))

        cv2.polylines(canvas, [poly], isClosed=True, color=border_col, thickness=thickness)

        # Compute centroid for on-road badge
        centroid = np.mean(poly, axis=0).astype(int)
        cx, cy = centroid[0], centroid[1]

        # On-Road Status Pill (e.g., "[ 🟢 GO (12s) | Queue: 3 ]")
        if app_signal == "GREEN":
            pill_text = f"GO ({remaining_sec:.0f}s) | Queue: {q_count}"
            pill_bg = (0, 160, 0)
            pill_text_col = (255, 255, 255)
        elif app_signal == "YELLOW":
            pill_text = f"WAIT ({remaining_sec:.0f}s)"
            pill_bg = (0, 200, 220)
            pill_text_col = (0, 0, 0)
        else:
            pill_text = f"STOP | Queue: {q_count}"
            pill_bg = (0, 0, 180)
            pill_text_col = (255, 255, 255)

        full_label = f"{name}: {pill_text}"
        font_scale = 0.55 * scale
        (tw, th), _ = cv2.getTextSize(full_label, cv2.FONT_HERSHEY_DUPLEX, font_scale, 1)

        # Center the pill around the centroid
        px1 = max(10, cx - tw // 2 - int(10 * scale))
        py1 = max(10, cy - th // 2 - int(8 * scale))
        px2 = min(w - 10, px1 + tw + int(20 * scale))
        py2 = py1 + th + int(16 * scale)

        cv2.rectangle(canvas, (px1, py1), (px2, py2), (15, 15, 15), -1)
        cv2.rectangle(canvas, (px1, py1), (px2, py2), pill_bg, -1)
        cv2.rectangle(canvas, (px1, py1), (px2, py2), (255, 255, 255), 1)
        cv2.putText(
            canvas,
            full_label,
            (px1 + int(10 * scale), py1 + th + int(4 * scale)),
            cv2.FONT_HERSHEY_DUPLEX,
            font_scale,
            pill_text_col,
            1,
            cv2.LINE_AA,
        )

    # ------------------------------------------------------------------------
    # 2. Vehicle Bounding Boxes & Footpoints
    # ------------------------------------------------------------------------
    if detected_boxes:
        for item in detected_boxes:
            if isinstance(item, dict):
                x1, y1, x2, y2 = item["box"]
                v_type = item["type"]
                foot = item["foot"]
                assigned = item.get("assigned")
            else:
                x1, y1, x2, y2, v_type, foot, assigned = item

            # Color code vehicle: Green if in green lane, Red if in stopped lane, Gray if outside
            if assigned:
                app_sig = signals.get(assigned, "RED")
                box_col = (0, 255, 0) if app_sig == "GREEN" else ((0, 255, 255) if app_sig == "YELLOW" else (0, 0, 255))
            else:
                box_col = (170, 170, 170)

            cv2.rectangle(canvas, (x1, y1), (x2, y2), box_col, max(1, int(2 * scale)))
            cv2.circle(canvas, foot, max(3, int(4 * scale)), (0, 0, 255), -1)
            cv2.putText(
                canvas,
                v_type,
                (x1, max(14, y1 - 4)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45 * scale,
                box_col,
                1,
                cv2.LINE_AA,
            )

    # ------------------------------------------------------------------------
    # 3. Top Status Header Banner
    # ------------------------------------------------------------------------
    banner_h = int(58 * scale)
    cv2.rectangle(canvas, (0, 0), (w, banner_h), (12, 12, 14), -1)
    cv2.line(canvas, (0, banner_h), (w, banner_h), (50, 50, 50), 1)

    time_str = f"Sim Time: {sim_time:.1f}s" if sim_time is not None else f"{fps:.1f} FPS"
    main_title = f"YABATECH Adaptive Traffic Control | {title_prefix} ({time_str})"
    cv2.putText(
        canvas,
        main_title,
        (int(15 * scale), int(26 * scale)),
        cv2.FONT_HERSHEY_DUPLEX,
        0.65 * scale,
        (0, 255, 255),
        1,
        cv2.LINE_AA,
    )

    reason_text = f"Controller Status: {decision_reason}"
    cv2.putText(
        canvas,
        reason_text,
        (int(15 * scale), int(48 * scale)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.48 * scale,
        (220, 220, 220),
        1,
        cv2.LINE_AA,
    )

    # ------------------------------------------------------------------------
    # 4. High-Visibility Traffic Signal Pods (Top Right)
    # ------------------------------------------------------------------------
    card_w = int(320 * scale)
    card_h = int(125 * scale)
    card_margin = int(14 * scale)
    start_x = w - card_w - card_margin
    start_y = banner_h + card_margin

    lamp_radius = int(15 * scale)
    lamp_spacing = int(36 * scale)

    for i, app in enumerate(approaches):
        name = app["name"] if isinstance(app, dict) else app.name
        y = start_y + i * (card_h + card_margin)
        signal_state = signals.get(name, "RED")
        is_active = name == active_approach

        # Card Housing
        card_bg = (20, 20, 24)
        border_col = (0, 255, 0) if signal_state == "GREEN" else ((0, 255, 255) if signal_state == "YELLOW" else (70, 70, 75))
        border_thick = 2 if is_active else 1

        cv2.rectangle(canvas, (start_x, y), (start_x + card_w, y + card_h), card_bg, -1)
        cv2.rectangle(canvas, (start_x, y), (start_x + card_w, y + card_h), border_col, border_thick)

        # Approach Name Header
        cv2.putText(
            canvas,
            name,
            (start_x + int(14 * scale), y + int(24 * scale)),
            cv2.FONT_HERSHEY_DUPLEX,
            0.55 * scale,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )

        # Traffic Signal Enclosure (Pod)
        pod_x = start_x + int(14 * scale)
        pod_y = y + int(36 * scale)
        pod_w = int(115 * scale)
        pod_h = int(44 * scale)
        cv2.rectangle(canvas, (pod_x, pod_y), (pod_x + pod_w, pod_y + pod_h), (6, 6, 8), -1)
        cv2.rectangle(canvas, (pod_x, pod_y), (pod_x + pod_w, pod_y + pod_h), (70, 70, 70), 1)

        # Lamp Center Points (Red, Yellow, Green)
        r_center = (pod_x + int(20 * scale), pod_y + int(22 * scale))
        y_center = (r_center[0] + lamp_spacing, r_center[1])
        g_center = (y_center[0] + lamp_spacing, r_center[1])

        is_red = signal_state in ("RED", "ALL_RED")
        is_yellow = signal_state == "YELLOW"
        is_green = signal_state == "GREEN"

        # Draw Red Lamp
        if is_red:
            cv2.circle(canvas, r_center, lamp_radius + int(4 * scale), (0, 0, 180), int(2 * scale))  # Glow
            cv2.circle(canvas, r_center, lamp_radius, (0, 0, 255), -1)  # Core
            cv2.circle(canvas, (r_center[0] - 3, r_center[1] - 3), int(lamp_radius * 0.35), (140, 140, 255), -1)  # Specular
        else:
            cv2.circle(canvas, r_center, lamp_radius, (15, 15, 60), -1)

        # Draw Yellow Lamp
        if is_yellow:
            cv2.circle(canvas, y_center, lamp_radius + int(4 * scale), (0, 180, 180), int(2 * scale))
            cv2.circle(canvas, y_center, lamp_radius, (0, 255, 255), -1)
            cv2.circle(canvas, (y_center[0] - 3, y_center[1] - 3), int(lamp_radius * 0.35), (200, 255, 255), -1)
        else:
            cv2.circle(canvas, y_center, lamp_radius, (20, 60, 60), -1)

        # Draw Green Lamp
        if is_green:
            cv2.circle(canvas, g_center, lamp_radius + int(4 * scale), (0, 180, 0), int(2 * scale))
            cv2.circle(canvas, g_center, lamp_radius, (0, 255, 0), -1)
            cv2.circle(canvas, (g_center[0] - 3, g_center[1] - 3), int(lamp_radius * 0.35), (180, 255, 180), -1)
        else:
            cv2.circle(canvas, g_center, lamp_radius, (15, 60, 15), -1)

        # Large High-Visibility Signal State Badge (Right of Pod)
        badge_x = pod_x + pod_w + int(12 * scale)
        badge_y = pod_y
        badge_w = card_w - pod_w - int(38 * scale)
        badge_h = pod_h

        if is_active:
            if signal_state == "GREEN":
                badge_bg = (0, 140, 0)
                badge_text = f"GREEN {remaining_sec:.0f}s"
                text_col = (255, 255, 255)
            elif signal_state == "YELLOW":
                badge_bg = (0, 180, 200)
                badge_text = f"YELLOW {remaining_sec:.0f}s"
                text_col = (0, 0, 0)
            else:
                badge_bg = (0, 0, 160)
                badge_text = f"ALL RED"
                text_col = (255, 255, 255)
        else:
            badge_bg = (0, 0, 140)
            badge_text = "RED (STOP)"
            text_col = (255, 255, 255)

        cv2.rectangle(canvas, (badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h), badge_bg, -1)
        cv2.rectangle(canvas, (badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h), (255, 255, 255), 1)

        font_scale_badge = 0.58 * scale
        (bw, bh), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_DUPLEX, font_scale_badge, 1)
        cv2.putText(
            canvas,
            badge_text,
            (badge_x + (badge_w - bw) // 2, badge_y + (badge_h + bh) // 2),
            cv2.FONT_HERSHEY_DUPLEX,
            font_scale_badge,
            text_col,
            1,
            cv2.LINE_AA,
        )

        # Queue Length Footer
        q_count = queue_counts.get(name, 0)
        footer_text = f"Current Queue: {q_count} vehicles"
        cv2.putText(
            canvas,
            footer_text,
            (start_x + int(14 * scale), y + int(106 * scale)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50 * scale,
            (200, 200, 200),
            1,
            cv2.LINE_AA,
        )

    return canvas
