"""
ServerRegistry — YAML-backed registry for MCP server records.

Reads and writes MCPServer entries to a YAML file (matching the existing
default.yaml registry pattern). No database — the YAML file IS the store.
"""
from __future__ import annotations

import logging
from pathlib import Path

import yaml

from schema.paas.mcp import MCPServer

logger = logging.getLogger(__name__)


class ServerRegistry:
    """CRUD operations on the MCP server registry YAML file."""

    def __init__(self, file_path: str | Path) -> None:
        self._file_path = Path(file_path)
        self._servers: dict[str, MCPServer] = {}

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def load(self) -> None:
        """Load servers from the YAML file into memory."""
        if not self._file_path.exists():
            logger.info("Registry file %s not found, starting empty", self._file_path)
            self._servers = {}
            return

        data = yaml.safe_load(self._file_path.read_text()) or {}
        raw_servers: list[dict] = data.get("servers", [])
        self._servers = {}
        for raw in raw_servers:
            server = self._dict_to_server(raw)
            self._servers[server.id] = server
        logger.info("Loaded %d servers from %s", len(self._servers), self._file_path)

    def save(self) -> None:
        """Persist the current in-memory state to the YAML file."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"servers": [self._server_to_dict(s) for s in self._servers.values()]}
        self._file_path.write_text(yaml.dump(data, default_flow_style=False))
        logger.info("Saved %d servers to %s", len(self._servers), self._file_path)

    def get_server(self, server_id: str) -> MCPServer | None:
        return self._servers.get(server_id)

    def add_server(self, server: MCPServer) -> None:
        if server.id in self._servers:
            raise ValueError(f"Server '{server.id}' already registered")
        self._servers[server.id] = server

    def remove_server(self, server_id: str) -> None:
        if server_id not in self._servers:
            raise KeyError(f"Server '{server_id}' not found")
        del self._servers[server_id]

    def list_servers(self) -> list[MCPServer]:
        return list(self._servers.values())

    # ----------------------------------------------------------------
    # Serialization helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _dict_to_server(data: dict) -> MCPServer:
        return MCPServer(
            id=data["id"],
            name=data["name"],
            source_path=data["source_path"],
            entry_point=data.get("entry_point", "server:app"),
            runtime_config=data.get("runtime_config"),
            port=data["port"],
            health_url=data["health_url"],
            status=data.get("status", "stopped"),
            process_id=data.get("process_id"),
        )

    @staticmethod
    def _server_to_dict(server: MCPServer) -> dict:
        return {
            "id": server.id,
            "name": server.name,
            "source_path": server.source_path,
            "entry_point": server.entry_point,
            "runtime_config": server.runtime_config,
            "port": server.port,
            "health_url": server.health_url,
            "status": server.status,
            "process_id": server.process_id,
        }
