#!/usr/bin/env python3
"""Kristen's worklist: one scrollable page, 165 farms, checked off as they go.

A PDF is the wrong shape for this job. She is working through a queue on a
laptop over several sittings, so the page needs to remember where she got to,
let her find a farm by name, and hide the ones already done.

Everything she needs for one envelope sits in one card: who it goes to, the
address laid out the way it is written, which printed piece goes in, and the
note copy with the name and the number already filled in. Nothing to look up
and nothing to work out.

    python scripts/build_worklist.py

Writes out/kristen_worklist.html, self-contained, no network. It carries
customer names and addresses, so it stays in out/, which is gitignored.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd  # noqa: E402

from build_letters import (  # noqa: E402
    classify, letter_text, split_care_of, title_case_address,
)

# As Clint gave it. brand.py carries "Suite 150L" as well; confirm which one
# belongs on the envelope before she writes 165 of them.
RETURN_ADDRESS = ["Cleaner Greener Future", "8595 College Blvd",
                  "Overland Park, KS 66210"]

CELLS = [
    ("broiler", Path("out/mail_list.csv"), "Mailer", "2-page sheet, front and back"),
    ("flyer", Path("out/mail_list_flyer.csv"), "Flyer", "1-page flyer"),
]

OUT = Path("out/kristen_worklist.html")


def build_rows() -> list[dict]:
    rows = []
    for cell, path, piece, piece_note in CELLS:
        if not path.exists():
            print(f"ERROR: {path} not found. Run scripts/mail_list.py first.",
                  file=sys.stderr)
            raise SystemExit(1)
        df = pd.read_csv(path)
        df = df.sort_values("annualized_kwh", ascending=False)
        for _, r in df.iterrows():
            salutation, status = classify(r["name"])
            address = [title_case_address(r["name"])]
            address += [title_case_address(l)
                        for l in split_care_of(r["mail_address"])]
            address.append(f"{title_case_address(r['city'])}, "
                           f"{str(r['state']).strip().upper()} "
                           f"{str(r['zip_code']).strip()}")
            rows.append({
                "id": f"{cell}-{len(rows)}",
                "cell": cell,
                "piece": piece,
                "pieceNote": piece_note,
                "name": title_case_address(r["name"]),
                "address": address,
                "note": letter_text(salutation, r),
                "flagged": status == "unknown",
                "rawName": str(r["name"]),
                "houses": int(r["houses"]),
                "state": str(r["state"]).strip().upper(),
            })
    return rows


STYLE = """
*{box-sizing:border-box}
:root{
  --ink:#10243A; --mute:#5C7387; --paper:#FCFDFD; --panel:#EEF4FA;
  --rule:#D8E3ED; --brand:#155DAE; --flag:#B3261E; --done:#3F8A4B;
}
@media (prefers-color-scheme: dark){
  :root{--ink:#E8EEF4; --mute:#9BB0C2; --paper:#101A24; --panel:#182634;
        --rule:#2A3B4D; --brand:#6BA6E8; --flag:#F2857D; --done:#7BC98A}
}
html{scroll-behavior:smooth}
body{margin:0;background:var(--paper);color:var(--ink);
  font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
header{position:sticky;top:0;z-index:10;background:var(--paper);
  border-bottom:2px solid var(--ink);padding:14px 20px 12px}
.bar{display:flex;flex-wrap:wrap;gap:16px;align-items:flex-start;
  max-width:900px;margin:0 auto}
.ret{background:var(--panel);border-radius:8px;padding:10px 14px;line-height:1.4}
.ret b{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--mute);margin-bottom:4px}
.grow{flex:1;min-width:220px}
h1{font-size:19px;margin:0 0 4px}
.count{font-variant-numeric:tabular-nums;color:var(--mute);font-size:14px}
.track{height:7px;border-radius:4px;background:var(--rule);margin-top:8px;overflow:hidden}
.fill{height:100%;background:var(--done);width:0;transition:width .2s}
.tools{display:flex;flex-wrap:wrap;gap:8px;max-width:900px;margin:12px auto 0}
/* A class selector beats the UA rule for [hidden], so say it explicitly.
   Without scripting these controls do nothing and must not be offered. */
.tools[hidden],.card[hidden],.empty[hidden]{display:none}
input[type=search]{flex:1;min-width:170px;padding:8px 12px;font-size:15px;
  border:1px solid var(--rule);border-radius:7px;background:var(--paper);color:var(--ink)}
button{padding:8px 13px;font-size:14px;border:1px solid var(--rule);border-radius:7px;
  background:var(--paper);color:var(--ink);cursor:pointer}
button.on{background:var(--brand);border-color:var(--brand);color:#fff}
main{max-width:900px;margin:0 auto;padding:18px 20px 80px}
.card{border:1px solid var(--rule);border-left:5px solid var(--brand);
  border-radius:9px;padding:14px 16px;margin-bottom:12px;background:var(--paper)}
.card.flyer{border-left-color:#7A5CC4}
.card.done{opacity:.42}
.card.done .body{display:none}
.top{display:flex;gap:13px;align-items:flex-start}
.chk{appearance:none;flex:none;width:27px;height:27px;margin:1px 0 0;
  border:2px solid var(--mute);border-radius:6px;cursor:pointer;background:var(--paper)}
.chk:checked{background:var(--done);border-color:var(--done)}
.chk:checked::after{content:"";display:block;width:7px;height:14px;margin:2px auto 0;
  border:solid #fff;border-width:0 3px 3px 0;transform:rotate(42deg)}
.who{flex:1;min-width:0}
.who h2{font-size:17px;margin:0 0 2px;font-weight:650}
.tag{display:inline-block;font-size:11px;letter-spacing:.05em;text-transform:uppercase;
  padding:3px 8px;border-radius:99px;background:var(--panel);color:var(--mute);margin-right:6px}
.tag.piece{background:var(--brand);color:#fff}
.tag.piece.flyer{background:#7A5CC4}
.num{color:var(--mute);font-size:13px;font-variant-numeric:tabular-nums}
.body{margin:13px 0 0 40px;display:grid;gap:13px;grid-template-columns:minmax(190px,1fr) 2fr}
@media(max-width:680px){.body{grid-template-columns:1fr;margin-left:0}}
.block b{display:block;font-size:11px;letter-spacing:.08em;text-transform:uppercase;
  color:var(--mute);margin-bottom:5px}
.addr{background:var(--panel);border-radius:8px;padding:11px 13px;
  font-size:16px;line-height:1.5}
.note{background:var(--panel);border-radius:8px;padding:12px 15px;
  font-family:Georgia,"Times New Roman",serif;font-size:16px;line-height:1.62}
.note p{margin:0 0 9px}.note p:last-child{margin:0}
.flag{margin:9px 0 0 40px;color:var(--flag);font-size:14px;font-weight:600}
@media(max-width:680px){.flag{margin-left:0}}
.empty{text-align:center;color:var(--mute);padding:50px 0}
.warn{background:#FFF3CD;color:#6B4E00;padding:9px 14px;font-size:14px;text-align:center}
@media print{header{position:static}.tools,.chk,button{display:none}
  .card{break-inside:avoid}.card.done .body{display:grid}}
"""

SCRIPT = """
// The cards are already in the HTML. This only adds the conveniences: saved
// checkmarks, filtering and the counter. With scripting off the whole list is
// still readable and every checkbox still ticks, which is what matters.
const KEY = 'cgf-worklist-v1';
const cards = Array.from(document.querySelectorAll('.card'));
let done = {}, storageOK = true;
try { done = JSON.parse(localStorage.getItem(KEY) || '{}'); }
catch (e) { storageOK = false; }

function save() {
  if (!storageOK) return;
  try { localStorage.setItem(KEY, JSON.stringify(done)); }
  catch (e) { storageOK = false; warn(); }
}
function warn() {
  if (document.getElementById('warn')) return;
  const d = document.createElement('div');
  d.id = 'warn'; d.className = 'warn';
  d.textContent = 'This browser will not remember your checkmarks after you '
    + 'close the page. Keep this tab open, or ask Clint to put it online.';
  document.body.insertBefore(d, document.body.firstChild);
}
if (!storageOK) warn();

let filter = 'todo', query = '';

function apply() {
  let shown = 0;
  for (const c of cards) {
    const isDone = !!done[c.dataset.id];
    c.classList.toggle('done', isDone);
    let ok = true;
    if (filter === 'todo' && isDone) ok = false;
    if (filter === 'broiler' && c.dataset.cell !== 'broiler') ok = false;
    if (filter === 'flyer' && c.dataset.cell !== 'flyer') ok = false;
    if (filter === 'flagged' && c.dataset.flagged !== '1') ok = false;
    if (ok && query && !c.dataset.search.includes(query)) ok = false;
    c.hidden = !ok;
    if (ok) shown++;
  }
  document.getElementById('none').hidden = shown > 0;
  const n = cards.filter(c => done[c.dataset.id]).length;
  document.getElementById('count').textContent =
    n + ' of ' + cards.length + ' done, ' + (cards.length - n) + ' to go';
  document.getElementById('fill').style.width = (n / cards.length * 100) + '%';
}

for (const c of cards) {
  const box = c.querySelector('.chk');
  box.checked = !!done[c.dataset.id];
  box.addEventListener('change', () => {
    if (box.checked) done[c.dataset.id] = 1; else delete done[c.dataset.id];
    save();
    c.classList.toggle('done', box.checked);
    if (filter === 'todo' && box.checked) setTimeout(apply, 220); else apply();
  });
}
document.querySelectorAll('[data-filter]').forEach(b => {
  b.addEventListener('click', () => {
    filter = b.dataset.filter;
    document.querySelectorAll('[data-filter]').forEach(x =>
      x.classList.toggle('on', x === b));
    apply();
  });
});
document.getElementById('q').addEventListener('input', e => {
  query = e.target.value.trim().toLowerCase(); apply();
});
document.getElementById('tools').hidden = false;
apply();
"""


def card_html(r: dict) -> str:
    e = html.escape
    search = e((r["name"] + " " + " ".join(r["address"])).lower(), quote=True)
    flag = (f'<div class="flag">Check this name first. The co-op file says: '
            f'{e(r["rawName"])}</div>') if r["flagged"] else ""
    note = "".join(f"<p>{e(p)}</p>" for p in r["note"])
    addr = "<br>".join(e(l) for l in r["address"])
    houses = f'{r["houses"]} house' + ("" if r["houses"] == 1 else "s")
    return f"""<article class="card {r['cell']}" data-id="{e(r['id'])}"
   data-cell="{r['cell']}" data-flagged="{'1' if r['flagged'] else '0'}"
   data-search="{search}">
  <div class="top">
    <input class="chk" type="checkbox" aria-label="Mark {e(r['name'])} done">
    <div class="who">
      <h2>{e(r['name'])}</h2>
      <span class="tag piece {'flyer' if r['cell'] == 'flyer' else ''}">{e(r['piece'])}</span>
      <span class="tag">{e(r['pieceNote'])}</span>
      <span class="num">{houses}</span>
    </div>
  </div>
  {flag}
  <div class="body">
    <div class="block"><b>Envelope</b><div class="addr">{addr}</div></div>
    <div class="block"><b>Write this note</b><div class="note">{note}</div></div>
  </div>
</article>"""


def main() -> int:
    rows = build_rows()
    OUT.parent.mkdir(exist_ok=True)

    ret = "<br>".join(html.escape(l) for l in RETURN_ADDRESS)
    cards = "\n".join(card_html(r) for r in rows)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mailing list</title><style>{STYLE}</style></head>
<body>
<header>
  <div class="bar">
    <div class="grow">
      <h1>Poultry mailing, {len(rows)} letters</h1>
      <div class="count" id="count">{len(rows)} to write</div>
      <div class="track"><div class="fill" id="fill"></div></div>
    </div>
    <div class="ret"><b>Return address, every envelope</b>{ret}</div>
  </div>
  <div class="tools" id="tools" hidden>
    <input id="q" type="search" placeholder="Find a name or a town">
    <button data-filter="todo" class="on">To do</button>
    <button data-filter="all">All</button>
    <button data-filter="broiler">Mailer only</button>
    <button data-filter="flyer">Flyer only</button>
    <button data-filter="flagged">Name to check</button>
  </div>
</header>
<main id="list">
{cards}
<p class="empty" id="none" hidden>Nothing here. Try another filter.</p>
</main>
<script>{SCRIPT}</script>
</body></html>"""

    OUT.write_text(page, encoding="utf-8")
    flagged = sum(1 for r in rows if r["flagged"])
    print(f"wrote {OUT}: {len(rows)} envelopes "
          f"({sum(1 for r in rows if r['cell'] == 'broiler')} mailer, "
          f"{sum(1 for r in rows if r['cell'] == 'flyer')} flyer)")
    print(f"names flagged for Clint: {flagged}")
    print("Holds customer names and addresses. out/ is gitignored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
