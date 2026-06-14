import torch
print("PyTorch:", torch.__version__)
print("CUDA:", torch.cuda.is_available())
print("GPU:", torch.cuda.get_device_name(0))
props = torch.cuda.get_device_properties(0)
print("VRAM:", props.total_memory / 1024**3, "GB")
print("CC:", props.major, ".", props.minor, sep="")
x = torch.randn(1000, 1000).cuda()
y = torch.matmul(x, x)
print("Test: matmul OK")
# Try loading a model
from transformers import AutoConfig
cfg = AutoConfig.from_pretrained(r"D:\loca_models\Qwen2.5-7B-Instruct")
print("Model config loaded OK")
