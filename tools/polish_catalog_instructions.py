"""Polish catalog Chinese instructions with the configured LLM and update SQLite."""

import json
import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from llm_client import LLMClient
from llm_config import LLMConfig

DB_PATH = os.path.join(ROOT, "assets", "catalog", "exercises.db")
BATCH_SIZE = 3


def parse_json_response(response):
    response = response.strip()
    if response.startswith("```"):
        response = response.split("\n", 1)[1].rsplit("```", 1)[0]
    start = response.find("[")
    end = response.rfind("]")
    if start < 0 or end < start:
        raise ValueError("LLM did not return a JSON array")
    return json.loads(response[start:end + 1])


def main():
    cfg = LLMConfig.load()
    if not cfg.is_configured:
        raise SystemExit("Configure the LLM in the app first")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    columns = {row[1] for row in conn.execute("PRAGMA table_info(exercise_catalog)")}
    if "instructions_polished" not in columns:
        conn.execute("ALTER TABLE exercise_catalog ADD COLUMN instructions_polished INTEGER NOT NULL DEFAULT 0")
        conn.commit()
    rows = conn.execute(
        "SELECT id, name_zh, name_en, instruction_steps_zh_json "
        "FROM exercise_catalog WHERE instructions_polished = 0 ORDER BY source_id").fetchall()
    client = LLMClient(
        api_key=cfg.api_key, api_base_url=cfg.api_base_url, model=cfg.model,
        temperature=0.2, max_tokens=4096, max_retries=cfg.max_retries,
        retry_base_delay=cfg.retry_base_delay, timeout=cfg.timeout)
    try:
        for offset in range(0, len(rows), BATCH_SIZE):
            batch = rows[offset:offset + BATCH_SIZE]
            payload = [{
                "id": row["id"], "name_zh": row["name_zh"], "name_en": row["name_en"],
                "steps": json.loads(row["instruction_steps_zh_json"]),
            } for row in batch]
            prompt = (
                "你是专业力量训练动作编辑。润色以下动作的中文步骤，要求准确、简洁、"
                "自然，不增加原文没有的训练效果或医学结论。每个步骤一句，保留关键姿势、"
                "轨迹、呼吸和安全提示。只返回JSON数组，格式为"
                "[{\"id\":\"...\",\"steps\":[\"...\"]}]。\n"
                + json.dumps(payload, ensure_ascii=False)
            )
            response = client.chat([
                {"role": "system", "content": "你只输出合法JSON，不输出Markdown。"},
                {"role": "user", "content": prompt},
            ], max_tokens=4096)["text"]
            try:
                polished = parse_json_response(response)
            except Exception:
                polished = []
                for item in payload:
                    single_prompt = (
                        "润色该力量训练动作的中文步骤。准确、简洁、自然，不增加医学结论。"
                        "只返回JSON对象：{\"id\":\"...\",\"steps\":[\"...\"]}。\n"
                        + json.dumps(item, ensure_ascii=False))
                    single = client.chat([
                        {"role": "system", "content": "只输出合法JSON对象。"},
                        {"role": "user", "content": single_prompt},
                    ], max_tokens=2048)["text"]
                    start, end = single.find("{"), single.rfind("}")
                    polished.append(json.loads(single[start:end + 1]))
            by_id = {item["id"]: item["steps"] for item in polished}
            for row in batch:
                steps = by_id.get(row["id"])
                if not isinstance(steps, list) or not steps:
                    raise ValueError(f"Missing polished steps for {row['id']}")
                conn.execute(
                    "UPDATE exercise_catalog SET instructions_zh = ?, "
                    "instruction_steps_zh_json = ?, instructions_polished = 1 WHERE id = ?",
                    ("\n".join(steps), json.dumps(steps, ensure_ascii=False), row["id"]))
            conn.commit()
            print(f"polished {min(offset + BATCH_SIZE, len(rows))}/{len(rows)}", flush=True)
    finally:
        client.close()
        conn.close()


if __name__ == "__main__":
    main()
