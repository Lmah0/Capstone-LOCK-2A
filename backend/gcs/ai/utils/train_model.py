from ultralytics import YOLO
import os
import torch

'''
Before running this file:

1. Download latest drivers for your nvda gpu (optional but generally better if you want the latest stuff)
2. Download Cuda Toolkit (make sure its applicable with your driver version) from NVDA website
3. Run the cmd, nvidia-smi, in your cmd line prompt to check what version cuda you should have installed on your pc
4. Go to pytorch website and download the torch version that works with your cuda version
5. Make sure your virtual or conda environment is setup w the dependencies installed
'''

def main():
    # Change to path where the training data is located
    os.chdir("/Users/Eric/Downloads/roboflow")

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
        device='cuda', # Use 'cuda' for GPU or 'mps' for Mac
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

if __name__ == "__main__":
    cudaAvaliable = torch.cuda.is_available()

    print(cudaAvaliable)
    print(torch.cuda.get_device_name(0))

    if not cudaAvaliable:
        quit()

    # Important for Windows multiprocessing
    torch.multiprocessing.freeze_support()
    main()