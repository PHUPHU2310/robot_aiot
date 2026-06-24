# Kiến trúc hệ thống AIoT Robot Pick & Place

## 1. Tổng quan

Hệ thống nhận lệnh ngôn ngữ tự nhiên, xác định vật thể cần thao tác, kiểm tra
an toàn, tính góc khớp và gửi lệnh tới robot. Các module được nối với nhau bằng
API ổn định để nhóm Vision và nhóm phần cứng có thể thay backend mà không sửa
Dashboard, Safety Gate hoặc Inverse Kinematics.

```text
User Command
     ↓
LLM Parser
     ↓
Safety Gate
     ↓
Object Detection
     ↓
Coordinate Transform
     ↓
Inverse Kinematics
     ↓
Robot Arm
```

Trong code hiện tại, Object Detection được lấy trước khi gọi Safety Gate vì
Safety Gate cần danh sách vật thể, confidence và tọa độ để quyết định có cho
phép điều khiển hay không. Luồng dữ liệu thực tế là:

```text
User Command ──→ LLM Parser ───────────────┐
                                           ├─→ Safety Gate
Camera ─→ Object Detection ─→ Calibration ─┘       ↓
                                             Inverse Kinematics
                                                    ↓
                                                Robot Arm
```

## 2. Trách nhiệm từng module

### User Command và Dashboard

`app.py` nhận câu lệnh từ Dashboard hoặc endpoint `/api/command`, điều phối các
module và hiển thị quyết định AI, kết quả IK, trạng thái robot và lịch sử lệnh.

### LLM Parser

`llm/parser.py` gọi Ollama `qwen3:0.6b` để chuyển câu lệnh thành dữ liệu có cấu
trúc:

```json
{
  "action": "pick_place",
  "target_object": "chai_nuoc"
}
```

Nếu Ollama không sẵn sàng, hệ thống tự chuyển sang rule-based parser.

### Object Detection

`vision/detect.py` là facade chung. Backend demo hoặc YOLO đều phải được chuẩn
hóa thành:

```python
{
    "class_name": "chai_nuoc",
    "confidence": 0.91,
    "x_mm": 180.0,
    "y_mm": 80.0,
    "z_mm": 20.0,
}
```

Dũng chỉ triển khai `vision/yolo_adapter.py` và đổi:

```python
VISION_BACKEND = "yolo"
```

### Coordinate Transform

`vision/calibration.py` chuyển tâm bounding box từ pixel camera sang millimeter
trong hệ tọa độ robot.

Backend hiện tại là phép biến đổi tuyến tính. Khi có camera thật, điền ma trận
từ `cv2.findHomography()` vào `HOMOGRAPHY_MATRIX` và đổi:

```python
CALIBRATION_BACKEND = "homography"
```

### Safety Gate

`safety/gate.py` chỉ cho phép thao tác khi:

- LLM nhận diện được hành động và vật thể.
- Camera tìm thấy đúng một vật thể phù hợp.
- Confidence đạt ngưỡng cấu hình.
- Tọa độ nằm trong workspace của robot.

### Inverse Kinematics

`robotics/ik.py` nhận tọa độ millimeter và trả bốn góc khớp theo thứ tự:

```text
[J1, J2, J3, J4]
```

Đơn vị của tất cả góc là độ.

### Robot Arm

`hardware/robot_arm.py` là facade điều khiển thống nhất. Backend hiện tại là
simulator. Nhóm phần cứng chỉ triển khai `hardware/drv8825_adapter.py` và đổi:

```python
HARDWARE_BACKEND = "drv8825"
```

## 3. API contract cho nhóm

### Vision API

```python
get_detected_objects() -> list[dict]
```

Output bắt buộc có:

```text
class_name, confidence, x_mm, y_mm, z_mm
```

### Calibration API

```python
pixel_to_mm(u: float, v: float) -> tuple[float, float]
```

Input là pixel camera; output là `(x_mm, y_mm)` trong hệ tọa độ robot.

### Hardware API

```python
home_all()
move_joints(joints)
gripper(open=True)
get_pose()
is_ready()
```

`move_joints()` nhận đúng bốn góc `[J1, J2, J3, J4]`. Mọi backend phải trả
`RobotCommandResult` cho các lệnh điều khiển và không được chứa logic IK hoặc
Safety Gate.

## 4. Quy tắc tích hợp

- Không import YOLO hoặc OpenCV trực tiếp trong `app.py`.
- Không import GPIO hoặc DRV8825 trực tiếp trong `app.py`.
- Không thay đổi schema detection sau `vision/detect.py`.
- Tọa độ giữa Vision, Safety Gate và IK luôn dùng millimeter.
- Góc giữa IK và Hardware luôn dùng độ.
- Backend mới phải vượt qua contract tests trước khi ghép hệ thống.

Chạy kiểm thử:

```powershell
venv\Scripts\python -m unittest discover -s tests -v
```

Chi tiết triển khai adapter nằm trong `docs/INTEGRATION.md`.
