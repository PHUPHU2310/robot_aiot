import math
from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class RobotCommandResult:
    success: bool
    message: str


def validate_joints(joints: Sequence[float]) -> list[float]:
    values = [float(value) for value in joints]
    if len(values) != 4:
        raise ValueError("Robot 4DOF yêu cầu đúng 4 góc khớp.")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Góc khớp phải là số hữu hạn.")
    return values


class RobotBackend(Protocol):
    """Contract bắt buộc cho simulator và driver phần cứng thật."""

    def home_all(self) -> RobotCommandResult:
        ...

    def move_joints(self, joints: Sequence[float]) -> RobotCommandResult:
        ...

    def gripper(self, open: bool = True) -> RobotCommandResult:
        ...

    def get_pose(self) -> list[float]:
        ...

    def is_ready(self) -> bool:
        ...
