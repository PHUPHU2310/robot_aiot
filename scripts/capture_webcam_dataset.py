"""
Chụp thêm ảnh webcam thật để fine-tune YOLO11n.

Ví dụ:
    python scripts/capture_webcam_dataset.py --class-name bottle --count 50
    python scripts/capture_webcam_dataset.py --class-name cup --count 50 --source 1

Phím trong cửa sổ camera:
    SPACE / s : lưu ảnh hiện tại
    q         : thoát

Ảnh sẽ được lưu vào:
    data/webcam_raw/<class_name>/

Sau khi chụp xong, đưa ảnh lên Roboflow/LabelImg để gán bbox rồi train lại YOLO.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass


VALID_CLASSES = ["bottle", "cup", "pen", "phone", "scissor"]


def parse_source(value: str):
    return int(value) if str(value).isdigit() else value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Capture webcam images for YOLO fine-tuning.")
    parser.add_argument("--class-name", required=True, choices=VALID_CLASSES)
    parser.add_argument("--source", default="0", help='Camera index, image/video path, or stream URL. Default: "0".')
    parser.add_argument("--output", default="data/webcam_raw", help="Output folder for raw images.")
    parser.add_argument("--count", type=int, default=50, help="Target number of images to capture.")
    parser.add_argument("--width", type=int, default=1280, help="Requested camera width.")
    parser.add_argument("--height", type=int, default=720, help="Requested camera height.")
    parser.add_argument(
        "--auto-interval",
        type=float,
        default=0,
        help="Auto-save every N seconds. Default 0 means manual SPACE/s only.",
    )
    return parser


def save_frame(frame, output_dir: Path, class_name: str, index: int) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = output_dir / f"{class_name}_{timestamp}_{index:03d}.jpg"
    ok = cv2.imwrite(str(path), frame)
    if not ok:
        raise RuntimeError(f"Không lưu được ảnh: {path}")
    return path


def main() -> int:
    args = build_parser().parse_args()
    source = parse_source(args.source)
    output_dir = Path(args.output) / args.class_name
    output_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened() and isinstance(source, int):
        cap.release()
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError(f"Không mở được camera/nguồn: {source}")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    print(f"Đang chụp class: {args.class_name}")
    print(f"Lưu vào: {output_dir.resolve()}")
    print("SPACE/s = lưu ảnh | q = thoát")

    saved = 0
    last_auto_save = time.monotonic()

    while saved < args.count:
        ok, frame = cap.read()
        if not ok or frame is None:
            print("Không đọc được frame, thử lại...")
            time.sleep(0.2)
            continue

        preview = frame.copy()
        cv2.putText(
            preview,
            f"{args.class_name}: {saved}/{args.count} | SPACE/s save | q quit",
            (20, 36),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (56, 189, 248),
            2,
            cv2.LINE_AA,
        )
        cv2.imshow("Capture YOLO Dataset", preview)

        should_save = False
        key = cv2.waitKey(1) & 0xFF
        if key in (ord("q"), 27):
            break
        if key in (ord(" "), ord("s")):
            should_save = True

        if args.auto_interval > 0 and time.monotonic() - last_auto_save >= args.auto_interval:
            should_save = True
            last_auto_save = time.monotonic()

        if should_save:
            saved += 1
            path = save_frame(frame, output_dir, args.class_name, saved)
            print(f"[{saved}/{args.count}] Saved {path}")

    cap.release()
    cv2.destroyAllWindows()
    print(f"Hoàn tất: đã lưu {saved} ảnh cho class {args.class_name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
