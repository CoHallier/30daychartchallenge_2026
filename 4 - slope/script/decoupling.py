import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# --- Load data ---

ROOT = Path(__file__).parent.parent.parent

ghg = pd.read_csv(ROOT / "data/GHG/per-capita-ghg-emissions.csv")
ghg.columns = ["Entity", "Code", "Year", "GHG"]

gdp = pd.read_csv(
    ROOT / "data/GDP/API_NY.GDP.PCAP.KD_DS2_en_csv_v2_82.csv",
    skiprows=4
)

# --- Filter 1994-2023 ---

YEARS = list(range(1994, 2024))
YEARS_STR = [str(y) for y in YEARS]

ghg_world = ghg[(ghg["Entity"] == "World") & (ghg["Year"].isin(YEARS))].set_index("Year")["GHG"]
ghg_eu = ghg[(ghg["Entity"] == "European Union (27)") & (ghg["Year"].isin(YEARS))].set_index("Year")["GHG"]

gdp_world = pd.Series(
    gdp[gdp["Country Code"] == "WLD"][YEARS_STR].values.flatten(),
    index=YEARS, dtype=float
)

gdp_eu = pd.Series(
    gdp[gdp["Country Code"] == "EUU"][YEARS_STR].values.flatten(),
    index=YEARS, dtype=float
)

# --- Index to 100 in 1994 ---

def index_100(series):
    return series / series.loc[1994] * 100

ghg_world_idx = index_100(ghg_world)
ghg_eu_idx = index_100(ghg_eu)
gdp_world_idx = index_100(gdp_world)
gdp_eu_idx = index_100(gdp_eu)

# --- Plot ---

fig, ax = plt.subplots(figsize=(11, 6))

ax.plot(YEARS, gdp_world_idx, label="GDP – World", color="#2196F3", linewidth=2)
ax.plot(YEARS, ghg_world_idx, label="GHG emissions – World", color="#2196F3", linewidth=2, linestyle="--")

ax.plot(YEARS, gdp_eu_idx, label="GDP – European Union", color="#4CAF50", linewidth=2)
ax.plot(YEARS, ghg_eu_idx, label="GHG emissions – European Union", color="#4CAF50", linewidth=2, linestyle="--")

ax.axhline(100, color="gray", linewidth=0.8, linestyle=":")

# --- Annotation: relative decoupling (World) ---
# GDP World grows faster than GHG World → gap visible around 2018
ax.annotate(
    "",
    xy=(2018, float(gdp_world_idx.loc[2018])),
    xytext=(2018, float(ghg_world_idx.loc[2018])),
    arrowprops=dict(arrowstyle="<->", color="#2196F3", lw=1.5)
)
ax.text(
    2018.3, (float(gdp_world_idx.loc[2018]) + float(ghg_world_idx.loc[2018])) / 2,
    "Relative\ndecoupling",
    color="#2196F3", fontsize=8.5, va="center"
)

# --- Annotation: absolute decoupling (EU) ---
# GHG EU goes down while GDP EU goes up → gap visible around 2019
ax.annotate(
    "",
    xy=(2007, float(gdp_eu_idx.loc[2007])),
    xytext=(2007, float(ghg_eu_idx.loc[2007])),
    arrowprops=dict(arrowstyle="<->", color="#4CAF50", lw=1.5)
)
ax.text(
    2007.3, (float(gdp_eu_idx.loc[2007]) + float(ghg_eu_idx.loc[2007])) / 2,
    "Absolute\ndecoupling",
    color="#4CAF50", fontsize=8.5, va="center"
)

ax.set_title("GDP vs. GHG emissions per capita (index 100 = 1994)", fontsize=14)
ax.set_xlabel("Year")
ax.set_ylabel("Index (base 100 in 1994)")
ax.legend(loc="upper left")
ax.set_xlim(1994, 2023)

plt.tight_layout()
plt.savefig(Path(__file__).parent.parent / "decoupling.png", dpi=150)
plt.show()
