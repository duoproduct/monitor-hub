"""
Monitor Hub - Heartbeat & Alerting System
Lightweight monitoring service for autonomous agents
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import sqlite3
import os
from typing import Optional
import uvicorn

from .slack_notifier import SlackNotifier
from .watchdog import Watchdog

# ===== CONFIG =====
DB_PATH = os.getenv("MONITOR_DB_PATH", "monitoring.db")
SLACK_USER_ID = os.getenv("SLACK_USER_ID", "")
AUTH_TOKEN = os.getenv("MONITOR_AUTH_TOKEN", "change-me-in-production")
ALERT_TIMEOUT_HOURS = int(os.getenv("ALERT_TIMEOUT_HOURS", "24"))

# ===== DATABASE SETUP =====
def init_db():
    """Initialize SQLite database for heartbeat tracking"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            last_heartbeat TIMESTAMP,
            expected_interval_hours INTEGER DEFAULT 24,
            status TEXT DEFAULT 'unknown',
            last_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS heartbeat_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_name TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

# ===== MODELS =====
class HeartbeatRequest(BaseModel):
    agent_name: str
    status: str  # "success" | "error"
    message: Optional[str] = ""
    expected_interval_hours: Optional[int] = 24

# ===== FASTAPI APP =====
app = FastAPI(
    title="Monitor Hub",
    description="Heartbeat & Alerting for Autonomous Agents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== DEPENDENCIES =====
async def verify_auth(x_auth_token: str = Header(...)):
    """Verify authentication token"""
    if x_auth_token != AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid auth token")
    return True

# ===== ENDPOINTS =====
@app.on_event("startup")
async def startup_event():
    """Initialize database and start watchdog on startup"""
    init_db()

    # Start watchdog in background
    watchdog = Watchdog(
        db_path=DB_PATH,
        slack_user_id=SLACK_USER_ID,
        timeout_hours=ALERT_TIMEOUT_HOURS
    )
    import asyncio
    asyncio.create_task(watchdog.start())

@app.post("/heartbeat", dependencies=[Depends(verify_auth)])
async def receive_heartbeat(heartbeat: HeartbeatRequest):
    """Receive heartbeat from agents"""

    if heartbeat.status not in ["success", "error"]:
        raise HTTPException(status_code=400, detail="Status must be 'success' or 'error'")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    now = datetime.now()

    # Update or insert agent
    cursor.execute("""
        INSERT OR REPLACE INTO agents (name, last_heartbeat, expected_interval_hours, status, last_message)
        VALUES (?, ?, ?, ?, ?)
    """, (
        heartbeat.agent_name,
        now,
        heartbeat.expected_interval_hours,
        heartbeat.status,
        heartbeat.message
    ))

    # Log heartbeat
    cursor.execute("""
        INSERT INTO heartbeat_log (agent_name, status, message, timestamp)
        VALUES (?, ?, ?, ?)
    """, (heartbeat.agent_name, heartbeat.status, heartbeat.message, now))

    conn.commit()
    conn.close()

    # Trigger alert on error
    if heartbeat.status == "error":
        slack = SlackNotifier(slack_user_id=SLACK_USER_ID)
        await slack.send_error_alert(
            agent_name=heartbeat.agent_name,
            error_message=heartbeat.message
        )

    return {
        "status": "received",
        "agent": heartbeat.agent_name,
        "timestamp": now.isoformat()
    }

@app.get("/status")
async def get_status():
    """Get current status of all monitored agents"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT name, last_heartbeat, expected_interval_hours, status, last_message
        FROM agents
        ORDER BY last_heartbeat DESC
    """)

    agents = []
    for row in cursor.fetchall():
        agents.append({
            "name": row[0],
            "last_heartbeat": row[1],
            "expected_interval_hours": row[2],
            "status": row[3],
            "last_message": row[4]
        })

    conn.close()

    return {"agents": agents, "total": len(agents)}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# ===== CLI =====
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
