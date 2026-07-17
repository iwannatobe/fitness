"""LLM 配置：API key / base url / model，持久化到 JSON。

跨平台配置目录：Android 用 app 私有目录，桌面用 ~/.fitnessapp。
"""

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

APP_NAME = "fitnessapp"


def _config_dir() -> Path:
    if "ANDROID_APP_PATH" in os.environ:
        d = Path(os.environ["ANDROID_APP_PATH"]) / "config"
    else:
        d = Path.home() / f".{APP_NAME}"
    d.mkdir(parents=True, exist_ok=True)
    return d


CONFIG_FILE = _config_dir() / "llm.json"


@dataclass
class LLMConfig:
    api_key: str = ""
    api_base_url: str = "https://api.deepseek.com"
    model: str = "deepseek-v4-flash"
    temperature: float = 0.3
    max_tokens: int = 1024
    max_retries: int = 3
    retry_base_delay: float = 2.0
    timeout: float = 60.0
    system_prompt: str = "你是一个健身助手，回答简洁有用，中文回复。你可以接收并分析用户发送的图片（食物照片、训练动作等）和语音录音。"

    @classmethod
    def load(cls) -> "LLMConfig":
        if not CONFIG_FILE.exists():
            return cls()
        try:
            raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return cls()
        valid = {k: v for k, v in raw.items() if k in cls.__dataclass_fields__}
        cfg = cls(**valid)
        _OLD_PROMPT = "你是一个健身助手，回答简洁有用，中文回复。"
        if cfg.system_prompt == _OLD_PROMPT:
            cfg.system_prompt = cls().system_prompt
            cfg.save()
        return cfg

    def save(self) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".json.tmp")
        tmp.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp, CONFIG_FILE)

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_base_url and self.model)
