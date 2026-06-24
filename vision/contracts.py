import math
from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence, Tuple


@dataclass(frozen=True)
class DetectedObject:
    """Contract chuẩn giữa Vision và Safety Gate. Tọa độ luôn tính bằng mm."""

    class_name: str
    confidence: float
    x_mm: float
    y_mm: float
    z_mm: float

    def __post_init__(self):
        if not self.class_name.strip():
            raise ValueError("class_name không được để trống.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence phải nằm trong khoảng 0..1.")
        if not all(math.isfinite(value) for value in (self.x_mm, self.y_mm, self.z_mm)):
            raise ValueError("Tọa độ vật thể phải là số hữu hạn.")

    def to_dict(self) -> dict:
        return {
            "class_name": self.class_name,
            "confidence": self.confidence,
            "x_mm": self.x_mm,
            "y_mm": self.y_mm,
            "z_mm": self.z_mm,
        }


class DetectorBackend(Protocol):
    """Backend YOLO/static chỉ cần trả raw detections theo mapping."""

    def detect(self) -> Sequence[Mapping]:
        ...


class CalibrationBackend(Protocol):
    """Contract chuyển điểm ảnh camera thành tọa độ mặt bàn robot."""

    def pixel_to_mm(self, u: float, v: float) -> Tuple[float, float]:
        ...
