"""Network monitoring scheduler."""

import logging
import time
import signal
import sys

import schedule

from config import config
from modules.internet import InternetMonitor
from modules.router import RouterMonitor
from modules.public_ip import PublicIPMonitor
from modules.system_monitor import SystemMonitor
from modules.bandwidth import BandwidthMonitor
from modules.devices import DeviceDiscovery
from modules.alerts import alert_manager

logger = logging.getLogger(__name__)


class MonitorScheduler:
    """Schedules and runs monitoring tasks."""

    def __init__(self) -> None:
        """Initialize monitoring scheduler."""
        self.internet_monitor = InternetMonitor()
        self.router_monitor = RouterMonitor()
        self.public_ip_monitor = PublicIPMonitor()
        self.system_monitor = SystemMonitor()
        self.bandwidth_monitor = BandwidthMonitor()
        self.device_discovery = DeviceDiscovery()
        self.running = False

    def setup_schedule(self) -> None:
        """Setup monitoring tasks."""
        # Internet connectivity check
        schedule.every(config.MONITOR_INTERVAL).seconds.do(
            self._run_with_error_handling,
            self.internet_monitor.monitor,
            "Internet Monitor"
        )

        # Router availability check
        schedule.every(config.MONITOR_INTERVAL).seconds.do(
            self._run_with_error_handling,
            self.router_monitor.monitor,
            "Router Monitor"
        )

        # Public IP check
        schedule.every(config.MONITOR_INTERVAL * 5).seconds.do(
            self._run_with_error_handling,
            self.public_ip_monitor.monitor,
            "Public IP Monitor"
        )

        # System resource monitoring
        schedule.every(config.MONITOR_INTERVAL).seconds.do(
            self._run_with_error_handling,
            self.system_monitor.monitor,
            "System Monitor"
        )

        # Bandwidth monitoring
        schedule.every(config.MONITOR_INTERVAL).seconds.do(
            self._run_with_error_handling,
            self.bandwidth_monitor.monitor,
            "Bandwidth Monitor"
        )

        # Device discovery
        schedule.every(config.DEVICE_SCAN_INTERVAL).seconds.do(
            self._run_with_error_handling,
            self.device_discovery.monitor,
            "Device Discovery"
        )

        logger.info("Monitoring schedule setup completed")

    @staticmethod
    def _run_with_error_handling(func, name: str) -> None:
        """
        Run a function with error handling.

        Args:
            func: Function to run
            name: Function name for logging
        """
        try:
            func()
        except Exception as e:
            logger.error(f"{name} error: {e}", exc_info=True)

    def run(self) -> None:
        """Run the scheduler."""
        self.setup_schedule()
        self.running = True
        logger.info("Network Monitor started")

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

        try:
            alert_manager.start()
            while self.running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
        finally:
            alert_manager.stop()

    def _handle_shutdown(self, signum, frame) -> None:
        """Handle shutdown signal."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def stop(self) -> None:
        """Stop the scheduler."""
        self.running = False
        logger.info("Network Monitor stopped")
        sys.exit(0)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_DIR / "monitor.log"),
            logging.StreamHandler()
        ]
    )

    scheduler = MonitorScheduler()
    scheduler.run()
