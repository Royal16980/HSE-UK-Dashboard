"""
Reads the crawler Excel in data/raw/, extracts basic fields,
writes tidy CSV to docs/convictions.csv
"""
import re, pathlib, pandas as pd, sys

RAW = pathlib.Path("data/raw").glob("*.xlsx")
RAW = next(RAW, None)
if RAW is None:
    sys.exit("No .xlsx found in data/raw/")

print(f"Parsing {RAW} …")

df_raw = pd.read_excel(RAW, sheet_name="Data")
detail_rows = df_raw[df_raw["url"].str.contains("case_details", na=False)]

records = []
for text, url in zip(detail_rows["text"], detail_rows["url"]):
    m_case = re.search(r"Case No\.?\s*\.?\s*(\d+)", text, re.I)
    if not m_case:
        continue
    def grab(label, patt):
        m = re.search(patt, text, re.I)
        return m.group(1).strip() if m else ""
    records.append({
        "Case Number":         m_case.group(1),
        "Defendant Name":      grab("Defendant",        r"Defendant\s+([^\n]+)"),
        "Offence Date":        grab("Offence Date",     r"Offence Date\s+([\d/]{10})"),
        "Local Authority":     grab("Local Authority",  r"Local Authority\s+([^\n]+)"),
        "Offence Description": grab("Description",      r"Description\s+([^\n]+)"),
        "Total Fine":          grab("Total Fine",       r"Total Fine\s+£\s*([\d,\.]+)").replace(",",""),
        "Link to Full Case Details": url
    })

out = pathlib.Path("docs/convictions.csv")
pd.DataFrame(records).to_csv(out, index=False)
print(f"Wrote {len(records)} rows → {out}")
