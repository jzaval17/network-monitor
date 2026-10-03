# 🚀 COMMANDS QUICK REFERENCE

## Ubuntu/WSL - One Command to Start Everything

```bash
cd /path/to/network-monitor && bash launch-ubuntu.sh
```

Then open: **http://localhost:5000**

---

## Manual Start (Two Terminals)

### Terminal 1: Monitor Process
```bash
cd /path/to/network-monitor
python3 monitor.py
```

### Terminal 2: Flask Dashboard
```bash
cd /path/to/network-monitor
python3 app.py
```

---

## Docker Deployment

```bash
cd /path/to/network-monitor
docker-compose up -d
```

Stop:
```bash
docker-compose down
```

View logs:
```bash
docker-compose logs -f
```

---

## API Testing

```bash
# Get status
curl http://localhost:5000/api/status | python3 -m json.tool

# Get devices
curl http://localhost:5000/api/devices | python3 -m json.tool

# Get recent events
curl "http://localhost:5000/api/events?limit=10" | python3 -m json.tool

# Get stats (24 hours)
curl "http://localhost:5000/api/stats?hours=24" | python3 -m json.tool

# Get uptime
curl http://localhost:5000/api/uptime | python3 -m json.tool

# Search devices
curl "http://localhost:5000/api/devices/search?q=192.168" | python3 -m json.tool

# Export events to CSV
curl http://localhost:5000/api/events/export > events.csv
```

---

## Configuration

Edit .env:
```bash
nano .env
```

Key settings:
```env
ROUTER_IP=192.168.1.1
GATEWAY_IP=192.168.1.1
DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/YOUR/URL
DISCORD_ENABLED=False
```

---

## Utilities

### View Current Status
```bash
python3 -c "from utils import print_status_summary; print_status_summary()"
```

### Get Database Stats
```bash
python3 -c "from utils import get_database_stats; import json; print(json.dumps(get_database_stats(), indent=2))"
```

### Export Events
```bash
python3 -c "from utils import export_events_to_csv; export_events_to_csv('events.csv')"
```

### Export Devices
```bash
python3 -c "from utils import export_devices_to_json; export_devices_to_json('devices.json')"
```

### Cleanup Old Events (30+ days)
```bash
python3 -c "from utils import cleanup_old_events; cleanup_old_events(30)"
```

---

## Testing

Run all tests:
```bash
python3 -m pytest tests/ -v
```

Run specific test:
```bash
python3 -m pytest tests/test_modules.py -v
```

With coverage:
```bash
python3 -m pytest tests/ --cov=modules --cov=database
```

---

## Logs

Monitor logs:
```bash
tail -f logs/monitor.log
```

Flask logs:
```bash
tail -f logs/app.log
```

Both together:
```bash
tail -f logs/*.log
```

---

## Process Management

Find process on port 5000:
```bash
lsof -i :5000
```

Kill process:
```bash
kill -9 <PID>
```

Kill all Python monitors:
```bash
pkill -f "python3 monitor.py"
pkill -f "python3 app.py"
```

---

## Database

Query devices:
```bash
python3 << 'EOF'
from database.db import db
for device in db.get_devices():
    print(f"{device['ip_address']} - {device['mac_address']} - {device['online']}")
EOF
```

Query recent events:
```bash
python3 << 'EOF'
from database.db import db
import json
events = db.get_events(limit=5)
print(json.dumps([dict(e) for e in events], indent=2, default=str))
EOF
```

Reset database:
```bash
rm network_monitor.db
# It will recreate on next run
```

---

## Installation

Install dependencies:
```bash
pip3 install -r requirements.txt
```

Install specific package:
```bash
pip3 install flask==3.0.0
```

Upgrade all packages:
```bash
pip3 install --upgrade -r requirements.txt
```

---

## Troubleshooting

Check Python version:
```bash
python3 --version
```

List installed packages:
```bash
pip3 list
```

Check if ARP works:
```bash
which arp
arp -a
```

Test internet connectivity:
```bash
curl -I https://www.google.com
```

Test Discord webhook:
```bash
curl -X POST https://discordapp.com/api/webhooks/YOUR/URL \
  -H "Content-Type: application/json" \
  -d '{"content":"Test message"}'
```

---

## Network Configuration

Find your router IP:
```bash
ip route | grep default
# or
route -n | grep default
```

Get your machine's IP:
```bash
hostname -I
# or
ip addr show
```

Get public IP:
```bash
curl https://api.ipify.org
```

Scan network (if installed):
```bash
arp-scan -l
```

---

## System Info

Check CPU usage:
```bash
top -bn1 | head -n 3
```

Check memory:
```bash
free -h
```

Check disk:
```bash
df -h
```

Monitor network:
```bash
iftop
# or
nethogs
```

---

## Advanced

Run monitor with verbose logging:
```bash
LOGLEVEL=DEBUG python3 monitor.py
```

Run Flask in debug mode:
```bash
FLASK_ENV=development FLASK_DEBUG=True python3 app.py
```

Run specific monitor module:
```bash
python3 << 'EOF'
from modules.internet import InternetMonitor
monitor = InternetMonitor()
is_online, response_time, url = monitor.check_connectivity()
print(f"Online: {is_online}, Response: {response_time}ms, URL: {url}")
EOF
```

---

## Backup

Backup database:
```bash
cp network_monitor.db network_monitor.db.backup
```

Backup logs:
```bash
tar -czf logs_backup.tar.gz logs/
```

Backup entire project:
```bash
tar -czf network-monitor_backup.tar.gz \
  --exclude=logs \
  --exclude=network_monitor.db \
  --exclude=__pycache__ \
  /path/to/network-monitor
```

---

## Useful One-Liners

Monitor network changes in real-time:
```bash
watch -n 5 'python3 -c "from utils import print_status_summary; print_status_summary()"'
```

Get device count:
```bash
python3 -c "from database.db import db; print(len(db.get_devices()))"
```

Get event count:
```bash
python3 -c "from database.db import db; print(len(db.get_events(limit=10000)))"
```

Start everything in one line:
```bash
python3 monitor.py & python3 app.py
```

Stop everything:
```bash
pkill -f "python3 monitor.py"; pkill -f "python3 app.py"
```

---

For more information, see:
- **README.md** - Full documentation
- **QUICKSTART.md** - Quick start guide
- **UBUNTU_LAUNCH.md** - Ubuntu instructions
