# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File   : img_tag.py
# Time   : 2025/4/16 21:48
# Author : 紫青宝剑
"""
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
import json
import os
import sqlite3
from datetime import datetime


class ImageLabeler:
    def __init__(self, root):
        self.root = root
        self.root.title("图片标注工具")

        # 读取配置文件
        with open('config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)

        # 初始化变量
        self.image_folder = ""
        self.image_list = []
        self.current_index = -1
        self.category_var = tk.StringVar()

        # 创建数据库
        self.conn = sqlite3.connect('labels.db')
        self.create_table()

        # 创建界面
        self.create_widgets()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS labels
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      image_path TEXT UNIQUE,
                      category TEXT,
                      create_time DATETIME)''')
        self.conn.commit()

    def create_widgets(self):
        # 使用绝对坐标布局
        # 加载文件夹按钮
        self.btn_load = tk.Button(self.root, text="加载图片文件夹", command=self.load_folder)
        self.btn_load.place(x=20, y=20, width=120, height=30)

        # 图片显示区域
        self.image_label = tk.Label(self.root, borderwidth=2, relief="groove")
        self.image_label.place(x=160, y=20, width=600, height=400)

        # 类别选择下拉框
        self.category_cb = ttk.Combobox(self.root, textvariable=self.category_var,
                                        values=self.config["categories"])
        self.category_cb.place(x=20, y=70, width=120, height=30)

        # 按钮区域
        self.btn_prev = tk.Button(self.root, text="上一张", command=self.prev_image)
        self.btn_prev.place(x=20, y=120, width=120, height=30)

        self.btn_next = tk.Button(self.root, text="下一张", command=self.next_image)
        self.btn_next.place(x=20, y=170, width=120, height=30)

        self.btn_submit = tk.Button(self.root, text="提交并下一张", command=self.submit)
        self.btn_submit.place(x=20, y=220, width=120, height=30)

    def load_folder(self):
        self.image_folder = filedialog.askdirectory()
        if self.image_folder:
            # 获取所有图片文件
            extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp']
            self.image_list = [os.path.join(self.image_folder, f)
                               for f in os.listdir(self.image_folder)
                               if f.split('.')[-1].lower() in extensions]
            if self.image_list:
                self.current_index = 0
                self.show_image()

    def show_image(self):
        if 0 <= self.current_index < len(self.image_list):
            image_path = self.image_list[self.current_index]

            # 加载图片并调整大小
            img = Image.open(image_path)
            img.thumbnail((600, 400))  # 保持比例缩放
            photo = ImageTk.PhotoImage(img)

            self.image_label.config(image=photo)
            self.image_label.image = photo  # 保持引用

            # 检查已有标注
            self.load_existing_label(image_path)

    def load_existing_label(self, image_path):
        cursor = self.conn.cursor()
        cursor.execute("SELECT category FROM labels WHERE image_path=?", (image_path,))
        result = cursor.fetchone()
        if result:
            self.category_var.set(result)
        else:
            self.category_var.set('')

    def prev_image(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.show_image()

    def next_image(self):
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.show_image()

    def submit(self):
        if self.current_index == -1:
            return

        image_path = self.image_list[self.current_index]
        category = self.category_var.get()

        if category:
            cursor = self.conn.cursor()
            # 使用INSERT OR REPLACE处理重复路径
            cursor.execute('''INSERT OR REPLACE INTO labels 
                            (image_path, category, create_time)
                            VALUES (?, ?, ?)''',
                           (image_path, category, datetime.now()))
            self.conn.commit()

            # 自动切换到下一张
            self.next_image()

    def __del__(self):
        self.conn.close()


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("800x450")
    app = ImageLabeler(root)
    root.mainloop()
