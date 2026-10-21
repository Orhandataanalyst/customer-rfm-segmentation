"""Customer RFM Segmentation — loads data/transactions.csv, computes RFM
scores, assigns customer segments, saves rfm_segments.csv and charts/.

Run:  python rfm_analysis.py
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).parent
NAVY, GOLD = "#1F3864", "#D9A441"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#ccc"})

tx = pd.read_csv(BASE / "data" / "transactions.csv", parse_dates=["OrderDate"])
snapshot = pd.Timestamp("2025-01-01")
rfm = tx.groupby("CustomerID").agg(
    Recency=("OrderDate", lambda d: (snapshot - d.max()).days),
    Frequency=("OrderID", "count"),
    Monetary=("OrderValue", "sum")).reset_index()

def score(s, invert=False):
    r = s.rank(pct=True)
    v = (1 - r) if invert else r
    return np.ceil(v * 5).clip(1, 5).astype(int)

rfm["R"], rfm["F"], rfm["M"] = score(rfm["Recency"], True), score(rfm["Frequency"]), score(rfm["Monetary"])

def segment(r):
    if r.R >= 4 and r.F >= 4: return "Champions"
    if r.F >= 4: return "Loyal Customers"
    if r.R >= 4 and r.F >= 2: return "Potential Loyalists"
    if r.R >= 4: return "New Customers"
    if r.R <= 2 and r.F >= 3: return "At Risk"
    if r.R <= 2 and r.F == 2: return "About to Sleep"
    if r.R <= 2: return "Lost"
    return "Regular Customers"

rfm["Segment"] = rfm.apply(segment, axis=1)
rfm.to_csv(BASE / "rfm_segments.csv", index=False)

seg = rfm.groupby("Segment").agg(Customers=("CustomerID", "count"), Revenue=("Monetary", "sum"))
print(seg.sort_values("Revenue", ascending=False).round(0).to_string())
print(f"\nTotal customers: {len(rfm)}   Total revenue: ${rfm['Monetary'].sum():,.0f}")

# ---------- charts ----------
(BASE / "charts").mkdir(exist_ok=True)
def bar(series, title, xlabel, fname, color=NAVY, fmt="{:,.0f}"):
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    s = series.sort_values()
    ax.barh(s.index, s.values, color=color)
    for i, v in enumerate(s.values):
        ax.text(v, i, " " + fmt.format(v), va="center", fontsize=9)
    ax.set_title(title, fontsize=12, weight="bold", color=NAVY, loc="left")
    ax.set_xlabel(xlabel); ax.spines[["top", "right"]].set_visible(False)
    ax.set_xlim(0, max(s.values) * 1.18)
    fig.tight_layout(); fig.savefig(BASE / "charts" / fname, dpi=150); plt.close(fig)

bar(seg["Customers"], "Customers by RFM Segment", "Customers", "customers_by_segment.png")
bar(seg["Revenue"], "Revenue by RFM Segment ($)", "Revenue ($)", "revenue_by_segment.png", color=GOLD)
fig, ax = plt.subplots(figsize=(8.5, 4.8))
ax.scatter(rfm["Recency"], rfm["Frequency"], s=np.sqrt(rfm["Monetary"]) * 2.2,
           c=rfm["Monetary"], cmap="YlOrBr", alpha=0.65, edgecolor="#fff", linewidth=0.3)
ax.set_xlabel("Recency (days since last order)"); ax.set_ylabel("Frequency (orders in 2024)")
ax.set_title("RFM Scatter — each dot is one customer (size/colour = total spend)",
             fontsize=11.5, weight="bold", color=NAVY, loc="left")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(BASE / "charts" / "rfm_scatter.png", dpi=150); plt.close(fig)
print("Charts written to charts/.")
