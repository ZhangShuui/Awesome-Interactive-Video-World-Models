#!/usr/bin/env python3
"""Render the GitHub Pages site from data/.

data/papers.jsonl + data/tags.json + web/*.template.html -> site/

The same rule as the README: the data file is the source, the site is output.
Edit data/papers.jsonl or web/, never site/. Unlike README.md the result is not
committed -- .gitignore covers site/ and the Pages workflow rebuilds it on every
push, so it cannot go stale.

The templates own all prose and all markup. This script fills marked blocks:

    <!-- BEGIN:ROWS -->  ... <!-- END:ROWS -->
    <!-- SLOT:COUNT -->

Interactive demos are hand-written pages under demos/<paper-id>/. Any directory
there whose name matches a paper id is copied into the build and given a wrapper
page carrying the site chrome; the paper's row in the index grows a DEMO badge.
Directories starting with `_` are skipped, which is how demos/_template stays a
template instead of becoming a demo for a paper called `_template`.

Usage:
  python3 scripts/build_site.py                # build into site/
  python3 scripts/build_site.py --out /tmp/x   # build somewhere else
  python3 scripts/build_site.py --check        # build to a temp dir, report only
"""
import argparse
import datetime as dt
import html
import json
import math
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
WEB = ROOT / "web"
DEMOS = ROOT / "demos"

# The row's id is already a link to the paper, so listing PAPER again on all
# 451 rows labels nothing -- 381 of them have no other link at all. Only the
# links that tell one row from another are named, and whichever link the id
# points at is dropped from the list rather than printed twice.
LINK_ORDER = [("paper", "PAPER"), ("website", "SITE"),
              ("code", "CODE"), ("blog", "BLOG")]
ID_LINK_ORDER = ("paper", "website", "blog")

# The comparison fields, in the order a reader wants them: what it is, how you
# drive it, how long it holds, what it remembers, how fast.
PROFILE_FIELDS = [
    ("backbone", "Backbone"),
    ("action_space", "Action space"),
    ("horizon", "Horizon"),
    ("memory", "Memory"),
    ("fps", "Reported FPS"),
    ("open_source", "Open source"),
]

# Entry points a hand-written demo may use, most conventional first.
DEMO_ENTRIES = ("index.html", "demo.html", "main.html")


def esc(value):
    return html.escape(str(value), quote=True)


# ------------------------------------------------------------------ loading --

def load_papers(path):
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            records.append(json.loads(line))
    return records


def load_tags(path):
    return json.loads(path.read_text(encoding="utf-8"))


def venue_of(rec):
    """Same rule as the README: a real venue wins, an inherited `arXiv 2026.06`
    is re-derived from the date so the whole page speaks one house style."""
    venue = (rec.get("venue") or "").strip()
    if venue and not re.match(r"^arxiv\b", venue, re.I):
        return venue
    date = rec.get("date") or ""
    if re.match(r"\d{4}-\d{2}", date):
        return f"arXiv {date[:4]}.{date[5:7]}"
    return venue or ""


def display_title(rec):
    """`Name: Title` prints its name once. The row already shows the name in
    display type, so repeating the prefix in the title reads as a stutter."""
    title = rec["title"].rstrip(". ")
    name = rec.get("name")
    if name and title.lower().startswith(f"{name.lower()}:"):
        title = title[len(name) + 1:].strip()
    return title


# -------------------------------------------------------------------- demos --

def find_demos(demos_dir, known_ids):
    """Map paper id -> entry filename, for every hand-written demo present.

    A directory that matches no paper is a mistake worth naming: it means a
    demo was written for an id that is not in the list, or the id was mistyped,
    and silently building nothing would hide that for as long as nobody looked.
    """
    found, orphans = {}, []
    if not demos_dir.is_dir():
        return found, orphans
    for child in sorted(demos_dir.iterdir()):
        if not child.is_dir() or child.name.startswith("_") or child.name.startswith("."):
            continue
        entry = next((e for e in DEMO_ENTRIES if (child / e).is_file()), None)
        if entry is None:
            orphans.append(f"demos/{child.name}/: no {' or '.join(DEMO_ENTRIES)}")
            continue
        if child.name not in known_ids:
            orphans.append(f"demos/{child.name}/: no paper with that id")
            continue
        found[child.name] = entry
    return found, orphans


# ----------------------------------------------------------------- rendering --

def render_readout(records, profiled, demos, years):
    cells = [
        (f"{len(records)}", "papers"),
        (f"{profiled}", "profiled"),
        (f"{min(years)}–{max(years)}", "span"),
    ]
    if demos:
        cells.append((f"{len(demos)}", "demos"))
    return "\n".join(
        f'      <li><span class="n">{esc(n)}</span><span class="k">{esc(k)}</span></li>'
        for n, k in cells)


def render_bars(tags, counts):
    top = max(counts.values()) if counts else 1
    out = []
    for i, tag in enumerate(tags):
        n = counts.get(tag["key"], 0)
        pct = round(100 * n / top, 2) if top else 0
        out.append(
            f'        <button class="bar" type="button" data-tag="{esc(tag["key"])}"'
            f' aria-pressed="false" style="--hue:{tag["hue"]};--i:{i}"'
            f' title="{esc(tag["title"])}">'
            f'<span class="bar__code">{esc(tag["code"])}</span>'
            f'<span class="bar__track"><span class="bar__fill" style="--pct:{pct}%;--i:{i}"></span></span>'
            f'<span class="bar__n">{n}</span></button>')
    return "\n".join(out)


def render_years(by_year):
    """Square root, not linear: 2026 has 268 papers and 2020 has 1, and a
    linear column chart renders the whole prehistory as an invisible line."""
    if not by_year:
        return ""
    years = list(range(min(by_year), max(by_year) + 1))
    top = math.sqrt(max(by_year.values()))
    out = []
    for i, year in enumerate(years):
        n = by_year.get(year, 0)
        h = round(100 * math.sqrt(n) / top, 2) if top else 0
        out.append(
            f'        <div class="year{"" if n else " year--empty"}" title="{n} paper(s) in {year}">'
            f'<span class="year__n">{n or ""}</span>'
            f'<span class="year__col" style="--h:{h}%;--i:{i}"></span>'
            f'<span class="year__k">{esc(str(year)[2:])}</span></div>')
    return "\n".join(out)


def render_chips(tags, counts):
    return "\n".join(
        f'      <button class="chip" type="button" data-tag="{esc(t["key"])}"'
        f' aria-pressed="false" style="--hue:{t["hue"]}"'
        f' title="{esc(t["blurb"])}">{esc(t["code"])}'
        f' <span style="opacity:.55">{counts.get(t["key"], 0)}</span></button>'
        for t in tags)


def render_flags(has_demo, n_code, n_profiled):
    flags = []
    if has_demo:
        flags.append(("demo", "DEMO"))
    flags.append(("code", f"CODE {n_code}"))
    flags.append(("profiled", f"PROFILED {n_profiled}"))
    return "\n".join(
        f'      <button class="chip chip--flag" type="button" data-flag="{esc(k)}"'
        f' aria-pressed="false">{esc(label)}</button>'
        for k, label in flags)


def render_tag_spans(rec, by_key, clickable=True):
    out = []
    for key in rec.get("tags", []):
        tag = by_key.get(key)
        if not tag:
            continue
        attrs = (f' class="tag" style="--hue:{tag["hue"]}" title="{esc(tag["title"])}"')
        if clickable:
            out.append(f'<button type="button" data-tag="{esc(key)}"{attrs}>{esc(tag["code"])}</button>')
        else:
            out.append(f'<span{attrs}>{esc(tag["code"])}</span>')
    return "".join(out)


def id_link_key(rec):
    links = rec.get("links") or {}
    return next((k for k in ID_LINK_ORDER if links.get(k)), None)


def render_links(rec, skip=None):
    links = rec.get("links") or {}
    return "".join(
        f'<a href="{esc(links[key])}" rel="noopener">{label}</a>'
        for key, label in LINK_ORDER if links.get(key) and key != skip)


def render_profile(rec):
    attrs = rec.get("attrs") or {}
    rows = [(label, attrs[key]) for key, label in PROFILE_FIELDS if attrs.get(key)]
    if not rows:
        return ""
    body = "\n".join(
        f'            <dt>{esc(label)}</dt><dd>{esc(value)}</dd>' for label, value in rows)
    return (
        '\n        <details class="profile">'
        '<summary>PROFILE</summary>'
        '\n          <dl class="profile__grid">\n' + body + "\n          </dl>"
        "\n        </details>")


def search_blob(rec, by_key):
    """One lowercased haystack per row. Tag codes go in too, so typing SYS
    finds the systems papers without reaching for the chip."""
    parts = [rec["id"], rec.get("name") or "", rec["title"], venue_of(rec)]
    for key in rec.get("tags", []):
        parts.append(key)
        tag = by_key.get(key)
        if tag:
            parts.append(tag["code"])
    return " ".join(parts).lower()


def render_row(rec, i, by_key, demo_ids):
    links = rec.get("links") or {}
    id_key = id_link_key(rec)
    paper_url = links.get(id_key, "") if id_key else ""
    name = rec.get("name")
    has_demo = rec["id"] in demo_ids

    ident = esc(rec["id"])
    id_cell = f'<a href="{esc(paper_url)}" rel="noopener">{ident}</a>' if paper_url else ident

    title_html = ""
    if name:
        title_html += f'<span class="row__name">{esc(name)}</span>'
    title_html += esc(display_title(rec))

    meta = []
    venue = venue_of(rec)
    if venue:
        meta.append(f'<span class="venue">{esc(venue)}</span>')
    tags_html = render_tag_spans(rec, by_key)
    if tags_html:
        meta.append(tags_html)
    links_html = render_links(rec, skip=id_key)
    if links_html:
        meta.append(f'<span class="links">{links_html}</span>')
    if has_demo:
        meta.append(f'<a class="demo-badge" href="demos/{ident}/">&#9654; DEMO</a>')

    return (
        f'    <li class="row" id="p-{ident}" style="--i:{i}"'
        f' data-search="{esc(search_blob(rec, by_key))}"'
        f' data-tags="{esc(" ".join(rec.get("tags", [])))}"'
        f'{" data-demo=\"1\"" if has_demo else ""}'
        f'{" data-code=\"1\"" if links.get("code") else ""}'
        f'{" data-profiled=\"1\"" if rec.get("attrs") else ""}>'
        f'\n      <div class="row__id">{id_cell}</div>'
        f'\n      <div class="row__main">'
        f'\n        <h2 class="row__title">{title_html}</h2>'
        f'\n        <div class="row__meta">{"".join(meta)}</div>'
        f'{render_profile(rec)}'
        f'\n      </div>\n    </li>')


# ------------------------------------------------------------------ filling --

def fill_block(text, name, body):
    pattern = re.compile(
        rf"(<!-- BEGIN:{name} -->).*?(<!-- END:{name} -->)", re.S)
    if not pattern.search(text):
        sys.exit(f"template has no {name} block")
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(2)}", text)


def fill_slot(text, name, value):
    return text.replace(f"<!-- SLOT:{name} -->", str(value))


# -------------------------------------------------------------------- build --

def build(out_dir, papers_path=None, tags_path=None, demos_dir=None):
    papers = load_papers(papers_path or DATA / "papers.jsonl")
    tags = load_tags(tags_path or DATA / "tags.json")
    by_key = {t["key"]: t for t in tags}
    known_ids = {r["id"] for r in papers}

    demos, orphans = find_demos(demos_dir or DEMOS, known_ids)
    for problem in orphans:
        print(f"[site] warning: {problem}", file=sys.stderr)

    records = sorted(papers, key=lambda r: (r.get("date") or "", r["id"]), reverse=True)

    counts = {t["key"]: 0 for t in tags}
    by_year = {}
    for rec in records:
        for key in rec.get("tags", []):
            if key in counts:
                counts[key] += 1
        date = rec.get("date") or ""
        if re.match(r"\d{4}", date):
            year = int(date[:4])
            by_year[year] = by_year.get(year, 0) + 1

    profiled = sum(1 for r in records if r.get("attrs"))
    n_code = sum(1 for r in records if (r.get("links") or {}).get("code"))

    page = (WEB / "index.template.html").read_text(encoding="utf-8")
    page = fill_block(page, "READOUT", render_readout(records, profiled, demos, by_year))
    page = fill_block(page, "BARS", render_bars(tags, counts))
    page = fill_block(page, "YEARS", render_years(by_year))
    page = fill_block(page, "CHIPS", render_chips(tags, counts))
    page = fill_block(page, "FLAGS", render_flags(bool(demos), n_code, profiled))
    page = fill_block(page, "ROWS", "\n".join(
        render_row(rec, i, by_key, demos) for i, rec in enumerate(records)))
    page = fill_slot(page, "COUNT", len(records))
    page = fill_slot(page, "PROFILED", profiled)
    page = fill_slot(page, "BUILT", dt.date.today().isoformat())

    out_dir = Path(out_dir)
    if out_dir.exists():
        shutil.rmtree(out_dir)
    (out_dir / "assets").mkdir(parents=True)

    (out_dir / "index.html").write_text(page, encoding="utf-8")
    shutil.copy2(WEB / "style.css", out_dir / "assets" / "style.css")
    shutil.copy2(WEB / "app.js", out_dir / "assets" / "app.js")
    # Pages runs Jekyll unless told not to, and Jekyll drops any directory
    # whose name begins with an underscore.
    (out_dir / ".nojekyll").write_text("", encoding="utf-8")

    for pid, entry in demos.items():
        rec = next(r for r in records if r["id"] == pid)
        build_demo_page(out_dir, rec, entry, by_key, demos_dir or DEMOS)

    return {"papers": len(records), "profiled": profiled, "demos": len(demos),
            "out": out_dir}


def build_demo_page(out_dir, rec, entry, by_key, demos_dir):
    pid = rec["id"]
    dest = out_dir / "demos" / pid
    shutil.copytree(demos_dir / pid, dest / "app")

    name = rec.get("name")
    heading = f"{name} — {display_title(rec)}" if name else display_title(rec)

    page = (WEB / "demo.template.html").read_text(encoding="utf-8")
    page = fill_block(page, "TAGS", render_tag_spans(rec, by_key, clickable=False))
    page = fill_block(page, "LINKS", render_links(rec))
    page = fill_slot(page, "TITLE", esc(name or display_title(rec)))
    page = fill_slot(page, "HEADING", esc(heading))
    page = fill_slot(page, "HASH", f"p-{esc(pid)}")
    page = fill_slot(page, "ENTRY", esc(entry))
    page = fill_slot(page, "ID", esc(pid))
    (dest / "index.html").write_text(page, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "site")
    ap.add_argument("--check", action="store_true",
                    help="build into a temporary directory and discard it")
    args = ap.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory() as tmp:
            stats = build(Path(tmp) / "site")
            print(f"[site] builds clean: {stats['papers']} papers, "
                  f"{stats['profiled']} profiled, {stats['demos']} demo(s)")
        return

    stats = build(args.out)
    print(f"[site] {stats['papers']} papers, {stats['profiled']} profiled, "
          f"{stats['demos']} demo(s) -> {stats['out']}")


if __name__ == "__main__":
    main()
