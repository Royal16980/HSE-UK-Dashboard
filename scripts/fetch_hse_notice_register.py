# scripts/fetch_hse_notice_register.py
"""
Pulls the HSE Improvement / Prohibition Notice Register via the
pre-filtered CSV endpoint and stores a slimmed file.
"""

import pandas as pd, pathlib, tempfile, requests

OUT = pathlib.Path("data/reference/hse_notices.csv")
URL = ("https://resources.hse.gov.uk/notices/"
       "resources/notices_data_export.csv")   # 30–40 MB

csv = requests.get(URL, timeout=120).content
df = pd.read_csv(pd.compat.StringIO(csv.decode("utf-8")))

keep = df[["NoticeNumber", "NoticeType", "Company", "LocalAuthority",
           "SICCode", "IssueDate", "Status"]]

keep.to_csv(OUT, index=False)
print(f"HSE Notices: {len(keep):,} rows → {OUT}")
