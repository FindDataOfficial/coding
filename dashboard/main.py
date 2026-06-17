"""FastAPI app that serves the config dashboard."""

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import load_config, save_config
from .discovery import (
    annotate_rich_editor,
    discover_yaml_files,
    load_dashboard_config,
)

# Path to default.yaml (relative to project root)
CONFIG_PATH = Path(__file__).resolve().parent.parent / "default.yaml"
# Path to dashboard.yaml (controls which files are discovered)
DASHBOARD_CONFIG_PATH = Path(__file__).resolve().parent.parent / "dashboard.yaml"
STATIC_DIR = Path(__file__).resolve().parent / "static"

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_app(
    config_path: Path | None = None,
    dashboard_config_path: Path | None = None,
) -> FastAPI:
    _config_path = config_path or CONFIG_PATH
    _dashboard_config_path = dashboard_config_path or DASHBOARD_CONFIG_PATH

    # Discover files at startup
    dashboard_cfg = load_dashboard_config(_dashboard_config_path)
    scan_configs = dashboard_cfg.get("scan", [{"path": ".", "recursive": False}])
    rich_editor_name = dashboard_cfg.get("rich_editor", "default.yaml")

    discovered = discover_yaml_files(scan_configs, PROJECT_ROOT)
    discovered = annotate_rich_editor(discovered, rich_editor_name)

    # Build a name -> absolute path lookup
    file_map: dict[str, Path] = {f["name"]: Path(f["path"]) for f in discovered}

    app = FastAPI(title="Config Dashboard", version="0.2.0")

    # ---------- File discovery route ----------

    @app.get("/api/files")
    async def list_files():
        """Return all discovered YAML files with metadata."""
        return discovered

    # ---------- Per-file CRUD routes ----------

    @app.get("/api/files/{name:path}")
    async def get_file(name: str):
        """Load a specific YAML file and return as JSON."""
        if name not in file_map:
            raise HTTPException(404, f"File not found: {name}")
        try:
            return load_config(file_map[name])
        except FileNotFoundError:
            raise HTTPException(404, f"File not found on disk: {name}")
        except Exception as e:
            raise HTTPException(500, f"Failed to load file: {e}")

    @app.post("/api/files/{name:path}")
    async def post_file(name: str, data: dict):
        """Validate and save config JSON back to a specific YAML file."""
        if name not in file_map:
            raise HTTPException(404, f"File not found: {name}")
        try:
            save_config(data, file_map[name])
            return {"ok": True}
        except Exception as e:
            raise HTTPException(400, f"Failed to save file: {e}")

    # ---------- Backward-compat routes (resolve via rich_editor or CONFIG_PATH) ----------

    def _resolve_default_path() -> Path:
        """Resolve the default config file path.

        Tries the rich_editor file first (if it exists in file_map),
        then falls back to the hardcoded CONFIG_PATH.
        """
        if rich_editor_name in file_map:
            return file_map[rich_editor_name]
        return _config_path

    @app.get("/api/config")
    async def get_config():
        """Load the default config file and return as JSON."""
        default_path = _resolve_default_path()
        try:
            return load_config(default_path)
        except FileNotFoundError:
            raise HTTPException(404, f"{default_path.name} not found")
        except Exception as e:
            raise HTTPException(500, f"Failed to load config: {e}")

    @app.post("/api/config")
    async def post_config(data: dict):
        """Validate and save config JSON back to the default config file."""
        default_path = _resolve_default_path()
        try:
            save_config(data, default_path)
            return {"ok": True}
        except Exception as e:
            raise HTTPException(400, f"Failed to save config: {e}")

    # ---------- Static files (the single-page dashboard) ----------
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


app = create_app()


def serve():
    """Entry point: start the uvicorn server."""
    import uvicorn

    uvicorn.run("dashboard.main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        serve()
    else:
        print("Usage: python -m dashboard.main serve")
