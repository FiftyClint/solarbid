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
import json
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
const ROWS = __ROWS__;
const KEY = 'cgf-worklist-v1';
let done = {};
let storageOK = true;
try { done = JSON.parse(localStorage.getItem(KEY) || '{}'); }
catch (e) { storageOK = false; }

function save() {
  if (!storageOK) return;
  try { localStorage.setItem(KEY, JSON.stringify(done)); }
  catch (e) { storageOK = false; showWarn(); }
}
function showWarn() {
  if (document.getElementById('warn')) return;
  const d = document.createElement('div');
  d.id = 'warn'; d.className = 'warn';
  d.textContent = 'This browser will not save your checkmarks between visits. '
    + 'Keep this tab open, or ask Clint to put it online instead.';
  document.body.insertBefore(d, document.body.firstChild);
}
if (!storageOK) showWarn();

let filter = 'todo', query = '';

function matches(r) {
  if (filter === 'todo' && done[r.id]) return false;
  if (filter === 'broiler' && r.cell !== 'broiler') return false;
  if (filter === 'flyer' && r.cell !== 'flyer') return false;
  if (filter === 'flagged' && !r.flagged) return false;
  if (!query) return true;
  const hay = (r.name + ' ' + r.address.join(' ')).toLowerCase();
  return hay.includes(query);
}

function render() {
  const main = document.getElementById('list');
  const shown = ROWS.filter(matches);
  main.innerHTML = shown.length ? '' : '<p class="empty">Nothing here. '
    + 'Try another filter.</p>';
  for (const r of shown) {
    const card = document.createElement('div');
    card.className = 'card ' + r.cell + (done[r.id] ? ' done' : '');
    card.innerHTML = `
      <div class="top">
        <input class="chk" type="checkbox" ${done[r.id] ? 'checked' : ''}
               aria-label="Mark ${r.name} done">
        <div class="who">
          <h2>${r.name}</h2>
          <span class="tag piece ${r.cell === 'flyer' ? 'flyer' : ''}">${r.piece}</span>
          <span class="tag">${r.pieceNote}</span>
          <span class="num">${r.houses} house${r.houses === 1 ? '' : 's'}</span>
        </div>
      </div>
      ${r.flagged ? `<div class="flag">Check this name first. The co-op file
        says: ${r.rawName}</div>` : ''}
      <div class="body">
        <div class="block"><b>Envelope</b>
          <div class="addr">${r.address.join('<br>')}</div></div>
        <div class="block"><b>Write this note</b>
          <div class="note">${r.note.map(p => '<p>' + p + '</p>').join('')}</div></div>
      </div>`;
    card.querySelector('.chk').addEventListener('change', (e) => {
      if (e.target.checked) done[r.id] = 1; else delete done[r.id];
      save(); card.classList.toggle('done', !!done[r.id]); updateCount();
      if (filter === 'todo' && done[r.id]) setTimeout(render, 220);
    });
    main.appendChild(card);
  }
  updateCount();
}

function updateCount() {
  const n = ROWS.filter(r => done[r.id]).length;
  document.getElementById('count').textContent =
    n + ' of ' + ROWS.length + ' done, ' + (ROWS.length - n) + ' to go';
  document.getElementById('fill').style.width = (n / ROWS.length * 100) + '%';
}

document.querySelectorAll('[data-filter]').forEach(b => {
  b.addEventListener('click', () => {
    filter = b.dataset.filter;
    document.querySelectorAll('[data-filter]').forEach(x =>
      x.classList.toggle('on', x === b));
    render();
  });
});
document.getElementById('q').addEventListener('input', e => {
  query = e.target.value.trim().toLowerCase(); render();
});
render();
"""


def main() -> int:
    rows = build_rows()
    OUT.parent.mkdir(exist_ok=True)

    ret = "<br>".join(html.escape(l) for l in RETURN_ADDRESS)
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Mailing list</title><style>{STYLE}</style></head>
<body>
<header>
  <div class="bar">
    <div class="grow">
      <h1>Poultry mailing, {len(rows)} letters</h1>
      <div class="count" id="count"></div>
      <div class="track"><div class="fill" id="fill"></div></div>
    </div>
    <div class="ret"><b>Return address, every envelope</b>{ret}</div>
  </div>
  <div class="tools">
    <input id="q" type="search" placeholder="Find a name or a town">
    <button data-filter="todo" class="on">To do</button>
    <button data-filter="all">All</button>
    <button data-filter="broiler">Mailer only</button>
    <button data-filter="flyer">Flyer only</button>
    <button data-filter="flagged">Name to check</button>
  </div>
</header>
<main id="list"></main>
<script>{SCRIPT.replace('__ROWS__', json.dumps(rows))}</script>
</body></html>"""

    OUT.write_text(page, encoding="utf-8")
    flagged = sum(1 for r in rows if r["flagged"])
    print(f"wrote {OUT}: {len(rows)} farms "
          f"({sum(1 for r in rows if r['cell'] == 'broiler')} mailer, "
          f"{sum(1 for r in rows if r['cell'] == 'flyer')} flyer)")
    print(f"names flagged for Clint: {flagged}")
    print("Holds customer names and addresses. out/ is gitignored.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
