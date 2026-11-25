import os
import time
from pymongo import MongoClient

def _load_env_file():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "atlas-credentials.env"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"),
        r"C:\Users\SOUMYAJIT\Downloads\atlas-credentials.env",
    ]
    for path in candidates:
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip('"').strip("'")
                        if key == "MONGODB_URI" and not os.getenv("MONGO_URI"):
                            os.environ["MONGO_URI"] = val
                        elif key == "MONGODB_USERNAME" and not os.getenv("MONGO_USER"):
                            os.environ["MONGO_USER"] = val
                        elif key == "MONGODB_PASSWORD" and not os.getenv("MONGO_PASS"):
                            os.environ["MONGO_PASS"] = val
            except Exception:
                pass
            break

_load_env_file()

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority")
DB_NAME = os.getenv("MONGO_DB", "monitoring_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "sensor_data")
M0_CAPACITY_BYTES = 512 * 1024 * 1024
NUM_VARIABLES = 20
DOCS_PER_RUN = 1000
POLL_INTERVAL = 3

def get_client(retries=10, timeout_ms=20000, wait=True):
    max_wait = int(os.getenv("ATLAS_MAX_WAIT", "300"))
    deadline = time.time() + max_wait if wait else None
    attempt = 0
    last_err = None
    while True:
        try:
            client = MongoClient(
                MONGO_URI,
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms,
                socketTimeoutMS=timeout_ms,
                retryWrites=True,
            )
            client.admin.command("ping")
            return client
        except Exception as e:
            last_err = e
            attempt += 1
            if attempt >= retries and not wait:
                raise
            if deadline is not None and time.time() >= deadline:
                raise last_err
            sleep_for = min(2 ** min(attempt, 5), 15)
            print("Atlas not reachable (attempt " + str(attempt) + "); retrying in " + str(sleep_for) + "s...", flush=True)
            time.sleep(sleep_for)
