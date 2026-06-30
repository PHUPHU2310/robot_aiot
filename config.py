# Cấu hình chung cho dự án robot_aiot

# Vật thể demo tạm thời, sau này thay bằng output YOLO của Dũng
DETECTED_OBJECTS = [
    {"class_name": "chai_nuoc", "confidence": 0.91, "x_mm": 180, "y_mm": 80, "z_mm": 20},
    {"class_name": "coc", "confidence": 0.87, "x_mm": 130, "y_mm": -60, "z_mm": 20},
    {"class_name": "but", "confidence": 0.82, "x_mm": 220, "y_mm": 30, "z_mm": 10},
    {"class_name": "dien_thoai", "confidence": 0.88, "x_mm": 100, "y_mm": -110, "z_mm": 10},
    {"class_name": "keo", "confidence": 0.86, "x_mm": 210, "y_mm": -40, "z_mm": 10},
]

DROP_ZONE = {"x_mm": 80, "y_mm": 140, "z_mm": 20}

# Backend phần cứng hiện tại. Sau này đổi thành "drv8825" khi driver thật sẵn sàng.
HARDWARE_BACKEND = "simulator"

# Backend vision: "static" hoặc "yolo".
VISION_BACKEND = "yolo"

# Backend calibration: "linear" hoặc "homography".
CALIBRATION_BACKEND = "linear"

# Calibration giả lập: tọa độ mm = (pixel - gốc pixel) * tỉ lệ.
# Khi có ảnh bàn robot thật, thay bằng ma trận homography đã hiệu chuẩn.
CALIBRATION_ORIGIN_PX = {"u": 320.0, "v": 240.0}
CALIBRATION_SCALE_MM_PER_PX = {"x": 0.5, "y": -0.5}
DEFAULT_OBJECT_Z_MM = 20.0

# Thay ma trận này bằng output của cv2.findHomography() rồi chọn "homography".
HOMOGRAPHY_MATRIX = [
    [1.0, 0.0, 0.0],
    [0.0, 1.0, 0.0],
    [0.0, 0.0, 1.0],
]

# Ollama local API. Nếu Ollama không chạy, hệ thống tự dùng parser rule-based.
OLLAMA_ENABLED = True
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen3:0.6b"
# Cold start trên CPU có thể mất hơn 30 giây khi máy đang bận.
OLLAMA_TIMEOUT_SECONDS = 90

CONFIDENCE_THRESHOLD = 0.70
WORKSPACE = {
    "min_radius": 60,
    "max_radius": 300,
    "min_z": 0,
    "max_z": 180,
}

# Link length giả lập, đơn vị mm. Sau này thay bằng số đo thật từ nhóm phần cứng.
LINKS = {
    "base_height": 70,
    "shoulder_to_elbow": 140,
    "elbow_to_wrist": 130,
    "wrist_to_gripper": 60,
}
# Giới hạn góc từng khớp (độ). Cập nhật theo bàn giao của nhóm phần cứng.
# [J1_min, J1_max], [J2_min, J2_max], [J3_min, J3_max], [J4_min, J4_max]
JOINT_LIMITS_DEG = [
    (-180, 180),   # J1: đế xoay
    (-90,   90),   # J2: vai
    (  0,  150),   # J3: khuỷu
    (-150, 150),   # J4: cổ tay
]

# ── ESP32 Serial (chỉ dùng khi HARDWARE_BACKEND = "drv8825") ──────────────────
# Pi/Linux: "/dev/ttyUSB0" hoặc "/dev/ttyACM0"
# Windows dev: "COM3" (kiểm tra Device Manager)
ESP32_PORT     = "/dev/ttyUSB0"
ESP32_BAUDRATE = 115200
ESP32_TIMEOUT_SEC = 10          # giây chờ ACK từ ESP32

# Tỉ số bước/độ từng khớp — cập nhật sau khi Thắng/Trung đo tỉ số truyền thật.
# Công thức: steps_per_deg = (200 * microstep) / 360 * gear_ratio
# Ví dụ 1/8 step, không gear: 200*8/360 = 4.444
STEPS_PER_DEG = {
    "j1": 4.444,   # đế xoay
    "j2": 4.444,   # vai
    "j3": 4.444,   # khuỷu
    "j4": 4.444,   # cổ tay
}

YOLO_MODEL_PATH = "models/best.pt"
YOLO_FRAME_SOURCE = 0        # 0 = webcam | "test.jpg" = ảnh tĩnh | URL stream của Pi
YOLO_CONF = 0.45             # ngưỡng detect thô; gate 0.70 lọc lần cuối
YOLO_SINGLE_BEST = False     # False để Dashboard thấy đầy đủ bbox/vật thể trong khung
