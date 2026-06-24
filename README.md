# robot_aiot — AIoT Robot Pick & Place

Prototype điều khiển tay máy 4DOF bằng lệnh tiếng Việt, kết hợp:

- Ollama Qwen3 để phân tích lệnh.
- Object Detection và Camera Calibration.
- Safety Gate.
- Inverse Kinematics.
- Hardware Adapter.
- FastAPI Dashboard, mô phỏng 2D và nhật ký hệ thống.

Project hiện chạy hoàn chỉnh với dữ liệu vật thể và robot giả lập. Các module
đã có contract ổn định để nhóm Vision và phần cứng thay backend mà không cần
sửa lại toàn bộ pipeline.

## Quick Start

### 1. Clone project

```bash
git clone https://github.com/PHUPHU2310/robot_aiot.git
cd robot_aiot
```

### 2. Tạo môi trường Python

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell chặn script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
```

Linux hoặc Raspberry Pi:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Cài Ollama

Cài Ollama, sau đó tải model:

```bash
ollama pull qwen3:0.6b
ollama list
```

Ollama không bắt buộc để mở Dashboard. Nếu Ollama chưa hoạt động, hệ thống tự
chuyển sang `rule_based_fallback`.

### 4. Chạy project

```bash
uvicorn app:app --reload
```

Hoặc trên Windows khi chưa activate `venv`:

```powershell
venv\Scripts\python -m uvicorn app:app --reload
```

Mở:

- Dashboard: <http://127.0.0.1:8000>
- Command History: <http://127.0.0.1:8000/history>
- FastAPI Docs: <http://127.0.0.1:8000/docs>

### 5. Test nhanh

Nhập trên Dashboard:

```text
gắp chai nước
```

Kết quả mong đợi:

```text
Parser: ollama:qwen3:0.6b
Target: chai_nuoc
Safety Gate: Allowed
IK: J1, J2, J3, J4
Robot: Pick Success, Place Success
Status: SIMULATED_SUCCESS
```

Có thể thử thêm:

```text
gắp cốc
gắp bút
hãy lấy cái cốc giúp tôi
```

Lệnh không hợp lệ như `hãy nhảy múa` phải bị Safety Gate từ chối.

## Kiến trúc

```text
User Command ──→ LLM Parser ───────────────┐
                                           ├─→ Safety Gate
Camera ─→ Object Detection ─→ Calibration ─┘       ↓
                                             Inverse Kinematics
                                                    ↓
                                             Hardware Adapter
                                                    ↓
                                                Robot Arm
```

Luồng xử lý:

1. Dashboard nhận lệnh tiếng Việt.
2. Ollama trả `action` và `target_object`.
3. Vision trả vật thể cùng tọa độ chuẩn theo millimeter.
4. Safety Gate kiểm tra confidence và workspace.
5. IK tính bốn góc `[J1, J2, J3, J4]`.
6. Hardware Adapter gửi lệnh tới simulator hoặc robot thật.
7. Dashboard hiển thị kết quả và ghi log CSV.

Tài liệu chi tiết:

- [Architecture](docs/Architecture.md)
- [Integration Contract](docs/INTEGRATION.md)
- [Bàn giao cho nhóm Vision](docs/HANDOFF_DUNG.md)

## Cấu trúc project

```text
robot_aiot/
├── app.py
├── config.py
├── logger.py
├── requirements.txt
├── llm/
│   └── parser.py
├── vision/
│   ├── contracts.py
│   ├── detect.py
│   ├── calibration.py
│   └── yolo_adapter.py
├── safety/
│   └── gate.py
├── robotics/
│   ├── ik.py
│   └── simulator.py
├── hardware/
│   ├── contracts.py
│   ├── robot_arm.py
│   └── drv8825_adapter.py
├── hardware_stub/
│   └── robot_arm.py
├── tests/
│   └── test_module_contracts.py
└── docs/
```

## Trạng thái module

| Module | Hiện tại | Điểm tích hợp |
|---|---|---|
| LLM Parser | Ollama `qwen3:0.6b` + fallback | `llm/parser.py` |
| Vision | Mock detections | `vision/yolo_adapter.py` |
| Calibration | Linear stub | `vision/calibration.py` |
| Safety Gate | Hoạt động | `safety/gate.py` |
| IK | Mô hình 4DOF | `robotics/ik.py` |
| Hardware | Simulator | `hardware/drv8825_adapter.py` |
| Dashboard | FastAPI | `app.py` |
| Logging | CSV + Command History | `logger.py` |

## Cấu hình backend

Mặc định trong `config.py`:

```python
VISION_BACKEND = "static"
CALIBRATION_BACKEND = "linear"
HARDWARE_BACKEND = "simulator"
```

Khi module thật đã sẵn sàng:

```python
VISION_BACKEND = "yolo"
CALIBRATION_BACKEND = "homography"
HARDWARE_BACKEND = "drv8825"
```

Chỉ đổi backend sau khi adapter tương ứng vượt qua contract tests.

## API contract cho nhóm

### Vision

Public API:

```python
get_detected_objects() -> list[dict]
```

Output chuẩn:

```python
[
    {
        "class_name": "chai_nuoc",
        "confidence": 0.91,
        "x_mm": 180.0,
        "y_mm": 80.0,
        "z_mm": 20.0,
    }
]
```

Quy ước:

- `confidence` nằm trong khoảng `0..1`.
- Tọa độ sau Vision facade luôn dùng millimeter.
- Không import YOLO hoặc OpenCV trực tiếp trong `app.py`.

### Calibration

```python
pixel_to_mm(u: float, v: float) -> tuple[float, float]
```

Input là pixel camera; output là `(x_mm, y_mm)` trong hệ tọa độ robot.

### Hardware

```python
home_all()
move_joints(joints)
gripper(open=True)
get_pose()
is_ready()
```

Quy ước:

- Robot có 4 khớp.
- Góc dùng đơn vị độ.
- Thứ tự luôn là `[J1, J2, J3, J4]`.
- Driver không chứa Safety Gate hoặc IK.
- Lệnh điều khiển trả `RobotCommandResult(success, message)`.

## Hướng dẫn cho Dũng: YOLO và Calibration

Dũng chỉ cần triển khai:

```text
vision/yolo_adapter.py
```

Ví dụ raw output:

```python
class YoloDetector:
    def detect(self):
        return [
            {
                "class_name": "chai_nuoc",
                "confidence": 0.91,
                "u": 680,
                "v": 80,
                "z": 20,
            }
        ]
```

`vision/detect.py` sẽ tự:

1. Nhận output từ YOLO.
2. Chuyển `u/v` sang millimeter.
3. Validate confidence và tọa độ.
4. Trả schema chuẩn cho Safety Gate.

Sau đó đổi:

```python
VISION_BACKEND = "yolo"
```

Để dùng homography:

```python
H, _ = cv2.findHomography(pixel_points, robot_points)
```

Chép ma trận `H` vào `HOMOGRAPHY_MATRIX` trong `config.py`, rồi đổi:

```python
CALIBRATION_BACKEND = "homography"
```

Không sửa `app.py`, `safety/gate.py` hoặc `robotics/ik.py`.

## Hướng dẫn nhóm phần cứng

Chỉ triển khai:

```text
hardware/drv8825_adapter.py
```

Giữ nguyên interface:

```python
class DRV8825RobotBackend:
    def home_all(self):
        ...

    def move_joints(self, joints):
        ...

    def gripper(self, open=True):
        ...

    def get_pose(self):
        ...

    def is_ready(self):
        ...
```

Sau khi driver đạt contract tests:

```python
HARDWARE_BACKEND = "drv8825"
```

Trước khi chạy robot thật phải kiểm tra chiều trục, step/độ, giới hạn cơ khí,
limit switch, homing và nút dừng khẩn cấp.

## Safety Gate

Lệnh bị từ chối khi:

- Không nhận diện được hành động hoặc vật thể.
- Camera không tìm thấy vật thể.
- Có nhiều vật thể cùng loại.
- Confidence thấp hơn `CONFIDENCE_THRESHOLD`.
- Tọa độ nằm ngoài `WORKSPACE`.
- IK hoặc Hardware Adapter báo lỗi.

Cấu hình hiện tại:

```python
CONFIDENCE_THRESHOLD = 0.70

WORKSPACE = {
    "min_radius": 60,
    "max_radius": 300,
    "min_z": 0,
    "max_z": 180,
}
```

Không nới giới hạn khi chưa đo robot thật.

## HTTP API

| Method | Endpoint | Mục đích |
|---|---|---|
| `GET` | `/` | Dashboard |
| `GET` | `/history` | Command History |
| `POST` | `/command` | Gửi lệnh và nhận trang HTML |
| `POST` | `/api/command` | Gửi lệnh và nhận JSON |

Ví dụ:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/command" `
  -Method Post `
  -Body @{ command = "gắp chai nước" }
```

## Logging

Runtime tạo:

- `logs/decision_log.csv`: parser, target, confidence, quyết định Safety Gate.
- `logs/action_log.csv`: góc pick/drop và kết quả điều khiển.

Các file CSV được `.gitignore` và không được commit.

## Kiểm thử

```powershell
python -m unittest discover -s tests -v
python -m pip check
```

Trạng thái ổn định hiện tại:

```text
Ran 7 tests
OK
```

Mọi backend mới phải vượt qua tests trước khi merge.

## Quy trình Git

Clone và tạo branch:

```bash
git clone https://github.com/PHUPHU2310/robot_aiot.git
cd robot_aiot
git switch -c feature/yolo-adapter
```

Trước khi commit:

```bash
python -m unittest discover -s tests -v
git status
git add <file-cua-minh>
git commit -m "Add YOLO detector adapter"
git push -u origin feature/yolo-adapter
```

Không commit:

- `venv/`
- `__pycache__/`
- CSV runtime.
- Uvicorn logs.
- Model weights lớn nếu chưa dùng Git LFS.

## Lỗi thường gặp

### `No module named fastapi`

```bash
pip install -r requirements.txt
```

### PowerShell không activate được `venv`

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
```

### Ollama chưa sẵn sàng hoặc timeout

```bash
ollama list
ollama pull qwen3:0.6b
```

Cold start trên CPU có thể chậm vì model phải được nạp vào RAM. Timeout mặc
định là 90 giây. Nếu Ollama vẫn lỗi, Dashboard tiếp tục chạy bằng parser dự
phòng và hiển thị cảnh báo.

### Port 8000 đang được sử dụng

```bash
uvicorn app:app --reload --port 8001
```

### Safety Gate từ chối lệnh

Kiểm tra tên class, confidence, số detection cùng loại, tọa độ millimeter và
giới hạn `WORKSPACE`. Lý do chi tiết có trên Dashboard và trong log.

## Phân công module

| Thành viên/nhóm | Phạm vi chính |
|---|---|
| Dũng — Vision | `vision/yolo_adapter.py`, homography |
| Nhóm phần cứng | `hardware/drv8825_adapter.py` |
| Phú — AI Control | LLM, Safety Gate, IK, Dashboard |

Nếu cần thay đổi contract chung, cả nhóm phải thống nhất và cập nhật:

- `vision/contracts.py`
- `hardware/contracts.py`
- `docs/INTEGRATION.md`
- `tests/test_module_contracts.py`
