import json
from models.database import get_db

def add_template(name, items):
    conn = get_db()
    conn.execute("INSERT INTO workout_templates (name, items) VALUES (?, ?)", (name, json.dumps(items, ensure_ascii=False)))
    conn.commit(); conn.close()

def get_templates():
    conn = get_db()
    rows = conn.execute("SELECT * FROM workout_templates ORDER BY created_at DESC").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r); d["items"] = json.loads(d["items"]); result.append(d)
    return result

def delete_template(template_id):
    conn = get_db()
    conn.execute("DELETE FROM workout_templates WHERE id = ?", (template_id,))
    conn.commit(); conn.close()

def update_template(template_id, name, items):
    conn = get_db()
    conn.execute("UPDATE workout_templates SET name = ?, items = ? WHERE id = ?", (name, json.dumps(items, ensure_ascii=False), template_id))
    conn.commit(); conn.close()
