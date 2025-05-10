import cv2
import torch
import numpy as np
import torchvision.transforms as transforms

import os
import time
import torch.jit

INFERENCE_WIDTH = 640 
INFERENCE_HEIGHT = 480 

#First realtime style transfer attempt using converted models
#Portals FF 2025

MODELS_TRT_DIR = "models_trt" 
MODEL_PATHS = {
    '1': (os.path.join(MODELS_TRT_DIR, "mosaic_trt.ts"), "Mosaic"), #has some artifacts; due to conversion?
    '2': (os.path.join(MODELS_TRT_DIR, "candy_trt.ts"), "Candy"), #doesnt work
    '3': (os.path.join(MODELS_TRT_DIR, "rain_princess_trt.ts"), "Rain Princess"), #doesnt work
    '4': (os.path.join(MODELS_TRT_DIR, "starry-night_trt.ts"), "Starry night"), #doesnt work
    '5': (os.path.join(MODELS_TRT_DIR, "udnie_trt.ts") , "Udnie"), #doesnt work
    '6': (os.path.join(MODELS_TRT_DIR, "stormtrooper_26000_trt.ts"), "Stormtrooper") #doesnt work

}


missing_models = False
for key, (model_path, model_name) in MODEL_PATHS.items():
    if not os.path.exists(model_path):
        print(f"ERROR: Compiled model not found: {model_path}")
        print(f"Please run the 'compile_trt.py' script for the '{model_name}' style.")
        missing_models = True
if missing_models:
    exit()



active_model_key = '1'

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Computation device: {device}")
if device == torch.device("cpu"):
    print("WARNING: CUDA not found. Running on CPU will be extremely slow.")
    print("Ensure PyTorch for Jetson and Torch-TensorRT are installed.")


# output folder for saved snapshots
output_dir = "snapshots"
os.makedirs(output_dir, exist_ok=True)
# snapshot counter logic
existing_files = [f for f in os.listdir(output_dir) if f.startswith("snapshot_") and f.endswith(".jpg")]
existing_numbers = [int(f.split("_")[1]) for f in existing_files if f.split("_")[1].isdigit()]
snapshot_counter = max(existing_numbers, default=0) + 1



def load_trt_model(model_path):
    print(f"Loading compiled TRT model from: {model_path}")
    try:
        # load the TorchScript module containing the TRT engine
        model_trt = torch.jit.load(model_path, map_location=device)
        model_trt.eval() # Ensure it's in evaluation mode
        print("TRT model loaded successfully.")
        # warmup inference to hide lag on first run
        print("Warming up TRT engine...")
        with torch.no_grad():
             dummy_input = torch.zeros((1, 3, INFERENCE_HEIGHT, INFERENCE_WIDTH), dtype=torch.float32).to(device)
             _ = model_trt(dummy_input)
        print("warmup complete.")
        return model_trt
    except Exception as e:
        print(f"\nERROR loading TorchScript TRT model: {e}")
        print("Ensure the model was compiled correctly with 'compile_trt.py'")
        print(f"Check compatibility between PyTorch, Torch-TensorRT, and CUDA versions.")
        exit()



print("\n Real-time video stylization using NN (Optimized with TensorRT)")
print("---------------------------Controls:----------------------")
print("1 = Mosaic")
print("2 = Candy")
print("3 = Rain Princess")
print("4 = Starry night")
print("5 = Udnie")
print("6 = Stormtrooper")
print("s = Snapshot")
print("q = Quit\n")

# model load
model_path, model_name = MODEL_PATHS[active_model_key]
model = load_trt_model(model_path)

#CORRECTED to use normalization
#mean/std should match the values used during original training
mean = np.array([0.485, 0.456, 0.406])
std = np.array([0.229, 0.224, 0.225])
transform = transforms.Compose([
    transforms.ToTensor(), # HWC uint8 [0, 255] -> CHW float32 [0.0, 1.0]
    transforms.Normalize(mean, std) # normalize using ImageNet stats
])


#denormalization function for post-processing
def denormalize_tensor(tensors):
    """ Denormalizes image tensors using mean and std """
    _mean = torch.tensor(mean, device=tensors.device).view(1, 3, 1, 1)
    _std = torch.tensor(std, device=tensors.device).view(1, 3, 1, 1)
    tensors = tensors * _std + _mean # reverse normalization
    return tensors


# open webcam
cap = cv2.VideoCapture(0)
# set camera res to match INFERENCE size
cap.set(cv2.CAP_PROP_FRAME_WIDTH, INFERENCE_WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, INFERENCE_HEIGHT)
print(f"Attempting to set camera resolution to: {INFERENCE_WIDTH}x{INFERENCE_HEIGHT}")
actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
if actual_width != INFERENCE_WIDTH or actual_height != INFERENCE_HEIGHT:
     print(f"WARNING: Camera opened at {int(actual_width)}x{int(actual_height)}, resizing will occur.")




frame_times = []
fps = 0.0

while True:
    loop_start_time = time.time()
    ret, frame = cap.read()
    if not ret:
        print("Error reading frame from camera.")
        break

   
    if frame.shape[1] != INFERENCE_WIDTH or frame.shape[0] != INFERENCE_HEIGHT:
         frame = cv2.resize(frame, (INFERENCE_WIDTH, INFERENCE_HEIGHT), interpolation=cv2.INTER_LINEAR)


    frame_flipped = cv2.flip(frame, 1)
    img_rgb = cv2.cvtColor(frame_flipped, cv2.COLOR_BGR2RGB) # BGR to RGB

    
    img_tensor = transform(img_rgb).unsqueeze(0).to(device)
    

    # inference using the loaded TRT model
    inf_start_time = time.time()
    with torch.no_grad():
        output_tensor = model(img_tensor) # output is NORMALIZED tensor on CUDA
    inf_end_time = time.time()

    # denormalize, clamp, convert
    output_denormalized = denormalize_tensor(output_tensor) # -> CHW float32 [0, 1] approx
    output_scaled = output_denormalized.mul(255).clamp(0, 255) # -> CHW float32 [0, 255]
    # remove batch dim, move to CPU, convert to numpy HWC uint8
    output_data = output_scaled.squeeze(0).cpu().numpy().transpose(1, 2, 0).astype('uint8')


    # convert stylized RGB back to BGR for OpenCV display
    output_bgr = cv2.cvtColor(output_data, cv2.COLOR_RGB2BGR)

    # prepare display frame (original flipped + stylized BGR)
    clean_output = output_bgr.copy() # For saving snapshots
    # ensure original frame matches output shape for hconcat
    original_resized_for_display = cv2.resize(frame_flipped, (output_bgr.shape[1], output_bgr.shape[0]))
    combined = cv2.hconcat([original_resized_for_display, output_bgr])

   
    panel_height = 40
    panel = np.zeros((panel_height, combined.shape[1], 3), dtype=np.uint8)

    # calculate FPS using moving average for stability
    current_time = time.time()
    frame_times.append(current_time)
    frame_times = frame_times[-20:] # keep last 20 timings
    if len(frame_times) > 1:
        fps = len(frame_times) / (frame_times[-1] - frame_times[0])

    inf_ms = (inf_end_time - inf_start_time) * 1000
    cv2.putText(panel, f"Style: {model_name}   FPS: {fps:.1f}   Infer(ms): {inf_ms:.1f}", (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2) # smaller font

    # show output
    output_with_panel = np.vstack([panel, combined])
    cv2.imshow("Real-time Style Transfer (TensorRT Optimized)", output_with_panel)

    # key bindings
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        print("Quitting...")
        break
    elif key == ord('s'):
        filename = os.path.join(output_dir, f"snapshot_{snapshot_counter}_{model_name.lower().replace(' ', '_')}.jpg")
        cv2.imwrite(filename, clean_output)
        print(f"Image saved as: {filename}")
        snapshot_counter += 1
    elif chr(key) in MODEL_PATHS:
        new_model_key = chr(key)
        if new_model_key != active_model_key:
            active_model_key = new_model_key
            model_path, model_name = MODEL_PATHS[active_model_key]
            print(f"\nSwitching style to: {model_name}")
            model = load_trt_model(model_path) # load the new compiled model
            frame_times = [] # reset FPS calculation

# release resources
print("Releasing camera and closing windows.")
cap.release()
cv2.destroyAllWindows()