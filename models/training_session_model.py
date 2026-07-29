"""Persistent timing for the current day's deployed training session."""

from datetime import datetime

from models.database import get_db


def start_today_training_session():
    today = datetime.now().date().isoformat()
    started_at = datetime.now().isoformat(timespec="seconds")
    conn = get_db()
    existing = conn.execute(
        "SELECT completed_at FROM training_sessions WHERE session_date = ?", (today,)
    ).fetchone()
    if existing and not existing["completed_at"]:
        # Redeploying edits today's plan without resetting the active session clock.
        conn.execute(
            "UPDATE training_sessions SET rest_plan_id = NULL, rest_started_at = NULL, "
            "rest_ends_at = NULL, rest_duration_seconds = NULL, rest_notified = 1 "
            "WHERE session_date = ?", (today,))
    else:
        conn.execute(
            "INSERT OR REPLACE INTO training_sessions "
            "(session_date, started_at, completed_at, duration_seconds, rest_notified) "
            "VALUES (?, ?, NULL, NULL, 1)",
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


def start_rest_timer(plan_id, duration_seconds):
    today = datetime.now().date().isoformat()
    started = datetime.now()
    duration = max(1, int(duration_seconds))
    ends = started.timestamp() + duration
    conn = get_db()
    cursor = conn.execute(
        "UPDATE training_sessions SET rest_plan_id = ?, rest_started_at = ?, "
        "rest_ends_at = ?, rest_duration_seconds = ?, rest_notified = 0 "
        "WHERE session_date = ?",
        (plan_id, started.isoformat(timespec="seconds"),
         datetime.fromtimestamp(ends).isoformat(timespec="seconds"), duration, today),
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def mark_rest_timer_notified():
    today = datetime.now().date().isoformat()
    conn = get_db()
    cursor = conn.execute(
        "UPDATE training_sessions SET rest_notified = 1 "
        "WHERE session_date = ? AND rest_notified = 0",
        (today,),
    )
    conn.commit()
    conn.close()
    return cursor.rowcount > 0


def cancel_rest_timer(plan_id=None):
    today = datetime.now().date().isoformat()
    conn = get_db()
    if plan_id is None:
        conn.execute(
            "UPDATE training_sessions SET rest_plan_id = NULL, rest_started_at = NULL, "
            "rest_ends_at = NULL, rest_duration_seconds = NULL, rest_notified = 1 "
            "WHERE session_date = ?", (today,))
    else:
        conn.execute(
            "UPDATE training_sessions SET rest_plan_id = NULL, rest_started_at = NULL, "
            "rest_ends_at = NULL, rest_duration_seconds = NULL, rest_notified = 1 "
            "WHERE session_date = ? AND rest_plan_id = ?", (today, plan_id))
    conn.commit()
    conn.close()
