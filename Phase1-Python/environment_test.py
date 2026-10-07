"""这个文件专门测试渐变天空、距离雾、水面和萤火虫粒子。"""

import pygame
from OpenGL.GL import glViewport

import camera
import level
import renderer


def create_test_blocks():
    """输入：无。输出：方块列表。功能：创建近景、中景和远景形状。"""
    return [
        level.Block(-1.8, 0.0, 0.0, "purple", "arch", True),
        level.Block(-0.5, 0.0, -0.6, "blue", "sphere", True),
        level.Block(0.8, 0.0, -2.2, "pink", "ring", True),
        level.Block(2.1, 0.0, -4.6, "white", "cone", True),
    ]


def main():
    """输入：无。输出：无。功能：同时显示天空、雾、水面和漂浮粒子。"""
    width = 1100
    height = 640
    pygame.init()
    pygame.display.set_mode(
        (width, height),
        pygame.OPENGL | pygame.DOUBLEBUF,
    )
    pygame.display.set_caption("天空、雾、水面与粒子测试")
    glViewport(0, 0, width, height)
    renderer.initialize_renderer()

    projection_matrix = camera.create_projection_matrix()
    view_matrix = camera.create_view_matrix()
    blocks = create_test_blocks()
    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        view_angle = pygame.time.get_ticks() * 0.025
        renderer.begin_frame(projection_matrix, view_matrix, view_angle)
        renderer.draw_water(0.0, -1.15, 0.0, size=16.0, resolution=30)
        renderer.begin_island_transform(0.0)
        for block in blocks:
            renderer.draw_block(
                block.x,
                block.y,
                block.z,
                1.0,
                block.color,
                block.shape,
            )
        renderer.end_island_transform()
        renderer.draw_fireflies(
            center_y=0.8,
            count=64,
            range_x=5.5,
            range_y=3.2,
            range_z=4.5,
        )
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
