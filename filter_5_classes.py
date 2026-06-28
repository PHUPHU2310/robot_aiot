import yaml, shutil
from pathlib import Path

RAW  = Path("D:/robot_aiot/household_raw")   # nơi vừa tải về
OUT  = Path("D:/robot_aiot/dataset5")        # bộ 5 class sạch
WANT = ["bottle", "cup", "pen", "phone", "scissor"]   # 5 class muốn giữ

with open(RAW / "data.yaml", encoding="utf-8") as f:
    data = yaml.safe_load(f)
names = data["names"]
if isinstance(names, dict):
    names = [names[i] for i in range(len(names))]

for w in WANT:
    if w not in names:
        raise SystemExit(f"Class '{w}' không có. Class sẵn có: {names}")

old_to_new = {names.index(w): i for i, w in enumerate(WANT)}

for split in ["train", "valid", "test"]:
    lbl_dir = RAW / split / "labels"
    img_dir = RAW / split / "images"
    if not lbl_dir.exists():
        continue
    out_img = OUT / split / "images"; out_img.mkdir(parents=True, exist_ok=True)
    out_lbl = OUT / split / "labels"; out_lbl.mkdir(parents=True, exist_ok=True)
    kept = 0
    for lbl in lbl_dir.glob("*.txt"):
        new_lines = []
        for line in lbl.read_text().splitlines():
            p = line.split()
            if not p:
                continue
            cid = int(p[0])
            if cid in old_to_new:                 # chỉ giữ 5 class
                p[0] = str(old_to_new[cid])        # đổi lại id 0..4
                new_lines.append(" ".join(p))
        if new_lines:                             # bỏ ảnh không chứa class nào trong 5
            (out_lbl / lbl.name).write_text("\n".join(new_lines))
            for ext in [".jpg", ".jpeg", ".png"]:
                src = img_dir / (lbl.stem + ext)
                if src.exists():
                    shutil.copy(src, out_img / src.name)
                    break
            kept += 1
    print(f"{split}: giữ {kept} ảnh")

with open(OUT / "data.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(
        {"train": "../train/images", "val": "../valid/images",
         "test": "../test/images", "nc": len(WANT), "names": WANT},
        f, sort_keys=False, allow_unicode=True)

print("Xong. Bộ 5 class ở:", OUT)