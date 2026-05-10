import json
import sys

def send_status(payload):
    """
    Sends a JSON payload to stdout for the extension to consume.
    """
    print(json.dumps(payload))
    sys.stdout.flush()
