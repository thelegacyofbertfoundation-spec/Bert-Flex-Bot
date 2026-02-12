"""
Cyberpunk-styled $BERT Flex Card Generator v3.
Features CyberBert mascot, no rank, high-res 2x rendering.
"""

import os
import math
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

from config import (
    CARD_WIDTH, CARD_HEIGHT, TOKEN_TICKER, TOKEN_NAME,
)

# ── Render at 2x then downscale ──
SCALE = 2
W = CARD_WIDTH * SCALE
H = CARD_HEIGHT * SCALE

# ── Colors ──
CYAN = (0, 240, 255)
MAGENTA = (255, 0, 229)
GOLD = (255, 215, 0)
NEON_GREEN = (0, 255, 130)
RED = (255, 60, 80)
BG_DARK = (8, 8, 18)
WHITE = (255, 255, 255)
DIM = (100, 100, 130)
LABEL_COLOR = (160, 160, 190)

# ── Mascot path ──
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MASCOT_PATH = os.path.join(SCRIPT_DIR, "assets", "cyberbert.png")


def _font(size, style="bold"):
    """Load fonts with extensive fallbacks for different environments."""
    paths = {
        "bold": [
            "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ],
        "medium": [
            "/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
        "regular": [
            "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
        "light": [
            "/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-ExtraLight.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "C:/Windows/Fonts/segoeuil.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ],
        "mono": [
            "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "C:/Windows/Fonts/consola.ttf",
            "C:/Windows/Fonts/cour.ttf",
        ],
        "mono_bold": [
            "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
            "C:/Windows/Fonts/consolab.ttf",
            "C:/Windows/Fonts/courbd.ttf",
        ],
    }
    for path in paths.get(style, paths["bold"]):
        try:
            return ImageFont.truetype(path, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def _glass_card(draw, bbox, accent_color, radius=16):
    """Glassmorphism card with accent border."""
    x0, y0, x1, y1 = [int(v) for v in bbox]
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=(15, 15, 30, 220))
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, outline=(*accent_color, 160), width=3)
    draw.line([(x0 + radius, y0 + 2), (x1 - radius, y0 + 2)], fill=(*accent_color, 80), width=2)


def _draw_bg(img, draw):
    """Background grid, glow, particles."""
    # Grid
    for x in range(0, W, 60):
        draw.line([(x, 0), (x, H)], fill=(20, 20, 40), width=1)
    for y in range(0, H, 60):
        draw.line([(0, y), (W, y)], fill=(20, 20, 40), width=1)

    # Corner glows
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for r in range(350, 0, -3):
        a = int(14 * (r / 350))
        gd.ellipse([-r, -r, r, r], fill=(0, 240, 255, a))
    for r in range(250, 0, -3):
        a = int(10 * (r / 250))
        gd.ellipse([W - r, H - r, W + r, H + r], fill=(255, 0, 229, a))
    img.paste(Image.alpha_composite(img, glow))

    # Particles
    for _ in range(35):
        x = random.randint(0, W)
        y = random.randint(0, H)
        s = random.randint(2, 5)
        a = random.randint(30, 100)
        c = random.choice([(*CYAN, a), (*MAGENTA, a), (255, 255, 255, a)])
        draw.ellipse([x, y, x + s, y + s], fill=c)


def _scanlines(img, opacity=8):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for y in range(0, img.height, 4):
        d.line([(0, y), (img.width, y)], fill=(0, 0, 0, opacity))
    return Image.alpha_composite(img, overlay)


def _gradient_bars(draw):
    """Top and bottom neon gradient bars."""
    for x in range(W):
        ratio = x / W
        r = int(CYAN[0] * (1 - ratio) + MAGENTA[0] * ratio)
        g = int(CYAN[1] * (1 - ratio) + MAGENTA[1] * ratio)
        b = int(CYAN[2] * (1 - ratio) + MAGENTA[2] * ratio)
        draw.line([(x, 0), (x, 6)], fill=(r, g, b))
    for x in range(W):
        ratio = x / W
        r = int(MAGENTA[0] * (1 - ratio) + CYAN[0] * ratio)
        g = int(MAGENTA[1] * (1 - ratio) + CYAN[1] * ratio)
        b = int(MAGENTA[2] * (1 - ratio) + CYAN[2] * ratio)
        draw.line([(x, H - 6), (x, H)], fill=(r, g, b))


def _neon_text(draw, pos, text, font, color, glow_radius=2):
    x, y = pos
    for dx in range(-glow_radius, glow_radius + 1):
        for dy in range(-glow_radius, glow_radius + 1):
            if dx == 0 and dy == 0:
                continue
            draw.text((x + dx, y + dy), text, font=font, fill=(*color, 35))
    draw.text((x, y), text, font=font, fill=(*color, 255))


def _get_hands_label(duration_str):
    if not duration_str or duration_str == "New holder":
        return "NEW"
    if "y" in duration_str:
        return "OG DIAMOND"
    if "m" in duration_str:
        try:
            months = int(duration_str.split("m")[0].strip())
        except ValueError:
            months = 0
        if months >= 6: return "DIAMOND"
        if months >= 3: return "STRONG"
        return "STEADY"
    return "FRESH"


def _format_mcap(mcap):
    if not mcap: return "N/A"
    if mcap >= 1e9: return f"${mcap / 1e9:.1f}B"
    if mcap >= 1e6: return f"${mcap / 1e6:.1f}M"
    if mcap >= 1e3: return f"${mcap / 1e3:.1f}K"
    return f"${mcap:.0f}"


def _place_mascot(img):
    """Place CyberBert on the right side with a gradient fade."""
    try:
        mascot = Image.open(MASCOT_PATH).convert("RGBA")
    except (FileNotFoundError, OSError):
        return  # No mascot file, skip

    # Target: fill right ~40% of card height, positioned bottom-right
    target_h = int(H * 0.85)
    aspect = mascot.width / mascot.height
    target_w = int(target_h * aspect)

    mascot = mascot.resize((target_w, target_h), Image.LANCZOS)

    # Create gradient alpha mask (fade on left edge)
    mask = Image.new("L", (target_w, target_h), 255)
    mask_draw = ImageDraw.Draw(mask)
    fade_width = int(target_w * 0.45)  # 45% fade zone
    for x in range(fade_width):
        alpha = int(255 * (x / fade_width))
        mask_draw.line([(x, 0), (x, target_h)], fill=alpha)

    # Apply mask to mascot
    mascot.putalpha(Image.composite(mascot.split()[3], Image.new("L", mascot.size, 0), mask))

    # Position: right-aligned, vertically centered
    paste_x = W - target_w + int(target_w * 0.08)  # slight overflow right
    paste_y = (H - target_h) // 2

    img.paste(mascot, (paste_x, paste_y), mascot)


# ══════════════════════════════════════
#  MAIN GENERATOR
# ══════════════════════════════════════

def generate_flex_card(data: dict) -> BytesIO:
    random.seed(hash(data.get("wallet", "")) % 2**32)

    img = Image.new("RGBA", (W, H), (*BG_DARK, 255))
    draw = ImageDraw.Draw(img)

    # === Background ===
    _draw_bg(img, draw)
    draw = ImageDraw.Draw(img)

    # === Place mascot FIRST (behind text) ===
    _place_mascot(img)
    draw = ImageDraw.Draw(img)

    _gradient_bars(draw)

    # === Layout: text on left ~60% ===
    px = 60
    text_zone_w = int(W * 0.58)

    # ── HEADER ──
    y = 50

    f_ticker = _font(56, "bold")
    _neon_text(draw, (px, y), TOKEN_TICKER, f_ticker, CYAN, glow_radius=3)

    # "FLEX CARD" badge
    f_badge = _font(24, "medium")
    badge_text = "FLEX CARD"
    badge_w = draw.textlength(badge_text, font=f_badge)
    badge_x = text_zone_w - badge_w - 20
    draw.rounded_rectangle(
        [badge_x - 15, y + 8, badge_x + badge_w + 15, y + 48],
        radius=8, fill=(255, 0, 229, 30), outline=(*MAGENTA, 200), width=2,
    )
    draw.text((badge_x, y + 12), badge_text, font=f_badge, fill=MAGENTA)

    y += 70

    # Wallet address
    f_wallet = _font(26, "mono")
    wallet_short = data.get("wallet_short", "????...????")
    draw.text((px, y), wallet_short, font=f_wallet, fill=DIM)
    y += 50

    # Separator
    draw.line([(px, y), (text_zone_w, y)], fill=(*CYAN, 50), width=2)
    y += 25

    # ── BALANCE ──
    f_label = _font(22, "medium")
    draw.text((px, y), "TOKEN BALANCE", font=f_label, fill=LABEL_COLOR)
    y += 35

    f_balance = _font(72, "bold")
    balance_str = data.get("balance_formatted", "0")
    _neon_text(draw, (px, y), f"{balance_str} BERT", f_balance, WHITE, glow_radius=2)
    y += 95

    # USD value + 24h change
    f_usd = _font(38, "bold")
    usd_str = data.get("usd_value_formatted", "$0")
    draw.text((px, y), f"~ {usd_str}", font=f_usd, fill=NEON_GREEN)

    change = data.get("price_change_24h")
    if change is not None:
        change_color = NEON_GREEN if change >= 0 else RED
        arrow = "+" if change >= 0 else ""
        f_change = _font(26, "medium")
        cx = px + draw.textlength(f"~ {usd_str}", font=f_usd) + 25
        draw.text((cx, y + 10), f"{arrow}{change:.1f}% 24h", font=f_change, fill=change_color)

    y += 70

    # Separator
    draw.line([(px, y), (text_zone_w, y)], fill=(*CYAN, 50), width=2)
    y += 25

    # ── STAT CARDS (2 cards: Diamond Hands + Market Cap) ──
    card_gap = 25
    card_w = (text_zone_w - px - card_gap) // 2
    card_h = 175

    cards = [
        {
            "label": "DIAMOND HANDS",
            "value": data.get("hold_duration", "N/A"),
            "sub": _get_hands_label(data.get("hold_duration", "")),
            "color": CYAN,
        },
        {
            "label": "MARKET CAP",
            "value": _format_mcap(data.get("market_cap")),
            "sub": TOKEN_TICKER,
            "color": MAGENTA,
        },
    ]

    for i, card in enumerate(cards):
        cx = px + i * (card_w + card_gap)
        _glass_card(draw, (cx, y, cx + card_w, y + card_h), card["color"], radius=14)

        f_cl = _font(18, "medium")
        draw.text((cx + 22, y + 16), card["label"], font=f_cl, fill=LABEL_COLOR)

        val = card["value"]
        f_val = _font(28 if len(val) > 14 else 36, "bold")
        _neon_text(draw, (cx + 22, y + 55), val, f_val, card["color"], glow_radius=1)

        if card["sub"]:
            f_sub = _font(18, "regular")
            draw.text((cx + 22, y + card_h - 40), card["sub"], font=f_sub, fill=DIM)

    # ── FOOTER ──
    footer_y = H - 55
    f_footer = _font(20, "regular")
    draw.text((px, footer_y), "www.bert.global  |  /flex your bag", font=f_footer, fill=DIM)

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ts_w = draw.textlength(now, font=f_footer)
    draw.text((W - px - ts_w, footer_y), now, font=f_footer, fill=DIM)

    # === Post-processing ===
    img = _scanlines(img, opacity=8)
    img = img.resize((CARD_WIDTH, CARD_HEIGHT), Image.LANCZOS)

    buffer = BytesIO()
    img.save(buffer, format="PNG", quality=95)
    buffer.seek(0)
    return buffer


# ── Preview ──
if __name__ == "__main__":
    sample_data = {
        "wallet": "5c1C2RRRqDmbbqjBxcv4fZuknqA2mF7WhX3eLCbxcv4f",
        "wallet_short": "5c1C...bxcv",
        "balance": 18_040_000,
        "balance_formatted": "18.04M",
        "price_usd": 0.0098,
        "usd_value": 176_740,
        "usd_value_formatted": "$176.74K",
        "market_cap": 10_800_000,
        "price_change_24h": 12.8,
        "hold_duration": "5m 6d",
    }
    buf = generate_flex_card(sample_data)
    with open("sample_flex_card.png", "wb") as f:
        f.write(buf.read())
    print("Sample card saved to sample_flex_card.png")
