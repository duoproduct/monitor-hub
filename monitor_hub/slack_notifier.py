"""
Slack Notification Layer
Uses Block Kit for clean, formatted alerts
"""

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime

class SlackNotifier:
    def __init__(self, slack_user_id: str, bot_token: str = None):
        self.client = WebClient(token=bot_token or os.getenv("SLACK_BOT_TOKEN"))
        self.slack_user_id = slack_user_id

    async def send_error_alert(self, agent_name: str, error_message: str):
        """Send formatted error alert to Slack user"""

        color = "#FF0000"  # Red for errors
        emoji = "🚨"
        title = f"{emoji} Agent Failure Alert"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Agent:*\n{agent_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Time:*\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error Message:*\n```{error_message}```"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "🔗 Check server logs for full traceback"
                    }
                ]
            }
        ]

        try:
            await self._send_message(blocks)
        except SlackApiError as e:
            print(f"Failed to send Slack alert: {e}")

    async def send_timeout_alert(self, agent_name: str, last_heartbeat: str, hours_overdue: int):
        """Send alert when agent hasn't sent heartbeat in too long"""

        color = "#FFA500"  # Orange for timeout
        emoji = "⏰"
        title = f"{emoji} Agent Timeout Warning"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Agent:*\n{agent_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Hours Overdue:*\n{hours_overdue}h"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Last Heartbeat:*\n{last_heartbeat}"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "⚠️ Agent may be stuck or crashed. Check logs."
                    }
                ]
            }
        ]

        try:
            await self._send_message(blocks)
        except SlackApiError as e:
            print(f"Failed to send Slack alert: {e}")

    async def send_daily_summary(self, agents_status: list):
        """Send daily health summary (optional, can be scheduled)"""

        emoji = "📊"
        title = f"{emoji} Daily Agent Health Summary"

        # Count statuses
        total = len(agents_status)
        healthy = sum(1 for a in agents_status if a["status"] == "success")
        errors = sum(1 for a in agents_status if a["status"] == "error")
        stale = sum(1 for a in agents_status if a["status"] == "stale")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Total Agents:*\n{total}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Healthy:*\n{healthy} ✅"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Errors:*\n{errors} 🚨"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Stale:*\n{stale} ⏰"
                    }
                ]
            }
        ]

        # Add agent list
        agent_list_text = "\n".join([
            f"{'✅' if a['status'] == 'success' else '🚨' if a['status'] == 'error' else '⏰'} {a['name']}"
            for a in agents_status
        ])

        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Agent Status:*\n{agent_list_text}"
            }
        })

        try:
            await self._send_message(blocks)
        except SlackApiError as e:
            print(f"Failed to send daily summary: {e}")

    async def _send_message(self, blocks: list):
        """Send message via Slack SDK"""
        try:
            # Open DM with user
            response = self.client.conversations_open(users=[self.slack_user_id])
            channel_id = response["channel"]["id"]

            # Send message
            self.client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text="Monitor Hub Alert"  # Fallback text
            )
        except SlackApiError as e:
            print(f"Slack API Error: {e.response['error']}")
            raise
