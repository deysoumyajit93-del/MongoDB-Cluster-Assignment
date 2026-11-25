"""One-click demo for presenting to a teacher.

Runs (in order):
  1. generate in a few environments
  2. pull + monitor machine parameters
  3. M0 capacity math
  4. live progress bar (short)
and writes a consolidated report: teacher_report.txt
"""

import os
import sys
import time
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import config

PY = sys.executable
REPORT = os.path.join(BASE, "teacher_report.txt")

def banner(t):
    print("\n" + "=" * 70)
    print("  " + t)
    print("=" * 70)

def run(cmd, env=None, capture=True):
    e = dict(os.environ)
    if env:
        e.update(env)
    r = subprocess.run([PY] + cmd, cwd=BASE, env=e,
                       capture_output=capture, text=True)
    if capture:
        print(r.stdout)
        if r.stderr.strip():
            print("STDERR:\n" + r.stderr)
    return r.returncode, (r.stdout if capture else "")

def main():
    if not config.MONGO_URI or "<username>" in config.MONGO_URI:
        print("ERROR: MONGO_URI not configured.")
        print("Set $env:MONGO_URI or place atlas-credentials.env in this folder / Downloads.")
        sys.exit(1)

    report_lines = []
    def log(s):
        report_lines.append(s)
        print(s)

    banner("STEP 1/5 - Generate data in 5 separate environments")
    env = {"DOCS_PER_RUN": "100"}
    # reuse launcher but override count by calling generate directly for 5 envs
    procs = []
    for i in range(5):
        e = dict(os.environ); e.update(env); e["ENV_ID"] = str(i)
        p = subprocess.Popen([PY, "generate_and_push.py"], cwd=BASE, env=e,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        procs.append((i, p))
        time.sleep(0.2)
    for i, p in procs:
        out, _ = p.communicate()
        print(f"--- env {i} ---")
        print(out.strip())
        report_lines.append(f"env {i}: {out.strip().splitlines()[-1]}")

    banner("STEP 2/5 - Pull data + monitor CPU / memory / network / doc size")
    rc, out = run(["pull_and_monitor.py"], env={"PULL_LIMIT": "0"})
    report_lines.append("\n--- pull_and_monitor.py ---")
    report_lines.append(out)

    banner("STEP 3/5 - M0 capacity math")
    rc, out = run(["m0_capacity.py"])
    report_lines.append("\n--- m0_capacity.py ---")
    report_lines.append(out)

    banner("STEP 4/5 - Per-environment aggregation + alert check")
    rc, out = run(["aggregate_report.py"])
    report_lines.append("\n--- aggregate_report.py ---")
    report_lines.append(out)
    rc, out = run(["alert_check.py"])
    report_lines.append("\n--- alert_check.py ---")
    report_lines.append(out)

    banner("STEP 5/5 - Live progress bar (5 seconds)")
    p = subprocess.Popen([PY, "progress_bar_atlas.py"], cwd=BASE,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    time.sleep(5)
    p.terminate()
    out, _ = p.communicate()
    text = (out or "").strip()
    print(text if text else "(no output)")
    report_lines.append("\n--- progress_bar_atlas.py ---")
    report_lines.append(text if text else "(no output)")

    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    banner("DEMO COMPLETE")
    print(f"Consolidated report written to: {REPORT}")
    print("Show your teacher: Atlas dashboard -> Metrics / Operational Log / Collections.")

if __name__ == "__main__":
    main()