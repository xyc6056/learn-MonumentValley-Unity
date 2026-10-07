"""这个文件负责使用 pygame 生成并播放简单音效。

不加载外部音频文件，所有音效都在启动时用正弦波生成。
"""

import array
import math

import pygame


# 音频采样率。
SAMPLE_RATE = 44100


def _create_tone(frequency, duration, volume=0.25, fade_out=True):
    """输入：频率、时长和音量。输出：pygame Sound。功能：生成简单正弦音效。"""
    sample_count = int(SAMPLE_RATE * duration)
    samples = array.array("h")

    for index in range(sample_count):
        time_seconds = index / SAMPLE_RATE
        fade = 1.0
        if fade_out:
            # 末端淡出，避免播放结束时出现爆音。
            fade = max(0.0, 1.0 - index / sample_count)
        value = math.sin(2.0 * math.pi * frequency * time_seconds)
        samples.append(int(value * volume * fade * 32767))

    return pygame.mixer.Sound(buffer=samples.tobytes())


def initialize_audio():
    """输入：无。输出：无。功能：初始化混音器并生成全部音效。"""
    try:
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
    except pygame.error as error:
        print(f"音效初始化失败：{error}")
        return
    globals()["rotate_sound"] = _create_tone(420.0, 0.12, 0.20)
    globals()["move_sound"] = _create_tone(620.0, 0.08, 0.18)
    globals()["jump_sound"] = _create_tone(780.0, 0.14, 0.22)
    globals()["complete_sound"] = _create_tone(880.0, 0.45, 0.28)


def play_rotate():
    """输入：无。输出：无。功能：播放旋转音效。"""
    sound = globals().get("rotate_sound")
    if sound is not None:
        sound.play()


def play_move():
    """输入：无。输出：无。功能：播放移动音效。"""
    sound = globals().get("move_sound")
    if sound is not None:
        sound.play()


def play_jump():
    """输入：无。输出：无。功能：播放跳跃音效。"""
    sound = globals().get("jump_sound")
    if sound is not None:
        sound.play()


def play_complete():
    """输入：无。输出：无。功能：播放过关音效。"""
    sound = globals().get("complete_sound")
    if sound is not None:
        sound.play()
