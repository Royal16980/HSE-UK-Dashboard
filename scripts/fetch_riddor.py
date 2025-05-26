# scripts/fetch_riddor.py
import pandas as pd, pathlib, requests, io

OUT = pathlib.Path("data/reference/riddor_la.csv")
URL = ("https://www.hse.gov.uk/statistics/tables/"
       "ridreg.xlsx")

xls = requests.get(URL, timeout=60).content
df = pd.read_excel(io.BytesIO(xls), sheet_name="Table1", skiprows=4)

df = df.rename(columns={"Local authority": "lad_code",
                        "Total non-fatal injuries": "injuries_2023"})
df[["lad_code", "injuries_2023"]].to_csv(OUT, index=False)
print(f"Saved {OUT}")
