import json
from models.database import get_db

def get_date_template_name(date_str):
    conn = get_db()
    plan_rows = conn.execute(
        "SELECT item_type, exercise_name FROM daily_plan WHERE plan_date = ?", (date_str,)
    ).fetchall()
    plan_items = {(row[0], row[1]) for row in plan_rows}
    if not plan_items:
        strength_rows = conn.execute(
            "SELECT DISTINCT exercise_name FROM strength_records WHERE record_date = ?",
            (date_str,),
        ).fetchall()
        cardio_rows = conn.execute(
            "SELECT DISTINCT exercise_type FROM cardio_records WHERE record_date = ?",
            (date_str,),
        ).fetchall()
        plan_items = ({("strength", row[0]) for row in strength_rows} |
                      {("cardio", row[0]) for row in cardio_rows})
    if not plan_items:
        conn.close()
        return None
    tmpl_rows = conn.execute("SELECT name, items FROM workout_templates").fetchall()
    conn.close()
    if not tmpl_rows:
        return None
    best_name, best_score = None, 0
    for t_name, t_items_json in tmpl_rows:
        try:
            items = json.loads(t_items_json)
        except (TypeError, json.JSONDecodeError):
            continue
        if not isinstance(items, list):
            continue
        tmpl_items = {(item.get("type"), item.get("name")) for item in items
                      if isinstance(item, dict) and item.get("type") and item.get("name")}
        if not tmpl_items:
            continue
        overlap = len(plan_items & tmpl_items)
        score = overlap / max(len(tmpl_items), len(plan_items))
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


def get_date_overview(date_str):
    """Return all user-facing records associated with one calendar date."""
    conn = get_db()
    strength = conn.execute(
        "SELECT * FROM strength_records WHERE record_date = ? ORDER BY created_at ASC, id ASC",
        (date_str,),
    ).fetchall()
    cardio = conn.execute(
        "SELECT * FROM cardio_records WHERE record_date = ? ORDER BY created_at ASC, id ASC",
        (date_str,),
    ).fetchall()
    plans = conn.execute(
        "SELECT * FROM daily_plan WHERE plan_date = ? ORDER BY id ASC",
        (date_str,),
    ).fetchall()
    meals = conn.execute(
        "SELECT * FROM meal_records WHERE record_date = ? ORDER BY id ASC",
        (date_str,),
    ).fetchall()
    body = conn.execute(
        "SELECT * FROM body_records WHERE record_date = ? ORDER BY created_at DESC, id DESC",
        (date_str,),
    ).fetchall()
    conn.close()

    strength = [dict(row) for row in strength]
    cardio = [dict(row) for row in cardio]
    plans = [dict(row) for row in plans]
    meals = [dict(row) for row in meals]
    body = [dict(row) for row in body]

    from models.metrics_model import (
        calc_cardio_calories, calc_strength_calories, get_user_weight,
    )
    reference_weight = get_user_weight(date_str)
    exercise_calories = sum(
        calc_strength_calories(
            row["exercise_name"], row["sets"], row["reps"], row["weight"],
            reference_weight,
        )
        for row in strength
    )
    exercise_calories += sum(
        calc_cardio_calories(row["exercise_type"], row["duration"], reference_weight)
        for row in cardio
    )

    return {
        "date": date_str,
        "template_name": get_date_template_name(date_str),
        "nuked": _is_nuked(date_str),
        "plans": plans,
        "strength": strength,
        "cardio": cardio,
        "meals": meals,
        "body": body,
        "intake_calories": round(sum(row["calories"] for row in meals), 0),
        "exercise_calories": round(exercise_calories, 0),
        "reference_weight": reference_weight,
    }


def _is_nuked(date_str):
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM nuke_markers WHERE record_date = ? LIMIT 1", (date_str,)
    ).fetchone()
    conn.close()
    return bool(row)
