import math
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import ConnectionPatch

# --- Chargement des données ---
df = pd.read_csv(
    "data/OMS/Morticd10_part6",
    low_memory=False
)

# --- Filtrage France, année 2023, hors code "AAA" (total toutes causes) ---
df_fr = df[
    (df["Country"] == 4080) &
    (df["Year"] == 2023) &
    (df["Cause"] != "AAA")
].copy()

# =============================================================================
# CATÉGORIES DE CAUSES DE DÉCÈS
# Basées sur la structure ICD-10 (OMS 2019)
# =============================================================================

# --- 1. Maladies transmissibles (Chapitre I + codes U spéciaux) ---
TRANSMISSIBLES_RAW = [
    ("A00", "B99", "Maladies transmissibles"),
    ("U04", "U04", "Maladies transmissibles"),  # SARS (U049)
    ("U07", "U07", "Maladies transmissibles"),  # COVID-19 (U071, U072)
]

# --- 2. MNT liées à la pollution/environnement (Tableau 8 OMS) ---
MNT_POLLUTION_RAW = [
    ("C33", "C34", "Cancers des voies respiratoires"),
    ("C32", "C32", "Cancers des voies respiratoires"),
    ("C67", "C67", "Cancer de la vessie"),
    ("C43", "C43", "Mélanome malin de la peau"),
    ("I20", "I25", "Cardiopathies ischémiques"),
    ("I60", "I69", "Maladies cérébrovasculaires (AVC)"),
    ("J40", "J47", "Maladies respiratoires chroniques"),
    ("J60", "J98", "Maladies respiratoires chroniques"),
    ("E10", "E14", "Diabète sucré"),
    ("G30", "G30", "Maladie d'Alzheimer"),
    ("K70", "K76", "Maladies du foie"),
    ("N00", "N15", "Maladies rénales"),
]

# --- 3. Autres MNT (chapitres II–XIV, XVI–XVII hors codes pollution) ---
# Note : chaque plage doit rester dans la même lettre (limite de expand_icd10_range)
AUTRES_MNT_RAW = [
    ("C00", "C99", "Cancers (autres)"),          # Chapitre II — C (hors codes pollution déjà pris)
    ("D00", "D48", "Cancers (autres)"),          # Chapitre II — D (tumeurs in situ, bénignes)
    ("D50", "D89", "Maladies du sang"),
    ("E00", "E09", "Maladies endocriniennes / métaboliques (autres)"),
    ("E15", "E90", "Maladies endocriniennes / métaboliques (autres)"),
    ("F00", "F99", "Troubles mentaux et comportementaux"),
    ("G00", "G29", "Maladies du système nerveux (autres)"),
    ("G31", "G99", "Maladies du système nerveux (autres)"),
    ("H00", "H59", "Maladies de l'œil"),
    ("H60", "H95", "Maladies de l'oreille"),
    ("I00", "I19", "Maladies cardiovasculaires (autres)"),
    ("I26", "I59", "Maladies cardiovasculaires (autres)"),
    ("I70", "I99", "Maladies cardiovasculaires (autres)"),
    ("J00", "J39", "Maladies respiratoires (autres)"),
    ("K00", "K69", "Maladies digestives (autres)"),
    ("K77", "K93", "Maladies digestives (autres)"),
    ("L00", "L99", "Maladies de la peau"),
    ("M00", "M99", "Maladies musculo-squelettiques"),
    ("N16", "N99", "Maladies génito-urinaires (autres)"),
    ("Q00", "Q99", "Malformations congénitales"),
]

# --- 4. Autres causes (traumatismes, causes externes, périnatal, grossesse…) ---
# Note : plages scindées par lettre
AUTRES_RAW = [
    ("O00", "O99", "Grossesse et accouchement"),
    ("P00", "P96", "Affections périnatales"),
    ("R00", "R99", "Symptômes non classifiés"),
    ("S00", "S99", "Traumatismes et empoisonnements"),  # Chapitre XIX — S
    ("T00", "T98", "Traumatismes et empoisonnements"),  # Chapitre XIX — T
    ("V00", "V99", "Causes externes"),                  # Chapitre XX — V
    ("W00", "W99", "Causes externes"),                  # Chapitre XX — W
    ("X00", "X99", "Causes externes"),                  # Chapitre XX — X
    ("Y00", "Y98", "Causes externes"),                  # Chapitre XX — Y
    ("Z00", "Z99", "Facteurs influençant la santé"),
]

# =============================================================================
# FONCTIONS UTILITAIRES
# =============================================================================

def expand_icd10_range(start, end):
    """Génère tous les préfixes ICD-10 à 3 caractères entre start et end inclus."""
    letter = start[0]
    return [
        f"{letter}{i:02d}"
        for i in range(int(start[1:]), int(end[1:]) + 1)
    ]

def build_prefix_list(raw_list):
    """Construit une liste de (préfixe_3chars, label) depuis une liste de plages."""
    return [
        (code, label)
        for start, end, label in raw_list
        for code in expand_icd10_range(start, end)
    ]

# Ordre de priorité : MNT pollution d'abord, puis transmissibles, puis autres MNT, puis autres
CATEGORY_PREFIXES = [
    ("MNT — pollution / environnement", build_prefix_list(MNT_POLLUTION_RAW)),
    ("Maladies transmissibles",          build_prefix_list(TRANSMISSIBLES_RAW)),
    ("MNT — autres",                     build_prefix_list(AUTRES_MNT_RAW)),
    ("Autres causes",                    build_prefix_list(AUTRES_RAW)),
]

def get_category(cause):
    """Retourne la catégorie principale pour un code cause ICD-10."""
    cause_str = str(cause)
    for category, prefixes in CATEGORY_PREFIXES:
        for prefix, _ in prefixes:
            if cause_str.startswith(prefix):
                return category
    return "Non classifié"

def get_mnt_label(cause):
    """Retourne le label détaillé si la cause est une MNT pollution."""
    cause_str = str(cause)
    for prefix, label in build_prefix_list(MNT_POLLUTION_RAW):
        if cause_str.startswith(prefix):
            return label
    return None

# =============================================================================
# CALCULS
# =============================================================================

df_fr["category"]  = df_fr["Cause"].apply(get_category)
df_fr["mnt_label"] = df_fr["Cause"].apply(get_mnt_label)

total_all_years = df_fr["Deaths1"].sum()

# --- DIAGNOSTIC : top 10 causes non classifiées (pour vérifier le format des codes) ---
non_classifie = df_fr[df_fr["category"] == "Non classifié"]
print("=== DIAGNOSTIC : top 10 codes non classifiés (par nb de décès) ===")
print(
    non_classifie.groupby("Cause")["Deaths1"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
    .to_string()
)
print()

# --- Vue d'ensemble par grande catégorie ---
by_category = (
    df_fr.groupby("category")["Deaths1"]
    .sum()
    .reset_index()
    .rename(columns={"Deaths1": "deaths"})
    .sort_values("deaths", ascending=False)
)
by_category["pct"] = (by_category["deaths"] / total_all_years * 100).round(2)

# --- Détail MNT pollution par maladie ---
df_mnt = df_fr[df_fr["mnt_label"].notna()]
by_mnt_disease = (
    df_mnt.groupby("mnt_label")["Deaths1"]
    .sum()
    .reset_index()
    .rename(columns={"Deaths1": "deaths", "mnt_label": "maladie"})
    .sort_values("deaths", ascending=False)
)
total_mnt = by_mnt_disease["deaths"].sum()
by_mnt_disease["pct_total_FR"]      = (by_mnt_disease["deaths"] / total_all_years * 100).round(2)
by_mnt_disease["pct_mnt_pollution"] = (by_mnt_disease["deaths"] / total_mnt * 100).round(2)

# =============================================================================
# AFFICHAGE
# =============================================================================

print("=== Total décès France 2023 ===")
print(f"{total_all_years:,.0f} décès\n")

print("=== Répartition par grande catégorie ===")
print(by_category.to_string(index=False))

print(f"\n=== Détail MNT liées à la pollution/environnement ===")
print(by_mnt_disease.to_string(index=False))
print(f"\n--- Total MNT pollution : {total_mnt:,.0f} décès ({total_mnt/total_all_years*100:.2f}% du total FR)")

# =============================================================================
# VISUALISATION — Deux donuts côte à côte
# Donut 1 : MNT / Maladies transmissibles / Autres causes (100% des décès)
# Donut 2 : au sein des MNT — MNT pollution vs MNT autres
# =============================================================================

BG = "#180714"
C_MNT_POLL  = "#B91000"
C_MNT_AUTRE = "#B403FF"
C_TRANSM    = "#650F85"
C_AUTRES    = "#A58FBD"

# --- Agrégation pour le donut 1 ---
cat = by_category.set_index("category")["deaths"]

d1_mnt     = cat.get("MNT — pollution / environnement", 0) + cat.get("MNT — autres", 0)
d1_transm  = cat.get("Maladies transmissibles", 0)
d1_autres  = (cat.get("Autres causes", 0) + cat.get("Non classifié", 0))

d1_values  = [d1_mnt, d1_transm, d1_autres]
d1_labels  = ["NCDs", "Infectious diseases", "Other causes"]
d1_colors  = [C_MNT_AUTRE, C_TRANSM, C_AUTRES]
d1_pcts    = [v / total_all_years * 100 for v in d1_values]

# --- Agrégation pour le donut 2 ---
d2_poll    = cat.get("MNT — pollution / environnement", 0)
d2_autres  = cat.get("MNT — autres", 0)
total_mnt_all = d2_poll + d2_autres

d2_values  = [d2_poll, d2_autres]
d2_labels  = ["Pollution-related NCDs", "Other NCDs (tobacco use, \n unhealthy diets, insufficient physical activity...)"]
d2_colors  = [C_MNT_POLL, C_AUTRES]
d2_pcts    = [v / total_mnt_all * 100 for v in d2_values]

# --- Figure ---
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 7))
fig.set_facecolor(BG)

def draw_donut(ax, values, labels, colors, pcts, center_line1, center_line2):
    ax.set_facecolor(BG)
    startAngle = -180*values[0]
    wedges, *_ = ax.pie(values, colors=colors, startangle=startAngle,
                        wedgeprops=dict(width=0.45, edgecolor=BG, linewidth=2))
    # Pourcentages placés au milieu de chaque arc (angles réels des wedges)
    for wedge, pct in zip(wedges, pcts):
        angle = (wedge.theta1 + wedge.theta2) / 2
        r = 0.725  # milieu de l'anneau (inner=0.55, outer=1.0)
        x = r * math.cos(math.radians(angle))
        y = r * math.sin(math.radians(angle))
        ax.text(x, y, f"{pct:.1f}%", ha="center", va="center",
                fontsize=10, fontweight="bold", color="#F1D0F7")
    # Texte central
    ax.text(0, 0.12, center_line1, ha="center", va="center",
            fontsize=18, fontweight="bold", color="#F1D0F7")
    ax.text(0, -0.1, center_line2, ha="center", va="center",
            fontsize=11, fontweight="bold", color="#F1D0F7", linespacing=1.5)
    # Légende sous le donut
    patches = [mpatches.Patch(color=c, label=l)
               for c, l in zip(colors, labels)]
    ax.legend(handles=patches, loc="lower center", bbox_to_anchor=(0.3, -0.06),
              ncol=1, frameon=False, fontsize=11, labelcolor="#F1D0F7")
    return wedges

wedges1 = draw_donut(ax1, d1_values, d1_labels, d1_colors, d1_pcts,
                     f"{d1_mnt/total_all_years*100:.1f}%", "of deaths\nare NCDs")

wedges2 = draw_donut(ax2, d2_values, d2_labels, d2_colors, d2_pcts,
                     f"{d2_poll/total_mnt_all*100:.1f}%", "of NCDs\nare pollution-related")


fig.suptitle("Mortality in France — 2023\nShare of NCDs and the role of pollution",
             color="#F1D0F7", fontsize=20, fontweight="bold", y=0.86)

plt.tight_layout(rect=(0, 0.08, 1, 0.95))

sources = (
    "Sources: WHO ICD-10 — icd.who.int/browse10/2019/en\n"
    "WHO Non-Communicable Diseases — who.int/health-topics/noncommunicable-diseases\n"
    "Cicolella A., The cost of inaction on NCDs, L'Économie Politique, 2018"
)
fig.text(0.98, 0, sources, ha="right", va="bottom",
         fontsize=6.5, color="#F1D0F7", fontstyle="italic", linespacing=1.6)

plt.savefig(r"1 - part-to-whole\output\MNT_donut_FR_20231.png", dpi=150,
            bbox_inches="tight", facecolor=fig.get_facecolor())
plt.show()
