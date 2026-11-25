import os

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

import time
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority")

def get_client(retries=5, timeout_ms=20000):
                                                                                         
    last_err = None
    for attempt in range(retries):
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
            time.sleep(min(2 ** attempt, 10))
    raise last_err
DB_NAME = os.getenv("MONGO_DB", "monitoring_db")
COLLECTION_NAME = os.getenv("MONGO_COLLECTION", "sensor_data")

M0_CAPACITY_BYTES = 512 * 1024 * 1024

NUM_VARIABLES = 20

DOCS_PER_RUN = 1000

POLL_INTERVAL = 3