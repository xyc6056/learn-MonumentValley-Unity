"""这个文件负责读取关卡文本并生成方块数据。

关卡文件每行一个方块，格式为：x,y,z,颜色。
新格式为：形状,x,y,z,颜色,是否可走；旧格式 x,y,z,颜色 仍可读取。
它还负责在岛屿吸附到 90 度后重新计算所有方块的屏幕位置。
它还负责按小人朝向和高度规则查找普通行走与跳跃目标。
坐标使用整数网格，颜色使用 purple、blue、pink、white 之一。
"""

import math
from collections import deque

from camera import (
    create_island_model_view_matrix,
    project_point_to_screen,
)

from shapes import get_shape_stand_offset


# 当前关卡支持的颜色名称，renderer.py 会把它们映射成实际 RGB 颜色。
SUPPORTED_COLORS = ("purple", "blue", "pink", "white", "gold")
# 当前关卡支持的形状名称。
SUPPORTED_SHAPES = (
    "cube",
    "cylinder",
    "sphere",
    "cone",
    "arch",
    "stairs",
    "ramp",
    "ring",
    "platform",
    "bridge",
    "pyramid",
    "prism",
)
# 屏幕非欧连通的最大距离。
SCREEN_CONNECT_DISTANCE_PIXELS = 90.0
# 两个方向都超过这个值时视为屏幕斜对角，不连通。
SCREEN_DIAGONAL_COMPONENT_PIXELS = 20.0
# 点击选格阈值，约等于半个格子的屏幕宽度，方便手动调整。
BLOCK_CLICK_RADIUS_PIXELS = 40.0
# 屏幕四个方向的二维单位向量。
SCREEN_DIRECTION_VECTORS = {
    "up": (0.0, -1.0),
    "down": (0.0, 1.0),
    "left": (-1.0, 0.0),
    "right": (1.0, 0.0),
}


class Block:
    """这个类表示一个方块，并保存它在屏幕上的二维位置。"""

    def __init__(self, x, y, z, color, shape="cube", walkable=True):
        """输入：坐标、颜色、形状和是否可走。输出：无。功能：初始化形状数据和屏幕位置。"""
        # 形状在网格中的坐标。
        self.x = x
        self.y = y
        self.z = z
        # 形状颜色名称。
        self.color = color
        # 形状类型名称。
        self.shape = shape
        # 是否允许站人以及参与连通判断。
        self.walkable = walkable
        # 形状投影到屏幕后的中心位置，初始值会在加载后重新计算。
        self.screen_x = 0.0
        self.screen_y = 0.0


def get_block_stand_point(block):
    """输入：方块。输出：世界坐标中的可站立点。功能：按形状偏移得到可站立位置。"""
    offset_x, offset_y, offset_z = get_shape_stand_offset(block.shape)
    return (
        block.x + offset_x,
        block.y + offset_y,
        block.z + offset_z,
    )


def parse_block_line(line, line_number):
    """输入：一行文本和行号。输出：Block 对象。功能：解析新格式并兼容旧格式。"""
    # 按逗号切分，并去掉每一项两端的空白字符。
    parts = [part.strip() for part in line.split(",")]

    # 新格式为形状,x,y,z,颜色,是否可走，旧格式为 x,y,z,颜色。
    if len(parts) == 6:
        shape = parts[0].lower()
        coordinate_parts = parts[1:4]
        color = parts[4].lower()
        walkable_text = parts[5].lower()
        if shape not in SUPPORTED_SHAPES:
            raise ValueError(f"关卡第 {line_number} 行形状不支持：{shape}")
        if walkable_text not in ("0", "1"):
            raise ValueError(f"关卡第 {line_number} 行是否可走必须是 0 或 1")
        walkable = walkable_text == "1"
    elif len(parts) == 4:
        # 旧格式默认使用方块形状，并允许站人。
        shape = "cube"
        coordinate_parts = parts[0:3]
        color = parts[3].lower()
        walkable = True
    else:
        raise ValueError(
            f"关卡第 {line_number} 行格式错误：需要 形状,x,y,z,颜色,是否可走 或 x,y,z,颜色"
        )

    # 坐标必须是整数，否则说明关卡数据写错了。
    try:
        x = int(coordinate_parts[0])
        y = int(coordinate_parts[1])
        z = int(coordinate_parts[2])
    except ValueError as error:
        raise ValueError(f"关卡第 {line_number} 行坐标不是整数") from error

    # 颜色统一转成小写，避免大小写导致读取失败。
    if color not in SUPPORTED_COLORS:
        raise ValueError(f"关卡第 {line_number} 行颜色不支持：{color}")

    return Block(x, y, z, color, shape, walkable)


def load_level(path):
    """输入：关卡文件路径。输出：Block 列表。功能：逐行读取关卡数据。"""
    blocks = []

    # 使用 utf-8 读取，保证文件在不同系统上都能正常解析。
    with open(path, "r", encoding="utf-8") as level_file:
        # enumerate 从 1 开始，便于错误信息直接指出文件行号。
        for line_number, raw_line in enumerate(level_file, start=1):
            line = raw_line.strip()
            # 跳过空行和以 # 开头的说明行。
            if not line or line.startswith("#"):
                continue
            blocks.append(parse_block_line(line, line_number))

    # 关卡不能为空，否则主循环无法绘制任何内容。
    if not blocks:
        raise ValueError("关卡文件没有有效方块")

    return blocks


def find_block(blocks, x, y, z):
    """输入：方块列表和坐标。输出：对应方块。功能：按网格坐标查找方块。"""
    for block in blocks:
        if block.x == x and block.y == y and block.z == z:
            return block
    raise ValueError(f"找不到坐标 {x},{y},{z} 的方块")


def find_goal_block(blocks):
    """输入：方块列表。输出：终点方块或 None。功能：查找金色终点方块。"""
    for block in blocks:
        if block.color == "gold":
            return block
    return None


def get_block_screen_distance(first_block, second_block):
    """输入：两个方块。输出：屏幕像素距离。功能：计算两个方块中心的 2D 距离。"""
    difference_x = first_block.screen_x - second_block.screen_x
    difference_y = first_block.screen_y - second_block.screen_y
    # 勾股定理计算屏幕上的二维直线距离。
    return math.hypot(difference_x, difference_y)


def are_blocks_normal_adjacent(first_block, second_block):
    """输入：两个方块。输出：是否世界坐标边相邻。"""
    if not first_block.walkable or not second_block.walkable:
        return False
    difference_x = abs(second_block.x - first_block.x)
    difference_y = abs(second_block.y - first_block.y)
    difference_z = abs(second_block.z - first_block.z)

    # x 或 z 只差 1，另一个为 0，且高度相同或只差 1。
    horizontal_edge = (difference_x == 1 and difference_z == 0) or (
        difference_z == 1 and difference_x == 0
    )
    return horizontal_edge and difference_y <= 1


def are_blocks_screen_edge_adjacent(first_block, second_block):
    """输入：两个方块。输出：屏幕 2D 是否边相邻。功能：只接受水平或垂直对齐的屏幕边。"""
    if not first_block.walkable or not second_block.walkable:
        return False
    if first_block is second_block:
        return False

    difference_x = second_block.screen_x - first_block.screen_x
    difference_y = second_block.screen_y - first_block.screen_y
    absolute_x = abs(difference_x)
    absolute_y = abs(difference_y)

    distance = math.hypot(difference_x, difference_y)
    if distance > SCREEN_CONNECT_DISTANCE_PIXELS:
        return False
    # 两个屏幕方向都明显偏移时，视为斜对角，不连通。
    if absolute_x > SCREEN_DIAGONAL_COMPONENT_PIXELS and absolute_y > SCREEN_DIAGONAL_COMPONENT_PIXELS:
        return False
    return True


def are_blocks_connected(first_block, second_block):
    """输入：两个方块。输出：是否连通。功能：只根据可站立点的屏幕边相邻判断。"""
    return are_blocks_screen_edge_adjacent(first_block, second_block)


def build_connectivity_graph(blocks):
    """输入：全部方块。输出：邻接表。功能：只让可走形状参与屏幕连通判断。"""
    adjacency = {id(block): [] for block in blocks}
    walkable_blocks = [block for block in blocks if block.walkable]

    for first_index in range(len(walkable_blocks)):
        for second_index in range(first_index + 1, len(walkable_blocks)):
            first_block = walkable_blocks[first_index]
            second_block = walkable_blocks[second_index]
            if not are_blocks_connected(first_block, second_block):
                continue
            # 双向加入邻接表，保证搜索方向对称。
            adjacency[id(first_block)].append(second_block)
            adjacency[id(second_block)].append(first_block)

    return adjacency


def are_blocks_adjacent_on_screen(first_block, second_block):
    """输入：两个方块。输出：是否屏幕边相邻。功能：兼容旧调用名称。"""
    return are_blocks_screen_edge_adjacent(first_block, second_block)


def print_connectivity_debug(blocks):
    """输入：全部方块。输出：无。功能：打印每对格子的世界差、屏幕差和连通结果。"""
    print("连通判断调试开始")
    for first_index in range(len(blocks)):
        for second_index in range(first_index + 1, len(blocks)):
            first_block = blocks[first_index]
            second_block = blocks[second_index]
            world_difference = (
                second_block.x - first_block.x,
                second_block.y - first_block.y,
                second_block.z - first_block.z,
            )
            screen_difference = (
                second_block.screen_x - first_block.screen_x,
                second_block.screen_y - first_block.screen_y,
            )
            normal_connected = are_blocks_normal_adjacent(first_block, second_block)
            screen_connected = are_blocks_screen_edge_adjacent(first_block, second_block)
            connected = are_blocks_connected(first_block, second_block)
            print(
                f"A=({first_block.x},{first_block.y},{first_block.z}) "
                f"B=({second_block.x},{second_block.y},{second_block.z}) "
                f"世界差={world_difference} "
                f"屏幕差=({screen_difference[0]:.2f},{screen_difference[1]:.2f}) "
                f"正常={normal_connected} 非欧={screen_connected} 总连通={connected}"
            )
    print("连通判断调试结束")

    # 用同一套判断生成邻接表，供寻路和发光显示复用。
    adjacency = build_connectivity_graph(blocks)
    for block in blocks:
        neighbors = adjacency[id(block)]
        neighbor_text = ", ".join(
            f"({item.x},{item.y},{item.z})" for item in neighbors
        )
        print(f"邻接表：({block.x},{block.y},{block.z}) -> [{neighbor_text}]")
    print("邻接表调试结束")


def find_blocks_at_column(blocks, x, z):
    """输入：方块列表和水平坐标。输出：同一竖列上的方块列表。"""
    column_blocks = []
    for block in blocks:
        if block.x == x and block.z == z:
            column_blocks.append(block)
    return column_blocks


def is_block_standable(block, blocks):
    """输入：方块和全部方块。输出：是否可站。功能：检查可走标记和上方遮挡。"""
    if not block.walkable:
        return False
    for other_block in blocks:
        if (
            other_block.x == block.x
            and other_block.z == block.z
            and other_block.y == block.y + 1
        ):
            return False
    return True


def get_block_click_distance(block, screen_position):
    """输入：方块和鼠标屏幕坐标。输出：鼠标到方块顶面中心的 2D 距离。"""
    difference_x = block.screen_x - screen_position[0]
    difference_y = block.screen_y - screen_position[1]
    return math.hypot(difference_x, difference_y)


def find_clicked_block(blocks, screen_position):
    """输入：方块列表和鼠标屏幕坐标。输出：阈值内最近的站立方块或 None。"""
    nearest_block = None
    nearest_distance = BLOCK_CLICK_RADIUS_PIXELS

    for block in blocks:
        # 被上方方块压住的格子不能作为站立点。
        if not is_block_standable(block, blocks):
            continue
        distance = get_block_click_distance(block, screen_position)
        if distance < nearest_distance:
            nearest_distance = distance
            nearest_block = block

    return nearest_block


def can_step_between(first_block, second_block, blocks, adjacency):
    """输入：起点、目标、全部方块和当前连通表。输出：能否迈一步。"""
    if first_block is second_block:
        return False
    if not is_block_standable(second_block, blocks):
        return False
    if second_block not in adjacency.get(id(first_block), []):
        return False
    height_difference = second_block.y - first_block.y
    # 普通移动允许同高和低一格，高一格用于跳跃，高两格以上不通。
    return -1 <= height_difference <= 1


def get_reachable_blocks(start_block, blocks, adjacency):
    """输入：起点、全部方块和当前连通表。输出：可达方块列表。"""
    visited_ids = {id(start_block)}
    queue = deque([start_block])
    reachable_blocks = []

    while queue:
        current_block = queue.popleft()
        for block in adjacency.get(id(current_block), []):
            if id(block) in visited_ids:
                continue
            if not can_step_between(current_block, block, blocks, adjacency):
                continue
            visited_ids.add(id(block))
            reachable_blocks.append(block)
            queue.append(block)

    return reachable_blocks


def find_path(start_block, target_block, blocks, adjacency):
    """输入：起点、目标、全部方块和当前连通表。输出：最短路径列表。"""
    if start_block is target_block:
        return []
    if not is_block_standable(target_block, blocks):
        return []

    parents = {id(start_block): None}
    queue = deque([start_block])

    while queue:
        current_block = queue.popleft()
        for block in adjacency.get(id(current_block), []):
            if id(block) in parents:
                continue
            if not can_step_between(current_block, block, blocks, adjacency):
                continue
            parents[id(block)] = current_block
            if block is target_block:
                return build_path(parents, start_block, target_block)
            queue.append(block)

    return []


def build_path(parents, start_block, target_block):
    """输入：父节点表、起点和终点。输出：从起点到终点的方块路径。"""
    path = []
    current_block = target_block

    while current_block is not start_block:
        path.append(current_block)
        current_block = parents[id(current_block)]

    path.reverse()
    return path


def get_reachable_options(current_block, blocks, adjacency):
    """输入：当前方块、全部方块和当前连通表。输出：可走选项列表。"""
    options = []
    for block in adjacency.get(id(current_block), []):
        if block is current_block:
            continue
        if not is_block_standable(block, blocks):
            continue
        height_difference = block.y - current_block.y
        # 只允许同高、低一格或高一格，更高或更低都不能直接连通。
        if -1 <= height_difference <= 1:
            options.append(block)
    return options


def get_walk_options(options, current_block):
    """输入：可走选项和当前方块。输出：普通行走选项。功能：筛选同高或更低的选项。"""
    return [
        block
        for block in options
        if current_block.y - 1 <= block.y <= current_block.y
    ]


def get_jump_options(options, current_block):
    """输入：可走选项和当前方块。输出：跳跃选项。功能：筛选高一格的选项。"""
    return [block for block in options if block.y == current_block.y + 1]


def get_screen_alignment(first_block, second_block, direction_name):
    """输入：两个方块和屏幕方向。输出：方向一致度。功能：计算目标方位和按键方向的贴合程度。"""
    difference_x = second_block.screen_x - first_block.screen_x
    difference_y = second_block.screen_y - first_block.screen_y
    distance = math.hypot(difference_x, difference_y)
    if distance <= 0.0:
        return -1.0
    direction_x, direction_y = SCREEN_DIRECTION_VECTORS[direction_name]
    # 点积除以长度，得到 -1 到 1 的方向一致度。
    return (
        difference_x * direction_x + difference_y * direction_y
    ) / distance


def select_option_by_screen_direction(options, current_block, direction_name):
    """输入：选项列表、当前方块和屏幕方向。输出：最贴合该方向的目标或 None。"""
    best_block = None
    best_alignment = 0.0
    best_distance = 1e9

    for block in options:
        alignment = get_screen_alignment(current_block, block, direction_name)
        # 只接受在按键方向半平面内的选项，避免按上却往下走。
        if alignment <= 0.0:
            continue
        distance = get_block_screen_distance(current_block, block)
        if alignment > best_alignment + 1e-6:
            best_alignment = alignment
            best_distance = distance
            best_block = block
        elif abs(alignment - best_alignment) <= 1e-6 and distance < best_distance:
            best_distance = distance
            best_block = block

    return best_block


def find_walk_target(current_block, blocks, direction_vector):
    """输入：当前方块、全部方块和水平方向向量。输出：普通行走目标或 None。"""
    direction_x, direction_z = direction_vector
    target_x = current_block.x + direction_x
    target_z = current_block.z + direction_z
    column_blocks = find_blocks_at_column(blocks, target_x, target_z)
    if not column_blocks:
        return None

    # 只有正上方没有方块的格子才能作为落脚点。
    standable_blocks = [
        block for block in column_blocks if is_block_standable(block, blocks)
    ]
    if not standable_blocks:
        return None

    # 优先寻找与当前高度相同的方块。
    for block in standable_blocks:
        if block.y == current_block.y:
            if are_blocks_adjacent_on_screen(current_block, block):
                return block
            return None

    # 没有同高度方块时，只允许走向低一格的方块。
    lower_blocks = [
        block for block in standable_blocks if block.y == current_block.y - 1
    ]
    if not lower_blocks:
        return None
    target_block = max(lower_blocks, key=lambda block: block.y)
    if are_blocks_adjacent_on_screen(current_block, target_block):
        return target_block
    return None


def find_jump_target(current_block, blocks, direction_vector):
    """输入：当前方块、全部方块和前方水平向量。输出：跳跃目标或 None。"""
    direction_x, direction_z = direction_vector
    target_x = current_block.x + direction_x
    target_z = current_block.z + direction_z
    target_y = current_block.y + 1

    for block in blocks:
        if block.x == target_x and block.y == target_y and block.z == target_z:
            # 目标方块上方也必须是空的，否则跳跃会落到方块内部。
            if not is_block_standable(block, blocks):
                return None
            if are_blocks_adjacent_on_screen(current_block, block):
                return block
            return None
    return None


def update_block_screen_positions(blocks, projection_matrix, view_matrix, island_angle):
    """输入：方块列表、投影矩阵、视图矩阵和岛屿角度。输出：无。"""
    # 先把岛屿旋转合并进视图矩阵，避免为每个方块重复计算旋转。
    model_view_matrix = create_island_model_view_matrix(view_matrix, island_angle)

    for block in blocks:
        # 使用形状自己的可站立点，并投影到屏幕。
        screen_position = project_point_to_screen(
            get_block_stand_point(block),
            projection_matrix,
            model_view_matrix,
        )
        block.screen_x = screen_position[0]
        block.screen_y = screen_position[1]
