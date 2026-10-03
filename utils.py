"""Utility functions and helpers."""

import csv
import json
from pathlib import Path
from typing import List, Dict
from database.db import db


def export_events_to_csv(filename: str, limit: int = None) -> None:
    """
    Export events to CSV file.

    Args:
        filename: Output CSV filename
        limit: Maximum number of events to export
    """
    events = db.get_events(limit=limit or 10000)

    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "timestamp", "event_type", "message", "severity"]
        )
        writer.writeheader()

        for event in events:
            writer.writerow(dict(event))

    print(f"Exported {len(events)} events to {filename}")


def export_devices_to_json(filename: str) -> None:
    """
    Export devices to JSON file.

    Args:
        filename: Output JSON filename
    """
    devices = db.get_devices(online_only=False)

    with open(filename, "w") as f:
        json.dump([dict(d) for d in devices], f, indent=2, default=str)

    print(f"Exported {len(devices)} devices to {filename}")


def cleanup_old_events(days: int = 30) -> int:
    """
    Delete events older than specified days.

    Args:
        days: Number of days to keep

    Returns:
        Number of events deleted
    """
    query = """
        DELETE FROM events
        WHERE timestamp < datetime('now', '-' || ? || ' days')
    """
    try:
        count = db.execute_query(query, (days,))
        print(f"Deleted {count} old events")
        return count
    except Exception as e:
        print(f"Error cleaning up events: {e}")
        return 0


def get_database_stats() -> Dict:
    """
    Get database statistics.

    Returns:
        Dictionary with database stats
    """
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Count records in each table
        stats = {}
        for table in ["events", "devices", "system_stats", "internet_status"]:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            stats[table] = cursor.fetchone()[0]

        # Get database size
        db_path = Path(db.db_path)
        stats["database_size_mb"] = db_path.stat().st_size / (1024 * 1024)

        return stats


def print_status_summary() -> None:
    """Print current network status summary."""
    internet_status = db.get_internet_status()
    router_status = db.get_router_status()
    public_ip = db.get_latest_public_ip()
    devices = db.get_devices(online_only=False)
    recent_stats = db.get_recent_stats(limit=1)

    print("\n" + "=" * 50)
    print("NETWORK MONITOR STATUS SUMMARY")
    print("=" * 50)

    if internet_status:
        print(f"Internet: {internet_status['status'].upper()}")
        if internet_status['response_time']:
            print(f"  Response Time: {internet_status['response_time']:.2f}ms")

    if router_status:
        print(f"Router: {router_status['status'].upper()}")
        if router_status['response_time']:
            print(f"  Response Time: {router_status['response_time']:.2f}ms")

    print(f"Public IP: {public_ip or 'Unknown'}")

    online_count = len([d for d in devices if d["online"]])
    print(f"Devices: {online_count}/{len(devices)} online")

    if recent_stats:
        stat = recent_stats[0]
        print(f"System Stats:")
        print(f"  CPU: {stat['cpu_percent']:.1f}%")
        print(f"  Memory: {stat['memory_percent']:.1f}%")
        print(f"  Disk: {stat['disk_percent']:.1f}%")

    print("=" * 50 + "\n")
