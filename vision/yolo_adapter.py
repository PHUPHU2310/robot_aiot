"""
vision/yolo_adapter.py  —  YOLO backend thật (Dũng).

`detect()` trả danh sách dict theo contract của Phú (xem README mục
"Hướng dẫn cho Dũng"). Ngoài ra adapter còn lưu lại frame đã vẽ bbox gần nhất
và phơi ra qua get_last_frame_data_uri() — detect.py sẽ tự gọi hàm này
(xem get_camera_frame_data_uri trong vision/detect.py), Dashboard hiển thị
ảnh đó mà không cần sửa app.py.
"""

import base64
import os
from pathlib import Path
from typing import Mapping, Optional, Sequence

import cv2
from ultralytics import YOLO

import config

_PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ---- Map tên class tiếng Anh (trong best.pt) -> tên tiếng Việt của hệ thống ----
CLASS_MAP_EN_TO_VI = {
    "bottle":  "chai_nuoc",
    "cup":     "coc",
    "pen":     "but",
    "phone":   "dien_thoai",
    "scissor": "keo",
}

# ---- Chiều cao gắp z (mm) theo từng class (camera overhead không đo được z) ----
Z_BY_CLASS_MM = {
    "chai_nuoc":  40,
    "coc":        40,
    "but":        10,
    "dien_thoai": 10,
    "keo":        10,
}
DEFAULT_Z_MM = 20

MODEL_PATH = getattr(config, "YOLO_MODEL_PATH", "models/best.pt")
FRAME_SOURCE = getattr(config, "YOLO_FRAME_SOURCE", 0)
RAW_CONF = getattr(config, "YOLO_CONF", 0.45)
SINGLE_BEST = getattr(config, "YOLO_SINGLE_BEST", True)


class YoloDetector:
    def __init__(self, model_path: str = MODEL_PATH, frame_source=FRAME_SOURCE):
        resolved = Path(model_path) if Path(model_path).is_absolute() else _PROJECT_ROOT / model_path
        if not resolved.is_file():
            raise FileNotFoundError(
                f"Không thấy weights YOLO: {resolved}. "
                "Đặt đúng đường dẫn best.pt vào YOLO_MODEL_PATH trong config.py."
            )
        self.model = YOLO(str(resolved))
        self.frame_source = frame_source
        self._last_frame_data_uri: Optional[str] = None

    def _grab_frame(self):
        src = self.frame_source
        if isinstance(src, str) and src.isdigit():
            src = int(src)
        if isinstance(src, str) and os.path.isfile(src):
            img = cv2.imread(src)
            if img is None:
                raise RuntimeError(f"Không đọc được ảnh: {src}")
            return img

        cap = cv2.VideoCapture(src)
        if not cap.isOpened() and isinstance(src, int):
            cap.release()
            cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)   # Windows
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"Không mở được camera/nguồn: {src}")

        ok, frame = False, None
        for _ in range(10):           # bỏ vài frame đầu (webcam mới mở hay đen)
            ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            raise RuntimeError(f"Không lấy được frame từ nguồn: {src}")
        return frame

    def detect(self) -> Sequence[Mapping]:
        frame = self._grab_frame()
        results = self.model.predict(frame, conf=RAW_CONF, verbose=False)
        r = results[0]

        # --- Vẽ bbox lên frame và lưu thành data URI để Dashboard hiển thị ---
        annotated = r.plot()                       # ảnh numpy đã có bbox + nhãn
        ok, buf = cv2.imencode(".jpg", annotated)
        if ok:
            b64 = base64.b64encode(buf).decode("ascii")
            self._last_frame_data_uri = f"data:image/jpeg;base64,{b64}"

        detections = []
        for b in r.boxes:
            en_name = self.model.names[int(b.cls)]
            vi_name = CLASS_MAP_EN_TO_VI.get(en_name)
            if vi_name is None:        # bỏ class ngoài 5 vật quan tâm
                continue
            x1, y1, x2, y2 = b.xyxy[0].tolist()
            detections.append({
                "class_name": vi_name,
                "confidence": float(b.conf),
                "u": (x1 + x2) / 2.0,
                "v": (y1 + y2) / 2.0,
                "z_mm": Z_BY_CLASS_MM.get(vi_name, DEFAULT_Z_MM),
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
            })

        if not detections:
            return []
        if SINGLE_BEST:
            best = max(detections, key=lambda d: d["confidence"])
            return [best]
        return detections

    def get_last_frame_data_uri(self) -> Optional[str]:
        """Được detect.py gọi tự động để lấy ảnh hiển thị lên Dashboard."""
        return self._last_frame_data_uri


# ---- Test nhanh adapter độc lập: python -m vision.yolo_adapter [nguồn] ----
if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else FRAME_SOURCE
    if isinstance(src, str) and src.isdigit():
        src = int(src)
    det = YoloDetector(frame_source=src)
    found = det.detect()
    print(f"Số vật nhận được: {len(found)}")
    for d in found:
        flag = "OK(>=0.70)" if d["confidence"] >= 0.70 else "thấp"
        print(f"  {d['class_name']:12s} conf={d['confidence']:.2f} "
              f"u={d['u']:.0f} v={d['v']:.0f} z={d['z_mm']}mm  [{flag}]")