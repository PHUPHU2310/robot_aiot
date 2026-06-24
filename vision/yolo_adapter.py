from typing import Mapping, Sequence


class YoloDetector:
    """
    Điểm tích hợp duy nhất dành cho Dũng.

    `detect()` phải trả danh sách mapping. Tọa độ có thể là:
    - u/v: tâm bounding box theo pixel; calibration sẽ đổi sang mm.
    - x_mm/y_mm/z_mm: nếu pipeline YOLO đã tự calibration.
    """

    def detect(self) -> Sequence[Mapping]:
        raise NotImplementedError(
            "Chưa có YOLO backend. Hãy cài model/camera trong "
            "vision/yolo_adapter.py rồi đặt VISION_BACKEND='yolo'."
        )
