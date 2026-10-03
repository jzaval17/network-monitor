"""Router/Gateway availability monitoring module."""

import logging
import subprocess
import platform
from typing import Tuple, Optional

from config import config
from database.db import db
from modules.alerts import alert_manager

logger = logging.getLogger(__name__)


class RouterMonitor:
    """Monitors router/gateway availability."""

    def __init__(self, router_ip: str = None) -> None:
        """
        Initialize router monitor.

        Args:
            router_ip: IP address of router/gateway
        """
        self.router_ip = router_ip or config.ROUTER_IP
        self.last_status: Optional[str] = None

    def ping_router(self) -> Tuple[bool, float]:
        """
        Ping router to check availability.

        Returns:
            Tuple of (is_reachable, response_time)
        """
        try:
            system = platform.system().lower()
            
            # Build ping command based on OS
            if system == "windows":
                cmd = ["ping", "-n", "1", "-w", "2000", self.router_ip]
            else:
                cmd = ["ping", "-c", "1", "-W", "2000", self.router_ip]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=5,
                text=True
            )

            if result.returncode == 0:
                # Try to extract response time
                response_time = self._extract_response_time(result.stdout, system)
                return True, response_time
            else:
                return False, 0.0

        except subprocess.TimeoutExpired:
            logger.warning(f"Router ping timed out for {self.router_ip}")
            return False, 0.0
        except Exception as e:
            logger.error(f"Failed to ping router: {e}")
            return False, 0.0

    @staticmethod
    def _extract_response_time(output: str, system: str) -> float:
        """
        Extract response time from ping output.

        Args:
            output: Ping command output
            system: Operating system name

        Returns:
            Response time in milliseconds
        """
        try:
            if system == "windows":
                # Windows format: "Reply from X: bytes=32 time=10ms TTL=64"
                if "time=" in output:
                    time_part = output.split("time=")[1].split("ms")[0]
                    return float(time_part)
            else:
                # Unix format: "time=10.5 ms"
                if "time=" in output:
                    time_part = output.split("time=")[1].split(" ")[0]
                    return float(time_part)
        except (ValueError, IndexError):
            pass

        return 0.0

    def monitor(self) -> None:
        """Monitor router availability and log status."""
        is_reachable, response_time = self.ping_router()
        status = "online" if is_reachable else "offline"

        # Log to database
        db.save_router_status(status, response_time)

        # Check if status changed
        if self.last_status and self.last_status != status:
            severity = "critical" if not is_reachable else "info"
            message = f"Router ({self.router_ip}) status changed to {status}"
            db.log_event("router_status_change", message, severity)

        self.last_status = status
        alert_manager.handle_router_status_change(is_reachable, self.router_ip)
