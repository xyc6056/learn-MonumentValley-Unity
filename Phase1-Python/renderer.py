"""这个文件负责使用 PyOpenGL 绘制场景。

它设置渲染状态，加载相机矩阵，并把关卡中的方块绘制成多个彩色立方体。
"""

import math

import time
import pygame

from level import get_block_stand_point
from shapes import (
    make_arch,
    make_bridge,
    make_cone,
    make_cube,
    make_cylinder,
    make_platform,
    make_ramp,
    make_ring,
    make_sphere,
    make_stairs,
)
from OpenGL.GL import (
    GL_FRAGMENT_SHADER,
    GL_BACK,
    GL_BLEND,
    GL_CCW,
    GL_COLOR_BUFFER_BIT,
    GL_CULL_FACE,
    GL_DEPTH_BUFFER_BIT,
    GL_DEPTH_TEST,
    GL_LINES,
    GL_MODELVIEW,
    GL_ONE_MINUS_SRC_ALPHA,
    GL_POINTS,
    GL_PROJECTION,
    GL_QUADS,
    GL_SRC_ALPHA,
    GL_TRIANGLES,
    GL_TEXTURE_2D,
    GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER,
    GL_RGBA,
    GL_UNSIGNED_BYTE,
    GL_VERTEX_SHADER,
    GL_LINEAR,
    glBegin,
    glBlendFunc,
    glBindTexture,
    glClear,
    glClearColor,
    glColor3f,
    glColor4f,
    glCullFace,
    glDisable,
    glEnable,
    glEnd,
    glFrontFace,
    glGetUniformLocation,
    glGenTextures,
    glLoadIdentity,
    glLoadMatrixf,
    glLineWidth,
    glMatrixMode,
    glNormal3f,
    glPointSize,
    glPopMatrix,
    glPushMatrix,
    glRotatef,
    glTexCoord2f,
    glTexImage2D,
    glTexParameteri,
    glTranslatef,
    glUniform1f,
    glUniform3f,
    glUseProgram,
    glVertex2f,
    glVertex3f,
)

from OpenGL.GL.shaders import compileProgram, compileShader


# 浅紫色背景，三个分量分别表示红、绿、蓝，取值范围都是 0.0 到 1.0。
BACKGROUND_COLOR = (0.86, 0.78, 0.95, 1.0)

# 方块名称到 RGB 颜色的映射，颜色分量范围都是 0.0 到 1.0。
BLOCK_COLORS = {
    "purple": (0.62, 0.38, 0.88),
    "blue": (0.34, 0.58, 0.96),
    "pink": (0.96, 0.54, 0.76),
    "white": (0.97, 0.97, 0.99),
    "gold": (1.0, 0.78, 0.22),
}

# 可走目标方块顶部高亮板的颜色。
REACHABLE_HIGHLIGHT_COLOR = (0.98, 0.72, 0.92)
# 鼠标悬停目标方块顶部高亮板的颜色。
HOVER_HIGHLIGHT_COLOR = (1.0, 0.35, 0.75)

# 形状名称到顶点生成函数的映射。
SHAPE_MAKERS = {
    "cube": make_cube,
    "cylinder": make_cylinder,
    "sphere": make_sphere,
    "cone": make_cone,
    "arch": make_arch,
    "stairs": make_stairs,
    "ramp": make_ramp,
    "ring": make_ring,
    "platform": make_platform,
    "bridge": make_bridge,
}

# 顶点着色器把顶点颜色、眼空间法线和位置传给片元着色器。
GRADIENT_VERTEX_SHADER = """
#version 120
varying vec3 vertex_normal;
varying vec4 vertex_color;
varying vec3 eye_position;
void main() {
    vec4 eye_vertex = gl_ModelViewMatrix * gl_Vertex;
    eye_position = eye_vertex.xyz;
    vertex_normal = normalize(gl_NormalMatrix * gl_Normal);
    vertex_color = gl_Color;
    gl_Position = gl_ProjectionMatrix * eye_vertex;
}
"""

# 片元着色器按法线做柔和光照，并在轮廓边缘叠加亮色微光。
GRADIENT_FRAGMENT_SHADER = """
#version 120
uniform vec3 glow_color;
uniform float glow_strength;
uniform vec3 fog_color;
uniform float fog_start;
uniform float fog_end;
varying vec3 vertex_normal;
varying vec4 vertex_color;
varying vec3 eye_position;
void main() {
    vec3 normal = normalize(vertex_normal);
    vec3 view_direction = normalize(-eye_position);
    vec3 key_direction = normalize(vec3(-0.48, 0.82, 0.42));
    vec3 fill_direction = normalize(vec3(0.58, 0.32, -0.50));
    vec3 key_color = vec3(1.00, 0.82, 0.58);
    vec3 fill_color = vec3(0.50, 0.66, 1.00);
    vec3 ambient_color = vec3(0.24, 0.22, 0.30);
    float key_amount = max(abs(dot(normal, key_direction)), 0.0);
    float fill_amount = max(abs(dot(normal, fill_direction)), 0.0);
    vec3 diffuse = ambient_color + key_color * key_amount * 0.82 + fill_color * fill_amount * 0.34;
    float edge = pow(clamp(1.0 - abs(dot(normal, view_direction)), 0.0, 1.0), 2.2);
    vec3 final_color = vertex_color.rgb * diffuse + glow_color * edge * glow_strength;
    float fog_amount = clamp((length(eye_position) - fog_start) / max(fog_end - fog_start, 0.001), 0.0, 1.0);
    final_color = mix(final_color, fog_color, fog_amount * 0.78);
    gl_FragColor = vec4(final_color, vertex_color.a);
}
"""

# 当前着色器程序和缓存，避免每帧重复编译或生成网格。
_gradient_program = None
_glow_color_location = -1
_glow_strength_location = -1
_fog_color_location = -1
_fog_start_location = -1
_fog_end_location = -1
_mesh_cache = {}


def _compile_gradient_shader():
    """输入：无。输出：无。功能：编译渐变和边缘微光着色器。"""
    global _gradient_program
    global _glow_color_location
    global _glow_strength_location
    global _fog_color_location
    global _fog_start_location
    global _fog_end_location

    vertex_shader = compileShader(GRADIENT_VERTEX_SHADER, GL_VERTEX_SHADER)
    fragment_shader = compileShader(GRADIENT_FRAGMENT_SHADER, GL_FRAGMENT_SHADER)
    _gradient_program = compileProgram(vertex_shader, fragment_shader)
    _glow_color_location = glGetUniformLocation(_gradient_program, "glow_color")
    _glow_strength_location = glGetUniformLocation(
        _gradient_program, "glow_strength"
    )
    _fog_color_location = glGetUniformLocation(_gradient_program, "fog_color")
    _fog_start_location = glGetUniformLocation(_gradient_program, "fog_start")
    _fog_end_location = glGetUniformLocation(_gradient_program, "fog_end")


def _enable_gradient_shader():
    """输入：无。输出：无。功能：启用渐变着色器。"""
    if _gradient_program is not None:
        glUseProgram(_gradient_program)


def _disable_gradient_shader():
    """输入：无。输出：无。功能：恢复固定管线。"""
    glUseProgram(0)


def _get_shape_mesh(shape, size):
    """输入：形状名和边长。输出：缩放后的顶点、法线和高度范围。"""
    cache_key = (shape, size)
    if cache_key in _mesh_cache:
        return _mesh_cache[cache_key]

    maker = SHAPE_MAKERS.get(shape, make_cube)
    vertices, normals = maker()
    scaled_vertices = [
        (point[0] * size, point[1] * size, point[2] * size)
        for point in vertices
    ]
    minimum_y = min(point[1] for point in scaled_vertices)
    maximum_y = max(point[1] for point in scaled_vertices)
    mesh = (scaled_vertices, normals, minimum_y, maximum_y)
    _mesh_cache[cache_key] = mesh
    return mesh


def _lighten_color(color, amount):
    """输入：基础颜色和亮度比例。输出：向白色靠近后的颜色。"""
    return (
        color[0] + (1.0 - color[0]) * amount,
        color[1] + (1.0 - color[1]) * amount,
        color[2] + (1.0 - color[2]) * amount,
    )


def _draw_gradient_shape(shape, size, color_name):
    """输入：形状、尺寸和颜色名。输出：无。功能：用渐变色和边缘微光绘制形状。"""
    vertices, normals, minimum_y, maximum_y = _get_shape_mesh(shape, size)
    base_color = get_block_color(color_name)
    bottom_color = shade_color(base_color, 0.52)
    top_color = _lighten_color(base_color, 0.42)
    glow_color = _lighten_color(base_color, 0.68)
    height_range = max(maximum_y - minimum_y, 1e-6)
    glUniform3f(_glow_color_location, glow_color[0], glow_color[1], glow_color[2])
    glUniform1f(_glow_strength_location, 0.72)
    glUniform3f(_fog_color_location, 0.93, 0.78, 0.95)
    glUniform1f(_fog_start_location, 4.0)
    glUniform1f(_fog_end_location, 11.0)
    glBegin(GL_TRIANGLES)
    for point, normal in zip(vertices, normals):
        gradient = (point[1] - minimum_y) / height_range
        red = bottom_color[0] + (top_color[0] - bottom_color[0]) * gradient
        green = bottom_color[1] + (top_color[1] - bottom_color[1]) * gradient
        blue = bottom_color[2] + (top_color[2] - bottom_color[2]) * gradient
        glColor3f(red, green, blue)
        glNormal3f(normal[0], normal[1], normal[2])
        glVertex3f(point[0], point[1], point[2])
    glEnd()


def initialize_renderer():
    """输入：无。输出：无。功能：设置背景色、深度测试和背面剔除。"""
    _compile_gradient_shader()
    # 设置每一帧清屏时使用的浅紫色背景。
    glClearColor(*BACKGROUND_COLOR)
    # 开启深度测试，保证离相机更近的面遮挡更远的面。
    glEnable(GL_DEPTH_TEST)
    # 开启背面剔除，减少不可见面的绘制，并避免实体内部面干扰画面。
    glDisable(GL_CULL_FACE)
    # 剔除背向相机的面。
    # 形状顶点绕序不完全一致，因此保持双面绘制。
    # 顶点按逆时针排列时视为正面，正好匹配立方体六个面的顶点顺序。
    glFrontFace(GL_CCW)


def begin_frame(projection_matrix, view_matrix, view_angle=0.0):
    """输入：投影矩阵、视图矩阵和视角。输出：无。功能：清屏并加载相机矩阵。"""
    # 同时清除颜色缓冲和深度缓冲，保证这一帧从干净画面开始。
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    draw_gradient_background(view_angle)

    # 切换到投影矩阵，并加载 camera.py 计算好的正交投影范围。
    glMatrixMode(GL_PROJECTION)
    glLoadMatrixf(tuple(projection_matrix))

    # 切换到模型视图矩阵，并加载相机的位置与朝向。
    glMatrixMode(GL_MODELVIEW)
    glLoadMatrixf(tuple(view_matrix))
    _enable_gradient_shader()


def draw_gradient_background(view_angle=0.0):
    """输入：视角角度。输出：无。功能：绘制浅紫到浅粉的渐变天空。"""
    _disable_gradient_shader()
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    view_shift = math.sin(math.radians(view_angle)) * 0.035
    top_left = (
        max(0.0, min(1.0, 0.88 + view_shift)),
        0.74,
        1.00,
    )
    top_right = (
        max(0.0, min(1.0, 0.91 - view_shift)),
        0.76,
        1.00,
    )
    bottom_left = (
        1.00,
        max(0.0, min(1.0, 0.78 + view_shift)),
        max(0.0, min(1.0, 0.90 - view_shift)),
    )
    bottom_right = (
        1.00,
        max(0.0, min(1.0, 0.80 - view_shift)),
        max(0.0, min(1.0, 0.92 + view_shift)),
    )

    glBegin(GL_QUADS)
    # 四个角使用略有差异的浅紫和浅粉，形成随视角微移的天空。
    glColor3f(*top_left)
    glVertex2f(-1.0, 1.0)
    glColor3f(*top_right)
    glVertex2f(1.0, 1.0)
    glColor3f(*bottom_right)
    glVertex2f(1.0, -1.0)
    glColor3f(*bottom_left)
    glVertex2f(-1.0, -1.0)
    glEnd()

    glEnable(GL_DEPTH_TEST)


def create_cube_faces(size):
    """输入：立方体边长。输出：六个面的顶点和亮度列表。功能：构造立方体六个面。"""
    half = size / 2.0

    # 每个面由四个顶点组成，顶点按从外侧观察时的逆时针顺序排列。
    # 不同面使用略有差异的亮度，让立体结构更容易辨认。
    faces = [
        (((-half, -half, half), (half, -half, half), (half, half, half), (-half, half, half)), 1.00),
        (((half, -half, -half), (-half, -half, -half), (-half, half, -half), (half, half, -half)), 0.82),
        (((-half, -half, -half), (-half, -half, half), (-half, half, half), (-half, half, -half)), 0.90),
        (((half, -half, half), (half, -half, -half), (half, half, -half), (half, half, half)), 0.96),
        (((-half, half, half), (half, half, half), (half, half, -half), (-half, half, -half)), 1.00),
        (((-half, -half, -half), (half, -half, -half), (half, -half, half), (-half, -half, half)), 0.86),
    ]
    return faces


def draw_face(vertices, brightness, base_color):
    """输入：四个顶点、面亮度和基础颜色。输出：无。功能：绘制一个带明暗的四边形面。"""
    # 根据当前面的亮度计算实际 RGB，再提交给 OpenGL。
    color = shade_color(base_color, brightness)
    glColor3f(color[0], color[1], color[2])

    glBegin(GL_QUADS)
    for vertex in vertices:
        # 逐个提交四边形顶点，交给 PyOpenGL 绘制。
        glVertex3f(vertex[0], vertex[1], vertex[2])
    glEnd()


def draw_completion_effect(goal_block, progress):
    """输入：终点方块和动画进度。输出：无。功能：绘制金色淡出板和上升粒子。"""
    if progress >= 1.0:
        return

    _disable_gradient_shader()
    # 粒子需要透明混合，并暂时关闭深度测试保证发光不被遮挡。
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # 用淡入淡出的全屏光晕强化过关瞬间。
    fade_alpha = math.sin(math.pi * progress) * 0.45
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glColor4f(1.0, 0.92, 0.70, fade_alpha)
    glBegin(GL_QUADS)
    glVertex2f(-1.0, -1.0)
    glVertex2f(1.0, -1.0)
    glVertex2f(1.0, 1.0)
    glVertex2f(-1.0, 1.0)
    glEnd()
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    fade = 1.0 - progress
    half_size = 0.45 + progress * 0.45
    plate_x, plate_y, plate_z = get_block_stand_point(goal_block)
    plate_y += 0.02
    glColor4f(1.0, 0.80, 0.20, fade * 0.75)
    glBegin(GL_QUADS)
    glVertex3f(plate_x - half_size, plate_y, plate_z - half_size)
    glVertex3f(plate_x + half_size, plate_y, plate_z - half_size)
    glVertex3f(plate_x + half_size, plate_y, plate_z + half_size)
    glVertex3f(plate_x - half_size, plate_y, plate_z + half_size)
    glEnd()

    # 用固定数量和固定角度生成粒子，避免每帧随机导致闪烁。
    glPointSize(6.0)
    glBegin(GL_POINTS)
    for index in range(36):
        angle = index * math.pi * 2.0 / 36.0 + progress * 3.0
        radius = 0.2 + progress * 1.4
        particle_x = plate_x + math.cos(angle) * radius
        particle_z = plate_z + math.sin(angle) * radius
        particle_y = (
            plate_y + 0.08 + progress * 1.2 + math.sin(angle * 3.0) * 0.15
        )
        glColor4f(1.0, 0.85, 0.25, fade)
        glVertex3f(particle_x, particle_y, particle_z)
    glEnd()

    glPointSize(1.0)
    glDisable(GL_BLEND)
    _enable_gradient_shader()


def draw_water_for_blocks(blocks, size=12.0):
    """输入：关卡方块。输出：无。功能：按关卡范围在岛屿下方绘制水面。"""
    if not blocks:
        return
    stand_points = [get_block_stand_point(block) for block in blocks]
    minimum_x = min(point[0] for point in stand_points)
    maximum_x = max(point[0] for point in stand_points)
    minimum_y = min(point[1] for point in stand_points)
    minimum_z = min(point[2] for point in stand_points)
    maximum_z = max(point[2] for point in stand_points)
    center_x = (minimum_x + maximum_x) * 0.5
    center_z = (minimum_z + maximum_z) * 0.5
    span_x = maximum_x - minimum_x
    span_z = maximum_z - minimum_z
    water_size = max(span_x, span_z) + 8.0
    draw_water(center_x, minimum_y - 1.0, center_z, water_size)


def draw_fireflies_for_blocks(blocks):
    """输入：关卡方块。输出：无。功能：按关卡范围铺开萤火虫粒子。"""
    if not blocks:
        return
    stand_points = [get_block_stand_point(block) for block in blocks]
    minimum_x = min(point[0] for point in stand_points)
    maximum_x = max(point[0] for point in stand_points)
    minimum_y = min(point[1] for point in stand_points)
    maximum_y = max(point[1] for point in stand_points)
    minimum_z = min(point[2] for point in stand_points)
    maximum_z = max(point[2] for point in stand_points)
    center_x = (minimum_x + maximum_x) * 0.5
    center_y = (minimum_y + maximum_y) * 0.5 + 1.0
    center_z = (minimum_z + maximum_z) * 0.5
    range_x = max(5.0, (maximum_x - minimum_x) * 0.65 + 2.0)
    range_y = max(3.0, maximum_y - minimum_y + 2.0)
    range_z = max(4.0, (maximum_z - minimum_z) * 0.65 + 2.0)
    draw_fireflies(
        center_x=center_x,
        center_y=center_y,
        center_z=center_z,
        range_x=range_x,
        range_y=range_y,
        range_z=range_z,
    )


def draw_fireflies(
    center_x=0.0,
    center_y=0.0,
    center_z=0.0,
    count=48,
    range_x=5.0,
    range_y=3.0,
    range_z=4.0,
    time_seconds=None,
):
    """输入：粒子范围和数量。输出：无。功能：绘制缓慢移动闪烁的萤火虫。"""
    _disable_gradient_shader()
    glDisable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    now = time.perf_counter() if time_seconds is None else time_seconds

    def particle_position(index):
        """输入：粒子编号。输出：位置和闪烁强度。功能：生成稳定的漂浮轨迹。"""
        phase = index * 2.399963
        spread = 0.35 + ((index * 37) % 100) / 100.0 * 0.65
        x = center_x + math.sin(now * 0.23 + phase) * range_x * spread
        y = (
            center_y
            + ((index * 53) % 100) / 100.0 * range_y
            + math.sin(now * 0.41 + phase * 1.7) * 0.22
        )
        z = center_z + math.cos(now * 0.19 + phase * 1.3) * range_z * spread
        flicker = 0.5 + 0.5 * math.sin(now * 1.65 + phase * 3.1)
        return x, y, z, flicker

    glPointSize(10.0)
    glBegin(GL_POINTS)
    for index in range(count):
        x, y, z, flicker = particle_position(index)
        glColor4f(1.0, 0.83, 0.42, 0.10 * flicker)
        glVertex3f(x, y, z)
    glEnd()

    glPointSize(3.0)
    glBegin(GL_POINTS)
    for index in range(count):
        x, y, z, flicker = particle_position(index)
        glColor4f(1.0, 0.92, 0.58, 0.35 + 0.55 * flicker)
        glVertex3f(x, y, z)
    glEnd()

    glPointSize(1.0)
    glDisable(GL_BLEND)
    glEnable(GL_DEPTH_TEST)
    _enable_gradient_shader()

def draw_water(center_x, base_y, center_z, size=10.0, resolution=24):
    """输入：水面中心、尺寸和网格密度。输出：无。功能：绘制轻微波动的半透明水面。"""
    _disable_gradient_shader()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glColor4f(0.40, 0.62, 0.96, 0.30)
    now = time.perf_counter()
    half_size = size * 0.5
    cell_size = size / resolution

    for x_index in range(resolution):
        x0 = center_x - half_size + x_index * cell_size
        x1 = x0 + cell_size
        for z_index in range(resolution):
            z0 = center_z - half_size + z_index * cell_size
            z1 = z0 + cell_size

            def wave(x, z):
                """输入：水面横纵坐标。输出：波高。功能：组合两组正弦波。"""
                return (
                    math.sin(x * 0.75 + now * 1.15) * 0.035
                    + math.cos(z * 0.90 - now * 0.85) * 0.025
                )

            glBegin(GL_QUADS)
            glVertex3f(x0, base_y + wave(x0, z0), z0)
            glVertex3f(x1, base_y + wave(x1, z0), z0)
            glVertex3f(x1, base_y + wave(x1, z1), z1)
            glVertex3f(x0, base_y + wave(x0, z1), z1)
            glEnd()

    glDisable(GL_BLEND)
    _enable_gradient_shader()
    glEnable(GL_DEPTH_TEST)


def draw_cube(size, color_name):
    """输入：立方体边长和颜色名称。输出：无。功能：在当前模型视图矩阵下绘制立方体。"""
    base_color = get_block_color(color_name)
    faces = create_cube_faces(size)
    for vertices, brightness in faces:
        draw_face(vertices, brightness, base_color)


def get_block_color(color_name):
    """输入：颜色名称。输出：RGB 三元组。功能：把关卡颜色名称转换成 OpenGL 颜色。"""
    if color_name not in BLOCK_COLORS:
        raise ValueError(f"未知方块颜色：{color_name}")
    return BLOCK_COLORS[color_name]


def shade_color(base_color, brightness):
    """输入：基础 RGB 和面亮度。输出：明暗处理后的 RGB。功能：计算一个面的实际颜色。"""
    # 三个颜色通道同时乘以亮度，保持原来的色相不变。
    return (
        base_color[0] * brightness,
        base_color[1] * brightness,
        base_color[2] * brightness,
    )


def draw_block(x, y, z, size, color_name, shape="cube"):
    """输入：坐标、尺寸、颜色和形状。输出：无。功能：绘制渐变微光形状。"""
    # 保存当前模型视图矩阵，避免平移影响后续方块。
    glPushMatrix()
    # 把方块中心平移到网格位置。
    glTranslatef(x, y, z)
    _draw_gradient_shape(shape, size, color_name)
    # 恢复矩阵，使下一个方块从原始视角重新开始。
    glPopMatrix()


def begin_island_transform(island_angle):
    """输入：岛屿角度。输出：无。功能：开始对整个岛应用垂直轴旋转。"""
    # 保存当前模型视图矩阵，让岛屿旋转不会破坏相机矩阵。
    glPushMatrix()
    # 绕 y 轴旋转，使关卡和小人围绕同一个垂直轴转动。
    glRotatef(island_angle, 0.0, 1.0, 0.0)


def end_island_transform():
    """输入：无。输出：无。功能：结束岛屿旋转并恢复相机矩阵。"""
    # 恢复矩阵，避免下一帧重复叠加岛屿旋转。
    glPopMatrix()


def draw_level(blocks, size):
    """输入：Block 列表和方块边长。输出：无。功能：绘制关卡中的全部方块。"""
    for block in blocks:
        draw_block(block.x, block.y, block.z, size, block.color, block.shape)


def draw_connectivity_edges(blocks, adjacency):
    """输入：方块列表和邻接表。输出：无。功能：绘制微弱发光的连通线。"""
    _disable_gradient_shader()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glLineWidth(2.0)
    glColor4f(0.75, 0.55, 1.0, 0.30)
    glBegin(GL_LINES)

    for block in blocks:
        for neighbor in adjacency.get(id(block), []):
            # 只绘制一次无向边，避免重复叠加变亮。
            if id(block) < id(neighbor):
                continue
            block_x, block_y, block_z = get_block_stand_point(block)
            neighbor_x, neighbor_y, neighbor_z = get_block_stand_point(neighbor)
            glVertex3f(block_x, block_y + 0.02, block_z)
            glVertex3f(neighbor_x, neighbor_y + 0.02, neighbor_z)

    glEnd()
    glLineWidth(1.0)
    glDisable(GL_BLEND)
    _enable_gradient_shader()


def draw_shadows(blocks):
    """输入：方块列表。输出：无。功能：在岛屿下方绘制半透明简单阴影。"""
    if not blocks:
        return

    _disable_gradient_shader()
    stand_points = {
        id(block): get_block_stand_point(block) for block in blocks
    }
    ground_y = min(point[1] for point in stand_points.values()) - 0.98
    shadow_sizes = {
        "cube": 0.48,
        "cylinder": 0.44,
        "sphere": 0.38,
        "cone": 0.42,
        "arch": 0.48,
        "stairs": 0.48,
        "ramp": 0.48,
        "ring": 0.34,
        "platform": 0.42,
        "bridge": 0.28,
    }

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    for block in blocks:
        block_stand = stand_points[id(block)]
        shadow_y = ground_y
        for other in blocks:
            if other is block:
                continue
            if other.x != block.x or other.z != block.z:
                continue
            other_stand = stand_points[id(other)]
            if other_stand[1] < block_stand[1]:
                shadow_y = max(shadow_y, other_stand[1] + 0.015)

        offset_x = block.x + 0.18
        offset_z = block.z - 0.18
        half_size = shadow_sizes.get(block.shape, 0.45)
        for layer_index, scale in enumerate((1.16, 1.00, 0.84)):
            layer_y = shadow_y + layer_index * 0.003
            glColor4f(0.16, 0.12, 0.28, 0.07 + layer_index * 0.035)
            glBegin(GL_QUADS)
            glVertex3f(offset_x - half_size * scale, layer_y, offset_z - half_size * scale)
            glVertex3f(offset_x + half_size * scale, layer_y, offset_z - half_size * scale)
            glVertex3f(offset_x + half_size * scale, layer_y, offset_z + half_size * scale)
            glVertex3f(offset_x - half_size * scale, layer_y, offset_z + half_size * scale)
            glEnd()

    glDisable(GL_BLEND)
    _enable_gradient_shader()


def draw_highlight(block, color):
    """输入：方块和高亮颜色。输出：无。功能：在方块顶面绘制一块高亮板。"""
    _disable_gradient_shader()
    half_size = 0.39
    # 高亮板贴在形状自己的可站立点上，避免和顶面发生深度冲突。
    top_x, top_y, top_z = get_block_stand_point(block)
    top_y += 0.005
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_QUADS)
    # 顶点按从上方观察的逆时针顺序排列，法线朝向正上方。
    glVertex3f(top_x - half_size, top_y, top_z - half_size)
    glVertex3f(top_x + half_size, top_y, top_z - half_size)
    glVertex3f(top_x + half_size, top_y, top_z + half_size)
    glVertex3f(top_x - half_size, top_y, top_z + half_size)
    glEnd()
    _enable_gradient_shader()


def draw_highlights(blocks, color):
    """输入：方块列表和高亮颜色。输出：无。功能：绘制所有指定方块的高亮。"""
    for block in blocks:
        draw_highlight(block, color)


def draw_direction_arrow(x, y, z, direction_x, direction_z):
    """输入：位置和朝向向量。输出：无。功能：在头顶绘制一个亮色三角箭头。"""
    direction_length = math.hypot(direction_x, direction_z)
    if direction_length <= 0.0:
        return
    _disable_gradient_shader()
    # 把朝向归一化，保证箭头大小不受向量长度影响。
    normalized_x = direction_x / direction_length
    normalized_z = direction_z / direction_length
    # 水平垂直向量用于生成三角形箭头的两个底角。
    perpendicular_x = -normalized_z
    perpendicular_z = normalized_x

    tip_x = x + normalized_x * 0.16
    tip_z = z + normalized_z * 0.16
    left_x = x - normalized_x * 0.05 + perpendicular_x * 0.09
    left_z = z - normalized_z * 0.05 + perpendicular_z * 0.09
    right_x = x - normalized_x * 0.05 - perpendicular_x * 0.09
    right_z = z - normalized_z * 0.05 - perpendicular_z * 0.09

    glColor3f(0.35, 1.0, 0.85)
    glBegin(GL_TRIANGLES)
    glVertex3f(tip_x, y, tip_z)
    glVertex3f(left_x, y, left_z)
    glVertex3f(right_x, y, right_z)
    glEnd()
    _enable_gradient_shader()


def draw_ui_rect(center_x, center_y, half_width, half_height, color, alpha=1.0):
    """输入：中心、半宽高、颜色和透明度。输出：无。功能：绘制屏幕空间矩形。"""
    _disable_gradient_shader()
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
    _enable_gradient_shader()
