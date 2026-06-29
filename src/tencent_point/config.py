"""配置加载"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG: dict[str, Any] = {
    "uid": 0,
    "year": 2026,
    "top_n": 50,
    "categories": [
        "云计算",
        "人工智能",
        "后端开发",
        "前端开发",
        "数据库",
        "DevOps",
    ],
    "posting_goal": {
        "articles_per_month": 4,
    },
    "api": {
        "timeout": 30,
        "max_retries": 3,
        "retry_delay": 2.0,
        "page_delay": 1.0,
    },
}


def _find_config() -> Path | None:
    """搜索配置文件路径"""
    candidates = [
        Path.cwd() / "config.yaml",
        Path.home() / ".tencent-point" / "config.yaml",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并两个字典，override 覆盖 base"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """加载配置文件，与默认值深度合并"""
    if path is not None:
        config_path = Path(path)
    else:
        config_path = _find_config()

    if config_path is None or not config_path.exists():
        return DEFAULT_CONFIG.copy()

    with open(config_path, "r", encoding="utf-8") as f:
        user_config = yaml.safe_load(f) or {}

    return _deep_merge(DEFAULT_CONFIG, user_config)
