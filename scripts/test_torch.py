import torch
print("PyTorch:", torch.__version__)
print("CUDA:", torch.cuda.is_available())
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    props = torch.cuda.get_device_properties(0)
    print("VRAM:", props.total_memory / 1024**3, "GB")
    x = torch.randn(1000, 1000).cuda()
    y = torch.matmul(x, x)
    print("matmul OK")
    from transformers import AutoModelForCausalLM
    model = AutoModelForCausalLM.from_pretrained(
        r"/mnt/d/loca_models/Qwen2.5-7B-Instruct",
        torch_dtype=torch.float16,
        device_map="auto",
    )
    print("Model loaded OK!")
    print("Params:", sum(p.numel() for p in model.parameters()) / 1e9, "B")
