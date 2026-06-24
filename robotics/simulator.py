import base64
import io
import math
import threading
from typing import Dict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import LINKS

_PLOT_LOCK = threading.Lock()


def render_robot_simulation(target_pose: Dict, ik_result: Dict) -> str:
    """Vẽ tay robot 2D tại tư thế gắp và trả về ảnh PNG dạng data URI."""
    joints = ik_result["joints_deg"]
    j2 = math.radians(joints[1])
    j3 = math.radians(joints[2])
    base_height = LINKS["base_height"]
    l1 = LINKS["shoulder_to_elbow"]
    l2 = LINKS["elbow_to_wrist"]

    shoulder = (0.0, base_height)
    elbow = (
        l1 * math.cos(j2),
        base_height + l1 * math.sin(j2),
    )
    wrist = (
        elbow[0] + l2 * math.cos(j2 + j3),
        elbow[1] + l2 * math.sin(j2 + j3),
    )
    target_radius = math.hypot(target_pose["x_mm"], target_pose["y_mm"])

    with _PLOT_LOCK:
        fig, ax = plt.subplots(figsize=(7.2, 4.2), facecolor="#0b1220")
        ax.set_facecolor("#0b1220")
        ax.plot(
            [shoulder[0], elbow[0], wrist[0]],
            [shoulder[1], elbow[1], wrist[1]],
            color="#38bdf8",
            linewidth=8,
            solid_capstyle="round",
            marker="o",
            markersize=11,
            markerfacecolor="#e2e8f0",
        )
        ax.plot([0, 0], [0, base_height], color="#64748b", linewidth=12, solid_capstyle="round")
        ax.scatter([target_radius], [target_pose["z_mm"]], s=180, c="#22c55e", marker="*", zorder=5)
        ax.annotate(
            "Vật thể",
            (target_radius, target_pose["z_mm"]),
            xytext=(8, 12),
            textcoords="offset points",
            color="#bbf7d0",
            fontsize=10,
        )
        ax.axhline(0, color="#334155", linewidth=2)
        ax.set_title(
            f"Mô phỏng tư thế gắp · J1 (góc nhìn từ trên) = {joints[0]:.2f}°",
            color="#f8fafc",
            fontsize=12,
            pad=14,
        )
        ax.set_xlabel("Bán kính từ đế (mm)", color="#94a3b8")
        ax.set_ylabel("Chiều cao (mm)", color="#94a3b8")
        ax.tick_params(colors="#94a3b8")
        for spine in ax.spines.values():
            spine.set_color("#334155")
        ax.grid(color="#1e293b", alpha=0.8)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xlim(-25, max(330, target_radius + 40))
        ax.set_ylim(-15, 240)
        fig.tight_layout()

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=130, facecolor=fig.get_facecolor())
        plt.close(fig)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
