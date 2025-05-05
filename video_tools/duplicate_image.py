# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File   : duplicate_image.py
# Time   : 2025/5/1 17:50
# Author : 紫青宝剑
"""
import os
import shutil

import torch
import pandas as pd
from torch import nn
from PIL import Image
from pyexpat import features
from torch.autograd import Variable
from torchvision import models, transforms


class DuplicateImage(object):

    def __init__(self):
        """初始化模型以及参数的配置;
        """
        self.target_folder = ""
        self.my_transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor()
        ])
        # 下载的 model 进行执行;
        model = models.resnet50(pretrained=False)

        model_path = r"D:\code\pythoncode\image_data_tools\models\resnet50-0676ba61.pth"
        model.load_state_dict(torch.load(model_path, weights_only=True))
        model.eval()
        self.resnet50_feature_extractor = model

    def image_to_features(self, image_path: str):
        """
        图片转换成为图像特征向量;
        :param image_path:
        :return:
        """
        img = Image.open(image_path)
        img_trans = self.my_transform(img)
        x = Variable(torch.unsqueeze(img_trans, 0).float(), requires_grad=False)
        y = self.resnet50_feature_extractor(x)
        y_li = y.data.numpy().tolist()[0]
        return y_li

    @staticmethod
    def move_file(source_path, target_path):
        """
        移动文件;
        :param source_path:
        :param target_path:
        :return:
        """
        try:
            if os.path.exists(source_path):
                raise FileExistsError(f"文件: {source_path}不存在;")
            shutil.move(source_path, target_path)
        except Exception as e:
            print(f"文件移动失败:{e}")

    @staticmethod
    def delete_file(file_path):
        """
        删除文件;
        :param file_path:
        :return:
        """
        try:
            if not os.path.exists(file_path):
                print(f"文件已经不存在.")
            os.remove(file_path)
        except Exception as e:
            print(f"文件删除失败:{e}")

    def single_folder(self, directory):
        """
        单一文件夹处理;
        :param directory:
        :return:
        """
        feature_li = []
        for img_name in os.listdir(directory):
            img_path = os.path.join(directory, img_name)
            img_feature = self.image_to_features(img_path)
            y_li = [img_name, directory] + img_feature
            feature_li.append(y_li)
        columns = [f"column_{str(i).zfill(4)}" for i in range(1000)]
        columns_li = ["img_name", "img_folder"] + columns
        df = pd.DataFrame(feature_li, columns=columns_li)
        df.to_csv("result.csv", index=False)
        new_df = df.drop_duplicates(subset=columns, keep="first", ignore_index=True)
        # new_df.to_csv("new_result.csv", index=False)
        video_names = set(new_df.img_name.tolist())
        source_video_names = df.img_name.tolist()
        for video_name in source_video_names:
            if video_name in video_names:
                self.delete_file(os.path.join(directory, video_name))

    def many_folder(self, directory):
        """
        二级子目录文件夹处理;
        :param directory:
        :return:
        """
        second_directory_li = os.listdir(directory)
        for folder in second_directory_li:
            self.single_folder(os.path.join(directory, folder))


if __name__ == '__main__':
    """程序启动;
    """
    data_set_folder = r"E:\dataset\image\duplicate"
    obj = DuplicateImage()
    obj.single_folder(data_set_folder)
