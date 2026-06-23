from __future__ import annotations

from pathlib import Path

import yaml


def load_config(path: str | Path) -> dict:
    config_path = Path(path).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("The MARC configuration must be a YAML mapping.")

    config["_config_path"] = config_path
    config["_base_dir"] = config_path.parent
    for section in ("input", "algorithms", "audit", "output"):
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")
    return config


def resolve_path(config: dict, value: str | Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (config["_base_dir"] / path).resolve()
