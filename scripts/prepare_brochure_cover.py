#!/usr/bin/env python3
"""Prepare a clean brochure cover image from the source flyer.

This script:
1) Center-crops the source image to match the zine panel aspect ratio.
2) Soft-masks instruction/date/location blocks so only the decorative border + title remain.
3) Saves deterministic outputs used by LaTeX.
"""

from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode


QR_URL = "https://daniel-redder.github.io/iai-research-is-awesome/"
QR_FILL_COLOR = "#8B5A2B"


TARGET_W_IN = 2.35
TARGET_H_IN = 3.85
TARGET_RATIO = TARGET_W_IN / TARGET_H_IN


def center_crop_to_ratio(image: Image.Image, target_ratio: float) -> Image.Image:
    w, h = image.size
    current_ratio = w / h

    if current_ratio > target_ratio:
        # Too wide: crop left/right.
        new_w = int(round(h * target_ratio))
        left = (w - new_w) // 2
        return image.crop((left, 0, left + new_w, h))

    if current_ratio < target_ratio:
        # Too tall: crop top/bottom.
        new_h = int(round(w / target_ratio))
        top = (h - new_h) // 2
        return image.crop((0, top, w, top + new_h))

    return image.copy()


def zoom_to_fill(image: Image.Image, zoom: float = 1.07) -> Image.Image:
    if zoom <= 1.0:
        return image.copy()

    w, h = image.size
    zw, zh = int(round(w * zoom)), int(round(h * zoom))
    resized = image.resize((zw, zh), Image.Resampling.LANCZOS)
    left = (zw - w) // 2
    top = (zh - h) // 2
    return resized.crop((left, top, left + w, top + h))


def build_white_block_mask(size: tuple[int, int]) -> Image.Image:
    """Binary mask: 255 where we force a white block."""
    w, h = size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)

    # Remove old logo band.
    draw.rectangle(
        (int(0.17 * w), int(0.01 * h), int(0.83 * w), int(0.16 * h)),
        fill=255,
    )

    # Remove instructions + date/location block.
    draw.rectangle(
        (int(0.10 * w), int(0.46 * h), int(0.90 * w), int(0.95 * h)),
        fill=255,
    )

    return mask


def remove_paper_texture_boolean(image: Image.Image, block_mask: Image.Image) -> Image.Image:
    """Boolean mask cleanup: whiten paper-like pixels and forced block regions."""
    rgb = image.convert("RGB")
    px = rgb.load()
    bm = block_mask.load()
    w, h = rgb.size

    for y in range(h):
        for x in range(w):
            if bm[x, y] > 0:
                px[x, y] = (255, 255, 255)
                continue

            r, g, b = px[x, y]
            vmax = max(r, g, b)
            vmin = min(r, g, b)
            sat = vmax - vmin

            # Boolean condition for "paper" texture pixels.
            is_paper = vmax >= 190 and sat <= 26
            if is_paper:
                px[x, y] = (255, 255, 255)

    return rgb.convert("RGBA")


def generate_qr(out_path: Path) -> None:
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=2,
    )
    qr.add_data(QR_URL)
    qr.make(fit=True)
    img = qr.make_image(fill_color=QR_FILL_COLOR, back_color="white").convert("RGB")
    img.save(out_path)


def generate_full_cover(clean_out: Path, logo_out: Path, qr_out: Path, out_path: Path) -> None:
    """Composite the entire cover into one exact-size PNG with no leakage risk."""
    canvas = Image.open(clean_out).convert("RGBA").resize((550, 850), Image.Resampling.LANCZOS)

    logo = Image.open(logo_out).convert("RGBA")
    logo.thumbnail((330, 155), Image.Resampling.LANCZOS)
    canvas.alpha_composite(logo, ((550 - logo.width) // 2, 24))

    font_paths = [
        "/nix/store/vkkzsj1pzpqajms973am53k137gjknrp-noto-fonts-2026.07.01/share/fonts/opentype/texgyrechorus-mediumitalic.otf",
        "/nix/store/vkkzsj1pzpqajms973am53k137gjknrp-noto-fonts-2026.07.01/share/fonts/opentype/TeXGyreChorus-MediumItalic.otf",
    ]
    script_font_path = next((p for p in font_paths if Path(p).exists()), None)
    draw = ImageDraw.Draw(canvas)

    if script_font_path:
        title_font = ImageFont.truetype(script_font_path, 96)
        title = "Friends Giving Potluck"
        box = draw.textbbox((0, 0), title, font=title_font)
        title_width = box[2] - box[0]
        draw.text(((550 - title_width) // 2, 220), title, font=title_font, fill=(104, 56, 38, 255), stroke_width=0)

    qr = Image.open(qr_out).convert("RGBA")
    qr.thumbnail((150, 150), Image.Resampling.LANCZOS)
    canvas.alpha_composite(qr, ((550 - qr.width) // 2, 515))

    if script_font_path:
        caption_font = ImageFont.truetype(script_font_path, 34)
        caption = "See our publications!"
        box = draw.textbbox((0, 0), caption, font=caption_font)
        caption_width = box[2] - box[0]
        draw.text(((550 - caption_width) // 2, 678), caption, font=caption_font, fill=(104, 56, 38, 255))

    canvas.convert("RGB").save(out_path)


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    brochure = repo_root / "brochure"

    src = brochure / "friendsgiving_reference.png"
    cropped_out = brochure / "friendsgiving_cover_cropped.png"
    clean_out = brochure / "friendsgiving_cover_clean.png"
    qr_out = brochure / "iai_site_qr.png"
    full_cover_out = brochure / "friendsgiving_full_cover.png"

    if not src.exists():
        raise FileNotFoundError(f"Missing source image: {src}")

    with Image.open(src) as img:
        cropped = center_crop_to_ratio(img, TARGET_RATIO)
        cropped = zoom_to_fill(cropped, zoom=1.07)
        cropped.save(cropped_out)

        block_mask = build_white_block_mask(cropped.size)
        cleaned = remove_paper_texture_boolean(cropped, block_mask)
        cleaned.save(clean_out)

    generate_qr(qr_out)
    generate_full_cover(clean_out, brochure / "InstituteArtificialIntelligence_logo_2.png", qr_out, full_cover_out)

    print(f"Wrote: {cropped_out}")
    print(f"Wrote: {clean_out}")
    print(f"Wrote: {qr_out}")
    print(f"Wrote: {full_cover_out}")


if __name__ == "__main__":
    main()
