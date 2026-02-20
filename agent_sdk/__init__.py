"""
Agent SDK - 5-line decorator wrapper for monitoring
Drop this into any Python script to enable automatic heartbeat + error tracking
"""

import functools
import os
import requests
from datetime import datetime
import traceback
import sys

# ===== CONFIG =====
MONITOR_HUB_URL = os.getenv("MONITOR_HUB_URL", "http://localhost:8000")
AUTH_TOKEN = os.getenv("MONITOR_AUTH_TOKEN", "change-me-in-production")


def send_heartbeat(agent_name: str, status: str, message: str = "", expected_interval_hours: int = 24):
    """
    Send heartbeat to Monitor Hub

    Args:
        agent_name: Name of the agent/script
        status: "success" or "error"
        message: Optional message (error traceback, etc.)
        expected_interval_hours: How often this agent should run (for timeout detection)
    """

    payload = {
        "agent_name": agent_name,
        "status": status,
        "message": message,
        "expected_interval_hours": expected_interval_hours
    }

    try:
        response = requests.post(
            f"{MONITOR_HUB_URL}/heartbeat",
            json=payload,
            headers={"X-Auth-Token": AUTH_TOKEN},
            timeout=5
        )
        print(f"[Monitor] Heartbeat sent: {status}")
    except requests.exceptions.RequestException as e:
        print(f"[Monitor] Failed to send heartbeat: {e}")


def monitor(agent_name: str, expected_interval_hours: int = 24):
    """
    Decorator that wraps your main function with automatic monitoring

    Usage:
        @monitor(agent_name="check_due_dates", expected_interval_hours=24)
        def main():
            # Your code here
            pass

        if __name__ == "__main__":
            main()
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Run the actual function
                result = func(*args, **kwargs)

                # Send success heartbeat
                send_heartbeat(
                    agent_name=agent_name,
                    status="success",
                    message="Script completed successfully",
                    expected_interval_hours=expected_interval_hours
                )

                return result

            except Exception as e:
                # Catch any unhandled exception
                error_traceback = traceback.format_exc()

                # Send error heartbeat before crash
                send_heartbeat(
                    agent_name=agent_name,
                    status="error",
                    message=f"Exception: {str(e)}\n\nTraceback:\n{error_traceback}",
                    expected_interval_hours=expected_interval_hours
                )

                # Re-raise the exception (so script still fails as expected)
                raise

        return wrapper
    return decorator


# ===== CONTEXT MANAGER VERSION =====
class MonitorContext:
    """
    Alternative: Context manager for more control

    Usage:
        with MonitorContext("my_agent", expected_interval_hours=24):
            # Your code here
            do_something()
    """

    def __init__(self, agent_name: str, expected_interval_hours: int = 24):
        self.agent_name = agent_name
        self.expected_interval_hours = expected_interval_hours

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Success
            send_heartbeat(
                agent_name=self.agent_name,
                status="success",
                message="Script completed successfully",
                expected_interval_hours=self.expected_interval_hours
            )
        else:
            # Error
            error_traceback = "".join(traceback.format_exception(exc_type, exc_val, exc_tb))
            send_heartbeat(
                agent_name=self.agent_name,
                status="error",
                message=f"Exception: {str(exc_val)}\n\nTraceback:\n{error_traceback}",
                expected_interval_hours=self.expected_interval_hours
            )

        # Don't suppress the exception
        return False
