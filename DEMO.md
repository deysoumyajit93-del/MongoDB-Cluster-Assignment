# How to run & present to your teacher

## 1. Set credentials (PowerShell)
```powershell
$env:MONGO_URI="mongodb+srv://deysoumyajit93_db_user:cOcpuiCTGdNEs245@cluster0.z9favcd.mongodb.net"
```
(or load from the attached `atlas-credentials.env`)

## 2. Install dependencies
```powershell
pip install -r requirements.txt
```

## 3. One-click demo
```powershell
python demo_for_teacher.py
```
This runs generation (5 envs), pull + monitoring, M0 capacity math, and a live progress bar, and writes `teacher_report.txt`.

## 4. What to SHOW in MongoDB Atlas (open in browser)
- **Clusters -> Metrics**: connections spike from 20 clients, ops/sec, network.
- **Database Access / Operational Log** (if enabled): shows multiple client connections and CRUD ops.
- **Collections -> sensor_data**: 10,000+ documents, each with 20 variables.
- **Storage**: ~2.5 MB used of 512 MB (M0).

## 5. Individual scripts (if teacher wants them separately)
```powershell
python run_20_environments.py      # 20 separate environments
python pull_and_monitor.py          # CPU, memory, network, doc size
python m0_capacity.py              # total docs in M0 math
python progress_bar_atlas.py       # live 0-100% storage bar (Ctrl+C to stop)
```

## 6. Key numbers to mention
- Doc size ~512 bytes (BSON).
- M0 capacity 512 MB -> ~1,048,576 docs raw / ~838,860 with overhead.
- CPU ~26%, Memory ~74%, Net recv ~5 MB during pull of 10,000 docs.