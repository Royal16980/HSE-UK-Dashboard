"""
Reads docs/convictions.csv and creates an interactive Plotly HTML
saved to docs/index.html
"""
import pathlib, pandas as pd, plotly.express as px

CSV = pathlib.Path("docs/convictions.csv")
if not CSV.exists():
    raise FileNotFoundError("convictions.csv not found - run build_csv.py first")

df = pd.read_csv(CSV, parse_dates=["Offence Date"], dayfirst=True)

fig = px.scatter(
    df,
    x="Offence Date",
    y=df["Total Fine"].astype(float),
    hover_data=["Defendant Name","Local Authority","Offence Description"],
    title="HSE Convictions – Fine vs Offence Date"
)

out = pathlib.Path("docs/index.html")
fig.write_html(out, include_plotlyjs='cdn')
print(f"Dashboard written → {out}")
