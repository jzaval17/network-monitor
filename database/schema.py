"""Database schema for network monitoring application."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS discord_delivery_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    payload TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT DEFAULT 'info',
    resolved INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT UNIQUE NOT NULL,
    mac_address TEXT UNIQUE NOT NULL,
    hostname TEXT,
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    online INTEGER DEFAULT 1,
    device_type TEXT,
    manufacturer TEXT
);

CREATE TABLE IF NOT EXISTS system_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    cpu_percent REAL,
    memory_percent REAL,
    memory_available INTEGER,
    memory_total INTEGER,
    bytes_sent INTEGER,
    bytes_received INTEGER,
    disk_percent REAL
);

CREATE TABLE IF NOT EXISTS internet_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    response_time REAL,
    checked_url TEXT
);

CREATE TABLE IF NOT EXISTS public_ip_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT NOT NULL,
    changed INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS alert_cooldown (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT UNIQUE NOT NULL,
    last_triggered DATETIME DEFAULT CURRENT_TIMESTAMP,
    cooldown_until DATETIME
);

CREATE TABLE IF NOT EXISTS router_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL,
    response_time REAL
);

CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip_address);
CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address);
CREATE INDEX IF NOT EXISTS idx_system_stats_timestamp ON system_stats(timestamp);
CREATE INDEX IF NOT EXISTS idx_internet_status_timestamp ON internet_status(timestamp);
CREATE INDEX IF NOT EXISTS idx_public_ip_timestamp ON public_ip_history(timestamp);
"""
