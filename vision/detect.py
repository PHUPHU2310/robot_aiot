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
    - x/y/z, hiểu là mm
    - u/v pixel, tự đi qua calibration
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


def normalize_detection_to_dict(detection: Mapping) -> dict:
    """Chuẩn hóa detection sang dict mm, giữ thêm metadata camera/bbox nếu có."""
    item = dict(detection)
    data = normalize_detection(item).to_dict()
    for key in ("u", "v", "bbox", "x1", "y1", "x2", "y2"):
        if key in item:
            data[key] = item[key]
    return data


_detector = create_detector_backend()
_static_detector = StaticDetector()
_last_vision_error: str | None = None


def get_camera_frame_data_uri() -> str | None:
    """Ảnh camera gần nhất đã vẽ bbox, nếu backend có hỗ trợ."""
    getter = getattr(_detector, "get_last_frame_data_uri", None)
    if callable(getter):
        return getter()
    return None


def capture_vision_state() -> dict:
    """
    Lấy trọn trạng thái Vision cho Dashboard.

    Nếu YOLO/camera lỗi, Dashboard vẫn chạy bằng mock data và hiển thị cảnh báo.
    """
    global _last_vision_error

    try:
        raw_objects = list(_detector.detect())
        objects = [normalize_detection_to_dict(item) for item in raw_objects]
        _last_vision_error = None
        fallback_used = False
    except Exception as exc:
        raw_objects = list(_static_detector.detect())
        objects = [normalize_detection_to_dict(item) for item in raw_objects]
        _last_vision_error = f"{type(exc).__name__}: {exc}"
        fallback_used = True

    return {
        "backend": VISION_BACKEND,
        "fallback_used": fallback_used,
        "warning": _last_vision_error,
        "objects": objects,
        "camera_frame": None if fallback_used else get_camera_frame_data_uri(),
    }


def get_detected_objects() -> list[dict]:
    """Public API ổn định mà Dashboard/Safety Gate sử dụng."""
    return capture_vision_state()["objects"]
