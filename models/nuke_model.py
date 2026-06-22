from models.database import get_db

def add_nuke_marker(date_str):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO nuke_markers (record_date) VALUES (?)", (date_str,))
    conn.commit(); conn.close()

def is_date_nuked(date_str):
    conn = get_db()
    row = conn.execute("SELECT 1 FROM nuke_markers WHERE record_date = ?", (date_str,)).fetchone()
    conn.close()
    return row is not None

def get_nuke_dates():
    conn = get_db()
    rows = conn.execute("SELECT record_date FROM nuke_markers").fetchall()
    conn.close()
    return {r[0] for r in rows}
