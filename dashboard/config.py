"""YAML config loader and saver for default.yaml."""

from pathlib import Path

import yaml


def load_config(path: str | Path) -> dict:
    """Load default.yaml and return as a Python dict."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def save_config(data: dict, path: str | Path) -> None:
    """Write a Python dict back to default.yaml with clean formatting."""
    with open(path, "w") as f:
        yaml.dump(
            data,
            f,
            default_flow_style=False,
            indent=2,
            allow_unicode=True,
            sort_keys=False,
        )
