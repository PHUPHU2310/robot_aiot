import math
from typing import Dict, List, Tuple

from config import CONFIDENCE_THRESHOLD, WORKSPACE


def find_target(target_object: str, detected_objects: List[Dict]) -> Tuple[Dict | None, str]:
    matches = [obj for obj in detected_objects if obj.get("class_name") == target_object]

    if len(matches) == 0:
        return None, "Không tìm thấy vật thể trong camera."

    if len(matches) > 1:
        return None, "Có nhiều vật cùng loại, cần người dùng xác nhận."

    return matches[0], "OK"


def check_workspace(x_mm: float, y_mm: float, z_mm: float) -> Tuple[bool, str]:
    radius = math.sqrt(x_mm**2 + y_mm**2)

    if radius < WORKSPACE["min_radius"]:
        return False, "Vật quá gần tâm robot."

    if radius > WORKSPACE["max_radius"]:
        return False, "Vật ngoài tầm với của robot."

    if z_mm < WORKSPACE["min_z"] or z_mm > WORKSPACE["max_z"]:
        return False, "Chiều cao z không hợp lệ."

    return True, "OK"


def safety_check(parsed_command: Dict, detected_objects: List[Dict]) -> Dict:
    target = parsed_command.get("target_object")
    action = parsed_command.get("action")

    if not action:
        return reject(parsed_command, "Không nhận diện được hành động.")

    if not target:
        return reject(parsed_command, "Không nhận diện được vật cần gắp.")

    obj, reason = find_target(target, detected_objects)
    if obj is None:
        return reject(parsed_command, reason)

    if obj.get("confidence", 0) < CONFIDENCE_THRESHOLD:
        return reject(parsed_command, "Độ tin cậy YOLO thấp hơn ngưỡng cho phép.", obj)

    ok, workspace_reason = check_workspace(obj["x_mm"], obj["y_mm"], obj["z_mm"])
    if not ok:
        return reject(parsed_command, workspace_reason, obj)

    return {
        "target_object": target,
        "action": action,
        "control_allowed": True,
        "need_human_review": False,
        "blocked_reason": "",
        "target_pose": {
            "x_mm": obj["x_mm"],
            "y_mm": obj["y_mm"],
            "z_mm": obj["z_mm"],
        },
        "confidence": obj.get("confidence"),
    }


def reject(parsed_command: Dict, reason: str, obj: Dict | None = None) -> Dict:
    data = {
        "target_object": parsed_command.get("target_object"),
        "action": parsed_command.get("action"),
        "control_allowed": False,
        "need_human_review": True,
        "blocked_reason": reason,
    }
    if obj:
        data["confidence"] = obj.get("confidence")
    return data
