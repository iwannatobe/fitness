"""饮食记录 CRUD：一餐一条，calories 为该餐总热量。"""

from datetime import date
from models.database import get_db


def add_meal(meal_type, food_summary, calories, items_json="", source="ai",
             record_date=None):
    if record_date is None:
        record_date = date.today().isoformat()
    conn = get_db()
    conn.execute(
        "INSERT INTO meal_records (record_date, meal_type, food_summary, "
        "calories, items_json, source) VALUES (?,?,?,?,?,?)",
        (record_date, meal_type, food_summary, calories, items_json, source),
    )
    conn.commit(); conn.close()


def get_meals_for_date(record_date=None):
    if record_date is None:
        record_date = date.today().isoformat()
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM meal_records WHERE record_date = ? ORDER BY id ASC",
        (record_date,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_today_meals():
    return get_meals_for_date(date.today().isoformat())


def delete_meal(meal_id):
    conn = get_db()
    conn.execute("DELETE FROM meal_records WHERE id = ?", (meal_id,))
    conn.commit(); conn.close()
