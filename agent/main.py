import sys
import json
import time
import os
from dotenv import load_dotenv
from watcher import start_watcher
from ipc import send_status

# Load API keys from .env file
load_dotenv()

def main():
    print("Auto-Doc Janitor Agent starting...")
    
    # Send initial status
    send_status({
        "event": "started",
        "tier": "System",
        "model": "N/A",
        "summary": "Agent initialized and watching for changes."
    })

    try:
        start_watcher()
    except KeyboardInterrupt:
        print("Agent stopping...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
