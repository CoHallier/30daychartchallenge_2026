import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

# --- Data ---
df = pd.read_csv("data/Footprint/earth.csv", low_memory=False, on_bad_lines="skip")
df_hq = df[df["Data Quality Score"] == "3A"].copy()
df_sorted = df_hq.sort_values("Total", ascending=False).reset_index(drop=True)

top5       = df_sorted.iloc[:5]
median_row = df_sorted.iloc[len(df_sorted) // 2]
india      = df_hq[df_hq["Short Name"] == "India"].iloc[0]

selected   = pd.concat([top5, median_row.to_frame().T, india.to_frame().T]).reset_index(drop=True)
MEDIAN_IDX = 5  # position of median in selected

# --- Earth icon from PNG (center-crop to square, then resize) ---
_img  = Image.open("data/Footprint/Terra_Flag.png").convert("RGBA")
_w, _h = _img.size                                   # 1280 x 768
_side  = min(_w, _h)                                 # 768
_img   = _img.crop(((_w - _side) // 2, 0, (_w + _side) // 2, _side))
earth_icon = np.array(_img.resize((50, 50), Image.Resampling.LANCZOS))

def partial_icon(icon: np.ndarray, fraction: float) -> np.ndarray:
    """Return icon with right (1-fraction) columns made transparent."""
    cut = max(1, int(round(icon.shape[1] * fraction)))
    out = icon.copy()
    out[:, cut:, 3] = 0
    return out

# --- Figure ---
BG        = "#ffffff"
LINE_COLOR = "#cccccc"
N     = len(selected)
x_max = int(np.ceil(selected["Total"].max()))
ROW   = 0.8   # reduced row spacing

fig, ax = plt.subplots(figsize=(max(14, x_max + 4), N * ROW + 2))
fig.set_facecolor(BG)
ax.set_facecolor(BG)

# Vertical separator between country names and icons
ax.axvline(x=-0.5, color=LINE_COLOR, linewidth=0.8, zorder=0)

for i, (_, row) in enumerate(selected.iterrows()):
    y        = (N - 1 - i) * ROW
    n_full   = int(row["Total"])
    fraction = row["Total"] - n_full
    is_median = (i == MEDIAN_IDX)

    # Horizontal line above each row (separator between countries)
    ax.axhline(y=y + ROW * 0.5, color=LINE_COLOR, linewidth=0.8, zorder=1)

    for j in range(n_full):
        ab = AnnotationBbox(OffsetImage(earth_icon, zoom=1.0), (j, y), frameon=False, pad=0)
        ax.add_artist(ab)

    if fraction > 0.05:
        ab = AnnotationBbox(OffsetImage(partial_icon(earth_icon, fraction), zoom=1.0), (n_full, y), frameon=False, pad=0)
        ax.add_artist(ab)

    label = ("Median country  |  " + row["Short Name"]) if is_median else row["Short Name"]
    color = "#555555" if is_median else "#000e78"
    ax.text(-0.6, y, label, ha="right", va="center",
            color=color, fontsize=14, fontweight="bold")
    last_x = n_full + (1 if fraction > 0.05 else 0) - 0.4
    ax.text(last_x, y, f"{row['Total']:.1f}",
            ha="left", va="center", color=color, fontsize=13)

# Bottom line
ax.axhline(y=(N - 1) * ROW - ROW * 0.5, color=LINE_COLOR, linewidth=0.8, zorder=0)

ax.set_xlim(-3.5, x_max + 1.5)
ax.set_ylim((N - 1) * ROW - ROW * 0.8, (N - 1) * ROW + ROW * 0.8)
ax.set_ylim(-ROW * 0.7, (N - 1) * ROW + ROW * 0.6)
ax.axis("off")

ax.set_title(
    "How Many Earths Do We Need?\nBiocapacity Demand by Country (2022)",
    color="#000e78", fontsize=18, fontweight="bold", pad=20, loc="left", x=0.02
)
fig.text(0.98, 0.01,
    "Source: Global Footprint Network — Data Quality: 3A",
    ha="right", color="#000e78", fontsize=9
)

plt.tight_layout(pad=1.5)
plt.savefig(r"2 - pictogram\output\earth_consumption.png", dpi=150,
            bbox_inches="tight", facecolor=BG)
plt.show()
