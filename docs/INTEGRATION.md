# Hợp đồng tích hợp module

Mục tiêu: nhóm Vision và Hardware chỉ sửa adapter của mình. Các module `app.py`,
`safety/` và `robotics/` không được phụ thuộc YOLO, OpenCV, GPIO hay DRV8825.

## 1. Vision / YOLO

Người phụ trách: Dũng.

Chỉ sửa:

```text
vision/yolo_adapter.py
```

Method bắt buộc:

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

Các dạng tọa độ được chấp nhận:

- `u`, `v`: pixel camera, tự động đi qua calibration.
- `x_mm`, `y_mm`, `z_mm`: tọa độ robot đã calibration.
- `x`, `y`, `z`: tương thích dữ liệu demo, được hiểu là mm.

Sau khi adapter chạy được, đổi:

```python
VISION_BACKEND = "yolo"
```

trong `config.py`.

Output chuẩn sau adapter luôn là:

```python
{
    "class_name": str,
    "confidence": float,  # 0..1
    "x_mm": float,
    "y_mm": float,
    "z_mm": float,
}
```

## 2. Camera calibration

Public API cố định:

```python
pixel_to_mm(u, v) -> (x_mm, y_mm)
```

Để dùng homography:

1. Dùng các cặp điểm pixel/mm để chạy `cv2.findHomography()`.
2. Chép ma trận 3×3 vào `HOMOGRAPHY_MATRIX` trong `config.py`.
3. Đổi `CALIBRATION_BACKEND = "homography"`.

Các module khác không cần import OpenCV và không cần sửa.

## 3. Hardware

Người phụ trách: nhóm phần cứng.

Chỉ sửa:

```text
hardware/drv8825_adapter.py
```

Class phải giữ nguyên 5 method:

```python
home_all() -> RobotCommandResult
move_joints(joints) -> RobotCommandResult
gripper(open=True) -> RobotCommandResult
get_pose() -> list[float]
is_ready() -> bool
```

Quy ước:

- Robot có 4 góc khớp, đơn vị độ.
- `move_joints()` nhận đúng thứ tự `[J1, J2, J3, J4]`.
- `get_pose()` trả cùng thứ tự.
- Không trả NaN hoặc Infinity.
- Lệnh thành công: `RobotCommandResult(True, "message")`.
- Lệnh thất bại: `RobotCommandResult(False, "lý do")`.
- Không đặt logic Safety Gate hoặc IK trong driver.

Sau khi driver chạy được, đổi:

```python
HARDWARE_BACKEND = "drv8825"
```

trong `config.py`.

## 4. Kiểm tra trước khi ghép

```powershell
venv\Scripts\python -m unittest discover -s tests -v
venv\Scripts\python -m uvicorn app:app --reload
```

Nếu contract test qua, adapter có thể ghép với phần còn lại mà không sửa luồng
Dashboard → Parser → Safety Gate → IK.
