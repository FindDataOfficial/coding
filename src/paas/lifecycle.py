"""
LifecycleManager — manages MCP server processes (start, stop, restart, status),
health checks, and log collection.

Uses subprocess for MVP. Docker support is handled by DockerDeployer (separate).
"""
from __future__ import annotations

import logging
import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import requests

from src.paas.port_allocator import PortAllocator
from src.paas.registry import ServerRegistry

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    healthy: bool
    status_code: int | None = None
    response_time_ms: float | None = None
    error: str | None = None
    last_checked: float = field(default_factory=time.time)


class LifecycleManager:
    """Process lifecycle, health polling, and log collection for MCP servers."""

    def __init__(
        self,
        registry: ServerRegistry,
        port_allocator: PortAllocator,
        check_interval: int = 30,
        log_dir: str | Path = "logs",
    ) -> None:
        self._registry = registry
        self._port_allocator = port_allocator
        self._check_interval = check_interval
        self._log_dir = Path(log_dir)
        self._running: dict[str, subprocess.Popen] = {}  # server_id -> process
        self._log_files: dict[str, Path] = {}             # server_id -> log path

    # ----------------------------------------------------------------
    # Process lifecycle
    # ----------------------------------------------------------------

    def start_server(self, server_id: str) -> None:
        """Start an MCP server as a subprocess."""
        server = self._registry.get_server(server_id)
        if server is None:
            raise KeyError(f"Server '{server_id}' not found in registry")

        if server_id in self._running:
            raise RuntimeError(f"Server '{server_id}' is already running")

        port = self._port_allocator.allocate(server_id)

        log_path = self._log_dir / f"{server_id}.log"
        self._log_dir.mkdir(parents=True, exist_ok=True)
        log_file = open(str(log_path), "a")

        cmd = [
            "uvicorn",
            f"{server.entry_point}",
            "--host", "0.0.0.0",
            "--port", str(port),
        ]

        env = os.environ.copy()
        env["PORT"] = str(port)

        process = subprocess.Popen(
            cmd,
            cwd=server.source_path,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # isolate process group for clean shutdown
        )

        self._running[server_id] = process
        self._log_files[server_id] = log_path
        server.status = "running"
        server.process_id = process.pid
        logger.info("Started server '%s' (pid=%d, port=%d)", server_id, process.pid, port)

    def stop_server(self, server_id: str) -> None:
        """Gracefully stop a running MCP server."""
        if server_id not in self._running:
            raise RuntimeError(f"Server '{server_id}' is not running")

        process = self._running.pop(server_id)
        server = self._registry.get_server(server_id)
        if server:
            server.status = "stopped"
            server.process_id = None

        try:
            # Send SIGTERM to the entire process group
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            logger.warning("Server '%s' did not stop gracefully, force-killing", server_id)
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            process.wait()
        except ProcessLookupError:
            pass  # already dead

        self._port_allocator.release(server_id)
        logger.info("Stopped server '%s'", server_id)

    def restart_server(self, server_id: str) -> None:
        """Restart a running MCP server."""
        self.stop_server(server_id)
        time.sleep(1)  # brief cooldown for port release
        self.start_server(server_id)

    def get_status(self, server_id: str) -> str:
        """Return the current status of a server (running/stopped/error)."""
        server = self._registry.get_server(server_id)
        if server is None:
            raise KeyError(f"Server '{server_id}' not found")
        return server.status

    # ----------------------------------------------------------------
    # Health checks
    # ----------------------------------------------------------------

    def check_health(self, server_id: str) -> HealthStatus:
        """Poll a server's health endpoint and return its status."""
        server = self._registry.get_server(server_id)
        if server is None:
            raise KeyError(f"Server '{server_id}' not found")

        start = time.monotonic()
        try:
            resp = requests.get(server.health_url, timeout=5)
            elapsed = (time.monotonic() - start) * 1000
            return HealthStatus(
                healthy=resp.status_code == 200,
                status_code=resp.status_code,
                response_time_ms=round(elapsed, 2),
                last_checked=time.time(),
            )
        except requests.RequestException as exc:
            return HealthStatus(
                healthy=False,
                error=str(exc),
                last_checked=time.time(),
            )

    def start_health_polling(self) -> None:
        """Begin periodic health polling for all running servers.

        In the MVP this is a placeholder — full polling requires a background
        thread or asyncio task. Callers should invoke check_health() per server
        on their own schedule (e.g., via a cron or FastAPI background task).
        """
        logger.info(
            "Health polling configured (interval=%ds). "
            "Use check_health() per server for MVP.",
            self._check_interval,
        )

    def stop_health_polling(self) -> None:
        """Stop periodic health polling (no-op in MVP)."""
        logger.info("Health polling stopped")

    # ----------------------------------------------------------------
    # Log collection
    # ----------------------------------------------------------------

    def collect_logs(self, server_id: str) -> str:
        """Return the collected logs for a server."""
        log_path = self._log_files.get(server_id)
        if log_path is None or not log_path.exists():
            return ""
        return log_path.read_text()
