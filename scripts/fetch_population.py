# scripts/fetch_population.py
import pandas as pd, requests, io, pathlib, re

OUT = pathlib.Path("data/reference/ons_population.csv")
URL = ("https://download.ukdataservice.ac.uk/datasets/"
       "ons/Population_Estimates_2023_MYE_Table_2.csv")

csv = requests.get(URL, timeout=30).content
df = pd.read_csv(io.BytesIO(csv))

# keep LAD rows only
df = df[df["geography"].str.match(r"E0|W0|S0|N0")]
df = df.rename(columns={"geography": "lad_code", "2023": "pop_2023"})
df[["lad_code", "pop_2023"]].to_csv(OUT, index=False)
print(f"Saved {OUT}")
