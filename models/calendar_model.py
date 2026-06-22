import json
from models.database import get_db

def get_date_template_name(date_str):
    conn = get_db()
    plan_rows = conn.execute("SELECT exercise_name FROM daily_plan WHERE plan_date = ? AND item_type = 'strength'", (date_str,)).fetchall()
    plan_names = {r[0] for r in plan_rows}
    if not plan_names:
        rec_rows = conn.execute("SELECT DISTINCT exercise_name FROM strength_records WHERE record_date = ?", (date_str,)).fetchall()
        plan_names = {r[0] for r in rec_rows}
    tmpl_rows = conn.execute("SELECT name, items FROM workout_templates").fetchall()
    conn.close()
    if not plan_names or not tmpl_rows: return None
    best_name, best_score = None, 0
    for t_name, t_items_json in tmpl_rows:
        items = json.loads(t_items_json)
        tmpl_names = {it["name"] for it in items if it.get("type") == "strength"}
        if not tmpl_names: continue
        overlap = len(plan_names & tmpl_names)
        score = overlap / max(len(tmpl_names), len(plan_names))
        if score >= 0.5 and score > best_score: best_score, best_name = score, t_name
    return best_name

def get_active_dates():
    conn = get_db()
    dates = {}
    for row in conn.execute("SELECT DISTINCT record_date FROM strength_records").fetchall():
        d = row[0]; dates.setdefault(d, {"strength":False,"cardio":False}); dates[d]["strength"] = True
    for row in conn.execute("SELECT DISTINCT record_date FROM cardio_records").fetchall():
        d = row[0]; dates.setdefault(d, {"strength":False,"cardio":False}); dates[d]["cardio"] = True
    conn.close()
    return dates

def get_date_detail(date_str):
    conn = get_db()
    s_rows = conn.execute("SELECT * FROM strength_records WHERE record_date = ? ORDER BY created_at DESC", (date_str,)).fetchall()
    c_rows = conn.execute("SELECT * FROM cardio_records WHERE record_date = ? ORDER BY created_at DESC", (date_str,)).fetchall()
    conn.close()
    return [dict(r) for r in s_rows], [dict(r) for r in c_rows]
