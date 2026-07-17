"""热量收支：BMR(Mifflin-St Jeor) / TDEE / 今日摄入 / 运动消耗 / 热量差 / 体重趋势。"""

from datetime import date, timedelta
from models.database import get_db
from models.profile_model import get_profile
from models.meal_model import get_meals_for_date
from models.metrics_model import get_user_weight


def get_bmr(weight_kg=None) -> float:
    """Mifflin-St Jeor 基础代谢率。"""
    p = get_profile()
    w = weight_kg if weight_kg else get_user_weight()
    base = 10 * w + 6.25 * p["height_cm"] - 5 * p["age"]
    return round(base + (5 if p["gender"] == "male" else -161), 0)


def get_tdee(weight_kg=None) -> float:
    """每日总能耗 = BMR × 活动系数。"""
    return round(get_bmr(weight_kg) * get_profile()["activity_factor"], 0)


def today_intake() -> float:
    """今日已摄入热量（三餐+加餐累计）。"""
    meals = get_meals_for_date(date.today().isoformat())
    return round(sum(m["calories"] for m in meals), 0)


def today_exercise_burn() -> float:
    """今日运动消耗：从 strength_records + cardio_records 实算。"""
    today = date.today().isoformat()
    conn = get_db()
    s_rows = conn.execute(
        "SELECT exercise_name, sets, reps, weight FROM strength_records "
        "WHERE record_date = ?", (today,)).fetchall()
    c_rows = conn.execute(
        "SELECT exercise_type, duration FROM cardio_records "
        "WHERE record_date = ?", (today,)).fetchall()
    conn.close()
    from models.metrics_model import calc_strength_calories, calc_cardio_calories
    total = 0.0
    for r in s_rows:
        total += calc_strength_calories(r["exercise_name"], r["sets"],
                                        r["reps"], r["weight"])
    for r in c_rows:
        total += calc_cardio_calories(r["exercise_type"], r["duration"])
    return round(total, 0)


def today_balance() -> dict:
    """今日热量收支：摄入 - (TDEE + 运动消耗)；负值=赤字(减脂)。"""
    intake = today_intake()
    burn = today_exercise_burn()
    tdee = get_tdee()
    return {
        "intake": intake,
        "tdee": tdee,
        "exercise": burn,
        "total_burn": round(tdee + burn, 0),
        "balance": round(intake - tdee - burn, 0),  # 负=赤字
        "deficit_goal": get_profile()["deficit_goal"],
    }


def weight_trend(days: int = 7) -> list[dict]:
    """近 N 天体重序列（按日去重，取该日最近一条）。"""
    conn = get_db()
    rows = conn.execute(
        "SELECT record_date, weight FROM body_records "
        "WHERE record_date >= date('now', ?) ORDER BY record_date ASC",
        (f"-{days} days",),
    ).fetchall()
    conn.close()
    by_date = {}
    for r in rows:
        by_date[r["record_date"]] = r["weight"]
    return [{"date": d, "weight": w} for d, w in sorted(by_date.items())]


def today_summary_text() -> str:
    """给 AI 注入的今日热量摘要文本。"""
    b = today_balance()
    meals = get_meals_for_date(date.today().isoformat())
    w = get_user_weight()
    lines = [f"当前体重约 {w}kg；今日热量：摄入 {b['intake']}kcal，"
             f"运动消耗 {b['exercise']}kcal，TDEE {b['tdee']}kcal，"
             f"收支 {b['balance']}kcal（{'赤字' if b['balance'] < 0 else '盈余'}），"
             f"减脂目标赤字 {b['deficit_goal']}kcal。"]
    if meals:
        lines.append("今日饮食：" + "；".join(
            f"{m['meal_type']} {m['food_summary']}({m['calories']}kcal)" for m in meals))
    else:
        lines.append("今日尚未记录饮食。")
    return "\n".join(lines)
