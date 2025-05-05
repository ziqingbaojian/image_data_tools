# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File   : test_scripts.py
# Time   : 2025/5/2 18:04
# Author : 紫青宝剑
# 测试脚本, 试试思路
"""
import torch
import torchvision.models as models

model = models.resnet50(pretrained=False)
# 加载本地下载好的文件模型;
model_path = r"D:\code\pythoncode\image_data_tools\models\resnet50-0676ba61.pth"
model.load_state_dict(torch.load(model_path, weights_only=True))
model.eval()
