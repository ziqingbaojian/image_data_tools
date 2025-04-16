# -*- coding: utf-8 -*-
""" 视频剪切工具;
使用前 pip install moviepy,
"""
import os
import random
import tkinter as tk
from tkinter import filedialog, messagebox

# python 3.8
# from moviepy.editor import VideoFileClip, vfx

# python 3.10
from moviepy import VideoFileClip, vfx


class DirectoryAndFileSelector:
    """ 视频处理;
    """

    def __init__(self, master):
        self.master = master
        self.master.geometry("700x300")
        self.master.title("视频分割工具")

        # 设置公共变量的对象信息;
        self.video_folder = None
        self.result_folder = None
        self.duration = None
        self.exist_timer = 0

        # 创建结果选择目录的标签
        self.result_label = tk.Label(master, text="视频目录:")
        self.result_label.place(x=20, y=20)

        # 创建结果选择目录的输入框
        self.directory_entry = tk.Entry(master, width=50)
        self.directory_entry.place(x=110, y=20)

        # 创建选择目录的按钮
        self.choose_directory_button = tk.Button(master, text="选择目录", command=self.choose_directory)
        self.choose_directory_button.place(x=520, y=20)

        # 创建文件选择目录的标签
        self.file_label = tk.Label(master, text="结果存储目录:")
        self.file_label.place(x=20, y=100)

        # 创建文件选择目录的输入框
        self.file_entry = tk.Entry(master, width=50)
        self.file_entry.place(x=110, y=100)

        # 创建选择文件的按钮
        self.choose_file_button = tk.Button(master, text="选择文件", command=self.choose_file)
        self.choose_file_button.place(x=520, y=100)

        self.run_btn = tk.Button(master, text="开始运行", command=self.run_video)

        self.run_btn.place(x=100, y=150)

    def choose_directory(self):
        directory = filedialog.askdirectory()
        self.video_folder = directory
        self.directory_entry.delete(0, tk.END)
        self.directory_entry.insert(0, directory)

    def choose_file(self):
        file_path = filedialog.askdirectory()
        self.result_folder = file_path
        self.file_entry.delete(0, tk.END)
        self.file_entry.insert(0, file_path)

    def run_video(self):
        """主要处理逻辑;
        """
        print("这里执行了..", self.video_folder, self.result_folder)
        videos = [i for i in os.listdir(self.video_folder) if i.endswith((".mp4", ".avi"))]
        for video in videos:
            video_path = os.path.join(self.video_folder, video)
            print(video, video.rsplit('.')[0])
            target_folder = self.result_folder + "/" + video.rsplit('.')[0]
            print(target_folder)
            if not os.path.isdir(target_folder):
                os.mkdir(target_folder)
            # 进行视频的剪辑;
            with VideoFileClip(video_path) as dur:
                total_time = dur.duration
                self.duration = total_time
            for i in range(int(total_time)):
                target_path = os.path.join(target_folder, f"{video.rsplit('.')[0]}_scene_{str(i).zfill(5)}.mp4")
                self.logic_video(video_path, target_path)
                if self.exist_timer == self.duration:
                    break
            self.exist_timer = 0
        messagebox.showinfo("完成", "剪辑完成！")

    @staticmethod
    def clip_video(video_path, output_path, start_time, end_time):
        """
        按照指定的格式进行裁剪;
        :param video_path:
        :param output_path:
        :param start_time:
        :param end_time:
        :return:
        """
        try:
            # 加载视频文件
            video = VideoFileClip(video_path)
            # 剪辑视频
            clipped_video = video.subclip(start_time, end_time)
            # 保存剪辑后的视频
            clipped_video.write_videofile(output_path, codec='libx264')
            # 进行视频的镜像翻转
            print(output_path)
            fx_target = f"{output_path.rsplit('.', maxsplit=1)[0]}_fx.mp4"
            print(fx_target)
            DirectoryAndFileSelector.clip_video_fx(video_path=output_path, target_path=fx_target)
        except Exception as e:
            print(e)

    @staticmethod
    def clip_video_fx(video_path, target_path):
        """
        视频画面旋转;
        :param video_path: 视频原路径;
        :param target_path: 目录路径;
        :return:
        """
        try:
            clip = VideoFileClip(video_path)
            clip_fx = clip.fx(vfx.mirror_x)  # 沿 x 轴进行翻转
            clip_fx.write_videofile(target_path, codec="libx264")  # 保存视频
        except Exception as e:
            print(f"视频镜像处理出现异常{e}")

    def logic_video(self, video_path, target_path):
        """循环剪切成为短视频;
        """
        timer = random.randint(6, 8)
        start_time = self.exist_timer
        end_timer = start_time + timer
        if end_timer > self.duration:
            end_timer = self.duration
        self.exist_timer = end_timer
        self.clip_video(video_path, target_path, start_time, end_timer)


if __name__ == '__main__':
    # 创建主窗口
    root = tk.Tk()

    # 创建选择器实例
    selector = DirectoryAndFileSelector(root)

    # 运行主循环
    root.mainloop()
