"""Flask web application for network monitoring dashboard."""

import logging
import csv
import io
from datetime import datetime, timedelta

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS

from config import config
from database.db import db

# Setup logging
logging.basicConfig(
    level=config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(config.LOG_DIR / "app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = config.SECRET_KEY
CORS(app)


@app.route("/")
@app.route("/dashboard/fragment")
def index():
    """Dashboard home page."""
    try:
        # Get current status
        internet_status = db.get_internet_status()
        router_status = db.get_router_status()
        public_ip = db.get_latest_public_ip()
        recent_stats = db.get_recent_stats(limit=1)
        devices = db.get_devices(online_only=False)
        recent_events = db.get_events(limit=10)

        # Calculate stats
        online_devices = len([d for d in devices if d["online"]])
        total_devices = len(devices)

        context = {
            "internet_status": internet_status,
            "router_status": router_status,
            "public_ip": public_ip,
            "current_stats": recent_stats[0] if recent_stats else None,
            "online_devices": online_devices,
            "total_devices": total_devices,
            "recent_events": recent_events,
        }

        template = "dashboard_content.html" if request.path == "/dashboard/fragment" else "index.html"
        return render_template(template, **context)
    except Exception as e:
        logger.error(f"Dashboard error: {e}", exc_info=True)
        return render_template("error.html", error=str(e)), 500


@app.route("/devices")
def devices_page():
    """Devices management page."""
    try:
        devices = db.get_devices(online_only=False)
        return render_template("devices.html", devices=devices)
    except Exception as e:
        logger.error(f"Devices page error: {e}", exc_info=True)
        return render_template("error.html", error=str(e)), 500


@app.route("/events")
def events_page():
    """Events log page."""
    try:
        page = request.args.get("page", 1, type=int)
        limit = 50
        offset = (page - 1) * limit

        query = """
            SELECT * FROM events
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        events = db.execute_query(query, (limit, offset))
        events = [dict(e) for e in events]

        return render_template("events.html", events=events, page=page)
    except Exception as e:
        logger.error(f"Events page error: {e}", exc_info=True)
        return render_template("error.html", error=str(e)), 500


@app.route("/stats")
def stats_page():
    """Statistics and charts page."""
    try:
        # Get last 24 hours of stats
        hours_ago = datetime.now() - timedelta(hours=24)
        query = """
            SELECT * FROM system_stats
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """
        stats = db.execute_query(query, (hours_ago,))
        stats = [dict(s) for s in stats]

        return render_template("stats.html", stats=stats)
    except Exception as e:
        logger.error(f"Stats page error: {e}", exc_info=True)
        return render_template("error.html", error=str(e)), 500


# API Endpoints

@app.route("/api/status")
def api_status():
    """Get current network status."""
    try:
        internet_status = db.get_internet_status()
        router_status = db.get_router_status()
        public_ip = db.get_latest_public_ip()
        recent_stats = db.get_recent_stats(limit=1)
        devices = db.get_devices(online_only=False)

        return jsonify({
            "internet": internet_status,
            "router": router_status,
            "public_ip": public_ip,
            "system_stats": recent_stats[0] if recent_stats else None,
            "devices": {
                "online": len([d for d in devices if d["online"]]),
                "total": len(devices),
            },
        })
    except Exception as e:
        logger.error(f"API status error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/devices")
def api_devices():
    """Get devices list."""
    try:
        online_only = request.args.get("online_only", "false").lower() == "true"
        devices = db.get_devices(online_only=online_only)

        # Convert to JSON-serializable format
        devices = [dict(d) for d in devices]

        return jsonify({
            "devices": devices,
            "count": len(devices),
        })
    except Exception as e:
        logger.error(f"API devices error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/events")
def api_events():
    """Get events with optional filtering."""
    try:
        limit = request.args.get("limit", 100, type=int)
        event_type = request.args.get("event_type")

        events = db.get_events(limit=limit, event_type=event_type)
        events = [dict(e) for e in events]

        return jsonify({
            "events": events,
            "count": len(events),
        })
    except Exception as e:
        logger.error(f"API events error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/stats")
def api_stats():
    """Get system statistics."""
    try:
        hours = request.args.get("hours", 24, type=int)
        hours_ago = datetime.now() - timedelta(hours=hours)

        query = """
            SELECT * FROM system_stats
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """
        stats = db.execute_query(query, (hours_ago,))
        stats = [dict(s) for s in stats]

        return jsonify({
            "stats": stats,
            "count": len(stats),
        })
    except Exception as e:
        logger.error(f"API stats error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/uptime")
def api_uptime():
    """Get uptime statistics."""
    try:
        # Calculate internet uptime (last 24 hours)
        hours_ago = datetime.now() - timedelta(hours=24)
        query = """
            SELECT COUNT(*) as total, 
                   SUM(CASE WHEN status = 'online' THEN 1 ELSE 0 END) as online
            FROM internet_status
            WHERE timestamp >= ?
        """
        result = db.execute_query(query, (hours_ago,), fetch_one=True)

        if result:
            total = result[0]
            online = result[1] or 0
            uptime_percent = (online / total * 100) if total > 0 else 0
        else:
            uptime_percent = 0

        return jsonify({
            "uptime_percent": uptime_percent,
            "last_24_hours": True,
        })
    except Exception as e:
        logger.error(f"API uptime error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/events/export")
def api_export_events():
    """Export events to CSV."""
    try:
        events = db.get_events(limit=10000)

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow(["Timestamp", "Type", "Message", "Severity"])

        # Write events
        for event in events:
            writer.writerow([
                event["timestamp"],
                event["event_type"],
                event["message"],
                event["severity"],
            ])

        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype="text/csv",
            as_attachment=True,
            download_name=f"events_{datetime.now().isoformat()}.csv"
        )
    except Exception as e:
        logger.error(f"API export error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/devices/search")
def api_search_devices():
    """Search devices by IP or MAC."""
    try:
        query = request.args.get("q", "").lower()

        if not query:
            return jsonify({"devices": []}), 400

        devices = db.get_devices(online_only=False)
        results = [
            dict(d) for d in devices
            if query in d.get("ip_address", "").lower()
            or query in d.get("mac_address", "").lower()
        ]

        return jsonify({
            "devices": results,
            "count": len(results),
        })
    except Exception as e:
        logger.error(f"API search error: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return render_template("error.html", error="Page not found"), 404


@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors."""
    return render_template("error.html", error="Internal server error"), 500


if __name__ == "__main__":
    logger.info(f"Starting Flask app on {config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
