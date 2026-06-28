"""
Tạo homography Pixel -> mm cho camera gắn trên bàn robot.

Ví dụ nhanh với camera mặc định:
    python scripts/calibrate_homography.py --source 0 --robot-points "0,0;200,0;200,150;0,150"

Ví dụ dùng ảnh đã chụp:
    python scripts/calibrate_homography.py --image calibration/board.jpg --robot-points "0,0;200,0;200,150;0,150"

Cách dùng:
    1. Đặt 4 điểm mốc trên mặt bàn robot, biết tọa độ mm thật của từng điểm.
    2. Truyền tọa độ mm theo đúng thứ tự qua --robot-points.
    3. Click các điểm pixel trên ảnh theo đúng thứ tự đó.
    4. Nhấn c để tính homography, r để click lại, q để thoát.

Script sẽ in đoạn config:
    CALIBRATION_BACKEND = "homography"
    HOMOGRAPHY_MATRIX = [...]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import cv2
import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def parse_source(value: str):
    return int(value) if str(value).isdigit() else value


def parse_points(value: str) -> np.ndarray:
    points = []
    for chunk in value.split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        x_text, y_text = chunk.split(",", maxsplit=1)
        points.append([float(x_text.strip()), float(y_text.strip())])
    if len(points) < 4:
        raise ValueError("Cần ít nhất 4 điểm mm, ví dụ: 0,0;200,0;200,150;0,150")
    return np.array(points, dtype=np.float32)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Calibrate homography from camera pixels to robot millimeters.")
    parser.add_argument("--image", help="Ảnh calibration đã chụp sẵn.")
    parser.add_argument("--source", default="0", help='Camera index/URL nếu không dùng --image. Default: "0".')
    parser.add_argument(
        "--robot-points",
        required=True,
        help='Danh sách điểm mm theo thứ tự click, ví dụ: "0,0;200,0;200,150;0,150".',
    )
    parser.add_argument("--output", default="calibration/homography_matrix.json")
    parser.add_argument("--save-frame", default="calibration/calibration_frame.jpg")
    return parser


def load_or_capture_frame(args) -> np.ndarray:
    if args.image:
        frame = cv2.imread(args.image)
        if frame is None:
            raise RuntimeError(f"Không đọc được ảnh: {args.image}")
        return frame

    source = parse_source(args.source)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened() and isinstance(source, int):
        cap.release()
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"Không mở được camera/nguồn: {source}")

    print("SPACE/s = chụp frame calibration | q = thoát")
    captured = None
    while True:
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        preview = frame.copy()
        cv2.putText(
            preview,
            "SPACE/s capture calibration frame | q quit",
            (20, 36),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (56, 189, 248),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow("Capture Homography Frame", preview)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key in (ord(" "), ord("s")):
            captured = frame.copy()
            break

    cap.release()
    cv2.destroyWindow("Capture Homography Frame")

    if captured is None:
        raise RuntimeError("Chưa chụp frame calibration.")

    save_path = Path(args.save_frame)
    save_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(save_path), captured)
    print(f"Đã lưu frame calibration: {save_path.resolve()}")
    return captured


def collect_pixel_points(frame: np.ndarray, expected_count: int) -> np.ndarray:
    points: list[list[float]] = []
    window_name = "Click Homography Points"

    def redraw():
        canvas = frame.copy()
        for index, (x, y) in enumerate(points, start=1):
            cv2.circle(canvas, (int(x), int(y)), 7, (74, 222, 128), -1)
            cv2.putText(
                canvas,
                str(index),
                (int(x) + 10, int(y) - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (74, 222, 128),
                2,
                cv2.LINE_AA,
            )
        cv2.putText(
            canvas,
            f"Click {len(points)}/{expected_count} | c compute | r reset | q quit",
            (20, 36),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.85,
            (56, 189, 248),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow(window_name, canvas)

    def on_mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < expected_count:
            points.append([float(x), float(y)])
            print(f"Pixel point {len(points)}: ({x}, {y})")
            redraw()

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(window_name, on_mouse)
    redraw()

    while True:
        key = cv2.waitKey(20) & 0xFF
        if key in (ord("q"), 27):
            cv2.destroyWindow(window_name)
            raise RuntimeError("Đã hủy calibration.")
        if key == ord("r"):
            points.clear()
            redraw()
        if key == ord("c"):
            if len(points) != expected_count:
                print(f"Cần click đủ {expected_count} điểm trước khi tính.")
                continue
            break

    cv2.destroyWindow(window_name)
    return np.array(points, dtype=np.float32)


def main() -> int:
    args = build_parser().parse_args()
    robot_points = parse_points(args.robot_points)
    frame = load_or_capture_frame(args)
    pixel_points = collect_pixel_points(frame, len(robot_points))

    matrix, mask = cv2.findHomography(pixel_points, robot_points)
    if matrix is None:
        raise RuntimeError("cv2.findHomography không tính được ma trận. Kiểm tra lại thứ tự điểm.")

    matrix_list = [[round(float(value), 8) for value in row] for row in matrix.tolist()]
    output = {
        "pixel_points": pixel_points.tolist(),
        "robot_points_mm": robot_points.tolist(),
        "homography_matrix": matrix_list,
        "inlier_mask": mask.flatten().astype(int).tolist() if mask is not None else None,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print("\n=== COPY VÀO config.py ===")
    print('CALIBRATION_BACKEND = "homography"')
    print("HOMOGRAPHY_MATRIX = [")
    for row in matrix_list:
        print(f"    {row},")
    print("]")
    print(f"\nĐã lưu chi tiết calibration: {output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
