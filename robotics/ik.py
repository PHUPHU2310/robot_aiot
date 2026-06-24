import math
from typing import Dict, List

from config import LINKS


def inverse_kinematics(x_mm: float, y_mm: float, z_mm: float) -> Dict:
    """
    IK demo cho robot 4DOF:
    J1: đế xoay
    J2: vai
    J3: khuỷu
    J4: cổ tay giữ đầu gắp hướng xuống

    Đây là bản mô phỏng. Khi có robot thật, cần chỉnh lại theo quy ước góc thực tế.
    """
    base_height = LINKS["base_height"]
    l1 = LINKS["shoulder_to_elbow"]
    l2 = LINKS["elbow_to_wrist"]

    j1 = math.degrees(math.atan2(y_mm, x_mm))

    r = math.sqrt(x_mm**2 + y_mm**2)
    z = z_mm - base_height

    distance = math.sqrt(r**2 + z**2)
    if distance > (l1 + l2) or distance < abs(l1 - l2):
        raise ValueError("Tọa độ ngoài vùng với tới của tay robot.")

    cos_j3 = (r**2 + z**2 - l1**2 - l2**2) / (2 * l1 * l2)
    cos_j3 = max(-1, min(1, cos_j3))
    j3_rad = math.acos(cos_j3)

    alpha = math.atan2(z, r)
    beta = math.atan2(l2 * math.sin(j3_rad), l1 + l2 * math.cos(j3_rad))
    j2_rad = alpha - beta

    j2 = math.degrees(j2_rad)
    j3 = math.degrees(j3_rad)

    # Giữ gripper hướng xuống tương đối so với mặt bàn
    j4 = -(j2 + j3)

    joints = [round(j1, 2), round(j2, 2), round(j3, 2), round(j4, 2)]

    return {
        "joints_deg": joints,
        "explain": {
            "j1_base": joints[0],
            "j2_shoulder": joints[1],
            "j3_elbow": joints[2],
            "j4_wrist": joints[3],
        }
    }
