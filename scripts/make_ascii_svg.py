"""
make_ascii_svg.py — Convert source-prepped.png into an animated ASCII art SVG.
Generates hxni-ascii.svg with gold monospace typography inside a terminal card.
"""
import os
import sys
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')

# ASCII brightness ramp (dark → bright)
ASCII_RAMP = " .`:-=+*cs#%@"

# Configuration
FONT_SIZE = 5.5
LINE_HEIGHT = 6.2
CHAR_WIDTH = 3.6
COLS = 100  # ASCII columns
BG_COLOR = "#0d0d0d"
TEXT_COLOR = "#D4AF37"
BORDER_COLOR = "#2a2a2a"
CARD_RADIUS = 12
PADDING_X = 16
PADDING_Y = 50  # leave room for terminal bar


def pixel_to_ascii(pixel, alpha=255):
    """Map a grayscale pixel to an ASCII character."""
    if alpha < 30:
        return " "
    idx = int(pixel / 255 * (len(ASCII_RAMP) - 1))
    return ASCII_RAMP[idx]


def main():
    root = Path(__file__).resolve().parent.parent
    img_path = root / "source-prepped.png"

    if not img_path.exists():
        print(f"[ERROR] {img_path} not found. Run prep_photo.py first.")
        return

    print(f"🎨 Loading {img_path}...")
    img = Image.open(img_path).convert("RGBA")

    # Calculate rows to maintain aspect ratio
    aspect = img.height / img.width
    char_aspect = LINE_HEIGHT / CHAR_WIDTH
    rows = int(COLS * aspect / char_aspect)

    # Resize image to ASCII grid
    img_resized = img.resize((COLS, rows), Image.LANCZOS)

    # Convert to ASCII lines
    ascii_lines = []
    for y in range(rows):
        line = ""
        for x in range(COLS):
            r, g, b, a = img_resized.getpixel((x, y))
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
            line += pixel_to_ascii(gray, a)
        ascii_lines.append(line.rstrip())

    # Strip empty trailing lines
    while ascii_lines and not ascii_lines[-1].strip():
        ascii_lines.pop()

    num_lines = len(ascii_lines)
    content_w = COLS * CHAR_WIDTH + PADDING_X * 2
    content_h = num_lines * LINE_HEIGHT + PADDING_Y + 20
    svg_w = content_w + 4
    svg_h = content_h + 4

    # Build SVG
    svg_parts = []
    svg_parts.append(f'''<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">
<defs>
  <style>
    @keyframes fin {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .ascii-line {{
      opacity: 0;
      animation: fin 0.3s ease forwards;
    }}
  </style>
</defs>

<!-- Terminal Card Background -->
<rect x="2" y="2" width="{content_w}" height="{content_h}" rx="{CARD_RADIUS}" ry="{CARD_RADIUS}"
      fill="{BG_COLOR}" stroke="{BORDER_COLOR}" stroke-width="1.5"/>

<!-- macOS Terminal Dots -->
<circle cx="18" cy="18" r="5" fill="#ff5f57"/>
<circle cx="34" cy="18" r="5" fill="#febc2e"/>
<circle cx="50" cy="18" r="5" fill="#28c840"/>

<!-- Terminal Title -->
<text x="{content_w / 2 + 2}" y="22" fill="#888" font-family="'SF Mono','Fira Code','Cascadia Code',monospace"
      font-size="9" text-anchor="middle">aqsam-husnain — ascii portrait</text>
''')

    # ASCII text lines
    for i, line in enumerate(ascii_lines):
        if not line.strip():
            continue
        y = PADDING_Y + i * LINE_HEIGHT
        delay = i * 0.015
        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
        svg_parts.append(
            f'<text class="ascii-line" x="{PADDING_X}" y="{y}" '
            f'fill="{TEXT_COLOR}" font-family="\'SF Mono\',\'Fira Code\',\'Cascadia Code\',monospace" '
            f'font-size="{FONT_SIZE}" style="animation-delay:{delay:.3f}s" '
            f'xml:space="preserve">{escaped}</text>'
        )

    svg_parts.append("</svg>")

    out_path = root / "wajahat-ascii.svg"
    out_path.write_text("\n".join(svg_parts), encoding="utf-8")
    print(f"✅ Generated {out_path} ({num_lines} lines, {svg_w:.0f}x{svg_h:.0f})")


if __name__ == "__main__":
    main()
