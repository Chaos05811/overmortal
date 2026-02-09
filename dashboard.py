#!/usr/bin/env python3
"""
Overmortal Progression Dashboard Generator

Parses prog.txt, computes analytics, and generates a stunning
interactive web dashboard as a single HTML file.
"""

import json
import os
import sys
import webbrowser
import random
from datetime import datetime, date, timedelta
from collections import defaultdict
from log_parser import LogParser
from flask import Flask, send_file, request, jsonify

STAGE_ORDER = [
    'Celestial Early', 'Celestial Middle', 'Celestial Late',
    'Eternal Early', 'Eternal Middle', 'Eternal Late',
]

STAGE_COLORS = {
    'Celestial Early':  '#60a5fa',
    'Celestial Middle': '#34d399',
    'Celestial Late':   '#fbbf24',
    'Eternal Early':    '#f87171',
    'Eternal Middle':   '#a78bfa',
    'Eternal Late':     '#2dd4bf',
}


def calc_absolute(stage_name, stage_pct):
    """Convert stage+percent to a single 0-100 journey percent."""
    if stage_name in STAGE_ORDER and stage_pct is not None:
        idx = STAGE_ORDER.index(stage_name)
        return round((idx * 100 + stage_pct) / len(STAGE_ORDER), 2)
    return None


def compute_analytics(entries):
    """Compute every metric the frontend needs."""
    dicts = [e.to_dict() for e in entries]
    valid = sorted(
        [e for e in dicts if e['date']],
        key=lambda x: x['date'],
    )

    if not valid:
        return {}

    first, last = valid[0], valid[-1]
    d1 = datetime.fromisoformat(first['date'])
    d2 = datetime.fromisoformat(last['date'])
    total_days = (d2 - d1).days + 1

    # ---- Summary ----
    summary = {
        'total_entries': len(valid),
        'total_days': total_days,
        'start_date': first['date'],
        'latest_date': last['date'],
        'current_stage': last['stage_name'],
        'current_stage_percent': last['stage_percent'],
        'current_g_level': last.get('g_level'),
        'current_g_percent': last.get('g_percent'),
        'total_breakthroughs': sum(1 for e in valid if e.get('is_breakthrough')),
        'absolute_progress': calc_absolute(last['stage_name'], last['stage_percent']),
    }

    # ---- Stage statistics ----
    stages = {}
    for stage in STAGE_ORDER:
        se = sorted(
            [e for e in valid if e['stage_name'] == stage],
            key=lambda x: x['date'],
        )
        if not se:
            stages[stage] = {'completed': False, 'entries': 0, 'days': 0}
            continue

        sd = datetime.fromisoformat(se[0]['date'])
        ed = datetime.fromisoformat(se[-1]['date'])
        days = max((ed - sd).days, 1)
        sp = se[0].get('stage_percent') or 0
        ep = se[-1].get('stage_percent') or 0
        rate = round((ep - sp) / days, 4) if days > 0 else 0

        # Check completion
        si = STAGE_ORDER.index(stage)
        completed = ep >= 99 or (
            si < len(STAGE_ORDER) - 1
            and any(e['stage_name'] == STAGE_ORDER[si + 1] for e in valid)
        )

        stages[stage] = {
            'start_date': se[0]['date'],
            'end_date': se[-1]['date'],
            'days': days,
            'start_percent': sp,
            'end_percent': ep,
            'daily_rate': rate,
            'entries': len(se),
            'completed': completed,
            'breakthroughs': sum(1 for e in se if e.get('is_breakthrough')),
        }

    # ---- Overall timeline (absolute progress) ----
    timeline = []
    for e in valid:
        ap = calc_absolute(e['stage_name'], e['stage_percent'])
        if ap is not None:
            timeline.append({
                'date': e['date'],
                'absolute': ap,
                'stage': e['stage_name'],
                'stage_percent': e['stage_percent'],
            })

    # ---- Breakthroughs ----
    breakthroughs = [
        {
            'date': e['date'],
            'stage': e['stage_name'],
            'g_level': e.get('g_level'),
            'g_percent': e.get('g_percent'),
            'next_milestone': e.get('next_milestone'),
        }
        for e in valid
        if e.get('is_breakthrough')
    ]

    # ---- Daily progress rates ----
    daily_rates = []
    for i in range(1, len(valid)):
        prev, curr = valid[i - 1], valid[i]
        if (
            prev['stage_name'] == curr['stage_name']
            and prev['stage_percent'] is not None
            and curr['stage_percent'] is not None
        ):
            dd = (
                datetime.fromisoformat(curr['date'])
                - datetime.fromisoformat(prev['date'])
            ).total_seconds() / 86400
            if dd > 0:
                r = (curr['stage_percent'] - prev['stage_percent']) / dd
                if r > 0:
                    daily_rates.append({
                        'date': curr['date'],
                        'rate': round(r, 4),
                        'stage': curr['stage_name'],
                    })

    # ---- Efficiency per stage ----
    efficiency = {}
    for stage in STAGE_ORDER:
        se = sorted(
            [e for e in valid if e['stage_name'] == stage],
            key=lambda x: x['date'],
        )
        if len(se) < 2:
            continue
        total_hrs, total_pct = 0.0, 0.0
        for i in range(1, len(se)):
            p, c = se[i - 1], se[i]
            if p['stage_percent'] is not None and c['stage_percent'] is not None:
                hrs = (
                    datetime.fromisoformat(c['date'])
                    - datetime.fromisoformat(p['date'])
                ).total_seconds() / 3600
                pct = c['stage_percent'] - p['stage_percent']
                if pct > 0:
                    total_hrs += hrs
                    total_pct += pct
        if total_pct > 0:
            efficiency[stage] = {
                'hours_per_pct': round(total_hrs / total_pct, 2),
                'pct_per_day': round(total_pct * 24 / total_hrs, 4) if total_hrs else 0,
            }

    # ---- Predictions ----
    predictions = {}
    if last['stage_name']:
        recent = sorted(
            [e for e in valid if e['stage_name'] == last['stage_name']],
            key=lambda x: x['date'],
        )
        if len(recent) >= 2:
            window = recent[-min(10, len(recent)):]
            wd1 = datetime.fromisoformat(window[0]['date'])
            wd2 = datetime.fromisoformat(window[-1]['date'])
            wdays = (wd2 - wd1).total_seconds() / 86400
            if (
                wdays > 0
                and window[0]['stage_percent'] is not None
                and window[-1]['stage_percent'] is not None
            ):
                rate = (window[-1]['stage_percent'] - window[0]['stage_percent']) / wdays
                remaining = 100 - (window[-1]['stage_percent'] or 0)
                if rate > 0:
                    d2c = remaining / rate
                    proj = wd2 + timedelta(days=d2c)
                    predictions = {
                        'current_rate': round(rate, 4),
                        'days_remaining': round(d2c, 1),
                        'projected_date': proj.strftime('%B %d, %Y'),
                        'stage': last['stage_name'],
                    }

    # ---- G-level data grouped by stage ----
    g_level_data = {}
    for stage in STAGE_ORDER:
        se = [
            e for e in valid
            if e['stage_name'] == stage and e['g_level'] is not None
        ]
        if not se:
            continue
        gd = defaultdict(list)
        for e in se:
            gd[e['g_level']].append({
                'date': e['date'],
                'percent': e.get('g_percent'),
                'bt': e.get('is_breakthrough', False),
            })
        # Convert keys to strings for JSON
        g_level_data[stage] = {str(k): v for k, v in sorted(gd.items())}

    # ---- Time-to-milestone series ----
    ttm = []
    for e in valid:
        if e.get('hours_to_next') is not None:
            h = (e['hours_to_next'] or 0) + (e.get('minutes_to_next') or 0) / 60
            ttm.append({
                'date': e['date'],
                'hours': round(h, 1),
                'milestone': e.get('next_milestone'),
                'stage': e['stage_name'],
            })

    return {
        'entries': dicts,
        'summary': summary,
        'stage_order': STAGE_ORDER,
        'stage_colors': STAGE_COLORS,
        'stages': stages,
        'overall_timeline': timeline,
        'breakthroughs': breakthroughs,
        'daily_rates': daily_rates,
        'efficiency': efficiency,
        'predictions': predictions,
        'g_level_data': g_level_data,
        'time_to_milestones': ttm,
    }


def generate_stars_css(count=80):
    """Generate random star positions for the background (subtle, static)."""
    sm = ', '.join(
        f'{random.randint(1, 3000)}px {random.randint(1, 3000)}px rgba(255,255,255,{round(random.uniform(0.08, 0.25), 2)})'
        for _ in range(count)
    )
    md = ', '.join(
        f'{random.randint(1, 3000)}px {random.randint(1, 3000)}px rgba(255,255,255,{round(random.uniform(0.15, 0.4), 2)})'
        for _ in range(count // 4)
    )
    return sm, md


def generate_dashboard(analytics, output_file='dashboard.html'):
    """Write the final dashboard HTML with data baked in."""
    stars_sm, stars_md = generate_stars_css()
    html = HTML_TEMPLATE.replace(
        '/*__DATA__*/null',
        json.dumps(analytics, default=str),
    ).replace(
        '/*__STARS_SM__*/', stars_sm,
    ).replace(
        '/*__STARS_MD__*/', stars_md,
    )

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    return output_file


# ======================================================================= #
#   FLASK SERVER
# ======================================================================= #

LOG_FILE = "prog.txt"
DASHBOARD_FILE = "dashboard.html"

app = Flask(__name__)


def rebuild_dashboard():
    """Parse log, compute analytics, regenerate dashboard.html."""
    parser = LogParser(LOG_FILE)
    entries = parser.parse()
    analytics = compute_analytics(entries)
    generate_dashboard(analytics, DASHBOARD_FILE)
    return len(entries)


@app.route("/")
def serve_dashboard():
    """Serve the dashboard HTML."""
    if not os.path.exists(DASHBOARD_FILE):
        rebuild_dashboard()
    return send_file(DASHBOARD_FILE)


@app.route("/api/add-entry", methods=["POST"])
def api_add_entry():
    """Append a new entry to prog.txt and regenerate the dashboard."""
    data = request.get_json(force=True)

    realm_phase = data.get("realm_phase", "").strip()
    overall_pct = data.get("overall_pct", "").strip()

    if not realm_phase:
        return jsonify({"error": "Realm Phase is required"}), 400
    if not overall_pct:
        return jsonify({"error": "Overall % is required"}), 400

    # Defaults for date/time
    today = date.today()
    now = datetime.now()
    default_date = today.strftime("%B %d")
    h, m = now.hour, now.minute
    ampm = "AM" if h < 12 else "PM"
    h = h % 12 or 12
    default_time = f"{h}:{m:02d} {ampm}"

    entry_date = data.get("date", "").strip() or default_date
    entry_time = data.get("time", "").strip() or default_time

    # Build entry lines
    header = f"{entry_date}, {entry_time} - {realm_phase} ({overall_pct}%)"
    lines = [header]

    action = data.get("action", "").strip()
    grade = data.get("grade", "").strip()
    time_remaining = data.get("time_remaining", "").strip()
    prediction = data.get("prediction", "").strip()

    if action:
        lines.append(action)
    if grade:
        lines.append(grade)
    if time_remaining:
        lines.append(time_remaining)
    if prediction:
        lines.append(prediction)

    entry_text = "\n".join(lines)

    # Append to log file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + entry_text + "\n")

    # Regenerate dashboard
    count = rebuild_dashboard()

    return jsonify({"ok": True, "entry": entry_text, "total_entries": count})


# ======================================================================= #
#   MAIN
# ======================================================================= #

def main():
    # Build on startup
    print("Parsing prog.txt...")
    count = rebuild_dashboard()
    print(f"  -> {count} entries parsed, dashboard.html generated")

    # Open browser and start server
    port = 5050
    print(f"\nStarting server at http://localhost:{port}")
    print("Press Ctrl+C to stop.\n")
    webbrowser.open(f"http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)


# ======================================================================= #
#   HTML TEMPLATE (everything in one file – CSS, JS, Chart.js)
# ======================================================================= #

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Overmortal — Journey of Celestial</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns@3.0.0/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
/* ===== STARS ===== */
#stars-sm,#stars-md{position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0}
#stars-sm{background:transparent;box-shadow:/*__STARS_SM__*/}
#stars-md{background:transparent;box-shadow:/*__STARS_MD__*/}

/* ===== RESET & BASE ===== */
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#070b14;--bg2:#0f1629;--card:rgba(15,22,41,.75);--card-h:rgba(22,33,62,.85);
  --t1:#f1f5f9;--t2:#94a3b8;--t3:#64748b;--border:rgba(148,163,184,.08);--bh:rgba(148,163,184,.18);
  --r:14px;--rl:22px;--accent:#f59e0b;--ag:rgba(245,158,11,.25);
  --ce:#60a5fa;--cm:#34d399;--cl:#fbbf24;--ee:#f87171;--em:#a78bfa;--el:#2dd4bf;
}
html{scroll-behavior:smooth}
body{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--t1);line-height:1.6;overflow-x:hidden;position:relative}

::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-track{background:var(--bg)}
::-webkit-scrollbar-thumb{background:rgba(148,163,184,.25);border-radius:3px}

a{color:var(--ce);text-decoration:none}
.container{max-width:1320px;margin:0 auto;padding:0 24px;position:relative;z-index:1}

/* ===== NAV ===== */
.nav{position:fixed;top:0;left:0;right:0;z-index:100;backdrop-filter:blur(20px) saturate(1.4);
  background:rgba(7,11,20,.7);border-bottom:1px solid var(--border);padding:0 24px}
.nav-inner{max-width:1320px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;height:56px}
.nav-brand{font-weight:800;font-size:1.05rem;
  background:linear-gradient(135deg,var(--ce),var(--em));-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.nav-links{display:flex;gap:6px}
.nav-links a{padding:6px 14px;border-radius:8px;font-size:.82rem;font-weight:500;color:var(--t2);transition:.2s}
.nav-links a:hover{background:rgba(255,255,255,.06);color:var(--t1)}

/* ===== HERO ===== */
.hero{min-height:70vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:100px 24px 60px;position:relative;overflow:hidden}
.hero-glow{position:absolute;inset:0;
  background:radial-gradient(ellipse at 25% 50%,rgba(96,165,250,.12) 0%,transparent 55%),
             radial-gradient(ellipse at 75% 40%,rgba(167,139,250,.10) 0%,transparent 55%),
             radial-gradient(ellipse at 50% 90%,rgba(245,158,11,.07) 0%,transparent 50%);
  animation:glowPulse 10s ease-in-out infinite alternate;pointer-events:none}
@keyframes glowPulse{0%{opacity:.6}100%{opacity:1}}
.hero-content{position:relative;z-index:1}
.hero h1{font-size:clamp(2.2rem,5vw,4rem);font-weight:900;letter-spacing:-.03em;line-height:1.1;
  background:linear-gradient(135deg,#60a5fa 0%,#a78bfa 40%,#f59e0b 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:.3rem}
.hero-sub{font-size:1.1rem;color:var(--t2);font-weight:400;margin-bottom:2.5rem}
.hero-badge{display:inline-flex;align-items:center;gap:10px;
  background:var(--card);border:1px solid var(--bh);border-radius:100px;padding:10px 28px;
  font-size:.95rem;font-weight:600;backdrop-filter:blur(12px)}
.hero-badge .dot{width:10px;height:10px;border-radius:50%;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 var(--ag)}50%{box-shadow:0 0 0 10px transparent}}
.hero-progress-wrap{margin-top:2.5rem;max-width:700px;margin-left:auto;margin-right:auto}
.hero-progress-label{display:flex;justify-content:space-between;font-size:.78rem;color:var(--t3);margin-bottom:6px;font-weight:500}
.hero-bar{height:10px;background:rgba(255,255,255,.06);border-radius:99px;overflow:hidden;position:relative}
.hero-bar-fill{height:100%;border-radius:99px;transition:width 1.8s cubic-bezier(.22,1,.36,1);
  background:linear-gradient(90deg,var(--ce),var(--cm),var(--cl),var(--ee),var(--em),var(--el))}

/* ===== SECTION ===== */
.section{padding:80px 0}
.section-head{text-align:center;margin-bottom:48px}
.section-head h2{font-size:1.8rem;font-weight:800;letter-spacing:-.02em;margin-bottom:.3rem}
.section-head p{color:var(--t2);font-size:.95rem}

/* ===== STATS GRID ===== */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:22px 18px;
  text-align:center;transition:.3s;backdrop-filter:blur(10px)}
.stat-card:hover{transform:translateY(-3px);border-color:var(--bh);box-shadow:0 12px 40px rgba(0,0,0,.35)}
.stat-icon{font-size:1.5rem;margin-bottom:6px}
.stat-val{font-family:'JetBrains Mono',monospace;font-size:1.65rem;font-weight:700;color:var(--accent);line-height:1.2}
.stat-label{font-size:.78rem;color:var(--t3);font-weight:500;margin-top:2px;text-transform:uppercase;letter-spacing:.04em}

/* ===== JOURNEY PATH ===== */
.journey-path{display:flex;align-items:flex-start;justify-content:space-between;gap:0;padding:10px 0 30px;overflow-x:auto}
.journey-node{display:flex;flex-direction:column;align-items:center;min-width:100px;flex:0 0 auto;position:relative;z-index:1}
.journey-dot{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-weight:700;font-size:.7rem;border:3px solid var(--border);color:var(--t3);transition:.3s;background:var(--bg2)}
.journey-dot.done{color:#fff;border-color:var(--c);background:var(--c);box-shadow:0 0 18px var(--cg)}
.journey-dot.active{border-color:var(--c);color:var(--c);animation:ring 2.5s infinite;box-shadow:0 0 18px var(--cg)}
@keyframes ring{0%,100%{box-shadow:0 0 0 0 var(--cg)}50%{box-shadow:0 0 0 10px transparent}}
.journey-dot.future{opacity:.35}
.journey-name{font-size:.72rem;font-weight:600;margin-top:8px;white-space:nowrap;color:var(--t2)}
.journey-meta{font-size:.65rem;color:var(--t3);margin-top:2px;font-family:'JetBrains Mono',monospace}
.journey-line{flex:1;height:3px;min-width:20px;background:var(--border);align-self:center;margin-top:26px;border-radius:2px;position:relative}
.journey-line.done{background:linear-gradient(90deg,var(--from),var(--to))}

/* ===== TABS ===== */
.tabs{display:flex;gap:4px;background:var(--bg2);padding:4px;border-radius:var(--r);margin-bottom:24px;overflow-x:auto;flex-wrap:nowrap}
.tab{padding:10px 22px;border:none;background:transparent;color:var(--t2);cursor:pointer;border-radius:calc(var(--r) - 2px);
  font:inherit;font-size:.85rem;font-weight:500;transition:.2s;white-space:nowrap}
.tab:hover{color:var(--t1)}
.tab.active{background:var(--card);color:var(--t1);box-shadow:0 2px 8px rgba(0,0,0,.25)}
.chart-panel{display:none}
.chart-panel.active{display:block}
.chart-wrap{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:20px;position:relative}
.chart-wrap canvas{width:100%!important;max-height:420px}

/* ===== GRID HELPERS ===== */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:768px){.grid-2{grid-template-columns:1fr}}

/* ===== G-LEVEL SUB-TABS ===== */
.sub-tabs{display:flex;gap:4px;margin-bottom:16px;flex-wrap:wrap}
.sub-tab{padding:6px 14px;border:1px solid var(--border);background:transparent;color:var(--t2);border-radius:8px;
  cursor:pointer;font:inherit;font-size:.78rem;font-weight:500;transition:.2s}
.sub-tab:hover{border-color:var(--bh);color:var(--t1)}
.sub-tab.active{background:var(--c);border-color:var(--c);color:#fff}

/* ===== TIMELINE ===== */
.timeline-wrap{max-height:560px;overflow-y:auto;padding-right:8px}
.timeline{position:relative;padding-left:28px}
.timeline::before{content:'';position:absolute;left:7px;top:0;bottom:0;width:2px;background:var(--border)}
.tl-item{position:relative;padding:10px 0 10px 20px;border-bottom:1px solid var(--border)}
.tl-item::before{content:'';position:absolute;left:-24px;top:16px;width:12px;height:12px;border-radius:50%;
  background:var(--c,var(--accent));box-shadow:0 0 8px var(--cg,var(--ag))}
.tl-date{font-size:.72rem;color:var(--t3);font-family:'JetBrains Mono',monospace}
.tl-title{font-weight:600;font-size:.88rem;margin-top:2px}
.tl-desc{font-size:.78rem;color:var(--t2);margin-top:1px}

/* ===== PREDICTIONS ===== */
.pred-card{background:var(--card);border:1px solid var(--border);border-radius:var(--r);padding:28px;backdrop-filter:blur(10px)}
.pred-row{display:flex;justify-content:space-between;align-items:center;padding:14px 0;border-bottom:1px solid var(--border)}
.pred-row:last-child{border:none}
.pred-label{font-size:.85rem;color:var(--t2)}
.pred-val{font-family:'JetBrains Mono',monospace;font-weight:700;font-size:1.05rem}

/* ===== DATA TABLE ===== */
.table-controls{display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap}
.table-controls input,.table-controls select{background:var(--bg2);border:1px solid var(--border);color:var(--t1);
  padding:10px 16px;border-radius:10px;font:inherit;font-size:.85rem;outline:none;transition:.2s}
.table-controls input:focus,.table-controls select:focus{border-color:var(--ce)}
.table-controls input{flex:1;min-width:200px}
.table-wrap{overflow-x:auto;border:1px solid var(--border);border-radius:var(--r);background:var(--card)}
table{width:100%;border-collapse:collapse;font-size:.82rem}
thead{background:rgba(255,255,255,.03)}
th{padding:12px 14px;text-align:left;font-weight:600;color:var(--t2);font-size:.75rem;text-transform:uppercase;letter-spacing:.04em;border-bottom:1px solid var(--border)}
td{padding:10px 14px;border-bottom:1px solid var(--border);color:var(--t2)}
tr:hover td{background:rgba(255,255,255,.02);color:var(--t1)}
.badge{display:inline-block;padding:2px 8px;border-radius:6px;font-size:.7rem;font-weight:600;color:#fff}
.badge-bt{background:var(--accent)}

/* ===== FOOTER ===== */
.footer{text-align:center;padding:40px 24px;color:var(--t3);font-size:.78rem;border-top:1px solid var(--border)}

/* ===== ANIMATIONS ===== */
.fade-in{opacity:0;transform:translateY(24px);transition:opacity .7s ease,transform .7s ease}
.fade-in.visible{opacity:1;transform:translateY(0)}

/* ===== ADD ENTRY BUTTON & MODAL ===== */
.nav-add-btn{padding:6px 16px;border-radius:8px;font-size:.82rem;font-weight:600;cursor:pointer;transition:.2s;
  background:linear-gradient(135deg,var(--accent),#d97706);color:#000;border:none;font-family:inherit}
.nav-add-btn:hover{transform:scale(1.05);box-shadow:0 0 16px var(--ag)}

.modal-overlay{display:none;position:fixed;inset:0;z-index:200;background:rgba(0,0,0,.6);backdrop-filter:blur(6px);
  align-items:center;justify-content:center}
.modal-overlay.open{display:flex}
.modal{background:var(--bg2);border:1px solid var(--bh);border-radius:var(--rl);padding:32px;width:90%;max-width:520px;
  position:relative;box-shadow:0 24px 80px rgba(0,0,0,.6)}
.modal-title{font-size:1.3rem;font-weight:800;margin-bottom:20px;
  background:linear-gradient(135deg,var(--accent),#fcd34d);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.modal-close{position:absolute;top:16px;right:16px;background:none;border:none;color:var(--t3);font-size:1.3rem;cursor:pointer;transition:.2s}
.modal-close:hover{color:var(--t1)}
.form-group{margin-bottom:14px}
.form-group label{display:block;font-size:.78rem;font-weight:600;color:var(--t2);margin-bottom:4px;text-transform:uppercase;letter-spacing:.03em}
.form-group input,.form-group select{width:100%;background:var(--card);border:1px solid var(--border);color:var(--t1);
  padding:10px 14px;border-radius:10px;font:inherit;font-size:.88rem;outline:none;transition:.2s}
.form-group input:focus,.form-group select:focus{border-color:var(--ce);box-shadow:0 0 0 3px rgba(96,165,250,.15)}
.form-group input::placeholder{color:var(--t3)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.form-hint{font-size:.7rem;color:var(--t3);margin-top:2px}
.form-submit{width:100%;padding:12px;border:none;border-radius:10px;font:inherit;font-size:.92rem;font-weight:700;cursor:pointer;
  background:linear-gradient(135deg,var(--accent),#d97706);color:#000;transition:.2s;margin-top:8px}
.form-submit:hover{transform:translateY(-1px);box-shadow:0 8px 24px var(--ag)}
.form-submit:disabled{opacity:.5;cursor:not-allowed;transform:none}
.form-msg{text-align:center;margin-top:10px;font-size:.82rem;font-weight:500;min-height:20px}
.form-msg.success{color:#34d399}
.form-msg.error{color:#f87171}

@media(max-width:640px){
  .stats-grid{grid-template-columns:repeat(2,1fr)}
  .hero h1{font-size:2rem}
  .journey-path{gap:4px}
  .form-row{grid-template-columns:1fr}
}
</style>
</head>
<body>

<!-- Stars -->
<div id="stars-sm"></div>
<div id="stars-md"></div>

<!-- Nav -->
<nav class="nav">
  <div class="nav-inner">
    <div class="nav-brand">Overmortal Tracker</div>
    <div class="nav-links">
      <a href="#overview">Overview</a>
      <a href="#journey">Journey</a>
      <a href="#analytics">Analytics</a>
      <a href="#milestones">Milestones</a>
      <a href="#data">Data</a>
      <button class="nav-add-btn" onclick="openAddModal()">+ Add Entry</button>
    </div>
  </div>
</nav>

<!-- Hero -->
<section class="hero" id="overview">
  <div class="hero-glow"></div>
  <div class="hero-content">
    <h1>Journey of Celestial</h1>
    <p class="hero-sub">Overmortal Progression Tracker</p>
    <div class="hero-badge" id="hero-badge">
      <span class="dot" style="background:var(--accent)"></span>
      <span id="hero-status">Loading...</span>
    </div>
    <div class="hero-progress-wrap">
      <div class="hero-progress-label">
        <span>Celestial Early</span>
        <span id="hero-pct">0%</span>
        <span>Eternal Late</span>
      </div>
      <div class="hero-bar"><div class="hero-bar-fill" id="hero-bar" style="width:0%"></div></div>
    </div>
  </div>
</section>

<!-- Stats -->
<section class="section" id="stats-section">
  <div class="container">
    <div class="stats-grid" id="stats-grid"></div>
  </div>
</section>

<!-- Journey Path -->
<section class="section" id="journey">
  <div class="container">
    <div class="section-head"><h2>The Cultivation Path</h2><p>Your journey across the realms</p></div>
    <div class="journey-path" id="journey-path"></div>
  </div>
</section>

<!-- Analytics -->
<section class="section" id="analytics">
  <div class="container">
    <div class="section-head"><h2>Analytics</h2><p>Deep-dive into your progression data</p></div>
    <div class="tabs" id="main-tabs">
      <button class="tab active" data-tab="overall">Overall Progress</button>
      <button class="tab" data-tab="stages">Stage Comparison</button>
      <button class="tab" data-tab="glevels">G-Level Tracker</button>
      <button class="tab" data-tab="rates">Daily Rate</button>
      <button class="tab" data-tab="ttm">Time to Milestone</button>
    </div>
    <div class="chart-panel active" id="panel-overall">
      <div class="chart-wrap"><canvas id="chart-overall"></canvas></div>
    </div>
    <div class="chart-panel" id="panel-stages">
      <div class="grid-2">
        <div class="chart-wrap"><canvas id="chart-stage-days"></canvas></div>
        <div class="chart-wrap"><canvas id="chart-stage-rate"></canvas></div>
      </div>
    </div>
    <div class="chart-panel" id="panel-glevels">
      <div class="sub-tabs" id="g-sub-tabs"></div>
      <div class="chart-wrap"><canvas id="chart-glevels"></canvas></div>
    </div>
    <div class="chart-panel" id="panel-rates">
      <div class="chart-wrap"><canvas id="chart-rates"></canvas></div>
    </div>
    <div class="chart-panel" id="panel-ttm">
      <div class="chart-wrap"><canvas id="chart-ttm"></canvas></div>
    </div>
  </div>
</section>

<!-- Milestones & Predictions -->
<section class="section" id="milestones">
  <div class="container">
    <div class="grid-2">
      <div>
        <div class="section-head" style="text-align:left"><h2>Breakthroughs</h2><p>Every milestone in your journey</p></div>
        <div class="timeline-wrap"><div class="timeline" id="timeline"></div></div>
      </div>
      <div>
        <div class="section-head" style="text-align:left"><h2>Predictions</h2><p>Where you're heading next</p></div>
        <div class="pred-card" id="predictions"></div>
        <div style="margin-top:20px">
          <div class="section-head" style="text-align:left"><h2>Efficiency</h2><p>Hours per 1% progress</p></div>
          <div class="pred-card" id="efficiency"></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Data Table -->
<section class="section" id="data">
  <div class="container">
    <div class="section-head"><h2>Data Explorer</h2><p>Browse every logged entry</p></div>
    <div class="table-controls">
      <input type="text" id="tbl-search" placeholder="Search entries...">
      <select id="tbl-filter"><option value="">All Stages</option></select>
    </div>
    <div class="table-wrap">
      <table>
        <thead><tr>
          <th>Date</th><th>Stage</th><th>Stage %</th><th>G-Level</th><th>G %</th><th>Hrs to Next</th><th>Type</th>
        </tr></thead>
        <tbody id="tbl-body"></tbody>
      </table>
    </div>
  </div>
</section>

<!-- Add Entry Modal -->
<div class="modal-overlay" id="add-modal">
  <div class="modal">
    <button class="modal-close" onclick="closeAddModal()">&times;</button>
    <div class="modal-title">Add New Entry</div>
    <form id="add-form" onsubmit="submitEntry(event)">
      <div class="form-row">
        <div class="form-group">
          <label>Date</label>
          <input type="text" id="f-date" placeholder="February 09">
          <div class="form-hint">Defaults to today</div>
        </div>
        <div class="form-group">
          <label>Time</label>
          <input type="text" id="f-time" placeholder="8:53 AM">
          <div class="form-hint">Defaults to now</div>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Realm Phase</label>
          <select id="f-realm">
            <option value="">Select...</option>
            <option value="Celestial Early">Celestial Early</option>
            <option value="Celestial Middle">Celestial Middle</option>
            <option value="Celestial Late">Celestial Late</option>
            <option value="Eternal Early">Eternal Early</option>
            <option value="Eternal Middle">Eternal Middle</option>
            <option value="Eternal Late">Eternal Late</option>
          </select>
        </div>
        <div class="form-group">
          <label>Overall %</label>
          <input type="text" id="f-pct" placeholder="95.9">
        </div>
      </div>
      <div class="form-group">
        <label>Action / Context <span style="color:var(--t3)">(optional)</span></label>
        <input type="text" id="f-action" placeholder="After Reset, Pills, Respires">
      </div>
      <div class="form-group">
        <label>Grade Status <span style="color:var(--t3)">(optional)</span></label>
        <input type="text" id="f-grade" placeholder="G20 at 49.4%  or  bt to G5 at 1.6%">
      </div>
      <div class="form-group">
        <label>Time Remaining <span style="color:var(--t3)">(optional)</span></label>
        <input type="text" id="f-remaining" placeholder="616.458 Yrs or 154 Hrs 6 Min to G21">
      </div>
      <div class="form-group">
        <label>EST / Prediction <span style="color:var(--t3)">(optional)</span></label>
        <input type="text" id="f-prediction" placeholder="predicted by ChatGpt">
      </div>
      <button type="submit" class="form-submit" id="f-submit">Add Entry</button>
      <div class="form-msg" id="f-msg"></div>
    </form>
  </div>
</div>

<footer class="footer">
  Generated on <span id="gen-date"></span> &bull; Overmortal Progression Tracker
</footer>

<script>
// ====== DATA ======
const D = /*__DATA__*/null;

const SC = D.stage_colors;
const SO = D.stage_order;

function stageColor(s){return SC[s]||'#64748b'}
function stageColorAlpha(s,a){
  const c=SC[s]||'#64748b';
  const r=parseInt(c.slice(1,3),16),g=parseInt(c.slice(3,5),16),b=parseInt(c.slice(5,7),16);
  return `rgba(${r},${g},${b},${a})`;
}
function fmtDate(iso){
  if(!iso)return '—';
  const d=new Date(iso);
  return d.toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
}
function fmtDateShort(iso){
  if(!iso)return '';
  const d=new Date(iso);
  return d.toLocaleDateString('en-US',{month:'short',day:'numeric'});
}

// ====== CHART.JS DEFAULTS ======
Chart.defaults.color='#94a3b8';
Chart.defaults.borderColor='rgba(148,163,184,.08)';
Chart.defaults.font.family="'Inter',system-ui,sans-serif";
Chart.defaults.plugins.legend.labels.usePointStyle=true;
Chart.defaults.plugins.legend.labels.pointStyleWidth=8;
Chart.defaults.plugins.tooltip.backgroundColor='rgba(15,22,41,.92)';
Chart.defaults.plugins.tooltip.borderColor='rgba(148,163,184,.15)';
Chart.defaults.plugins.tooltip.borderWidth=1;
Chart.defaults.plugins.tooltip.cornerRadius=10;
Chart.defaults.plugins.tooltip.padding=12;
Chart.defaults.animation={duration:1200,easing:'easeOutQuart'};

// ====== HERO ======
function initHero(){
  const s=D.summary;
  document.getElementById('hero-status').textContent=
    `${s.current_stage} (${s.current_stage_percent}%) — G${s.current_g_level} at ${s.current_g_percent||'?'}%`;
  document.getElementById('hero-badge').querySelector('.dot').style.background=stageColor(s.current_stage);
  const pct=s.absolute_progress||0;
  document.getElementById('hero-pct').textContent=pct.toFixed(1)+'%';
  setTimeout(()=>document.getElementById('hero-bar').style.width=pct+'%',300);
}

// ====== STATS ======
function initStats(){
  const s=D.summary;
  const avgRate=D.daily_rates.length?
    (D.daily_rates.reduce((a,b)=>a+b.rate,0)/D.daily_rates.length).toFixed(2):'—';
  const cards=[
    {icon:'📅',val:s.total_days,label:'Days Tracked'},
    {icon:'📊',val:s.total_entries,label:'Total Entries'},
    {icon:'⚡',val:s.total_breakthroughs,label:'Breakthroughs'},
    {icon:'🎯',val:SO.filter(st=>D.stages[st]&&D.stages[st].completed).length+'/'+SO.length,label:'Stages Done'},
    {icon:'📈',val:avgRate+'%',label:'Avg Daily Rate'},
    {icon:'🏔️',val:(s.absolute_progress||0).toFixed(1)+'%',label:'Journey Complete'},
  ];
  const grid=document.getElementById('stats-grid');
  grid.innerHTML=cards.map(c=>`
    <div class="stat-card fade-in">
      <div class="stat-icon">${c.icon}</div>
      <div class="stat-val">${c.val}</div>
      <div class="stat-label">${c.label}</div>
    </div>`).join('');
}

// ====== JOURNEY PATH ======
function initJourney(){
  const wrap=document.getElementById('journey-path');
  let html='';
  SO.forEach((stage,i)=>{
    const sd=D.stages[stage]||{};
    const col=stageColor(stage);
    const colG=stageColorAlpha(stage,.3);
    const isDone=sd.completed;
    const isCurrent=stage===D.summary.current_stage;
    const cls=isDone?'done':isCurrent?'active':'future';
    const meta=sd.days?`${sd.days}d / ${sd.daily_rate||0}%/d`:'—';

    if(i>0){
      const prevCol=stageColor(SO[i-1]);
      const lineDone=isDone||isCurrent;
      html+=`<div class="journey-line${lineDone?' done':''}" style="${lineDone?`--from:${prevCol};--to:${col}`:''}"></div>`;
    }
    html+=`
      <div class="journey-node">
        <div class="journey-dot ${cls}" style="--c:${col};--cg:${colG}">${isDone?'✓':isCurrent?'◉':'○'}</div>
        <div class="journey-name">${stage.replace(' ','<br>')}</div>
        <div class="journey-meta">${meta}</div>
      </div>`;
  });
  wrap.innerHTML=html;
}

// ====== CHARTS ======
let charts={};

function initOverallChart(){
  const ctx=document.getElementById('chart-overall');
  const tl=D.overall_timeline;
  // Build one dataset per stage (for colored segments)
  const datasets=[];
  let prevLast=null;
  SO.forEach(stage=>{
    const pts=tl.filter(p=>p.stage===stage);
    if(!pts.length)return;
    const data=[];
    if(prevLast)data.push({x:new Date(prevLast.date),y:prevLast.absolute});
    pts.forEach(p=>data.push({x:new Date(p.date),y:p.absolute}));
    prevLast=pts[pts.length-1];
    const col=stageColor(stage);
    datasets.push({
      label:stage,data,borderColor:col,
      backgroundColor:stageColorAlpha(stage,.08),
      fill:true,tension:.35,pointRadius:1.5,pointHoverRadius:5,borderWidth:2.5,
    });
  });
  charts.overall=new Chart(ctx,{
    type:'line',
    data:{datasets},
    options:{
      responsive:true,maintainAspectRatio:false,
      interaction:{mode:'index',intersect:false},
      scales:{
        x:{type:'time',time:{unit:'week',tooltipFormat:'MMM d, yyyy'},grid:{display:false}},
        y:{min:0,max:100,title:{display:true,text:'Journey %'},grid:{color:'rgba(148,163,184,.06)'}},
      },
      plugins:{
        legend:{position:'bottom'},
        tooltip:{callbacks:{label:function(ctx){
          const d=D.overall_timeline.find(p=>Math.abs(new Date(p.date)-ctx.parsed.x)<86400000&&p.stage===ctx.dataset.label);
          return d?`${d.stage}: ${d.stage_percent}% (${d.absolute}% overall)`:`${ctx.dataset.label}: ${ctx.parsed.y}%`;
        }}}
      }
    }
  });
}

function initStageCharts(){
  const labels=SO.filter(s=>D.stages[s]&&D.stages[s].days>0);
  const days=labels.map(s=>D.stages[s].days);
  const rates=labels.map(s=>D.stages[s].daily_rate);
  const cols=labels.map(s=>stageColor(s));

  charts.stageDays=new Chart(document.getElementById('chart-stage-days'),{
    type:'bar',
    data:{labels:labels.map(s=>s.replace(' ','\n')),datasets:[{label:'Days',data:days,backgroundColor:cols.map(c=>c+'cc'),borderColor:cols,borderWidth:1,borderRadius:6}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{y:{title:{display:true,text:'Days'},grid:{color:'rgba(148,163,184,.06)'}},x:{grid:{display:false}}}
    }
  });
  charts.stageRate=new Chart(document.getElementById('chart-stage-rate'),{
    type:'bar',
    data:{labels:labels.map(s=>s.replace(' ','\n')),datasets:[{label:'% / day',data:rates,backgroundColor:cols.map(c=>c+'cc'),borderColor:cols,borderWidth:1,borderRadius:6}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{y:{title:{display:true,text:'% per day'},grid:{color:'rgba(148,163,184,.06)'}},x:{grid:{display:false}}}
    }
  });
}

function initGLevelChart(){
  const tabsEl=document.getElementById('g-sub-tabs');
  const availableStages=SO.filter(s=>D.g_level_data[s]);
  tabsEl.innerHTML=availableStages.map((s,i)=>{
    const c=stageColor(s);
    return `<button class="sub-tab${i===0?' active':''}" data-stage="${s}" style="--c:${c}">${s}</button>`;
  }).join('');

  function render(stage){
    if(charts.glevels)charts.glevels.destroy();
    const gd=D.g_level_data[stage]||{};
    const datasets=[];
    const keys=Object.keys(gd).map(Number).sort((a,b)=>a-b);
    const palette=['#60a5fa','#34d399','#fbbf24','#f87171','#a78bfa','#2dd4bf','#fb923c','#e879f9','#38bdf8','#4ade80',
                   '#facc15','#f472b6','#818cf8','#22d3ee','#a3e635','#c084fc','#fb7185','#fdba74','#86efac','#67e8f9'];
    keys.forEach((gl,idx)=>{
      const pts=gd[String(gl)].filter(p=>p.percent!==null).map(p=>({x:new Date(p.date),y:p.percent}));
      if(!pts.length)return;
      datasets.push({
        label:'G'+gl,data:pts,
        borderColor:palette[idx%palette.length],
        backgroundColor:'transparent',
        tension:.3,pointRadius:2,pointHoverRadius:5,borderWidth:2,
      });
    });
    charts.glevels=new Chart(document.getElementById('chart-glevels'),{
      type:'line',data:{datasets},
      options:{
        responsive:true,maintainAspectRatio:false,
        interaction:{mode:'nearest',intersect:false},
        scales:{
          x:{type:'time',time:{unit:'week',tooltipFormat:'MMM d, yyyy'},grid:{display:false}},
          y:{min:0,max:100,title:{display:true,text:'G-Level %'},grid:{color:'rgba(148,163,184,.06)'}},
        },
        plugins:{legend:{position:'bottom',labels:{font:{size:11}}}}
      }
    });
  }

  render(availableStages[0]);
  tabsEl.addEventListener('click',e=>{
    const btn=e.target.closest('.sub-tab');
    if(!btn)return;
    tabsEl.querySelectorAll('.sub-tab').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    render(btn.dataset.stage);
  });
}

function initRatesChart(){
  const dr=D.daily_rates;
  if(!dr.length)return;
  const data=dr.map(p=>({x:new Date(p.date),y:p.rate}));
  // 7-point moving average
  const ma=[];
  for(let i=6;i<dr.length;i++){
    const slice=dr.slice(i-6,i+1);
    const avg=slice.reduce((a,b)=>a+b.rate,0)/slice.length;
    ma.push({x:new Date(dr[i].date),y:Math.round(avg*10000)/10000});
  }
  charts.rates=new Chart(document.getElementById('chart-rates'),{
    type:'line',
    data:{datasets:[
      {label:'Daily Rate',data,borderColor:'rgba(96,165,250,.4)',backgroundColor:'rgba(96,165,250,.06)',
       fill:true,tension:.3,pointRadius:1.5,borderWidth:1.5},
      {label:'7-day Average',data:ma,borderColor:'#f87171',backgroundColor:'transparent',
       tension:.4,pointRadius:0,borderWidth:2.5},
    ]},
    options:{
      responsive:true,maintainAspectRatio:false,
      interaction:{mode:'index',intersect:false},
      scales:{
        x:{type:'time',time:{unit:'week',tooltipFormat:'MMM d, yyyy'},grid:{display:false}},
        y:{title:{display:true,text:'% per day'},grid:{color:'rgba(148,163,184,.06)'}},
      },
      plugins:{legend:{position:'bottom'}}
    }
  });
}

function initTTMChart(){
  const ttm=D.time_to_milestones;
  if(!ttm.length)return;
  const data=ttm.map(p=>({x:new Date(p.date),y:p.hours}));
  charts.ttm=new Chart(document.getElementById('chart-ttm'),{
    type:'scatter',
    data:{datasets:[{
      label:'Hours to Next',data,
      borderColor:'#a78bfa',backgroundColor:'rgba(167,139,250,.15)',
      showLine:true,tension:.2,pointRadius:2,pointHoverRadius:6,borderWidth:2,fill:true,
    }]},
    options:{
      responsive:true,maintainAspectRatio:false,
      scales:{
        x:{type:'time',time:{unit:'week',tooltipFormat:'MMM d, yyyy'},grid:{display:false}},
        y:{title:{display:true,text:'Hours'},grid:{color:'rgba(148,163,184,.06)'}},
      },
      plugins:{legend:{display:false},
        tooltip:{callbacks:{label:ctx=>{
          const p=ttm[ctx.dataIndex];
          return `${p.hours} hrs to ${p.milestone||'next'} (${p.stage})`;
        }}}
      }
    }
  });
}

// ====== TABS ======
function initTabs(){
  document.getElementById('main-tabs').addEventListener('click',e=>{
    const btn=e.target.closest('.tab');
    if(!btn)return;
    document.querySelectorAll('#main-tabs .tab').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.chart-panel').forEach(p=>p.classList.remove('active'));
    document.getElementById('panel-'+btn.dataset.tab).classList.add('active');
  });
}

// ====== TIMELINE ======
function initTimeline(){
  const wrap=document.getElementById('timeline');
  const bts=D.breakthroughs.slice().reverse().slice(0,60);
  wrap.innerHTML=bts.map(b=>{
    const col=stageColor(b.stage);
    const colG=stageColorAlpha(b.stage,.3);
    const title=b.g_level?`Breakthrough to G${b.g_level}${b.g_percent!==null?' at '+b.g_percent+'%':''}`:
      'Stage Breakthrough';
    return `<div class="tl-item" style="--c:${col};--cg:${colG}">
      <div class="tl-date">${fmtDate(b.date)}</div>
      <div class="tl-title">${title}</div>
      <div class="tl-desc">${b.stage}${b.next_milestone?' → '+b.next_milestone:''}</div>
    </div>`;
  }).join('');
}

// ====== PREDICTIONS ======
function initPredictions(){
  const wrap=document.getElementById('predictions');
  const p=D.predictions;
  if(!p||!p.current_rate){
    wrap.innerHTML='<div class="pred-row"><span class="pred-label">Not enough recent data for predictions</span></div>';
    return;
  }
  wrap.innerHTML=`
    <div class="pred-row"><span class="pred-label">Current Stage</span><span class="pred-val" style="color:${stageColor(p.stage)}">${p.stage}</span></div>
    <div class="pred-row"><span class="pred-label">Current Rate</span><span class="pred-val">${p.current_rate}% / day</span></div>
    <div class="pred-row"><span class="pred-label">Days Remaining</span><span class="pred-val">${p.days_remaining}</span></div>
    <div class="pred-row"><span class="pred-label">Projected Completion</span><span class="pred-val" style="color:var(--accent)">${p.projected_date}</span></div>
  `;
}

function initEfficiency(){
  const wrap=document.getElementById('efficiency');
  const eff=D.efficiency;
  const stages=Object.keys(eff);
  if(!stages.length){wrap.innerHTML='<div class="pred-row"><span class="pred-label">No efficiency data yet</span></div>';return;}
  wrap.innerHTML=stages.map(s=>`
    <div class="pred-row">
      <span class="pred-label" style="color:${stageColor(s)}">${s}</span>
      <span class="pred-val">${eff[s].hours_per_pct} hrs/% &nbsp; (${eff[s].pct_per_day}%/day)</span>
    </div>`).join('');
}

// ====== DATA TABLE ======
function initTable(){
  const filter=document.getElementById('tbl-filter');
  SO.forEach(s=>{
    const opt=document.createElement('option');
    opt.value=s;opt.textContent=s;filter.appendChild(opt);
  });

  const entries=D.entries.filter(e=>e.date).sort((a,b)=>b.date.localeCompare(a.date));
  const body=document.getElementById('tbl-body');

  function render(list){
    body.innerHTML=list.map(e=>{
      const col=stageColor(e.stage_name);
      const hrs=e.hours_to_next!==null?e.hours_to_next+(e.minutes_to_next?'h '+e.minutes_to_next+'m':'h'):'—';
      const type=e.is_breakthrough?'<span class="badge badge-bt">BT</span>':'';
      return `<tr>
        <td style="color:var(--t1);font-family:'JetBrains Mono',monospace;font-size:.75rem">${fmtDate(e.date)}</td>
        <td><span style="color:${col};font-weight:600">${e.stage_name||'—'}</span></td>
        <td>${e.stage_percent!==null?e.stage_percent+'%':'—'}</td>
        <td>${e.g_level!==null?'G'+e.g_level:'—'}</td>
        <td>${e.g_percent!==null?e.g_percent+'%':'—'}</td>
        <td style="font-family:'JetBrains Mono',monospace;font-size:.75rem">${hrs}</td>
        <td>${type}</td>
      </tr>`;
    }).join('');
  }

  render(entries);

  function applyFilters(){
    const q=document.getElementById('tbl-search').value.toLowerCase();
    const sf=filter.value;
    const filtered=entries.filter(e=>{
      if(sf&&e.stage_name!==sf)return false;
      if(q){
        const txt=JSON.stringify(e).toLowerCase();
        if(!txt.includes(q))return false;
      }
      return true;
    });
    render(filtered);
  }

  document.getElementById('tbl-search').addEventListener('input',applyFilters);
  filter.addEventListener('change',applyFilters);
}

// ====== FADE-IN OBSERVER ======
function initObserver(){
  const obs=new IntersectionObserver(entries=>{
    entries.forEach(e=>{if(e.isIntersecting)e.target.classList.add('visible')});
  },{threshold:.1});
  document.querySelectorAll('.fade-in').forEach(el=>obs.observe(el));
}

// ====== ADD ENTRY MODAL ======
function openAddModal(){
  const modal=document.getElementById('add-modal');
  modal.classList.add('open');
  // Set defaults
  const now=new Date();
  const months=['January','February','March','April','May','June','July','August','September','October','November','December'];
  const day=String(now.getDate()).padStart(2,'0');
  document.getElementById('f-date').placeholder=months[now.getMonth()]+' '+day;
  let h=now.getHours(),m=now.getMinutes(),ampm=h>=12?'PM':'AM';
  h=h%12||12;
  document.getElementById('f-time').placeholder=h+':'+String(m).padStart(2,'0')+' '+ampm;
  // Pre-select current realm
  const cur=D.summary.current_stage;
  if(cur){document.getElementById('f-realm').value=cur}
  document.getElementById('f-msg').textContent='';
  document.getElementById('f-msg').className='form-msg';
}

function closeAddModal(){
  document.getElementById('add-modal').classList.remove('open');
}

document.getElementById('add-modal').addEventListener('click',e=>{
  if(e.target===e.currentTarget)closeAddModal();
});

async function submitEntry(e){
  e.preventDefault();
  const btn=document.getElementById('f-submit');
  const msg=document.getElementById('f-msg');
  btn.disabled=true;
  msg.textContent='Saving...';
  msg.className='form-msg';

  const realm=document.getElementById('f-realm').value;
  const pct=document.getElementById('f-pct').value.trim();
  if(!realm){msg.textContent='Realm Phase is required';msg.className='form-msg error';btn.disabled=false;return}
  if(!pct){msg.textContent='Overall % is required';msg.className='form-msg error';btn.disabled=false;return}

  const body={
    date:document.getElementById('f-date').value.trim(),
    time:document.getElementById('f-time').value.trim(),
    realm_phase:realm,
    overall_pct:pct,
    action:document.getElementById('f-action').value.trim(),
    grade:document.getElementById('f-grade').value.trim(),
    time_remaining:document.getElementById('f-remaining').value.trim(),
    prediction:document.getElementById('f-prediction').value.trim(),
  };

  try{
    const res=await fetch('/api/add-entry',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await res.json();
    if(res.ok){
      msg.textContent='Entry added! Reloading dashboard...';
      msg.className='form-msg success';
      setTimeout(()=>window.location.reload(),1200);
    }else{
      msg.textContent=data.error||'Failed to add entry';
      msg.className='form-msg error';
      btn.disabled=false;
    }
  }catch(err){
    msg.textContent='Network error — is the server running?';
    msg.className='form-msg error';
    btn.disabled=false;
  }
}

// ====== INIT ======
document.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('gen-date').textContent=new Date().toLocaleDateString('en-US',{month:'long',day:'numeric',year:'numeric'});
  initHero();
  initStats();
  initJourney();
  initTabs();
  initOverallChart();
  initStageCharts();
  initGLevelChart();
  initRatesChart();
  initTTMChart();
  initTimeline();
  initPredictions();
  initEfficiency();
  initTable();
  setTimeout(initObserver,100);
});
</script>
</body>
</html>"""

if __name__ == "__main__":
    main()
