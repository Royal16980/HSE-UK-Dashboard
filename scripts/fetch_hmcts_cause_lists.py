# scripts/fetch_hmcts_cause_lists.py
"""
Downloads HMCTS daily cause-list PDFs, extracts rows where the
'Claimant' is the Health & Safety Executive, writes tidy CSV.
"""

import pdfplumber, pathlib, requests, io, re, csv, datetime as dt, tqdm

OUT = pathlib.Path("data/reference/hmcts_upcoming.csv")
BASE = "https://www.gov.uk"

# The master HTML page lists PDF links for ~70 courts each day
LIST_URL = f"{BASE}/government/collections/hmcts-hearing-lists"

html = requests.get(LIST_URL, timeout=60).text
pdf_links = re.findall(r'href=\"(/government/uploads/[^\"]+\\.pdf)\"', html)

records = []
for link in tqdm.tqdm(pdf_links, desc="PDFs"):
    url = BASE + link
    pdf = pdfplumber.open(io.BytesIO(requests.get(url, timeout=60).content))
    for page in pdf.pages:
        text = page.extract_text() or ""
        for line in text.splitlines():
            if "Health and Safety Executive" in line:
                # crude parse: split by multiple spaces
                parts = re.split(r" {2,}", line.strip())
                if len(parts) >= 3:
                    records.append({
                        "court": pdf.metadata.get("Title", "")[:80],
                        "hearing_date": pdf.metadata.get("ModDate", "")[2:10],
                        "case_ref": parts[1],
                        "defendant": parts[2]
                    })
    pdf.close()

# save
pathlib.Path("data/reference").mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=records[0].keys())
    w.writeheader(); w.writerows(records)
print(f"HMCTS: {len(records)} rows → {OUT}")
