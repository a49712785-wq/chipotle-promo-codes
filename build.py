#!/usr/bin/env python3
"""chipotlecoupons.us homepage builder.

Renders the offer board from data/offers.json into index.html and stamps
every freshness surface from the same `last_checked` date: masthead badge,
board H2 (offer count + date), intro tokens, <title>/meta month + count,
WebPage schema dateModified, and sitemap.xml homepage lastmod.

HONESTY RULE: `last_checked` in data/offers.json may only be set to a date
on which every active offer was actually re-verified against its official
source. This script stamps dates; it does not invent them.

Usage:
    python3 build.py           # render + stamp index.html and sitemap.xml
    python3 build.py --check   # validate data only, write nothing
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "offers.json"
INDEX = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"

MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
MON3 = [m[:3] for m in MONTHS]


def long_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"


def short_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{MON3[d.month - 1]} {d.day}"


def month_year(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{MONTHS[d.month - 1]} {d.year}"


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def render_card(o: dict) -> str:
    kind = o["kind"]
    classes = "offer-card"
    if o.get("featured"):
        classes += " featured"
    if kind == "community":
        classes += " community"
    parts = [f'<article class="{classes}">']
    top = f'<div class="offer-card-top"><span class="offer-tag tag-{kind}">{esc(o["tag"])}</span>'
    if o.get("chip"):
        top += f' <span class="status-badge {o["chip"]["class"]}">{esc(o["chip"]["text"])}</span>'
    top += "</div>"
    parts.append(top)
    parts.append(f'<h3 class="offer-headline">{esc(o["headline"])}</h3>')
    parts.append(f'<p class="offer-benefit">{esc(o["benefit"])}</p>')
    if o.get("code"):
        if o.get("featured"):
            parts.append(
                '<div class="offer-code-row">'
                f'<span class="code-display">{esc(o["code"])}</span>'
                f'<button class="btn-copy" data-copy-code="{esc(o["code"])}" aria-label="Copy code {esc(o["code"])}">'
                "<span>Copy Code</span></button></div>"
            )
        else:
            parts.append(
                f'<p class="offer-code"><button class="code-chip" data-copy-code="{esc(o["code"])}" '
                f'aria-label="Copy code {esc(o["code"])}"><span class="code-chip-text">{esc(o["code"])}</span>'
                '<span class="code-chip-action">Copy</span></button></p>'
            )
    parts.append(f'<p class="offer-terms">{esc(o["terms"])}</p>')
    if o.get("cta"):
        parts.append(
            f'<p class="offer-cta"><a href="{o["cta"]["href"]}">{esc(o["cta"]["text"])} &rarr;</a></p>'
        )
    checked = short_date(o["checked"])
    if o.get("source_url"):
        footer = (f'Checked {checked} · <a href="{o["source_url"]}" target="_blank" '
                  f'rel="noopener">{esc(o["source_label"])}</a>')
    else:
        footer = f'Checked {checked} · {esc(o["source_label"])}'
    parts.append(f'<p class="offer-footer">{footer}</p>')
    parts.append("</article>")
    return "\n        ".join(parts)


def replace_region(text: str, start_marker: str, end_marker: str, new: str, name: str) -> str:
    pat = re.compile(re.escape(start_marker) + r".*?" + re.escape(end_marker), re.S)
    if not pat.search(text):
        raise SystemExit(f"ERROR: markers for {name} not found ({start_marker} ... {end_marker})")
    return pat.sub(lambda m: start_marker + new + end_marker, text, count=1)


def main() -> int:
    check_only = "--check" in sys.argv
    data = json.loads(DATA.read_text(encoding="utf-8"))
    last_checked = data["last_checked"]
    offers = data["offers"]
    active = [o for o in offers if o.get("active")]

    errors, warnings = [], []
    for o in offers:
        if o.get("active"):
            if o["kind"] != "community" and not o.get("source_url"):
                errors.append(f"offer {o['id']}: active non-community offer has no source_url")
            if o["checked"] != last_checked:
                warnings.append(f"offer {o['id']}: checked {o['checked']} != last_checked {last_checked}")
    code_count = sum(1 for o in active if o["kind"] == "code")
    if code_count > 1:
        warnings.append(
            f"intro must not claim one live checkout code with {code_count} active code offers — update the intro copy"
        )
    elif code_count == 0:
        print("NOTE: no active checkout-code offers — intro/title must not claim a live code")
    for w in warnings:
        print("WARNING:", w)
    if errors:
        for e in errors:
            print("ERROR:", e)
        return 1
    print(f"offers: {len(active)} active of {len(offers)} total · last_checked {last_checked}")
    if check_only:
        print("--check: nothing written")
        return 0

    text = INDEX.read_text(encoding="utf-8")
    count = len(active)
    ld = long_date(last_checked)
    my = month_year(last_checked)

    # 1) Offer board cards
    cards = "\n        ".join(render_card(o) for o in active)
    text = replace_region(text, "<!-- OFFERS:START -->", "<!-- OFFERS:END -->",
                          "\n        " + cards + "\n        ", "offer board")

    # 2) Board H2 (count + date)
    text = replace_region(text, "<!-- BOARD-H2:START -->", "<!-- BOARD-H2:END -->",
                          f"{count} Chipotle Promo Codes &amp; Offers — Checked {ld}", "board H2")

    # 3) Masthead badge
    text = replace_region(text, "<!-- BADGE:START -->", "<!-- BADGE:END -->",
                          f"Last checked against Chipotle's official sources: {ld}.", "badge")

    # 4) Intro tokens (other-offers count + today's date)
    text = replace_region(text, "<!-- INTRO-COUNT:START -->", "<!-- INTRO-COUNT:END -->",
                          str(count), "intro count")
    text = replace_region(text, "<!-- INTRO-DATE:START -->", "<!-- INTRO-DATE:END -->",
                          ld, "intro date")

    # 5) Title month (title, og:title, twitter:title, schema name share the string)
    new_title = f"Chipotle Promo Codes ({my}) — Boorito, Free Delivery & Rewards, Checked Daily"
    text, n = re.subn(r"Chipotle Promo Codes \([A-Z][a-z]+ \d{4}\) — [^\"<]+", new_title, text)
    if n < 3:
        print(f"WARNING: title string replaced in {n} places (expected >=3)")

    # 6) Meta descriptions (name/og/twitter + schema description share the build template)
    desc = (f"{count} Chipotle promo codes &amp; offers for {my} — Boorito $6 entrée, $0 delivery Nov 1, "
            f"free Rewards offers and more, checked daily against Chipotle's official terms.")
    desc_json = desc.replace("&amp;", "&")
    text = re.sub(r'(<meta name="description" content=")[^"]*(")', rf"\g<1>{desc}\g<2>", text)
    text = re.sub(r'(<meta property="og:description" content=")[^"]*(")', rf"\g<1>{desc}\g<2>", text)
    text = re.sub(r'(<meta name="twitter:description" content=")[^"]*(")', rf"\g<1>{desc}\g<2>", text)
    text = re.sub(r'("description": ")[^"]*(",\s*\n\s*"url": "https://chipotlecoupons\.us/")',
                  lambda m: m.group(1) + desc_json + m.group(2), text)

    # 7) WebPage schema name + dateModified
    text = re.sub(r'("@type": "WebPage",\s*\n\s*"name": ")[^"]*(")',
                  rf"\g<1>{new_title}\g<2>", text)
    text = re.sub(r'("dateModified": ")[\d-]+(")', rf"\g<1>{last_checked}\g<2>", text)

    INDEX.write_text(text, encoding="utf-8")
    print("index.html updated")

    # 8) Sitemap homepage lastmod
    sm = SITEMAP.read_text(encoding="utf-8")
    sm2, n = re.subn(r"(<loc>https://chipotlecoupons\.us/</loc>\s*<lastmod>)[\d-]+(</lastmod>)",
                     rf"\g<1>{last_checked}\g<2>", sm)
    if n != 1:
        print(f"WARNING: sitemap homepage lastmod replaced {n} times (expected 1)")
    else:
        SITEMAP.write_text(sm2, encoding="utf-8")
        print("sitemap.xml updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
