from typing import Sequence

from config import HARDWARE_BACKEND
from hardware.contracts import RobotBackend, RobotCommandResult, validate_joints


def create_robot_backend(name: str = HARDWARE_BACKEND) -> RobotBackend:
    if name == "simulator":
        from hardware_stub.robot_arm import RobotArmStub

        return RobotArmStub()
    if name == "drv8825":
        from hardware.drv8825_adapter import DRV8825RobotBackend

        return DRV8825RobotBackend()
    raise ValueError(f"Hardware backend không hợp lệ: {name}")


class RobotArm:
    """Facade ổn định cho app; validation và lựa chọn backend nằm tại đây."""

    def __init__(self, backend: str = HARDWARE_BACKEND):
        self.backend_name = backend
        self._backend = create_robot_backend(backend)

    def _ensure_success(self, result: RobotCommandResult) -> RobotCommandResult:
        if not result.success:
            raise RuntimeError(result.message)
        return result

    def home_all(self) -> RobotCommandResult:
        return self._ensure_success(self._backend.home_all())

    def move_joints(self, joints: Sequence[float]) -> RobotCommandResult:
        return self._ensure_success(self._backend.move_joints(validate_joints(joints)))

    def gripper(self, open: bool = True) -> RobotCommandResult:
        return self._ensure_success(self._backend.gripper(open=bool(open)))

    def get_pose(self) -> list[float]:
        return validate_joints(self._backend.get_pose())

    def is_ready(self) -> bool:
        return self._backend.is_ready()
