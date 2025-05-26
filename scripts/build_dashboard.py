"""
Elegant multi‑tab HSE dashboard builder
--------------------------------------
Creates **docs/index.html** with:
  ▸ Tab 1 – Timeline scatter (fine vs offence date)
  ▸ Tab 2 – Bubble map (toggle absolute / per‑capita)
  ▸ Smooth fade‑in transitions between tabs (CSS + JavaScript)
  ▸ Dark‑mode friendly colour palette

It uses only Plotly + a tiny vanilla‑JS tab switcher, so the output
is a single self‑contained HTML file—no React or Dash server needed.
"""
from pathlib import Path
import pandas as pd, numpy as np, plotly.express as px, plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

CSV   = Path("docs/convictions.csv")
POP   = Path("data/reference/ons_population.csv")
CENT  = Path("data/reference/la_centroids.csv")
HTML  = Path("docs/index.html")

# ------------------------------------------------------------------
# Load convictions --------------------------------------------------
# ------------------------------------------------------------------
if not CSV.exists():
    raise FileNotFoundError("docs/convictions.csv missing – run build_csv.py first")

df = pd.read_csv(CSV, parse_dates=["Offence Date"], dayfirst=True)

# ------------------------------------------------------------------
# Cluster offence description (quick TF‑IDF) ------------------------
# ------------------------------------------------------------------
if "cluster_name" not in df.columns:
    tfidf = TfidfVectorizer(stop_words="english", max_df=0.9, min_df=2)
    X = tfidf.fit_transform(df["Offence Description"].fillna(""))
    k  = 6
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    order  = km.cluster_centers_.argsort()[:, ::-1]
    terms  = tfidf.get_feature_names_out()
    names  = [", ".join(terms[order[i, :3]]) for i in range(k)]
    df["cluster_name"] = [names[l] for l in labels]

# ------------------------------------------------------------------
# Timeline scatter --------------------------------------------------
# ------------------------------------------------------------------
scatter = px.scatter(
    df,
    x="Offence Date",
    y=df["Total Fine"].astype(float),
    hover_data=["Defendant Name", "Local Authority", "Offence Description"],
    color="cluster_name",
    title="HSE Convictions – Fine vs Offence Date",
    template="plotly"   # dark‑mode compatible
)
scatter.update_xaxes(rangeslider_visible=True)
scatter_html = scatter.to_html(full_html=False, include_plotlyjs="cdn")

# ------------------------------------------------------------------
# Map overlay -------------------------------------------------------
# ------------------------------------------------------------------
if CENT.exists():
    cent = pd.read_csv(CENT)
    df = df.merge(cent, left_on="Local Authority", right_on="name", how="left")
else:
    df["lat"] = df["lon"] = np.nan

if POP.exists():
    pop = pd.read_csv(POP)
    df = df.merge(pop, on="lad_code", how="left")
    df["fine_per_100k"] = df["Total Fine"] / df["pop_2023"].replace(0, np.nan) * 1e5
else:
    df["fine_per_100k"] = np.nan

map_df = (
    df.dropna(subset=["lat", "lon"])
      .groupby(["Local Authority", "lat", "lon"], as_index=False)
      .agg(total_fine=("Total Fine", "sum"), fine_per_100k=("fine_per_100k", "mean"))
)
size_abs = np.sqrt(map_df["total_fine"]/1e3) + 4
size_pc  = np.sqrt(map_df["fine_per_100k"].fillna(0)) + 4

fig_map = go.Figure()
fig_map.add_trace(go.Scattergeo(
    lat=map_df["lat"], lon=map_df["lon"],
    text=[f"<b>{la}</b><br>£{fine:,.0f}" for la, fine in zip(map_df["Local Authority"], map_df["total_fine"])],
    marker=dict(size=size_abs, color="#3B82F6", opacity=0.8, line_width=0.5),
    name="Total fine £"
))
fig_map.add_trace(go.Scattergeo(
    lat=map_df["lat"], lon=map_df["lon"],
    text=[f"<b>{la}</b><br>£{pc:,.0f} /100k" for la, pc in zip(map_df["Local Authority"], map_df["fine_per_100k"])],
    marker=dict(size=size_pc, color="#F97316", opacity=0.8, line_width=0.5),
    name="Fine per 100k",
    visible=False
))
fig_map.update_layout(
    title="Local‑authority bubble map",
    geo=dict(scope="europe", projection_type="mercator", center=dict(lat=54, lon=-2), fitbounds="locations"),
    legend=dict(x=0.01, y=0.99),
    margin=dict(l=0, r=0, t=50, b=0)
)
fig_map.update_layout(
    updatemenus=[{
        "buttons": [
            {"label": "Total fine £", "method": "update", "args": [{"visible": [True, False]}]},
            {"label": "Fine per 100k", "method": "update", "args": [{"visible": [False, True]}]},
        ],
        "direction": "left",
        "x": 0.5,
        "y": 1.18,
        "pad": {"r": 10, "t": 10},
    }]
)
map_html = fig_map.to_html(full_html=False, include_plotlyjs=False)

# ------------------------------------------------------------------
# Build HTML shell with tabbed layout + fade transitions -------------
# ------------------------------------------------------------------
HTML.write_text(f"""
<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='utf-8'>
<title>HSE UK Dashboard</title>
<link rel='preconnect' href='https://fonts.gstatic.com'>
<link href='https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap' rel='stylesheet'>
<style>
  body{{font-family:Inter,Segoe UI,Helvetica Neue,Arial,sans-serif;margin:0;background:#f7f8fa;color:#111;}}
  header{{padding:1.2rem 1.8rem;border-bottom:1px solid #e5e7eb;background:#fff;}}
  h1{{margin:0;font-size:1.5rem;color:#0f172a;}}
  nav button{{background:#e5e7eb;border:none;padding:0.6rem 1rem;margin:0 0.2rem;border-radius:0.4rem;font-weight:600;cursor:pointer;transition:background 0.3s;}}
  nav button.active,nav button:hover{{background:#3b82f6;color:#fff;}}
  section{{display:none;opacity:0;transform:scale(0.98);transition:opacity 0.4s,transform 0.4s;}}
  section.show{{display:block;opacity:1;transform:scale(1);}}
</style>
</head>
<body>
<header>
  <h1>HSE UK Dashboard</h1>
  <nav>
    <button id='tab-timeline' class='active' onclick="showTab('timeline')">Timeline</button>
    <button id='tab-map' onclick="showTab('map')">Map</button>
  </nav>
</header>
<section id='timeline' class='show'>
  {scatter_html}
</section>
<section id='map'>
  {map_html}
</section>
<script>
function showTab(id){{
  document.querySelectorAll('section').forEach(s=>s.classList.remove('show'));
  document.querySelectorAll('nav button').forEach(b=>b.classList.remove('active'));
  document.getElementById(id).classList.add('show');
  document.getElementById('tab-'+id).classList.add('active');
}}
</script>
</body>
</html>
""", encoding="utf-8")
print(f"Dashboard written → {HTML}")
