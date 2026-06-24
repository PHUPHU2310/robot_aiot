from typing import Sequence

from hardware.contracts import RobotCommandResult, validate_joints


class RobotArmStub:
    """Module giả lập phần cứng. Sau này thay bằng module GPIO/DRV8825 của Trung."""

    def __init__(self):
        self.pose = [0, 0, 0, 0]
        self.gripper_open = True

    def home_all(self):
        self.pose = [0, 0, 0, 0]
        return RobotCommandResult(True, "Đã home toàn bộ khớp.")

    def move_joints(self, joints: Sequence[float]):
        self.pose = validate_joints(joints)
        return RobotCommandResult(True, f"Giả lập move_joints: {self.pose}")

    def gripper(self, open=True):
        self.gripper_open = open
        return RobotCommandResult(True, "Gripper mở" if open else "Gripper đóng")

    def get_pose(self):
        return list(self.pose)

    def is_ready(self):
        return True
