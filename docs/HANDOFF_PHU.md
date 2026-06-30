# Bàn giao cho Phú — Việc còn lại trước demo

> **Ngày:** 2026-06-30  
> **Từ:** Dũng  
> **Tình trạng code:** Pipeline simulation hoàn chỉnh, đang chờ số liệu thật từ nhóm phần cứng và ảnh thật để retrain YOLO.

---

## 1. Tổng quan những gì đã xong

Phú không cần viết lại bất kỳ module nào. Tất cả đã chạy ở chế độ simulation:

| Module | File | Tình trạng |
|---|---|---|
| LLM parser + Ollama | `llm/parser.py` | ✅ Hoàn chỉnh |
| Safety gate | `safety/gate.py` | ✅ Hoàn chỉnh |
| Inverse Kinematics 4DOF | `robotics/ik.py` | ✅ Có joint limits |
| Dashboard FastAPI | `app.py` | ✅ Hoàn chỉnh |
| Logging 3 CSV | `logger.py` | ✅ Hoàn chỉnh |
| YOLO adapter | `vision/yolo_adapter.py` | ✅ Hoàn chỉnh |
| Calibration homography | `vision/calibration.py` | ✅ Script sẵn sàng |
| ESP32 serial adapter | `hardware/drv8825_adapter.py` | ✅ Đã implement |
| Hardware simulator | `hardware_stub/robot_arm.py` | ✅ Dùng để test |

---

## 2. Việc Phú cần làm — theo thứ tự ưu tiên

---

### P1 — Retrain YOLO từ ảnh thật (quan trọng nhất)

Model hiện tại train trên ảnh Roboflow — chưa chụp từ camera overhead gắn trực tiếp trên bàn robot. Khi ghép phần cứng, góc nhìn và ánh sáng khác → độ chính xác có thể giảm.

**Bước 1: Thu thập ảnh thật**
```bash
# Chụp ảnh từ camera overhead đã gắn cố định
python scripts/capture_webcam_dataset.py --source 0 --output dataset_real/
```
- Chụp mỗi vật ít nhất **50–80 ảnh**, nhiều vị trí, nhiều góc xoay
- Giữ nguyên ánh sáng như lúc demo thật
- 5 vật: chai nước, cốc, bút, điện thoại, kéo

**Bước 2: Gán nhãn**
- Dùng [Roboflow](https://roboflow.com) hoặc LabelImg
- Export format YOLO v8
- Đặt vào `dataset_real/train/`, `dataset_real/valid/`

**Bước 3: Train lại**
```bash
# Sửa data_path trong train_yolo.py trước khi chạy
python train_yolo.py
```
Sau khi train xong, copy `runs/.../weights/best.pt` vào `models/best.pt`:
```bash
copy runs\detect\runs_train\<tên_run>\weights\best.pt models\best.pt
```

**Bước 4: Kiểm tra**
```bash
python -m vision.yolo_adapter
```
Phải thấy vật detect với confidence ≥ 0.70.

---

### P2 — Hiệu chuẩn Homography (sau khi camera gắn cố định)

**Điều kiện:** Camera đã gắn cố định overhead, không được xê dịch sau bước này.

**Bước 1:** Đặt 4 điểm mốc trên bàn, biết tọa độ mm thật. Ví dụ:
```
Điểm 1: góc trên-trái  →  (  0,   0) mm
Điểm 2: góc trên-phải  →  (200,   0) mm
Điểm 3: góc dưới-phải  →  (200, 150) mm
Điểm 4: góc dưới-trái  →  (  0, 150) mm
```

**Bước 2:** Chạy script, click vào 4 điểm theo đúng thứ tự trên:
```bash
python scripts/calibrate_homography.py \
    --source 0 \
    --robot-points "0,0;200,0;200,150;0,150" \
    --update-config
```
Flag `--update-config` tự ghi matrix vào `config.py` và bật `CALIBRATION_BACKEND = "homography"`.

**Bước 3:** Kiểm tra sai số:
```bash
python -c "
from vision.calibration import HomographyCalibration
from config import HOMOGRAPHY_MATRIX
cal = HomographyCalibration(HOMOGRAPHY_MATRIX)
# Đặt vật ở vị trí đã biết, so sánh với kết quả tính
print(cal.pixel_to_mm(u=..., v=...))
"
```
Sai số chấp nhận được: **< 5mm**.

---

### P3 — Cập nhật thông số phần cứng vào `config.py`

Sau khi nhóm Thắng/Trung bàn giao, cập nhật các giá trị sau trong `config.py`:

#### 3a. Chiều dài đốt tay (Thắng đo, đơn vị mm)
```python
# config.py — dòng 51
LINKS = {
    "base_height":        70,   # ← đo từ mặt bàn đến khớp vai
    "shoulder_to_elbow": 140,   # ← đo đốt 1
    "elbow_to_wrist":    130,   # ← đo đốt 2
    "wrist_to_gripper":   60,   # ← đo đốt 3 đến đầu kẹp
}
```

#### 3b. Giới hạn góc từng khớp (Trung đo, đơn vị độ)
```python
# config.py — dòng 60
JOINT_LIMITS_DEG = [
    (-180, 180),   # J1: đế xoay    ← thay bằng giới hạn thật
    ( -90,  90),   # J2: vai         ← thay bằng giới hạn thật
    (   0, 150),   # J3: khuỷu       ← thay bằng giới hạn thật
    (-150, 150),   # J4: cổ tay      ← thay bằng giới hạn thật
]
```

#### 3c. Steps/degree từng khớp (Trung tính sau khi đo tỉ số truyền)
```python
# config.py
# Công thức: (200 × microstep) / 360 × gear_ratio
# Ví dụ 1/8 step, belt 2:1: 200×8/360×2 = 8.889
STEPS_PER_DEG = {
    "j1": 4.444,   # ← thay sau khi đo
    "j2": 4.444,
    "j3": 4.444,
    "j4": 4.444,
}
```

#### 3d. Vị trí ô thả (đo thực tế trên bàn)
```python
# config.py — dòng 12
DROP_ZONE = {"x_mm": 80, "y_mm": 140, "z_mm": 20}  # ← đo vị trí ô thả thật
```

---

### P4 — Bật backend ESP32 (sau khi Trung xong firmware)

Chỉ cần đổi 2 dòng trong `config.py`:

```python
# Bước 1: đổi port (kiểm tra trên Pi: ls /dev/ttyUSB*)
ESP32_PORT = "/dev/ttyUSB0"   # hoặc /dev/ttyACM0

# Bước 2: bật backend thật
HARDWARE_BACKEND = "drv8825"  # thay "simulator"
```

Test ngay sau khi đổi:
```bash
python -c "
from hardware.robot_arm import RobotArm
r = RobotArm()
print('Ready:', r.is_ready())
print(r.home_all())
"
```

---

### P5 — Cải tiến IK: chọn giải pháp elbow-up hoặc elbow-down

Hiện tại `robotics/ik.py` chỉ tính elbow-up (j3 = +acos). Nếu tư thế đó vượt joint limit, raise ValueError ngay cả khi elbow-down vẫn hợp lệ.

Cần sửa `robotics/ik.py` để thử cả 2 nghiệm:

```python
# robotics/ik.py — thay khối tính j3/j2
for sign in (1, -1):   # thử elbow-up trước, rồi elbow-down
    j3_rad = sign * math.acos(cos_j3)
    beta   = math.atan2(l2 * math.sin(j3_rad), l1 + l2 * math.cos(j3_rad))
    j2_rad = alpha - beta
    j2     = math.degrees(j2_rad)
    j3     = math.degrees(j3_rad)
    j4     = -(j2 + j3)

    joints = [round(j1, 2), round(j2, 2), round(j3, 2), round(j4, 2)]

    # Kiểm tra joint limits cho nghiệm này
    if all(lo <= a <= hi for a, (lo, hi) in zip(joints, JOINT_LIMITS_DEG)):
        break   # nghiệm hợp lệ, dùng luôn
else:
    raise ValueError("Không có nghiệm IK nào thỏa joint limits.")
```

---

## 3. Checklist trước demo

```
Phần code (Phú):
[ ] Retrain YOLO từ ảnh overhead thật, best.pt mới vào models/
[ ] Chạy calibrate_homography.py với camera thật, --update-config
[ ] Cập nhật LINKS từ số đo Thắng
[ ] Cập nhật JOINT_LIMITS_DEG từ số đo Trung
[ ] Cập nhật STEPS_PER_DEG từ số đo Trung
[ ] Cập nhật DROP_ZONE vị trí ô thả thật
[ ] Sửa IK dual-solution (P5)
[ ] Đổi HARDWARE_BACKEND = "drv8825" khi firmware xong
[ ] Chạy unit test: python -m pytest tests/ -v
[ ] Chạy end-to-end: uvicorn app:app, thử lệnh "gắp chai nước"

Chờ từ nhóm phần cứng:
[ ] Bảng LINKS (chiều dài đốt tay, mm) — Thắng
[ ] Bảng JOINT_LIMITS_DEG (min/max từng khớp, độ) — Trung
[ ] Bảng STEPS_PER_DEG (tỉ số truyền, microstep) — Trung
[ ] Xác nhận ESP32 firmware xong, ACK protocol OK — Trung
[ ] Xác nhận camera gắn cố định overhead — Thắng
[ ] Xác nhận vị trí ô thả (x_mm, y_mm) — Thắng
```

---

## 4. Cấu trúc file cần biết

```
config.py                  ← MỌI thông số tập trung ở đây
hardware/drv8825_adapter.py ← Serial ESP32, Trung không cần sửa
robotics/ik.py             ← IK 4DOF, Phú cần cải tiến dual-solution
vision/yolo_adapter.py     ← YOLO adapter, đã xong
scripts/calibrate_homography.py  ← Chạy khi camera gắn xong
scripts/capture_webcam_dataset.py ← Thu thập ảnh thật
train_yolo.py              ← Retrain YOLO
models/best.pt             ← Weights đang dùng
logs/                      ← detection_log.csv, decision_log.csv, action_log.csv
```

---

## 5. Chạy nhanh để kiểm tra hiện trạng

```bash
cd d:\robot_aiot
venv\Scripts\Activate.ps1

# Unit test
python -m pytest tests/ -v

# Test YOLO (cần webcam)
python -m vision.yolo_adapter

# Test IK
python -c "from robotics.ik import inverse_kinematics; print(inverse_kinematics(180, 80, 40))"

# Chạy toàn bộ Dashboard
uvicorn app:app --reload --host 0.0.0.0 --port 8000
# Mở: http://localhost:8000
# Thử lệnh: gắp chai nước
```

---

## 6. Liên hệ khi cần

- **Thắng**: số đo cơ khí, vị trí camera, vị trí ô thả
- **Trung**: joint limits, steps/deg, xác nhận firmware ESP32, port serial
- **Dũng**: bất kỳ vấn đề nào về YOLO, calibration, vision pipeline

> Mọi thông số phần cứng chỉ cần điền vào `config.py` — không cần sửa code pipeline.
