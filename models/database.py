import sqlite3
import os
import json
from config.constants import DB_FILENAME, DEFAULT_TEMPLATES
from utils.platform import get_db_path

def get_db():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS strength_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT, exercise_name TEXT NOT NULL, sets INTEGER NOT NULL,
            reps INTEGER NOT NULL, weight REAL NOT NULL, record_date DATE NOT NULL,
            notes TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS cardio_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT, exercise_type TEXT NOT NULL,
            distance REAL NOT NULL, duration INTEGER NOT NULL, record_date DATE NOT NULL,
            notes TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS body_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT, weight REAL, body_fat REAL,
            chest REAL, waist REAL, arm REAL, record_date DATE NOT NULL,
            notes TEXT DEFAULT '', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS nuke_markers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, record_date DATE NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS workout_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, items TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS daily_plan (
            id INTEGER PRIMARY KEY AUTOINCREMENT, plan_date DATE NOT NULL, item_type TEXT NOT NULL,
            exercise_name TEXT NOT NULL, target_sets INTEGER, target_reps INTEGER,
            target_weight REAL, target_weight_step REAL DEFAULT 0, target_rep_step REAL DEFAULT 0,
            target_distance REAL, target_duration INTEGER, completed INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS custom_exercises (
            exercise_name TEXT NOT NULL, ex_type TEXT NOT NULL,
            PRIMARY KEY (exercise_name, ex_type)
        );
        CREATE TABLE IF NOT EXISTS user_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT, record_date DATE UNIQUE, weight_kg REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            gender TEXT DEFAULT 'male',
            height_cm REAL DEFAULT 170,
            age INTEGER DEFAULT 30,
            activity_factor REAL DEFAULT 1.375,
            deficit_goal INTEGER DEFAULT 500
        );
        CREATE TABLE IF NOT EXISTS meal_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT, record_date DATE NOT NULL,
            meal_type TEXT NOT NULL, food_summary TEXT NOT NULL,
            calories REAL NOT NULL, items_json TEXT DEFAULT '',
            source TEXT DEFAULT 'ai', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # 确保 user_profile 有默认行
    conn.execute("INSERT OR IGNORE INTO user_profile (id) VALUES (1)")
    cols = [r[1] for r in conn.execute("PRAGMA table_info(daily_plan)").fetchall()]
    if "target_weight_step" not in cols:
        conn.execute("ALTER TABLE daily_plan ADD COLUMN target_weight_step REAL DEFAULT 0")
        conn.commit()
    if "target_rep_step" not in cols:
        cols2 = [r[1] for r in conn.execute("PRAGMA table_info(daily_plan)").fetchall()]
        if "target_rep_step" not in cols2:
            conn.execute("ALTER TABLE daily_plan ADD COLUMN target_rep_step REAL DEFAULT 0")
            conn.commit()
    existing = conn.execute("SELECT COUNT(*) FROM workout_templates").fetchone()[0]
    if existing == 0:
        for name, items in DEFAULT_TEMPLATES:
            conn.execute("INSERT INTO workout_templates (name, items) VALUES (?, ?)",
                         (name, json.dumps(items, ensure_ascii=False)))
    else:
        conn.execute("DELETE FROM workout_templates WHERE name IS NULL OR name = ''")
        old_defaults = {"推胸日", "拉背日", "腿日"}
        existing_names = {r[0] for r in conn.execute("SELECT name FROM workout_templates").fetchall()}
        for name in old_defaults & existing_names:
            conn.execute("DELETE FROM workout_templates WHERE name = ?", (name,))
        for name, items in DEFAULT_TEMPLATES:
            if name not in existing_names:
                conn.execute("INSERT INTO workout_templates (name, items) VALUES (?, ?)",
                             (name, json.dumps(items, ensure_ascii=False)))
    conn.commit()
    conn.close()
