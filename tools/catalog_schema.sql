CREATE TABLE IF NOT EXISTS exercise_catalog (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,
    name_zh TEXT NOT NULL,
    name_en TEXT NOT NULL,
    item_type TEXT NOT NULL DEFAULT 'strength',
    body_part TEXT NOT NULL,
    equipment TEXT NOT NULL,
    target TEXT NOT NULL,
    muscle_group TEXT NOT NULL,
    secondary_muscles_json TEXT NOT NULL DEFAULT '[]',
    instructions_zh TEXT NOT NULL,
    instruction_steps_zh_json TEXT NOT NULL,
    thumbnail_path TEXT NOT NULL,
    gif_path TEXT NOT NULL,
    attribution TEXT NOT NULL DEFAULT '© Gym visual — https://gymvisual.com/',
    source_commit TEXT NOT NULL,
    instructions_polished INTEGER NOT NULL DEFAULT 0,
    animation_frames_json TEXT NOT NULL DEFAULT '[]',
    animation_interval REAL NOT NULL DEFAULT 0.12,
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_catalog_name_zh ON exercise_catalog(name_zh);
CREATE INDEX IF NOT EXISTS idx_catalog_body_part ON exercise_catalog(body_part);
CREATE INDEX IF NOT EXISTS idx_catalog_equipment ON exercise_catalog(equipment);

CREATE TABLE IF NOT EXISTS exercise_aliases (
    alias TEXT PRIMARY KEY,
    exercise_id TEXT NOT NULL,
    FOREIGN KEY(exercise_id) REFERENCES exercise_catalog(id)
);

-- Add a movement with stable media names:
-- 1. Put <source_id>.jpg in assets/catalog/thumbs/
-- 2. Put <source_id>.gif in assets/catalog/gifs/
-- 3. Run an INSERT such as:
-- INSERT INTO exercise_catalog (
--   id, source_id, name_zh, name_en, body_part, equipment, target,
--   muscle_group, instructions_zh, instruction_steps_zh_json,
--   thumbnail_path, gif_path, source_commit
-- ) VALUES (
--   'local-1001', '1001', '中文动作名', 'English exercise name',
--   'chest', 'dumbbell', 'pectorals', 'triceps',
--   '步骤一\n步骤二', '["步骤一", "步骤二"]',
--   'assets/catalog/thumbs/1001.jpg', 'assets/catalog/gifs/1001.gif', 'local'
-- );
