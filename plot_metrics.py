\
\
\
\
   

import os
import sys
import csv
import warnings
warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(BASE, "metrics_timeseries.csv")
if not os.path.isfile(csv_path):
    print("Run pull_and_monitor.py first to generate metrics_timeseries.csv")
    sys.exit(1)

rows = []
with open(csv_path, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        rows.append(r)

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.DataFrame(rows).astype({
    "t_sec": float, "cpu_percent": float, "mem_percent": float,
    "mem_used_mb": float, "net_bytes_sent": float, "net_bytes_recv": float,
})
df["net_recv_mb"] = df["net_bytes_recv"] / (1024 * 1024)
df["net_sent_mb"] = df["net_bytes_sent"] / (1024 * 1024)
dt = df["t_sec"].diff().replace(0, np.nan)
df["recv_mbps"] = (df["net_bytes_recv"].diff() / dt / (1024 * 1024)).fillna(0).clip(lower=0)
df["sent_mbps"] = (df["net_bytes_sent"].diff() / dt / (1024 * 1024)).fillna(0).clip(lower=0)
df["recv_mbps_s"] = df["recv_mbps"].rolling(3, min_periods=1).mean()
df["sent_mbps_s"] = df["sent_mbps"].rolling(3, min_periods=1).mean()

sns.set_theme(style="whitegrid", context="notebook", font_scale=1.05)
palette = sns.color_palette("husl", 6)

fig = plt.figure(figsize=(16, 12))
gs = fig.add_gridspec(3, 2, hspace=0.45, wspace=0.35)

ax = fig.add_subplot(gs[0, 0])
sns.lineplot(data=df, x="t_sec", y="cpu_percent", ax=ax, color=palette[0], linewidth=2, label="CPU %")
ax.fill_between(df["t_sec"], df["cpu_percent"], alpha=0.25, color=palette[0])
i = df["cpu_percent"].idxmax()
ax.scatter(df.loc[i, "t_sec"], df.loc[i, "cpu_percent"], color="red", zorder=5, s=60)
ax.annotate(f"peak {df.loc[i,'cpu_percent']:.1f}%",
            (df.loc[i, "t_sec"], df.loc[i, "cpu_percent"]),
            xytext=(10, 12), textcoords="offset points", fontsize=8, color="red",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="red", alpha=0.7),
            arrowprops=dict(arrowstyle="->", color="red", lw=0.8))
ax.set_title("CPU usage", fontweight="bold")
ax.set_ylabel("CPU %"); ax.set_xlabel("Time (s)")
ax.set_ylim(0, max(100, df["cpu_percent"].max() * 1.15))

ax = fig.add_subplot(gs[0, 1])
sns.lineplot(data=df, x="t_sec", y="mem_percent", ax=ax, color=palette[1], linewidth=2, label="Memory %")
ax.fill_between(df["t_sec"], df["mem_percent"], alpha=0.25, color=palette[1])
i = df["mem_percent"].idxmax()
ax.scatter(df.loc[i, "t_sec"], df.loc[i, "mem_percent"], color="red", zorder=5, s=60)
ax.annotate(f"peak {df.loc[i,'mem_percent']:.1f}%",
            (df.loc[i, "t_sec"], df.loc[i, "mem_percent"]),
            xytext=(10, 12), textcoords="offset points", fontsize=8, color="red",
            bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="red", alpha=0.7),
            arrowprops=dict(arrowstyle="->", color="red", lw=0.8))
ax.set_title("Memory usage", fontweight="bold")
ax.set_ylabel("Memory %"); ax.set_xlabel("Time (s)")

ax = fig.add_subplot(gs[1, 0])
sns.lineplot(data=df, x="t_sec", y="mem_used_mb", ax=ax, color=palette[2], linewidth=2)
ax.fill_between(df["t_sec"], df["mem_used_mb"], alpha=0.2, color=palette[2])
ax.set_title("Memory used (MB)", fontweight="bold")
ax.set_ylabel("MB"); ax.set_xlabel("Time (s)")

ax = fig.add_subplot(gs[1, 1])
sns.lineplot(data=df, x="t_sec", y="net_recv_mb", ax=ax, color=palette[3], linewidth=2, label="Received")
sns.lineplot(data=df, x="t_sec", y="net_sent_mb", ax=ax, color=palette[4], linewidth=2, label="Sent")
ax.fill_between(df["t_sec"], df["net_recv_mb"], alpha=0.15, color=palette[3])
ax.set_title("Cumulative network transfer", fontweight="bold")
ax.set_ylabel("MB"); ax.set_xlabel("Time (s)")
ax.legend(loc="upper left", frameon=True)

ax = fig.add_subplot(gs[2, 0])
sns.lineplot(data=df, x="t_sec", y="recv_mbps_s", ax=ax, color=palette[3], linewidth=2, label="Recv (smoothed)")
sns.lineplot(data=df, x="t_sec", y="sent_mbps_s", ax=ax, color=palette[4], linewidth=2, label="Sent (smoothed)")
ax.set_title("Network throughput (MB/s)", fontweight="bold")
ax.set_ylabel("MB/s"); ax.set_xlabel("Time (s)")
ax.legend(loc="upper right", frameon=True)

ax = fig.add_subplot(gs[2, 1])
sns.scatterplot(data=df, x="cpu_percent", y="mem_percent", ax=ax, hue="t_sec",
                palette="viridis", size="net_recv_mb", sizes=(20, 200), legend=False)
sns.regplot(data=df, x="cpu_percent", y="mem_percent", ax=ax, scatter=False,
            color="black", line_kws=dict(linewidth=1.5, linestyle="--"))
r = df["cpu_percent"].corr(df["mem_percent"])
ax.set_title(f"CPU vs Memory (r = {r:.2f})", fontweight="bold")
ax.set_xlabel("CPU %"); ax.set_ylabel("Memory %")

total_recv = df["net_recv_mb"].iloc[-1]
total_sent = df["net_sent_mb"].iloc[-1]
summary = (f"Samples: {len(df)}\n"
           f"CPU avg/max: {df['cpu_percent'].mean():.1f}% / {df['cpu_percent'].max():.1f}%\n"
           f"Mem avg/max: {df['mem_percent'].mean():.1f}% / {df['mem_percent'].max():.1f}%\n"
           f"Net recv: {total_recv:.2f} MB | sent: {total_sent:.2f} MB\n"
           f"Peak recv throughput: {df['recv_mbps'].max():.2f} MB/s")
fig.text(0.5, 0.015, summary, ha="center", va="bottom", fontsize=9,
         bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="gray", alpha=0.95))

fig.suptitle("Atlas pull — machine metrics dashboard", fontsize=16, fontweight="bold", y=0.995)
plt.tight_layout(rect=[0, 0.07, 1, 0.97])
out = os.path.join(BASE, "metrics_dashboard.png")
plt.savefig(out, dpi=150, bbox_inches="tight")
print(f"Saved {out}")
plt.close(fig)

corr_cols = [c for c in ["cpu_percent", "mem_percent", "mem_used_mb", "net_recv_mb", "net_sent_mb"]
             if df[c].std(ddof=0) > 0]
with np.errstate(divide="ignore", invalid="ignore"):
    corr = df[corr_cols].corr()
fig2, ax2 = plt.subplots(figsize=(9, 7))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", center=0, square=True,
            linewidths=0.8, annot_kws={"size": 11, "weight": "bold"},
            cbar_kws={"shrink": 0.8, "label": "Pearson r"}, ax=ax2)
ax2.set_title("Metric correlation heatmap", fontweight="bold", pad=12)
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=30, ha="right", fontsize=10)
ax2.set_yticklabels(ax2.get_yticklabels(), rotation=0, fontsize=10)
for label in ax2.get_xticklabels() + ax2.get_yticklabels():
    label.set_horizontalalignment("right" if label in ax2.get_xticklabels() else "right")
plt.tight_layout(pad=1.5)
out2 = os.path.join(BASE, "metrics_correlation.png")
plt.savefig(out2, dpi=150, bbox_inches="tight")
print(f"Saved {out2}")
plt.close(fig2)