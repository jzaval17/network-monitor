"""Configuration management for network monitoring application."""

import os
from typing import List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent


class Config:
    """Base configuration."""

    # Flask
    DEBUG = False
    TESTING = False
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-key-change-in-production")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")

    # Database
    DATABASE_PATH = os.getenv("DATABASE_PATH", str(PROJECT_ROOT / "network_monitor.db"))
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

    # Monitoring intervals (seconds)
    MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "60"))
    DEVICE_SCAN_INTERVAL = int(os.getenv("DEVICE_SCAN_INTERVAL", "300"))

    # Network configuration
    ROUTER_IP = os.getenv("ROUTER_IP", "192.168.1.1")
    GATEWAY_IP = os.getenv("GATEWAY_IP", "192.168.1.1")
    INTERNET_CHECK_TIMEOUT = int(os.getenv("INTERNET_CHECK_TIMEOUT", "5"))

    # Internet check URLs
    INTERNET_CHECK_URLS: List[str] = [
        url.strip()
        for url in os.getenv(
            "INTERNET_CHECK_URLS", "https://www.google.com,https://www.cloudflare.com"
        ).split(",")
    ]

    # Alerting
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
    DISCORD_ENABLED = os.getenv("DISCORD_ENABLED", "False").lower() == "true"
    ALERT_COOLDOWN = int(os.getenv("ALERT_COOLDOWN", "300"))
    DISCORD_CONFIRM_CHECKS = max(2, int(os.getenv("DISCORD_CONFIRM_CHECKS", "2")))
    DISCORD_RESOURCE_CHECKS = max(2, int(os.getenv("DISCORD_RESOURCE_CHECKS", "3")))
    DISCORD_RESOURCE_COOLDOWN = max(300, int(os.getenv("DISCORD_RESOURCE_COOLDOWN", "1800")))
    DISCORD_MIN_INTERVAL = max(30, int(os.getenv("DISCORD_MIN_INTERVAL", "300")))
    DISCORD_BATCH_SECONDS = max(5, int(os.getenv("DISCORD_BATCH_SECONDS", "20")))
    DISCORD_MAX_AGE_SECONDS = max(300, int(os.getenv("DISCORD_MAX_AGE_SECONDS", "86400")))
    DISCORD_SILENT = os.getenv("DISCORD_SILENT", "True").lower() == "true"
    DISCORD_DEVICE_ALERTS = os.getenv("DISCORD_DEVICE_ALERTS", "True").lower() == "true"
    DISCORD_DEVICE_DISCONNECT_ALERTS = os.getenv("DISCORD_DEVICE_DISCONNECT_ALERTS", "False").lower() == "true"

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = PROJECT_ROOT / "logs"

    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "5000"))

    # Thresholds
    CPU_THRESHOLD = int(os.getenv("CPU_THRESHOLD", "80"))
    MEMORY_THRESHOLD = int(os.getenv("MEMORY_THRESHOLD", "85"))

    @classmethod
    def init_app(cls) -> None:
        """Initialize application configuration."""
        # Create logs directory if it doesn't exist
        cls.LOG_DIR.mkdir(exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Testing configuration."""

    DEBUG = True
    TESTING = True
    DATABASE_PATH = ":memory:"
    DISCORD_ENABLED = False
    LOGGER_ENABLED = False


# Select configuration based on environment
ENV = os.getenv("FLASK_ENV", "development")
if ENV == "production":
    config = ProductionConfig()
elif ENV == "testing":
    config = TestingConfig()
else:
    config = DevelopmentConfig()

config.init_app()
