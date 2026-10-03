"""Public IP address monitoring module."""

import logging
from ipaddress import ip_address
from typing import Optional

import requests

from database.db import db
from modules.alerts import alert_manager

logger = logging.getLogger(__name__)


class PublicIPMonitor:
    """Monitors public IP address changes."""

    # Multiple public IP detection services for redundancy
    IP_CHECK_SERVICES = [
        "https://api.ipify.org?format=json",
        "https://checkip.amazonaws.com",
        "https://icanhazip.com",
        "https://ifconfig.me",
    ]

    def __init__(self, timeout: int = 5) -> None:
        """
        Initialize public IP monitor.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.last_ip: Optional[str] = None

    def get_public_ip(self) -> Optional[str]:
        """
        Get current public IP address.

        Returns:
            Public IP address or None if unable to determine
        """
        for service in self.IP_CHECK_SERVICES:
            try:
                response = requests.get(service, timeout=self.timeout)
                response.raise_for_status()
                if "ipify" in service:
                    candidate = response.json().get("ip")
                else:
                    candidate = response.text.strip()
                return str(ip_address(candidate))
            except (requests.RequestException, ValueError, TypeError, AttributeError) as e:
                logger.debug(f"Failed to get IP from {service}: {e}")
                continue

        logger.warning("Unable to determine public IP address")
        return None

    def monitor(self) -> None:
        """Monitor public IP and detect changes."""
        current_ip = self.get_public_ip()

        if not current_ip:
            logger.warning("Could not determine public IP")
            return

        # Get last known IP from database
        if not self.last_ip:
            self.last_ip = db.get_latest_public_ip()

        changed = 0
        if self.last_ip and self.last_ip != current_ip:
            changed = 1
            logger.warning(f"Public IP changed from {self.last_ip} to {current_ip}")
            db.log_event(
                "public_ip_change",
                f"Public IP changed from {self.last_ip} to {current_ip}",
                "warning"
            )

        # Save current IP
        db.save_public_ip(current_ip, changed)
        if changed:
            alert_manager.handle_public_ip_change(self.last_ip, current_ip)
        self.last_ip = current_ip
