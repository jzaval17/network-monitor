"""Network bandwidth monitoring module."""

import logging
from typing import Dict

import psutil

from database.db import db

logger = logging.getLogger(__name__)


class BandwidthMonitor:
    """Monitors network bandwidth usage."""

    def __init__(self) -> None:
        """Initialize bandwidth monitor."""
        self.last_bytes_sent = 0
        self.last_bytes_received = 0

    def get_bandwidth_usage(self) -> Dict[str, int]:
        """
        Get current bandwidth usage.

        Returns:
            Dictionary with bytes_sent and bytes_received
        """
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_received": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_received": net_io.packets_recv,
            }
        except Exception as e:
            logger.error(f"Failed to get bandwidth usage: {e}")
            return {
                "bytes_sent": 0,
                "bytes_received": 0,
                "packets_sent": 0,
                "packets_received": 0,
            }

    def get_bandwidth_delta(self) -> Dict[str, int]:
        """
        Get bandwidth usage since last check.

        Returns:
            Dictionary with delta values
        """
        current = self.get_bandwidth_usage()

        delta = {
            "bytes_sent": current["bytes_sent"] - self.last_bytes_sent,
            "bytes_received": current["bytes_received"] - self.last_bytes_received,
        }

        self.last_bytes_sent = current["bytes_sent"]
        self.last_bytes_received = current["bytes_received"]

        return delta

    def monitor(self) -> None:
        """Monitor bandwidth usage."""
        usage = self.get_bandwidth_usage()

        logger.debug(
            f"Bandwidth - Sent: {usage['bytes_sent']}, "
            f"Received: {usage['bytes_received']}"
        )

        # Store for later retrieval via API
        self.last_bytes_sent = usage["bytes_sent"]
        self.last_bytes_received = usage["bytes_received"]
