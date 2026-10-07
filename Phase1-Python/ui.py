"""这个文件负责绘制菜单、选关和暂停界面。

界面全部使用 pygame 字体生成纹理，再交给 PyOpenGL 绘制。
"""

import pygame

from OpenGL.GL import (
    GL_BLEND,
    GL_DEPTH_TEST,
    GL_LINEAR,
    GL_MODELVIEW,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_PROJECTION,
    GL_QUADS,
    GL_RGBA,
    GL_SRC_ALPHA,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_UNSIGNED_BYTE,
    glBegin,
    glBindTexture,
    glBlendFunc,
    glColor4f,
    glDisable,
    glEnable,
    glEnd,
    glGenTextures,
    glLoadIdentity,
    glMatrixMode,
    glPopMatrix,
    glPushMatrix,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glVertex2f,
)

from window import WINDOW_HEIGHT, WINDOW_WIDTH


# 字体缓存和纹理缓存，避免每帧重复创建资源。
FONT_CACHE = {}
TEXTURE_CACHE = {}
FONT_PATHS = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "C:/Windows/Fonts/simsun.ttc",
]


def get_font(size):
    """输入：字号。输出：字体对象。功能：优先加载中文字体。"""
    if size in FONT_CACHE:
        return FONT_CACHE[size]

    font = None
    for font_path in FONT_PATHS:
        try:
            font = pygame.font.Font(font_path, size)
            break
        except Exception:
            continue

    if font is None:
        font = pygame.font.Font(None, size)

    FONT_CACHE[size] = font
    return font


def draw_rect(center_x, center_y, half_width, half_height, color, alpha=1.0):
    """输入：中心、半宽高、颜色和透明度。输出：无。功能：绘制屏幕矩形。"""
    glDisable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor4f(color[0], color[1], color[2], alpha)
    glBegin(GL_QUADS)
    glVertex2f(center_x - half_width, center_y - half_height)
    glVertex2f(center_x + half_width, center_y - half_height)
    glVertex2f(center_x + half_width, center_y + half_height)
    glVertex2f(center_x - half_width, center_y + half_height)
    glEnd()
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glDisable(GL_BLEND)


def draw_text(text, center_x, center_y, size, color=(1.0, 1.0, 1.0), alpha=1.0):
    """输入：文字、中心、字号、颜色和透明度。输出：无。功能：绘制屏幕文字。"""
    font = get_font(size)
    text_surface = font.render(text, True, color)
    texture_key = (text, size, color)

    if texture_key not in TEXTURE_CACHE:
        texture_data = pygame.image.tostring(text_surface, "RGBA", True)
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D,
            0,
            GL_RGBA,
            text_surface.get_width(),
            text_surface.get_height(),
            0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            texture_data,
        )
        TEXTURE_CACHE[texture_key] = texture

    texture = TEXTURE_CACHE[texture_key]
    half_width = text_surface.get_width() / WINDOW_WIDTH
    half_height = text_surface.get_height() / WINDOW_HEIGHT

    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, texture)
    glColor4f(1.0, 1.0, 1.0, alpha)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(center_x - half_width, center_y - half_height)
    glTexCoord2f(1.0, 0.0)
    glVertex2f(center_x + half_width, center_y - half_height)
    glTexCoord2f(1.0, 1.0)
    glVertex2f(center_x + half_width, center_y + half_height)
    glTexCoord2f(0.0, 1.0)
    glVertex2f(center_x - half_width, center_y + half_height)
    glEnd()
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glDisable(GL_TEXTURE_2D)
    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)


def draw_menu_panel(title, items, selected_index, subtitle=None):
    """输入：标题、选项、选中下标和副标题。输出：None。功能：绘制统一风格菜单。"""
    draw_rect(0.0, 0.0, 0.48, 0.62, (0.20, 0.12, 0.34), 0.72)
    draw_text(title, 0.0, 0.47, 42, (1.0, 0.87, 0.96))

    if subtitle is not None:
        draw_text(subtitle, 0.0, 0.35, 24, (0.88, 0.86, 1.0), 0.92)

    start_y = 0.20
    step_y = 0.17
    for index, item in enumerate(items):
        item_y = start_y - index * step_y
        if index == selected_index:
            draw_rect(0.0, item_y, 0.34, 0.065, (0.72, 0.46, 0.95), 0.85)
            text_color = (1.0, 1.0, 1.0)
        else:
            text_color = (0.86, 0.84, 0.96)
        draw_text(item, 0.0, item_y, 30, text_color)


def draw_level_select(level_rows, selected_index):
    """输入：关卡行和选中下标。输出：None。功能：绘制选关界面。"""
    draw_rect(0.0, 0.0, 0.52, 0.68, (0.20, 0.12, 0.34), 0.74)
    draw_text("选择关卡", 0.0, 0.52, 40, (1.0, 0.87, 0.96))

    start_y = 0.34
    step_y = 0.14
    for index, row in enumerate(level_rows):
        item_y = start_y - index * step_y
        if index == selected_index:
            draw_rect(0.0, item_y, 0.36, 0.055, (0.72, 0.46, 0.95), 0.85)
            text_color = (1.0, 1.0, 1.0)
        else:
            text_color = (0.86, 0.84, 0.96)
        draw_text(row, 0.0, item_y, 27, text_color)


def draw_pause_menu(selected_index):
    """输入：选中下标。输出：None。功能：绘制暂停菜单。"""
    draw_rect(0.0, 0.0, 1.0, 1.0, (0.12, 0.08, 0.22), 0.45)
    draw_menu_panel("已暂停", ["继续游戏", "重开本关", "回主菜单"], selected_index)
