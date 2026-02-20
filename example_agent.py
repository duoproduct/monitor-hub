"""
Example: How to integrate Monitor SDK into your existing scripts
This shows the before/after for a typical agent script
"""

# ===== BEFORE (your original script) =====
"""
def main():
    # Your existing code
    check_due_dates()
    send_notifications()
    generate_reports()

if __name__ == "__main__":
    main()
"""

# ===== AFTER (with monitoring) =====
from agent_sdk import monitor  # <-- Add this import

@monitor(agent_name="check_due_dates", expected_interval_hours=24)  # <-- Add decorator
def main():
    # Your existing code - NO changes needed!
    check_due_dates()
    send_notifications()
    generate_reports()

if __name__ == "__main__":
    main()


# ===== ALTERNATIVE: Context Manager =====
"""
from agent_sdk import MonitorContext

def main():
    with MonitorContext("check_due_dates", expected_interval_hours=24):
        # Your existing code here
        check_due_dates()
        send_notifications()
        generate_reports()

if __name__ == "__main__":
    main()
"""


# ===== FULL EXAMPLE WITH REAL LOGIC =====
@monitor(agent_name="example_scraper", expected_interval_hours=12)
def run_scraper():
    """
    Example scraper with automatic error tracking
    """
    import time
    import random

    print("Starting scraper...")

    # Simulate work
    time.sleep(2)

    # Simulate potential error (uncomment to test error alert)
    # if random.random() < 0.3:
    #     raise ValueError("Failed to fetch data from API")

    print("Scraper completed successfully!")
    return {"status": "ok", "items_scraped": 42}


if __name__ == "__main__":
    run_scraper()
