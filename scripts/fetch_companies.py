# scripts/fetch_companies.py
import pathlib, zipfile, csv, requests, io, pyarrow as pa, pyarrow.parquet as pq, tqdm

PARTS = range(1, 16)   # Parts 1–15
OUT   = pathlib.Path("data/reference/companies.parquet")
COLUMNS = ["CompanyName", "CompanyNumber", "RegAddress.PostCode",
           "SICCode.SicText_1", "CompanyStatus"]

rows = []
for p in PARTS:
    url = f"https://download.companieshouse.gov.uk/BasicCompanyData-Part{p}.zip"
    print(f"Downloading Part {p}…")
    zbytes = io.BytesIO(requests.get(url, stream=True).content)
    with zipfile.ZipFile(zbytes) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            for row in tqdm.tqdm(csv.DictReader(io.TextIOWrapper(f, 'utf-8'))):
                rows.append({k: row.get(k, "") for k in COLUMNS})

table = pa.Table.from_pylist(rows)
pq.write_table(table, OUT)
print(f"Wrote {OUT}  ({len(rows):,} companies)")
