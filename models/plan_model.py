from datetime import date
from models.database import get_db

def clear_today_plan():
    today = date.today().isoformat()
    conn = get_db()
    conn.execute("DELETE FROM daily_plan WHERE plan_date = ?", (today,))
    conn.commit(); conn.close()

def add_plan_item(item_type, exercise_name, target_sets=None, target_reps=None,
                  target_weight=None, target_weight_step=0, target_rep_step=0,
                  target_distance=None, target_duration=None, exercise_id=None):
    today = date.today().isoformat()
    conn = get_db()
    conn.execute("INSERT INTO daily_plan (plan_date, item_type, exercise_name, target_sets, target_reps, target_weight, target_weight_step, target_rep_step, target_distance, target_duration, exercise_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (today, item_type, exercise_name, target_sets, target_reps, target_weight, target_weight_step, target_rep_step, target_distance, target_duration, exercise_id))
    conn.commit(); conn.close()

def get_today_plan():
    today = date.today().isoformat()
    conn = get_db()
    rows = conn.execute("SELECT * FROM daily_plan WHERE plan_date = ? ORDER BY id ASC", (today,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def complete_plan_item(plan_id):
    conn = get_db()
    conn.execute("UPDATE daily_plan SET completed = 1 WHERE id = ?", (plan_id,))
    conn.commit(); conn.close()
    from models.training_session_model import finish_today_training_session_if_complete
    finish_today_training_session_if_complete()

def delete_plan_item(plan_id):
    conn = get_db()
    conn.execute("DELETE FROM daily_plan WHERE id = ?", (plan_id,))
    conn.commit(); conn.close()

def update_plan_item(plan_id, **fields):
    allowed = {
        "target_sets", "target_reps", "target_weight",
        "target_weight_step", "target_rep_step",
        "target_distance", "target_duration",
    }
    cols = []
    vals = []
    for k, v in fields.items():
        if k in allowed:
            cols.append(f"{k} = ?")
            vals.append(v)
    if not cols:
        return
    conn = get_db()
    vals.append(plan_id)
    conn.execute(f"UPDATE daily_plan SET {', '.join(cols)} WHERE id = ?", vals)
    conn.commit(); conn.close()
