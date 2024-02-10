"""
render_heatmap_svg.py — Render a custom contribution heatmap SVG from contributions.json.
Generates contrib-heatmap.svg with a dark theme and gold-tone color gradient.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')

# Color palette (level 0–4)
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
# Gold-themed alternative
GOLD_COLORS = ["#1a1a1a", "#3d2e00", "#6b4f00", "#9a7200", "#D4AF37"]

BG = "#0d0d0d"
BORDER = "#2a2a2a"
TEXT_COLOR = "#888"
LABEL_COLOR = "#666"
FONT = "'SF Mono','Fira Code','Cascadia Code',monospace"
CELL = 12
GAP = 3
RADIUS = 12
PAD_X = 50
PAD_Y = 55
MONTH_LABELS_Y = 42
DOW_LABELS_X = 12

DOW_NAMES = ["", "Mon", "", "Wed", "", "Fri", ""]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def main():
    root = Path(__file__).resolve().parent.parent
    data_path = root / "data" / "contributions.json"

    if not data_path.exists():
        print(f"[ERROR] {data_path} not found. Run fetch_contributions.py first.")
        return

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    days = data.get("days", [])
    metrics = data.get("metrics", {})

    if not days:
        print("[WARN] No contribution data found.")
        return

    # Build date → level map
    date_map = {d["date"]: d["level"] for d in days}

    # Determine date range (52 weeks back from latest date)
    latest = datetime.strptime(days[-1]["date"], "%Y-%m-%d")
    start = latest - timedelta(weeks=52)
    # Align start to Sunday
    start -= timedelta(days=start.weekday() + 1)
    if start.weekday() != 6:
        start -= timedelta(days=(start.weekday() + 1) % 7)

    # Generate week columns
    weeks = []
    current = start
    while current <= latest:
        week = []
        for dow in range(7):
            d = current + timedelta(days=dow)
            ds = d.strftime("%Y-%m-%d")
            level = date_map.get(ds, 0)
            week.append((ds, level, d))
        weeks.append(week)
        current += timedelta(weeks=1)

    num_weeks = len(weeks)
    svg_w = PAD_X + num_weeks * (CELL + GAP) + 20
    svg_h = PAD_Y + 7 * (CELL + GAP) + 60  # extra room for legend

    svg = []
    svg.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">

<!-- Card Background -->
<rect x="2" y="2" width="{svg_w - 4}" height="{svg_h - 4}" rx="{RADIUS}" ry="{RADIUS}"
      fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>

<!-- Terminal Dots -->
<circle cx="18" cy="18" r="5" fill="#ff5f57"/>
<circle cx="34" cy="18" r="5" fill="#febc2e"/>
<circle cx="50" cy="18" r="5" fill="#28c840"/>

<!-- Title -->
<text x="{svg_w / 2}" y="22" fill="{TEXT_COLOR}" font-family="{FONT}" font-size="10" text-anchor="middle">
  Contribution Graph — @aqsam-husnain
</text>
''')

    # Day-of-week labels
    for dow in range(7):
        if DOW_NAMES[dow]:
            y = PAD_Y + dow * (CELL + GAP) + CELL - 2
            svg.append(
                f'<text x="{DOW_LABELS_X}" y="{y}" fill="{LABEL_COLOR}" '
                f'font-family="{FONT}" font-size="9">{DOW_NAMES[dow]}</text>'
            )

    # Month labels
    last_month = -1
    for wi, week in enumerate(weeks):
        for ds, level, d in week:
            if d.month != last_month and d.day <= 7:
                x = PAD_X + wi * (CELL + GAP)
                svg.append(
                    f'<text x="{x}" y="{MONTH_LABELS_Y}" fill="{LABEL_COLOR}" '
                    f'font-family="{FONT}" font-size="9">{MONTH_NAMES[d.month - 1]}</text>'
                )
                last_month = d.month
                break

    # Contribution cells
    for wi, week in enumerate(weeks):
        for dow, (ds, level, d) in enumerate(week):
            x = PAD_X + wi * (CELL + GAP)
            y = PAD_Y + dow * (CELL + GAP)
            color = GOLD_COLORS[min(level, 4)]
            svg.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" ry="2" '
                f'fill="{color}"><title>{ds}</title></rect>'
            )

    # Legend
    legend_y = PAD_Y + 7 * (CELL + GAP) + 15
    svg.append(
        f'<text x="{PAD_X}" y="{legend_y}" fill="{LABEL_COLOR}" '
        f'font-family="{FONT}" font-size="9">Less</text>'
    )
    for i, c in enumerate(GOLD_COLORS):
        lx = PAD_X + 30 + i * (CELL + GAP)
        svg.append(
            f'<rect x="{lx}" y="{legend_y - 10}" width="{CELL}" height="{CELL}" rx="2" fill="{c}"/>'
        )
    svg.append(
        f'<text x="{PAD_X + 30 + 5 * (CELL + GAP) + 4}" y="{legend_y}" fill="{LABEL_COLOR}" '
        f'font-family="{FONT}" font-size="9">More</text>'
    )

    # Metrics
    total = metrics.get("total_contributions", 0)
    cur_streak = metrics.get("current_streak", 0)
    long_streak = metrics.get("longest_streak", 0)
    metrics_y = legend_y + 20
    metrics_text = f"{total} contributions in the last year  ·  🔥 {cur_streak} day streak  ·  ⚡ {long_streak} longest"
    svg.append(
        f'<text x="{svg_w / 2}" y="{metrics_y}" fill="{TEXT_COLOR}" '
        f'font-family="{FONT}" font-size="9.5" text-anchor="middle">{metrics_text}</text>'
    )

    svg.append("</svg>")

    out = root / "contrib-heatmap.svg"
    out.write_text("\n".join(svg), encoding="utf-8")
    print(f"✅ Generated {out} ({num_weeks} weeks, {svg_w}x{svg_h})")


if __name__ == "__main__":
    main()
