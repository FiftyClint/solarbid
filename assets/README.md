# Asset slots

Drop these in and re-run the build scripts. Nothing else changes.

| File | What it is | Status |
|---|---|---|
| `cgf_logo.png` | CGF logo, transparent PNG, roughly 4:1 crop of the wordmark lockup | **still needed** |
| `ground_mount_1.jpg` | Real ground mount install | **still needed** |
| `ground_mount_2.jpg` | Second ground mount install | **still needed** |
| `poultry_roof.jpg` | Optional. A poultry roof array, if one exists. | optional |
| `cgf_team.jpg` | Optional. Bottom right of the company flyer if present. | optional |

The solar flyer lays out however many photos it finds, side by side in one
band. Two real jobs read as a track record; one reads as stock. Landscape crops
work best since each gets a half-width slot.

Images attached in chat do not reach this filesystem. Copy them into `assets/`
from a local clone and push.

Build:

```bash
python scripts/build_company_flyer.py                    # poultry
python scripts/build_company_flyer.py --vertical general # other industries
python scripts/build_ad.py                               # solar, by farm size
```

## Brand

`scripts/brand.py` holds the palette and every shared element. All three pieces
read from it.

| Token | Hex | Use |
|---|---|---|
| `BRAND` | `#155DAE` | Headlines, key figures, call bar |
| `BRAND_MID` | `#3D86BA` | Secondary |
| `ACCENT` | `#52FB2A` | **Dark ground only** |
| `ACCENT_SOFT` | `#AEF75C` | Fill, with dark text over it |
| `INK` | `#10243A` | Body text. Navy derived from the brand blue |
| `PAPER` | `#FCFDFD` | Ground |

**Contrast rule, do not break it.** `#52FB2A` on white measures about 1.8:1 and
`#AEF75C` is worse. Neither is ever text on a light background. The green earns
its place on the navy bars and in the top stripe, where it has real contrast and
carries the brand without being asked to be legible.

Also confirm before printing: `PHONE`, `ADDRESS`, `WEB` in `brand.py`, and the
Newell Coach case figures in `build_company_flyer.py`. Both CGF domains are
blocked from the build environment, so those came from a public listing.
