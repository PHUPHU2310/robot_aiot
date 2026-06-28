"""
vision/yolo_adapter.py  —  YOLO backend thật (Dũng).

Thay cho bản mock. `detect()` trả danh sách dict theo đúng contract:
- class_name : tên tiếng Việt khớp parser của Phú (chai_nuoc, coc, ...)
- confidence : điểm tin cậy YOLO (gate 0.70 trong config sẽ lọc lần cuối)
- u, v       : tâm bbox theo PIXEL  -> calibration đổi sang mm
- z_mm       : chiều cao gắp, tra theo class (camera overhead không đo được z)

Bật backend này bằng: VISION_BACKEND = "yolo" trong config.py
"""

import os
from typing import Mapping, Sequence

import cv2
from ultralytics import YOLO

import config

# ---- Map tên class tiếng Anh (trong best.pt) -> tên tiếng Việt của hệ thống ----
# Sửa lại nếu nhóm chọn 5 vật khác. Tên phải khớp với parser/LLM của Phú.
CLASS_MAP_EN_TO_VI = {
    "bottle":  "chai_nuoc",
    "cup":     "coc",
    "pen":     "but",
    "phone":   "dien_thoai",
    "scissor": "keo",
}

# ---- Chiều cao gắp z (mm) theo từng class ----
# Camera nhìn từ trên xuống KHÔNG suy ra được z, nên tra theo loại vật.
# Số tạm; nhóm phần cứng đo lại theo vật + mặt bàn thật rồi cập nhật.
Z_BY_CLASS_MM = {
    "chai_nuoc":  40,
    "coc":        40,
    "but":        10,
    "dien_thoai": 10,
    "keo":        10,
}
DEFAULT_Z_MM = 20

# ---- Đọc cấu hình (có default để chạy được ngay nếu chưa thêm vào config) ----
MODEL_PATH = getattr(
    config, "YOLO_MODEL_PATH",
    "D:/robot_aiot/runs/detect/runs_train/household5-2/weights/best.pt",
)
# Nguồn frame: 0 = webcam laptop | đường dẫn ảnh ("test.jpg") | URL stream của Pi
FRAME_SOURCE = getattr(config, "YOLO_FRAME_SOURCE", 0)
# Ngưỡng detect thô (thấp); safety gate 0.70 mới là ngưỡng lọc cuối.
RAW_CONF = getattr(config, "YOLO_CONF", 0.25)


class YoloDetector:
    def __init__(self, model_path: str = MODEL_PATH, frame_source=FRAME_SOURCE):
        if not os.path.isfile(model_path):
            raise FileNotFoundError(
                f"Không thấy weights YOLO: {model_path}. "
                "Đặt đúng đường dẫn best.pt vào YOLO_MODEL_PATH trong config.py."
            )
        self.model = YOLO(model_path)
        self.frame_source = frame_source

    def _grab_frame(self):
        """Lấy 1 frame: từ ảnh tĩnh, webcam, hoặc URL stream của Pi."""
        src = self.frame_source
        if isinstance(src, str) and os.path.isfile(src):       # ảnh tĩnh
            img = cv2.imread(src)
            if img is None:
                raise RuntimeError(f"Không đọc được ảnh: {src}")
            return img

        # camera index (int) hoặc URL stream (str)
        cap = cv2.VideoCapture(src)
        if not cap.isOpened() and isinstance(src, int):
            cap.release()
            cap = cv2.VideoCapture(src, cv2.CAP_DSHOW)   # Windows: backend DirectShow
        if not cap.isOpened():
            cap.release()
            raise RuntimeError(f"Không mở được camera/nguồn: {src}")

        ok, frame = False, None
        for _ in range(10):          # bỏ vài frame đầu (webcam mới mở hay trả frame đen)
            ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            raise RuntimeError(f"Không lấy được frame từ nguồn: {src}")
        return frame

    def detect(self) -> Sequence[Mapping]:
        frame = self._grab_frame()
        results = self.model.predict(frame, conf=RAW_CONF, verbose=False)

        detections = []
        for r in results:
            for b in r.boxes:
                en_name = self.model.names[int(b.cls)]
                vi_name = CLASS_MAP_EN_TO_VI.get(en_name)
                if vi_name is None:           # bỏ class ngoài 5 vật quan tâm
                    continue
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                detections.append({
                    "class_name": vi_name,
                    "confidence": float(b.conf),
                    "u": (x1 + x2) / 2.0,     # tâm bbox theo pixel
                    "v": (y1 + y2) / 2.0,
                    "z_mm": Z_BY_CLASS_MM.get(vi_name, DEFAULT_Z_MM),
                })
        if not detections:
            return []
        # Demo đặt 1 vật/lần → chỉ giữ vật tin cậy nhất trong khung
        if getattr(config, "YOLO_SINGLE_BEST", True):
            best = max(detections, key=lambda d: d["confidence"])
            return [best]
        return detections


# ---- Test nhanh adapter độc lập (không cần chạy cả pipeline) ----
# Chạy:  python vision/yolo_adapter.py
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