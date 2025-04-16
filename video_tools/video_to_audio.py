# -*- coding: utf-8 -*-
""" 视频拆分成为音频文件;
"""

# python 3.8
# import moviepy.editor as mp

import moviepy as mp


def extract_audio(videos_file_path, target_name):
    my_clip = mp.VideoFileClip(videos_file_path)
    my_clip.audio.write_audiofile(f'{target_name}.mp3')


extract_audio('../../data/起风了.mp4', "起风了")
