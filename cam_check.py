import cv2
from ultralytics import YOLO
import config

model = YOLO(config.YOLO_MODEL_PATH)
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

print("Bấm 'q' để thoát.")
while True:
    ok, frame = cap.read()
    if not ok:
        break
    res = model.predict(frame, conf=0.45, verbose=False)[0]

    if len(res.boxes) > 0:
        # chọn box confidence cao nhất
        confs = res.boxes.conf.tolist()
        i = confs.index(max(confs))
        b = res.boxes[i]
        x1, y1, x2, y2 = map(int, b.xyxy[0].tolist())
        name = model.names[int(b.cls)]
        conf = float(b.conf)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{name} {conf:.2f}", (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    else:
        cv2.putText(frame, "khong co vat", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv2.imshow("webcam", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()