# Image-generator prompts for the flyer

## Read this first

**No generator renders this flyer.** It carries roughly 200 words and six exact
figures. Every model still garbles text at that density, and the one thing that
cannot be wrong here is a number. Use these to make *art*, then set the type in
Canva, InDesign, or the Python build. Never retype a figure off a generated
image.

**One hard line.** Do not generate a photograph of a poultry farm or a solar
install and let it sit on the page as though it were a CGF job. The mailer's
whole argument is that we did real work on real farms; a synthetic customer
photo passed off as ours poisons that, and a grower who half-recognizes the
place will know. Generated texture, abstraction and obvious illustration are
fine. Generated evidence is not.

The palette, everywhere: navy `#10243A`, bright green `#52FB2A` as accent only,
paper `#FCFDFD`, mid blue `#155DAE`.

---

## 1. Hero band, abstract

The flyer currently has no image because the only photographs on hand are solar
arrays, which argue against a bill-analysis offer. This fills that hole without
changing the subject.

> An abstract graphic band for the top of a print flyer, 3:1 landscape. Deep
> navy field, near-black. Across it, a faint grid of thin horizontal rules and
> aligned numeric columns, like an electricity bill or a ledger seen from far
> away and slightly out of focus. One single row picked out in bright acid
> green, glowing very slightly, as though someone has run a highlighter across
> one line of a statement. Extremely minimal, mostly empty navy, no readable
> text, no icons, no logos, no people, no gradients beyond a subtle vignette.
> Flat editorial print design, high contrast, generous negative space. Colours:
> #10243A navy, #52FB2A green.

Ask for it wide and crop down. The point is the one green line: it is the
"somebody finally read this" idea, with no photograph required.

---

## 2. Full-page direction study

For deciding a look, not for printing. Expect the text to come out as nonsense.

> A single-page 8.5x11 portrait direct-mail flyer, modern editorial print
> design, 2025. Top third is a solid deep navy block containing a very large
> two-line headline in a bold modern grotesque, the second line in bright acid
> green. Lower two thirds white, holding a small section heading and four
> numbered items separated by thin hairline rules, each item a short bold title
> above two lines of small body copy, numerals set in small monospace. A thick
> bright green horizontal rule near the bottom, then a closing statement and a
> small footer. Left-aligned throughout, ragged right, generous white space, no
> boxes, no drop shadows, no icons, no illustrations, no photographs. Colours:
> #10243A, #52FB2A, #FCFDFD. Style of a well-designed contemporary annual report
> or a Pentagram print piece, not a small-business clip-art flyer.

Add "text is placeholder, legibility not required" if the model keeps trying to
spell.

---

## 3. The photograph we actually lack

Only if it is clearly a made image, and captioned as an illustration. Better
still, send someone to take the real one.

> Wide landscape photograph, 3:1, of long low poultry houses on flat farmland at
> dusk in late autumn, northeast Arkansas. Corrugated metal roofs, ventilation
> fans in the end walls, gravel track, bare fields, a line of trees on the
> horizon. Overcast blue hour light, no sun flare, no drama. Documentary, plain,
> slightly cool colour. No people, no vehicles, no solar panels, no text or
> watermarks. Shot on a 35mm lens, deep focus, slightly desaturated.

If it goes in, caption it as an illustration. It cannot imply a customer.

---

## 4. The subject itself

The most honest image on a page about bills is a bill.

> Extreme close crop of a paper utility statement lying on a worn wooden table,
> shot from directly above. Only part of the sheet in frame, rows of small
> figures running off the edges, the paper slightly creased. One line marked
> with a single stroke of bright green highlighter. Cool overcast daylight from
> one side, soft shadow. Plain documentary photography, no hands, no branding,
> no readable company name, no logos. Muted colour, fine paper texture.

Nothing on this sheet has to be legible, so the model's text problem stops
mattering. Best fit of the four for a piece about reading a bill.

---

## Getting a usable file back

Ask for 300 DPI or at least 2550x3300 for a full page, 2550x850 for a band.
Most generators return 1024px and it will look soft on paper. Upscale, or use
the image as a band rather than a full bleed where the softness shows less.

Then set the type over it properly. Every figure on the page comes from
`scripts/segment_table.py` and `out/mail_list*.csv`, not from a picture.
