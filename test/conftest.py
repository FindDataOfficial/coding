"""Shared test fixtures."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Ensure dashboard package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def temp_yaml_path():
    """Create a temporary YAML file with sample config data."""
    content = {
        "models": {
            "default": "claude-sonnet",
            "providers": {
                "anthropic": {"api_key_env": "ANTHROPIC_API_KEY", "base_url": "https://api.anthropic.com"},
                "openai": {"api_key_env": "OPENAI_API_KEY", "base_url": "https://api.openai.com/v1"},
            },
            "registry": [
                {"id": "claude-sonnet", "provider": "anthropic", "name": "claude-sonnet-4-6", "max_tokens": 4096, "temperature": 0.7},
                {"id": "gpt-4o", "provider": "openai", "name": "gpt-4o", "max_tokens": 4096, "temperature": 0.7},
            ],
        },
        "databases": {
            "default": "sqlite-dev",
            "registry": [
                {"id": "sqlite-dev", "driver": "sqlite", "url": "sqlite:///data/dev.db", "pool": {"min_size": 1, "max_size": 5, "timeout_seconds": 30}, "auto_migrate": True},
                {"id": "postgres-prod", "driver": "postgresql", "url_env": "DATABASE_URL", "pool": {"min_size": 5, "max_size": 50, "timeout_seconds": 60}, "ssl_mode": "require", "auto_migrate": False},
            ],
        },
        "logging": {"level": "info", "format": "json", "output": "stderr"},
        "runtime": {"workers": 4, "request_timeout": 60, "shutdown_timeout": 30},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        import yaml
        yaml.dump(content, f, default_flow_style=False, indent=2, allow_unicode=True, sort_keys=False)
        tmp_path = f.name

    yield tmp_path

    # Cleanup
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)


@pytest.fixture
def client(temp_yaml_path, monkeypatch):
    """Create a FastAPI TestClient pointing at the temp YAML."""
    from dashboard.main import create_app

    # Override CONFIG_PATH in the main module
    import dashboard.main as main_mod
    monkeypatch.setattr(main_mod, "CONFIG_PATH", Path(temp_yaml_path))

    app = create_app()
    from fastapi.testclient import TestClient
    return TestClient(app)
