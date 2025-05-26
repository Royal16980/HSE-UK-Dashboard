# scripts/fetch_pfd_reports.py
"""
Scrapes the Judiciary website for Prevention-of-Future-Death reports
where 'Health and Safety Executive' (or obvious industrial keywords)
appear in the report summary.
"""

import requests, bs4, pathlib, csv, tqdm, re

BASE = "https://www.judiciary.uk/prevention-of-future-death-reports"
OUT  = pathlib.Path("data/reference/pfd_hse.csv")
pathlib.Path("data/reference").mkdir(parents=True, exist_ok=True)

records = []
page = 1
while True:
    url = f"{BASE}/page/{page}/"
    soup = bs4.BeautifulSoup(requests.get(url, timeout=30).text, "lxml")
    items = soup.select("article")
    if not items:
        break
    for art in items:
        title = art.select_one("h3").get_text(strip=True)
        link  = art.select_one("a")["href"]
        if re.search(r"health|safety|industrial|work", title, re.I):
            date = art.select_one("time")["datetime"][:10]
            records.append({"title": title, "url": link, "date": date})
    page += 1

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=records[0].keys())
    w.writeheader(); w.writerows(records)
print(f"PFD: {len(records)} rows → {OUT}")
