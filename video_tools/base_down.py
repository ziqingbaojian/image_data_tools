# -*- coding: utf-8 -*-
import time
from concurrent.futures import ThreadPoolExecutor
from yt_dlp import YoutubeDL


def youtube_download(url):
    """
    cachedir: 禁用缓存
    quiet: 不打印
    extract_flat: 如果是播放列表，仅返回视频列表，不解析每个视频的下载地址
    """
    download_options = {
        'writesubtitles': True,
        'subtitleslangs': ['en', 'zh'],
        'format': 'bestvideo+bestaudio',  # 下载最好格式的视频和音频
        'outtmpl': '%(title)s.%(ext)s',  # 设置下载文件的命名模板
        'merge_output_format': 'mp4'  # 将视频和音频合并为mp4格式
    }
    # ydl = YoutubeDL({'cachedir': False, 'quiet': True, 'extract_flat': True, })
    ydl = YoutubeDL(download_options)
    result = ydl.extract_info(url, download=True)
    return result


if __name__ == '__main__':
    pool = ThreadPoolExecutor(10)
    # li = [
    # "https://www.bilibili.com/video/BV1fK421h7ke",
    # ]
    li = [f"https://www.bilibili.com/video/BV1tQBXYYEwa/?p={i}" for i in range(90)]

    start = time.time()
    for href in li:
        fur = pool.submit(youtube_download, href)  # 异步多线程
    pool.shutdown(True)
    end = time.time()  # 使用多线程, 可以缩短一半的时间
    print("运行时间:", end - start)
