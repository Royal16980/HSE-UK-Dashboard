"""
Creates docs/pending_cases.csv by combining:
  * HMCTS upcoming hearings
  * HSE live enforcement notices
  * Coroners PFD reports
Key fields: signal_type, date, defendant/company, la, ref/url
"""

import pandas as pd, pathlib, datetime as dt

ref = pathlib.Path("data/reference")
hmcts  = pd.read_csv(ref/"hmcts_upcoming.csv")      .assign(signal="hearing")
notices = pd.read_csv(ref/"hse_notices.csv")        .assign(signal="notice")
pfd     = pd.read_csv(ref/"pfd_hse.csv")            .assign(signal="pfd")

# thin to common cols
hmcts_t  = hmcts.rename(columns={"defendant":"subject"})[
    ["signal","hearing_date","subject","court","case_ref"]]
notices_t = notices.rename(columns={"Company":"subject","IssueDate":"date"})[
    ["signal","date","subject","NoticeNumber","NoticeType","Status"]]
pfd_t = pfd.rename(columns={"date":"date","title":"subject","url":"ref"})[
    ["signal","date","subject","ref"]]

pending = pd.concat([hmcts_t, notices_t, pfd_t], ignore_index=True)
pending.to_csv("docs/pending_cases.csv", index=False)
print(f"Pending signals: {len(pending):,} rows → docs/pending_cases.csv")
