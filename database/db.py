"""Database management module for network monitoring application."""

import sqlite3
import logging
from typing import Any, List, Dict, Optional
from datetime import datetime
from contextlib import contextmanager
from config import config
from database.schema import SCHEMA_SQL

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations."""

    def __init__(self, db_path: str = None) -> None:
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or config.DATABASE_PATH
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database with schema."""
        try:
            with self.get_connection() as conn:
                conn.executescript(SCHEMA_SQL)
                conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    @contextmanager
    def get_connection(self) -> sqlite3.Connection:
        """
        Get database connection context manager.

        Yields:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(
        self, query: str, params: tuple = None, fetch_one: bool = False
    ) -> Any:
        """
        Execute a query.

        Args:
            query: SQL query string
            params: Query parameters
            fetch_one: If True, returns single row; otherwise returns all rows

        Returns:
            Query result
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                if "SELECT" in query.upper():
                    return cursor.fetchone() if fetch_one else cursor.fetchall()
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            logger.error(f"Database query failed: {e}")
            raise

    def log_event(self, event_type: str, message: str, severity: str = "info") -> int:
        """
        Log an event to database.

        Args:
            event_type: Type of event
            message: Event message
            severity: Event severity level (info, warning, error, critical)

        Returns:
            Event ID
        """
        query = """
            INSERT INTO events (event_type, message, severity, timestamp)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (event_type, message, severity))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to log event: {e}")
            raise

    def add_device(
        self,
        ip_address: str,
        mac_address: str,
        hostname: str = None,
        device_type: str = None,
        manufacturer: str = None,
    ) -> int:
        """
        Add or update device in database.

        Args:
            ip_address: Device IP address
            mac_address: Device MAC address
            hostname: Device hostname
            device_type: Type of device
            manufacturer: Device manufacturer

        Returns:
            Device ID
        """
        query = """
            INSERT OR REPLACE INTO devices
            (ip_address, mac_address, hostname, device_type, manufacturer, last_seen, online)
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP, 1)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (ip_address, mac_address, hostname, device_type, manufacturer),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to add device: {e}")
            raise

    def get_devices(self, online_only: bool = True) -> List[Dict]:
        """
        Get devices from database.

        Args:
            online_only: If True, only returns online devices

        Returns:
            List of device dictionaries
        """
        query = "SELECT * FROM devices"
        if online_only:
            query += " WHERE online = 1"
        query += " ORDER BY last_seen DESC"

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get devices: {e}")
            raise

    def update_device_online_status(self, ip_address: str, online: int) -> None:
        """
        Update device online status.

        Args:
            ip_address: Device IP address
            online: 1 for online, 0 for offline
        """
        query = """
            UPDATE devices
            SET online = ?, last_seen = CURRENT_TIMESTAMP
            WHERE ip_address = ?
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (online, ip_address))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update device status: {e}")
            raise

    def save_system_stats(
        self,
        cpu_percent: float,
        memory_percent: float,
        memory_available: int = None,
        memory_total: int = None,
        bytes_sent: int = None,
        bytes_received: int = None,
        disk_percent: float = None,
    ) -> int:
        """
        Save system statistics to database.

        Args:
            cpu_percent: CPU utilization percentage
            memory_percent: Memory utilization percentage
            memory_available: Available memory in bytes
            memory_total: Total memory in bytes
            bytes_sent: Bytes sent
            bytes_received: Bytes received
            disk_percent: Disk utilization percentage

        Returns:
            Stats ID
        """
        query = """
            INSERT INTO system_stats
            (timestamp, cpu_percent, memory_percent, memory_available, memory_total,
             bytes_sent, bytes_received, disk_percent)
            VALUES (CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    query,
                    (
                        cpu_percent,
                        memory_percent,
                        memory_available,
                        memory_total,
                        bytes_sent,
                        bytes_received,
                        disk_percent,
                    ),
                )
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to save system stats: {e}")
            raise

    def get_recent_stats(self, limit: int = 100) -> List[Dict]:
        """
        Get recent system statistics.

        Args:
            limit: Number of recent records to return

        Returns:
            List of stats dictionaries
        """
        query = """
            SELECT * FROM system_stats
            ORDER BY timestamp DESC
            LIMIT ?
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            raise

    def save_internet_status(
        self, status: str, response_time: float = None, checked_url: str = None
    ) -> int:
        """
        Save internet connectivity status.

        Args:
            status: Status (online/offline)
            response_time: Response time in seconds
            checked_url: URL that was checked

        Returns:
            Status record ID
        """
        query = """
            INSERT INTO internet_status (timestamp, status, response_time, checked_url)
            VALUES (CURRENT_TIMESTAMP, ?, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (status, response_time, checked_url))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to save internet status: {e}")
            raise

    def get_internet_status(self) -> Optional[Dict]:
        """
        Get latest internet status.

        Returns:
            Latest internet status record or None
        """
        query = """
            SELECT * FROM internet_status
            ORDER BY timestamp DESC
            LIMIT 1
        """
        try:
            result = self.execute_query(query, fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Failed to get internet status: {e}")
            raise

    def save_public_ip(self, ip_address: str, changed: int = 0) -> int:
        """
        Save public IP address.

        Args:
            ip_address: Public IP address
            changed: 1 if IP changed since last record, 0 otherwise

        Returns:
            Record ID
        """
        query = """
            INSERT INTO public_ip_history (timestamp, ip_address, changed)
            VALUES (CURRENT_TIMESTAMP, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (ip_address, changed))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to save public IP: {e}")
            raise

    def get_latest_public_ip(self) -> Optional[str]:
        """
        Get latest public IP address.

        Returns:
            Latest public IP address or None
        """
        query = """
            SELECT ip_address FROM public_ip_history
            ORDER BY timestamp DESC
            LIMIT 1
        """
        try:
            result = self.execute_query(query, fetch_one=True)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Failed to get public IP: {e}")
            raise

    def get_events(
        self, limit: int = 100, event_type: str = None
    ) -> List[Dict]:
        """
        Get events from database.

        Args:
            limit: Number of events to return
            event_type: Filter by event type

        Returns:
            List of event dictionaries
        """
        query = "SELECT * FROM events"
        params = []
        if event_type:
            query += " WHERE event_type = ?"
            params.append(event_type)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            raise

    def mark_alert_cooldown(self, alert_type: str, cooldown_seconds: int) -> None:
        """
        Mark an alert as in cooldown.

        Args:
            alert_type: Type of alert
            cooldown_seconds: Cooldown duration in seconds
        """
        query = """
            INSERT OR REPLACE INTO alert_cooldown
            (alert_type, last_triggered, cooldown_until)
            VALUES (?, CURRENT_TIMESTAMP, datetime('now', '+' || ? || ' seconds'))
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (alert_type, cooldown_seconds))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to mark alert cooldown: {e}")
            raise

    def is_alert_in_cooldown(self, alert_type: str) -> bool:
        """
        Check if alert is in cooldown period.

        Args:
            alert_type: Type of alert

        Returns:
            True if in cooldown, False otherwise
        """
        query = """
            SELECT * FROM alert_cooldown
            WHERE alert_type = ? AND cooldown_until > CURRENT_TIMESTAMP
        """
        try:
            result = self.execute_query(query, (alert_type,), fetch_one=True)
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to check alert cooldown: {e}")
            raise

    def save_router_status(self, status: str, response_time: float = None) -> int:
        """
        Save router connectivity status.

        Args:
            status: Status (online/offline)
            response_time: Response time in seconds

        Returns:
            Status record ID
        """
        query = """
            INSERT INTO router_status (timestamp, status, response_time)
            VALUES (CURRENT_TIMESTAMP, ?, ?)
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (status, response_time))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to save router status: {e}")
            raise

    def get_router_status(self) -> Optional[Dict]:
        """
        Get latest router status.

        Returns:
            Latest router status record or None
        """
        query = """
            SELECT * FROM router_status
            ORDER BY timestamp DESC
            LIMIT 1
        """
        try:
            result = self.execute_query(query, fetch_one=True)
            return dict(result) if result else None
        except Exception as e:
            logger.error(f"Failed to get router status: {e}")
            raise


# Global database instance
db = DatabaseManager()
