# scripts/fetch_fatals.py
import pandas as pd, requests, io, pathlib

OUT = pathlib.Path("data/reference/fatal_cases.csv")
URL = ("https://www.hse.gov.uk/statistics/tables/fatalinjuries.xlsx")

xls = requests.get(URL, timeout=60).content
df = pd.read_excel(io.BytesIO(xls), sheet_name="Table3", skiprows=4)

df = df.rename(columns={"Local Authority": "lad_code",
                        "Number of fatal injuries": "fatal_2023"})
df[["lad_code", "fatal_2023"]].to_csv(OUT, index=False)
print(f"Saved {OUT}")
