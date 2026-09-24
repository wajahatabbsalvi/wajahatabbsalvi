"""
make_info_card.py — Generate a neofetch-style terminal info card SVG for Wajahat Abbas.
Ensures 100% strict XML validity (properly escaped entities &amp;, &lt;, &gt;).
"""
import sys
import html
import xml.etree.ElementTree as ET
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

BG = "#0d0d0d"
BORDER = "#2a2a2a"
GOLD = "#D4AF37"
SILVER = "#c0c0c0"
MUTED = "#666666"
RADIUS = 12
FONT = "'SF Mono','Fira Code','Cascadia Code',monospace"
FONT_SIZE = 11.5
LINE_H = 25
PAD_X = 24
PAD_Y = 55
CARD_W = 490
SEPARATOR = "------------------------------------"

INFO_LINES = [
    ("OS", "Full-Stack & AI Systems Architect v3.2"),
    ("Host", "Wajahat Abbas"),
    ("Role", "Software Engineer · 3+ Years Experience"),
    ("Location", "Punjab, Pakistan (PKT UTC+5)"),
    ("Status", "Available for High-Impact Roles"),
    ("", SEPARATOR),
    ("Frontend", "React · Next.js · TypeScript · Tailwind · Redux"),
    ("Backend", "Python · FastAPI · Flask · Node.js · Express · Go"),
    ("AI / LLMs", "OpenAI · Claude 3.5 · LangChain · Qdrant · Ollama"),
    ("Architecture", "Microservices · WebSockets · CRDT · Celery · BullMQ"),
    ("Databases", "PostgreSQL · Redis · MongoDB · SQLAlchemy · Prisma"),
    ("DevOps", "Docker · Container Orchestration · Prometheus · Git"),
    ("", SEPARATOR),
    ("GitHub", "github.com/wajahatabbsalvi"),
    ("Email", "codespellbinders@gmail.com"),
    ("", SEPARATOR),
    ("", "Architecting distributed systems & autonomous AI agents."),
]


def main():
    root = Path(__file__).resolve().parent.parent
    num_lines = len(INFO_LINES)
    card_h = PAD_Y + num_lines * LINE_H + 30

    svg = []
    svg.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{CARD_W}" height="{card_h}" viewBox="0 0 {CARD_W} {card_h}">
<defs>
  <style>
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateX(-8px); }}
      to   {{ opacity: 1; transform: translateX(0); }}
    }}
    .info-line {{
      opacity: 0;
      animation: fadeIn 0.4s ease forwards;
    }}
  </style>
</defs>

<!-- Card Background -->
<rect x="2" y="2" width="{CARD_W - 4}" height="{card_h - 4}" rx="{RADIUS}" ry="{RADIUS}"
      fill="{BG}" stroke="{BORDER}" stroke-width="1.5"/>

<!-- Terminal Dots -->
<circle cx="20" cy="20" r="5" fill="#ff5f57"/>
<circle cx="36" cy="20" r="5" fill="#febc2e"/>
<circle cx="52" cy="20" r="5" fill="#28c840"/>

<!-- Terminal Title -->
<text x="{CARD_W / 2}" y="24" fill="#888" font-family="{FONT}" font-size="10" text-anchor="middle">wajahat@terminal:~</text>
''')

    for i, (key, val) in enumerate(INFO_LINES):
        y = PAD_Y + i * LINE_H
        delay = 0.4 + i * 0.06

        safe_val = html.escape(val, quote=True)
        safe_key = html.escape(key, quote=True)

        if key == "" and val == SEPARATOR:
            svg.append(
                f'<text class="info-line" x="{PAD_X}" y="{y}" fill="{MUTED}" '
                f'font-family="{FONT}" font-size="{FONT_SIZE}" '
                f'style="animation-delay:{delay:.2f}s" xml:space="preserve">{safe_val}</text>'
            )
        elif key == "":
            svg.append(
                f'<text class="info-line" x="{PAD_X}" y="{y}" fill="{SILVER}" '
                f'font-family="{FONT}" font-size="{FONT_SIZE}" '
                f'style="animation-delay:{delay:.2f}s">{safe_val}</text>'
            )
        else:
            svg.append(
                f'<text class="info-line" x="{PAD_X}" y="{y}" font-family="{FONT}" '
                f'font-size="{FONT_SIZE}" style="animation-delay:{delay:.2f}s">'
                f'<tspan fill="{GOLD}">{safe_key}</tspan>'
                f'<tspan fill="{MUTED}"> ~ </tspan>'
                f'<tspan fill="{SILVER}">{safe_val}</tspan>'
                f'</text>'
            )

    svg.append("</svg>")

    svg_content = "\n".join(svg)

    # Strict XML Validation
    try:
        ET.fromstring(svg_content)
        print("✅ Strict XML validation passed for info-card.svg")
    except Exception as e:
        print(f"❌ XML validation failed: {e}")
        sys.exit(1)

    out = root / "info-card.svg"
    out.write_text(svg_content, encoding="utf-8")
    print(f"✅ Generated {out} ({num_lines} lines, {CARD_W}x{card_h})")


if __name__ == "__main__":
    main()
