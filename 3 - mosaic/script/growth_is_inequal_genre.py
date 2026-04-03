import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

XLS_PATH = r"C:\Users\challier\Documents\30DayChartChallenge\data\INSEE\ip1377.xls"

# =============================================================================
# DONNÉES
# =============================================================================

df_raw = pd.read_excel(XLS_PATH, sheet_name="Tab 1", header=None)

# Groupes : (label, index colonne dans le fichier)
GROUPS = [
    ("Employed men",   3),
    ("Unemployed men", 7),
    ("Employed women", 4),
    ("Unemployed women", 8),
]

# Activités : (label, index ligne dans le fichier)
# On prend les lignes "parent" qui agrègent leurs sous-catégories
ACTIVITIES = [
    ("Sleep & physiology", 5),
    ("Work & training",    9),
    ("Domestic tasks",     13),
    ("Leisure",            18),
]

# Palette
COLORS = [
    "#B58892",   # Sleep & physiology  — violet foncé
    "#F57A97",   # Work & training     — rouge
    "#85A089",   # Domestic tasks      — orange
    "#374D3A",   # Leisure             — bleu
    "#755E63",   # Other               — gris
]


def to_minutes(val):
    """Convertit une valeur HH:MM:SS (string, time ou timedelta) en minutes."""
    if pd.isna(val):
        return 0.0
    # timedelta (xlrd peut renvoyer des fractions de jour)
    if hasattr(val, "total_seconds"):
        return val.total_seconds() / 60
    # datetime.time
    if hasattr(val, "hour"):
        return val.hour * 60 + val.minute + val.second / 60
    # string "HH:MM:SS"
    s = str(val).strip()
    parts = s.split(":")
    if len(parts) >= 2:
        return int(parts[0]) * 60 + int(parts[1]) + (int(parts[2]) / 60 if len(parts) == 3 else 0)
    return 0.0


# Construction du DataFrame : lignes = activités, colonnes = groupes
records = []
for act_label, row_idx in ACTIVITIES:
    row = {"activity": act_label}
    for grp_label, col_idx in GROUPS:
        row[grp_label] = to_minutes(df_raw.iloc[row_idx, col_idx])
    records.append(row)

df = pd.DataFrame(records).set_index("activity").astype(float)

# Ajout d'une catégorie "Other" pour atteindre 1440 min (24h)
total_day = 24 * 60
df.loc["Other"] = total_day - df.sum(axis=0)

# Normalisation en % du jour
df_pct = (df / total_day * 100).astype(float)

# =============================================================================
# VISUALISATION — Marimekko / Mosaic chart
# Toutes les colonnes ont la même largeur (on compare des profils, pas des volumes)
# =============================================================================

BG = "#F4FDF5"
group_labels = [g for g, _ in GROUPS]
activities    = list(df_pct.index)
n_groups      = len(group_labels)
bar_width     = 1.0

fig, ax = plt.subplots(figsize=(12, 8))
fig.set_facecolor(BG)
ax.set_facecolor(BG)

bottoms = [0.0] * n_groups

for i, act in enumerate(activities):
    heights: list[float] = df_pct.loc[act, group_labels].tolist()
    bars = ax.bar(
        range(n_groups), heights,
        bottom=bottoms,
        width=bar_width,
        color=COLORS[i],
        edgecolor=BG,
        linewidth=1.2,
    )
    # Label au centre de chaque segment (si assez grand)
    for j, (h, b) in enumerate(zip(heights, bottoms)):
        if h > 4:
            # Temps en heures:minutes pour le label
            minutes = df.loc[act, group_labels[j]]
            h_int = int(minutes // 60)
            m_int = int(minutes % 60)
            ax.text(
                j, b + h / 2,
                f"{h_int}h{m_int:02d}",
                ha="center", va="center",
                fontsize=8.5, fontweight="bold", color="white",
            )
    bottoms = [b + h for b, h in zip(bottoms, heights)]

# --- Axes & style ---
ax.set_xticks(range(n_groups))
ax.set_xticklabels(group_labels, color="#5D6353", fontsize=11, fontweight="bold")
ax.set_ylim(0, 100)
ax.set_ylabel("% of the day (24h)", color="#5D6353", fontsize=10)
ax.tick_params(axis="y", colors="#5D6353")
ax.tick_params(axis="x", length=0)
for spine in ax.spines.values():
    spine.set_visible(False)
ax.yaxis.grid(True, color="#FFFAF6", linewidth=0.6, zorder=0)
ax.set_axisbelow(True)

# --- Légende ---
legend_patches = [
    mpatches.Patch(color=COLORS[i], label=act)
    for i, act in enumerate(activities)
]
ax.legend(
    handles=legend_patches,
    loc="upper right",
    bbox_to_anchor=(1.18, 1),
    frameon=False,
    fontsize=9,
    labelcolor="#5D6353",
)

# --- Titre & source ---
ax.set_title(
    "How is a day spent?\nEmployed vs. unemployed, men vs. women — France, 2010",
    color="#5D6353", fontsize=13, fontweight="bold", pad=16, loc="left",
)
fig.text(
    0.98, 0.01,
    "Source: INSEE, Enquête Emploi du Temps 2010 (ip1377)",
    ha="right", va="top",
    fontsize=7, color="#5D6353", fontstyle="italic",
)

plt.tight_layout()
plt.savefig(
    r"3 - mosaic\output\growth_is_inequal_genre.png",
    dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor(),
)
plt.show()
