import os
import re

# File lookups
possible_filenames = [
    "EconomyAudit1_0.md",
    "EconomyAudit1_0.txt",
    "EconomyAudio1_0.md",
    "EconomyAudio1_0.txt",
]
raw_text = None

for fname in possible_filenames:
    if os.path.exists(fname):
        with open(fname, "r", encoding="utf-8") as f:
            raw_text = f.read()
        print(f"Loaded data from {fname}")
        break

if not raw_text:
    print("Using default text provided in prompt...")
    raw_text = """============================================================
  ELDEN EARTH — ECONOMY AUDIT   2026-10-22 02:21 UTC
============================================================

Players counted: 58  (demo accounts excluded: 1, seeded 25,000 EB)
------------------------------------------------------------
  WORLD TOTALS
------------------------------------------------------------
  EB (Elden Bucks)      40,940
  RC (Realm Coins)      23.9653
  Diamonds              10,381
  Lifetime rent (RC)    70.2084   <- all-time RC faucet
  RP (Reward Points)    4,003   <- redeemable liability (~$40.03)
  Plots owned           3,540
------------------------------------------------------------
  SINCE LAST RUN  (2026-10-22 02:18 UTC)
------------------------------------------------------------
  EB                            0 0%
  RC                            0 0%
  Diamonds                      0 0%
  Lifetime rent                 0 0%
  RP                            0 0%
  Plots                         0 0%
------------------------------------------------------------
  TOP 5 HOLDERS
------------------------------------------------------------
  EB:
    1. November Storm — 5,778
    2. Mathew Mack — 4,150
    3. Jim Haynes — 4,150
    4. Gretchen Alexander — 4,150
    5. Nadine Roy — 4,150
  RC:
    1. November Storm — 5.9762
    2. Jess — 3.7388
    3. imacatmeow — 2.3105
    4. Davinci Machen — 2.3044
    5. VicAdmin — 2.2159
  RP:
    1. Davinci Machen — 775
    2. November Storm — 646
    3. VicAdmin — 559
    4. Jess — 382
    5. imacatmeow — 366
============================================================"""


def extract_top5(currency_code):
    section_match = re.search(
        rf"{currency_code}:\n((?:\s+\d+\.\s+[^\n]+\n?){{1,5}})", raw_text
    )
    items = []
    if section_match:
        lines = section_match.group(1).strip().split("\n")
        for line in lines:
            m = re.match(r"\s*(\d+)\.\s+(.*?)\s*—\s*([\d,\.]+)", line)
            if m:
                items.append((m.group(1), m.group(2).strip(), m.group(3)))
    return items


top_eb = extract_top5("EB")
top_rc = extract_top5("RC")
top_rp = extract_top5("RP")

output_csv = "Economy_Audit_Report.csv"

rows = [
    ["ELDEN EARTH — ECONOMY AUDIT REPORT", "", "", "", "", "", ""],
    [
        "Audit Timestamp",
        "2026-10-22 02:21 UTC",
        "",
        "Total Players",
        "58",
        "Demo Accounts Excluded",
        "1",
    ],
    [],
    ["1. WORLD TOTALS & VELOCITY"],
    [
        "Metric / Token",
        "Current Supply",
        "Change Since Last Run",
        "% Growth",
        "Notes / Liability",
    ],
    ["EB (Elden Bucks)", "40940", "0", "0.0%", "Primary game currency"],
    ["RC (Realm Coins)", "23.9653", "0", "0.0%", "Crypto/faucet asset"],
    ["Diamonds", "10381", "0", "0.0%", "Premium token"],
    [
        "Lifetime Rent (RC)",
        "70.2084",
        "0",
        "0.0%",
        "All-time RC faucet emission",
    ],
    [
        "RP (Reward Points)",
        "4003",
        "0",
        "0.0%",
        "Redeemable liability (~$40.03)",
    ],
    ["Plots Owned", "3540", "0", "0.0%", "Total parcels claimed"],
    [],
    ["2. TOP 5 HOLDERS DISTRIBUTION"],
    [
        "Rank",
        "Player (EB)",
        "EB Amount",
        "",
        "Rank",
        "Player (RC)",
        "RC Amount",
    ],
]

for i in range(5):
    eb_rank, eb_player, eb_amt = top_eb[i] if i < len(top_eb) else ("", "", "")
    rc_rank, rc_player, rc_amt = top_rc[i] if i < len(top_rc) else ("", "", "")
    rows.append(
        [eb_rank, eb_player, eb_amt, "", rc_rank, rc_player, rc_amt]
    )

rows.append([])
rows.append(["3. REWARD POINTS (RP) LIABILITY"])
rows.append(
    ["Rank", "Player", "RP Balance", "Est. USD Liability ($0.01/RP)"]
)

for i in range(len(top_rp)):
    rp_rank, rp_player, rp_amt = top_rp[i]
    amt_clean = float(rp_amt.replace(",", ""))
    usd_val = f"${amt_clean * 0.01:.2f}"
    rows.append([rp_rank, rp_player, rp_amt, usd_val])

import csv

with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

print(f"Report generated successfully without external libraries: {output_csv}")