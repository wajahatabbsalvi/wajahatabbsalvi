"""
prep_photo.py — Background removal + contrast enhancement for hero portrait.
Usage: python scripts/prep_photo.py hero.png
"""
import sys
import os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <input_image>")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"[ERROR] File not found: {input_path}")
        sys.exit(1)

    from rembg import remove
    from PIL import Image, ImageEnhance
    import numpy as np
    import cv2

    print(f"📸 Loading image: {input_path}")
    with open(input_path, "rb") as f:
        input_data = f.read()

    print("🔧 Removing background with U2Net...")
    output_data = remove(input_data)

    img = Image.open(__import__("io").BytesIO(output_data)).convert("RGBA")

    # Convert to numpy for CLAHE contrast enhancement
    arr = np.array(img)
    # Work on the RGB channels only
    rgb = arr[:, :, :3]
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    l = clahe.apply(l)
    lab = cv2.merge([l, a, b])
    rgb_enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    arr[:, :, :3] = rgb_enhanced
    img = Image.fromarray(arr)

    # Auto-crop to content bounding box with padding
    bbox = img.split()[-1].getbbox()  # alpha channel bbox
    if bbox:
        pad = 20
        x1 = max(0, bbox[0] - pad)
        y1 = max(0, bbox[1] - pad)
        x2 = min(img.width, bbox[2] + pad)
        y2 = min(img.height, bbox[3] + pad)
        img = img.crop((x1, y1, x2, y2))

    # Resize to a reasonable height for ASCII conversion
    target_h = 600
    ratio = target_h / img.height
    target_w = int(img.width * ratio)
    img = img.resize((target_w, target_h), Image.LANCZOS)

    # Bump brightness slightly
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)

    output_path = Path(input_path).parent / "source-prepped.png"
    img.save(output_path)
    print(f"✅ Saved prepped image: {output_path} ({img.width}x{img.height})")

if __name__ == "__main__":
    main()
