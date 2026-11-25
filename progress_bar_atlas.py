                                                                               

import os
import sys
import time

import config

def bar(pct, width=40):
    pct = max(0.0, min(100.0, pct))
    filled = int(width * pct / 100.0)
    return "[" + "#" * filled + "-" * (width - filled) + "]"

def main():
    poll = float(os.getenv("POLL_INTERVAL", str(config.POLL_INTERVAL)))
    client = config.get_client()
    db = client[config.DB_NAME]

    print("Monitoring M0 storage occupancy (Ctrl+C to stop)...\n")
    try:
        while True:
            objects = 0
            try:
                st = db.command("dbStats")
                used = st.get("storageSize", 0) or st.get("dataSize", 0)
                objects = st.get("objects", 0)
            except Exception as e:
                used = 0
                print(f"stats error: {e}", end="\r")
            pct = (used / config.M0_CAPACITY_BYTES) * 100.0
            line = (f"{bar(pct)} {pct:6.3f}%  "
                    f"used={used/(1024*1024):.4f}MB / {config.M0_CAPACITY_BYTES/(1024*1024):.0f}MB  "
                    f"docs~={objects}")
            sys.stdout.write("\r" + line + "   ")
            sys.stdout.flush()
            if pct >= 100.0:
                print("\nM0 cluster is FULL (100%).")
                break
            time.sleep(poll)
    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        client.close()

if __name__ == "__main__":
    main()
