# Handwritten note

Goes in the envelope with whichever printed piece the farm is getting. Written
to be copied by hand 165 times, so it is short on purpose.

**The note is held constant across both test cells.** The broiler farms get the
two-page mailer and the layer, pullet and breeder farms get the Ogilvy-register
flyer, and the only thing that varies between them is that printed piece. Send
the note to one cell and not the other and the note becomes a second variable,
which makes the flyer result unreadable.

You do not write these from this file. `python scripts/build_letters.py broiler`
and `... flyer` produce one page per farm with the name, the number and the
envelope address already filled in.

**Solar is not mentioned.** It is the fifth thing we do and the example on the
back of the sheet, not the reason for the envelope. A handwritten note that opens
with solar is a solar note, and it tells him we are an equipment company before
he has read a word about what we actually do.

---

## Standard

> Hi [Name],
>
> A [N]-house farm around here runs about [X] kWh a year. Most of that is fans.
>
> I read power bills for a living. Rate class, meter multipliers, demand
> charges, sales tax. Send 12 months of yours to info@cgf.solutions and I
> will tell you what I find. No charge, no obligation.
>
> The sheet explains the rest.
>
> Clint

### Fill values for [X]

Round to the nearest 10,000, because these are medians standing in for his farm
rather than measurements of it. A segment with fewer than ten farms gets no
number at all and takes the second version below.

| cell | segment | farms | [X] |
|---|---|---|---|
| broiler | 3 houses | 10 | 230,000 |
| broiler | 4 houses | 48 | 250,000 |
| broiler | 5 or 6 houses | 18 | 330,000 |
| flyer | egg, 1 house | 66 | 110,000 |

"Most of that is fans" stays on the broiler letters only. Ventilation is about
88% of a broiler house's load and there is a source for that. Layer and pullet
houses carry lighting, belts and augers on top of ventilation, and there is no
split here worth standing behind, so those letters leave the sentence out.

---

## Segments too thin to quote (23 farms across both cells)

Three two-house broiler farms, and twenty layer, pullet and breeder farms whose
segment holds fewer than ten. One of the two-house broilers has a bad house
count in the co-op data. Open on the bill instead of on a number.

> Hi [Name],
>
> I read power bills for a living. Rate class, meter multipliers, demand
> charges, sales tax. On a poultry farm they are worth reading.
>
> Send 12 months of yours to info@cgf.solutions and I will tell you what I
> find. No charge, no obligation.
>
> The sheet explains the rest.
>
> Clint

---

## Why it is written this way

It opens with a number about his farm because that is the fastest way to show we
did work before asking for anything. "Most of that is fans" is the second
signal: it says we know poultry, in four words, without a paragraph about our
experience.

Then one ask, and it is the cheapest one we have. Twelve months of billing costs
him an email and can end with us telling him there is nothing here.

No solar, no savings figure, no deadline. Those are on the sheet, where a
grower who wants them will find them.
