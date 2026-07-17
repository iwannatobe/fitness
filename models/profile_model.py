"""用户画像：性别/身高/年龄/活动系数/减脂赤字目标（单行表）。"""

from models.database import get_db


def get_profile() -> dict:
    conn = get_db()
    row = conn.execute("SELECT * FROM user_profile WHERE id = 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"gender": "male", "height_cm": 170, "age": 30,
            "activity_factor": 1.375, "deficit_goal": 500}


def set_profile(gender=None, height_cm=None, age=None,
                activity_factor=None, deficit_goal=None):
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO user_profile (id) VALUES (1)")
    fields = {"gender": gender, "height_cm": height_cm, "age": age,
              "activity_factor": activity_factor, "deficit_goal": deficit_goal}
    sets = [f"{k} = ?" for k, v in fields.items() if v is not None]
    vals = [v for v in fields.values() if v is not None]
    if sets:
        vals.append(1)
        conn.execute(f"UPDATE user_profile SET {', '.join(sets)} WHERE id = ?", vals)
        conn.commit()
    conn.close()
