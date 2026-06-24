from typing import Sequence

from hardware.contracts import RobotCommandResult


class DRV8825RobotBackend:
    """
    Điểm tích hợp duy nhất dành cho nhóm phần cứng.

    Nhóm phần cứng triển khai GPIO/DRV8825/NEMA17 trong file này và giữ nguyên
    các method public. Không cần sửa app.py, IK, Safety Gate hoặc Dashboard.
    """

    def __init__(self):
        raise NotImplementedError(
            "Chưa cấu hình chân GPIO/DRV8825 trong hardware/drv8825_adapter.py."
        )

    def home_all(self) -> RobotCommandResult:
        raise NotImplementedError

    def move_joints(self, joints: Sequence[float]) -> RobotCommandResult:
        raise NotImplementedError

    def gripper(self, open: bool = True) -> RobotCommandResult:
        raise NotImplementedError

    def get_pose(self) -> list[float]:
        raise NotImplementedError

    def is_ready(self) -> bool:
        return False
