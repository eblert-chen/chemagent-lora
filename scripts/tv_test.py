import torchvision
import torch
import sys
print("torch:", torch.__version__)
print("torchvision:", torchvision.__version__)
print("torch.cuda:", torch.cuda.is_available())
x = torch.randn(100,100).cuda()
print("cuda OK")
