# 🔔 Monitor Hub - Heartbeat & Alerting System

Lightweight monitoring for autonomous Python agents. Silent unless broken.

## 📋 Features

- ✅ **Zero-Config Agent SDK**: 5-line decorator integration
- 🚨 **Instant Error Alerts**: Automatic Slack notifications on crashes
- ⏰ **Timeout Detection**: Watchdog detects stale agents
- 📊 **Daily Health Summary**: Optional status reports
- 🔐 **Token-Based Auth**: Secure endpoint access
- 🐳 **Lightweight**: SQLite + FastAPI, minimal overhead

## 🏗 Architecture

```
┌─────────────────┐      HTTP POST      ┌──────────────┐
│   Your Agents   │ ──────────────────> │ Monitor Hub  │
│ (Python scripts) │  /heartbeat JSON    │  (FastAPI)   │
└─────────────────┘                     └──────────────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │   SQLite DB  │
                                        │ (Last Seen)  │
                                        └──────────────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │   Watchdog   │
                                        │ (Background) │
                                        └──────────────┘
                                                │
                              Alert Triggered   ▼
                                        ┌──────────────┐
                                        │    Slack     │
                                        │ (DM to User) │
                                        └──────────────┘
```

---

## 🚀 Quick Start

### 1. Slack App Setup (5 minutes)

#### Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Name it "Monitor Hub" → Select your workspace
4. Click **"Create App"**

#### Step 2: Configure Permissions

1. Navigate to **OAuth & Permissions** (left sidebar)
2. Under **Bot Token Scopes**, add:
   - `chat:write`
   - `channels:read`
   - `im:write` (critical for DM!)
   - `users:read`

3. Scroll up → Click **"Install to Workspace"**
4. Copy the **Bot User OAuth Token** (starts with `xoxb-`)
   - Save it to your `.env` file as `SLACK_BOT_TOKEN`

#### Step 3: Get Your User ID

1. Open Slack → Right-click your name → **"Copy member ID"**
   - Or go to: https://api.slack.com/methods/auth.test/test
   - Look for `"user_id"` in the response
   - Save it to your `.env` file as `SLACK_USER_ID`

---

### 2. Server Deployment (10 minutes)

#### Prerequisites

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm

# Verify
python3 --version  # Should be 3.8+
npm --version      # Should be 8+
```

#### Deploy

```bash
# Clone or upload files to server
cd /opt
sudo mkdir -p monitor-hub
sudo chown $USER:$USER monitor-hub

# Copy monitoring-system/* to /opt/monitor-hub/
cd /opt/monitor-hub

# Run deployment script
chmod +x deploy.sh
./deploy.sh
```

#### Configure Environment

```bash
# Edit environment file
nano /opt/monitor-hub/.env
```

Fill in your values:

```bash
# ===== MONITOR HUB CONFIG =====
MONITOR_HUB_URL=http://localhost:8000
MONITOR_AUTH_TOKEN=generate-random-secure-string-here
ALERT_TIMEOUT_HOURS=24

# ===== DATABASE =====
MONITOR_DB_PATH=/opt/monitor-hub/monitoring.db

# ===== SLACK (from Step 1) =====
SLACK_BOT_TOKEN=your-actual-slack-bot-token
SLACK_USER_ID=your-actual-user-id
```

Generate secure auth token:

```bash
# Generate random token
openssl rand -hex 32
# Use output as MONITOR_AUTH_TOKEN
```

#### Start Service

```bash
cd /opt/monitor-hub
pm2 restart monitor-hub
pm2 logs monitor-hub
```

Verify:

```bash
curl http://localhost:8000/health
# Should return: {"status":"healthy","timestamp":"..."}
```

---

### 3. Agent Integration (2 minutes per script)

#### Install SDK

```bash
pip install requests  # Or add to your requirements.txt
```

#### Option A: Decorator (Recommended)

```python
# check_due_dates.py
from agent_sdk import monitor

@monitor(agent_name="check_due_dates", expected_interval_hours=24)
def main():
    # Your existing code - NO changes!
    check_kaiten_tasks()
    send_reminders()

if __name__ == "__main__":
    main()
```

#### Option B: Context Manager

```python
# scraper.py
from agent_sdk import MonitorContext

def main():
    with MonitorContext("scraper", expected_interval_hours=12):
        scrape_data()
        upload_to_s3()

if __name__ == "__main__":
    main()
```

#### Test Integration

```bash
# Run your script
python check_due_dates.py

# Check Monitor Hub logs
pm2 logs monitor-hub --lines 20

# Should see: [Monitor] Heartbeat sent: success
```

---

## 📊 API Reference

### POST /heartbeat

Send heartbeat from agent.

**Headers:**
```
X-Auth-Token: your-auth-token
Content-Type: application/json
```

**Body:**
```json
{
  "agent_name": "check_due_dates",
  "status": "success",
  "message": "Completed successfully",
  "expected_interval_hours": 24
}
```

**Response:**
```json
{
  "status": "received",
  "agent": "check_due_dates",
  "timestamp": "2026-02-20T10:30:00"
}
```

### GET /status

Get status of all monitored agents.

**Response:**
```json
{
  "agents": [
    {
      "name": "check_due_dates",
      "last_heartbeat": "2026-02-20T10:30:00",
      "expected_interval_hours": 24,
      "status": "success",
      "last_message": "Completed successfully"
    }
  ],
  "total": 1
}
```

---

## 🔔 Alert Types

### 1. Error Alert (Immediate)
Triggered when agent sends `status: "error"` or crashes.

```
🚨 Agent Failure Alert
Agent: check_due_dates
Time: 2026-02-20 10:30:00

Error Message:
Exception: Connection timeout
...
```

### 2. Timeout Alert (Watchdog)
Triggered when agent hasn't sent heartbeat in `expected_interval_hours`.

```
⏰ Agent Timeout Warning
Agent: scraper
Hours Overdue: 26h
Last Heartbeat: 2026-02-19 08:00:00
```

### 3. Daily Summary (Optional)
Can be scheduled via cron to send daily health report.

---

## 🛠 Operations

### View Status

```bash
# PM2 status
pm2 status

# View logs
pm2 logs monitor-hub

# Real-time monitoring
pm2 monit
```

### Restart Service

```bash
pm2 restart monitor-hub
```

### Update Code

```bash
cd /opt/monitor-hub
git pull  # Or copy new files
pm2 restart monitor-hub
```

### Backup Database

```bash
cp /opt/monitor-hub/monitoring.db /backup/monitoring-$(date +%Y%m%d).db
```

---

## 🧪 Testing

### Test Error Alert

```python
# test_error.py
from agent_sdk import monitor

@monitor(agent_name="test_error")
def main():
    raise Exception("Test error - please ignore")

if __name__ == "__main__":
    main()
```

### Manual Heartbeat

```bash
curl -X POST http://localhost:8000/heartbeat \
  -H "X-Auth-Token: your-token" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "manual_test",
    "status": "success",
    "message": "Manual test",
    "expected_interval_hours": 24
  }'
```

---

## 🔒 Security Best Practices

1. **Rotate Auth Tokens**: Change `MONITOR_AUTH_TOKEN` periodically
2. **Firewall Rules**: Only expose internally, use nginx reverse proxy if needed
3. **Database Permissions**: Ensure only `monitor` user can read/write DB
4. **Slack Token Security**: Never commit tokens to git

---

## 📈 Scaling Considerations

### Multiple Servers
- Run Monitor Hub on central server
- All agents point to `MONITOR_HUB_URL=http://central-server:8000`

### High Availability
- Run multiple instances behind load balancer
- Use PostgreSQL instead of SQLite (requires DB schema updates)

### Rate Limiting
- Add `slowapi` for rate limiting on `/heartbeat`
- Use Redis for distributed locking in Watchdog

---

## 🐛 Troubleshooting

### Slack alerts not arriving
```bash
# Check token
echo $SLACK_BOT_TOKEN
# Verify bot has `im:write` permission
# Check DM is enabled: https://api.slack.com/methods/conversations.open
```

### Watchdog not triggering
```bash
# Check database
sqlite3 /opt/monitor-hub/monitoring.db
> SELECT * FROM agents;
> SELECT * FROM heartbeat_log ORDER BY timestamp DESC LIMIT 10;
```

### Agent not sending heartbeat
```bash
# Check agent logs
python your_script.py
# Look for: [Monitor] Heartbeat sent: success
# Verify MONITOR_HUB_URL and AUTH_TOKEN
```

---

## 📝 Example Dashboard Integration

```python
# Add to Grafana/Prometheus
import sqlite3
import json
from flask import Flask

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    conn = sqlite3.connect('monitoring.db')
    cursor = conn.cursor()

    cursor.execute("SELECT status, COUNT(*) FROM agents GROUP BY status")
    data = dict(cursor.fetchall())

    return {
        "healthy": data.get("success", 0),
        "errors": data.get("error", 0),
        "stale": data.get("stale", 0)
    }
```

---

## 📄 License

MIT

## 👤 Support

Created by @alex for autonomous agent monitoring

---

**Silent unless broken.** 🔔
