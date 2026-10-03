# Ubuntu/WSL LAUNCH INSTRUCTIONS

## 🚀 One-Command Startup

Open Ubuntu terminal and paste:

```bash
cd /path/to/network-monitor && bash launch-ubuntu.sh
```

Then open browser to: **http://localhost:5000**

---

## 📋 Step-by-Step Manual Setup

### 1. Navigate to Project
```bash
cd /path/to/network-monitor
```

### 2. Install Dependencies (if not already done)
```bash
pip3 install -r requirements.txt
```

### 3. (Optional) Configure Settings
```bash
nano .env
# Edit ROUTER_IP if needed (default: 192.168.1.1)
```

### 4. Terminal 1 - Start Monitor
```bash
python3 monitor.py
```

You should see:
```
2026-01-15 10:30:45 - monitor - INFO - Network Monitor started
2026-01-15 10:31:05 - internet - INFO - Internet is online
2026-01-15 10:31:15 - router - INFO - Router is online
```

### 5. Terminal 2 - Start Flask App
```bash
python3 app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
```

### 6. Open Dashboard
Open your browser and go to: **http://localhost:5000**

---

## ✅ Verify It's Working

### Check Monitor Logs
```bash
tail -f logs/monitor.log
```

### Check Flask Logs
```bash
tail -f logs/app.log
```

### Test API
```bash
curl http://localhost:5000/api/status | python3 -m json.tool
```

### Check Database
```bash
python3 -c "from utils import print_status_summary; print_status_summary()"
```

---

## 🎯 Dashboard Features

Once running, you can:

1. **View Status**: Real-time internet, router, IP, device counts
2. **List Devices**: See all network devices with IP/MAC addresses  
3. **View Events**: Complete log of all monitoring events
4. **See Charts**: 24-hour CPU, Memory, Disk usage graphs
5. **Export Data**: Download events as CSV
6. **Search Devices**: Find devices by IP or MAC address

---

## 🔌 API Endpoints

Test these endpoints:

```bash
# Status
curl http://localhost:5000/api/status

# Devices
curl http://localhost:5000/api/devices

# Events
curl http://localhost:5000/api/events?limit=10

# Stats
curl http://localhost:5000/api/stats?hours=24

# Search
curl "http://localhost:5000/api/devices/search?q=192.168"

# Export
curl http://localhost:5000/api/events/export -o events.csv
```

---

## 🛑 Stop the Application

Press **Ctrl+C** in either terminal to stop.

Or kill processes:
```bash
# Kill monitor
pkill -f "python3 monitor.py"

# Kill Flask
pkill -f "python3 app.py"
```

---

## 🔧 Troubleshooting

### Port 5000 Already in Use
```bash
# Find process
lsof -i :5000

# Kill it
kill -9 <PID>
```

### Dependencies Not Installed
```bash
pip3 install --upgrade -r requirements.txt
```

### Device Discovery Not Working
```bash
# Check arp command
which arp

# Install if missing
sudo apt-get install arp-scan iputils-ping
```

### Database Issues
```bash
# Remove old database (will auto-recreate)
rm network_monitor.db
```

---

## 📊 First Run Checklist

- [ ] Dependencies installed (`pip3 install -r requirements.txt`)
- [ ] .env configured with your router IP
- [ ] Monitor started (`python3 monitor.py`)
- [ ] Flask app started (`python3 app.py`)
- [ ] Dashboard accessible at http://localhost:5000
- [ ] Status shows "🟢 Online" for internet
- [ ] Devices appear in the devices page
- [ ] Events logged in the events page
- [ ] Charts loading in stats page
- [ ] API responding to requests

---

## 🎓 Common Tasks

### View Network Status
```bash
python3 -c "from utils import print_status_summary; print_status_summary()"
```

### List All Devices
```bash
python3 -c "from database.db import db; [print(f\"{d['ip_address']} - {d['mac_address']}\") for d in db.get_devices()]"
```

### Export Events
```bash
curl http://localhost:5000/api/events/export -o events.csv
```

### Get Uptime Percentage
```bash
curl http://localhost:5000/api/uptime | python3 -m json.tool
```

### Check Database Stats
```bash
python3 -c "from utils import get_database_stats; import json; print(json.dumps(get_database_stats(), indent=2))"
```

---

## 📱 Access from Other Machines

If you want to access the dashboard from another computer on your network:

1. Find your machine's IP:
   ```bash
   hostname -I
   ```

2. Access dashboard at:
   ```
   http://<YOUR_IP>:5000
   ```

3. To allow external access, edit app.py and change:
   ```python
   app.run(host='0.0.0.0', port=5000)  # Already configured
   ```

---

## 🐳 Docker Alternative

Instead of manual setup, use Docker:

```bash
cd /path/to/network-monitor

# Start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 📞 Getting Help

1. Check **README.md** for detailed documentation
2. Check **QUICKSTART.md** for common issues
3. Review logs: `tail -f logs/monitor.log`
4. Test API: `curl http://localhost:5000/api/status`
5. Check database: Run `python3 -c "from utils import print_status_summary; print_status_summary()"`

---

## 🎉 You're Ready!

Your Network Monitor is now running. Enjoy monitoring your home network! 🌐
