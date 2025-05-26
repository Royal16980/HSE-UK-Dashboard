# scripts/build_csv.py
# (1) read the crawler Excel that lives in data/raw/
# (2) parse it into a tidy CSV, (3) save to docs/

import pandas as pd, re, pathlib, sys

RAW = pathlib.Path("data/raw/dataset_website-content-crawler.xlsx")
OUT = pathlib.Path("docs/convictions.csv")

if not RAW.exists():
    sys.exit("Input file not found")

df_raw = pd.read_excel(RAW, sheet_name="Data")

# --- super-simple parser (like the chat demo) --------------------------
detail_rows = df_raw[df_raw["url"].str.contains("case_details", na=False)]

records = []
for text, url in zip(detail_rows["text"], detail_rows["url"]):
    m_no = re.search(r"Case No\.?\s*\.?\s*(\d+)", text, re.I)
    m_def = re.search(r"Defendant\s+([^\n]+)", text, re.I)
    m_date = re.search(r"Offence Date\s+([\d/]{10})", text, re.I)
    m_la = re.search(r"Local Authority\s+([^\n]+)", text, re.I)
    m_desc = re.search(r"Description\s+([^\n]+)", text, re.I)
    m_fine = re.search(r"Total Fine\s+£\s*([\d,\.]+)", text, re.I)

    if not m_no:
        continue
    records.append({
        "Case Number": m_no.group(1),
        "Defendant Name": m_def.group(1) if m_def else "",
        "Offence Date": m_date.group(1) if m_date else "",
        "Local Authority": m_la.group(1) if m_la else "",
        "Offence Description": m_desc.group(1) if m_desc else "",
        "Total Fine": m_fine.group(1).replace(",", "") if m_fine else "",
        "Link to Full Case Details": url
    })

df = pd.DataFrame(records)
df.to_csv(OUT, index=False)
print(f"Wrote {len(df):,} rows → {OUT}")
