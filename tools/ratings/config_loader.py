"""Configuration loader for the ratings tooling."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PACKAGE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PACKAGE_DIR / "config.yaml"


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    """Load YAML configuration with package-relative defaults."""
    config_path = Path(path or DEFAULT_CONFIG_PATH)
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)

    package_dir = config_path.parent
    config["db_path"] = str((package_dir / config["db_path"]).resolve())
    config["roster_path"] = str((package_dir / config["roster_path"]).resolve())
    return config
