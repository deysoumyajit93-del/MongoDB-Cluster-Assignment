"""Aggregate per-environment statistics from Atlas data."""

import os
import sys
import csv

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import config


def main():
    client = config.get_client()
    coll = client[config.DB_NAME][config.COLLECTION_NAME]

    # Per-environment aggregation
    pipeline = [
        {"$group": {
            "_id": "$env_id",
            "count": {"$sum": 1},
            "avg_var_1": {"$avg": "$var_1"},
            "avg_var_2": {"$avg": "$var_2"},
            "min_var_1": {"$min": "$var_1"},
            "max_var_1": {"$max": "$var_1"},
            "first_ts": {"$min": "$timestamp"},
            "last_ts": {"$max": "$timestamp"},
        }},
        {"$sort": {"_id": 1}},
    ]
    rows = list(coll.aggregate(pipeline))

    print("===== PER-ENVIRONMENT AGGREGATION =====")
    print(f"{'env':>4} {'count':>7} {'avg_var1':>10} {'min_var1':>10} {'max_var1':>10}")
    out_rows = []
    for r in rows:
        print(f"{r['_id']:>4} {r['count']:>7} {r['avg_var_1']:>10.2f} {r['min_var_1']:>10.2f} {r['max_var_1']:>10.2f}")
        out_rows.append({
            "env_id": r["_id"],
            "count": r["count"],
            "avg_var_1": round(r["avg_var_1"], 4),
            "avg_var_2": round(r["avg_var_2"], 4),
            "min_var_1": r["min_var_1"],
            "max_var_1": r["max_var_1"],
            "first_ts": str(r["first_ts"]),
            "last_ts": str(r["last_ts"]),
        })

    # Overall stats
    total = coll.estimated_document_count()
    print(f"\nTotal documents: {total}")
    print(f"Distinct environments: {len(rows)}")

    # Write CSV
    csv_path = os.path.join(BASE, "aggregate_report.csv")
    if out_rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
            w.writeheader()
            w.writerows(out_rows)
        print(f"CSV written to {csv_path}")

    client.close()


if __name__ == "__main__":
    main()
