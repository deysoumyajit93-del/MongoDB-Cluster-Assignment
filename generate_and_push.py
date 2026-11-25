"""Generate data for 20 variables in a loop and push documents to MongoDB Atlas."""

import os
import random
import time
import socket
from datetime import datetime, timezone

from bson import encode

import config


def make_document(env_id: int, seq: int) -> dict:
    """Build a single document containing 20 variables."""
    doc = {
        "env_id": env_id,
        "seq": seq,
        "timestamp": datetime.now(timezone.utc),
        "hostname": socket.gethostname(),
    }
    for i in range(1, config.NUM_VARIABLES + 1):
        doc[f"var_{i}"] = round(random.uniform(0, 100), 4)
    doc["metrics"] = {
        f"m_{i}": random.randint(0, 1000) for i in range(1, 6)
    }
    doc["tags"] = [f"tag_{random.randint(1, 5)}" for _ in range(3)]
    return doc


def main():
    env_id = int(os.getenv("ENV_ID", "0"))
    n_docs = int(os.getenv("DOCS_PER_RUN", str(config.DOCS_PER_RUN)))

    client = config.get_client()
    coll = client[config.DB_NAME][config.COLLECTION_NAME]

    print(f"[env {env_id}] Connected. Inserting {n_docs} documents...")
    batch = []
    batch_size = 100
    inserted = 0
    t0 = time.time()
    for seq in range(n_docs):
        doc = make_document(env_id, seq)
        batch.append(doc)
        if len(batch) >= batch_size:
            coll.insert_many(batch, ordered=False)
            inserted += len(batch)
            batch = []
            if inserted % 500 == 0:
                print(f"[env {env_id}] inserted {inserted}/{n_docs}")
    if batch:
        coll.insert_many(batch, ordered=False)
        inserted += len(batch)

    elapsed = time.time() - t0
    sample_size = len(encode(make_document(env_id, 0)))
    print(f"[env {env_id}] Done. inserted={inserted} elapsed={elapsed:.2f}s "
          f"rate={inserted/elapsed:.1f} docs/s approx_doc_size={sample_size} bytes")
    client.close()


if __name__ == "__main__":
    main()
