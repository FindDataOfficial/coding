"""
ServerRouter — FastAPI router that exposes the PAAS API.

Endpoints:
    GET  /api/servers          — list all registered servers
    GET  /api/servers/{id}     — get one server
    POST /api/servers          — register and deploy a new server
    POST /api/servers/{id}/start  — start a server
    POST /api/servers/{id}/stop   — stop a server
    GET  /api/servers/{id}/logs   — get server logs
    GET  /api/servers/{id}/health — get health status
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException

from schema.paas.mcp import MCPServer
from src.paas.lifecycle import LifecycleManager
from src.paas.nginx_config import NginxConfigManager
from src.paas.registry import ServerRegistry

logger = logging.getLogger(__name__)


class ServerRouter:
    """FastAPI router for the MCP PAAS dashboard API."""

    def __init__(
        self,
        registry: ServerRegistry,
        lifecycle: LifecycleManager,
        nginx_manager: NginxConfigManager,
    ) -> None:
        self._registry = registry
        self._lifecycle = lifecycle
        self._nginx = nginx_manager
        self.router = APIRouter(prefix="/api")
        self._register_routes()

    # ----------------------------------------------------------------
    # Route registration
    # ----------------------------------------------------------------

    def _register_routes(self) -> None:
        router = self.router

        @router.get("/servers")
        def list_servers() -> list[dict[str, Any]]:
            servers = self._registry.list_servers()
            return [self._server_to_dict(s) for s in servers]

        @router.get("/servers/{server_id}")
        def get_server(server_id: str) -> dict[str, Any]:
            server = self._registry.get_server(server_id)
            if server is None:
                raise HTTPException(status_code=404, detail=f"Server '{server_id}' not found")
            return self._server_to_dict(server)

        @router.post("/servers", status_code=201)
        def deploy_server(config: dict[str, Any]) -> dict[str, Any]:
            server = MCPServer(
                id=config["id"],
                name=config["name"],
                source_path=config["source_path"],
                entry_point=config.get("entry_point", "server:app"),
                runtime_config=config.get("runtime_config"),
                port=config.get("port", 0),  # 0 means auto-allocate
                health_url=config["health_url"],
                status="stopped",
                process_id=None,
            )
            self._registry.add_server(server)
            self._registry.save()
            self._lifecycle.start_server(server.id)
            self._nginx.generate_config(server.id)
            self._nginx.reload()
            self._registry.save()
            logger.info("Deployed server '%s'", server.id)
            return self._server_to_dict(server)

        @router.post("/servers/{server_id}/start")
        def start_server(server_id: str) -> dict[str, str]:
            try:
                self._lifecycle.start_server(server_id)
                self._registry.save()
                return {"status": "started", "server_id": server_id}
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except RuntimeError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

        @router.post("/servers/{server_id}/stop")
        def stop_server(server_id: str) -> dict[str, str]:
            try:
                self._lifecycle.stop_server(server_id)
                self._registry.save()
                return {"status": "stopped", "server_id": server_id}
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            except RuntimeError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc

        @router.get("/servers/{server_id}/logs")
        def get_logs(server_id: str) -> dict[str, str]:
            try:
                logs = self._lifecycle.collect_logs(server_id)
                return {"server_id": server_id, "logs": logs}
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc

        @router.get("/servers/{server_id}/health")
        def get_health(server_id: str) -> dict[str, Any]:
            try:
                status = self._lifecycle.check_health(server_id)
                return {
                    "server_id": server_id,
                    "healthy": status.healthy,
                    "status_code": status.status_code,
                    "response_time_ms": status.response_time_ms,
                    "error": status.error,
                    "last_checked": status.last_checked,
                }
            except KeyError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc

    # ----------------------------------------------------------------
    # Serialization
    # ----------------------------------------------------------------

    @staticmethod
    def _server_to_dict(server: MCPServer) -> dict[str, Any]:
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
