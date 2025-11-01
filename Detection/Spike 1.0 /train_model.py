from ultralytics import YOLO
import os

# Change to the LOCK-2A directory so relative paths in data.yaml work correctly
os.chdir("/Users/lionelhasan/Capstone/LOCK-2A")

# Initialize YOLOv11 model
model = YOLO('yolo11n.pt')

# Train the model - use just the filename
results = model.train(
    data='data.yaml',  # YOLO will find it relative to current directory
    epochs=50,
    imgsz=640,
    batch=8,
    name='yolo11_training',
    project='runs/detect',
    patience=50,
    save=True,
    device='mps',
    verbose=True,
    plots=True,
)

# Save the best weights
best_model_path = model.trainer.best
print(f"\nTraining complete! Best weights saved at: {best_model_path}")

# Validate the model
metrics = model.val()
print(f"\nValidation metrics:")
print(f"mAP50: {metrics.box.map50}")
print(f"mAP50-95: {metrics.box.map}")

# Print results summary
print(f"\nResults saved to: runs/detect/yolo11_training")
print(f"Check training plots at: runs/detect/yolo11_training/")

# Export the model (optional)
# model.export(format='onnx')