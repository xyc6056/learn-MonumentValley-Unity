"""这个文件负责小人的站立、朝向、移动动画和几何体绘制。

小人由几个纯色立方体组成，不加载任何图片或模型。
移动方向由外部按摄像机屏幕方向计算，玩家朝向只负责转身表现。
"""

import math

from level import get_block_stand_point
from renderer import draw_block, draw_direction_arrow


# 普通移动一格需要的时间，单位为秒。
MOVE_DURATION_SECONDS = 0.2
# 小人转向需要的时间，单位为秒。
TURN_DURATION_SECONDS = 0.15
# 跳跃动画持续时间，单位为秒。
JUMP_DURATION_SECONDS = 0.4
# 跳跃时向上增加的弧线高度。
JUMP_HEIGHT = 0.55
# 起跳前下蹲的深度。
CROUCH_DEPTH = 0.12
# 到达终点后庆祝时向上弹跳的高度。
CELEBRATION_BOB_HEIGHT = 0.12
# 普通行走时轻微向上的弧度。
WALK_BOB_HEIGHT = 0.05
# 站立时轻微上下浮动的幅度。
IDLE_BOB_HEIGHT = 0.02
# 不能移动时上下轻微抖动的幅度。
BLOCKED_FEEDBACK_HEIGHT = 0.06
# 不能移动反馈的持续时间。
BLOCKED_FEEDBACK_DURATION = 0.16


class Player:
    """这个类保存小人位置、朝向、目标方块和动画状态。"""

    def __init__(self, start_block):
        """输入：起点方块。输出：无。功能：创建站在起点方块上的小人。"""
        # 记录小人当前所在方块和目标方块。
        self.current_block = start_block
        self.target_block = start_block
        # 是否正在移动。
        self.moving = False
        # 待执行的路径队列，每一项是一个目标方块。
        self.path_queue = []
        # 动画类型，取值为 walk 或 jump。
        self.animation_type = "walk"
        # 本帧是否刚开始新的一步，用于播放音效。
        self.step_started = False
        # 是否正在播放到达终点的庆祝动画。
        self.celebrating = False
        # 庆祝动画的累计时间。
        self.celebration_elapsed = 0.0

        # 世界坐标表示小人脚底的位置，直接使用形状自己的可站立点。
        self.world_x, self.world_y, self.world_z = get_block_stand_point(start_block)

        # 朝向使用世界坐标中的水平方向向量，初始朝向 x 轴正方向。
        self.facing_x = 1.0
        self.facing_z = 0.0

        # 记录移动起点、终点和动画进度。
        self.start_x = self.world_x
        self.start_y = self.world_y
        self.start_z = self.world_z
        self.target_x = self.world_x
        self.target_y = self.world_y
        self.target_z = self.world_z
        self.move_elapsed = 0.0
        self.move_duration = MOVE_DURATION_SECONDS

        # 记录转身动画状态。
        self.turn_elapsed = 0.0
        self.turn_duration = 0.0
        self.turn_start_angle = 0.0
        self.turn_angle_difference = 0.0

        # 站立浮动计时和不能移动反馈计时。
        self.idle_time = 0.0
        self.blocked_feedback_elapsed = 0.0

    def get_direction_vector(self, direction_name):
        """输入：方向名称。输出：小人的水平方向。功能：保留给测试脚本使用的朝向方向查询。"""
        # 朝向经过格子移动后始终是整数单位方向，这里转成整数更稳定。
        forward_x = int(round(self.facing_x))
        forward_z = int(round(self.facing_z))

        if direction_name == "forward":
            return forward_x, forward_z
        if direction_name == "backward":
            return -forward_x, -forward_z
        if direction_name == "left":
            return forward_z, -forward_x
        if direction_name == "right":
            return -forward_z, forward_x
        raise ValueError(f"未知方向名称：{direction_name}")

    def start_move_to(self, target_block):
        """输入：目标方块。输出：无。功能：开始普通格子移动。"""
        # 已经在移动时忽略新的移动请求。
        if self.moving:
            return
        # 目标方块就是当前方块时不需要移动。
        if target_block is self.current_block:
            return

        self._begin_animation(target_block, "walk")
        # 普通移动时长按格子距离计算，一格约为 0.2 秒。
        step_distance = max(
            abs(target_block.x - self.current_block.x),
            abs(target_block.y - self.current_block.y),
            abs(target_block.z - self.current_block.z),
            1,
        )
        self.move_duration = MOVE_DURATION_SECONDS * step_distance

    def start_jump_to(self, target_block):
        """输入：目标方块。输出：无。功能：开始带下蹲和弧线的跳跃。"""
        # 已经在移动时忽略新的跳跃请求。
        if self.moving:
            return
        if target_block is self.current_block:
            return

        self._begin_animation(target_block, "jump")
        self.move_duration = JUMP_DURATION_SECONDS


    def follow_path(self, path_blocks):
        """输入：方块路径列表。输出：无。功能：把路径加入队列并开始逐格移动。"""
        if self.moving:
            return
        self.path_queue = list(path_blocks)
        self._start_next_path_step()


    def _start_next_path_step(self):
        """输入：无。输出：无。功能：从路径队列取出下一格并选择行走或跳跃。"""
        if not self.path_queue:
            return
        next_block = self.path_queue.pop(0)
        if next_block.y == self.current_block.y + 1:
            self.start_jump_to(next_block)
        else:
            self.start_move_to(next_block)

    def _begin_animation(self, target_block, animation_type):
        """输入：目标方块和动画类型。输出：无。功能：初始化一次移动和转身动画。"""
        self.target_block = target_block
        self.animation_type = animation_type
        self.start_x = self.world_x
        self.start_y = self.world_y
        self.start_z = self.world_z
        self.target_x, self.target_y, self.target_z = get_block_stand_point(target_block)
        self.move_elapsed = 0.0
        self.moving = True
        self.step_started = True
        self.blocked_feedback_elapsed = 0.0

        # 根据目标方块相对当前位置的水平方向计算目标朝向。
        direction_x = self.target_x - self.start_x
        direction_z = self.target_z - self.start_z
        direction_length = math.hypot(direction_x, direction_z)
        if direction_length <= 0.0:
            self.turn_duration = 0.0
            return

        target_facing_x = direction_x / direction_length
        target_facing_z = direction_z / direction_length
        start_angle = math.atan2(self.facing_z, self.facing_x)
        target_angle = math.atan2(target_facing_z, target_facing_x)

        # 计算最短转向角，避免 350 度这种绕远路的问题。
        angle_difference = (target_angle - start_angle + math.pi) % (math.pi * 2.0) - math.pi
        self.turn_start_angle = start_angle
        self.turn_angle_difference = angle_difference
        self.turn_elapsed = 0.0

        # 方向几乎相同时不需要转身动画。
        if abs(angle_difference) <= 0.001:
            self.turn_duration = 0.0
            self.facing_x = target_facing_x
            self.facing_z = target_facing_z
        else:
            self.turn_duration = TURN_DURATION_SECONDS

    def play_blocked_feedback(self):
        """输入：无。输出：无。功能：播放轻微的不能移动反馈。"""
        # 正在移动时不播放反馈，避免和移动动画叠加。
        if self.moving:
            return
        self.blocked_feedback_elapsed = BLOCKED_FEEDBACK_DURATION


    def start_celebration(self):
        """输入：无。输出：无。功能：在终点开始庆祝动画。"""
        self.path_queue = []
        self.moving = False
        self.celebrating = True
        self.celebration_elapsed = 0.0

    def update(self, delta_time):
        """输入：帧间隔时间。输出：无。功能：推进站立浮动、反馈、转身和移动动画。"""
        # 站立浮动计时始终累加，静止和移动时都能使用。
        self.idle_time += delta_time
        # 庆祝动画独立计时，保证到达终点后持续播放。
        if self.celebrating:
            self.celebration_elapsed += delta_time
        # 不能移动反馈逐帧衰减。
        if self.blocked_feedback_elapsed > 0.0:
            self.blocked_feedback_elapsed = max(
                0.0,
                self.blocked_feedback_elapsed - delta_time,
            )

        if not self.moving:
            return

        # 先完成转身，再开始格子移动。
        if self.turn_elapsed < self.turn_duration:
            turn_finished = self._update_turn_animation(delta_time)
            if not turn_finished:
                return

        # 累加位移动画时间，并把总进度限制在 0 到 1。
        self.move_elapsed += delta_time
        progress = min(self.move_elapsed / self.move_duration, 1.0)

        if self.animation_type == "jump":
            self._update_jump_animation(progress)
        else:
            self._update_walk_animation(progress)

        # 动画结束后精确落到目标方块顶面。
        if progress >= 1.0:
            self.world_x = self.target_x
            self.world_y = self.target_y
            self.world_z = self.target_z
            self.current_block = self.target_block
            self.moving = False
            # 当前这一格结束后，如果还有路径就继续下一格。
            if self.path_queue:
                self._start_next_path_step()

    def _update_turn_animation(self, delta_time):
        """输入：帧间隔时间。输出：转身是否完成。功能：插值更新小人朝向。"""
        self.turn_elapsed += delta_time
        progress = min(self.turn_elapsed / self.turn_duration, 1.0)
        # 使用平滑曲线让转向更自然。
        smooth_progress = progress * progress * (3.0 - 2.0 * progress)
        current_angle = (
            self.turn_start_angle
            + self.turn_angle_difference * smooth_progress
        )
        self.facing_x = math.cos(current_angle)
        self.facing_z = math.sin(current_angle)
        return progress >= 1.0

    def _update_walk_animation(self, progress):
        """输入：动画进度。输出：无。功能：更新普通行走位置。"""
        # 用平滑曲线让起步和停止更自然。
        smooth_progress = progress * progress * (3.0 - 2.0 * progress)
        self.world_x = self.start_x + (self.target_x - self.start_x) * smooth_progress
        self.world_y = self.start_y + (self.target_y - self.start_y) * smooth_progress
        self.world_z = self.start_z + (self.target_z - self.start_z) * smooth_progress

        # 普通移动加入很小的正弦弧线。
        self.world_y += math.sin(math.pi * progress) * WALK_BOB_HEIGHT

    def _update_jump_animation(self, progress):
        """输入：动画进度。输出：无。功能：更新下蹲、跃起和落地位置。"""
        crouch_end = 0.25

        if progress < crouch_end:
            # 前四分之一时间原地下蹲。
            crouch_progress = progress / crouch_end
            self.world_x = self.start_x
            self.world_y = self.start_y - math.sin(crouch_progress * math.pi * 0.5) * CROUCH_DEPTH
            self.world_z = self.start_z
            return

        # 剩余时间完成水平位移，并叠加抛物线跳跃高度。
        flight_progress = (progress - crouch_end) / (1.0 - crouch_end)
        self.world_x = self.start_x + (self.target_x - self.start_x) * flight_progress
        self.world_y = self.start_y + (self.target_y - self.start_y) * flight_progress
        self.world_z = self.start_z + (self.target_z - self.start_z) * flight_progress
        self.world_y += math.sin(math.pi * flight_progress) * JUMP_HEIGHT

    def draw(self):
        """输入：无。输出：无。功能：用多个小立方体绘制小人。"""
        # 静止时加入轻微上下浮动。
        idle_offset = 0.0
        if not self.moving:
            idle_offset = math.sin(self.idle_time * 3.0) * IDLE_BOB_HEIGHT

        # 到达终点后连续弹跳，和场景粒子一起形成庆祝动画。
        celebration_offset = 0.0
        if self.celebrating:
            celebration_offset = (
                abs(math.sin(self.celebration_elapsed * math.pi * 4.0))
                * CELEBRATION_BOB_HEIGHT
            )

        # 不能移动时上下轻微抖动。
        blocked_offset = 0.0
        if self.blocked_feedback_elapsed > 0.0:
            feedback_progress = 1.0 - (
                self.blocked_feedback_elapsed / BLOCKED_FEEDBACK_DURATION
            )
            blocked_offset = math.sin(feedback_progress * math.pi * 2.0) * BLOCKED_FEEDBACK_HEIGHT

        feet_y = (
            self.world_y
            + idle_offset
            + blocked_offset
            + celebration_offset
        )

        # 两条腿。
        draw_block(self.world_x - 0.07, feet_y + 0.06, self.world_z, 0.12, "blue")
        draw_block(self.world_x + 0.07, feet_y + 0.06, self.world_z, 0.12, "blue")
        # 身体。
        draw_block(self.world_x, feet_y + 0.28, self.world_z, 0.28, "purple")
        # 两条手臂。
        draw_block(self.world_x - 0.19, feet_y + 0.30, self.world_z, 0.10, "pink")
        draw_block(self.world_x + 0.19, feet_y + 0.30, self.world_z, 0.10, "pink")
        # 头部。
        draw_block(self.world_x, feet_y + 0.55, self.world_z, 0.20, "white")

        # 在头部朝向的一侧放一个小方块，作为小人面朝方向的标记。
        face_x = self.world_x + self.facing_x * 0.11
        face_z = self.world_z + self.facing_z * 0.11
        draw_block(face_x, feet_y + 0.55, face_z, 0.08, "purple")
        # 在头顶绘制亮色箭头，让小人朝向一眼可见。
        draw_direction_arrow(
            self.world_x,
            feet_y + 0.72,
            self.world_z,
            self.facing_x,
            self.facing_z,
        )
