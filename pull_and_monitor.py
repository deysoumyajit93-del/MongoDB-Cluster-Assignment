\
                                                             

import os
import time
import threading
from datetime import datetime

import psutil
from bson import encode

import config

class Monitor:
    def __init__(self, interval=0.5):
        self.interval = interval
        self._stop = threading.Event()
        self.cpu_samples = []
        self.mem_samples = []                   
        self.mem_used_samples = []            
        self.net_start = None
        self.net_end = None
        self.series = []                                 
        self.thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.net_start = psutil.net_io_counters()
        self.thread.start()

    def stop(self):
        self._stop.set()
        self.thread.join()
        self.net_end = psutil.net_io_counters()

    def _run(self):
        t0 = time.time()
        while not self._stop.is_set():
            cpu = psutil.cpu_percent(interval=None)
            vm = psutil.virtual_memory()
            net = psutil.net_io_counters()
            self.cpu_samples.append(cpu)
            self.mem_samples.append(vm.percent)
            self.mem_used_samples.append(vm.used)
            self.series.append({
                "t_sec": round(time.time() - t0, 3),
                "cpu_percent": cpu,
                "mem_percent": vm.percent,
                "mem_used_mb": round(vm.used / (1024 * 1024), 2),
                "net_bytes_sent": net.bytes_sent - self.net_start.bytes_sent,
                "net_bytes_recv": net.bytes_recv - self.net_start.bytes_recv,
            })
            time.sleep(self.interval)

    def summary(self):
        def avg(xs):
            return sum(xs) / len(xs) if xs else 0.0

        net_sent = self.net_end.bytes_sent - self.net_start.bytes_sent
        net_recv = self.net_end.bytes_recv - self.net_start.bytes_recv
        return {
            "cpu_avg_percent": round(avg(self.cpu_samples), 2),
            "cpu_max_percent": round(max(self.cpu_samples) if self.cpu_samples else 0, 2),
            "mem_avg_percent": round(avg(self.mem_samples), 2),
            "mem_max_percent": round(max(self.mem_samples) if self.mem_samples else 0, 2),
            "mem_avg_used_mb": round(avg(self.mem_used_samples) / (1024 * 1024), 2),
            "net_bytes_sent": net_sent,
            "net_bytes_recv": net_recv,
            "net_mb_sent": round(net_sent / (1024 * 1024), 4),
            "net_mb_recv": round(net_recv / (1024 * 1024), 4),
            "samples": len(self.cpu_samples),
        }

def main():
    limit = int(os.getenv("PULL_LIMIT", "0"))           
    client = config.get_client()
    coll = client[config.DB_NAME][config.COLLECTION_NAME]

    print(f"Pulling from {config.DB_NAME}.{config.COLLECTION_NAME} (limit={limit or 'ALL'})...")
    monitor = Monitor(interval=0.5)
    monitor.start()
    t0 = time.time()

    count = 0
    sizes = []
    cursor = coll.find({})
    if limit > 0:
        cursor = cursor.limit(limit)

    for doc in cursor:
        count += 1
        sizes.append(len(encode(doc)))
        if count % 1000 == 0:
            print(f"  pulled {count} docs...")

    elapsed = time.time() - t0
    monitor.stop()

    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "metrics_timeseries.csv")
    with open(csv_path, "w", newline="") as f:
        import csv
        w = csv.DictWriter(f, fieldnames=list(monitor.series[0].keys()) if monitor.series else
                           ["t_sec", "cpu_percent", "mem_percent", "mem_used_mb", "net_bytes_sent", "net_bytes_recv"])
        w.writeheader()
        for row in monitor.series:
            w.writerow(row)
    print(f"Time-series metrics written to {csv_path}")

    avg_size = sum(sizes) / len(sizes) if sizes else 0
    min_size = min(sizes) if sizes else 0
    max_size = max(sizes) if sizes else 0

    stats = monitor.summary()
    print("\n===== PULL SUMMARY =====")
    print(f"documents_pulled: {count}")
    print(f"elapsed_sec: {elapsed:.2f}")
    print(f"docs_per_sec: {count/elapsed:.1f}" if elapsed > 0 else "docs_per_sec: n/a")
    print(f"doc_size_bytes: avg={avg_size:.1f} min={min_size} max={max_size}")
    print("\n===== MACHINE PARAMETERS (while running) =====")
    for k, v in stats.items():
        print(f"{k}: {v}")

    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pull_report.txt")
    with open(report_path, "w") as f:
        f.write(f"generated_at: {datetime.now().isoformat()}\n")
        f.write(f"documents_pulled: {count}\n")
        f.write(f"elapsed_sec: {elapsed:.2f}\n")
        f.write(f"doc_size_bytes_avg: {avg_size:.1f}\n")
        f.write(f"doc_size_bytes_min: {min_size}\n")
        f.write(f"doc_size_bytes_max: {max_size}\n")
        for k, v in stats.items():
            f.write(f"{k}: {v}\n")
    print(f"\nReport written to {report_path}")

    client.close()

if __name__ == "__main__":
    main()
