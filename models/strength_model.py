from models.database import get_db

def add_strength(exercise_name, sets, reps, weight, record_date, notes=""):
    conn = get_db()
    conn.execute("INSERT INTO strength_records (exercise_name, sets, reps, weight, record_date, notes) VALUES (?,?,?,?,?,?)", (exercise_name, sets, reps, weight, record_date, notes))
    conn.commit(); conn.close()

def get_last_strength(exercise_name):
    conn = get_db()
    row = conn.execute("SELECT * FROM strength_records WHERE exercise_name = ? ORDER BY record_date DESC, created_at DESC LIMIT 1", (exercise_name,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_strength_records():
    conn = get_db()
    rows = conn.execute("SELECT * FROM strength_records ORDER BY record_date DESC, created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_strength(record_id):
    conn = get_db()
    conn.execute("DELETE FROM strength_records WHERE id = ?", (record_id,))
    conn.commit(); conn.close()
