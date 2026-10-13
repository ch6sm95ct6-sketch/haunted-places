from pathlib import Path
from math import sqrt
import re

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.colors import LinearSegmentedColormap


# =======================================================
# 1. SETTINGS AND COLOURS
# =======================================================

OUTPUT = Path(__file__).resolve().parent / "ghost_results"
OUTPUT.mkdir(exist_ok=True)

DATA_URL = (
    "https://raw.githubusercontent.com/rfordatascience/"
    "tidytuesday/main/data/2023/2023-10-10/haunted_places.csv"
)

CATEGORIES = ["Schools", "Hotels", "Cemeteries"]

LOCATION_PATTERNS = {
    "Schools": (
        r"\b(schools?|universit(?:y|ies)|"
        r"colleges?|academ(?:y|ies))\b"
    ),
    "Hotels": r"\b(hotels?|motels?|inns?|resorts?)\b",
    "Cemeteries": (
        r"\b(cemeter(?:y|ies)|graveyards?|burial grounds?)\b"
    ),
}

# These detect keyword mentions, not verified events.
PHENOMENA = {
    "Footsteps": r"\b(footsteps?|footfalls?)\b",
    "Voices": r"\b(voices?|whisper(?:s|ing)?|scream(?:s|ing)?)\b",
    "Apparitions": r"\b(apparitions?|figures?|shadows?)\b",
    "Moving objects": (
        r"\b(objects?|chairs?|furniture|doors?)\b"
        r"[^.!?]{0,50}\b"
        r"(mov(?:e[sd]?|ing)|open(?:s|ed|ing)?|"
        r"slam(?:s|med|ming)?|clos(?:e[sd]?|ing))\b"
    ),
}

# Palette inspired by your presentation.
BACKGROUND = "#080A0B"
PANEL = "#151719"
TEXT = "#F2EAE6"
MUTED = "#B5AAA6"

COLORS = [
    "#C65B51",  # Schools: red lamplight
    "#98665D",  # Hotels: muted brick red
    "#87999D",  # Cemeteries: misty blue-grey
]

plt.rcParams.update({
    "figure.facecolor": BACKGROUND,
    "axes.facecolor": PANEL,
    "savefig.facecolor": BACKGROUND,
    "text.color": TEXT,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": TEXT,
    "font.family": "DejaVu Sans",
    "font.size": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.spines.bottom": False,
})


# =======================================================
# 2. DOWNLOAD AND CLEAN THE DATA
# =======================================================

data_file = OUTPUT / "haunted_places.csv"

if data_file.exists():
    print("Loading the saved dataset...")
    data = pd.read_csv(data_file)
else:
    print("Downloading the dataset...")
    data = pd.read_csv(DATA_URL)
    data.to_csv(data_file, index=False)

required_columns = {"location", "description", "city", "state"}

if not required_columns.issubset(data.columns):
    raise ValueError(
        f"Dataset must contain these columns: {required_columns}"
    )

original_rows = len(data)
data = data.drop_duplicates().copy()

for column in required_columns:
    data[column] = data[column].fillna("").astype(str)

print(f"Original rows: {original_rows:,}")
print(f"Exact duplicate rows removed: {original_rows - len(data):,}")


# =======================================================
# 3. CLASSIFY LOCATIONS
# =======================================================

def classify_location(name):
    """Classify using location names, rather than descriptions."""

    matches = [
        category
        for category, pattern in LOCATION_PATTERNS.items()
        if re.search(pattern, name, flags=re.IGNORECASE)
    ]

    if len(matches) == 1:
        return matches[0]

    if len(matches) > 1:
        return "Ambiguous"

    return "Other / unclassified"


data["category"] = data["location"].apply(classify_location)

selected = data[
    data["category"].isin(CATEGORIES)
].copy()

counts = (
    selected["category"]
    .value_counts()
    .reindex(CATEGORIES, fill_value=0)
)

n_total = len(selected)

if n_total < 2:
    raise ValueError("At least two classified reports are needed.")

data.to_csv(
    OUTPUT / "classified_locations.csv",
    index=False
)

# Export up to 10 reports per category for manual review.
review = pd.concat([
    group.sample(n=min(10, len(group)), random_state=42)
    for _, group in selected.groupby("category")
])

review[
    ["location", "city", "state", "category", "description"]
].to_csv(
    OUTPUT / "classification_review.csv",
    index=False
)


# =======================================================
# 4. STANDARD DEVIATION AND UNCERTAINTY
# =======================================================

def calculate_statistics(k, n):
    """
    k: number of matching reports
    n: total number of reports in the comparison

    SD measures variation in individual 0/1 observations.
    SE measures uncertainty in the estimated proportion.

    Confidence intervals assume independent reports.
    They exclude reporting bias and classification errors.
    """

    if n == 0:
        return {
            "reports": k,
            "denominator": n,
            "percentage": float("nan"),
            "sample_SD_binary": float("nan"),
            "standard_error_pp": float("nan"),
            "CI95_lower_percent": float("nan"),
            "CI95_upper_percent": float("nan"),
        }

    p = k / n

    # Sample SD of binary observations, using divisor n - 1.
    sd = (
        sqrt(n * p * (1 - p) / (n - 1))
        if n > 1 else float("nan")
    )

    # Plug-in binomial standard error.
    se = sqrt(p * (1 - p) / n)

    # Individual 95% Wilson confidence interval.
    z = 1.959963984540054
    denominator = 1 + z**2 / n

    centre = (
        p + z**2 / (2 * n)
    ) / denominator

    half_width = (
        z
        * sqrt(
            p * (1 - p) / n
            + z**2 / (4 * n**2)
        )
        / denominator
    )

    lower = max(0, centre - half_width)
    upper = min(1, centre + half_width)

    return {
        "reports": k,
        "denominator": n,
        "percentage": p * 100,
        "sample_SD_binary": sd,
        "standard_error_pp": se * 100,
        "CI95_lower_percent": lower * 100,
        "CI95_upper_percent": upper * 100,
    }


location_rows = []

for category in CATEGORIES:
    result = calculate_statistics(
        k=int(counts[category]),
        n=n_total
    )

    location_rows.append({
        "category": category,
        **result
    })

statistics = pd.DataFrame(
    location_rows
).set_index("category")

statistics.to_csv(
    OUTPUT / "location_statistics.csv"
)

print("\nLOCATION STATISTICS")
print(statistics.round(3).to_string())

print("\nSD: sample standard deviation of the 0/1 indicator.")
print("SE: standard error in percentage points.")
print("CI: individual 95% Wilson confidence interval.")


# =======================================================
# 5. FIRST GRAPH: LOCATIONS WITH ERROR BARS
# =======================================================

fig, ax = plt.subplots(figsize=(12, 7.5))

fig.subplots_adjust(
    left=0.18,
    right=0.94,
    top=0.72,
    bottom=0.26
)

fig.text(
    0.08, 0.92,
    "THE HAUNTING INDEX",
    fontsize=11,
    weight="bold",
    color=COLORS[0]
)

fig.text(
    0.08, 0.85,
    "Do ghosts have a favourite place?",
    fontsize=25,
    weight="bold"
)

fig.text(
    0.08, 0.79,
    "Schools, hotels and cemeteries in a US collection of haunting reports",
    fontsize=12,
    color=MUTED
)

percentages = statistics["percentage"]

left_errors = (
    percentages - statistics["CI95_lower_percent"]
)

right_errors = (
    statistics["CI95_upper_percent"] - percentages
)

bars = ax.barh(
    CATEGORIES,
    percentages,
    color=COLORS,
    height=0.55,
    zorder=3
)

ax.errorbar(
    x=percentages.to_numpy(),
    y=list(range(len(CATEGORIES))),
    xerr=[
        left_errors.to_numpy(),
        right_errors.to_numpy()
    ],
    fmt="none",
    ecolor=TEXT,
    elinewidth=2,
    capsize=7,
    capthick=2,
    zorder=5
)

ax.invert_yaxis()
ax.set_xlim(0, 95)

ax.set_xticks([0, 20, 40, 60, 80])
ax.xaxis.set_major_formatter(
    PercentFormatter(xmax=100)
)

ax.set_xlabel(
    "Share of reports in these three categories",
    labelpad=15
)

ax.tick_params(
    axis="both",
    length=0,
    pad=10
)

ax.grid(
    axis="x",
    color=TEXT,
    alpha=0.07,
    zorder=0
)

for bar, category in zip(bars, CATEGORIES):
    row = statistics.loc[category]

    y = bar.get_y() + bar.get_height() / 2
    label_x = row["CI95_upper_percent"] + 1.4

    ax.text(
        label_x,
        y - 0.08,
        f'{row["percentage"]:.1f}%  ·  '
        f'{int(row["reports"]):,} reports',
        va="center",
        fontsize=11,
        weight="bold",
        color=TEXT
    )

    ax.text(
        label_x,
        y + 0.12,
        f'95% CI: {row["CI95_lower_percent"]:.1f}'
        f'–{row["CI95_upper_percent"]:.1f}%',
        va="center",
        fontsize=9,
        color=MUTED
    )

fig.text(
    0.08, 0.15,
    f"{n_total:,} classified reports  •  "
    "White error bars show model-based 95% Wilson intervals",
    fontsize=10,
    color=MUTED
)

fig.text(
    0.08, 0.105,
    "Intervals assume independent reports and exclude reporting bias "
    "and keyword-classification errors.",
    fontsize=9,
    color=MUTED
)

fig.text(
    0.08, 0.065,
    "More reports do not imply greater haunting risk. "
    "Building totals and reporting rates are unknown.",
    fontsize=9,
    color=MUTED
)

fig.text(
    0.08, 0.025,
    "Source: Shadowlands Haunted Places Index / Tim Renner / TidyTuesday",
    fontsize=9,
    color=MUTED
)

fig.savefig(
    OUTPUT / "01_haunted_locations_red.png",
    dpi=300
)

fig.savefig(
    OUTPUT / "01_haunted_locations_red.pdf"
)

plt.close(fig)


# =======================================================
# 6. ANALYSE PHENOMENA
# =======================================================

for phenomenon, pattern in PHENOMENA.items():
    selected[phenomenon] = selected["description"].apply(
        lambda description: bool(
            re.search(
                pattern,
                description,
                flags=re.IGNORECASE
            )
        )
    )

# Percentage mentioning each phenomenon within each category.
rates = (
    selected.groupby("category")[list(PHENOMENA)]
    .mean()
    .reindex(CATEGORIES)
    * 100
)

rates.round(2).to_csv(
    OUTPUT / "phenomena_percentages.csv"
)

# Save SD, SE and confidence intervals for every heatmap cell.
phenomenon_rows = []

for category in CATEGORIES:
    group = selected[selected["category"] == category]

    for phenomenon in PHENOMENA:
        result = calculate_statistics(
            k=int(group[phenomenon].sum()),
            n=len(group)
        )

        phenomenon_rows.append({
            "category": category,
            "phenomenon": phenomenon,
            **result
        })

pd.DataFrame(phenomenon_rows).to_csv(
    OUTPUT / "phenomena_statistics.csv",
    index=False
)

# Additional numerical summary:
# number of detected phenomenon types per report, from 0 to 4.
selected["phenomenon_types_mentioned"] = (
    selected[list(PHENOMENA)].sum(axis=1)
)

phenomenon_count_summary = (
    selected.groupby("category")["phenomenon_types_mentioned"]
    .agg(["count", "mean", "std"])
    .reindex(CATEGORIES)
    .rename(columns={"std": "sample_SD"})
)

phenomenon_count_summary.to_csv(
    OUTPUT / "phenomenon_count_summary.csv"
)

print("\nNUMBER OF PHENOMENON TYPES MENTIONED PER REPORT")
print(phenomenon_count_summary.round(3).to_string())


# =======================================================
# 7. SECOND GRAPH: PHENOMENA HEATMAP
# =======================================================

cmap = LinearSegmentedColormap.from_list(
    "haunted_hallway",
    [
        "#090B0D",
        "#382020",
        "#783732",
        "#C65B51",
        "#F0C2AD",
    ]
)

cmap.set_bad(PANEL)

fig, ax = plt.subplots(figsize=(12, 7.5))

fig.subplots_adjust(
    left=0.18,
    right=0.88,
    top=0.72,
    bottom=0.25
)

fig.text(
    0.08, 0.92,
    "THE STORIES BEHIND THE SIGHTINGS",
    fontsize=11,
    weight="bold",
    color=COLORS[2]
)

fig.text(
    0.08, 0.85,
    "Footsteps, whispers and things that move",
    fontsize=23,
    weight="bold"
)

fig.text(
    0.08, 0.79,
    "Percentage of reports in each category mentioning a selected phenomenon",
    fontsize=12,
    color=MUTED
)

# Keep the original 0–100% scale.
image = ax.imshow(
    rates.to_numpy(),
    cmap=cmap,
    vmin=0,
    vmax=100,
    aspect="auto"
)

ax.set_xticks(
    range(len(PHENOMENA)),
    labels=list(PHENOMENA)
)

ax.set_yticks(
    range(len(CATEGORIES)),
    labels=[
        f"{category}\n(n = {counts[category]:,})"
        for category in CATEGORIES
    ]
)

ax.tick_params(
    axis="both",
    length=0,
    pad=12
)

# Gaps between cells.
ax.set_xticks([0.5, 1.5, 2.5], minor=True)
ax.set_yticks([0.5, 1.5], minor=True)

ax.grid(
    which="minor",
    color=BACKGROUND,
    linewidth=5
)

ax.tick_params(which="minor", length=0)

for row in range(len(CATEGORIES)):
    for column in range(len(PHENOMENA)):
        value = rates.iloc[row, column]

        label = (
            "N/A"
            if pd.isna(value)
            else f"{value:.1f}%"
        )

        label_color = (
            BACKGROUND
            if pd.notna(value) and value > 75
            else TEXT
        )

        ax.text(
            column,
            row,
            label,
            ha="center",
            va="center",
            fontsize=17,
            weight="bold",
            color=label_color
        )

colorbar = fig.colorbar(
    image,
    ax=ax,
    fraction=0.035,
    pad=0.035
)

colorbar.set_label(
    "Reports mentioning phenomenon (%)",
    labelpad=12
)

colorbar.outline.set_visible(False)

fig.text(
    0.08, 0.13,
    "A report may mention multiple phenomena, so row percentages "
    "need not sum to 100%.",
    fontsize=10,
    color=MUTED
)

fig.text(
    0.08, 0.08,
    "Keyword matches are approximate: they can miss synonyms "
    "or include negated statements.",
    fontsize=9,
    color=MUTED
)

fig.text(
    0.08, 0.035,
    "Source: Shadowlands Haunted Places Index / Tim Renner / TidyTuesday",
    fontsize=9,
    color=MUTED
)

fig.savefig(
    OUTPUT / "02_haunting_phenomena_red.png",
    dpi=300
)

fig.savefig(
    OUTPUT / "02_haunting_phenomena_red.pdf"
)

plt.close(fig)


# =======================================================
# 8. FINISHED
# =======================================================

print(f"\nGraphs and statistics saved in:\n{OUTPUT}")

print("\nGraphs:")
print("  01_haunted_locations_red.png")
print("  02_haunting_phenomena_red.png")

print("\nStatistics:")
print("  location_statistics.csv")
print("  phenomena_statistics.csv")
print("  phenomenon_count_summary.csv")

print(
    "\nCheck classification_review.csv manually "
    "before drawing final conclusions."
) 