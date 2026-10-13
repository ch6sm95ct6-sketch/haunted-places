# Do ghosts prefer schools, hotels or cemeteries?

**Marie Piekarek (I6416514) · MAT2007**

This project compares the representation of schools, hotels and cemeteries in a collection of US haunting reports, then compares keyword mentions in their descriptions. It measures patterns in collected reports, not whether ghosts exist or the probability that a building is haunted.

## Repository contents

- `ghostanalysis.py`: the Python analysis and plotting code.
- `README.md`: data provenance, cleaning rules and instructions for reproduction.
- `report.pdf`: the short report, exported from Overleaf after compiling `report.tex`.
- `report.tex`: editable LaTeX report source, referencing the two accompanying PNG graphs.

The generated `ghost_results` folder contains figures and CSV tables. It is created automatically and does not need to be uploaded for the script to run. The report requires `locations.png` and `phenomena.png` in the same Overleaf project as `report.tex`. Both graphs are included in the project ZIP. This repository is for the haunted-places project, separate from the molecular-asymmetry project.

## Dataset and provenance

The source is [TidyTuesday's 10 October 2023 dataset](https://github.com/rfordatascience/tidytuesday/tree/main/data/2023/2023-10-10), **Haunted Places in the United States**. Tim Renner compiled the reports from the Shadowlands Haunted Places Index.

[Download the source CSV](https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2023/2023-10-10/haunted_places.csv).

The script downloads this CSV on its first run and caches it as `ghost_results/haunted_places.csv`. If that file exists, it uses the cached copy. An internet connection is needed only when downloading. Required columns are `location`, `description`, `city` and `state`; geographic coordinates are not used.

The tested cached copy contains 10,992 rows. Its SHA-256 checksum is:

```text
da584a9dc3cc9daf6fecb9346508730fba8eaa586dc718382db6116a36285930
```

This checksum identifies the local cached CSV used for the reported run; a freshly downloaded CSV saved by another pandas version may differ in formatting. The upstream URL uses the main branch and could change. Keep the tested cached file if exact reproduction is required.

## Installation and execution

Use Python 3 and a terminal in the folder containing `ghostanalysis.py`. The analysis was tested with Python 3.14.7, pandas 3.0.6 and Matplotlib 3.11.2.

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install pandas==3.0.6 matplotlib==3.11.2
python ghostanalysis.py
```

If using an existing environment, activate it and run the last two commands there. The imports `pathlib`, `math` and `re` are part of Python's standard library. No user input is needed while the program runs.

The script needs permission to create and write a `ghost_results` folder beside itself. It uses an existing cached dataset if available and overwrites generated figures and result CSVs when rerun. It does not modify the cached dataset during cleaning. For a machine without a graphical display, run:

```bash
MPLBACKEND=Agg python ghostanalysis.py
```

For offline use, first create `ghost_results` beside the script and put the original `haunted_places.csv` inside it. Do not put a manually filtered dataset there.

## Cleaning and selection

No manual cleaning is needed to reproduce these results; the script performs the following steps:

1. Read the CSV and check the required columns.
2. Remove exact duplicates across all columns: 2 rows removed, leaving 10,990.
3. Replace missing values in the four text columns with empty strings. In this snapshot, 3 location names and 3 city values are missing; no descriptions are missing.
4. Search **location names**, case-insensitively with whole-word regular expressions, for category keywords.
5. Retain only records matching exactly one category. Exclude 6 ambiguous matches and 7,475 unmatched records.

| Category | Included keywords, with plural variants |
|---|---|
| Schools | school, university, college, academy |
| Hotels | hotel, motel, inn, resort |
| Cemeteries | cemetery, graveyard, burial ground |

The 3,509 selected reports represent 31.9% of the cleaned dataset. A record is a listed place/report, not necessarily a unique building or an independent event. Exact duplicate removal does not establish independence.

## Methods and uncertainty

Location shares use the same denominator, **3,509 selected reports**. Phenomenon percentages use the number of reports **within each category**. The script searches descriptions for:

- Footsteps: footsteps or footfalls.
- Voices: voices, whispers or screams and the variants defined in the code.
- Apparitions: apparitions, figures or shadows.
- Moving objects: an object/chair/furniture/door keyword followed within 50 characters, without crossing `.`, `!` or `?`, by a movement/opening/slamming/closing keyword.

Matches indicate words, not verified experiences. Negation is not resolved. Reports can match several groups or none, so percentages need not sum to 100%.

For `k` matches among `n` reports, `p = k/n`. The script reports the binary sample SD, the plug-in standard error `sqrt(p*(1-p)/n)`, and individual 95% Wilson intervals with `z = 1.959963984540054`. Percentages and SEs are expressed in percent and percentage points, respectively. Binary SD is on the 0–1 scale and is not an uncertainty on the mean.

Wilson intervals assume independent reports. They are model-based intervals, not corrections for reporting bias, unknown building totals or imperfect keyword classification. They are not adjusted for multiple comparisons.

## Main results

| Category | Reports | Share of selected reports | 95% Wilson interval |
|---|---:|---:|---:|
| Schools | 2,125 | 60.6% | 58.9–62.2% |
| Hotels | 580 | 16.5% | 15.3–17.8% |
| Cemeteries | 804 | 22.9% | 21.6–24.3% |

Schools are the largest category among the selected records. Moving-object keywords occur in 257 school reports (12.1%) but only 9 cemetery reports (1.1%), a descriptive difference of about 11 percentage points. This does not establish a causal effect of location.

| Category | Footsteps | Voices | Apparitions | Moving objects |
|---|---:|---:|---:|---:|
| Schools | 8.9% | 14.5% | 15.4% | 12.1% |
| Hotels | 9.0% | 11.7% | 18.1% | 10.9% |
| Cemeteries | 3.1% | 15.2% | 19.8% | 1.1% |

The report includes both supplied graphs: category shares with Wilson intervals and the phenomenon-percentage heatmap. Running the code produces the original presentation-style graphs as PNG and PDF files.

## Generated files

All outputs go to `ghost_results`, beside the script:

| File | Purpose |
|---|---|
| `haunted_places.csv` | Cached source data |
| `classified_locations.csv` | Cleaned records with classification labels |
| `classification_review.csv` | Up to ten sampled records per selected category, seed 42 |
| `location_statistics.csv` | Counts, shares, SD, SE and Wilson intervals |
| `phenomena_percentages.csv` | Within-category keyword percentages |
| `phenomena_statistics.csv` | Counts and uncertainties for each keyword/category combination |
| `phenomenon_count_summary.csv` | Mean and sample SD of the number of keyword groups per report |
| `01_haunted_locations_red.png` / `.pdf` | Category shares with Wilson error bars |
| `02_haunting_phenomena_red.png` / `.pdf` | Keyword-percentage heatmap |

The script was rerun on the supplied cached dataset and reproduced the presentation's category counts and percentages. The review sample is exported for inspection; no measured classification-accuracy rate or completed human validation is claimed.

## Limitations and conclusion

Voluntary reports are not a random sample of US buildings. Building totals and reporting rates are unknown, and stories may be dependent. Keyword rules can miss or misinterpret phrases. Consequently, the findings describe this collection under these selection rules: schools account for most selected reports and keyword content differs between settings. They do not establish that ghosts prefer schools or that schools have a higher haunting risk.

## Compile the short report

`report.tex` follows the teacher's headings: Introduction, Data sample, Results and discussion, and References. Its title is compact rather than on a separate cover page to respect the two-page maximum.

Create your own Overleaf project, upload `report.tex`, `locations.png` and `phenomena.png`, select `report.tex` as the main document and use pdfLaTeX. Click Recompile, check that the resulting report is at most two pages, then download it as `report.pdf`. Upload that PDF alongside this README and `ghostanalysis.py` in your haunted-places repository. The LaTeX source can also be kept for reproducibility. Do not edit the teacher's shared template directly.
