import torch
import torch_tensorrt
import argparse
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from models.transformer_net import TransformerNet 


COMPILATION_WIDTH = 640
COMPILATION_HEIGHT = 480


def compile_model_to_trt(pth_path, output_ts_path):
    """Loads a PyTorch .pth model and compiles it using Torch-TensorRT"""

    print(f"Loading model from: {pth_path}")
    # load original PyTorch model definition
    model = TransformerNet()

    state_dict = torch.load(pth_path, map_location="cpu")


    ignored = [k for k in state_dict.keys() if "running_mean" in k or "running_var" in k]
    for k in ignored:
        del state_dict[k]
    for k in list(state_dict.keys()):
        if k.startswith("saved_model."):
            state_dict[k.replace("saved_model.", "")] = state_dict.pop(k)


    model.load_state_dict(state_dict, strict=False)
    model.eval() 
    model.cuda()

    print("Model loaded and moved to CUDA")


    inputs = [
        torch_tensorrt.Input(
            min_shape=[1, 3, COMPILATION_HEIGHT, COMPILATION_WIDTH],
            opt_shape=[1, 3, COMPILATION_HEIGHT, COMPILATION_WIDTH],
            max_shape=[1, 3, COMPILATION_HEIGHT, COMPILATION_WIDTH],
            dtype=torch.float32, 
        )
    ]


    enabled_precisions = {torch.float, torch.half}

    print(f"Compiling model to TensorRT (FP16 enabled) for input size {COMPILATION_HEIGHT}x{COMPILATION_WIDTH}...")
    try:
        trt_ts_module = torch_tensorrt.compile(
            model,
            inputs=inputs,
            enabled_precisions=enabled_precisions,
            workspace_size=1 << 30,  # 1 GB workspace
        )
        print("Compilation successful")


        torch.jit.save(trt_ts_module, output_ts_path)
        print(f"Compiled TensorRT model saved to: {output_ts_path}")

    except Exception as e:
        print(f"\nERROR during Torch-TensorRT compilation: {e}")
        print("Compilation failed. Check model compatibility/input specs")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="")
    parser.add_argument("--model_in", type=str, required=True, help="")
    parser.add_argument("--model_out", type=str, required=True, help="")
    args = parser.parse_args()


    os.makedirs(os.path.dirname(args.model_out), exist_ok=True)

    compile_model_to_trt(args.model_in, args.model_out)

