import torch
print(torch.cuda.is_available())  # 若為True則GPU可用
print(torch.cuda.device_count())  # 可用GPU數量