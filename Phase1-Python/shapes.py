"""这个文件负责生成纯几何形状的三角形顶点和顶点法线。

每个 make_* 函数都返回 (vertices, normals)：
vertices 是顶点列表，每三个连续元素组成一个三角形。
normals 与 vertices 等长，每个顶点对应一个已经归一化的法线。
所有形状都围绕局部原点生成，方便后续按关卡坐标直接平移。
"""

import math


# 各形状相对网格中心的局部可站立点。
# 除楼梯和斜坡外，其余形状通常取高度方向的顶面中心。
SHAPE_STAND_OFFSETS = {
    "cube": (0.0, 0.5, 0.0),
    "cylinder": (0.0, 0.5, 0.0),
    "sphere": (0.0, 0.5, 0.0),
    "cone": (0.0, 0.5, 0.0),
    "pyramid": (0.0, 0.5, 0.0),
    "prism": (0.0, 0.5, 0.0),
    "arch": (0.0, 0.275, 0.0),
    "stairs": (0.4, 0.5, 0.0),
    "ramp": (0.0, 0.0, 0.0),
    "ring": (0.0, 0.12, 0.0),
    "platform": (0.0, 0.06, 0.0),
    "bridge": (0.0, -0.02, 0.0),
}
# 未登记形状回退到单位立方体的顶面中心。
DEFAULT_SHAPE_STAND_OFFSET = (0.0, 0.5, 0.0)


def get_shape_stand_offset(shape):
    """输入：形状名称。输出：局部可站立点偏移。功能：为关卡连通和角色落点提供统一定义。"""
    return SHAPE_STAND_OFFSETS.get(shape, DEFAULT_SHAPE_STAND_OFFSET)


def _normalize(vector):
    """输入：三维向量。输出：单位向量。功能：避免法线长度影响光照。"""
    length = math.sqrt(
        vector[0] * vector[0]
        + vector[1] * vector[1]
        + vector[2] * vector[2]
    )
    if length <= 1e-12:
        raise ValueError("无法归一化零向量")
    return (
        vector[0] / length,
        vector[1] / length,
        vector[2] / length,
    )


def _subtract(first, second):
    """输入：两个三维点。输出：first 减 second。功能：计算边向量。"""
    return (
        first[0] - second[0],
        first[1] - second[1],
        first[2] - second[2],
    )


def _cross(first, second):
    """输入：两个三维向量。输出：叉积。功能：由两条边计算面法线。"""
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _face_normal(first, second, third):
    """输入：三角形三个顶点。输出：单位面法线。功能：按逆时针绕序计算朝向。"""
    edge_a = _subtract(second, first)
    edge_b = _subtract(third, first)
    return _normalize(_cross(edge_a, edge_b))


def _append_triangle(vertices, normals, first, second, third, normal=None):
    """输入：网格数组和三角形三点。输出：无。功能：追加一个平面三角形。"""
    if normal is None:
        normal = _face_normal(first, second, third)
    for point in (first, second, third):
        vertices.append(point)
        normals.append(normal)


def _append_quad(vertices, normals, first, second, third, fourth, normal=None):
    """输入：网格数组和四边形四点。输出：无。功能：拆成两个平面三角形。"""
    if normal is None:
        normal = _face_normal(first, second, third)
    _append_triangle(vertices, normals, first, second, third, normal)
    _append_triangle(vertices, normals, first, third, fourth, normal)


def _append_triangle_smooth(
    vertices,
    normals,
    first,
    first_normal,
    second,
    second_normal,
    third,
    third_normal,
):
    """输入：三点和各自法线。输出：无。功能：追加一个光滑三角形。"""
    for point, normal in (
        (first, first_normal),
        (second, second_normal),
        (third, third_normal),
    ):
        vertices.append(point)
        normals.append(_normalize(normal))


def _append_quad_smooth(
    vertices,
    normals,
    first,
    first_normal,
    second,
    second_normal,
    third,
    third_normal,
    fourth,
    fourth_normal,
):
    """输入：四点及各自法线。输出：无。功能：拆成两个光滑三角形。"""
    _append_triangle_smooth(
        vertices,
        normals,
        first,
        first_normal,
        second,
        second_normal,
        third,
        third_normal,
    )
    _append_triangle_smooth(
        vertices,
        normals,
        first,
        first_normal,
        third,
        third_normal,
        fourth,
        fourth_normal,
    )


def _append_box(vertices, normals, center, size):
    """输入：中心点和三轴尺寸。输出：无。功能：追加一个轴对齐立方体。"""
    center_x, center_y, center_z = center
    size_x, size_y, size_z = size
    half_x = size_x * 0.5
    half_y = size_y * 0.5
    half_z = size_z * 0.5

    # 八个角点按 xyz 方向编号，000 表示三个轴都取负方向。
    point_000 = (center_x - half_x, center_y - half_y, center_z - half_z)
    point_100 = (center_x + half_x, center_y - half_y, center_z - half_z)
    point_110 = (center_x + half_x, center_y + half_y, center_z - half_z)
    point_010 = (center_x - half_x, center_y + half_y, center_z - half_z)
    point_001 = (center_x - half_x, center_y - half_y, center_z + half_z)
    point_101 = (center_x + half_x, center_y - half_y, center_z + half_z)
    point_111 = (center_x + half_x, center_y + half_y, center_z + half_z)
    point_011 = (center_x - half_x, center_y + half_y, center_z + half_z)

    # 每个面都按从外部观察时的逆时针方向写入。
    _append_quad(vertices, normals, point_001, point_101, point_111, point_011)
    _append_quad(vertices, normals, point_100, point_000, point_010, point_110)
    _append_quad(vertices, normals, point_000, point_001, point_011, point_010)
    _append_quad(vertices, normals, point_101, point_100, point_110, point_111)
    _append_quad(vertices, normals, point_011, point_111, point_110, point_010)
    _append_quad(vertices, normals, point_000, point_100, point_101, point_001)


def _require_positive(value, name):
    """输入：数值和参数名。输出：数值。功能：拒绝零或负尺寸。"""
    if value <= 0.0:
        raise ValueError(f"{name} 必须大于零")
    return value


def _require_segments(value, name, minimum=3):
    """输入：分段数和参数名。输出：分段数。功能：保证曲面不会退化。"""
    if value < minimum:
        raise ValueError(f"{name} 不能小于 {minimum}")
    return value


def make_cube(size=1.0):
    """参数：size 为立方体边长，几何中心位于原点。"""
    # 六个面各由两个三角形组成，顶点按外侧逆时针顺序环绕。
    _require_positive(size, "size")
    vertices = []
    normals = []
    _append_box(vertices, normals, (0.0, 0.0, 0.0), (size, size, size))
    return vertices, normals


def make_cylinder(radius=0.45, height=1.0, segments=24):
    """参数：radius 为半径，height 为高度，segments 为圆周分段数。"""
    # 侧面按圆周分成四边形，每个顶点法线沿半径水平向外。
    # 顶面和底面使用独立三角形，法线固定朝上或朝下。
    _require_positive(radius, "radius")
    _require_positive(height, "height")
    _require_segments(segments, "segments")
    vertices = []
    normals = []
    half_height = height * 0.5
    top_center = (0.0, half_height, 0.0)
    bottom_center = (0.0, -half_height, 0.0)

    for index in range(segments):
        angle_a = math.tau * index / segments
        angle_b = math.tau * (index + 1) / segments
        normal_a = (math.cos(angle_a), 0.0, math.sin(angle_a))
        normal_b = (math.cos(angle_b), 0.0, math.sin(angle_b))
        bottom_a = (
            radius * normal_a[0],
            -half_height,
            radius * normal_a[2],
        )
        bottom_b = (
            radius * normal_b[0],
            -half_height,
            radius * normal_b[2],
        )
        top_a = (
            radius * normal_a[0],
            half_height,
            radius * normal_a[2],
        )
        top_b = (
            radius * normal_b[0],
            half_height,
            radius * normal_b[2],
        )

        _append_quad_smooth(
            vertices,
            normals,
            bottom_a,
            normal_a,
            bottom_b,
            normal_b,
            top_b,
            normal_b,
            top_a,
            normal_a,
        )
        _append_triangle(
            vertices,
            normals,
            top_a,
            top_center,
            top_b,
            (0.0, 1.0, 0.0),
        )
        _append_triangle(
            vertices,
            normals,
            bottom_a,
            bottom_b,
            bottom_center,
            (0.0, -1.0, 0.0),
        )

    return vertices, normals


def make_sphere(radius=0.5, segments=24, rings=12):
    """参数：radius 为半径，segments 为经度分段，rings 为纬度分段。"""
    # 球面点 = (r*cos longitude*sin latitude, r*cos latitude, r*sin longitude*sin latitude)。
    # 法线等于从球心指向顶点的单位向量，因此球面光照连续。
    _require_positive(radius, "radius")
    _require_segments(segments, "segments")
    _require_segments(rings, "rings", 2)
    vertices = []
    normals = []

    for ring_index in range(rings):
        latitude_a = math.pi * ring_index / rings
        latitude_b = math.pi * (ring_index + 1) / rings

        for segment_index in range(segments):
            longitude_a = math.tau * segment_index / segments
            longitude_b = math.tau * (segment_index + 1) / segments

            def sphere_point(latitude, longitude):
                """输入：纬度和经度。输出：球面点。功能：复用经纬度公式。"""
                sin_latitude = math.sin(latitude)
                return (
                    radius * math.cos(longitude) * sin_latitude,
                    radius * math.cos(latitude),
                    radius * math.sin(longitude) * sin_latitude,
                )

            first = sphere_point(latitude_a, longitude_a)
            second = sphere_point(latitude_a, longitude_b)
            third = sphere_point(latitude_b, longitude_b)
            fourth = sphere_point(latitude_b, longitude_a)
            first_normal = _normalize(first)
            second_normal = _normalize(second)
            third_normal = _normalize(third)
            fourth_normal = _normalize(fourth)

            if ring_index == 0:
                _append_triangle_smooth(
                    vertices,
                    normals,
                    first,
                    first_normal,
                    third,
                    third_normal,
                    fourth,
                    fourth_normal,
                )
            elif ring_index == rings - 1:
                _append_triangle_smooth(
                    vertices,
                    normals,
                    first,
                    first_normal,
                    second,
                    second_normal,
                    fourth,
                    fourth_normal,
                )
            else:
                _append_quad_smooth(
                    vertices,
                    normals,
                    first,
                    first_normal,
                    second,
                    second_normal,
                    third,
                    third_normal,
                    fourth,
                    fourth_normal,
                )

    return vertices, normals


def make_cone(radius=0.5, height=1.0, segments=24):
    """参数：radius 为底面半径，height 为高度，segments 为圆周分段数。"""
    # 侧面从底面圆环连接到顶部尖点，每个小面使用自己的面法线。
    # 底面使用扇形三角形，法线固定朝下。
    _require_positive(radius, "radius")
    _require_positive(height, "height")
    _require_segments(segments, "segments")
    vertices = []
    normals = []
    half_height = height * 0.5
    apex = (0.0, half_height, 0.0)
    bottom_center = (0.0, -half_height, 0.0)

    for index in range(segments):
        angle_a = math.tau * index / segments
        angle_b = math.tau * (index + 1) / segments
        bottom_a = (
            radius * math.cos(angle_a),
            -half_height,
            radius * math.sin(angle_a),
        )
        bottom_b = (
            radius * math.cos(angle_b),
            -half_height,
            radius * math.sin(angle_b),
        )

        _append_triangle(vertices, normals, bottom_a, apex, bottom_b)
        _append_triangle(
            vertices,
            normals,
            bottom_a,
            bottom_b,
            bottom_center,
            (0.0, -1.0, 0.0),
        )

    return vertices, normals


def make_arch(
    outer_radius=0.55,
    inner_radius=0.34,
    depth=0.45,
    segments=18,
):
    """参数：outer_radius 为外半径，inner_radius 为内半径，depth 为厚度。"""
    # 拱门由 xy 平面上的半圆环沿 z 轴拉伸而成。
    # 外弧、内弧、前后端面和两个底部切面分别生成四边形。
    _require_positive(outer_radius, "outer_radius")
    _require_positive(inner_radius, "inner_radius")
    _require_positive(depth, "depth")
    _require_segments(segments, "segments", 2)
    if inner_radius >= outer_radius:
        raise ValueError("inner_radius 必须小于 outer_radius")

    vertices = []
    normals = []
    half_depth = depth * 0.5
    center_offset_y = -outer_radius * 0.5

    for index in range(segments):
        angle_a = math.pi * index / segments
        angle_b = math.pi * (index + 1) / segments
        cosine_a = math.cos(angle_a)
        sine_a = math.sin(angle_a)
        cosine_b = math.cos(angle_b)
        sine_b = math.sin(angle_b)

        inner_front_a = (
            inner_radius * cosine_a,
            inner_radius * sine_a + center_offset_y,
            half_depth,
        )
        inner_front_b = (
            inner_radius * cosine_b,
            inner_radius * sine_b + center_offset_y,
            half_depth,
        )
        outer_front_a = (
            outer_radius * cosine_a,
            outer_radius * sine_a + center_offset_y,
            half_depth,
        )
        outer_front_b = (
            outer_radius * cosine_b,
            outer_radius * sine_b + center_offset_y,
            half_depth,
        )
        inner_back_a = (
            inner_radius * cosine_a,
            inner_radius * sine_a + center_offset_y,
            -half_depth,
        )
        inner_back_b = (
            inner_radius * cosine_b,
            inner_radius * sine_b + center_offset_y,
            -half_depth,
        )
        outer_back_a = (
            outer_radius * cosine_a,
            outer_radius * sine_a + center_offset_y,
            -half_depth,
        )
        outer_back_b = (
            outer_radius * cosine_b,
            outer_radius * sine_b + center_offset_y,
            -half_depth,
        )

        _append_quad(
            vertices,
            normals,
            inner_front_a,
            outer_front_a,
            outer_front_b,
            inner_front_b,
            (0.0, 0.0, 1.0),
        )
        _append_quad(
            vertices,
            normals,
            outer_back_a,
            inner_back_a,
            inner_back_b,
            outer_back_b,
            (0.0, 0.0, -1.0),
        )
        _append_quad(
            vertices,
            normals,
            outer_front_a,
            outer_back_a,
            outer_back_b,
            outer_front_b,
            (cosine_a, sine_a, 0.0),
        )
        _append_quad(
            vertices,
            normals,
            inner_back_a,
            inner_front_a,
            inner_front_b,
            inner_back_b,
            (-cosine_a, -sine_a, 0.0),
        )

    outer_front_start = (outer_radius, center_offset_y, half_depth)
    inner_front_start = (inner_radius, center_offset_y, half_depth)
    outer_back_start = (outer_radius, center_offset_y, -half_depth)
    inner_back_start = (inner_radius, center_offset_y, -half_depth)
    outer_front_end = (-outer_radius, center_offset_y, half_depth)
    inner_front_end = (-inner_radius, center_offset_y, half_depth)
    outer_back_end = (-outer_radius, center_offset_y, -half_depth)
    inner_back_end = (-inner_radius, center_offset_y, -half_depth)

    _append_quad(
        vertices,
        normals,
        outer_front_start,
        inner_front_start,
        inner_back_start,
        outer_back_start,
        (0.0, -1.0, 0.0),
    )
    _append_quad(
        vertices,
        normals,
        inner_front_end,
        outer_front_end,
        outer_back_end,
        inner_back_end,
        (0.0, -1.0, 0.0),
    )

    return vertices, normals


def make_stairs(
    step_count=5,
    run=1.0,
    width=0.75,
    height=1.0,
):
    """参数：step_count 为台阶数，run 为总进深，width 为宽度，height 为总高。"""
    # 每一级台阶都是一个从底部延伸到该级顶面的长方体。
    # 台阶沿 x 方向排列，宽度沿 z 方向，高度沿 y 方向。
    _require_segments(step_count, "step_count", 2)
    _require_positive(run, "run")
    _require_positive(width, "width")
    _require_positive(height, "height")
    vertices = []
    normals = []
    step_depth = run / step_count
    step_height = height / step_count

    for index in range(step_count):
        step_top = -height * 0.5 + step_height * (index + 1)
        step_bottom = -height * 0.5
        center_x = -run * 0.5 + step_depth * (index + 0.5)
        center_y = (step_top + step_bottom) * 0.5
        _append_box(
            vertices,
            normals,
            (center_x, center_y, 0.0),
            (step_depth, step_top - step_bottom, width),
        )

    return vertices, normals


def make_ramp(length=1.0, width=0.75, height=0.6):
    """参数：length 为斜面长度，width 为宽度，height 为高低两端差。"""
    # 斜坡是沿 z 轴拉伸的直角三角形棱柱。
    # 左端高度为零，右端高度为 height，斜面从低端连接到高端。
    _require_positive(length, "length")
    _require_positive(width, "width")
    _require_positive(height, "height")
    vertices = []
    normals = []
    half_length = length * 0.5
    half_width = width * 0.5
    half_height = height * 0.5

    bottom_front_left = (-half_length, -half_height, half_width)
    bottom_front_right = (half_length, -half_height, half_width)
    top_front_right = (half_length, half_height, half_width)
    bottom_back_left = (-half_length, -half_height, -half_width)
    bottom_back_right = (half_length, -half_height, -half_width)
    top_back_right = (half_length, half_height, -half_width)

    _append_triangle(
        vertices,
        normals,
        bottom_back_left,
        top_back_right,
        bottom_back_right,
        (0.0, 0.0, -1.0),
    )
    _append_triangle(
        vertices,
        normals,
        bottom_front_left,
        bottom_front_right,
        top_front_right,
        (0.0, 0.0, 1.0),
    )
    _append_quad(
        vertices,
        normals,
        bottom_front_left,
        bottom_back_left,
        bottom_back_right,
        bottom_front_right,
        (0.0, -1.0, 0.0),
    )
    _append_quad(
        vertices,
        normals,
        bottom_front_right,
        bottom_back_right,
        top_back_right,
        top_front_right,
        _normalize((-height, length, 0.0)),
    )
    _append_quad(
        vertices,
        normals,
        bottom_back_right,
        bottom_front_right,
        top_front_right,
        top_back_right,
        (1.0, 0.0, 0.0),
    )

    return vertices, normals


def make_ring(major_radius=0.38, tube_radius=0.12, major_segments=28, tube_segments=12):
    """参数：major_radius 为环半径，tube_radius 为管半径，二者决定圆环尺寸。"""
    # 圆环参数方程把主圆放在 xz 平面，管截面绕主圆旋转。
    # 顶点法线等于从管中心指向表面点的单位向量，保证圆周方向平滑。
    _require_positive(major_radius, "major_radius")
    _require_positive(tube_radius, "tube_radius")
    _require_segments(major_segments, "major_segments")
    _require_segments(tube_segments, "tube_segments")
    vertices = []
    normals = []

    for major_index in range(major_segments):
        major_a = math.tau * major_index / major_segments
        major_b = math.tau * (major_index + 1) / major_segments
        cosine_major_a = math.cos(major_a)
        sine_major_a = math.sin(major_a)
        cosine_major_b = math.cos(major_b)
        sine_major_b = math.sin(major_b)

        for tube_index in range(tube_segments):
            tube_a = math.tau * tube_index / tube_segments
            tube_b = math.tau * (tube_index + 1) / tube_segments
            cosine_tube_a = math.cos(tube_a)
            sine_tube_a = math.sin(tube_a)
            cosine_tube_b = math.cos(tube_b)
            sine_tube_b = math.sin(tube_b)

            def ring_point(major_cosine, major_sine, tube_cosine, tube_sine):
                """输入：主圆和管截面的三角函数值。输出：圆环点。"""
                radial = major_radius + tube_radius * tube_cosine
                return (
                    radial * major_cosine,
                    tube_radius * tube_sine,
                    radial * major_sine,
                )

            first = ring_point(
                cosine_major_a,
                sine_major_a,
                cosine_tube_a,
                sine_tube_a,
            )
            second = ring_point(
                cosine_major_a,
                sine_major_a,
                cosine_tube_b,
                sine_tube_b,
            )
            third = ring_point(
                cosine_major_b,
                sine_major_b,
                cosine_tube_b,
                sine_tube_b,
            )
            fourth = ring_point(
                cosine_major_b,
                sine_major_b,
                cosine_tube_a,
                sine_tube_a,
            )
            first_normal = (
                cosine_tube_a * cosine_major_a,
                sine_tube_a,
                cosine_tube_a * sine_major_a,
            )
            second_normal = (
                cosine_tube_b * cosine_major_a,
                sine_tube_b,
                cosine_tube_b * sine_major_a,
            )
            third_normal = (
                cosine_tube_b * cosine_major_b,
                sine_tube_b,
                cosine_tube_b * sine_major_b,
            )
            fourth_normal = (
                cosine_tube_a * cosine_major_b,
                sine_tube_a,
                cosine_tube_a * sine_major_b,
            )

            _append_quad_smooth(
                vertices,
                normals,
                first,
                first_normal,
                fourth,
                fourth_normal,
                third,
                third_normal,
                second,
                second_normal,
            )

    return vertices, normals


def make_platform(length=1.1, width=0.8, thickness=0.12):
    """参数：length 为 x 方向长度，width 为 z 方向宽度，thickness 为板厚。"""
    # 浮空平台就是一个尺寸较薄的轴对齐长方体。
    _require_positive(length, "length")
    _require_positive(width, "width")
    _require_positive(thickness, "thickness")
    vertices = []
    normals = []
    _append_box(
        vertices,
        normals,
        (0.0, 0.0, 0.0),
        (length, thickness, width),
    )
    return vertices, normals


def make_bridge(
    length=1.35,
    width=0.5,
    thickness=0.1,
    rail_height=0.14,
    rail_width=0.08,
):
    """参数：length 为桥长，width 为桥宽，thickness 为桥面厚度，rail_* 为栏杆尺寸。"""
    # 桥由一块薄桥面和两条沿 x 方向延伸的细长栏杆组成。
    # 栏杆位于 z 方向两侧，整座桥的几何中心仍对齐原点。
    _require_positive(length, "length")
    _require_positive(width, "width")
    _require_positive(thickness, "thickness")
    _require_positive(rail_height, "rail_height")
    _require_positive(rail_width, "rail_width")
    if rail_width * 2.0 >= width:
        raise ValueError("rail_width 过大，栏杆会互相重叠")

    vertices = []
    normals = []
    total_height = thickness + rail_height
    bottom_y = -total_height * 0.5
    deck_center_y = bottom_y + thickness * 0.5
    deck_top_y = bottom_y + thickness
    rail_center_y = (deck_top_y + total_height * 0.5) * 0.5
    rail_center_z = width * 0.5 - rail_width * 0.5

    _append_box(
        vertices,
        normals,
        (0.0, deck_center_y, 0.0),
        (length, thickness, width),
    )
    _append_box(
        vertices,
        normals,
        (0.0, rail_center_y, rail_center_z),
        (length, rail_height, rail_width),
    )
    _append_box(
        vertices,
        normals,
        (0.0, rail_center_y, -rail_center_z),
        (length, rail_height, rail_width),
    )

    return vertices, normals


def _draw_mesh(vertices, normals):
    """输入：顶点和法线列表。输出：无。功能：把三角形网格提交给 OpenGL。"""
    from OpenGL.GL import GL_TRIANGLES, glBegin, glEnd, glNormal3f, glVertex3f

    glBegin(GL_TRIANGLES)
    for point, normal in zip(vertices, normals):
        glNormal3f(normal[0], normal[1], normal[2])
        glVertex3f(point[0], point[1], point[2])
    glEnd()


def run_shape_test():
    """输入：无。输出：无。功能：打开窗口并排绘制十种形状。"""
    import pygame
    from OpenGL.GL import (
        GL_AMBIENT,
        GL_AMBIENT_AND_DIFFUSE,
        GL_COLOR_MATERIAL,
        GL_COLOR_BUFFER_BIT,
        GL_DEPTH_TEST,
        GL_DEPTH_BUFFER_BIT,
        GL_DIFFUSE,
        GL_FRONT_AND_BACK,
        GL_LIGHT0,
        GL_LIGHTING,
        GL_MODELVIEW,
        GL_NORMALIZE,
        GL_POSITION,
        GL_PROJECTION,
        glClear,
        glClearColor,
        glColor3f,
        glColorMaterial,
        glEnable,
        glLightfv,
        glLoadIdentity,
        glMatrixMode,
        glOrtho,
        glPopMatrix,
        glPushMatrix,
        glRotatef,
        glTranslatef,
        glViewport,
    )

    width = 1400
    height = 480
    pygame.init()
    pygame.display.set_mode(
        (width, height),
        pygame.OPENGL | pygame.DOUBLEBUF,
    )
    pygame.display.set_caption("形状测试：十种几何体")
    glViewport(0, 0, width, height)
    glClearColor(0.10, 0.12, 0.22, 1.0)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_NORMALIZE)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glLightfv(GL_LIGHT0, GL_POSITION, (5.0, 9.0, 7.0, 1.0))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.96, 0.90, 1.0))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.32, 0.30, 0.42, 1.0))

    shape_makers = (
        make_cube,
        make_cylinder,
        make_sphere,
        make_cone,
        make_arch,
        make_stairs,
        make_ramp,
        make_ring,
        make_platform,
        make_bridge,
    )
    colors = (
        (0.92, 0.42, 0.70),
        (0.38, 0.66, 0.98),
        (0.70, 0.48, 0.95),
        (0.98, 0.68, 0.38),
        (0.46, 0.84, 0.78),
        (0.94, 0.50, 0.58),
        (0.52, 0.76, 0.96),
        (0.82, 0.58, 0.98),
        (0.98, 0.78, 0.50),
        (0.58, 0.88, 0.62),
    )
    meshes = [maker() for maker in shape_makers]
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-7.2, 7.2, -2.4, 2.4, -20.0, 20.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glRotatef(22.0, 1.0, 0.0, 0.0)
        glRotatef(-28.0, 0.0, 1.0, 0.0)

        for index, (vertices, normals) in enumerate(meshes):
            glPushMatrix()
            glTranslatef((index - 4.5) * 1.38, 0.0, 0.0)
            glColor3f(colors[index][0], colors[index][1], colors[index][2])
            _draw_mesh(vertices, normals)
            glPopMatrix()

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def run_gradient_shape_test():
    """输入：无。输出：无。功能：用着色器显示多种颜色的渐变微光形状。"""
    import pygame
    import camera
    import renderer
    from OpenGL.GL import (
        GL_MODELVIEW,
        GL_PROJECTION,
        glLoadIdentity,
        glMatrixMode,
        glOrtho,
        glRotatef,
        glViewport,
    )

    width = 1400
    height = 480
    pygame.init()
    pygame.display.set_mode(
        (width, height),
        pygame.OPENGL | pygame.DOUBLEBUF,
    )
    pygame.display.set_caption("渐变与边缘微光测试")
    glViewport(0, 0, width, height)
    renderer.initialize_renderer()
    projection_matrix = camera.create_projection_matrix()
    view_matrix = camera.create_view_matrix()
    shape_names = (
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
    )
    color_names = (
        "purple",
        "blue",
        "pink",
        "white",
        "gold",
    )
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        renderer.begin_frame(projection_matrix, view_matrix)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(-7.2, 7.2, -2.4, 2.4, -20.0, 20.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glRotatef(22.0, 1.0, 0.0, 0.0)
        glRotatef(-28.0, 0.0, 1.0, 0.0)

        for index, shape_name in enumerate(shape_names):
            color_name = color_names[index % len(color_names)]
            renderer.draw_block(
                (index - 4.5) * 1.38,
                0.0,
                0.0,
                1.0,
                color_name,
                shape_name,
            )

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    run_gradient_shape_test()
