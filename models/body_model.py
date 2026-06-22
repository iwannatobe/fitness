from models.database import get_db

def add_body(weight, body_fat, chest, waist, arm, record_date, notes=""):
    conn = get_db()
    conn.execute("INSERT INTO body_records (weight, body_fat, chest, waist, arm, record_date, notes) VALUES (?,?,?,?,?,?,?)", (weight, body_fat, chest, waist, arm, record_date, notes))
    conn.commit(); conn.close()

def get_body_records():
    conn = get_db()
    rows = conn.execute("SELECT * FROM body_records ORDER BY record_date DESC, created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_body(record_id):
    conn = get_db()
    conn.execute("DELETE FROM body_records WHERE id = ?", (record_id,))
    conn.commit(); conn.close()
