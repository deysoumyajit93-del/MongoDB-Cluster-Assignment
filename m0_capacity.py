"""Calculate how many documents can be stored in a MongoDB Atlas M0 (free) cluster."""

import os
import math
from bson import encode

import config


def sample_avg_doc_size(coll, sample_n=500):
    sizes = []
    for doc in coll.find({}).limit(sample_n):
        sizes.append(len(encode(doc)))
    if not sizes:
        return None, 0
    return sum(sizes) / len(sizes), len(sizes)


def main():
    client = config.get_client()
    db = client[config.DB_NAME]
    coll = db[config.COLLECTION_NAME]

    avg_size, n = sample_avg_doc_size(coll)
    print(f"Sampled {n} documents; avg BSON size = {avg_size:.2f} bytes")

    # Fallback if collection empty
    if avg_size is None or avg_size <= 0:
        avg_size = 256.0
        print("Collection empty; using default avg doc size 256 bytes")

    # db stats
    try:
        st = db.command("dbStats")
        print("\n===== Atlas DB stats =====")
        print(f"dataSize (bytes): {st.get('dataSize')}")
        print(f"storageSize (bytes): {st.get('storageSize')}")
        print(f"indexSize (bytes): {st.get('indexSize')}")
        print(f"totalSize (bytes): {st.get('totalSize')}")
    except Exception as e:
        print("dbStats unavailable:", e)

    capacity = config.M0_CAPACITY_BYTES
    # Raw document capacity (data only)
    raw_docs = capacity / avg_size
    # Account for a typical index overhead (~20%) and MongoDB/Atlas overhead
    overhead_factor = 1.25
    effective_capacity = capacity / overhead_factor
    effective_docs = effective_capacity / avg_size

    print("\n===== M0 CAPACITY MATH =====")
    print(f"M0 capacity: {capacity} bytes ({capacity/(1024*1024)} MB)")
    print(f"Avg doc size: {avg_size:.2f} bytes")
    print(f"Raw max documents (no overhead): {raw_docs:,.0f}")
    print(f"With ~{int((overhead_factor-1)*100)}% overhead factor: {effective_docs:,.0f}")
    print(f"Approx documents (floor): {math.floor(effective_docs):,}")

    # Also compute based on current stored size how full we are
    try:
        st = db.command("dbStats")
        used = st.get("storageSize", 0) or st.get("dataSize", 0)
        pct = (used / capacity) * 100
        print(f"\nCurrent storage used: {used} bytes ({used/(1024*1024):.4f} MB)")
        print(f"Current occupancy: {pct:.4f}% of M0")
    except Exception:
        pass

    client.close()


if __name__ == "__main__":
    main()
