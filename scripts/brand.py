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

# --- CGF brand ------------------------------------------------------------
# Supplied palette: #155dae deep blue, #3d86ba mid blue, #52fb2a green,
# #aef75c lime, #fcfdfd white.
#
# CONTRAST RULE, do not break it: the greens are accents, never text on white.
# #52fb2a on white measures about 1.8:1 and #aef75c is worse. They read as
# highlight against dark ground or as a fill with dark text over them. Blue and
# navy carry everything that has to be read.
BRAND = "#155DAE"        # primary, headlines and key figures
BRAND_DK = "#0F4685"
BRAND_MID = "#3D86BA"
ACCENT = "#52FB2A"       # on dark ground only
ACCENT_SOFT = "#AEF75C"  # fill, with dark text over it
PAPER = "#FCFDFD"
PANEL = "#EEF4FA"
INK = "#10243A"          # navy derived from the brand blue, not a flat black
MUTE = "#5C7387"
RULE_C = "#CFDCE8"

# --- swap for real details -----------------------------------------------
PHONE = "913-349-6586"        # from public listing; confirm before printing
ADDRESS = "1800 Main St, Parsons, KS 67357"
WEB = "cleanergreenerfuture.com"

ASSETS = Path("assets")
LOGO_PATH = ASSETS / "cgf_logo.png"
PHOTO_ROOF = ASSETS / "poultry_roof.jpg"
PHOTO_TEAM = ASSETS / "cgf_team.jpg"

# Real CGF/NEA Solar ground mount installs. Two of them run side by side on the
# solar flyer, which is stronger than one wide crop: two jobs reads as a track
# record, one reads as a stock photo.
PHOTO_GROUND = [ASSETS / "ground_mount_1.jpg", ASSETS / "ground_mount_2.jpg"]


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


def photo_band(ax, x0, x1, y0, y1, paths, fallback_label, fallback_sub=""):
    """Fill a band with however many real photos exist, else a placeholder."""
    from matplotlib.image import imread

    have = [p for p in paths if p.exists()]
    if not have:
        slot(ax, x0, y0, x1, y1, fallback_label, fallback_sub)
        return 0

    gap = 0.012
    w = ((x1 - x0) - gap * (len(have) - 1)) / len(have)
    for i, path in enumerate(have):
        left = x0 + i * (w + gap)
        ax.imshow(imread(str(path)), extent=(left, left + w, y0, y1),
                  aspect="auto", zorder=2)
    return len(have)


def rule(ax, y, x0=L, x1=R, c=RULE_C, lw=0.8):
    ax.plot([x0, x1], [y, y], color=c, lw=lw, solid_capstyle="butt", zorder=1)


def masthead(ax, tagline):
    """Identity bar shared by every piece.

    A blue-to-green stripe runs the full bleed at the top, echoing the logo's
    own split. It is the only place the green appears against light ground, and
    it appears as a solid mark rather than as anything anyone has to read.
    """
    from matplotlib.image import imread

    ax.add_patch(Rectangle((0, 0.988), 0.62, 0.012, facecolor=BRAND,
                           edgecolor="none", zorder=4))
    ax.add_patch(Rectangle((0.62, 0.988), 0.38, 0.012, facecolor=ACCENT,
                           edgecolor="none", zorder=4))

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
            color="#CFE2F5", ha="left", va="center")
    ax.text(R - 0.024, y + h * 0.50, PHONE, family=DISPLAY, weight="bold",
            size=26, color=PAPER, ha="right", va="center")


def footer(ax, y=0.014):
    ax.text(L, y, f"{ADDRESS}   ·   {WEB}", family=MONO, size=6.2,
            color=MUTE, ha="left", va="center")
