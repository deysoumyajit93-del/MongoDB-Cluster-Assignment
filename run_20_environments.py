"""Launch the generator in 20 separate (sub)environments/processes and wait."""

import os
import sys
import subprocess
import time

BASE = os.path.dirname(os.path.abspath(__file__))
PYTHON = sys.executable
SCRIPT = os.path.join(BASE, "generate_and_push.py")

NUM_ENVS = 20


def main():
    if not os.getenv("MONGO_URI"):
        print("WARNING: MONGO_URI env var not set. Set it before running, e.g.")
        print('  set MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/...')
        # continue; script will fail fast with clear error

    procs = []
    for env_id in range(NUM_ENVS):
        env = dict(os.environ)
        env["ENV_ID"] = str(env_id)
        env["DOCS_PER_RUN"] = os.getenv("DOCS_PER_RUN", "200")
        p = subprocess.Popen(
            [PYTHON, SCRIPT],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=BASE,
        )
        procs.append((env_id, p))
        print(f"Started environment {env_id} (pid {p.pid})")
        time.sleep(0.3)  # stagger to avoid thundering herd

    print("\nAll 20 environments started. Waiting for completion...")
    for env_id, p in procs:
        out, _ = p.communicate()
        print(f"===== ENV {env_id} (exit {p.returncode}) =====")
        print(out.strip())

    print("\nAll environments finished.")


if __name__ == "__main__":
    main()