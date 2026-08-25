# Print and mail spec

What to hand a printer, and what to buy. 135 envelopes total, in two cells.
That is one envelope per recipient, not per farm: 165 farms belong to 135
people, and 25 of them own more than one.

| cell | envelopes | printed piece | pages | sheets |
|---|---|---|---|---|
| broiler | 58 | `out/home_print/CGF_Mailer_2page_HOMEPRINT.pdf` | 2, duplex | 58 |
| flyer | 77 | `out/home_print/CGF_Farm_Energy_Review_HOMEPRINT.pdf` | 1, single side | 77 |

The Canva pieces above are what goes in the envelopes. The Python-built
`out/cgf_mailer.pdf` and `out/cgf_test_flyer.pdf` stay as fallbacks.

Plus 135 blank note cards and 135 envelopes, both written by hand.

`out/letters_to_copy.pdf` and `out/letters_to_copy_flyer.pdf` are not mailed.
They are the working stack she writes from, 135 pages, plain office paper,
single sided.

---

## What it actually costs

193 color sides, not 135 prints, because the mailer is duplex. Printing at home
the cash cost is ink or toner rather than a per-side price, so the ink note
under Specification matters more than any table of vendor rates.

Envelopes, blank cards and 135 stamps put the campaign somewhere around $200 to
$300 all in. Check the current first-class rate rather than trusting a number
from here.

**Do not optimize this line.** One four-house farm converting is a $315,000
project. An afternoon spent shaving print cost is the worst paid work available
in this campaign.

## Specification

**Printing at home**

The Canva pieces bleed to the paper edge and no home printer can put ink there.
It holds back about 0.17in on the sides and often more at the foot, rarely
equally on all four, so a full-bleed page comes back framed in a lopsided white
sliver that reads as a misprint.

Use the files in `out/home_print/`. Same designs, scaled to 0.941 and centred
inside a 0.25in safe margin, so the white frame is even and reads as a border.
Regenerate after any new export:

    python scripts/prep_home_print.py path/to/design.pdf

**Print at 100%, not "fit to page".** The driver would shrink an already-shrunk
page again and the margin would stop being even.

**Two things a home printer does to these that a commercial one would not**

- *Ink.* The review sheet is 35% dark coverage, the mailer front 19%, the back
  13%. On an inkjet, 77 sheets of near-solid navy is slow and genuinely
  expensive, and cartridges empty faster than the page count suggests. A laser
  handles it far better. On an inkjet, print ten, look at the cartridge, and
  decide before committing to the rest.
- *Banding.* Large solid navy is where a tired printer shows itself first. Check
  a proof for streaks across the dark field before running the lot.

**Resolution, worth fixing at source**

The pages are flattened images rather than live type, so what was exported is
what prints:

| page | pixels | effective |
|---|---|---|
| Review sheet | 2550 x 3300 | 300 DPI, good |
| Mailer front | 1530 x 1980 | 180 DPI, slightly soft |
| Mailer back | 1086 x 1448 | **128 DPI, visibly soft** |

The mailer back carries every figure, and 128 DPI is where small type starts to
look furry on paper. Re-export that page at 300 DPI before running 58 of them.
Nothing else needs redoing.

**Both pieces**

- 8.5 x 11 in, portrait.
- 28lb or 32lb text weight, uncoated, white or natural. Not gloss. Gloss reads
  as an advertisement, which is the register the whole piece is trying to avoid.
- The mailer prints **duplex, flip on long edge**. Front is how we work, back is
  the numbers. Printed as two loose sheets it stops making sense.

**Note cards**

- 135 blank cards, roughly 4 x 6 in, same white as the sheet if you can match it.
- Flat correspondence cards, not folded. The note is about 55 words and a
  fold-over card leaves three empty faces, which reads as a card that ran out of
  things to say.

**Envelopes**

- 135 #10 (4.125 x 9.5 in). Takes the sheet folded in thirds with the card
  alongside.
- Blank. Not window, not pre-printed with the logo. A logo on the envelope
  turns a handwritten letter back into direct mail before it is opened.
- Hand-address them, including the return address. It is on every copy sheet
  and on the worklist page, and it goes without the suite line:

      Cleaner Greener Future
      8595 College Blvd
      Overland Park, KS 66210
- **Real stamps, not a meter.** Metered postage on a hand-addressed envelope is
  the single detail that gives the whole thing away.

---

## Two things to get right

**Returned mail is data, not waste.** The addresses come from co-op billing
records of unknown vintage. Anything that comes back is a bad record, and
knowing which is worth more than the stamp. That is the reason for the return
address.

**Print a proof of each piece and read it on paper before running the lot.** Colour
sits differently on uncoated stock than on screen, and the photographs on both
pieces are the part most likely to disappoint. Check the arrays still read as
arrays and are not a dark smear.
