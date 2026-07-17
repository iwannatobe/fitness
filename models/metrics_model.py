from datetime import date
from models.database import get_db
from config.constants import CARDIO_MET, STRENGTH_MET, STRENGTH_MET_DEFAULT, DEFAULT_WEIGHT_KG, CARDIO_CAL_DEFAULT_MET

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
    """力量训练消耗：MET × 体重(kg) × (组数 × 2分钟) / 60

    每组成估算 2 分钟（含动作执行 30-45s + 组间休息 + 准备），
    参考《体力活动纲要》(Compendium of Physical Activities) 的 MET 值：
    深蹲/硬拉 = 6.0，卧推/划船 = 5.5，孤立动作 = 3.5-4.0。
    """
    if body_weight is None:
        body_weight = get_user_weight()
    met = STRENGTH_MET.get(exercise_name, STRENGTH_MET_DEFAULT)
    est_time_hours = (sets * 2.0) / 60.0
    return round(met * body_weight * est_time_hours, 1)

def calc_cardio_calories(exercise_type, duration_min, body_weight=None):
    if body_weight is None: body_weight = get_user_weight()
    met = CARDIO_MET.get(exercise_type, CARDIO_CAL_DEFAULT_MET)
    return round(met * body_weight * (duration_min / 60.0), 1)
