from typing import Tuple

from config import (
    CALIBRATION_BACKEND,
    CALIBRATION_ORIGIN_PX,
    CALIBRATION_SCALE_MM_PER_PX,
    HOMOGRAPHY_MATRIX,
)
from vision.contracts import CalibrationBackend


class LinearCalibration:
    """Calibration giả lập dùng gốc pixel và tỉ lệ mm/pixel."""

    def pixel_to_mm(self, u: float, v: float) -> Tuple[float, float]:
        x_mm = (u - CALIBRATION_ORIGIN_PX["u"]) * CALIBRATION_SCALE_MM_PER_PX["x"]
        y_mm = (v - CALIBRATION_ORIGIN_PX["v"]) * CALIBRATION_SCALE_MM_PER_PX["y"]
        return round(x_mm, 2), round(y_mm, 2)


class HomographyCalibration:
    """Biến đổi phối cảnh 3×3; ma trận được tạo từ cv2.findHomography()."""

    def __init__(self, matrix):
        if len(matrix) != 3 or any(len(row) != 3 for row in matrix):
            raise ValueError("HOMOGRAPHY_MATRIX phải là ma trận 3x3.")
        self.matrix = [[float(value) for value in row] for row in matrix]

    def pixel_to_mm(self, u: float, v: float) -> Tuple[float, float]:
        h = self.matrix
        denominator = h[2][0] * u + h[2][1] * v + h[2][2]
        if abs(denominator) < 1e-9:
            raise ValueError("Điểm pixel không thể biến đổi bằng homography hiện tại.")
        x_mm = (h[0][0] * u + h[0][1] * v + h[0][2]) / denominator
        y_mm = (h[1][0] * u + h[1][1] * v + h[1][2]) / denominator
        return round(x_mm, 2), round(y_mm, 2)


def create_calibration_backend(name: str = CALIBRATION_BACKEND) -> CalibrationBackend:
    if name == "linear":
        return LinearCalibration()
    if name == "homography":
        return HomographyCalibration(HOMOGRAPHY_MATRIX)
    raise ValueError(f"Calibration backend không hợp lệ: {name}")


_calibration = create_calibration_backend()


def pixel_to_mm(u: float, v: float) -> Tuple[float, float]:
    """Public API ổn định; code bên ngoài không phụ thuộc backend calibration."""
    return _calibration.pixel_to_mm(float(u), float(v))
