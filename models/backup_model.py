"""数据导出 / 导入：把用户数据备份为 JSON，或从备份恢复。

导出范围只含用户数据表，不含随应用自带的动作资料库（exercise_catalog /
exercise_aliases），因为新版本自带这些。
"""

import json
import os
import sqlite3
from datetime import datetime

from models.database import get_db
from utils.platform import get_db_path

# 导出的用户数据表（顺序敏感：先有引用的表）
EXPORT_TABLES = [
    "strength_records",
    "cardio_records",
    "body_records",
    "meal_records",
    "user_metrics",
    "user_profile",
    "workout_templates",
    "custom_exercises",
    "nuke_markers",
    "exercise_usage",
]


def export_backup_json() -> dict:
    """把当前用户数据导出为可 JSON 序列化的 dict。"""
    conn = get_db()
    data = {
        "app": "fitness",
        "version": 2,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "tables": {},
    }
    for table in EXPORT_TABLES:
        rows = conn.execute(f"SELECT * FROM {table}").fetchall()
        data["tables"][table] = [dict(r) for r in rows]
    conn.close()
    return data


def save_backup_file(target_path=None) -> str:
    """把导出数据写到 JSON 文件，返回路径。"""
    data = export_backup_json()
    if not target_path:
        target_path = _default_backup_path()
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    tmp = target_path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, target_path)
    return target_path


def _default_backup_path():
    return os.path.join(os.path.dirname(get_db_path()), "fitness_backup.json")


def import_backup_file(source_path) -> dict:
    """从 JSON 备份恢复用户数据。返回 {"imported": n, "skipped": n}。"""
    with open(source_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if data.get("app") != "fitness":
        raise ValueError("不是本应用的备份文件")
    conn = get_db()
    imported = 0
    skipped = 0
    tables_data = data.get("tables", {})
    for table in EXPORT_TABLES:
        rows = tables_data.get(table, [])
        if table not in _table_columns(conn):
            continue
        for row in rows:
            try:
                if _insert_row(conn, table, row):
                    imported += 1
                else:
                    skipped += 1
            except Exception:
                skipped += 1
    conn.commit()
    conn.close()
    return {"imported": imported, "skipped": skipped}


def _table_columns(conn):
    cols = {}
    for table in EXPORT_TABLES:
        try:
            cols[table] = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        except Exception:
            cols[table] = set()
    return cols


def _insert_row(conn, table, row):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    # 按主键去重：若该行主键已存在则跳过（幂等合并）
    pks = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")
           if r[5] > 0]
    if pks and all(pk in row for pk in pks):
        exists = conn.execute(
            f"SELECT 1 FROM {table} WHERE " + " AND ".join(f"{pk}=?" for pk in pks),
            [row[pk] for pk in pks]).fetchone()
        if exists:
            return False
    allowed = [c for c in cols if c in row]
    values = [row[c] for c in allowed]
    placeholders = ",".join("?" * len(allowed))
    col_sql = ",".join(allowed)
    conn.execute(
        f"INSERT INTO {table} ({col_sql}) VALUES ({placeholders})", values)
    return True
