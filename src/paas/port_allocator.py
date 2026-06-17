"""
PortAllocator — manages port allocation in the configured range.

Tracks which server owns which port. Allocates the lowest available port.
Ports are released when a server is removed or stopped.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class PortAllocator:
    """Allocate and release ports from a configurable range."""

    def __init__(self, start_port: int = 8100, end_port: int = 8199) -> None:
        if start_port > end_port:
            raise ValueError(f"start_port ({start_port}) must be <= end_port ({end_port})")
        self._start_port = start_port
        self._end_port = end_port
        self._allocated: dict[str, int] = {}  # server_id -> port

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------

    def allocate(self, server_id: str) -> int:
        """Assign the lowest available port to a server.

        Raises RuntimeError if no ports are available.
        """
        if server_id in self._allocated:
            raise ValueError(f"Server '{server_id}' already has port {self._allocated[server_id]}")

        used_ports = set(self._allocated.values())
        for port in range(self._start_port, self._end_port + 1):
            if port not in used_ports:
                self._allocated[server_id] = port
                logger.info("Allocated port %d to server '%s'", port, server_id)
                return port

        raise RuntimeError(
            f"No available ports in range {self._start_port}-{self._end_port}"
        )

    def release(self, server_id: str) -> None:
        """Free the port assigned to a server."""
        if server_id not in self._allocated:
            raise KeyError(f"Server '{server_id}' has no allocated port")
        port = self._allocated.pop(server_id)
        logger.info("Released port %d from server '%s'", port, server_id)

    def is_allocated(self, port: int) -> bool:
        """Check whether a specific port is currently in use."""
        return port in self._allocated.values()

    def available_count(self) -> int:
        """Return how many ports are still free."""
        total = self._end_port - self._start_port + 1
        return total - len(self._allocated)
