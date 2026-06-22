from models.database import get_db

def add_cardio(exercise_type, distance, duration, record_date, notes=""):
    conn = get_db()
    conn.execute("INSERT INTO cardio_records (exercise_type, distance, duration, record_date, notes) VALUES (?,?,?,?,?)", (exercise_type, distance, duration, record_date, notes))
    conn.commit(); conn.close()

def get_last_cardio(exercise_type):
    conn = get_db()
    row = conn.execute("SELECT * FROM cardio_records WHERE exercise_type = ? ORDER BY record_date DESC, created_at DESC LIMIT 1", (exercise_type,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_cardio_records():
    conn = get_db()
    rows = conn.execute("SELECT * FROM cardio_records ORDER BY record_date DESC, created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_cardio(record_id):
    conn = get_db()
    conn.execute("DELETE FROM cardio_records WHERE id = ?", (record_id,))
    conn.commit(); conn.close()
