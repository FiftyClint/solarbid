"""Shared brand system for CGF print pieces.

Both flyers go in the same envelope, so they have to read as a set. Palette,
type and furniture live here once; change a color and every piece updates.

ASSET SLOTS: swap BRAND, PHONE and the asset paths for the real ones.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
# Paired dollar signs in a string get parsed as LaTeX math and silently mangle
# the text. Every figure on these pieces is a dollar amount, so turn it off.
matplotlib.rcParams["text.parse_math"] = False
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle

FONTS = Path("/root/.claude/skills/synced/canvas-design/canvas-fonts")
for _f in FONTS.glob("*.ttf"):
    fm.fontManager.addfont(str(_f))

DISPLAY = "Big Shoulders"
BODY = "Work Sans"
MONO = "Geist Mono"

# --- swap for real brand colors ------------------------------------------
BRAND = "#9E2B20"
BRAND_DK = "#6E1E16"
PAPER = "#F7F3EA"
PANEL = "#EDE7DA"
INK = "#1A1713"
MUTE = "#6B635A"
RULE_C = "#CFC6B6"

# --- swap for real details -----------------------------------------------
PHONE = "913-349-6586"        # from public listing; confirm before printing
ADDRESS = "1800 Main St, Parsons, KS 67357"
WEB = "cleanergreenerfuture.com"

ASSETS = Path("assets")
LOGO_PATH = ASSETS / "cgf_logo.png"
PHOTO_ROOF = ASSETS / "poultry_roof.jpg"
PHOTO_TEAM = ASSETS / "cgf_team.jpg"

PAGE_W, PAGE_H = 8.5, 11.0
L, R = 0.075, 0.925


def slot(ax, x0, y0, x1, y1, label, sub=""):
    """A placeholder that reads as deliberate rather than broken."""
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, facecolor=PANEL,
                           edgecolor=RULE_C, linewidth=0.8,
                           linestyle=(0, (4, 3))))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2 + (0.008 if sub else 0), label,
            family=MONO, size=7.0, color=MUTE, ha="center", va="center")
    if sub:
        ax.text((x0 + x1) / 2, (y0 + y1) / 2 - 0.014, sub, family=MONO,
                size=5.8, color=MUTE, ha="center", va="center")


def rule(ax, y, x0=L, x1=R, c=RULE_C, lw=0.8):
    ax.plot([x0, x1], [y, y], color=c, lw=lw, solid_capstyle="butt", zorder=1)


def masthead(ax, tagline):
    """Identity bar shared by every piece."""
    from matplotlib.image import imread

    if LOGO_PATH.exists():
        ax.imshow(imread(str(LOGO_PATH)), extent=(L, L + 0.16, 0.938, 0.972),
                  aspect="auto", zorder=3)
    else:
        slot(ax, L, 0.936, L + 0.16, 0.974, "CGF LOGO")

    ax.text(R, 0.966, PHONE, family=DISPLAY, weight="bold", size=21,
            color=BRAND, ha="right", va="center")
    ax.text(R, 0.941, tagline, family=MONO, size=6.4, color=MUTE,
            ha="right", va="center")
    rule(ax, 0.921, lw=1.6, c=INK)


def callbar(ax, headline, sub, y=0.028, h=0.072):
    """The one ask, in the same place on every piece."""
    from matplotlib.patches import FancyBboxPatch

    ax.add_patch(FancyBboxPatch((L, y), R - L, h,
                                boxstyle="round,pad=0,rounding_size=0.006",
                                facecolor=BRAND, edgecolor="none"))
    ax.text(L + 0.024, y + h * 0.71, headline, family=DISPLAY, weight="bold",
            size=23, color=PAPER, ha="left", va="center")
    ax.text(L + 0.024, y + h * 0.32, sub, family=BODY, size=9.0,
            color="#F0D9D5", ha="left", va="center")
    ax.text(R - 0.024, y + h * 0.50, PHONE, family=DISPLAY, weight="bold",
            size=26, color=PAPER, ha="right", va="center")


def footer(ax, y=0.014):
    ax.text(L, y, f"{ADDRESS}   ·   {WEB}", family=MONO, size=6.2,
            color=MUTE, ha="left", va="center")
