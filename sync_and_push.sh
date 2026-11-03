#!/bin/bash

SOURCE_DIR="/Users/vic/git/1/EE/functions"
REPO_DIR="/Users/vic/Elden Earth Blog Posts/EconomyReport"

echo "=== Sync started at $(date) ==="

cd "$REPO_DIR" || exit 1

# 1. Pull remote changes while clean
git pull origin main --quiet

# 2. Copy and SANITIZE CSV files (completely strip UID column)
python3 -c "
import glob, csv, os
src = '$SOURCE_DIR'
dst = '$REPO_DIR'
for f in glob.glob(os.path.join(src, 'player-growth-*.csv')):
    fname = os.path.basename(f)
    out_path = os.path.join(dst, fname)
    with open(f, 'r', encoding='utf-8-sig') as infile:
        reader = csv.DictReader(infile)
        fieldnames = [c for c in reader.fieldnames if c != 'UID']
        rows = []
        for row in reader:
            row.pop('UID', None)
            rows.append(row)
    with open(out_path, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
print('All CSVs sanitized: UID column completely removed.')
"

# 3. Build latest index.html
python3 generate_dashboard.py

# 4. Stage sanitized CSVs and index.html
git add player-growth-*.csv index.html

# 5. Commit and push only if changes exist
if ! git diff --cached --quiet; then
    DATE_STR=$(date "+%Y-%m-%d")
    git commit -m "Auto: daily economy data sync $DATE_STR"
    git push origin main
    echo "Successfully pushed daily sanitized updates for $DATE_STR!"
else
    echo "No new updates to push today. Repo is already up to date."
fi

echo "=== Sync finished ==="
