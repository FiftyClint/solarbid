# Print and mail spec

What to hand a printer, and what to buy. 135 envelopes total, in two cells.
That is one envelope per recipient, not per farm: 165 farms belong to 135
people, and 25 of them own more than one.

| cell | envelopes | printed piece | pages | sheets |
|---|---|---|---|---|
| broiler | 58 | `out/cgf_mailer.pdf` | 2, duplex | 58 |
| flyer | 77 | `out/cgf_test_flyer.pdf` | 1, single side | 77 |

Plus 135 blank note cards and 135 envelopes, both written by hand.

`out/letters_to_copy.pdf` and `out/letters_to_copy_flyer.pdf` are not mailed.
They are the working stack she writes from, 135 pages, plain office paper,
single sided.

---

## What it actually costs

The job is 193 color sides, not 135 prints. The mailer is duplex, so each
broiler sheet is two.

| | per side | total |
|---|---|---|
| retail counter (FedEx, Staples, UPS Store) | $1.00 | $193 |
| retail, negotiated at volume | $0.60 | $116 |
| online short run, 3 to 7 days | ~$0.35 | ~$68 |
| in-house colour laser, consumables only | ~$0.10 | ~$19 |

Add envelopes, blank cards and 135 stamps, and the whole campaign lands
somewhere between $200 and $350 depending on which row you pick. Check the
current first-class rate rather than trusting a number from here.

## Recommendation

**Both pieces are static.** Every broiler mailer is identical to every other
broiler mailer, and every flyer is identical to every other flyer. All the
personalization is in the handwriting. That matters because it is exactly the
job short-run printing is cheap at: two SKUs, no variable data, no proofs per
record.

So: **if there is a colour laser in the Overland Park office, run it there.**
About $24 of toner, and a reprint after the flyer test is an afternoon.

If there is not, **order both pieces from an online short-run printer**, not
from the counter. The counter is the $244 option and it buys nothing here except
same-day, which this campaign does not need. Handwriting 135 letters is the long
pole, not printing.

**Do not optimize this line.** The spread between the cheapest and most
expensive route is about $175 across 135 growers. One four-house farm converting
is a $315,000 project. Spending an afternoon shaving print cost is the worst
paid work available in this campaign. Pick a route, order the good stock, and
put the time into the letters.

## Specification

**Both printed pieces**

- 8.5 x 11 in, portrait, no bleed.
- The mailer holds all content inside a 0.64 in margin, so there is nothing to
  trim and nothing to lose at the edge.
- The flyer runs a navy field and a photograph nearly full width. They stop
  0.29 in short of the paper edge on purpose, because an office laser cannot
  print to the edge and leaves an uneven white strip that reads as a misprint.
  Print it at 100%, not "fit to page", or that margin grows and the balance
  goes with it. Going to a commercial printer that takes real bleed? Set
  BLEED = True at the top of scripts/build_test_flyer.py and re-run.
- Full color. Both carry photographs and the blue is load-bearing. The flyer
  also lays a large solid navy across the top: check the proof for banding, as
  heavy solid coverage is where a tired laser shows itself first.
- 28lb or 32lb text weight, uncoated, white or natural. Not gloss. Gloss reads
  as an advertisement, which is the register the whole piece is trying to avoid.
- The mailer prints **duplex, flip on long edge**. Page 1 is how we work,
  page 2 is the solar example, and the copy on page 1 says "the back of this
  page." Printed as two loose sheets it stops making sense.

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
