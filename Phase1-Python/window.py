"""这个文件负责创建 pygame 窗口、处理窗口事件和刷新显示。

它只管理窗口、鼠标点击、鼠标拖拽、退出事件和画面刷新，不负责 OpenGL 绘制。
"""

import math

import pygame


# 窗口宽度，单位为像素。
WINDOW_WIDTH = 800
# 窗口高度，单位为像素。
WINDOW_HEIGHT = 600
# 窗口标题，方便确认当前运行的是第几个 Demo。
WINDOW_TITLE = "非欧几何解谜 Demo 5"
# 鼠标水平移动 1 像素时，岛屿旋转的角度。
ROTATION_DEGREES_PER_PIXEL = 0.45
# 鼠标按下后移动不超过这个距离，松开时算点击。
CLICK_MAX_MOVEMENT_PIXELS = 5.0


class InputState:
    """这个类保存窗口运行状态、鼠标点击状态、拖拽状态和鼠标位置。"""

    def __init__(self):
        """输入：无。输出：无。功能：初始化输入状态。"""
        # 窗口是否继续运行。
        self.running = True
        # 鼠标左键是否处于按下状态。
        self.mouse_down = False
        # 鼠标是否已经超过点击阈值，进入拖拽旋转状态。
        self.dragging = False
        # 鼠标按下时的屏幕位置。
        self.press_position = (0, 0)
        # 本次按下是否已经进入拖拽状态。
        self.drag_started = False
        # 本帧是否完成了一次点击，保存点击位置。
        self.clicked_position = None
        # 本帧是否完成了一次拖拽并松手。
        self.drag_released = False
        # 本帧鼠标水平移动产生的旋转角度。
        self.rotation_delta = 0.0
        # 本帧是否刚开始拖拽旋转。
        self.rotation_started = False
        # 当前鼠标位置，用于悬停高亮。
        self.mouse_position = None
        # 本帧按下的键盘按键列表。
        self.key_events = []
        # 本帧是否按下 Esc。
        self.escape_pressed = False


def create_window():
    """输入：无。输出：pygame 显示表面。功能：初始化 pygame 并创建 OpenGL 窗口。"""
    pygame.init()

    # 请求 24 位深度缓冲，后面的 3D 方块才能正确进行深度遮挡。
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    # 请求双缓冲，绘制完成后再整帧显示，避免画面闪烁。
    pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)

    # OPENGL 表示由 PyOpenGL 负责绘制，DOUBLEBUF 表示使用双缓冲。
    screen = pygame.display.set_mode(
        (WINDOW_WIDTH, WINDOW_HEIGHT),
        pygame.OPENGL | pygame.DOUBLEBUF,
    )
    pygame.display.set_caption(WINDOW_TITLE)
    return screen


def create_input_state():
    """输入：无。输出：InputState 对象。功能：创建鼠标和窗口输入状态。"""
    return InputState()


def process_events(input_state):
    """输入：输入状态。输出：窗口是否继续运行。功能：读取鼠标和键盘事件。"""
    # 每帧先清空上一帧的瞬时输入。
    input_state.clicked_position = None
    input_state.drag_released = False
    input_state.rotation_delta = 0.0
    input_state.rotation_started = False
    input_state.key_events = []
    input_state.escape_pressed = False

    for event in pygame.event.get():
        # 用户点击窗口右上角关闭按钮时退出主循环。
        if event.type == pygame.QUIT:
            input_state.running = False
        # 记录所有键盘按下，交给菜单和游戏逻辑处理。
        elif event.type == pygame.KEYDOWN:
            input_state.key_events.append(event.key)
            if event.key == pygame.K_ESCAPE:
                input_state.escape_pressed = True
        # 鼠标左键按下时开始记录本次操作。
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            input_state.mouse_down = True
            input_state.dragging = False
            input_state.drag_started = False
            input_state.press_position = event.pos
            input_state.mouse_position = event.pos
        # 鼠标移动时，先判断是否超过点击阈值，再决定是否旋转。
        elif event.type == pygame.MOUSEMOTION:
            input_state.mouse_position = event.pos
            if input_state.mouse_down:
                if not input_state.drag_started:
                    difference_x = event.pos[0] - input_state.press_position[0]
                    difference_y = event.pos[1] - input_state.press_position[1]
                    movement_distance = math.hypot(difference_x, difference_y)
                    if movement_distance > CLICK_MAX_MOVEMENT_PIXELS:
                        input_state.drag_started = True
                        input_state.dragging = True
                        input_state.rotation_started = True
                if input_state.dragging:
                    input_state.rotation_delta += (
                        event.rel[0] * ROTATION_DEGREES_PER_PIXEL
                    )
        # 鼠标左键松开时，根据是否拖拽来决定点击或吸附。
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if input_state.mouse_down:
                difference_x = event.pos[0] - input_state.press_position[0]
                difference_y = event.pos[1] - input_state.press_position[1]
                movement_distance = math.hypot(difference_x, difference_y)
                if (
                    input_state.drag_started
                    or movement_distance > CLICK_MAX_MOVEMENT_PIXELS
                ):
                    input_state.drag_released = True
                else:
                    input_state.clicked_position = event.pos
            input_state.mouse_down = False
            input_state.dragging = False
            input_state.drag_started = False
            input_state.mouse_position = event.pos

    # 即使没有鼠标移动事件，也读取一次当前位置，方便悬停高亮。
    if input_state.mouse_position is None:
        input_state.mouse_position = pygame.mouse.get_pos()

    return input_state.running


def refresh_display():
    """输入：无。输出：无。功能：交换双缓冲，把这一帧的绘制结果显示到窗口。"""
    pygame.display.flip()


def set_window_caption(caption):
    """输入：窗口标题。输出：无。功能：修改窗口标题作为教学提示。"""
    pygame.display.set_caption(caption)


def close_window():
    """输入：无。输出：无。功能：关闭 pygame 并释放窗口相关资源。"""
    pygame.quit()
