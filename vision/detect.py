from copy import deepcopy
from typing import Mapping, Sequence

from config import DEFAULT_OBJECT_Z_MM, DETECTED_OBJECTS, VISION_BACKEND
from vision.calibration import pixel_to_mm
from vision.contracts import DetectedObject, DetectorBackend


class StaticDetector:
    """Backend demo; mô phỏng output của detector thật."""

    def detect(self) -> Sequence[Mapping]:
        return deepcopy(DETECTED_OBJECTS)


def create_detector_backend(name: str = VISION_BACKEND) -> DetectorBackend:
    if name == "static":
        return StaticDetector()
    if name == "yolo":
        from vision.yolo_adapter import YoloDetector

        return YoloDetector()
    raise ValueError(f"Vision backend không hợp lệ: {name}")


def normalize_detection(detection: Mapping) -> DetectedObject:
    """
    Chuẩn hóa raw detection thành contract mm.

    Input chấp nhận:
    - x_mm/y_mm/z_mm
    - x/y/z (được hiểu là mm)
    - u/v pixel (đi qua calibration)
    """
    item = dict(detection)
    if "x_mm" in item and "y_mm" in item:
        x_mm, y_mm = item["x_mm"], item["y_mm"]
    elif "u" in item and "v" in item:
        x_mm, y_mm = pixel_to_mm(item["u"], item["v"])
    elif "x" in item and "y" in item:
        x_mm, y_mm = item["x"], item["y"]
    else:
        raise ValueError("Detection cần có x_mm/y_mm, x/y hoặc u/v.")

    return DetectedObject(
        class_name=str(item["class_name"]),
        confidence=float(item["confidence"]),
        x_mm=float(x_mm),
        y_mm=float(y_mm),
        z_mm=float(item.get("z_mm", item.get("z", DEFAULT_OBJECT_Z_MM))),
    )


_detector = create_detector_backend()


def get_detected_objects() -> list[dict]:
    """Public API ổn định mà Dashboard/Safety Gate sử dụng."""
    return [normalize_detection(item).to_dict() for item in _detector.detect()]
