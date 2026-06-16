"""FastAPI app that serves the config dashboard."""

import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import load_config, save_config

# Path to default.yaml (relative to project root)
CONFIG_PATH = Path(__file__).resolve().parent.parent / "default.yaml"
STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(title="Config Dashboard", version="0.1.0")

    # ---------- API routes ----------

    @app.get("/api/config")
    async def get_config():
        """Load default.yaml and return as JSON."""
        try:
            return load_config(CONFIG_PATH)
        except FileNotFoundError:
            raise HTTPException(404, "default.yaml not found")
        except Exception as e:
            raise HTTPException(500, f"Failed to load config: {e}")

    @app.post("/api/config")
    async def post_config(data: dict):
        """Validate and save config JSON back to default.yaml."""
        try:
            save_config(data, CONFIG_PATH)
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
