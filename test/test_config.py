"""Tests for dashboard/config.py."""

import json
import os
import tempfile

import yaml

from dashboard.config import load_config, save_config


def test_load_config(temp_yaml_path):
    """load_config should read YAML and return a Python dict."""
    data = load_config(temp_yaml_path)
    assert isinstance(data, dict)
    assert "models" in data
    assert "databases" in data
    assert data["models"]["default"] == "claude-sonnet"


def test_save_config_creates_file():
    """save_config should write a valid YAML file."""
    data = {
        "models": {
            "default": "test-model",
            "providers": {"test": {"api_key_env": "KEY"}},
            "registry": [{"id": "test-model", "provider": "test", "name": "test-1", "max_tokens": 100, "temperature": 0.5}],
        },
        "databases": {
            "default": "test-db",
            "registry": [{"id": "test-db", "driver": "sqlite", "url": "sqlite:///test.db"}],
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        tmp_path = f.name

    try:
        save_config(data, tmp_path)

        # Verify file exists and is valid YAML
        assert os.path.exists(tmp_path)
        with open(tmp_path, "r") as f:
            loaded = yaml.safe_load(f)

        assert loaded["models"]["default"] == "test-model"
        assert loaded["databases"]["default"] == "test-db"
        assert len(loaded["models"]["registry"]) == 1
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_round_trip_preserves_structure(temp_yaml_path):
    """Loading and saving should preserve the logical structure."""
    original = load_config(temp_yaml_path)
    save_config(original, temp_yaml_path)
    reloaded = load_config(temp_yaml_path)

    assert reloaded["models"]["default"] == original["models"]["default"]
    assert len(reloaded["models"]["registry"]) == len(original["models"]["registry"])
    assert reloaded["databases"]["default"] == original["databases"]["default"]


def test_save_config_with_nested_pool():
    """save_config should handle nested pool dicts in databases."""
    data = {
        "databases": {
            "default": "db1",
            "registry": [
                {"id": "db1", "driver": "postgresql", "url": "postgresql://localhost/db",
                 "pool": {"min_size": 2, "max_size": 10, "timeout_seconds": 30},
                 "ssl_mode": "require", "auto_migrate": False},
            ],
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        tmp_path = f.name

    try:
        save_config(data, tmp_path)
        loaded = load_config(tmp_path)
        pool = loaded["databases"]["registry"][0]["pool"]
        assert pool["min_size"] == 2
        assert pool["max_size"] == 10
        assert loaded["databases"]["registry"][0]["ssl_mode"] == "require"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
