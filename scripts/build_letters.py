#!/usr/bin/env python3
"""Copy sheets: one page per farm, letter filled in, envelope address below.

These are working pages, not a mailed piece. Someone sits with the stack and
writes each letter out by hand, then addresses the envelope from the same page.
So it is set large, one farm to a page, with nothing to interpret and nothing to
look up.

Names come out of a co-op billing file in the order GIVEN MIDDLE SURNAME, all
caps, and about 40% of them are businesses rather than people. A wrong first
name in handwriting is worse than no first name, so anything the parser cannot
resolve confidently is marked CHECK THIS NAME on the page rather than guessed.

    python scripts/build_letters.py

Writes out/letters_to_copy.pdf. Personal data, so it stays in out/, which is
gitignored.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

from brand import (  # noqa: E402
    ADDRESS, BRAND, EMAIL, Flow, INK, L, MUTE, PAGE_H, PAGE_W, PANEL, PAPER,
    R, RULE_C,
)

HEAD = "Work Sans"
SERIF = "IBM Plex Serif"
MONO = "Geist Mono"

MAIL_LIST = Path("out/mail_list.csv")
OUT = Path("out/letters_to_copy.pdf")

# Round figures, matching copy/handwritten_note.md.
KWH_BY_ROW = {"3 houses": "230,000", "4 houses": "250,000",
              "5-6 houses": "330,000"}

# Positive evidence, not absence of evidence. An earlier version greeted a farm
# called AR ORIGINS as "Hi Ar," because ORIGINS was not on a business-word list.
# No list of business words is ever complete, so the test is inverted: a token
# must be a recognizable given name to be used, and everything else is flagged
# for a human. Common US given names, which in this county skew traditional.
GIVEN_NAMES = set("""
JAMES JOHN ROBERT MICHAEL WILLIAM DAVID RICHARD JOSEPH THOMAS CHARLES
CHRISTOPHER DANIEL MATTHEW ANTHONY DONALD MARK PAUL STEVEN ANDREW KENNETH
GEORGE JOSHUA KEVIN BRIAN EDWARD RONALD TIMOTHY JASON JEFFREY RYAN JACOB GARY
NICHOLAS ERIC JONATHAN STEPHEN LARRY JUSTIN SCOTT BRANDON BENJAMIN SAMUEL
GREGORY FRANK ALEXANDER RAYMOND PATRICK JACK DENNIS JERRY TYLER AARON JOSE
ADAM NATHAN HENRY ZACHARY DOUGLAS PETER KYLE WALTER ETHAN JEREMY HAROLD KEITH
CHRISTIAN ROGER NOAH GERALD CARL TERRY SEAN AUSTIN ARTHUR LAWRENCE JESSE DYLAN
BRYAN JOE JORDAN BILLY BRUCE ALBERT WILLIE GABRIEL LOGAN ALAN JUAN WAYNE RALPH
RANDY EUGENE VINCENT RUSSELL ELMER LOUIS BOBBY PHILIP JOHNNY CLARENCE ERNEST
CLIFFORD LEROY LEONARD MARVIN GLENN HOWARD FLOYD CECIL EARL CLYDE CHESTER
LESTER DALE DEAN DARRELL DUANE DWIGHT MELVIN MERLE ORVILLE OTIS VERNON VIRGIL
WENDELL WILBUR WOODROW HERMAN HOMER HORACE HUBERT LLOYD LUTHER MARION MAURICE
MILTON MORRIS MURRAY NORMAN OSCAR PERCY PRESTON RUFUS SAMMY SHELBY SIDNEY
STANLEY THEODORE TROY TRUMAN VICTOR WADE WALLACE WARREN WESLEY WILBERT WINSTON
BUDDY DONNIE JIMMY TOMMY RICKY DANNY RANDALL RODNEY GERALD DARREL JERRELL
KENNY LONNIE MARTY MICKEY RUSTY SONNY TERRELL TRAVIS TREVOR TYRONE
MARY PATRICIA JENNIFER LINDA ELIZABETH BARBARA SUSAN JESSICA SARAH KAREN NANCY
LISA MARGARET BETTY SANDRA ASHLEY DOROTHY KIMBERLY EMILY DONNA MICHELLE CAROL
AMANDA MELISSA DEBORAH STEPHANIE REBECCA LAURA SHARON CYNTHIA KATHLEEN AMY
SHIRLEY ANGELA HELEN ANNA BRENDA PAMELA NICOLE RUTH KATHERINE SAMANTHA
CHRISTINE CATHERINE VIRGINIA DEBRA RACHEL JANET EMMA CAROLYN MARIA HEATHER
DIANE JULIE JOYCE VICTORIA KELLY CHRISTINA JOAN EVELYN LAUREN JUDITH MEGAN
CHERYL ANDREA HANNAH MARTHA JACQUELINE FRANCES GLORIA ANN TERESA KATHRYN SARA
JANICE JEAN ALICE MADISON DORIS ABIGAIL JULIA JUDY GRACE DENISE MARILYN AMBER
BEVERLY DANIELLE THERESA DIANA BRITTANY NATALIE ROSE RACHAEL LORI TIFFANY
KAYLA ALEXIS MARIE CONNIE PEGGY WANDA BONNIE JUANITA LOIS NORMA PAULA ROBERTA
SHELIA SHERRY STELLA VELMA VERA VIOLA WILMA BERTHA BEULAH EDNA ETHEL FLORENCE
GERALDINE GLADYS HAZEL IRENE LUCILLE MABEL MILDRED MYRTLE NELLIE OPAL PAULINE
THELMA WILLIE LINDSEY LESLIE TRACY DANA JAMIE JORDAN CASEY
JAKE LUKE COLE CODY CHAD BRETT SHANE CLINT DUSTIN DUSTY JARED JEREMIAH LEVI
CALEB SETH ISAAC ELI OWEN MASON HUNTER BLAKE CHASE GRANT DREW REID TANNER TREY
COREY DARIN DARREN DERRICK DEWAYNE DWAYNE ELDON EMMETT FRANKLIN GENE GLEN
GORDON GRADY GREG HAL HANK HOYT JAY JEFF JIM JIMMIE JOEL JON KENT KIRK KURT
LANCE LANE LEE LELAND LEON LYLE MACK MALCOLM MARC MATT MAX MITCHELL MONTE NEAL
NED NICK NOEL PHIL RANDAL RAY REX RICK ROD RON ROY SAM SHAWN SPENCER STEVE
STUART TED TIM TODD TOM TONY VAN VERN WAYLON WILEY ZANE
ALLISON ANGIE APRIL BECKY BELINDA BETH BRANDI CANDY CARLA CARRIE CATHY
CHARLOTTE CHRISTY CLAUDIA COLLEEN CRYSTAL DARLENE DAWN DEANNA DEE DELORES DENA
DIXIE ELAINE ELLA ERIN FAYE GAIL GINA GINGER GWEN HOLLY IDA JAN JANE JANIE
JEANNE JENNY JILL JOANN JODY JOSIE JOY KATHY KAY KELLIE KIM KRIS LANA LEAH
LENA LINDSAY LORETTA LORRAINE LOU LUCY LYNN MANDY MARCIA MARGIE MARLENE MELANIE
MELINDA MISTY MOLLY MONICA NADINE NAOMI NINA NOLA PAM PATSY PAULETTE PENNY
PHYLLIS RENEE RHONDA RITA ROBIN RONDA ROSA ROSIE SALLY SHANNON SHERI SHERRI
STACY SUE SUZANNE TAMMY TANYA TERRI TINA TONYA TRACI TRINA VICKI VICKIE VIVIAN
WENDY YVONNE
""".split())

SUFFIXES = {"JR", "SR", "II", "III", "IV"}

# Not used to decide a salutation, only to explain why there is not one. A farm
# trading as an entity has no first name to greet, and that is normal rather
# than something to go and check.
BUSINESS_WORDS = {
    "FARM", "FARMS", "FARMING", "LLC", "INC", "INCORPORATED", "LP", "LLP",
    "CO", "COMPANY", "TRUST", "POULTRY", "ENTERPRISES", "ENTERPRISE", "SONS",
    "PARTNERSHIP", "PROPERTIES", "RANCH", "ESTATE", "REVOCABLE", "LIVING",
    "BROTHERS", "BROS", "FAMILY", "CORP", "CORPORATION", "ETAL", "ORIGINS",
}


def classify(raw: str) -> tuple[str, str]:
    """Return (salutation, status) where status is person, business or unknown."""
    salutation, confident = parse_first_name(raw)
    if confident:
        return salutation, "person"
    tokens = {t for t in str(raw).upper().replace(".", "").split()}
    if tokens & BUSINESS_WORDS:
        return "", "business"
    return "", "unknown"


def parse_first_name(raw: str) -> tuple[str, bool]:
    """Return (salutation, confident).

    Order in this file is given name first: JOHN A SMITH. Verified against the
    account file, where common given names land on token 0 and never on token 1.
    """
    tokens = [t for t in str(raw).upper().replace(".", "").split() if t]
    if not tokens:
        return "", False

    # ROBERT & MARY SMITH -> both of them, which is how a neighbour writes it.
    if "&" in tokens:
        i = tokens.index("&")
        if (i == 1 and len(tokens) >= 3
                and tokens[0] in GIVEN_NAMES and tokens[2] in GIVEN_NAMES):
            return f"{tokens[0].title()} and {tokens[2].title()}", True
        return "", False

    first = tokens[0]
    if first in SUFFIXES or first not in GIVEN_NAMES:
        return "", False
    return first.title(), True


def title_case_address(s: str) -> str:
    """Billing files are all caps. Handwriting them back in caps looks like a
    bill, which is the opposite of the point."""
    out = []
    for word in str(s).split():
        if word.upper() in {"AR", "MO", "TN", "KS", "OK", "TX", "PO", "US",
                            "NE", "NW", "SE", "SW", "N", "S", "E", "W"}:
            out.append(word.upper())
        elif any(c.isdigit() for c in word):
            out.append(word.upper())
        else:
            out.append(word.title())
    return " ".join(out)


def letter_text(salutation: str, houses: float, sheet_row: str) -> list[str]:
    greet = f"Hi {salutation}," if salutation else "Hi,"
    kwh = KWH_BY_ROW.get(sheet_row)
    if kwh:
        opener = (f"A {int(houses)}-house farm around here runs about {kwh} kWh "
                  "a year. Most of that is fans.")
    else:
        # The two-house farms have no median worth quoting. Same note, opened on
        # the bill instead of the number.
        opener = ("I read power bills for a living. Rate class, meter "
                  "multipliers, demand charges, sales tax. On a poultry farm "
                  "they are worth reading.")
    if kwh:
        body = ("I read power bills for a living. Rate class, meter "
                "multipliers, demand charges, sales tax. Send 12 months of "
                f"yours to {EMAIL} and I will tell you what I find. No charge, "
                "no obligation.")
    else:
        body = (f"Send 12 months of yours to {EMAIL} and I will tell you what I "
                "find. No charge, no obligation.")
    return [greet, opener, body, "The sheet explains the rest.", "Clint"]


def page(pdf, row, index, total):
    fig = plt.figure(figsize=(PAGE_W, PAGE_H), dpi=150)
    fig.patch.set_facecolor(PAPER)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.canvas.draw()

    salutation, status = classify(row["name"])

    # ------------------------------------------------------------- page head
    ax.add_patch(Rectangle((L, 0.951), 0.019, 0.013, facecolor="none",
                           edgecolor=MUTE, lw=0.9))
    ax.text(L + 0.030, 0.9575, f"{index} of {total}", family=MONO, size=9,
            color=MUTE, ha="left", va="center")
    ax.text(R, 0.9575, f"{int(row['houses'])} houses", family=MONO, size=9,
            color=MUTE, ha="right", va="center")
    ax.plot([L, R], [0.934, 0.934], color=INK, lw=1.2)

    flow = Flow(fig, ax, 0.905)
    flow.text("Copy this letter", HEAD, 11, weight="bold", color=BRAND,
              gap_after=0.014)

    if status == "unknown":
        flow.text(f"CHECK THIS NAME. The billing file says: {row['name']}. "
                  "Write the grower's first name if you know it, otherwise "
                  "leave the greeting as Hi,",
                  MONO, 8.2, color="#B3261E", leading=1.45, gap_after=0.014)
    elif status == "business":
        flow.text(f"Billed to {title_case_address(row['name'])}, so there is no "
                  "first name. Greeting stays Hi, unless you know the grower.",
                  MONO, 8.2, color=MUTE, leading=1.45, gap_after=0.014)

    for i, para in enumerate(letter_text(salutation, row["houses"],
                                         row["sheet_row"])):
        flow.text(para, SERIF, 14, leading=1.55,
                  gap_after=0.020 if i < 4 else 0.0)

    # -------------------------------------------------------------- envelope
    flow.gap(0.030)
    ax.plot([L, R], [flow.y, flow.y], color=RULE_C, lw=0.9)
    flow.gap(0.026)
    flow.text("Address the envelope", HEAD, 11, weight="bold", color=BRAND,
              gap_after=0.016)

    box_top = flow.y
    inner = Flow(fig, ax, box_top - 0.030, x0=L + 0.040, x1=R - 0.040)
    inner.text(title_case_address(row["name"]), SERIF, 15, leading=1.45,
               gap_after=0.004)
    inner.text(title_case_address(row["mail_address"]), SERIF, 15, leading=1.45,
               gap_after=0.004)
    inner.text(f"{title_case_address(row['city'])}, "
               f"{str(row['state']).strip().upper()} "
               f"{str(row['zip_code']).strip()}", SERIF, 15, leading=1.45)
    box_bottom = inner.y - 0.030
    ax.add_patch(Rectangle((L, box_bottom), R - L, box_top - box_bottom,
                           facecolor=PANEL, edgecolor="none", zorder=0))

    flow.y = box_bottom
    flow.gap(0.022)
    flow.text(f"Return address: Cleaner Greener Future, {ADDRESS}", MONO, 7.5,
              color=MUTE, leading=1.4)

    pdf.savefig(fig, facecolor=PAPER)
    plt.close(fig)
    return status


def main() -> int:
    if not MAIL_LIST.exists():
        print(f"ERROR: {MAIL_LIST} not found. Run scripts/mail_list.py first.",
              file=sys.stderr)
        return 1

    df = pd.read_csv(MAIL_LIST)
    # Write the biggest farms first. If the stack never gets finished, the ones
    # that did get done are the ones worth the most.
    df = df.sort_values("annualized_kwh", ascending=False).reset_index(drop=True)

    unsure = 0
    with PdfPages(OUT) as pdf:
        for i, row in df.iterrows():
            if page(pdf, row, i + 1, len(df)) == "unknown":
                unsure += 1

    print(f"wrote {OUT}: {len(df)} letters, ordered largest farm first")
    print(f"names needing a look before writing: {unsure}")
    print(f"greeted by first name: "
          f"{sum(1 for _, r in df.iterrows() if classify(r['name'])[1] == 'person')}")
    print(f"business names, greeting stays 'Hi,': "
          f"{sum(1 for _, r in df.iterrows() if classify(r['name'])[1] == 'business')}")
    print(f"out-of-state envelopes: "
          f"{(df.state.astype(str).str.strip() != 'AR').sum()}")
    print("Personal data. out/ is gitignored; keep it off the repo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
