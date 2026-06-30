"""
hardware/drv8825_adapter.py — Giao tiếp Pi ↔ ESP32 qua UART.

Pi gửi lệnh JSON, ESP32 thực thi motor rồi trả ACK JSON.

Protocol:
    Pi  →  ESP32 : {"cmd": "move_joints", "joints": [45.0, -30.0, 60.0, -30.0]}\n
    ESP32 →  Pi  : {"status": "ok", "pose": [45.0, -30.0, 60.0, -30.0]}\n

    Pi  →  ESP32 : {"cmd": "home_all"}\n
    ESP32 →  Pi  : {"status": "ok", "pose": [0, 0, 0, 0]}\n

    Pi  →  ESP32 : {"cmd": "gripper", "open": true}\n
    ESP32 →  Pi  : {"status": "ok"}\n

    Pi  →  ESP32 : {"cmd": "get_pose"}\n
    ESP32 →  Pi  : {"status": "ok", "pose": [45.0, -30.0, 60.0, -30.0]}\n

Khi HARDWARE_BACKEND = "drv8825" trong config.py, hệ thống tự dùng file này.
Không cần sửa app.py, IK, Safety Gate hay Dashboard.
"""

import json
import threading
from typing import Sequence

import serial

from config import ESP32_BAUDRATE, ESP32_PORT, ESP32_TIMEOUT_SEC
from hardware.contracts import RobotCommandResult


class DRV8825RobotBackend:
    """
    Điểm tích hợp duy nhất dành cho nhóm phần cứng.
    Trung implement firmware ESP32 theo protocol ở trên,
    Thắng đấu dây ESP32 GPIO → DRV8825 → NEMA17.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._pose = [0.0, 0.0, 0.0, 0.0]
        try:
            self._ser = serial.Serial(
                port=ESP32_PORT,
                baudrate=ESP32_BAUDRATE,
                timeout=ESP32_TIMEOUT_SEC,
            )
        except serial.SerialException as exc:
            raise RuntimeError(
                f"Không mở được cổng serial ESP32 ({ESP32_PORT}). "
                f"Kiểm tra ESP32_PORT trong config.py. Chi tiết: {exc}"
            ) from exc

    # ── Public API (giữ nguyên contract) ──────────────────────────────────────

    def home_all(self) -> RobotCommandResult:
        ack = self._send({"cmd": "home_all"})
        self._pose = list(ack.get("pose", [0.0, 0.0, 0.0, 0.0]))
        return RobotCommandResult(True, "Homed toàn bộ khớp.")

    def move_joints(self, joints: Sequence[float]) -> RobotCommandResult:
        ack = self._send({"cmd": "move_joints", "joints": list(joints)})
        self._pose = list(ack.get("pose", joints))
        return RobotCommandResult(True, f"move_joints OK: {self._pose}")

    def gripper(self, open: bool = True) -> RobotCommandResult:
        ack = self._send({"cmd": "gripper", "open": bool(open)})
        state = "mở" if open else "đóng"
        return RobotCommandResult(True, f"Gripper {state}.")

    def get_pose(self) -> list[float]:
        ack = self._send({"cmd": "get_pose"})
        self._pose = list(ack.get("pose", self._pose))
        return self._pose

    def is_ready(self) -> bool:
        return self._ser.is_open

    # ── Internal ───────────────────────────────────────────────────────────────

    def _send(self, payload: dict) -> dict:
        """Gửi lệnh JSON, chờ ACK, raise nếu ESP32 báo lỗi hoặc timeout."""
        with self._lock:
            line = json.dumps(payload, ensure_ascii=False) + "\n"
            self._ser.write(line.encode("utf-8"))
            self._ser.flush()

            raw = self._ser.readline()
            if not raw:
                raise RuntimeError(
                    f"ESP32 không phản hồi sau {ESP32_TIMEOUT_SEC}s "
                    f"(lệnh: {payload.get('cmd')}). Kiểm tra kết nối UART."
                )

        try:
            ack = json.loads(raw.decode("utf-8").strip())
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"ESP32 trả dữ liệu không hợp lệ: {raw!r}. Lỗi: {exc}"
            ) from exc

        if ack.get("status") != "ok":
            raise RuntimeError(
                f"ESP32 báo lỗi lệnh '{payload.get('cmd')}': "
                f"{ack.get('msg', 'unknown error')}"
            )

        return ack
