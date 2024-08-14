from ultralytics import YOLO
model = YOLO("yolov8n.pt")
model.train(
    data="dataset/data.yaml", 
    epochs=100, 
    imgsz=640,
    batch=16, 
    lr0=0.01,
    momentum=0.937
)
metrics = model.val()