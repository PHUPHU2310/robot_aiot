# robot_aiot — AIoT Robot Pick & Place

Hệ thống điều khiển tay máy 4DOF bằng lệnh ngôn ngữ tự nhiên, kết hợp Ollama
LLM, nhận diện vật thể, chuyển đổi tọa độ, Safety Gate, Inverse Kinematics,
Dashboard giám sát và lớp adapter cho phần cứng.

Phiên bản hiện tại chạy hoàn chỉnh bằng:

- Ollama `qwen3:0.6b` hoặc rule-based fallback.
- Dữ liệu vật thể giả lập.
- Calibration tuyến tính giả lập.
- Robot simulator.

Các interface đã được chuẩn hóa để nhóm Vision và Hardware có thể thay backend
mà không sửa `app.py`, Safety Gate hoặc IK.

## 1. Chức năng hiện có

- Nhập lệnh tiếng Việt, ví dụ `gắp chai nước`, `gắp cốc`, `gắp bút`.
- Phân tích lệnh bằng Ollama và ép output theo JSON Schema.
- Tự chuyển sang parser rule-based nếu Ollama không hoạt động.
- Đọc danh sách vật thể qua Vision API thống nhất.
- Chuyển tọa độ pixel camera sang millimeter.
- Kiểm tra confidence, số lượng vật thể và workspace.
- Tính IK cho robot 4DOF.
- Điều khiển robot qua Hardware Adapter.
- Hiển thị AI Decision, IK Result, Robot Status và mô phỏng robot 2D.
- Ghi `decision_log.csv` và `action_log.csv`.
- Hiển thị Command History trên Dashboard.
- Có contract tests cho Vision, Calibration và Hardware.

## 2. Kiến trúc hệ thống

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

Luồng xử lý một lệnh:

1. Người dùng nhập lệnh trên Dashboard.
2. Ollama chuyển câu lệnh thành `action` và `target_object`.
3. Vision trả danh sách vật thể và tọa độ chuẩn theo millimeter.
4. Safety Gate kiểm tra vật thể, confidence và vùng làm việc.
5. IK tính bốn góc `[J1, J2, J3, J4]`.
6. Hardware Adapter chuyển lệnh tới simulator hoặc robot thật.
7. Dashboard hiển thị kết quả và logger ghi CSV.

Tài liệu chi tiết:

- [Kiến trúc hệ thống](docs/Architecture.md)
- [Hợp đồng tích hợp module](docs/INTEGRATION.md)

## 3. Cấu trúc project

```text
robot_aiot/
├── app.py                         # FastAPI Dashboard và điều phối hệ thống
├── config.py                      # Backend, workspace, robot links, Ollama
├── logger.py                      # Đọc/ghi log CSV
├── requirements.txt
├── llm/
│   └── parser.py                  # Ollama parser và rule-based fallback
├── vision/
│   ├── contracts.py               # Contract dữ liệu Vision/Calibration
│   ├── detect.py                  # Vision facade và chuẩn hóa detection
│   ├── calibration.py             # Linear/Homography calibration
│   └── yolo_adapter.py            # Điểm tích hợp YOLO của nhóm Vision
├── safety/
│   └── gate.py                    # Confidence và workspace checks
├── robotics/
│   ├── ik.py                      # Inverse Kinematics 4DOF
│   └── simulator.py               # Hình mô phỏng robot 2D
├── hardware/
│   ├── contracts.py               # Contract cho mọi robot backend
│   ├── robot_arm.py               # Hardware facade và backend factory
│   └── drv8825_adapter.py          # Điểm tích hợp GPIO/DRV8825
├── hardware_stub/
│   └── robot_arm.py               # Backend simulator hiện tại
├── tests/
│   └── test_module_contracts.py
├── logs/                          # CSV sinh trong lúc chạy, không commit
└── docs/
    ├── Architecture.md
    └── INTEGRATION.md
```

## 4. Yêu cầu

- Python 3.10 trở lên.
- Windows 10/11, Linux hoặc Raspberry Pi OS.
- Ollama nếu muốn sử dụng LLM thật.
- Model Ollama `qwen3:0.6b`.

Không bắt buộc cài Ollama để chạy Dashboard. Khi Ollama không sẵn sàng, hệ
thống dùng parser dự phòng.

## 5. Cài đặt

Giải nén `robot_aiot_v1.zip`, sau đó mở Terminal tại thư mục `robot_aiot`.

Nếu dùng PowerShell:

```powershell
cd robot_aiot
```

### Windows PowerShell

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell chặn script activate:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
```

Có thể không activate và chạy trực tiếp:

```powershell
venv\Scripts\python -m pip install -r requirements.txt
```

### Linux hoặc Raspberry Pi

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## 6. Cài Ollama

Cài Ollama từ trang chính thức, sau đó tải model:

```bash
ollama pull qwen3:0.6b
```

Kiểm tra:

```bash
ollama list
```

Model mong đợi:

```text
qwen3:0.6b
```

Cấu hình Ollama nằm trong `config.py`:

```python
OLLAMA_ENABLED = True
OLLAMA_BASE_URL = "http://127.0.0.1:11434"
OLLAMA_MODEL = "qwen3:0.6b"
OLLAMA_TIMEOUT_SECONDS = 90
```

Lần gọi đầu có thể chậm vài giây vì Ollama phải nạp model vào RAM. Các lần gọi
sau sẽ nhanh hơn nhờ `keep_alive`.

## 7. Chạy hệ thống

### Khi đã activate virtual environment

```bash
uvicorn app:app --reload
```

### Windows không activate

```powershell
venv\Scripts\python -m uvicorn app:app --reload
```

Sau khi thấy:

```text
Uvicorn running on http://127.0.0.1:8000
```

mở:

- Dashboard: <http://127.0.0.1:8000>
- Command History: <http://127.0.0.1:8000/history>
- FastAPI docs: <http://127.0.0.1:8000/docs>

## 8. Test demo nhanh

Nhập:

```text
gắp chai nước
```

Kết quả mong đợi:

```text
Parser: ollama:qwen3:0.6b
Target: chai_nuoc
Confidence: 0.91
Safety Gate: Allowed
IK: J1, J2, J3, J4
Robot Status: Pick Success, Place Success
Status: SIMULATED_SUCCESS
```

Có thể thử thêm:

```text
gắp cốc
gắp bút
hãy lấy cái cốc giúp tôi
```

Lệnh không hợp lệ như `hãy nhảy múa` phải bị Safety Gate từ chối.

## 9. HTTP API

### Dashboard

```http
GET /
```

### Command History

```http
GET /history
```

### Gửi lệnh và nhận trang HTML

```http
POST /command
Content-Type: application/x-www-form-urlencoded

command=gắp chai nước
```

### Gửi lệnh và nhận JSON

```http
POST /api/command
Content-Type: application/x-www-form-urlencoded

command=gắp chai nước
```

Ví dụ PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/command" `
  -Method Post `
  -Body @{ command = "gắp chai nước" }
```

## 10. Cấu hình backend

Mặc định project dùng:

```python
HARDWARE_BACKEND = "simulator"
VISION_BACKEND = "static"
CALIBRATION_BACKEND = "linear"
```

Khi các module thật sẵn sàng:

```python
HARDWARE_BACKEND = "drv8825"
VISION_BACKEND = "yolo"
CALIBRATION_BACKEND = "homography"
```

Chỉ đổi backend sau khi adapter tương ứng vượt qua contract tests.

## 11. API contract bắt buộc

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
- Tọa độ sau facade luôn dùng millimeter.
- `class_name` phải khớp tên mà LLM parser sử dụng.
- Không để YOLO/OpenCV lan sang `app.py`.

### Calibration

Public API:

```python
pixel_to_mm(u: float, v: float) -> tuple[float, float]
```

Quy ước:

- `u`, `v` là tọa độ pixel.
- Output là `(x_mm, y_mm)` trong hệ tọa độ robot.
- Homography được cấu hình phía sau API này.

### Hardware

Public API:

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
- `move_joints()` và `get_pose()` phải dùng cùng thứ tự.
- Lệnh trả `RobotCommandResult(success, message)`.
- Driver không chứa Safety Gate hoặc IK.

## 12. Hướng dẫn cho nhóm Vision

Người phụ trách Vision chỉ sửa:

```text
vision/yolo_adapter.py
```

Ví dụ:

```python
class YoloDetector:
    def detect(self):
        # frame = camera.read()
        # results = model(frame)
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

`vision/detect.py` sẽ:

1. Nhận raw output.
2. Đổi `u/v` sang mm nếu cần.
3. Kiểm tra confidence và tọa độ.
4. Trả schema chuẩn cho Safety Gate.

Sau đó đổi:

```python
VISION_BACKEND = "yolo"
```

Không sửa `app.py`, `safety/gate.py` hoặc `robotics/ik.py`.

## 13. Hướng dẫn calibration camera

Thu thập các cặp điểm:

```text
pixel camera (u, v) ↔ tọa độ mặt bàn robot (x_mm, y_mm)
```

Dùng OpenCV:

```python
H, _ = cv2.findHomography(pixel_points, robot_points)
```

Chép ma trận `H` vào:

```python
HOMOGRAPHY_MATRIX = [
    [h11, h12, h13],
    [h21, h22, h23],
    [h31, h32, h33],
]
```

và đổi:

```python
CALIBRATION_BACKEND = "homography"
```

Các module còn lại không cần sửa.

## 14. Hướng dẫn cho nhóm phần cứng

Nhóm phần cứng chỉ sửa:

```text
hardware/drv8825_adapter.py
```

Cần triển khai:

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

Sau đó đổi:

```python
HARDWARE_BACKEND = "drv8825"
```

Trước khi chạy robot thật:

- Kiểm tra chiều dương của từng trục.
- Kiểm tra số step/độ và microstepping.
- Thiết lập giới hạn góc cơ khí.
- Kiểm tra limit switch và quy trình homing.
- Chạy tốc độ thấp trước.
- Chuẩn bị nút dừng khẩn cấp độc lập.

Simulator chạy thành công không đồng nghĩa robot thật đã an toàn.

## 15. Safety Gate

Safety Gate từ chối lệnh nếu:

- Không nhận diện được action.
- Không nhận diện được target object.
- Không tìm thấy vật thể.
- Có nhiều vật thể cùng loại.
- Confidence thấp hơn `CONFIDENCE_THRESHOLD`.
- Vật thể nằm ngoài `WORKSPACE`.
- IK hoặc Hardware Adapter trả lỗi.

Cấu hình:

```python
CONFIDENCE_THRESHOLD = 0.70

WORKSPACE = {
    "min_radius": 60,
    "max_radius": 300,
    "min_z": 0,
    "max_z": 180,
}
```

Không nới giới hạn workspace khi chưa đo robot thật.

## 16. Robot và IK

Kích thước tay máy hiện tại là dữ liệu giả lập:

```python
LINKS = {
    "base_height": 70,
    "shoulder_to_elbow": 140,
    "elbow_to_wrist": 130,
    "wrist_to_gripper": 60,
}
```

Khi có robot thật, phải cập nhật bằng số đo thực tế trước khi test chuyển động.

Drop zone:

```python
DROP_ZONE = {
    "x_mm": 80,
    "y_mm": 140,
    "z_mm": 20,
}
```

## 17. Log hệ thống

Các file sinh trong `logs/`:

### `decision_log.csv`

Ghi:

- Thời gian.
- Command.
- Parser.
- Target.
- Confidence.
- Allowed/Rejected.
- Lý do từ chối.

### `action_log.csv`

Ghi:

- Target.
- Pick joints.
- Drop joints.
- Kết quả hoặc lỗi phần cứng.

CSV là runtime data và được `.gitignore`; không commit log cá nhân lên repository.

## 18. Chạy kiểm thử

```powershell
venv\Scripts\python -m unittest discover -s tests -v
```

Kết quả ổn định hiện tại:

```text
Ran 7 tests
OK
```

Kiểm tra dependency:

```powershell
venv\Scripts\python -m pip check
```

Mọi adapter mới phải vượt qua tests trước khi merge.

## 19. Quy trình làm việc Git cho nhóm

Nếu nhận project qua Git remote, trước khi sửa:

```bash
git status
git pull
```

Nếu nhận `robot_aiot_v1.zip`, bản ZIP không chứa thư mục `.git`. Có thể chạy
project ngay mà không cần Git, hoặc khởi tạo repository cá nhân:

```bash
git init
git add .
git commit -m "Import robot_aiot prototype v1"
```

Tạo branch theo phần việc:

```bash
# Chọn một branch phù hợp với nhiệm vụ của mình:
git switch -c feature/yolo-adapter
# hoặc: git switch -c feature/drv8825-adapter
# hoặc: git switch -c feature/camera-calibration
```

Sau khi sửa:

```bash
python -m unittest discover -s tests -v
git status
git add <file-cua-minh>
git commit -m "Add YOLO detector adapter"
```

Không commit:

- `venv/`
- `__pycache__/`
- Log CSV.
- Uvicorn runtime logs.
- Model weights lớn nếu nhóm chưa thống nhất Git LFS.

## 20. Xử lý lỗi thường gặp

### `No module named fastapi`

```bash
pip install -r requirements.txt
```

Đảm bảo đang dùng đúng Python:

```powershell
venv\Scripts\python --version
venv\Scripts\python -m pip --version
```

### Không activate được PowerShell

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
```

### Ollama không phản hồi

Kiểm tra:

```bash
ollama list
```

Sau đó tải model nếu thiếu:

```bash
ollama pull qwen3:0.6b
```

Dashboard vẫn chạy bằng `rule_based_fallback`, nhưng phần Parser trên kết quả
sẽ hiển thị cảnh báo.

Nếu lần gọi đầu báo timeout, đợi model nạp xong rồi thử lại. Cấu hình mặc định
cho phép tối đa 90 giây để phù hợp máy chạy CPU.

### Port 8000 đang được sử dụng

Chạy cổng khác:

```bash
uvicorn app:app --reload --port 8001
```

Sau đó mở <http://127.0.0.1:8001>.

### Lệnh bị Safety Gate từ chối

Kiểm tra:

- Tên vật thể trong output Vision.
- Confidence.
- Có nhiều detection cùng class hay không.
- Tọa độ `x_mm/y_mm/z_mm`.
- Giới hạn `WORKSPACE`.
- Lý do tại Dashboard hoặc `decision_log.csv`.

### IK báo ngoài tầm với

Kiểm tra:

- Calibration có đúng đơn vị mm không.
- `LINKS` có đúng kích thước robot không.
- Vật thể có nằm trong workspace vật lý không.

## 21. Trạng thái hiện tại

| Module | Backend hiện tại | Sẵn sàng thay backend |
|---|---|---|
| LLM Parser | Ollama `qwen3:0.6b` | Có fallback |
| Vision | Static detections | Có `YoloDetector` adapter |
| Calibration | Linear stub | Có Homography backend |
| Safety Gate | Hoạt động | Có |
| IK | 4DOF simulator model | Cần cập nhật kích thước thật |
| Hardware | Simulator | Có DRV8825 adapter contract |
| Dashboard | FastAPI HTML | Hoạt động |
| Logging | CSV + History | Hoạt động |

## 22. Phạm vi file của từng thành viên

| Thành viên/nhóm | File chính được sửa |
|---|---|
| Vision/YOLO | `vision/yolo_adapter.py` |
| Camera calibration | `config.py`, dữ liệu homography |
| Hardware | `hardware/drv8825_adapter.py` |
| LLM/AI | `llm/parser.py` |
| IK/Robot model | `robotics/ik.py`, thông số `LINKS` |
| Dashboard/Integration | `app.py`, `logger.py` |

Nếu cần thay đổi contract chung, cả nhóm phải thống nhất trước và cập nhật:

- `vision/contracts.py`
- `hardware/contracts.py`
- `docs/INTEGRATION.md`
- Contract tests

## 23. Snapshot ổn định

Commit nền hiện tại:

```text
f2cf26e Complete AI dashboard, LLM parser, IK and simulator
```

Trước khi ghép module thật, có thể quay lại commit này để đối chiếu trạng thái
simulator ổn định.
