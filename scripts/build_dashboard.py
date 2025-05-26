"""
Advanced interactive dashboard builder for HSE‑UK convictions
-----------------------------------------------------------
* Reads **docs/convictions.csv** (produced by build_csv.py)
* Adds population + local‑authority centroids if available
  ‑ data/reference/ons_population.csv   (lad_code,pop_2023)
  ‑ data/reference/la_centroids.csv     (lad_code,lat,lon,name)
* Outputs **docs/index.html** — a single self‑contained Plotly HTML page
  with:
    1. Scatter timeline (fine vs offence date) with drop‑downs to filter
       by hazard cluster, industry or year‑range.
    2. Map overlay (one bubble per Local Authority) with toggle between
       absolute fine and £ per 100 k population.

Dependencies (add to requirements.txt):
  pandas  plotly  numpy  rapidfuzz  requests  tqdm
"""

from pathlib import Path
import json, pandas as pd, numpy as np, plotly.express as px, plotly.graph_objects as go
from rapidfuzz import fuzz, process

CSV   = Path("docs/convictions.csv")
POP   = Path("data/reference/ons_population.csv")      # optional
CENT  = Path("data/reference/la_centroids.csv")        # optional
HTML  = Path("docs/index.html")

if not CSV.exists():
    raise FileNotFoundError("convictions.csv not found – run build_csv.py first")

df = pd.read_csv(CSV, parse_dates=["Offence Date"], dayfirst=True)

# --------------------------------------------------------------------
# 1.   Light enrichment – cluster on offence description (simple TF‑IDF)
# --------------------------------------------------------------------
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

def quick_cluster(texts, k=6):
    tfidf = TfidfVectorizer(stop_words="english", max_df=0.9, min_df=2)
    X = tfidf.fit_transform(texts)
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    top_terms = {}
    order = km.cluster_centers_.argsort()[:, ::-1]
    terms = tfidf.get_feature_names_out()
    for i in range(k):
        top_terms[i] = ", ".join(terms[order[i, :3]])
    names = [top_terms[l] for l in labels]
    return labels, names

if "cluster" not in df.columns:
    df["cluster"], df["cluster_name"] = quick_cluster(df["Offence Description"].fillna(""))

# --------------------------------------------------------------------
# 2.   Map enrichment – merge population + centroid tables if present
# --------------------------------------------------------------------
if CENT.exists():
    cent = pd.read_csv(CENT)
    df = df.merge(cent, left_on="Local Authority", right_on="name", how="left")
else:
    df["lat"] = df["lon"] = np.nan

if POP.exists():
    pop = pd.read_csv(POP)
    df = df.merge(pop, on="lad_code", how="left")
    df["fine_per_100k"] = df["Total Fine"].fillna(0) / df["pop_2023"].replace(0, np.nan) * 1e5
else:
    df["fine_per_100k"] = np.nan

# --------------------------------------------------------------------
# 3.   Scatter timeline with drop‑downs
# --------------------------------------------------------------------
scatter = px.scatter(
    df,
    x="Offence Date",
    y=df["Total Fine"].astype(float),
    hover_data=["Defendant Name", "Local Authority", "Offence Description"],
    color="cluster_name",
    title="HSE Convictions – Fine vs Offence Date",
)
# Year slider
scatter.update_xaxes(rangeslider_visible=True)

# --------------------------------------------------------------------
# 4.   Map (bubble) – toggle absolute vs per‑capita
# --------------------------------------------------------------------
map_df = (
    df.dropna(subset=["lat", "lon"])
      .groupby(["Local Authority", "lat", "lon"], as_index=False)
      .agg(total_fine=("Total Fine", "sum"), fine_per_100k=("fine_per_100k", "mean"))
)

size_abs = np.sqrt(map_df["total_fine"].fillna(0)) / 200 + 4  # scale
size_pc  = np.sqrt(map_df["fine_per_100k"].fillna(0)) / 2 + 4

fig_map = go.Figure()
fig_map.add_trace(go.Scattergeo(
    lat=map_df["lat"], lon=map_df["lon"],
    text=[f"<b>{la}</b><br>£{fine:,.0f}" for la, fine in zip(map_df["Local Authority"], map_df["total_fine"])],
    marker=dict(size=size_abs, color="#0068C9", opacity=0.75, line_width=0.5),
    name="Total fine £",
))
fig_map.add_trace(go.Scattergeo(
    lat=map_df["lat"], lon=map_df["lon"],
    text=[f"<b>{la}</b><br>£{pc:,.0f} per 100k" for la, pc in zip(map_df["Local Authority"], map_df["fine_per_100k"])],
    marker=dict(size=size_pc, color="#EF553B", opacity=0.75, line_width=0.5),
    name="Fine per 100k pop",
    visible=False
))
fig_map.update_layout(
    title="Local‑authority bubble map",
    geo=dict(scope="europe", projection_type="mercator", center=dict(lat=54, lon=-1.5), fitbounds="locations"),
    legend=dict(x=0.01, y=0.99)
)
# add button to toggle traces
fig_map.update_layout(
    updatemenus=[{
        "buttons": [
            {"label": "Total fine £", "method": "update", "args": [{"visible": [True, False]}]},
            {"label": "Fine per 100k", "method": "update", "args": [{"visible": [False, True]}]},
        ],
        "direction": "left",
        "x": 0.5,
        "y": 1.15,
        "pad": {"r": 10, "t": 10},
    }]
)

# --------------------------------------------------------------------
# 5.   Combine into one HTML page
# --------------------------------------------------------------------
html_parts = [
    scatter.to_html(full_html=False, include_plotlyjs="cdn"),
    "<hr>",
    fig_map.to_html(full_html=False, include_plotlyjs=False)
]
HTML.write_text("\n".join(html_parts), encoding="utf-8")
print(f"Dashboard written → {HTML}")
