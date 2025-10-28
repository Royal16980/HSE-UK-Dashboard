import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

CSV = Path("docs/convictions.csv")
POP = Path("data/reference/ons_population.csv")
CENT = Path("data/reference/la_centroids.csv")

@st.cache_data
def load_data():
    df = pd.read_csv(CSV, parse_dates=["Offence Date"], dayfirst=True)
    if "cluster_name" not in df.columns:
        tfidf = TfidfVectorizer(stop_words="english", max_df=0.9, min_df=2)
        X = tfidf.fit_transform(df["Offence Description"].fillna(""))
        k = 6
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        order = km.cluster_centers_.argsort()[:, ::-1]
        terms = tfidf.get_feature_names_out()
        names = [", ".join(terms[order[i, :3]]) for i in range(k)]
        df["cluster_name"] = [names[l] for l in labels]
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
    return df


def build_scatter(df: pd.DataFrame) -> go.Figure:
    fig = px.scatter(
        df,
        x="Offence Date",
        y=df["Total Fine"].astype(float),
        hover_data=["Defendant Name", "Local Authority", "Offence Description"],
        color="cluster_name",
        title="HSE Convictions – Fine vs Offence Date",
        template="plotly",
    )
    fig.update_xaxes(rangeslider_visible=True)
    return fig


def build_map(df: pd.DataFrame) -> go.Figure:
    map_df = (
        df.dropna(subset=["lat", "lon"])
          .groupby(["Local Authority", "lat", "lon"], as_index=False)
          .agg(total_fine=("Total Fine", "sum"), fine_per_100k=("fine_per_100k", "mean"))
    )
    size_abs = np.sqrt(map_df["total_fine"] / 1e3) + 4
    size_pc = np.sqrt(map_df["fine_per_100k"].fillna(0)) + 4

    fig = go.Figure()
    fig.add_trace(go.Scattergeo(
        lat=map_df["lat"],
        lon=map_df["lon"],
        text=[f"<b>{la}</b><br>£{fine:,.0f}" for la, fine in zip(map_df["Local Authority"], map_df["total_fine"])],
        marker=dict(size=size_abs, color="#3B82F6", opacity=0.8, line_width=0.5),
        name="Total fine £",
    ))
    fig.add_trace(go.Scattergeo(
        lat=map_df["lat"],
        lon=map_df["lon"],
        text=[f"<b>{la}</b><br>£{pc:,.0f} /100k" for la, pc in zip(map_df["Local Authority"], map_df["fine_per_100k"])],
        marker=dict(size=size_pc, color="#F97316", opacity=0.8, line_width=0.5),
        name="Fine per 100k",
        visible=False,
    ))
    fig.update_layout(
        title="Local-authority bubble map",
        geo=dict(scope="europe", projection_type="mercator", center=dict(lat=54, lon=-2), fitbounds="locations"),
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=0, r=0, t=50, b=0),
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
    return fig


def main():
    st.set_page_config(page_title="HSE UK Dashboard", layout="wide")
    st.title("HSE UK Dashboard")
    df = load_data()

    tab1, tab2 = st.tabs(["Timeline", "Map"])
    with tab1:
        st.plotly_chart(build_scatter(df), use_container_width=True)
    with tab2:
        st.plotly_chart(build_map(df), use_container_width=True)


if __name__ == "__main__":
    main()
