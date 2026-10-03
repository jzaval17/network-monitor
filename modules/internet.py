"""Internet connectivity monitoring module."""

import logging
import time
from typing import Tuple, Optional
import requests

from config import config
from database.db import db
from modules.alerts import alert_manager

logger = logging.getLogger(__name__)


class InternetMonitor:
    """Monitors internet connectivity."""

    def __init__(self, check_urls: list = None, timeout: int = None) -> None:
        """
        Initialize internet monitor.

        Args:
            check_urls: List of URLs to check for connectivity
            timeout: Request timeout in seconds
        """
        self.check_urls = check_urls or config.INTERNET_CHECK_URLS
        self.timeout = timeout or config.INTERNET_CHECK_TIMEOUT
        self.last_status: Optional[str] = None

    def check_connectivity(self) -> Tuple[bool, float, str]:
        """
        Check internet connectivity.

        Returns:
            Tuple of (is_online, response_time, checked_url)
        """
        for url in self.check_urls:
            try:
                start = time.time()
                response = requests.head(url, timeout=self.timeout, allow_redirects=True)
                response_time = time.time() - start

                if response.status_code < 400:
                    logger.info(f"Internet is online (checked {url})")
                    return True, response_time, url
            except requests.RequestException as e:
                logger.debug(f"Failed to reach {url}: {e}")
                continue

        logger.warning("Internet appears to be offline")
        return False, 0.0, self.check_urls[0] if self.check_urls else ""

    def monitor(self) -> None:
        """Monitor internet connectivity and log status."""
        is_online, response_time, checked_url = self.check_connectivity()
        status = "online" if is_online else "offline"

        # Log to database
        db.save_internet_status(status, response_time, checked_url)

        # Check if status changed
        if self.last_status and self.last_status != status:
            severity = "critical" if not is_online else "info"
            message = f"Internet status changed to {status}"
            db.log_event("internet_status_change", message, severity)

        self.last_status = status
        alert_manager.handle_internet_status_change(is_online)
