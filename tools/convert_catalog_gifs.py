"""Convert catalog GIFs to Kivy-safe JPEG frame sequences and update SQLite."""

import json
import os
import sqlite3

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "assets", "catalog")
DB_PATH = os.path.join(CATALOG, "exercises.db")


def main():
    conn = sqlite3.connect(DB_PATH)
    columns = {row[1] for row in conn.execute("PRAGMA table_info(exercise_catalog)")}
    if "animation_frames_json" not in columns:
        conn.execute(
            "ALTER TABLE exercise_catalog ADD COLUMN animation_frames_json "
            "TEXT NOT NULL DEFAULT '[]'"
        )
    if "animation_interval" not in columns:
        conn.execute(
            "ALTER TABLE exercise_catalog ADD COLUMN animation_interval "
            "REAL NOT NULL DEFAULT 0.12"
        )
    rows = conn.execute("SELECT id, source_id, gif_path FROM exercise_catalog").fetchall()
    for index, (exercise_id, source_id, gif_path) in enumerate(rows, 1):
        source = os.path.join(ROOT, gif_path.replace("/", os.sep))
        frame_dir = os.path.join(CATALOG, "frames", source_id)
        os.makedirs(frame_dir, exist_ok=True)
        frames = []
        durations = []
        with Image.open(source) as gif:
            for frame_index in range(gif.n_frames):
                gif.seek(frame_index)
                rgba = gif.convert("RGBA")
                background = Image.new("RGBA", rgba.size, "white")
                background.alpha_composite(rgba)
                relative = f"assets/catalog/frames/{source_id}/{frame_index:02d}.jpg"
                output = os.path.join(ROOT, relative.replace("/", os.sep))
                background.convert("RGB").save(output, "JPEG", quality=88, optimize=True)
                frames.append(relative)
                durations.append(max(40, int(gif.info.get("duration", 120))))
        interval = sum(durations) / len(durations) / 1000.0 if durations else 0.12
        conn.execute(
            "UPDATE exercise_catalog SET animation_frames_json = ?, "
            "animation_interval = ? WHERE id = ?",
            (json.dumps(frames), interval, exercise_id),
        )
        if index % 20 == 0:
            print(f"converted {index}/{len(rows)}", flush=True)
    conn.commit()
    conn.close()
    print(f"converted {len(rows)} animations", flush=True)


if __name__ == "__main__":
    main()
