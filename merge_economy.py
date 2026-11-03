import glob
import os
import pandas as pd

# 1. Get the folder where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# 2. Look for all CSV files in the SAME folder as the script
pattern = os.path.join(script_dir, "player-growth-*.csv")
csv_files = sorted(glob.glob(pattern))

if not csv_files:
    print(f"No CSV files matching 'player-growth-*.csv' found in:\n{script_dir}")
    exit()

print(f"Reading {len(csv_files)} files from the current folder...")
df_list = [pd.read_csv(f) for f in csv_files]
master_df = pd.concat(df_list, ignore_index=True)

# 3. Clean numeric columns
numeric_cols = [
    "Plots Owned",
    "New Plots",
    "Total RC",
    "Total RP (EOD)",
    "Total EB (EOD)",
    "Plot Purchasing Power",
]
for col in numeric_cols:
    if col in master_df.columns:
        master_df[col] = pd.to_numeric(master_df[col], errors="coerce").fillna(
            0
        )

# 4. Identify Top 20 Players on the latest date available
latest_date = master_df["Date"].max()
latest_snapshot = master_df[master_df["Date"] == latest_date]

# Rank by Total EB (change to 'Total RC' if you prefer)
top_20_players = latest_snapshot.sort_values(
    by="Total EB (EOD)", ascending=False
).head(20)
top_20_uids = top_20_players["UID"].tolist()

print(f"Identified Top 20 players as of {latest_date}.")

# 5. Filter for Top 20 across all days and build Pivot Tables
top_df = master_df[master_df["UID"].isin(top_20_uids)].copy()

# Add short UID to player name to avoid duplicate column names
top_df["Player_Label"] = (
    top_df["Player"] + " (" + top_df["UID"].str[:4] + ")"
)

# Pivots: Rows = Date, Columns = Each Player
pivot_eb = top_df.pivot_table(
    index="Date",
    columns="Player_Label",
    values="Total EB (EOD)",
    aggfunc="first",
).fillna(0)

pivot_rc = top_df.pivot_table(
    index="Date", columns="Player_Label", values="Total RC", aggfunc="first"
).fillna(0)

# 6. Overall Macro Economy Summary
daily_summary = (
    master_df.groupby("Date")
    .agg(
        Total_Players=("UID", "count"),
        Active_Today=(
            "Last Active",
            lambda s: (s == master_df.loc[s.index, "Date"]).sum(),
        ),
        Total_Plots=("Plots Owned", "sum"),
        Total_EB_Supply=("Total EB (EOD)", "sum"),
        Total_RC_Supply=("Total RC", "sum"),
    )
    .reset_index()
    .sort_values("Date")
)

# 7. Save output directly in the current directory
output_file = os.path.join(script_dir, "Game_Economy_Report.xlsx")

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    pivot_eb.to_excel(writer, sheet_name="Top 20 EB History")
    pivot_rc.to_excel(writer, sheet_name="Top 20 RC History")
    daily_summary.to_excel(writer, sheet_name="Macro Economy", index=False)
    master_df.to_excel(writer, sheet_name="Master Raw Data", index=False)

print(f"\nDone! File created at:\n{output_file}")