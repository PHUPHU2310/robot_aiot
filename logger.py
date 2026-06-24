import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def append_csv(filename: str, row: Dict):
    path = LOG_DIR / filename
    row = {"time": datetime.now().isoformat(timespec="seconds"), **row}

    fieldnames = list(row.keys())
    existing_rows = []
    if path.exists() and path.stat().st_size > 0:
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            old_fieldnames = reader.fieldnames or []
            existing_rows = list(reader)

        new_fields = [name for name in fieldnames if name not in old_fieldnames]
        fieldnames = old_fieldnames + new_fields
        if new_fields:
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(existing_rows)

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if f.tell() == 0:
            writer.writeheader()
        writer.writerow(row)


def read_csv(filename: str, limit: int = 100) -> List[Dict]:
    """Đọc các bản ghi mới nhất, trả danh sách rỗng nếu log chưa tồn tại."""
    path = LOG_DIR / filename
    if not path.exists() or path.stat().st_size == 0:
        return []

    with path.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    return list(reversed(rows[-limit:]))
