import os
import glob
import csv
import json
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_files = sorted(glob.glob(os.path.join(script_dir, "player-growth-*.csv")))

if not csv_files:
    print("No CSV files found matching 'player-growth-*.csv'!")
    exit()

print(f"Reading {len(csv_files)} files...")

all_rows = []
for fpath in csv_files:
    with open(fpath, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_rows.append(row)

def safe_float(val, default=0.0):
    try:
        return float(val)
    except (ValueError, TypeError):
        return default

# 1. Identify Real Players (Plots Owned > 0 AND Total RC > 0)
real_players = set()
for r in all_rows:
    plots = safe_float(r.get("Plots Owned", 0))
    rc = safe_float(r.get("Total RC", 0))
    player = r.get("Player")
    if plots > 0 and rc > 0 and player:
        real_players.add(player)

# 2. Extract Individual Player Histories
players_data = {}
for r in all_rows:
    player = r.get("Player")
    if player not in real_players:
        continue

    date = r.get("Date")
    plots = int(safe_float(r.get("Plots Owned", 0)))
    eb = round(safe_float(r.get("Total EB (EOD)", 0)), 2)
    rc = round(safe_float(r.get("Total RC", 0)), 4)
    rp = round(safe_float(r.get("Total RP (EOD)", 0)), 2)

    if player not in players_data:
        players_data[player] = {
            "name": player,
            "plots": plots,
            "dates": [],
            "eb": [],
            "rc": [],
            "rp": [],
            "plots_history": []
        }

    p = players_data[player]
    p["plots"] = plots
    p["dates"].append(date)
    p["eb"].append(eb)
    p["rc"].append(rc)
    p["rp"].append(rp)
    p["plots_history"].append(plots)

sorted_players = sorted(players_data.items(), key=lambda x: x[1]["plots"], reverse=True)
players_json = json.dumps(players_data)
sorted_names_json = json.dumps([name for name, _ in sorted_players])

# 3. Global Growth
all_dates = sorted(list(set(r.get("Date") for r in all_rows if r.get("Date"))))

player_first_date = {}
for name, p in players_data.items():
    player_first_date[name] = min(p["dates"])

global_dates = all_dates
daily_new_players = []
cumulative_players = []
running_total = 0

for d in global_dates:
    new_count = sum(1 for name, f_date in player_first_date.items() if f_date == d)
    running_total += new_count
    daily_new_players.append(new_count)
    cumulative_players.append(running_total)

global_data = {
    "dates": global_dates,
    "total": cumulative_players,
    "new": daily_new_players,
    "latest_total": cumulative_players[-1] if cumulative_players else 0,
    "latest_new": daily_new_players[-1] if daily_new_players else 0
}
global_json = json.dumps(global_data)

last_sync_time = datetime.now().strftime("%b %d, %Y - %I:%M %p")

# 4. Generate HTML
html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
<title>Player Economy Terminal</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  :root {{
    --bg-dark: #131722;
    --card-bg: #1e222d;
    --border: #2a2e39;
    --accent: #2962ff;
    --text-main: #d1d4dc;
    --text-muted: #787b86;
    --green: #089981;
    --gold: #f7a600;
  }}
  * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
  body {{
    margin: 0; padding: 12px; background: var(--bg-dark);
    color: var(--text-main); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  .top-bar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }}
  .title {{ font-size: 1.15rem; font-weight: 700; color: #fff; }}
  .sync-badge {{
    font-size: 0.72rem; color: var(--text-muted); background: var(--card-bg);
    padding: 5px 8px; border-radius: 6px; border: 1px solid var(--border);
    cursor: pointer;
  }}
  select {{
    width: 100%; background: var(--card-bg); color: #fff; border: 1px solid var(--border);
    padding: 12px; font-size: 1rem; border-radius: 8px; outline: none; margin-bottom: 10px;
  }}
  .stats-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 12px; }}
  .stat-card {{ background: var(--card-bg); padding: 10px 12px; border-radius: 8px; border: 1px solid var(--border); }}
  .stat-label {{ font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; }}
  .stat-val {{ font-size: 1.1rem; font-weight: 700; margin-top: 3px; color: #fff; }}
  .controls {{ display: flex; gap: 6px; margin-bottom: 12px; overflow-x: auto; }}
  .tab-btn {{
    flex: 1; padding: 10px 6px; background: var(--card-bg); border: 1px solid var(--border);
    color: var(--text-muted); border-radius: 6px; font-size: 0.82rem; font-weight: 600; text-align: center;
  }}
  .tab-btn.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  .chart-box {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px;
    padding: 10px; height: 330px; position: relative; margin-bottom: 24px;
  }}
  .divider {{ height: 1px; background: var(--border); margin: 24px 0 16px 0; }}
</style>
</head>
<body>

<div class="top-bar">
  <div class="title">📈 Player Economy Terminal</div>
  <div class="sync-badge" onclick="window.location.reload(true)">🔄 {last_sync_time}</div>
</div>

<select id="playerSelect" onchange="updatePlayer()"></select>

<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-label">Plots Owned</div>
    <div class="stat-val" id="statPlots" style="color: var(--green);">0</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Total EB</div>
    <div class="stat-val" id="statEB">0</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Total RC</div>
    <div class="stat-val" id="statRC" style="color: var(--gold);">0</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">Total RP</div>
    <div class="stat-val" id="statRP">0</div>
  </div>
</div>

<div class="controls">
  <button class="tab-btn active player-btn" onclick="setMetric('eb', this)">Total EB</button>
  <button class="tab-btn player-btn" onclick="setMetric('rc', this)">Total RC</button>
  <button class="tab-btn player-btn" onclick="setMetric('plots_history', this)">Plots</button>
  <button class="tab-btn player-btn" onclick="setMetric('rp', this)">Total RP</button>
</div>

<div class="chart-box">
  <canvas id="tradingChart"></canvas>
</div>

<div class="divider"></div>

<div class="header">
  <div class="title">🌐 Global Real Player Growth</div>
</div>

<div class="stats-grid">
  <div class="stat-card">
    <div class="stat-label">Total Real Players</div>
    <div class="stat-val" style="color: var(--green);" id="globalTotal">{global_data['latest_total']}</div>
  </div>
  <div class="stat-card">
    <div class="stat-label">New Real Players (Latest Day)</div>
    <div class="stat-val" style="color: var(--accent);" id="globalNew">+{global_data['latest_new']}</div>
  </div>
</div>

<div class="controls">
  <button class="tab-btn active global-btn" onclick="setGlobalMetric('total', this)">Total Players</button>
  <button class="tab-btn global-btn" onclick="setGlobalMetric('new', this)">New Players Joined</button>
</div>

<div class="chart-box">
  <canvas id="globalChart"></canvas>
</div>

<script>
const players = {players_json};
const sortedNames = {sorted_names_json};
const globalData = {global_json};

let currentMetric = 'eb';
let chartInstance = null;
let globalChartInstance = null;
let currentGlobalMetric = 'total';

const select = document.getElementById('playerSelect');
sortedNames.forEach(name => {{
  const opt = document.createElement('option');
  opt.value = name;
  opt.innerText = `${{name}} (${{players[name].plots}} plots)`;
  select.appendChild(opt);
}});

function getMetricConfig(metric) {{
  const configs = {{
    'eb': {{ label: 'Total EB', color: '#2962ff', bg: 'rgba(41, 98, 255, 0.15)' }},
    'rc': {{ label: 'Total RC', color: '#f7a600', bg: 'rgba(247, 166, 0, 0.15)' }},
    'plots_history': {{ label: 'Plots Owned', color: '#089981', bg: 'rgba(8, 153, 129, 0.15)' }},
    'rp': {{ label: 'Total RP', color: '#e91e63', bg: 'rgba(233, 30, 99, 0.15)' }}
  }};
  return configs[metric];
}}

function renderChart() {{
  const name = select.value;
  const p = players[name];
  const conf = getMetricConfig(currentMetric);

  const lastIdx = p.dates.length - 1;
  document.getElementById('statPlots').innerText = p.plots_history[lastIdx];
  document.getElementById('statEB').innerText = Number(p.eb[lastIdx]).toLocaleString();
  document.getElementById('statRC').innerText = Number(p.rc[lastIdx]).toLocaleString();
  document.getElementById('statRP').innerText = Number(p.rp[lastIdx]).toLocaleString();

  const ctx = document.getElementById('tradingChart').getContext('2d');
  if (chartInstance) chartInstance.destroy();

  chartInstance = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: p.dates,
      datasets: [{{
        label: conf.label,
        data: p[currentMetric],
        borderColor: conf.color,
        backgroundColor: conf.bg,
        borderWidth: 2.5,
        fill: true,
        tension: 0.25,
        pointRadius: 3,
        pointBackgroundColor: conf.color
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          backgroundColor: '#1e222d',
          titleColor: '#fff',
          bodyColor: conf.color,
          borderColor: '#2a2e39',
          borderWidth: 1
        }}
      }},
      scales: {{
        x: {{
          grid: {{ color: '#2a2e39' }},
          ticks: {{ color: '#787b86', maxTicksLimit: 6 }}
        }},
        y: {{
          grid: {{ color: '#2a2e39' }},
          ticks: {{ color: '#787b86' }}
        }}
      }}
    }}
  }});
}}

function setMetric(metric, btn) {{
  currentMetric = metric;
  document.querySelectorAll('.player-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderChart();
}}

function updatePlayer() {{
  renderChart();
}}

function renderGlobalChart() {{
  const ctx = document.getElementById('globalChart').getContext('2d');
  if (globalChartInstance) globalChartInstance.destroy();

  const isBar = currentGlobalMetric === 'new';
  const label = isBar ? 'New Real Players Joined' : 'Total Real Players';
  const color = isBar ? '#089981' : '#2962ff';
  const bg = isBar ? 'rgba(8, 153, 129, 0.4)' : 'rgba(41, 98, 255, 0.15)';

  globalChartInstance = new Chart(ctx, {{
    type: isBar ? 'bar' : 'line',
    data: {{
      labels: globalData.dates,
      datasets: [{{
        label: label,
        data: isBar ? globalData.new : globalData.total,
        borderColor: color,
        backgroundColor: bg,
        borderWidth: isBar ? 1.5 : 2.5,
        fill: true,
        tension: 0.2,
        borderRadius: isBar ? 4 : 0,
        pointRadius: isBar ? 0 : 3,
        pointBackgroundColor: color
      }}]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{
        legend: {{ display: false }},
        tooltip: {{
          backgroundColor: '#1e222d',
          titleColor: '#fff',
          bodyColor: color,
          borderColor: '#2a2e39',
          borderWidth: 1
        }}
      }},
      scales: {{
        x: {{
          grid: {{ color: '#2a2e39' }},
          ticks: {{ color: '#787b86', maxTicksLimit: 6 }}
        }},
        y: {{
          beginAtZero: isBar,
          grid: {{ color: '#2a2e39' }},
          ticks: {{ color: '#787b86', precision: 0 }}
        }}
      }}
    }}
  }});
}}

function setGlobalMetric(metric, btn) {{
  currentGlobalMetric = metric;
  document.querySelectorAll('.global-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  renderGlobalChart();
}}

renderChart();
renderGlobalChart();
</script>
</body>
</html>
"""

output_path = os.path.join(script_dir, "index.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"\nDone! File created at: {output_path}")
