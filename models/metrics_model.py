from datetime import date
from models.database import get_db
from config.constants import CARDIO_MET, STRENGTH_CAL_FACTOR, STRENGTH_CAL_FACTORS, DEFAULT_REPS, DEFAULT_WEIGHT_KG, CARDIO_CAL_DEFAULT_MET

def get_user_weight(date_str=None):
    if date_str is None: date_str = date.today().isoformat()
    conn = get_db()
    row = conn.execute("SELECT weight FROM body_records WHERE record_date <= ? ORDER BY record_date DESC LIMIT 1", (date_str,)).fetchone()
    if row and row[0]: conn.close(); return row[0]
    row = conn.execute("SELECT weight_kg FROM user_metrics WHERE record_date <= ? ORDER BY record_date DESC LIMIT 1", (date_str,)).fetchone()
    conn.close()
    return row[0] if row else DEFAULT_WEIGHT_KG

def set_user_weight(date_str, weight_kg):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO user_metrics (record_date, weight_kg) VALUES (?, ?)", (date_str, weight_kg))
    conn.commit(); conn.close()

def calc_strength_calories(exercise_name, sets, reps, weight_kg, body_weight=None):
    if body_weight is None: body_weight = get_user_weight()
    reps = reps or DEFAULT_REPS
    weight = weight_kg if weight_kg > 0 else body_weight * 0.4
    factor = STRENGTH_CAL_FACTORS.get(exercise_name, STRENGTH_CAL_FACTOR)
    return round(sets * reps * weight * factor * (body_weight / DEFAULT_WEIGHT_KG), 1)

def calc_cardio_calories(exercise_type, duration_min, body_weight=None):
    if body_weight is None: body_weight = get_user_weight()
    met = CARDIO_MET.get(exercise_type, CARDIO_CAL_DEFAULT_MET)
    return round(met * body_weight * (duration_min / 60.0), 1)
