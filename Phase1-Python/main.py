"""这个文件是游戏的程序入口和状态主循环。

它负责主菜单、选关、游戏、暂停、过关和进度保存。
"""

import sys
import time
from pathlib import Path

# 让 Windows 终端按 utf-8 输出调试信息，避免中文乱码。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from OpenGL.GL import glViewport

import audio
import database
import ui
from camera import create_projection_matrix, create_view_matrix
from level import (
    build_connectivity_graph,
    find_block,
    find_clicked_block,
    find_goal_block,
    find_path,
    get_block_click_distance,
    get_reachable_blocks,
    is_block_standable,
    load_level,
    update_block_screen_positions,
)
from player import Player
from renderer import (
    begin_frame,
    begin_island_transform,
    draw_completion_effect,
    draw_connectivity_edges,
    draw_fireflies_for_blocks,
    draw_highlight,
    draw_highlights,
    draw_level,
    draw_shadows,
    draw_water_for_blocks,
    end_island_transform,
    initialize_renderer,
    HOVER_HIGHLIGHT_COLOR,
    REACHABLE_HIGHLIGHT_COLOR,
)
from window import (
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
    close_window,
    create_input_state,
    create_window,
    process_events,
    refresh_display,
    set_window_caption,
)


# 方块边长，单位是 OpenGL 坐标单位。
BLOCK_SIZE = 1.0
# 关卡文件路径表。
LEVEL_PATHS = {
    1: Path(__file__).resolve().parent / "levels" / "level1.txt",
    2: Path(__file__).resolve().parent / "levels" / "level2.txt",
    3: Path(__file__).resolve().parent / "levels" / "level3.txt",
    4: Path(__file__).resolve().parent / "levels" / "level4.txt",
    5: Path(__file__).resolve().parent / "levels" / "level5.txt",
}
# 每个关卡的起点方块坐标。
LEVEL_STARTS = {
    1: (0, -1, -1),
    2: (0, -1, -1),
    3: (0, -1, -1),
    4: (0, -1, -1),
    5: (0, -1, -1),
}
# 进度数据库路径。
DATABASE_PATH = Path(__file__).resolve().parent / "progress.db"
# 总关卡数。
TOTAL_LEVELS = len(LEVEL_PATHS)
# 过关动画持续时间。
COMPLETION_DURATION_SECONDS = 2.5
# 自动吸附速度，单位为度每秒。
SNAP_SPEED_DEGREES_PER_SECOND = 360.0
# 单帧最大时间，避免窗口卡顿后自动旋转跳跃过大。
MAX_FRAME_DELTA_SECONDS = 0.05
# 判断角度是否已经到达目标的小误差范围。
ANGLE_EPSILON = 0.001
# 是否在终端打印当前所有屏幕连通对。
DEBUG_CONNECTIVITY = False

# 游戏状态。
STATE_MAIN_MENU = "main_menu"
STATE_LEVEL_SELECT = "level_select"
STATE_PLAYING = "playing"
STATE_PAUSED = "paused"


def setup_viewport():
    """输入：无。输出：无。功能：让 OpenGL 绘制区域覆盖整个窗口。"""
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)


def get_snap_target(angle):
    """输入：当前角度。输出：最近的 90 度倍数。功能：计算自动吸附目标。"""
    return round(angle / 90.0) * 90.0


def move_towards(current_angle, target_angle, max_delta):
    """输入：当前角度、目标角度和本帧最大变化量。输出：移动后的角度。"""
    difference = target_angle - current_angle
    if abs(difference) <= max_delta:
        return target_angle
    return current_angle + (max_delta if difference > 0.0 else -max_delta)


def update_island_angle(current_angle, target_angle, is_snapping, input_state, delta_time):
    """输入：角度、吸附状态、输入状态和帧间隔。输出：新角度、目标角度、吸附状态、是否完成。"""
    if input_state.dragging:
        current_angle += input_state.rotation_delta
        return current_angle, current_angle, False, False

    if input_state.drag_released:
        target_angle = get_snap_target(current_angle)
        if abs(current_angle - target_angle) <= ANGLE_EPSILON:
            normalized_angle = current_angle % 360.0
            return normalized_angle, normalized_angle, False, True
        return current_angle, target_angle, True, False

    if not is_snapping:
        return current_angle, target_angle, False, False

    max_delta = SNAP_SPEED_DEGREES_PER_SECOND * delta_time
    current_angle = move_towards(current_angle, target_angle, max_delta)

    if abs(target_angle - current_angle) <= ANGLE_EPSILON:
        normalized_angle = target_angle % 360.0
        return normalized_angle, normalized_angle, False, True

    return current_angle, target_angle, True, False


def print_click_debug(blocks, clicked_position):
    """输入：方块列表和点击屏幕坐标。输出：无。功能：打印点击选格的 2D 距离调试信息。"""
    print(f"点击屏幕坐标：{clicked_position}")
    for block in blocks:
        distance = get_block_click_distance(block, clicked_position)
        standable = is_block_standable(block, blocks)
        print(
            f"  方块=({block.x}, {block.y}, {block.z}) "
            f"屏幕2D=({block.screen_x:.2f}, {block.screen_y:.2f}) "
            f"距离={distance:.2f} 可站立={standable}"
        )


def try_click_move(player, blocks, adjacency, input_state, can_click):
    """输入：小人、方块、当前连通表、输入状态和是否允许点击。输出：无。"""
    if not can_click or player.moving or player.path_queue or input_state.clicked_position is None:
        return

    print_click_debug(blocks, input_state.clicked_position)
    clicked_block = find_clicked_block(blocks, input_state.clicked_position)
    if clicked_block is None:
        print("选中方块：无")
        player.play_blocked_feedback()
        return
    print(f"选中方块：({clicked_block.x}, {clicked_block.y}, {clicked_block.z})")

    if clicked_block is player.current_block:
        return

    path_blocks = find_path(player.current_block, clicked_block, blocks, adjacency)
    if not path_blocks:
        player.play_blocked_feedback()
        return

    player.follow_path(path_blocks)


def get_hovered_block(player, blocks, input_state, reachable_blocks):
    """输入：小人、方块、输入状态和可达列表。输出：悬停且可达的方块或 None。"""
    if input_state.mouse_position is None:
        return None
    hovered_block = find_clicked_block(blocks, input_state.mouse_position)
    if hovered_block is None or hovered_block is player.current_block:
        return None
    if hovered_block not in reachable_blocks:
        return None
    return hovered_block


def get_menu_click_index(input_state, item_count, start_y, step_y):
    """输入：输入状态、选项数量、起始高度和间距。输出：鼠标点击的选项下标或 None。"""
    if input_state.clicked_position is None:
        return None

    click_x, click_y = input_state.clicked_position
    normalized_x = click_x / WINDOW_WIDTH * 2.0 - 1.0
    normalized_y = 1.0 - click_y / WINDOW_HEIGHT * 2.0

    for index in range(item_count):
        item_y = start_y - index * step_y
        if abs(normalized_x) <= 0.36 and abs(normalized_y - item_y) <= 0.065:
            return index
    return None


def get_key_menu_change(input_state, item_count):
    """输入：输入状态和选项数量。输出：光标变化量。功能：把方向键转换成菜单移动。"""
    change = 0
    for key in input_state.key_events:
        if key in (87, 119, 1073741906):  # W 和上方向键
            change -= 1
        if key in (83, 115, 1073741905):  # S 和下方向键
            change += 1
    if change == 0:
        return 0
    return change % item_count


def is_enter_pressed(input_state):
    """输入：输入状态。输出：是否按下确认键。"""
    return any(key in (13, 32) for key in input_state.key_events)


def print_connected_pairs(blocks, adjacency):
    """输入：方块和邻接表。输出：无。功能：打印当前所有屏幕连通对。"""
    print("当前屏幕连通对：")
    pair_count = 0
    for first_index in range(len(blocks)):
        first_block = blocks[first_index]
        neighbor_ids = {id(block) for block in adjacency.get(id(first_block), [])}
        for second_index in range(first_index + 1, len(blocks)):
            second_block = blocks[second_index]
            if id(second_block) not in neighbor_ids:
                continue
            pair_count += 1
            print(
                f"  ({first_block.x},{first_block.y},{first_block.z}) {first_block.shape}"
                f" <-> ({second_block.x},{second_block.y},{second_block.z}) {second_block.shape}"
            )
    if pair_count == 0:
        print("  无")
    print("连通对打印结束")


def load_scene(level_number, projection_matrix, view_matrix):
    """输入：关卡编号和相机矩阵。输出：方块、终点、小人和连通表。"""
    blocks = load_level(LEVEL_PATHS[level_number])
    start_block = find_block(blocks, *LEVEL_STARTS[level_number])
    goal_block = find_goal_block(blocks)
    if goal_block is None:
        raise ValueError(f"第 {level_number} 关没有金色终点方块")
    player = Player(start_block)
    update_block_screen_positions(blocks, projection_matrix, view_matrix, 0.0)
    adjacency = build_connectivity_graph(blocks)
    if DEBUG_CONNECTIVITY:
        print_connected_pairs(blocks, adjacency)
    return blocks, goal_block, player, adjacency


def get_level_rows():
    """输入：无。输出：选关界面文字列表。功能：从数据库读取每关完成状态。"""
    rows = []
    for level_number in sorted(LEVEL_PATHS):
        progress = database.read_progress(DATABASE_PATH, level_number)
        completed = progress is not None and progress["completed"]
        status = "已通关" if completed else "未通关"
        rows.append(f"第 {level_number} 关    {status}")
    return rows


def draw_game_scene(
    projection_matrix,
    view_matrix,
    blocks,
    goal_block,
    player,
    adjacency,
    island_angle,
    reachable_blocks,
    hovered_block,
    completion_active,
    completion_elapsed,
):
    """输入：场景数据和状态。输出：无。功能：绘制 3D 游戏场景但不刷新屏幕。"""
    begin_frame(projection_matrix, view_matrix, island_angle)
    draw_water_for_blocks(blocks)
    begin_island_transform(island_angle)
    draw_shadows(blocks)
    draw_level(blocks, BLOCK_SIZE)
    draw_connectivity_edges(blocks, adjacency)
    draw_highlights(reachable_blocks, REACHABLE_HIGHLIGHT_COLOR)
    if hovered_block is not None:
        draw_highlight(hovered_block, HOVER_HIGHLIGHT_COLOR)
    player.draw()
    if completion_active:
        progress = min(completion_elapsed / COMPLETION_DURATION_SECONDS, 1.0)
        draw_completion_effect(goal_block, progress)
    end_island_transform()
    draw_fireflies_for_blocks(blocks)


def main():
    """输入：无。输出：退出码。功能：启动菜单和游戏主循环。"""
    database.initialize_database(DATABASE_PATH)
    input_state = create_input_state()
    create_window()

    try:
        setup_viewport()
        initialize_renderer()
        audio.initialize_audio()
        projection_matrix = create_projection_matrix()
        view_matrix = create_view_matrix()

        game_state = STATE_MAIN_MENU
        menu_index = 0
        level_select_index = 0
        pause_index = 0
        current_level = 1
        blocks = []
        goal_block = None
        player = None
        connectivity_adjacency = {}
        island_angle = 0.0
        target_angle = 0.0
        is_snapping = False
        completion_active = False
        completion_elapsed = 0.0
        has_rotated = False
        previous_time = time.perf_counter()

        while process_events(input_state):
            current_time = time.perf_counter()
            delta_time = min(current_time - previous_time, MAX_FRAME_DELTA_SECONDS)
            previous_time = current_time

            if game_state == STATE_MAIN_MENU:
                items = ["开始游戏", "选择关卡", "退出"]
                change = get_key_menu_change(input_state, len(items))
                if change != 0:
                    menu_index = (menu_index + change) % len(items)
                clicked_index = get_menu_click_index(input_state, len(items), 0.20, 0.17)
                if clicked_index is not None:
                    menu_index = clicked_index
                    activate = True
                else:
                    activate = is_enter_pressed(input_state)

                if activate:
                    if menu_index == 0:
                        current_level = 1
                        blocks, goal_block, player, connectivity_adjacency = load_scene(
                            current_level, projection_matrix, view_matrix
                        )
                        island_angle = 0.0
                        target_angle = 0.0
                        is_snapping = False
                        has_rotated = False
                        set_window_caption("拖动鼠标旋转")
                        game_state = STATE_PLAYING
                    elif menu_index == 1:
                        level_select_index = 0
                        game_state = STATE_LEVEL_SELECT
                    else:
                        input_state.running = False

                begin_frame(projection_matrix, view_matrix)
                ui.draw_menu_panel("非欧几何解谜", items, menu_index, "拖动旋转，点击方块移动")
                refresh_display()
                continue

            if game_state == STATE_LEVEL_SELECT:
                rows = get_level_rows()
                change = get_key_menu_change(input_state, len(rows))
                if change != 0:
                    level_select_index = (level_select_index + change) % len(rows)
                clicked_index = get_menu_click_index(input_state, len(rows), 0.34, 0.14)
                if clicked_index is not None:
                    level_select_index = clicked_index
                    activate = True
                else:
                    activate = is_enter_pressed(input_state)

                if input_state.escape_pressed:
                    game_state = STATE_MAIN_MENU
                elif activate:
                    current_level = level_select_index + 1
                    blocks, goal_block, player, connectivity_adjacency = load_scene(
                        current_level, projection_matrix, view_matrix
                    )
                    island_angle = 0.0
                    target_angle = 0.0
                    is_snapping = False
                    has_rotated = current_level != 1
                    set_window_caption("拖动鼠标旋转" if current_level == 1 else WINDOW_TITLE)
                    game_state = STATE_PLAYING

                begin_frame(projection_matrix, view_matrix)
                ui.draw_level_select(rows, level_select_index)
                refresh_display()
                continue

            if game_state == STATE_PAUSED:
                items = ["继续游戏", "重开本关", "回主菜单"]
                change = get_key_menu_change(input_state, len(items))
                if change != 0:
                    pause_index = (pause_index + change) % len(items)
                clicked_index = get_menu_click_index(input_state, len(items), 0.20, 0.17)
                if clicked_index is not None:
                    pause_index = clicked_index
                    activate = True
                else:
                    activate = is_enter_pressed(input_state)

                if activate:
                    if pause_index == 0:
                        game_state = STATE_PLAYING
                    elif pause_index == 1:
                        blocks, goal_block, player, connectivity_adjacency = load_scene(
                            current_level, projection_matrix, view_matrix
                        )
                        island_angle = 0.0
                        target_angle = 0.0
                        is_snapping = False
                        completion_active = False
                        completion_elapsed = 0.0
                        game_state = STATE_PLAYING
                    else:
                        game_state = STATE_MAIN_MENU
                        menu_index = 0

                draw_game_scene(
                    projection_matrix,
                    view_matrix,
                    blocks,
                    goal_block,
                    player,
                    connectivity_adjacency,
                    island_angle,
                    [],
                    None,
                    False,
                    0.0,
                )
                ui.draw_pause_menu(pause_index)
                refresh_display()
                continue

            if input_state.escape_pressed:
                pause_index = 0
                game_state = STATE_PAUSED
                continue

            if input_state.rotation_started and not has_rotated:
                has_rotated = True
                audio.play_rotate()
                set_window_caption(WINDOW_TITLE)

            island_angle, target_angle, is_snapping, snap_finished = update_island_angle(
                island_angle,
                target_angle,
                is_snapping,
                input_state,
                delta_time,
            )
            if snap_finished:
                update_block_screen_positions(
                    blocks, projection_matrix, view_matrix, island_angle
                )
                connectivity_adjacency = build_connectivity_graph(blocks)
                if DEBUG_CONNECTIVITY:
                    print_connected_pairs(blocks, connectivity_adjacency)

            can_click = not input_state.dragging and not is_snapping and not completion_active
            if can_click:
                try_click_move(player, blocks, connectivity_adjacency, input_state, can_click)
            player.update(delta_time)
            if player.step_started:
                if player.animation_type == "jump":
                    audio.play_jump()
                else:
                    audio.play_move()
                player.step_started = False

            if (
                not completion_active
                and player.current_block is goal_block
                and not player.moving
                and not player.path_queue
            ):
                completion_active = True
                completion_elapsed = 0.0
                player.start_celebration()
                audio.play_complete()
                database.save_progress(DATABASE_PATH, current_level, True)

            reachable_blocks = []
            hovered_block = None
            if can_click and not completion_active and not player.moving and not player.path_queue:
                reachable_blocks = get_reachable_blocks(
                    player.current_block, blocks, connectivity_adjacency
                )
                hovered_block = get_hovered_block(
                    player, blocks, input_state, reachable_blocks
                )

            draw_game_scene(
                projection_matrix,
                view_matrix,
                blocks,
                goal_block,
                player,
                connectivity_adjacency,
                island_angle,
                reachable_blocks,
                hovered_block,
                completion_active,
                completion_elapsed,
            )
            refresh_display()

            if completion_active:
                completion_elapsed += delta_time
                if completion_elapsed >= COMPLETION_DURATION_SECONDS:
                    if current_level < TOTAL_LEVELS:
                        current_level += 1
                        blocks, goal_block, player, connectivity_adjacency = load_scene(
                            current_level, projection_matrix, view_matrix
                        )
                        island_angle = 0.0
                        target_angle = 0.0
                        is_snapping = False
                        completion_active = False
                        completion_elapsed = 0.0
                        has_rotated = True
                        set_window_caption(WINDOW_TITLE)
                    else:
                        game_state = STATE_MAIN_MENU
                        menu_index = 0
                        completion_active = False
                        completion_elapsed = 0.0
    finally:
        close_window()

    return 0


if __name__ == "__main__":
    # 用系统退出码结束程序。
    sys.exit(main())
