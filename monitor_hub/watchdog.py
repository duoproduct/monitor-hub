"""
Watchdog - Background process that checks agent health
Runs every 5 minutes to detect stale/failed agents
"""

import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Optional

from .slack_notifier import SlackNotifier


class Watchdog:
    def __init__(self, db_path: str, slack_user_id: str, timeout_hours: int = 24):
        self.db_path = db_path
        self.slack_user_id = slack_user_id
        self.timeout_hours = timeout_hours
        self.check_interval_seconds = 300  # 5 minutes
        self.running = False

    async def start(self):
        """Start the watchdog background process"""
        self.running = True
        print(f"[Watchdog] Started - checking every {self.check_interval_seconds}s")

        while self.running:
            try:
                await self.check_all_agents()
            except Exception as e:
                print(f"[Watchdog] Error during check: {e}")

            await asyncio.sleep(self.check_interval_seconds)

    async def stop(self):
        """Stop the watchdog"""
        self.running = False
        print("[Watchdog] Stopped")

    async def check_all_agents(self):
        """Check all agents for timeout or error conditions"""

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all agents
        cursor.execute("""
            SELECT name, last_heartbeat, expected_interval_hours, status
            FROM agents
        """)

        slack = SlackNotifier(slack_user_id=self.slack_user_id)

        for row in cursor.fetchall():
            agent_name, last_heartbeat_str, expected_interval, status = row

            if not last_heartbeat_str:
                continue  # Skip agents with no heartbeat yet

            # Parse timestamp
            try:
                last_heartbeat = datetime.fromisoformat(last_heartbeat_str)
            except:
                continue

            # Calculate time since last heartbeat
            time_since_heartbeat = datetime.now() - last_heartbeat
            hours_overdue = time_since_heartbeat.total_seconds() / 3600

            # Check if agent is stale
            if hours_overdue > expected_interval:
                await slack.send_timeout_alert(
                    agent_name=agent_name,
                    last_heartbeat=last_heartbeat_str,
                    hours_overdue=int(hours_overdue)
                )

                # Update agent status to stale
                cursor.execute("""
                    UPDATE agents
                    SET status = 'stale'
                    WHERE name = ?
                """, (agent_name,))
                conn.commit()

        conn.close()
