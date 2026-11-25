                                                                                           

import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import config

THRESHOLD_PCT = float(os.getenv("ALERT_THRESHOLD_PCT", "80"))

def connect():
    return config.get_client()

def main():
    client = connect()
    db = client[config.DB_NAME]
    st = db.command("dbStats")
    used = st.get("storageSize", 0) or st.get("dataSize", 0)
    pct = (used / config.M0_CAPACITY_BYTES) * 100.0
    print(f"Storage used: {used} bytes ({used/(1024*1024):.4f} MB)")
    print(f"Occupancy: {pct:.4f}% (threshold {THRESHOLD_PCT}%)")
    if pct >= THRESHOLD_PCT:
        print("ALERT: M0 storage threshold exceeded!")
        client.close()
        sys.exit(2)
    print("OK: within threshold.")
    client.close()

if __name__ == "__main__":
    main()