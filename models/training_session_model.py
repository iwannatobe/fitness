"""Persistent timing for the current day's deployed training session."""

from datetime import datetime

from models.database import get_db


def start_today_training_session():
    today = datetime.now().date().isoformat()
    started_at = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    conn.execute(
        "INSERT OR REPLACE INTO training_sessions "
        "(session_date, started_at, completed_at, duration_seconds) VALUES (?, ?, NULL, NULL)",
        (today, started_at),
    )
    conn.commit()
    conn.close()


def finish_today_training_session_if_complete():
    today = datetime.now().date().isoformat()
    conn = get_db()
    session = conn.execute(
        "SELECT started_at, completed_at FROM training_sessions WHERE session_date = ?", (today,)
    ).fetchone()
    if not session or session["completed_at"]:
        conn.close()
        return False
    remaining = conn.execute(
        "SELECT COUNT(*) FROM daily_plan WHERE plan_date = ? AND completed = 0", (today,)
    ).fetchone()[0]
    if remaining:
        conn.close()
        return False
    completed_at = datetime.now()
    started_at = datetime.fromisoformat(session["started_at"])
    duration = max(0, round((completed_at - started_at).total_seconds()))
    conn.execute(
        "UPDATE training_sessions SET completed_at = ?, duration_seconds = ? WHERE session_date = ?",
        (completed_at.isoformat(timespec="seconds"), duration, today),
    )
    conn.commit()
    conn.close()
    return True


def get_today_training_session():
    today = datetime.now().date().isoformat()
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM training_sessions WHERE session_date = ?", (today,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
