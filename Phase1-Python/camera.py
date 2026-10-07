"""这个文件负责等距相机的投影矩阵和视图矩阵。

相机保持固定：水平方向绕 y 轴旋转 45 度，俯视角度约 30 度。
所有矩阵都使用 OpenGL 的列主序格式，共 16 个浮点数。
"""

import math


# 窗口宽度，单位为像素。
WINDOW_WIDTH = 800
# 窗口高度，单位为像素。
WINDOW_HEIGHT = 600

# 正交投影可见区域的一半高度，数值越大，看到的范围越广。
ORTHO_HALF_HEIGHT = 3.0
# 正交投影可见区域的一半宽度，根据窗口宽高比计算，避免画面被拉伸。
ORTHO_HALF_WIDTH = ORTHO_HALF_HEIGHT * (WINDOW_WIDTH / WINDOW_HEIGHT)
# 正交投影的近裁剪面。
ORTHO_NEAR = -20.0
# 正交投影的远裁剪面。
ORTHO_FAR = 20.0

# 相机俯视角度，单位为度。
CAMERA_PITCH_DEGREES = 30.0
# 相机水平旋转角度，单位为度。
CAMERA_YAW_DEGREES = 45.0
# 相机沿 z 轴与原点之间的距离。
CAMERA_DISTANCE = 6.0


def identity_matrix():
    """输入：无。输出：4x4 单位矩阵。功能：创建列主序的单位矩阵。"""
    # 列表按“列优先”排列，因此对角线位置是 0、5、10、15。
    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, 1.0, 0.0, 0.0,
        0.0, 0.0, 1.0, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def multiply_matrices(left, right):
    """输入：两个 4x4 列主序矩阵。输出：乘积矩阵。功能：计算 left 乘以 right。"""
    result = [0.0] * 16

    # 遍历结果矩阵的每一列和每一行。
    for column in range(4):
        for row in range(4):
            total = 0.0
            # 矩阵乘法：结果[row, column] 等于左矩阵第 row 行与右矩阵第 column 列的点积。
            for index in range(4):
                total += left[index * 4 + row] * right[column * 4 + index]
            result[column * 4 + row] = total

    return result


def create_orthographic_projection(left, right, bottom, top, near, far):
    """输入：正交投影的左右、上下、近远范围。输出：投影矩阵。功能：构造 glOrtho 矩阵。"""
    result = identity_matrix()

    # 把 x 方向范围映射到 OpenGL 的 -1 到 1。
    result[0] = 2.0 / (right - left)
    # 把 y 方向范围映射到 OpenGL 的 -1 到 1。
    result[5] = 2.0 / (top - bottom)
    # 把 z 方向范围映射到 OpenGL 的 -1 到 1，方向与相机坐标相反。
    result[10] = -2.0 / (far - near)

    # 平移投影区域中心，保证 left、bottom、near 对应裁剪空间边界。
    result[12] = -(right + left) / (right - left)
    result[13] = -(top + bottom) / (top - bottom)
    result[14] = -(far + near) / (far - near)

    return result


def create_projection_matrix():
    """输入：无。输出：正交投影矩阵。功能：创建适合当前窗口比例和等距视角的投影矩阵。"""
    return create_orthographic_projection(
        -ORTHO_HALF_WIDTH,
        ORTHO_HALF_WIDTH,
        -ORTHO_HALF_HEIGHT,
        ORTHO_HALF_HEIGHT,
        ORTHO_NEAR,
        ORTHO_FAR,
    )


def create_translation_matrix(x, y, z):
    """输入：沿三个轴平移的距离。输出：平移矩阵。功能：构造平移矩阵。"""
    result = identity_matrix()

    # 列主序矩阵中，第四列的 12、13、14 号元素负责 x、y、z 平移。
    result[12] = x
    result[13] = y
    result[14] = z
    return result


def create_rotation_x_matrix(degrees):
    """输入：绕 x 轴的旋转角度。输出：旋转矩阵。功能：构造绕 x 轴的旋转矩阵。"""
    radians = math.radians(degrees)
    cosine = math.cos(radians)
    sine = math.sin(radians)

    return [
        1.0, 0.0, 0.0, 0.0,
        0.0, cosine, sine, 0.0,
        0.0, -sine, cosine, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def create_rotation_y_matrix(degrees):
    """输入：绕 y 轴的旋转角度。输出：旋转矩阵。功能：构造绕 y 轴的旋转矩阵。"""
    radians = math.radians(degrees)
    cosine = math.cos(radians)
    sine = math.sin(radians)

    return [
        cosine, 0.0, -sine, 0.0,
        0.0, 1.0, 0.0, 0.0,
        sine, 0.0, cosine, 0.0,
        0.0, 0.0, 0.0, 1.0,
    ]


def create_view_matrix():
    """输入：无。输出：视图矩阵。功能：组合相机平移、俯角和水平转角。"""
    # 正角度让相机升到物体上方，俯视角约为 30 度。
    pitch_matrix = create_rotation_x_matrix(CAMERA_PITCH_DEGREES)
    # 绕 y 轴旋转 45 度，让方块的正面和侧面同时可见。
    yaw_matrix = create_rotation_y_matrix(CAMERA_YAW_DEGREES)
    # 沿 z 轴后退，把相机前方的世界坐标移动到正交投影范围内。
    translation_matrix = create_translation_matrix(0.0, 0.0, -CAMERA_DISTANCE)

    # 从顶点的变换顺序看：先绕 y 轴水平旋转，再绕 x 轴俯仰，最后沿 z 轴平移。
    rotation_matrix = multiply_matrices(pitch_matrix, yaw_matrix)
    return multiply_matrices(translation_matrix, rotation_matrix)


def create_island_model_view_matrix(view_matrix, island_angle):
    """输入：基础视图矩阵和岛屿角度。输出：含岛屿旋转的模型视图矩阵。"""
    # 岛屿绕世界坐标的 y 轴旋转，因此先构造绕 y 轴的旋转矩阵。
    island_rotation = create_rotation_y_matrix(island_angle)
    # 顶点先旋转，再经过原有视图矩阵，等价于让整个岛绕垂直轴旋转。
    return multiply_matrices(view_matrix, island_rotation)


def transform_point(matrix, point):
    """输入：4x4 列主序矩阵和三维点。输出：变换后的四维坐标。"""
    x, y, z = point
    # 列主序矩阵中，第 row 行第 col 列的元素位置是 col * 4 + row。
    transformed_x = matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12]
    transformed_y = matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13]
    transformed_z = matrix[2] * x + matrix[6] * y + matrix[10] * z + matrix[14]
    transformed_w = matrix[3] * x + matrix[7] * y + matrix[11] * z + matrix[15]
    return transformed_x, transformed_y, transformed_z, transformed_w


def project_point_to_screen(point, projection_matrix, model_view_matrix):
    """输入：三维点、投影矩阵和模型视图矩阵。输出：屏幕像素坐标。"""
    # 依次经过模型视图和投影，得到裁剪空间坐标。
    eye_point = transform_point(model_view_matrix, point)
    clip_point = transform_point(projection_matrix, eye_point[:3])

    # 透视除法把裁剪空间坐标变成 -1 到 1 的标准化设备坐标。
    if abs(clip_point[3]) < 1e-9:
        raise ValueError("投影结果无效，w 分量接近 0")
    normalized_x = clip_point[0] / clip_point[3]
    normalized_y = clip_point[1] / clip_point[3]

    # 把 -1 到 1 的坐标映射成窗口像素坐标。
    screen_x = (normalized_x + 1.0) * 0.5 * WINDOW_WIDTH
    # 屏幕 y 轴向下，因此用 1.0 - normalized_y 进行翻转。
    screen_y = (1.0 - normalized_y) * 0.5 * WINDOW_HEIGHT
    return screen_x, screen_y
