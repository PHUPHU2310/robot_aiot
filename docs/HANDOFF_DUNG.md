# Bàn giao AI Control Prototype v1.0 cho Dũng

Dũng ơi, mình đã hoàn thành phần **AI Control Prototype v1.0** của project
`robot_aiot`.

Hiện tại project có:

- Dashboard điều khiển.
- Ollama Qwen3 Parser.
- Safety Gate.
- Inverse Kinematics.
- Robot Simulator 2D.
- Logging và Command History.

Các API đã chuẩn hóa để tích hợp:

```python
get_detected_objects()
pixel_to_mm()
move_joints()
gripper()
```

Hiện dữ liệu vật thể đang là mock data trong `config.py`.

Khi ông hoàn thành YOLO11n và Homography, chỉ cần triển khai:

```text
vision/yolo_adapter.py
```

Sau đó đổi trong `config.py`:

```python
VISION_BACKEND = "yolo"
CALIBRATION_BACKEND = "homography"
```

Pipeline còn lại không cần sửa:

```text
YOLO → Calibration → Safety Gate → IK → Robot Adapter
```

Mình sẽ giữ phần LLM, Safety Gate, IK và Dashboard. Ông phụ trách YOLO,
Calibration và Detection Pipeline.

Contract chi tiết:

- `docs/Architecture.md`
- `docs/INTEGRATION.md`
- `README.md`

Trước khi ghép, chạy:

```powershell
cd robot_aiot
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama pull qwen3:0.6b
python -m unittest discover -s tests -v
uvicorn app:app --reload
```

Sau đó mở `http://127.0.0.1:8000` và thử `gắp chai nước`.

Nếu nhận project qua ZIP, giải nén rồi tích hợp trực tiếp. Nếu nhóm đưa project
lên Git remote, tạo branch riêng trước khi sửa `vision/yolo_adapter.py`.
