"""
YOLO11n backend cho Dashboard.

Adapter này giữ contract ổn định cho phần AI Control:

[
    {
        "class_name": "chai_nuoc",
        "confidence": 0.91,
        "u": 520,
        "v": 340,
        "bbox": {"x1": 480, "y1": 300, "x2": 560, "y2": 380},
        "z_mm": 20,
    }
]

`vision.detect` sẽ tự gọi `pixel_to_mm(u, v)` để đổi pixel sang tọa độ robot.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import Mapping, Sequence

import config

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_MODEL_PATH = PROJECT_ROOT / "runs" / "detect" / "runs_train" / "household5-2" / "weights" / "best.pt"

# Tên class trong dataset5/data.yaml -> tên class chuẩn của pipeline.
CLASS_MAP_EN_TO_VI = {
    "bottle": "chai_nuoc",
    "cup": "coc",
    "pen": "but",
    "phone": "dien_thoai",
    "scissor": "keo",
    "scissors": "keo",
}

# Camera nhìn từ trên xuống không đo trực tiếp z, nên tạm tra theo loại vật.
Z_BY_CLASS_MM = {
    "chai_nuoc": 40,
    "coc": 40,
    "but": 10,
    "dien_thoai": 10,
    "keo": 10,
}

DISPLAY_COLORS = {
    "chai_nuoc": (56, 189, 248),
    "coc": (74, 222, 128),
    "but": (250, 204, 21),
    "dien_thoai": (168, 85, 247),
    "keo": (251, 113, 133),
}


def resolve_project_path(value: str | os.PathLike) -> Path:
    """Cho phép config dùng path tương đối để Dũng clone về máy khác vẫn chạy."""
    path = Path(value)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


class YoloDetector:
    def __init__(self, model_path=None, frame_source=None):
        self.model_path = resolve_project_path(
            model_path or getattr(config, "YOLO_MODEL_PATH", DEFAULT_MODEL_PATH)
        )
        self.frame_source = getattr(config, "YOLO_FRAME_SOURCE", 0) if frame_source is None else frame_source
        self.raw_conf = float(getattr(config, "YOLO_CONF", 0.45))
        self.single_best = bool(getattr(config, "YOLO_SINGLE_BEST", False))
        self.model = None
        self.last_frame = None
        self.last_annotated_frame = None
        self.last_detections: list[dict] = []

    def _load_model(self):
        if self.model is not None:
            return self.model

        if not self.model_path.is_file():
            raise FileNotFoundError(
                f"Không thấy weights YOLO: {self.model_path}. "
                "Kiểm tra YOLO_MODEL_PATH trong config.py hoặc file runs/.../best.pt."
            )

        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "Chưa cài ultralytics. Chạy: pip install -r requirements.txt"
            ) from exc

        self.model = YOLO(str(self.model_path))
        return self.model

    def _grab_frame(self):
        try:
            import cv2
        except ImportError as exc:
            raise RuntimeError(
                "Chưa cài OpenCV. Chạy: pip install -r requirements.txt"
            ) from exc

        src = self.frame_source
        if isinstance(src, str) and src.isdigit():
            src = int(src)

        if isinstance(src, str):
            image_path = resolve_project_path(src)
            if image_path.is_file():
                frame = cv2.imread(str(image_path))
                if frame is None:
                    raise RuntimeError(f"Không đọc được ảnh: {image_path}")
                return frame

        cap = cv2.VideoCapture(src)
        if not cap.isOpened() and isinstance(src, int):
            cap.release()
            cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"Không mở được camera/nguồn: {src}")

        ok, frame = False, None
        for _ in range(10):
            ok, frame = cap.read()
        cap.release()

        if not ok or frame is None:
            raise RuntimeError(f"Không lấy được frame từ nguồn: {src}")
        return frame

    def detect(self) -> Sequence[Mapping]:
        model = self._load_model()
        frame = self._grab_frame()
        results = model.predict(frame, conf=self.raw_conf, verbose=False)

        detections: list[dict] = []
        for result in results:
            for box in result.boxes:
                model_name = model.names[int(box.cls)]
                class_name = CLASS_MAP_EN_TO_VI.get(str(model_name).lower())
                if class_name is None:
                    continue

                x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
                detections.append({
                    "class_name": class_name,
                    "confidence": float(box.conf),
                    "u": round((x1 + x2) / 2.0, 2),
                    "v": round((y1 + y2) / 2.0, 2),
                    "bbox": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "x2": round(x2, 2),
                        "y2": round(y2, 2),
                    },
                    "z_mm": Z_BY_CLASS_MM.get(class_name, getattr(config, "DEFAULT_OBJECT_Z_MM", 20.0)),
                })

        detections.sort(key=lambda item: item["confidence"], reverse=True)
        if self.single_best and detections:
            detections = [detections[0]]

        self.last_frame = frame
        self.last_detections = detections
        self.last_annotated_frame = self._draw_detections(frame, detections)
        return detections

    def _draw_detections(self, frame, detections: Sequence[Mapping]):
        import cv2

        annotated = frame.copy()
        for item in detections:
            bbox = item.get("bbox")
            if not bbox:
                continue
            x1 = int(bbox["x1"])
            y1 = int(bbox["y1"])
            x2 = int(bbox["x2"])
            y2 = int(bbox["y2"])
            class_name = str(item["class_name"])
            color = DISPLAY_COLORS.get(class_name, (56, 189, 248))
            label = f"{class_name} {item['confidence']:.2f}"

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            cv2.circle(annotated, (int(item["u"]), int(item["v"])), 4, color, -1)
            cv2.putText(
                annotated,
                label,
                (x1, max(y1 - 8, 18)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                color,
                2,
                cv2.LINE_AA,
            )
        return annotated

    def get_last_frame_data_uri(self) -> str | None:
        frame = self.last_annotated_frame if self.last_annotated_frame is not None else self.last_frame
        if frame is None:
            return None

        import cv2

        ok, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
        if not ok:
            return None
        encoded = base64.b64encode(buffer).decode("ascii")
        return f"data:image/jpeg;base64,{encoded}"


if __name__ == "__main__":
    import sys

    source = sys.argv[1] if len(sys.argv) > 1 else getattr(config, "YOLO_FRAME_SOURCE", 0)
    detector = YoloDetector(frame_source=source)
    found = detector.detect()
    print(f"Số vật nhận được: {len(found)}")
    for item in found:
        print(
            f"{item['class_name']:12s} conf={item['confidence']:.2f} "
            f"u={item['u']:.0f} v={item['v']:.0f} bbox={item['bbox']}"
        )
