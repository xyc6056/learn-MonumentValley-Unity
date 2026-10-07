"""这个文件负责使用 sqlite3 保存关卡、进度和设置。

数据库包含三张表：
levels：关卡编号、名称、方块数据、起点、终点
progress：关卡编号、是否完成、最佳步数
settings：设置键、设置值
"""

import re
import sqlite3
from contextlib import closing
from pathlib import Path


# 默认数据库文件路径。
DEFAULT_DATABASE_PATH = Path(__file__).resolve().parent / "progress.db"
# 默认关卡目录。
DEFAULT_LEVELS_DIRECTORY = Path(__file__).resolve().parent / "levels"
# 每个关卡默认起点；未配置时使用第一个方块。
DEFAULT_LEVEL_STARTS = {
    1: (0, -1, -1),
    2: (0, -1, -1),
    3: (0, -1, -1),
    4: (0, -1, -1),
    5: (0, -1, -1),
}


def create_tables(connection):
    """输入：数据库连接。输出：无。功能：创建三张表。"""
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS levels (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            blocks TEXT NOT NULL,
            start TEXT NOT NULL,
            goal TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS progress (
            level_id INTEGER PRIMARY KEY,
            completed INTEGER NOT NULL DEFAULT 0,
            best_moves INTEGER
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )


def get_table_columns(connection, table_name):
    """输入：数据库连接和表名。输出：列名集合。"""
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row[1] for row in rows}


def migrate_progress_table(connection):
    """输入：数据库连接。输出：无。功能：迁移旧版 progress 表。"""
    columns = get_table_columns(connection, "progress")

    # 旧版表使用 level_number 和 unlocked，需要重建并保留完成状态。
    if "level_number" in columns and "level_id" not in columns:
        connection.execute("ALTER TABLE progress RENAME TO progress_old")
        connection.execute(
            """
            CREATE TABLE progress (
                level_id INTEGER PRIMARY KEY,
                completed INTEGER NOT NULL DEFAULT 0,
                best_moves INTEGER
            )
            """
        )
        connection.execute(
            """
            INSERT INTO progress (level_id, completed, best_moves)
            SELECT level_number, completed, NULL
            FROM progress_old
            """
        )
        connection.execute("DROP TABLE progress_old")
        return

    # 新版表只缺 best_moves 时直接补列。
    if "best_moves" not in columns:
        connection.execute("ALTER TABLE progress ADD COLUMN best_moves INTEGER")


def parse_level_id(file_path):
    """输入：关卡路径。输出：关卡编号或 None。"""
    match = re.fullmatch(r"level(\d+)\.txt", file_path.name)
    return int(match.group(1)) if match else None


def parse_level_blocks(blocks_text):
    """输入：关卡文本。输出：方块列表。"""
    blocks = []
    for raw_line in blocks_text.splitlines():
        parts = [part.strip() for part in raw_line.strip().split(",")]
        if len(parts) == 4:
            blocks.append(
                (int(parts[0]), int(parts[1]), int(parts[2]), parts[3].lower())
            )
    return blocks


def find_start_block(level_id, blocks):
    """输入：关卡编号和方块列表。输出：起点坐标。"""
    if level_id in DEFAULT_LEVEL_STARTS:
        return DEFAULT_LEVEL_STARTS[level_id]
    return blocks[0][:3] if blocks else (0, 0, 0)


def find_goal_block(blocks):
    """输入：方块列表。输出：终点坐标。"""
    for x, y, z, color in blocks:
        if color == "gold":
            return x, y, z
    return blocks[-1][:3] if blocks else (0, 0, 0)


def format_position(position):
    """输入：坐标。输出：x,y,z 文本。"""
    return f"{position[0]},{position[1]},{position[2]}"


def sync_levels_from_directory(connection, levels_directory):
    """输入：数据库连接和关卡目录。输出：无。"""
    for file_path in sorted(levels_directory.glob("level*.txt")):
        level_id = parse_level_id(file_path)
        if level_id is None:
            continue

        blocks_text = file_path.read_text(encoding="utf-8")
        blocks = parse_level_blocks(blocks_text)
        connection.execute(
            """
            INSERT INTO levels (id, name, blocks, start, goal)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                blocks = excluded.blocks,
                start = excluded.start,
                goal = excluded.goal
            """,
            (
                level_id,
                f"第 {level_id} 关",
                blocks_text,
                format_position(find_start_block(level_id, blocks)),
                format_position(find_goal_block(blocks)),
            ),
        )


def initialize_database(
    database_path=DEFAULT_DATABASE_PATH,
    levels_directory=DEFAULT_LEVELS_DIRECTORY,
):
    """输入：数据库路径和关卡目录。输出：无。"""
    with closing(sqlite3.connect(database_path)) as connection:
        create_tables(connection)
        migrate_progress_table(connection)
        sync_levels_from_directory(connection, levels_directory)
        connection.commit()


def read_level(database_path, level_id):
    """输入：数据库路径和关卡编号。输出：关卡字典或 None。"""
    with closing(sqlite3.connect(database_path)) as connection:
        row = connection.execute(
            """
            SELECT id, name, blocks, start, goal
            FROM levels
            WHERE id = ?
            """,
            (level_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "blocks": row[2],
        "start": row[3],
        "goal": row[4],
    }


def save_progress(database_path, level_id, completed, best_moves=None):
    """输入：数据库路径、关卡编号、完成状态和最佳步数。输出：无。"""
    with closing(sqlite3.connect(database_path)) as connection:
        row = connection.execute(
            """
            SELECT best_moves
            FROM progress
            WHERE level_id = ?
            """,
            (level_id,),
        ).fetchone()

        old_best_moves = row[0] if row is not None else None
        if best_moves is None:
            final_best_moves = old_best_moves
        elif old_best_moves is None:
            final_best_moves = best_moves
        else:
            final_best_moves = min(old_best_moves, best_moves)

        connection.execute(
            """
            INSERT INTO progress (level_id, completed, best_moves)
            VALUES (?, ?, ?)
            ON CONFLICT(level_id) DO UPDATE SET
                completed = excluded.completed,
                best_moves = excluded.best_moves
            """,
            (level_id, 1 if completed else 0, final_best_moves),
        )
        connection.commit()


def read_progress(database_path, level_id):
    """输入：数据库路径和关卡编号。输出：进度字典或 None。"""
    with closing(sqlite3.connect(database_path)) as connection:
        row = connection.execute(
            """
            SELECT level_id, completed, best_moves
            FROM progress
            WHERE level_id = ?
            """,
            (level_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "level_id": row[0],
        "completed": bool(row[1]),
        "best_moves": row[2],
    }


def save_setting(database_path, key, value):
    """输入：数据库路径、设置键和值。输出：无。"""
    with closing(sqlite3.connect(database_path)) as connection:
        connection.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, str(value)),
        )
        connection.commit()


def read_setting(database_path, key, default=None):
    """输入：数据库路径、设置键和默认值。输出：设置值。"""
    with closing(sqlite3.connect(database_path)) as connection:
        row = connection.execute(
            """
            SELECT value
            FROM settings
            WHERE key = ?
            """,
            (key,),
        ).fetchone()

    if row is None:
        return default
    return row[0]
