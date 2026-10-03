"""Network device discovery module using ARP scanning."""

import logging
import subprocess
import platform
import re
from typing import List, Dict, Tuple, Optional

from config import config
from database.db import db
from modules.alerts import alert_manager

logger = logging.getLogger(__name__)


class DeviceDiscovery:
    """Discovers devices on the local network."""

    def __init__(self, gateway_ip: str = None) -> None:
        """
        Initialize device discovery.

        Args:
            gateway_ip: Gateway/router IP address for network range detection
        """
        self.gateway_ip = gateway_ip or config.GATEWAY_IP
        self.known_devices: Dict[str, bool] = {}

    def get_network_range(self) -> str:
        """
        Determine network range from gateway IP.

        Returns:
            Network range in CIDR notation (e.g., "192.168.1.0/24")
        """
        parts = self.gateway_ip.split(".")
        if len(parts) == 4:
            return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        return "192.168.1.0/24"

    def scan_arp_windows(self) -> Optional[List[Dict[str, str]]]:
        """
        Scan network using ARP on Windows.

        Returns:
            List of device dictionaries with ip and mac
        """
        devices = []
        try:
            # First, ping the network range to populate ARP table
            network_range = self.get_network_range()
            base_ip = ".".join(network_range.split(".")[:-1])

            # Ping broadcast to populate ARP table
            for i in range(1, 255, 10):
                ping_ip = f"{base_ip}.{i}"
                try:
                    subprocess.run(
                        ["ping", "-n", "1", "-w", "100", ping_ip],
                        capture_output=True,
                        timeout=1
                    )
                except:
                    pass

            # Get ARP table
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return None

            # Parse ARP output
            lines = result.stdout.split("\n")
            for line in lines:
                match = re.search(
                    r"(\d+\.\d+\.\d+\.\d+)\s+([a-fA-F0-9\-]{17})",
                    line
                )
                if match:
                    ip = match.group(1)
                    mac = match.group(2).replace("-", ":")
                    devices.append({"ip": ip, "mac": mac})

        except Exception as e:
            logger.error(f"ARP scan failed on Windows: {e}")
            return None

        return devices

    def scan_arp_linux(self) -> Optional[List[Dict[str, str]]]:
        """
        Scan network using ARP on Linux.

        Returns:
            List of device dictionaries with ip and mac
        """
        devices = []
        try:
            network_range = self.get_network_range()

            # Use arp-scan if available
            try:
                result = subprocess.run(
                    ["arp-scan", "-l", "-q"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    return None
                lines = result.stdout.split("\n")
                for line in lines:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        ip = parts[0].strip()
                        mac = parts[1].strip()
                        if re.match(r"\d+\.\d+\.\d+\.\d+", ip):
                            devices.append({"ip": ip, "mac": mac})
            except FileNotFoundError:
                # Fallback to arp command
                result = subprocess.run(
                    ["arp", "-n"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    return None
                lines = result.stdout.split("\n")
                for line in lines:
                    match = re.search(
                        r"(\d+\.\d+\.\d+\.\d+).*?([a-fA-F0-9:]{17})",
                        line
                    )
                    if match:
                        ip = match.group(1)
                        mac = match.group(2)
                        devices.append({"ip": ip, "mac": mac})

        except Exception as e:
            logger.error(f"ARP scan failed on Linux: {e}")
            return None

        return devices

    def scan_network(self) -> Optional[List[Dict[str, str]]]:
        """
        Scan network for devices.

        Returns:
            List of discovered devices
        """
        system = platform.system().lower()

        if system == "windows":
            return self.scan_arp_windows()
        elif system in ["linux", "darwin"]:
            return self.scan_arp_linux()
        else:
            logger.warning(f"Unsupported OS for device discovery: {system}")
            return None

    def monitor(self) -> None:
        """Scan network and update device database."""
        devices = self.scan_network()
        if devices is None:
            logger.warning("Skipping device updates after an unsuccessful scan")
            return

        alert_manager.observe_devices(devices)

        logger.info(f"Discovered {len(devices)} devices on network")

        # Add/update devices in database
        for device in devices:
            ip = device.get("ip")
            mac = device.get("mac")

            if ip and mac:
                # Check if device is new
                was_known = ip in self.known_devices
                self.known_devices[ip] = True

                try:
                    db.add_device(ip, mac)

                    if not was_known:
                        logger.info(f"New device discovered: {ip} ({mac})")
                        db.log_event(
                            "device_discovered",
                            f"New device discovered: IP={ip}, MAC={mac}",
                            "info"
                        )
                except Exception as e:
                    logger.error(f"Failed to add device {ip}: {e}")

        # Check for devices that went offline
        current_ips = {d.get("ip") for d in devices}
        for known_ip in list(self.known_devices.keys()):
            if known_ip not in current_ips and self.known_devices.get(known_ip):
                logger.info(f"Device went offline: {known_ip}")
                db.update_device_online_status(known_ip, 0)
                db.log_event(
                    "device_disconnected",
                    f"Device went offline: {known_ip}",
                    "warning"
                )
                self.known_devices[known_ip] = False
