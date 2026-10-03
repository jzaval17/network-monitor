# QUICK START GUIDE - Network Monitor

## ⚡ 5-Minute Setup

### On Windows (WSL/Ubuntu Terminal)

```bash
# 1. Navigate to project
cd /path/to/network-monitor

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Configure settings (edit this file)
nano .env

# 4. Start everything
python3 -c "
import subprocess
import time
# Start monitor in background
subprocess.Popen(['python3', 'monitor.py'])
time.sleep(2)
# Start Flask app
subprocess.run(['python3', 'app.py'])
"
```

Or use the quick script:
```bash
bash run.sh
```

### On macOS/Linux

```bash
# Navigate to project
cd network-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or: . venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
nano .env  # Edit with your settings

# Terminal 1: Start monitor
python3 monitor.py

# Terminal 2: Start Flask app
python3 app.py

# Open dashboard
open http://localhost:5000
```

---

## 🔧 Configuration

Edit `.env` with your network details:

```env
ROUTER_IP=192.168.1.1          # Your router's IP
GATEWAY_IP=192.168.1.1         # Your gateway IP
MONITOR_INTERVAL=60            # Check every 60 seconds
DEVICE_SCAN_INTERVAL=300       # Scan devices every 5 minutes
```

### Optional: Discord Alerts

```env
DISCORD_ENABLED=True
DISCORD_WEBHOOK_URL=https://discordapp.com/api/webhooks/YOUR_ID/TOKEN
```

To get webhook URL:
1. Go to your Discord server
2. Select #channel → Edit → Integrations → Webhooks
3. Create Webhook and copy the URL

---

## 🚀 Running the Application

### Option 1: Two Terminals (Recommended)

**Terminal 1 - Monitor Process:**
```bash
python3 monitor.py
```
Expected output:
```
2024-01-15 10:30:45 - monitor - INFO - Network Monitor started
2024-01-15 10:31:05 - internet - INFO - Internet is online
2024-01-15 10:31:15 - router - INFO - Router is online
```

**Terminal 2 - Flask Dashboard:**
```bash
python3 app.py
```
Expected output:
```
WARNING in app.run(): This is a development server.
Running on http://0.0.0.0:5000
```

Then open: **http://localhost:5000**

### Option 2: Single Terminal (Background)

```bash
# Start monitor in background
nohup python3 monitor.py > logs/monitor.log 2>&1 &

# Start Flask app (foreground)
python3 app.py
```

### Option 3: Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 📊 Dashboard Features

### Home Page
- Internet Status (🟢 Online / 🔴 Offline)
- Router Status
- Public IP Address
- Connected Devices Count
- CPU/Memory/Disk Usage
- Recent Events

### Pages
- **Devices**: View all discovered devices with IP/MAC addresses
- **Events**: Complete event log with filtering and export to CSV
- **Stats**: Historical charts (CPU, Memory, Disk usage over 24 hours)

### API Endpoints
```bash
# Get current status
curl http://localhost:5000/api/status

# Get devices
curl http://localhost:5000/api/devices

# Export events to CSV
curl http://localhost:5000/api/events/export > events.csv

# Search devices by IP
curl "http://localhost:5000/api/devices/search?q=192.168"
```

---

## 🔍 Monitoring What Happens

### Monitor Process Checks:
1. **Internet Connectivity** - Pings Google, Cloudflare every 60s
2. **Router/Gateway** - Pings router every 60s
3. **Public IP** - Detects IP changes every 5 minutes
4. **System Resources** - CPU/Memory/Disk every 60s
5. **Network Devices** - Scans network via ARP every 5 minutes
6. **Events** - Logs all changes to database

### Log Files
```bash
# Monitor logs
tail -f logs/monitor.log

# Flask app logs
tail -f logs/app.log

# Database
ls -lh network_monitor.db
```

---

## 🚨 Alert Types

When configured with Discord, you'll get alerts for:

- 🔴 **Internet Outage** - Lost connectivity
- 🟢 **Internet Restored** - Connection restored
- 🔴 **Router Outage** - Router unreachable
- ➕ **New Device** - Device joined network
- ➖ **Device Disconnected** - Device left network
- ⚠️ **High CPU** - CPU > 80%
- ⚠️ **High Memory** - Memory > 85%
- 🔄 **IP Changed** - Public IP changed

---

## 📱 First Run Checklist

- [ ] Edit `.env` with your ROUTER_IP
- [ ] Run `python3 monitor.py`
- [ ] Run `python3 app.py` (in another terminal)
- [ ] Open http://localhost:5000
- [ ] Verify dashboard shows data
- [ ] Check "Recent Events" tab
- [ ] View discovered devices in "Devices" tab
- [ ] Optional: Configure Discord webhook for alerts

---

## ⚠️ Troubleshooting

### Port Already in Use
```bash
# Find process on port 5000
lsof -i :5000

# Kill it
kill -9 <PID>
```

### Module Import Errors
```bash
# Reinstall dependencies
pip3 install --upgrade -r requirements.txt
```

### Database Locked
```bash
# Remove old database
rm network_monitor.db

# Restart application (it will recreate)
python3 monitor.py
```

### Device Discovery Not Working
```bash
# Check if arp command is available
which arp

# On Ubuntu
sudo apt-get install iputils-ping net-tools arp-scan
```

---

## 📈 Next Steps

1. **Set up Discord alerts** - Get notified of issues
2. **Configure email alerts** - Check `modules/alerts.py`
3. **Adjust monitoring intervals** - Customize `.env`
4. **Archive old data** - Run `python3 -c "from utils import cleanup_old_events; cleanup_old_events(30)"`
5. **Deploy to Docker** - Run on server with `docker-compose`

---

## 🆘 Getting Help

### Check Status
```bash
python3 -c "from utils import print_status_summary; print_status_summary()"
```

### View Recent Events
```bash
python3 -c "from database.db import db; import json; print(json.dumps([dict(e) for e in db.get_events(limit=5)], indent=2, default=str))"
```

### List Devices
```bash
python3 -c "from database.db import db; import json; print(json.dumps([dict(d) for d in db.get_devices()], indent=2))"
```

---

## 📚 File Reference

| File | Purpose |
|------|---------|
| `monitor.py` | Scheduled monitoring tasks |
| `app.py` | Flask web application |
| `config.py` | Configuration management |
| `modules/internet.py` | Internet connectivity checks |
| `modules/router.py` | Router availability checks |
| `modules/devices.py` | Network device discovery (ARP) |
| `modules/system_monitor.py` | CPU/Memory/Disk monitoring |
| `modules/alerts.py` | Discord webhook alerts |
| `database/db.py` | SQLite database manager |

---

## 🎯 Success Indicators

✅ Monitor should show:
```
2024-01-15 10:31:05 - internet - INFO - Internet is online
2024-01-15 10:31:15 - router - INFO - Router is online
```

✅ Dashboard should display:
- Internet: 🟢 Online
- Connected devices count
- CPU/Memory usage

✅ Check logs folder:
```bash
ls -l logs/
# Should have monitor.log and app.log
```

---

## 🎓 Learning Resources

- **Flask Documentation**: https://flask.palletsprojects.com/
- **psutil Documentation**: https://psutil.readthedocs.io/
- **SQLite Documentation**: https://www.sqlite.org/docs.html

Enjoy your Network Monitor! 🌐
