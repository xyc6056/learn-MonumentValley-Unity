"""这个文件只测试 pygame 键盘输入，不初始化 OpenGL。

运行后会打开一个小窗口。
点击窗口让它获得焦点，然后按 W、A、S、D、方向键或空格。
控制台会打印 pygame 收到的原始按键和映射后的移动方向。
"""

import sys

import pygame


# 让 Windows 终端按 utf-8 输出中文，避免中文变成乱码。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# 按键到移动方向的映射，和游戏里的规则保持一致。
KEY_DIRECTIONS = {
    pygame.K_w: "forward",
    pygame.K_UP: "forward",
    pygame.K_s: "backward",
    pygame.K_DOWN: "backward",
    pygame.K_a: "left",
    pygame.K_LEFT: "left",
    pygame.K_d: "right",
    pygame.K_RIGHT: "right",
    pygame.K_SPACE: "jump",
}


# 用于逐帧轮询的按键名称，避免只看 KEYDOWN 事件。
POLL_KEYS = {
    pygame.K_w: "w",
    pygame.K_UP: "up",
    pygame.K_s: "s",
    pygame.K_DOWN: "down",
    pygame.K_a: "a",
    pygame.K_LEFT: "left",
    pygame.K_d: "d",
    pygame.K_RIGHT: "right",
    pygame.K_SPACE: "space",
}


def force_window_focus():
    """输入：无。输出：无。功能：在 Windows 上尝试把 pygame 窗口切到前台。"""
    try:
        import ctypes

        window_info = pygame.display.get_wm_info()
        window_handle = window_info.get("window")
        if window_handle:
            result = ctypes.windll.user32.SetForegroundWindow(window_handle)
            print(f"自动聚焦结果：{result}", flush=True)
    except Exception as error:
        print(f"自动聚焦失败：{error}", flush=True)


def main():
    """输入：无。输出：无。功能：打开 pygame 窗口并打印键盘事件。"""
    pygame.init()
    screen = pygame.display.set_mode((520, 220))
    pygame.display.set_caption("键盘输入测试：请先点击窗口")
    force_window_focus()
    print("测试已启动，请点击窗口后按键。", flush=True)
    focus_gained = getattr(pygame, "WINDOWFOCUSGAINED", None)
    focus_lost = getattr(pygame, "WINDOWFOCUSLOST", None)
    running = True
    previous_pressed = {key: False for key in POLL_KEYS}
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif focus_gained is not None and event.type == focus_gained:
                print("窗口获得焦点", flush=True)
            elif focus_lost is not None and event.type == focus_lost:
                print("窗口失去焦点", flush=True)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                key_name = pygame.key.name(event.key)
                direction = KEY_DIRECTIONS.get(event.key, "未映射")
                print(f"KEYDOWN 原始按键={key_name} 映射方向={direction}", flush=True)

        screen.fill((245, 235, 255))
        # 用简单色块代替文字，避免 pygame 字体初始化兼容问题。
        pygame.draw.rect(screen, (150, 100, 220), (30, 80, 460, 60), border_radius=8)
        pygame.display.flip()

        # 轮询当前按住的键，确认是否只是 KEYDOWN 事件被输入法截走。
        pressed_keys = pygame.key.get_pressed()
        for key_code, key_name in POLL_KEYS.items():
            is_pressed = pressed_keys[key_code]
            if is_pressed and not previous_pressed[key_code]:
                print(f"轮询检测到按下：{key_name}", flush=True)
            previous_pressed[key_code] = is_pressed

    pygame.quit()


if __name__ == "__main__":
    main()
