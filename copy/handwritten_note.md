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
> [N] houses run about [X] kWh a year. At 11 cents that is around [$Y].
>
> I know that because I went through a year of usage on 176 farms around here.
> What I cannot see is whether you are billed right for it, or whether there are
> other ways to cut what you spend. Send 12 months of your bills to
> info@cgf.solutions and I will tell you what I find. No charge.
>
> More in the sheet if you want it.
>
> Clint

House count is spelled out, because the sentence opens on it and a numeral at
the head of a handwritten line reads like a form. Single-house layer farms open
"A single egg house runs about..." instead.

### Fill values

kWh rounded to the nearest 10,000 and dollars to the nearest 1,000, at 11 cents.
Both are medians standing in for his farm rather than measurements of it. A
segment with fewer than ten farms gets neither and takes the version below.

| cell | segment | farms | [X] | [$Y] |
|---|---|---|---|---|
| broiler | 3 houses | 10 | 230,000 | $25,000 |
| broiler | 4 houses | 48 | 250,000 | $28,000 |
| broiler | 5 or 6 houses | 18 | 330,000 | $36,000 |
| flyer | egg, 1 house | 66 | 110,000 | $12,000 |

---

## Segments too thin to quote (23 farms across both cells)

Three two-house broiler farms, and twenty layer, pullet and breeder farms whose
segment holds fewer than ten. No median, so no money line to open on.

> I went through a year of power usage on 176 poultry farms around Randolph and
> Clay counties. Yours is one I could not get a clean read on.
>
> What I cannot see is whether you are billed right for it, or whether there are
> other ways to cut what you spend. ...

---

## Why it is written this way

**Money leads, because that is what he feels.** 250,000 kWh is a number he has
to translate. $28,000 is a number he already resents. Same fact, and the earlier
draft made him do the arithmetic himself.

**Provenance follows in the same breath.** "I know that because I went through a
year of usage on 176 farms around here" answers the question he asks the moment
he reads his own figure, and it fixes what the personalization breaks: 48 of the
broiler farms are four-house and every one gets $28,000. Two neighbours
comparing letters now see exactly what the letter says it is.

**The limit is what earns the ask.** We know what his farm draws. We cannot see
whether he is billed right for it, or whether there is a cheaper way to run it.
His bills are the only thing that closes that gap, which is the honest reason to
ask for them rather than for his attention.

**It does not repeat the sheet.** No solar, no savings figure, no deadline, no
services list. "More in the sheet if you want it" hands the rest off and gives
him permission to ignore it.

**What is deliberately not in it.** An earlier draft said the power bill comes
out of the grower's settlement rather than the integrator's. That is probably
true and it would be the strongest line here, but it is not verified, and the
one sentence a grower could catch us out on is not the one to guess at.
