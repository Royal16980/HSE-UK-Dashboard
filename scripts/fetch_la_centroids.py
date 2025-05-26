# scripts/fetch_la_centroids.py
import pandas as pd, requests, io, pathlib, sys

OUT = pathlib.Path("data/reference/la_centroids.csv")
URL = ("https://raw.githubusercontent.com/mysociety/"
       "uk_local_authority_names_and_codes/main/data/uk_local_authorities.csv")

csv = requests.get(URL, timeout=30).content
df = pd.read_csv(io.BytesIO(csv))

keep = (df
        .loc[:, ["gss-code", "nice-name", "lat", "long"]]
        .rename(columns={"gss-code": "lad_code",
                         "nice-name": "name",
                         "long": "lon"}))

keep.to_csv(OUT, index=False)
print(f"Saved {OUT}  ({len(keep):,} rows)")
