from ultralytics import YOLO

model = YOLO("yolo11n.pt")          # bắt đầu từ pretrained → hội tụ nhanh hơn

model.train(
    data="D:/robot_aiot/dataset5/data.yaml",
    epochs=30,
    imgsz=416,         # giảm xuống 416 nếu CPU quá chậm
    batch=8,           # CPU nên để nhỏ
    device="cpu",
    project="runs_train",
    name="household5",
    patience=15,       # tự dừng sớm nếu không cải thiện
)