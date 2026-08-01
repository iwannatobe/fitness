from datetime import date
from models.database import get_db

def add_body(weight, body_fat, chest, waist, arm, record_date, notes=""):
    conn = get_db()
    conn.execute("INSERT INTO body_records (weight, body_fat, chest, waist, arm, record_date, notes) VALUES (?,?,?,?,?,?,?)", (weight, body_fat, chest, waist, arm, record_date, notes))
    conn.commit(); conn.close()

def set_latest_body(weight, body_fat, chest, waist, arm, notes=""):
    """Replace all body data with a single latest snapshot."""
    today = date.today().isoformat()
    conn = get_db()
    conn.execute("DELETE FROM body_records")
    conn.execute(
        "INSERT INTO body_records (weight, body_fat, chest, waist, arm, record_date, notes) "
        "VALUES (?,?,?,?,?,?,?)",
        (weight, body_fat, chest, waist, arm, today, notes))
    conn.commit(); conn.close()

def get_latest_body():
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM body_records ORDER BY created_at DESC, id DESC LIMIT 1").fetchone()
    conn.close()
    return dict(row) if row else None

def get_body_records():
    conn = get_db()
    rows = conn.execute("SELECT * FROM body_records ORDER BY record_date DESC, created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def delete_body(record_id):
    conn = get_db()
    conn.execute("DELETE FROM body_records WHERE id = ?", (record_id,))
    conn.commit(); conn.close()
