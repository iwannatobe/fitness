"""Offline exercise catalog backed by SQLite, including local media paths."""

import json
import os
import sqlite3

from models.database import get_db

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SEED_DB = os.path.join(_ROOT, "assets", "catalog", "exercises.db")


def sync_catalog():
    """Import/update the packaged catalog into the user's writable database."""
    if not os.path.isfile(_SEED_DB):
        return
    seed = sqlite3.connect(_SEED_DB)
    seed.row_factory = sqlite3.Row
    rows = seed.execute("SELECT * FROM exercise_catalog").fetchall()
    alias_rows = seed.execute(
        "SELECT alias, exercise_id FROM exercise_aliases"
    ).fetchall() if seed.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='exercise_aliases'"
    ).fetchone()[0] else []
    seed.close()
    conn = get_db()
    conn.executemany("""
        INSERT INTO exercise_catalog (
            id, source_id, name_zh, name_en, item_type, body_part, equipment,
            target, muscle_group, secondary_muscles_json, instructions_zh,
            instruction_steps_zh_json, thumbnail_path, gif_path, attribution,
            source_commit, instructions_polished, enabled
            , animation_frames_json, animation_interval, is_common
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            source_id=excluded.source_id, name_zh=excluded.name_zh,
            name_en=excluded.name_en, item_type=excluded.item_type,
            body_part=excluded.body_part, equipment=excluded.equipment,
            target=excluded.target, muscle_group=excluded.muscle_group,
            secondary_muscles_json=excluded.secondary_muscles_json,
            instructions_zh=excluded.instructions_zh,
            instruction_steps_zh_json=excluded.instruction_steps_zh_json,
            thumbnail_path=excluded.thumbnail_path, gif_path=excluded.gif_path,
            attribution=excluded.attribution, source_commit=excluded.source_commit,
            instructions_polished=excluded.instructions_polished,
            animation_frames_json=excluded.animation_frames_json,
            animation_interval=excluded.animation_interval,
            enabled=excluded.enabled, is_common=excluded.is_common
    """, [(
        row["id"], row["source_id"], row["name_zh"], row["name_en"],
        row["item_type"], row["body_part"], row["equipment"], row["target"],
        row["muscle_group"], row["secondary_muscles_json"], row["instructions_zh"],
        row["instruction_steps_zh_json"], row["thumbnail_path"], row["gif_path"],
        row["attribution"], row["source_commit"],
        row["instructions_polished"] if "instructions_polished" in row.keys() else 0,
        row["enabled"],
        row["animation_frames_json"] if "animation_frames_json" in row.keys() else "[]",
        row["animation_interval"] if "animation_interval" in row.keys() else 0.12,
        row["is_common"] if "is_common" in row.keys() else 1,
    ) for row in rows])
    # Aliases are packaged catalog metadata, not user data. Rebuild them so
    # stale mappings from older app versions cannot point at removed rows.
    conn.execute("DELETE FROM exercise_aliases")
    conn.executemany(
        "INSERT INTO exercise_aliases (alias, exercise_id) VALUES (?, ?) "
        "ON CONFLICT(alias) DO UPDATE SET exercise_id=excluded.exercise_id",
        [(row["alias"], row["exercise_id"]) for row in alias_rows],
    )
    conn.commit()
    conn.close()


def search_catalog(query="", body_part="", limit=100, common_only=False):
    conn = get_db()
    conditions = ["enabled = 1"]
    values = []
    if common_only:
        # 常用 = 用户通过模板训练完成过的动作，按最近使用排序
        conditions.append("id IN (SELECT exercise_id FROM exercise_usage)")
    if query:
        conditions.append("(name_zh LIKE ? OR name_en LIKE ? OR equipment LIKE ? OR target LIKE ?)")
        like = f"%{query.strip()}%"
        values.extend([like, like, like, like])
    if body_part:
        conditions.append("body_part = ?")
        values.append(body_part)
    values.append(limit)
    order = ("CASE WHEN id IN (SELECT exercise_id FROM exercise_usage) THEN 0 ELSE 1 END, "
             "(SELECT last_used_at FROM exercise_usage WHERE exercise_id = id) DESC, "
             "body_part, name_zh")
    rows = conn.execute(
        "SELECT * FROM exercise_catalog WHERE " + " AND ".join(conditions)
        + " ORDER BY " + order + " LIMIT ?", values).fetchall()
    conn.close()
    return [_row_to_dict(row) for row in rows]


def record_exercise_used(exercise_id):
    """Increment the usage counter for a completed catalog exercise."""
    if not exercise_id:
        return
    conn = get_db()
    conn.execute(
        "INSERT INTO exercise_usage (exercise_id, use_count) VALUES (?, 1) "
        "ON CONFLICT(exercise_id) DO UPDATE SET "
        "use_count = use_count + 1, last_used_at = CURRENT_TIMESTAMP",
        (exercise_id,),
    )
    conn.commit()
    conn.close()


def get_catalog_exercise(exercise_id):
    if not exercise_id:
        return None
    conn = get_db()
    row = conn.execute("SELECT * FROM exercise_catalog WHERE id = ?", (exercise_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def find_catalog_exercise(exercise_id=None, exercise_name=None):
    if exercise_id:
        found = get_catalog_exercise(exercise_id)
        if found:
            return found
    if not exercise_name:
        return None
    conn = get_db()
    row = conn.execute("""
        SELECT c.* FROM exercise_catalog c
        LEFT JOIN exercise_aliases a ON a.exercise_id = c.id
        WHERE c.enabled = 1 AND (a.alias = ? OR c.name_zh = ?)
        ORDER BY CASE WHEN a.alias = ? THEN 0 ELSE 1 END
        LIMIT 1
    """, (exercise_name, exercise_name, exercise_name)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def resolve_media_path(relative_path):
    if not relative_path:
        return ""
    path = os.path.join(_ROOT, relative_path.replace("/", os.sep))
    return path if os.path.isfile(path) else ""


def _row_to_dict(row):
    data = dict(row)
    data["secondary_muscles"] = json.loads(data.pop("secondary_muscles_json"))
    data["steps_zh"] = json.loads(data.pop("instruction_steps_zh_json"))
    data["animation_frames"] = json.loads(data.pop("animation_frames_json", "[]"))
    return data
