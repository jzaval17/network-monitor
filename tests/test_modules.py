"""Unit tests for network monitoring modules."""

import unittest
from unittest.mock import patch, MagicMock
import sqlite3
import tempfile
import os

from config import TestingConfig
from database.db import DatabaseManager
from modules.internet import InternetMonitor
from modules.router import RouterMonitor
from modules.public_ip import PublicIPMonitor
from modules.system_monitor import SystemMonitor


class TestDatabaseManager(unittest.TestCase):
    """Test database management."""

    def setUp(self):
        """Set up test database."""
        self.db_fd, self.db_path = tempfile.mkstemp()
        self.db = DatabaseManager(db_path=self.db_path)

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_database_initialization(self):
        """Test database schema creation."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = {row[0] for row in cursor.fetchall()}

            self.assertIn("events", tables)
            self.assertIn("devices", tables)
            self.assertIn("system_stats", tables)

    def test_log_event(self):
        """Test event logging."""
        event_id = self.db.log_event(
            "test_event",
            "Test message",
            "info"
        )
        self.assertIsNotNone(event_id)

        events = self.db.get_events()
        self.assertTrue(len(events) > 0)

    def test_add_device(self):
        """Test device addition."""
        device_id = self.db.add_device(
            "192.168.1.100",
            "aa:bb:cc:dd:ee:ff",
            "test-device"
        )
        self.assertIsNotNone(device_id)

        devices = self.db.get_devices(online_only=False)
        self.assertTrue(len(devices) > 0)

    def test_alert_cooldown(self):
        """Test alert cooldown mechanism."""
        self.db.mark_alert_cooldown("test_alert", 60)

        is_in_cooldown = self.db.is_alert_in_cooldown("test_alert")
        self.assertTrue(is_in_cooldown)


class TestInternetMonitor(unittest.TestCase):
    """Test internet monitoring."""

    @patch("modules.internet.requests.head")
    def test_connectivity_online(self, mock_head):
        """Test internet connectivity detection (online)."""
        mock_head.return_value.status_code = 200

        monitor = InternetMonitor()
        is_online, response_time, url = monitor.check_connectivity()

        self.assertTrue(is_online)
        self.assertGreater(response_time, 0)

    @patch("modules.internet.requests.head")
    def test_connectivity_offline(self, mock_head):
        """Test internet connectivity detection (offline)."""
        mock_head.side_effect = Exception("Connection failed")

        monitor = InternetMonitor()
        is_online, response_time, url = monitor.check_connectivity()

        self.assertFalse(is_online)


class TestSystemMonitor(unittest.TestCase):
    """Test system resource monitoring."""

    def test_cpu_stats(self):
        """Test CPU stats retrieval."""
        monitor = SystemMonitor()
        cpu_percent = monitor.get_cpu_stats()

        self.assertGreaterEqual(cpu_percent, 0)
        self.assertLessEqual(cpu_percent, 100)

    def test_memory_stats(self):
        """Test memory stats retrieval."""
        monitor = SystemMonitor()
        memory_stats = monitor.get_memory_stats()

        self.assertIn("percent", memory_stats)
        self.assertIn("available", memory_stats)
        self.assertIn("total", memory_stats)

    def test_disk_stats(self):
        """Test disk stats retrieval."""
        monitor = SystemMonitor()
        disk_percent = monitor.get_disk_stats()

        self.assertGreaterEqual(disk_percent, 0)
        self.assertLessEqual(disk_percent, 100)


class TestPublicIPMonitor(unittest.TestCase):
    """Test public IP monitoring."""

    @patch("modules.public_ip.requests.get")
    def test_get_public_ip(self, mock_get):
        """Test public IP retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ip": "203.0.113.42"}
        mock_get.return_value = mock_response

        monitor = PublicIPMonitor()
        ip = monitor.get_public_ip()

        self.assertEqual(ip, "203.0.113.42")


if __name__ == "__main__":
    unittest.main()
