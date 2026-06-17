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


@pytest.fixture
def multi_file_env(tmp_path, monkeypatch):
    """Create a temp directory with multiple YAML files and a dashboard.yaml.

    Directory structure:
        tmp_path/
        ├── dashboard.yaml
        ├── default.yaml          (rich editor target)
        ├── extra/
        │   └── settings.yaml
        ├── save/
        │   ├── agents.yaml
        │   └── workflows.yaml
        └── nested/
            └── deep/
                └── config.yaml

    Returns a dict with:
        - client: TestClient configured for the multi-file env
        - root: Path to the temp project root
        - dashboard_yaml: Path to the dashboard.yaml
    """
    import yaml
    from dashboard.main import create_app
    from fastapi.testclient import TestClient

    root = tmp_path / "project"
    root.mkdir()

    # --- Create YAML files ---

    # default.yaml (rich editor target)
    default_content = {
        "models": {
            "default": "test-model",
            "default_model_high": "test-model",
            "default_model_middle": "test-model",
            "default_model_low": "test-model",
            "providers": {
                "test-provider": {"api_key_env": "TEST_KEY", "base_url": "https://test.example.com"},
            },
            "registry": [
                {"id": "test-model", "provider": "test-provider", "name": "test-model-1", "max_tokens": 4096, "temperature": 0.7},
            ],
        },
        "databases": {
            "default": "test-db",
            "registry": [
                {"id": "test-db", "driver": "sqlite", "url": "sqlite:///test.db", "pool": {"min_size": 1, "max_size": 5, "timeout_seconds": 30}, "auto_migrate": True},
            ],
        },
    }
    _write_yaml(root / "default.yaml", default_content)

    # extra/settings.yaml (non-rich, flat directory)
    extra_dir = root / "extra"
    extra_dir.mkdir()
    _write_yaml(extra_dir / "settings.yaml", {"theme": "dark", "language": "en"})

    # save/agents.yaml (non-rich)
    save_dir = root / "save"
    save_dir.mkdir()
    _write_yaml(save_dir / "agents.yaml", {"agents": {"default": "helper", "registry": [{"id": "helper", "type": "general"}]}})

    # save/workflows.yaml (non-rich)
    _write_yaml(save_dir / "workflows.yaml", {"workflows": {"default": "build", "registry": [{"id": "build", "steps": 3}]}})

    # nested/deep/config.yaml (recursive scan test)
    nested_dir = root / "nested" / "deep"
    nested_dir.mkdir(parents=True)
    _write_yaml(nested_dir / "config.yaml", {"nested": True, "value": 42})

    # A .txt file that should be ignored
    (extra_dir / "notes.txt").write_text("hello")

    # A .json file that should be ignored
    (extra_dir / "data.json").write_text('{"a": 1}')

    # --- Create dashboard.yaml ---
    dashboard_yaml = root / "dashboard.yaml"
    dashboard_cfg = {
        "scan": [
            {"path": ".", "recursive": False},
            {"path": "extra", "recursive": False},
            {"path": "save", "recursive": False},
            {"path": "nested", "recursive": True},
        ],
        "rich_editor": "default.yaml",
    }
    _write_yaml(dashboard_yaml, dashboard_cfg)

    # --- Override paths in main module ---
    import dashboard.main as main_mod

    monkeypatch.setattr(main_mod, "PROJECT_ROOT", root)
    monkeypatch.setattr(main_mod, "DASHBOARD_CONFIG_PATH", dashboard_yaml)
    monkeypatch.setattr(main_mod, "CONFIG_PATH", root / "default.yaml")

    app = create_app()
    tc = TestClient(app)

    return {
        "client": tc,
        "root": root,
        "dashboard_yaml": dashboard_yaml,
    }


def _write_yaml(path, data):
    """Helper: write a dict as a YAML file."""
    import yaml
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, indent=2, allow_unicode=True, sort_keys=False)
