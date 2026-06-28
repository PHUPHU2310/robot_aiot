# robot_aiot — AIoT Robot Pick & Place

`robot_aiot` là prototype điều khiển tay máy gắp/thả vật bằng lệnh tiếng Việt. Hệ thống kết hợp LLM, YOLO11n, Safety Gate, Inverse Kinematics, Robot Simulator và Dashboard FastAPI.

Mục tiêu của bản hiện tại là chứng minh pipeline AI Control trước khi ghép robot thật:

```text
Người dùng nhập lệnh
        ↓
LLM Parser / Ollama
        ↓
YOLO11n Camera Detection
        ↓
Pixel → mm / Homography
        ↓
Safety Gate
        ↓
Inverse Kinematics
        ↓
Robot Simulator / Hardware Adapter
        ↓
Logging + Dashboard
```

## 1. Trạng thái hiện tại

Các phần đã có:

- Dashboard điều khiển bằng FastAPI.
- Nhập lệnh tiếng Việt, ví dụ `gắp chai nước`.
- Ollama Qwen3 parser, có rule-based fallback nếu Ollama lỗi.
- YOLO11n đã nối vào Dashboard.
- Hiển thị camera frame, bounding box, class, confidence, pixel `(u, v)`.
- Chuyển pixel sang tọa độ robot `(x_mm, y_mm, z_mm)`.
- Safety Gate kiểm tra vật thể, confidence và vùng làm việc.
- IK tính góc `J1, J2, J3, J4`.
- Robot 2D simulator.
- Hardware adapter để sau này ghép DRV8825/GPIO/NEMA17.
- Command History và CSV logs.
- Script chụp ảnh webcam, test YOLO camera, calibrate homography.

Các phần còn cần nhóm tích hợp thêm:

- Fine-tune YOLO bằng ảnh webcam thật để confidence ổn định hơn.
- Hiệu chuẩn homography với camera gắn thật trên bàn robot.
- Ghép robot thật của nhóm phần cứng.

## 2. Cấu trúc project

```text
robot_aiot/
├── app.py                         # FastAPI Dashboard + API
├── config.py                      # Cấu hình backend, YOLO, workspace, IK
├── logger.py                      # Ghi/đọc log CSV
├── requirements.txt               # Thư viện Python
├── train_yolo.py                  # Train lại YOLO11n
├── yolo11n.pt                     # Pretrained YOLO11n base model
├── dataset5/                      # Dataset YOLO hiện tại
├── runs/
│   └── detect/runs_train/...      # Kết quả train, best.pt
├── llm/
│   └── parser.py                  # Ollama parser + fallback
├── vision/
│   ├── detect.py                  # Vision facade: get_detected_objects()
│   ├── yolo_adapter.py            # YOLO11n backend
│   ├── calibration.py             # Linear / Homography pixel_to_mm()
│   └── contracts.py               # Contract dữ liệu Vision
├── safety/
│   └── gate.py                    # Safety Gate
├── robotics/
│   ├── ik.py                      # Inverse Kinematics
│   └── simulator.py               # Mô phỏng robot 2D
├── hardware/
│   ├── robot_arm.py               # Hardware facade
│   ├── contracts.py               # Contract phần cứng
│   └── drv8825_adapter.py         # Chỗ nhóm phần cứng triển khai thật
├── hardware_stub/
│   └── robot_arm.py               # Simulator backend
├── scripts/
│   ├── test_yolo_camera.py        # Test YOLO + camera riêng
│   ├── capture_webcam_dataset.py  # Chụp ảnh fine-tune YOLO
│   └── calibrate_homography.py    # Tính HOMOGRAPHY_MATRIX
├── tests/
│   └── test_module_contracts.py   # Unit tests contract
└── docs/
    ├── Architecture.md
    ├── INTEGRATION.md
    └── HANDOFF_DUNG.md
```

Lưu ý: Dashboard hiện render HTML trực tiếp trong `app.py`, không dùng `index.html` riêng.

## 3. Cài đặt và chạy dự án

### Bước 1: Clone project

```bash
git clone https://github.com/PHUPHU2310/robot_aiot.git
cd robot_aiot
```

### Bước 2: Tạo môi trường Python

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell chặn activate:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\Activate.ps1
```

Linux/Raspberry Pi:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Bước 3: Cài Ollama

Cài Ollama rồi pull model:

```bash
ollama pull qwen3:0.6b
ollama list
```

Nếu Ollama chưa chạy, Dashboard vẫn hoạt động bằng rule-based fallback.

### Bước 4: Chạy server

```powershell
python -m uvicorn app:app --reload
```

Mở trình duyệt:

```text
http://127.0.0.1:8000
```

Các trang quan trọng:

- Dashboard: <http://127.0.0.1:8000>
- Command History: <http://127.0.0.1:8000/history>
- API docs: <http://127.0.0.1:8000/docs>

Quan trọng: terminal chạy `uvicorn` phải luôn mở. Nếu tắt terminal hoặc nhấn `Ctrl + C`, trình duyệt sẽ báo `This site can’t be reached`.

## 4. Cách demo nhanh

Chạy server:

```powershell
python -m uvicorn app:app --reload
```

Mở:

```text
http://127.0.0.1:8000
```

Đặt vật trước camera, sau đó nhập:

```text
gắp chai nước
```

Hoặc:

```text
gắp cốc
gắp bút
gắp điện thoại
gắp kéo
```

Nếu YOLO nhận ra vật thể và confidence đủ cao, Dashboard sẽ hiển thị:

- AI Decision.
- Vật thể cần gắp.
- Confidence.
- Safety Gate cho phép.
- IK Result: `J1, J2, J3, J4`.
- Robot Status.
- Robot 2D Simulation.

Nếu confidence thấp hoặc không tìm thấy vật thể, robot sẽ bị chặn. Đây là hành vi đúng của Safety Gate.

Ví dụ:

```text
YOLO confidence = 0.52
CONFIDENCE_THRESHOLD = 0.70
→ Safety Gate chặn robot
```

Muốn demo nhanh có thể giảm tạm trong `config.py`:

```python
CONFIDENCE_THRESHOLD = 0.50
```

Khi demo nghiêm túc nên giữ threshold cao và cải thiện dataset/camera.

## 5. Giải thích từng module

### 5.1 Dashboard — `app.py`

Dashboard là giao diện chính của hệ thống.

Chức năng:

- Nhận lệnh người dùng qua form.
- Gọi LLM parser.
- Lấy danh sách vật thể từ Vision.
- Chạy Safety Gate.
- Chạy IK nếu được phép.
- Gửi lệnh tới robot simulator/hardware adapter.
- Hiển thị camera, bbox, confidence, IK result và robot status.
- Ghi log quyết định.

Endpoint chính:

| Method | Endpoint | Mục đích |
|---|---|---|
| `GET` | `/` | Dashboard |
| `GET` | `/history` | Lịch sử lệnh |
| `POST` | `/command` | Chạy lệnh và trả HTML |
| `POST` | `/api/command` | Chạy lệnh và trả JSON |

### 5.2 LLM Parser — `llm/parser.py`

Parser chuyển lệnh tự nhiên sang JSON điều khiển.

Ví dụ:

```text
gắp chai nước
```

Thành:

```json
{
  "action": "pick_place",
  "target_object": "chai_nuoc"
}
```

Model hiện dùng:

```python
OLLAMA_MODEL = "qwen3:0.6b"
```

Nếu Ollama lỗi hoặc timeout, hệ thống dùng `rule_based_fallback`.

Các object hiện hỗ trợ:

| Lệnh tiếng Việt | Class chuẩn |
|---|---|
| chai nước / chai | `chai_nuoc` |
| cốc / ly | `coc` |
| bút | `but` |
| điện thoại | `dien_thoai` |
| kéo | `keo` |
| hộp | `hop` |

Lưu ý: YOLO dataset hiện có 5 class chính, chưa ưu tiên `hop`.

### 5.3 YOLO Vision — `vision/yolo_adapter.py`

YOLO nhận ảnh camera và trả:

```python
{
    "class_name": "chai_nuoc",
    "confidence": 0.91,
    "u": 520,
    "v": 340,
    "bbox": {
        "x1": 480,
        "y1": 300,
        "x2": 560,
        "y2": 380
    },
    "z_mm": 20
}
```

Sau đó `vision/detect.py` chuẩn hóa thành output cho hệ thống:

```python
{
    "class_name": "chai_nuoc",
    "confidence": 0.91,
    "x_mm": 180.0,
    "y_mm": 80.0,
    "z_mm": 20.0
}
```

Map class YOLO sang class hệ thống:

| YOLO class | System class |
|---|---|
| `bottle` | `chai_nuoc` |
| `cup` | `coc` |
| `pen` | `but` |
| `phone` | `dien_thoai` |
| `scissor` | `keo` |

Config liên quan trong `config.py`:

```python
VISION_BACKEND = "yolo"
YOLO_MODEL_PATH = "runs/detect/runs_train/household5-2/weights/best.pt"
YOLO_FRAME_SOURCE = 0
YOLO_CONF = 0.45
YOLO_SINGLE_BEST = False
```

Nếu muốn test bằng ảnh tĩnh:

```python
YOLO_FRAME_SOURCE = "dataset5/test/images/ten_anh.jpg"
```

### 5.4 Calibration / Homography — `vision/calibration.py`

Robot cần tọa độ millimeter, nhưng camera chỉ trả pixel.

Do đó cần hàm:

```python
pixel_to_mm(u, v) -> (x_mm, y_mm)
```

Hiện có 2 backend:

```python
CALIBRATION_BACKEND = "linear"
```

hoặc:

```python
CALIBRATION_BACKEND = "homography"
```

Khi camera gắn thật lên bàn robot, dùng script homography để tạo ma trận chuẩn.

### 5.5 Safety Gate — `safety/gate.py`

Safety Gate quyết định robot có được chạy hay không.

Robot bị chặn nếu:

- Parser không hiểu hành động.
- Parser không hiểu vật thể.
- Camera không tìm thấy vật thể.
- Có nhiều vật cùng loại.
- Confidence thấp hơn `CONFIDENCE_THRESHOLD`.
- Vật nằm ngoài workspace.
- IK hoặc Hardware báo lỗi.

Config:

```python
CONFIDENCE_THRESHOLD = 0.70

WORKSPACE = {
    "min_radius": 60,
    "max_radius": 300,
    "min_z": 0,
    "max_z": 180,
}
```

Đây là phần quan trọng để giải thích với thầy: AI hiểu lệnh chưa đủ; robot chỉ chạy khi camera xác nhận và điều kiện an toàn đạt.

### 5.6 Inverse Kinematics — `robotics/ik.py`

IK nhận tọa độ vật:

```text
x_mm, y_mm, z_mm
```

và trả góc:

```text
J1, J2, J3, J4
```

Các thông số link robot nằm trong `config.py`:

```python
LINKS = {
    "base_height": 70,
    "shoulder_to_elbow": 140,
    "elbow_to_wrist": 130,
    "wrist_to_gripper": 60,
}
```

Khi có robot thật, nhóm phần cứng đo lại chiều dài tay máy rồi cập nhật các số này.

### 5.7 Robot Simulator — `robotics/simulator.py`

Khi lệnh được Safety Gate cho phép, Dashboard hiển thị mô phỏng 2D tư thế robot.

Mục tiêu:

- Demo được IK dù chưa có robot thật.
- Cho thấy robot đang với tới vị trí vật.
- Hỗ trợ kiểm tra logic pick/place.

### 5.8 Hardware Adapter — `hardware/`

Dashboard không gọi trực tiếp GPIO/DRV8825.

Thay vào đó dùng interface:

```python
home_all()
move_joints(joints)
gripper(open=True)
get_pose()
is_ready()
```

Hiện tại:

```python
HARDWARE_BACKEND = "simulator"
```

Khi phần cứng sẵn sàng:

```python
HARDWARE_BACKEND = "drv8825"
```

Nhóm phần cứng chỉ cần triển khai trong:

```text
hardware/drv8825_adapter.py
```

Không cần sửa Dashboard, LLM, Safety Gate hay IK nếu giữ đúng interface.

### 5.9 Logging — `logger.py`

Hệ thống ghi:

```text
logs/decision_log.csv
logs/action_log.csv
```

Dashboard lịch sử:

```text
http://127.0.0.1:8000/history
```

Log giúp viết báo cáo và chứng minh hệ thống có giám sát.

## 6. Script hỗ trợ nhóm Vision

### 6.1 Test YOLO camera

Chạy:

```powershell
python scripts/test_yolo_camera.py
```

Nếu có nhiều camera:

```powershell
python scripts/test_yolo_camera.py --source 1
```

Test bằng ảnh:

```powershell
python scripts/test_yolo_camera.py --source dataset5/test/images/ten_anh.jpg --once --save calibration/yolo_test.jpg
```

Mục tiêu: kiểm tra YOLO có detect được vật không trước khi mở Dashboard.

### 6.2 Chụp ảnh webcam để fine-tune

Chụp mỗi vật khoảng 40–60 ảnh:

```powershell
python scripts/capture_webcam_dataset.py --class-name bottle --count 50
python scripts/capture_webcam_dataset.py --class-name cup --count 50
python scripts/capture_webcam_dataset.py --class-name pen --count 50
python scripts/capture_webcam_dataset.py --class-name phone --count 50
python scripts/capture_webcam_dataset.py --class-name scissor --count 50
```

Phím:

- `SPACE` hoặc `s`: lưu ảnh.
- `q`: thoát.

Ảnh lưu vào:

```text
data/webcam_raw/<class_name>/
```

Sau đó label bằng Roboflow/LabelImg, export YOLO format rồi train lại.

### 6.3 Train lại YOLO

Chạy:

```powershell
python train_yolo.py
```

File train hiện dùng:

```python
model = YOLO("yolo11n.pt")
model.train(
    data="dataset5/data.yaml",
    epochs=30,
    imgsz=416,
    batch=8,
    device="cpu",
    project="runs/detect/runs_train",
    name="household5",
    patience=15,
)
```

Sau khi train xong, cập nhật `YOLO_MODEL_PATH` trong `config.py` nếu đường dẫn `best.pt` thay đổi.

### 6.4 Tạo Homography

Đặt 4 điểm mốc trên mặt bàn robot và đo tọa độ thật theo mm.

Ví dụ:

```text
P1 = (0, 0)
P2 = (200, 0)
P3 = (200, 150)
P4 = (0, 150)
```

Chạy:

```powershell
python scripts/calibrate_homography.py --source 0 --robot-points "0,0;200,0;200,150;0,150"
```

Quy trình:

1. Nhấn `SPACE` để chụp frame calibration.
2. Click 4 điểm trên ảnh theo đúng thứ tự.
3. Nhấn `c` để tính homography.
4. Copy đoạn `HOMOGRAPHY_MATRIX` in ra vào `config.py`.
5. Đổi:

```python
CALIBRATION_BACKEND = "homography"
```

Nếu click sai, nhấn `r` để reset.

## 7. API contract giữa các nhóm

### 7.1 Vision API

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
        "z_mm": 20.0
    }
]
```

Quy ước:

- `class_name` dùng tên chuẩn của hệ thống.
- `confidence` nằm trong `0..1`.
- Tọa độ đưa sang Safety Gate luôn là millimeter.
- `app.py` không import trực tiếp YOLO/OpenCV.

### 7.2 Calibration API

```python
pixel_to_mm(u: float, v: float) -> tuple[float, float]
```

Input là pixel camera, output là tọa độ robot theo mm.

### 7.3 Hardware API

```python
home_all()
move_joints(joints)
gripper(open=True)
get_pose()
is_ready()
```

Quy ước:

- Robot có 4 khớp.
- Đơn vị góc là độ.
- Thứ tự joints luôn là `[J1, J2, J3, J4]`.
- Driver không chứa logic LLM, Safety Gate hoặc IK.

## 8. Phân công đề xuất

| Thành viên/nhóm | Phạm vi |
|---|---|
| Phú | LLM Parser, Dashboard, Safety Gate, IK, Simulator, pipeline chính |
| Dũng | YOLO11n, dataset, training, inference, camera calibration |
| Trung/Thắng/nhóm phần cứng | Robot arm, stepper, DRV8825, GPIO, gripper, homing |

Khi tích hợp, cố gắng giữ nguyên API. Nếu đổi contract, phải cập nhật:

- `vision/contracts.py`
- `hardware/contracts.py`
- `docs/INTEGRATION.md`
- `tests/test_module_contracts.py`

## 9. Kiểm thử

Chạy unit tests:

```powershell
python -m unittest discover -s tests -v
```

Kết quả mong đợi:

```text
Ran 8 tests
OK
```

Kiểm tra thư viện:

```powershell
python -m pip check
```

Kết quả mong đợi:

```text
No broken requirements found.
```

Test API bằng PowerShell:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/command" `
  -Method Post `
  -Body @{ command = "gắp chai nước" }
```

## 10. Troubleshooting

### 10.1 Trình duyệt báo `This site can't be reached`

Nguyên nhân: server chưa chạy hoặc đã bị tắt.

Chạy lại:

```powershell
python -m uvicorn app:app --reload
```

### 10.2 `No module named fastapi` hoặc `No module named ultralytics`

Chạy:

```powershell
pip install -r requirements.txt
```

### 10.3 YOLO nhận vật nhưng Safety Gate chặn

Kiểm tra confidence trên Dashboard.

Nếu:

```text
confidence = 0.52
CONFIDENCE_THRESHOLD = 0.70
```

thì robot bị chặn là đúng.

Cách xử lý:

- Đưa vật rõ hơn trước camera.
- Tăng ánh sáng.
- Tránh tay/mặt/người che vật.
- Đặt vật trên nền đơn giản.
- Fine-tune thêm ảnh webcam thật.
- Demo nhanh thì giảm tạm `CONFIDENCE_THRESHOLD`.

### 10.4 Parser hiểu lệnh nhưng camera không tìm thấy vật

Ví dụ Dashboard báo:

```text
Không tìm thấy vật thể trong camera.
```

Nghĩa là LLM đã hiểu, nhưng YOLO chưa detect được object tương ứng.

Cách xử lý:

- Kiểm tra camera bằng `scripts/test_yolo_camera.py`.
- Đặt vật rõ trong khung hình.
- Fine-tune thêm dữ liệu cho class đó.

### 10.5 Camera không mở được

Thử đổi source:

```python
YOLO_FRAME_SOURCE = 1
```

hoặc test:

```powershell
python scripts/test_yolo_camera.py --source 1
```

### 10.6 Ollama timeout

Kiểm tra:

```bash
ollama list
ollama pull qwen3:0.6b
```

Nếu Ollama chưa sẵn sàng, hệ thống vẫn dùng fallback để demo.

## 11. Quy trình Git cho nhóm

Trước khi sửa:

```bash
git pull
```

Tạo branch:

```bash
git switch -c feature/ten-viec
```

Kiểm tra trước khi commit:

```bash
python -m unittest discover -s tests -v
git status
```

Commit:

```bash
git add .
git commit -m "Mo ta ngan gon thay doi"
git push -u origin feature/ten-viec
```

Không commit:

- `venv/`
- `__pycache__/`
- `logs/*.csv`
- `data/webcam_raw/`
- `calibration/`
- file model quá lớn nếu chưa dùng Git LFS.

## 12. Tóm tắt để báo cáo

Hệ thống hiện đã hoàn thành pipeline AI Control prototype:

```text
User Command
→ Ollama LLM Parser
→ YOLO11n Object Detection
→ Pixel-to-mm Calibration
→ Safety Gate
→ Inverse Kinematics
→ Robot Simulator / Hardware Adapter
→ Dashboard + Logging
```

Điểm mạnh của bản hiện tại:

- Có Dashboard trực quan.
- Có AI parser bằng Ollama.
- Có YOLO camera + bounding box.
- Có Safety Gate chặn lệnh không an toàn.
- Có IK và mô phỏng robot.
- Có log phục vụ báo cáo.
- Có contract rõ để ghép YOLO, homography và robot thật.

Việc tiếp theo của nhóm:

1. Fine-tune YOLO bằng ảnh webcam thật.
2. Calibrate homography với camera gắn cố định.
3. Đo lại thông số robot thật.
4. Triển khai `hardware/drv8825_adapter.py`.
5. Test toàn pipeline với robot thật.
