"""System resource monitoring module."""

import logging
from typing import Dict

import psutil

from config import config
from database.db import db
from modules.alerts import alert_manager

logger = logging.getLogger(__name__)


class SystemMonitor:
    """Monitors system resources (CPU, memory, disk)."""

    def __init__(
        self,
        cpu_threshold: int = None,
        memory_threshold: int = None
    ) -> None:
        """
        Initialize system monitor.

        Args:
            cpu_threshold: CPU usage alert threshold (%)
            memory_threshold: Memory usage alert threshold (%)
        """
        self.cpu_threshold = cpu_threshold or config.CPU_THRESHOLD
        self.memory_threshold = memory_threshold or config.MEMORY_THRESHOLD
        self.last_cpu_alert: bool = False
        self.last_memory_alert: bool = False

    def get_cpu_stats(self) -> float:
        """
        Get CPU utilization percentage.

        Returns:
            CPU usage percentage (0-100)
        """
        try:
            return psutil.cpu_percent(interval=1)
        except Exception as e:
            logger.error(f"Failed to get CPU stats: {e}")
            return 0.0

    def get_memory_stats(self) -> Dict[str, int]:
        """
        Get memory statistics.

        Returns:
            Dictionary with memory stats
        """
        try:
            memory = psutil.virtual_memory()
            return {
                "percent": memory.percent,
                "available": memory.available,
                "total": memory.total,
            }
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            return {"percent": 0, "available": 0, "total": 0}

    def get_disk_stats(self) -> float:
        """
        Get disk utilization percentage.

        Returns:
            Disk usage percentage (0-100)
        """
        try:
            disk = psutil.disk_usage("/")
            return disk.percent
        except Exception as e:
            logger.error(f"Failed to get disk stats: {e}")
            return 0.0

    def get_network_stats(self) -> Dict[str, int]:
        """
        Get network statistics.

        Returns:
            Dictionary with network stats
        """
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_received": net_io.bytes_recv,
            }
        except Exception as e:
            logger.error(f"Failed to get network stats: {e}")
            return {"bytes_sent": 0, "bytes_received": 0}

    def monitor(self) -> None:
        """Monitor system resources and log statistics."""
        cpu_percent = self.get_cpu_stats()
        memory_stats = self.get_memory_stats()
        disk_percent = self.get_disk_stats()
        network_stats = self.get_network_stats()

        memory_percent = memory_stats.get("percent", 0)

        # Save statistics to database
        db.save_system_stats(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available=memory_stats.get("available"),
            memory_total=memory_stats.get("total"),
            bytes_sent=network_stats.get("bytes_sent"),
            bytes_received=network_stats.get("bytes_received"),
            disk_percent=disk_percent,
        )

        logger.debug(
            f"System stats - CPU: {cpu_percent}%, Memory: {memory_percent}%, "
            f"Disk: {disk_percent}%"
        )

        # Check thresholds and alert if needed
        self._check_cpu_threshold(cpu_percent)
        self._check_memory_threshold(memory_percent)
        alert_manager.observe_resources(cpu_percent, memory_percent)

    def _check_cpu_threshold(self, cpu_percent: float) -> None:
        """Check CPU threshold and alert if exceeded."""
        if cpu_percent > self.cpu_threshold and not self.last_cpu_alert:
            db.log_event(
                "high_cpu_usage",
                f"CPU usage is {cpu_percent}% (threshold: {self.cpu_threshold}%)",
                "warning"
            )
            self.last_cpu_alert = True
        elif cpu_percent <= self.cpu_threshold and self.last_cpu_alert:
            db.log_event(
                "cpu_usage_normal",
                f"CPU usage returned to normal: {cpu_percent}%",
                "info"
            )
            self.last_cpu_alert = False

    def _check_memory_threshold(self, memory_percent: float) -> None:
        """Check memory threshold and alert if exceeded."""
        if memory_percent > self.memory_threshold and not self.last_memory_alert:
            db.log_event(
                "high_memory_usage",
                f"Memory usage is {memory_percent}% (threshold: {self.memory_threshold}%)",
                "warning"
            )
            self.last_memory_alert = True
        elif memory_percent <= self.memory_threshold and self.last_memory_alert:
            db.log_event(
                "memory_usage_normal",
                f"Memory usage returned to normal: {memory_percent}%",
                "info"
            )
            self.last_memory_alert = False
