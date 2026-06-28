"""
Test YOLO11n + camera độc lập trước khi mở Dashboard.

Ví dụ:
    python scripts/test_yolo_camera.py
    python scripts/test_yolo_camera.py --source 1
    python scripts/test_yolo_camera.py --source dataset5/test/images/example.jpg --once --save out.jpg

Phím:
    q : thoát
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import cv2

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except AttributeError:
    pass

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from vision.yolo_adapter import YoloDetector  # noqa: E402


def parse_source(value: str):
    return int(value) if str(value).isdigit() else value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview YOLO detections from camera/image.")
    parser.add_argument("--source", default="0", help='Camera index, image/video path, or stream URL. Default: "0".')
    parser.add_argument("--model", help="Path to YOLO best.pt. Default comes from config.py.")
    parser.add_argument("--once", action="store_true", help="Run one detection only.")
    parser.add_argument("--save", help="Save the latest annotated frame to this path.")
    return parser


def print_detections(detections):
    if not detections:
        print("Không phát hiện vật thể.")
        return
    for item in detections:
        bbox = item.get("bbox", {})
        print(
            f"{item['class_name']:12s} conf={item['confidence']:.2f} "
            f"u={item['u']:.0f} v={item['v']:.0f} "
            f"bbox=({bbox.get('x1', 0):.0f},{bbox.get('y1', 0):.0f})"
            f"→({bbox.get('x2', 0):.0f},{bbox.get('y2', 0):.0f})"
        )


def main() -> int:
    args = build_parser().parse_args()
    detector = YoloDetector(model_path=args.model, frame_source=parse_source(args.source))

    while True:
        detections = detector.detect()
        print_detections(detections)

        frame = detector.last_annotated_frame if detector.last_annotated_frame is not None else detector.last_frame
        if frame is None:
            raise RuntimeError("YOLO không trả frame.")

        if args.save:
            output_path = Path(args.save)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), frame)
            print(f"Đã lưu ảnh test: {output_path.resolve()}")

        cv2.imshow("YOLO11n Camera Test", frame)
        key = cv2.waitKey(0 if args.once else 1) & 0xFF
        if args.once or key in (ord("q"), 27):
            break

    cv2.destroyAllWindows()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
