# Network Monitor

A production-quality home network monitoring platform built with Python, Flask, and SQLite. Monitors internet connectivity, network devices, system resources, and sends Discord alerts.

## Features

### 🌐 Network Monitoring
- **Internet Connectivity**: Checks internet status every 60 seconds using multiple reliable endpoints
- **Router Availability**: Pings router/gateway to detect outages
- **Public IP Tracking**: Detects and logs public IP address changes
- **Device Discovery**: Automatically discovers and tracks devices on the network using ARP scanning
- **Bandwidth Monitoring**: Tracks network bandwidth usage

### 💻 System Monitoring
- **CPU Usage**: Real-time CPU utilization monitoring
- **Memory Usage**: RAM utilization tracking
- **Disk Usage**: Disk space monitoring
- **Uptime Statistics**: Calculates internet uptime percentages

### 🚨 Alerting System
- **Discord Integration**: Sends alerts to Discord webhooks
- **Smart Cooldowns**: Prevents alert spam with configurable cooldown timers
- **Multi-trigger Alerts**:
  - Internet outages
  - Router/gateway unavailability
  - Public IP changes
  - New devices discovered
  - Device disconnections
  - High CPU/memory usage

### 📊 Web Dashboard
- **Live Dashboard**: Status cards, resource readings, and recent events refresh every 30 seconds, with a Refresh now button and refresh-failure feedback
- **Clear Empty States**: Missing measurements show Waiting for data; internet latency is converted to milliseconds
- **Device Management**: View all discovered devices with IP/MAC addresses
- **Event Logging**: Complete event history with filtering
- **Statistics Charts**: 24-hour historical graphs for CPU, memory, disk usage
- **Uptime Tracking**: Internet uptime percentages

### 🔌 REST API
- `/api/status` - Current network status
- `/api/devices` - List all devices
- `/api/events` - Event log with filtering
- `/api/stats` - System statistics
- `/api/uptime` - Uptime percentages
- `/api/events/export` - Export events to CSV
- `/api/devices/search` - Search devices by IP/MAC

## Tech Stack

- **Backend**: Python 3.12+, Flask, SQLite
- **Monitoring**: psutil, requests, schedule
- **Network**: scapy, ARP scanning
- **Frontend**: Bootstrap 5, Chart.js
- **Containerization**: Docker, Docker Compose

## Installation

### System Requirements
- Python 3.12 or higher
- Linux, macOS, or Windows
- Administrator/sudo access (for ARP scanning)

### Local Setup

1. **Clone and navigate to project**
```bash
cd network-monitor
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure application**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run monitor (in one terminal)**
```bash
python monitor.py
```

6. **Run Flask app (in another terminal)**
```bash
python app.py
```

7. **Access dashboard**
Open http://localhost:5000 in your browser

## Docker Installation

### Using Docker Compose (Recommended)

1. **Create .env file**
```bash
cp .env.example .env
# Edit .env with your settings
```

2. **Build and run**
```bash
docker-compose up -d
```

3. **View logs**
```bash
docker-compose logs -f network-monitor
```

4. **Stop container**
```bash
docker-compose down
```

### Using Docker directly

```bash
docker build -t network-monitor .
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/network_monitor.db:/app/network_monitor.db \
  -e ROUTER_IP=192.168.1.1 \
  -e GATEWAY_IP=192.168.1.1 \
  --cap-add=NET_ADMIN \
  --restart unless-stopped \
  network-monitor
```

## Configuration

Edit `.env` file to customize:

```env
# Flask
FLASK_ENV=development
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here

# Monitoring Intervals (seconds)
MONITOR_INTERVAL=60
DEVICE_SCAN_INTERVAL=300

# Network Configuration
ROUTER_IP=192.168.1.1
GATEWAY_IP=192.168.1.1
INTERNET_CHECK_TIMEOUT=5
INTERNET_CHECK_URLS=https://www.google.com,https://www.cloudflare.com

# Discord Alerts
DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/YOUR/WEBHOOK/URL
DISCORD_ENABLED=False

# System Configuration
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=5000

# Alert Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
ALERT_COOLDOWN=300
```

### Discord Webhook Setup

1. Create a Discord server (if not already)
2. Create a channel for alerts
3. Right-click channel → Edit → Integrations → Webhooks
4. Create Webhook and copy URL
5. Paste URL in `.env` as `DISCORD_WEBHOOK_URL`
6. Set `DISCORD_ENABLED=True`

## Project Structure

```
network-monitor/
├── app.py                 # Flask application
├── monitor.py            # Monitoring scheduler
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose config
├── README.md            # This file
│
├── database/
│   ├── __init__.py
│   ├── schema.py        # Database schema
│   └── db.py            # Database management
│
├── modules/
│   ├── __init__.py
│   ├── internet.py      # Internet connectivity monitoring
│   ├── router.py        # Router availability monitoring
│   ├── public_ip.py     # Public IP change detection
│   ├── devices.py       # Device discovery (ARP scanning)
│   ├── bandwidth.py     # Bandwidth monitoring
│   ├── system_monitor.py # CPU/Memory/Disk monitoring
│   └── alerts.py        # Discord alerting system
│
├── templates/
│   ├── base.html        # Base template
│   ├── index.html       # Dashboard
│   ├── devices.html     # Devices page
│   ├── events.html      # Events log
│   ├── stats.html       # Statistics/charts
│   └── error.html       # Error page
│
├── static/
│   ├── css/
│   │   └── style.css    # Custom styles
│   └── js/
│       └── main.js      # Client-side JavaScript
│
├── logs/                # Application logs
└── tests/               # Unit and integration tests
```

## Database Schema

### Events Table
- `id` - Event ID
- `timestamp` - Event timestamp
- `event_type` - Type of event
- `message` - Event message
- `severity` - Severity level (info, warning, error, critical)
- `resolved` - Whether event is resolved

### Devices Table
- `id` - Device ID
- `ip_address` - Device IP address
- `mac_address` - Device MAC address
- `hostname` - Device hostname
- `first_seen` - First discovery timestamp
- `last_seen` - Last activity timestamp
- `online` - Current online status (1/0)
- `device_type` - Type of device
- `manufacturer` - Device manufacturer

### System Stats Table
- `id` - Record ID
- `timestamp` - Timestamp
- `cpu_percent` - CPU usage percentage
- `memory_percent` - Memory usage percentage
- `memory_available` - Available memory (bytes)
- `memory_total` - Total memory (bytes)
- `bytes_sent` - Network bytes sent
- `bytes_received` - Network bytes received
- `disk_percent` - Disk usage percentage

## API Usage Examples

### Get Current Status
```bash
curl http://localhost:5000/api/status
```

### Get All Devices
```bash
curl http://localhost:5000/api/devices
```

### Get Recent Events
```bash
curl http://localhost:5000/api/events?limit=50
```

### Get System Statistics (Last 24 Hours)
```bash
curl http://localhost:5000/api/stats?hours=24
```

### Search Devices
```bash
curl http://localhost:5000/api/devices/search?q=192.168.1
```

### Export Events to CSV
```bash
curl http://localhost:5000/api/events/export -o events.csv
```

## Monitoring Workflow

1. **Monitor Process** (`monitor.py`):
   - Runs scheduled monitoring tasks
   - Collects data from all monitoring modules
   - Stores data in SQLite database
   - Triggers alerts based on thresholds

2. **Flask Application** (`app.py`):
   - Serves web dashboard
   - Provides REST API endpoints
   - Displays historical data and charts
   - Allows event/device filtering and export

3. **Alert System**:
   - Monitors database for events
   - Sends Discord notifications based on alert types
   - Implements cooldown to prevent spam

## Troubleshooting

### Device Discovery Not Working
- Ensure running with administrator/sudo privileges
- Check if `arp-scan` or `arp` command is available
- Try pinging network addresses first: `ping 192.168.1.1`

### Discord Alerts Not Sending
- Verify webhook URL is correct
- Ensure `DISCORD_ENABLED=True`
- Check Discord webhook has permissions
- Review logs for detailed error messages

### High Memory Usage
- Device discovery scans can be memory-intensive
- Increase `DEVICE_SCAN_INTERVAL` if too frequent
- Limit historical data by archiving old events

### Port Already in Use
- Change `PORT` in `.env` file
- Or kill process using port 5000:
```bash
# Linux/macOS
lsof -ti:5000 | xargs kill -9

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

## Performance Optimization

### For Large Networks
1. Increase `DEVICE_SCAN_INTERVAL` (e.g., 600 seconds)
2. Reduce monitoring interval for non-critical metrics
3. Archive old events periodically

### For Low-Resource Systems
1. Increase all monitoring intervals
2. Disable device discovery if not needed
3. Reduce chart history retention

## Security Considerations

1. **Change SECRET_KEY** in production
2. **Secure Discord webhook URL** - Don't commit to repo
3. **Use strong passwords** if adding authentication
4. **Run behind reverse proxy** (nginx/Apache) in production
5. **Enable HTTPS** for remote access
6. **Restrict access** to trusted networks only

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or suggestions:
- Check existing GitHub issues
- Create a new GitHub issue
- Review documentation in README.md

## Roadmap

- [ ] Authentication/user accounts
- [ ] Mobile-responsive dashboard improvements
- [ ] Email alerting
- [ ] Slack integration
- [ ] Network topology visualization
- [ ] VPN monitoring
- [ ] Speed test integration
- [ ] Historical data export
- [ ] Custom alert rules
- [ ] Multi-network support

## Credits

Built with Python, Flask, Bootstrap 5, and Chart.js

### Dashboard regression checks

Run `python -m unittest tests.test_dashboard` and `node tests/test_dashboard_refresh.js`. Dashboard refresh displays the latest saved measurements; collection still runs separately through `monitor.py`.

## Discord notifications

Discord alerts are collected by `monitor.py` and delivered by a background worker.
The Flask dashboard alone does not send alerts. Existing SQLite databases receive
the additional delivery-state table automatically on the next start.

### Enable

In your local `.env`, set `DISCORD_ENABLED=True` and set `DISCORD_WEBHOOK_URL` to a
Discord incoming webhook for your chosen text channel. Keep the URL private. The
URL must use HTTPS on a Discord domain. A bot account is not needed. Restart
`monitor.py` after changing settings, and run only one monitor process per database.
Do not put the webhook URL in browser code or commit `.env`.

### Quiet defaults

| Behavior | Default |
| --- | --- |
| Internet/router outage and recovery | Two consecutive samples confirm each transition |
| CPU/memory warnings | Three consecutive high samples; one warning per ongoing episode |
| Resource recovery | Three samples below the threshold minus five percentage points; no recovery message |
| Repeated resource episodes | At least 30 minutes between warnings of the same kind |
| First device scan | Quiet baseline, remembered across restarts |
| New devices | Grouped by MAC address; changing IP does not announce a new device |
| Device disconnects | Off by default; optional alerts require two successful scans with the device absent |
| Message grouping | Wait 20 seconds, combine changes, summarize device bursts |
| Channel message frequency | At least five minutes between successful deliveries, including recoveries |
| Mentions and push alerts | No mentions, TTS, push, or desktop notifications by default |
| Offline queue | Persisted in SQLite; messages expire after 24 hours; device queue is bounded |

These settings are listed in `.env.example`. `DISCORD_SILENT=False` allows Discord
push/desktop notifications according to your channel settings; mentions remain
blocked. Set `DISCORD_DEVICE_ALERTS=False` to disable new-device notices. Leave
`DISCORD_DEVICE_DISCONNECT_ALERTS=False` for networks with sleeping/mobile devices.
With the default 60-second sampling interval, transient failures and brief resource
spikes do not notify. Collection time, batching, and the five-minute message limit
can delay notices; this is intentionally a quiet monitor, not instant paging.

When the internet is down, Discord may be unreachable. Failed sends are retried
with increasing delays, and rate limits honor Discord's `retry_after`. A confirmed
recovery replaces an undelivered outage notice with one duration summary. Duration
is approximate and includes confirmation time; monitoring gaps are not measured
uptime. Invalid/revoked webhooks pause delivery instead of retrying endlessly.
Transient send timeouts can rarely cause a duplicate if Discord accepted a message
but its response was lost; webhook delivery cannot guarantee exactly-once sending.
Changing the webhook starts fresh delivery state so the new channel does not receive
an old channel's backlog. Failed scans do not generate device-disconnection events.

### Check locally or request a test

From an activated project environment:

```bash
python discord_status.py
```

This prints enabled/disabled status, queue size, last successful delivery (Unix time),
next attempt time, and any delivery error without exposing the webhook. It makes no
network request. To explicitly queue one test message while `monitor.py` is running:

```bash
python discord_status.py --queue-test
```

The test follows the configured silent setting and normal batching/cooldowns. After
fixing a rejected webhook or channel permission, restart the monitor if `.env`
changed. If the URL is unchanged, resume paused delivery with:

```bash
python discord_status.py --reset-delivery
```

### Regression tests

The Discord tests use temporary SQLite databases, fake time, and mocked HTTP.
Collector wiring tests mock network scans and system measurements. With project
dependencies installed, run:

```bash
DISCORD_ENABLED=False python -m unittest tests.test_alerts tests.test_alert_wiring
```

Protocol references: [Discord incoming webhooks](https://discord.com/developers/docs/resources/webhook#execute-webhook),
[rate limits](https://discord.com/developers/docs/topics/rate-limits), and
[silent message flags](https://discord.com/developers/docs/resources/message#message-object-message-flags).
