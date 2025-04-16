# !/usr/bin/env python
# -*-coding:utf-8 -*-

"""
# File   : down_video_up.py
# Time   : 2025/4/16 21:35
# Author : 紫青宝剑
"""
# -*- coding: utf-8 -*-
import os
import time
from concurrent.futures import ThreadPoolExecutor

import paramiko
from yt_dlp import YoutubeDL


def youtube_download(url):
    """
    cachedir: 禁用缓存
    quiet: 不打印
    extract_flat: 如果是播放列表，仅返回视频列表，不解析每个视频的下载地址
    """
    ydl = YoutubeDL({'cachedir': False, 'quiet': True, 'extract_flat': True, })
    result = ydl.extract_info(url, download=True)
    return result


def upload_video(response):
    """
    上传视频到服务器;
    :param local_path:
    :param remote_path:
    :return:
    """
    # title = response.result().get("title") + " " + f'[{response.result().get("id")}]' + '.mp4'
    title = response.result().get("requested_downloads")[0].get("_filename")
    hostname = '192.168.177.129'
    port = 22
    username = 'whj'
    password = '123456'
    # 创建SSH客户端
    client = paramiko.SSHClient()

    # 允许连接不在known_hosts文件中的主机
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # 连接服务器
    client.connect(hostname, port=port, username=username, password=password)

    # 创建SFTP客户端
    sftp = client.open_sftp()
    v = r"D:\code\pythoncode\pro_video_utils\scripts"
    local_path = os.path.join(v, title)
    # print(local_path)
    remote_path = '/home/whj/data/video/' + title
    # 上传文件
    sftp.put(local_path, remote_path)
    os.remove(local_path)

    # 关闭SFTP客户端
    sftp.close()

    # 关闭SSH连接
    client.close()

    print("文件上传成功！")
    return True


if __name__ == '__main__':
    pool = ThreadPoolExecutor(10)
    li = [
        'https://www.youtube.com/watch?v=egGrZiFbUCE'
        # "https://www.youtube.com/watch?v=uSVlBs8LB00",
        # "https://www.youtube.com/watch?v=nSDz2W7SbOk",
        # "https://www.youtube.com/watch?v=emK7Me-Mldo",
        # "https://www.youtube.com/watch?v=N3CTgtz3GMc"
    ]

    start = time.time()
    for href in li:
        fur = pool.submit(youtube_download, href)  # 异步多线程
        # fur.add_done_callback(upload_video)
    # pool.shutdown(True)
    end = time.time()  # 使用多线程, 可以缩短一半的时间
    print("运行时间:", end - start)
