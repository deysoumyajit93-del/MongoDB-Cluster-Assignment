                                                                                                

import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import config

MAX_WAIT_SEC = int(os.getenv("MAX_WAIT_SEC", "300"))
INTERVAL = int(os.getenv("WAIT_INTERVAL", "10"))

def try_connect():
    try:
        c = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=15000)
        c.admin.command("ping")
        c.close()
        return True
    except Exception as e:
        print(f"  not ready: {str(e)[:90]}")
        return False

def main():
    print(f"Waiting for Atlas (up to {MAX_WAIT_SEC}s)...")
    deadline = time.time() + MAX_WAIT_SEC
    while time.time() < deadline:
        if try_connect():
            print("Atlas is reachable. Ready.")
            return 0
        time.sleep(INTERVAL)
    print("Timed out waiting for Atlas.")
    return 1

if __name__ == "__main__":
    sys.exit(main())
