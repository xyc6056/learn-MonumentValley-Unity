"""这个文件是一个不打开窗口、不初始化 OpenGL 的小人移动测试脚本。

它会伪造 renderer 模块，避免 player.py 导入 PyOpenGL。
然后构造一个平面测试关卡，模拟按下 W、A、S、D，
并打印小人移动前后的世界坐标。
"""

import sys
import types


# 让 Windows 终端按 utf-8 输出中文，避免中文变成乱码。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


# 在导入 player.py 前伪造 renderer 模块，避免初始化 OpenGL。
fake_renderer = types.ModuleType("renderer")
fake_renderer.draw_block = lambda *args, **kwargs: None
fake_renderer.draw_direction_arrow = lambda *args, **kwargs: None
sys.modules["renderer"] = fake_renderer

import level
from player import Player


# 按键名称到小人方向名称的映射。
KEY_DIRECTIONS = {
    "W": "forward",
    "A": "left",
    "S": "backward",
    "D": "right",
}


class FakeKeyState:
    """这个类表示一个假的按键状态。"""

    def __init__(self, pressed_key):
        """输入：按键名称。输出：无。功能：保存当前按下的键。"""
        self.pressed_key = pressed_key


def create_test_blocks():
    """输入：无。输出：方块列表。功能：创建一个简单的十字形平面测试关卡。"""
    # 每个元组依次是 x、y、z 和手动设置的屏幕 x、屏幕 y。
    block_data = [
        (0, 0, 0, 400.0, 300.0),
        (1, 0, 0, 480.0, 300.0),
        (-1, 0, 0, 320.0, 300.0),
        (0, 0, 1, 400.0, 220.0),
        (0, 0, -1, 400.0, 380.0),
    ]

    blocks = []
    for x, y, z, screen_x, screen_y in block_data:
        block = level.Block(x, y, z, "white")
        block.screen_x = screen_x
        block.screen_y = screen_y
        blocks.append(block)
    return blocks


def create_player(blocks):
    """输入：方块列表。输出：Player 对象。功能：把小人放到中心方块上。"""
    start_block = next(block for block in blocks if block.x == 0 and block.y == 0 and block.z == 0)
    return Player(start_block)


def format_position(player):
    """输入：小人。输出：坐标字符串。功能：格式化小人的世界坐标。"""
    return (
        f"({player.world_x:.2f}, {player.world_y:.2f}, {player.world_z:.2f})"
    )


def find_candidate_block(blocks, x, y, z):
    """输入：方块列表和目标坐标。输出：方块或 None。功能：按坐标查找候选目标格。"""
    for block in blocks:
        if block.x == x and block.y == y and block.z == z:
            return block
    return None


def move_with_key(player, blocks, key_state):
    """输入：小人、方块和假按键状态。输出：无。功能：模拟一次按键移动并打印结果。"""
    key_name = key_state.pressed_key
    direction_name = KEY_DIRECTIONS[key_name]

    # 根据小人当前朝向计算按键对应的水平方向。
    direction_x, direction_z = player.get_direction_vector(direction_name)
    target_x = player.current_block.x + direction_x
    target_y = player.current_block.y
    target_z = player.current_block.z + direction_z

    # 查找规则允许的移动目标。
    target_block = level.find_walk_target(
        player.current_block,
        blocks,
        (direction_x, direction_z),
    )

    # 单独计算目标格是否存在以及二维屏幕是否连通，便于失败时打印细节。
    candidate_block = find_candidate_block(blocks, target_x, target_y, target_z)
    connected = (
        candidate_block is not None
        and level.are_blocks_adjacent_on_screen(
            player.current_block,
            candidate_block,
        )
    )

    before_position = format_position(player)

    # 有合法目标时开始移动，并把动画更新到结束。
    if target_block is not None:
        player.start_move_to(target_block)
        player.update(1.0)

    after_position = format_position(player)

    print(f"按键 {key_name}：")
    print(f"  移动前：{before_position}")
    print(f"  移动后：{after_position}")

    # 位置完全没变化时输出失败原因所需的诊断信息。
    if before_position == after_position:
        print("移动失败")
        print(f"  目标格坐标：({target_x}, {target_y}, {target_z})")
        print(f"  是否连通：{connected}")


def main():
    """输入：无。输出：无。功能：依次模拟 W、A、S、D 四种按键。"""
    for key_name in ("W", "A", "S", "D"):
        blocks = create_test_blocks()
        player = create_player(blocks)
        key_state = FakeKeyState(key_name)
        move_with_key(player, blocks, key_state)
        print()


if __name__ == "__main__":
    main()
