# scripts/fetch_imd.py
import pandas as pd, requests, io, pathlib

OUT = pathlib.Path("data/reference/imd_la.csv")
URL = ("https://assets.publishing.service.gov.uk/"
       "government/uploads/system/uploads/attachment_data/file/835374/"
       "File_14_LA_Summaries_IMD2019.xlsx")

xls = requests.get(URL, timeout=60).content
df = pd.read_excel(io.BytesIO(xls), sheet_name="IMD")

df = df.rename(columns={"Local Authority District code (2019)": "lad_code",
                        "Average rank": "imd_avg_rank",
                        "Decile": "imd_decile"})
df[["lad_code", "imd_avg_rank", "imd_decile"]].to_csv(OUT, index=False)
print(f"Saved {OUT}")
