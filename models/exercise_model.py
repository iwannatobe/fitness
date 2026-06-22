from models.database import get_db

def get_custom_exercises(ex_type):
    conn = get_db()
    rows = conn.execute("SELECT exercise_name FROM custom_exercises WHERE ex_type = ? ORDER BY exercise_name", (ex_type,)).fetchall()
    conn.close()
    return [r[0] for r in rows]

def add_custom_exercise(ex_type, name):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO custom_exercises (exercise_name, ex_type) VALUES (?, ?)", (name, ex_type))
    conn.commit(); conn.close()

def delete_custom_exercise(ex_type, name):
    conn = get_db()
    conn.execute("DELETE FROM custom_exercises WHERE exercise_name = ? AND ex_type = ?", (name, ex_type))
    conn.commit(); conn.close()
