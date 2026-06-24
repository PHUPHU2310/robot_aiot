# AIoT Robot Pick & Place - Phần Phú

Phần này gồm:
- LLM parser bằng Ollama (`qwen3:0.6b`) với rule-based fallback
- Safety Gate
- Inverse Kinematics demo
- Hardware Adapter tại `hardware/robot_arm.py`, hiện dùng simulator
- FastAPI Dashboard và mô phỏng robot 2D
- Interface YOLO tại `vision/detect.py`
- Calibration pixel → mm tại `vision/calibration.py`
- Logging CSV

Contract tích hợp chi tiết cho từng thành viên:

```text
docs/INTEGRATION.md
```

## Cài đặt

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Để dùng LLM parser, cài Ollama và tải model:

```bash
ollama pull qwen3:0.6b
```

## Chạy

```bash
uvicorn app:app --reload
```

Mở trình duyệt:

```text
http://127.0.0.1:8000
```

Lịch sử lệnh và kết quả Safety Gate:

```text
http://127.0.0.1:8000/history
```

## Test nhanh

Nhập:

```text
gắp chai nước
```

Kết quả mong muốn:
- Parser nhận ra `chai_nuoc`
- Safety Gate cho phép
- IK tính góc
- Robot giả lập chạy pick & place
- Ghi log vào thư mục `logs/`
- Hiển thị ảnh mô phỏng robot đang với tới vật

## Sau này cần thay

- Dũng chỉ sửa `vision/yolo_adapter.py`, sau đó chọn
  `VISION_BACKEND = "yolo"`. `vision/detect.py` là facade chung, không cần sửa.
- Khi hiệu chuẩn camera thật, giữ nguyên interface `pixel_to_mm(u, v)` và thay
  ma trận `HOMOGRAPHY_MATRIX` bằng output `cv2.findHomography()`.
- Trung chỉ sửa `hardware/drv8825_adapter.py`, rồi đổi
  `HARDWARE_BACKEND = "drv8825"`. `hardware/robot_arm.py` là facade chung.
- `LINKS` trong `config.py` thay bằng kích thước thật của tay robot.

## Contract test

```bash
python -m unittest discover -s tests -v
```
