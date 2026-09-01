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

Long-form explainers are single self-contained pages under explainers/, named
explainers/<paper-id>.html. They are published as themselves rather than
wrapped, and the row grows an EXPLAINER badge. Same registration rule: the
filename is the whole of it.

Notes are the same kind of page written across the index instead of down one
paper -- a comparison table, a taxonomy, a timeline. They belong to no row, so
notes/<slug>.html is published under /notes/ behind a listing page of its own.
A note names itself: the listing reads its <title> and its <meta description>,
so there is still no register to keep.

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
EXPLAINERS = ROOT / "explainers"
NOTES = ROOT / "notes"

# The row's id is already a link to the paper, so listing PAPER again on all
# 451 rows labels nothing -- 381 of them have no other link at all. Only the
# links that tell one row from another are named, and whichever link the id
# points at is dropped from the list rather than printed twice.
LINK_ORDER = [("paper", "PAPER"), ("website", "SITE"),
              ("code", "CODE"), ("blog", "BLOG")]
ID_LINK_ORDER = ("paper", "website", "blog")

# Everything that leaves the site opens beside it. The index is scanned, not
# read start to finish, and following a paper should not cost the reader the
# filter they built and the place they had scrolled to. noreferrer rides along
# with noopener because a target="_blank" without it hands the new page a
# handle on this one.
NEW_TAB = ' target="_blank" rel="noopener noreferrer"'


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

# An explainer is a long document that already carries its own sticky header,
# its own theme toggle and its own scroll-progress bar. Wrapping it in an
# iframe the way a demo is wrapped would break all three -- a progress bar
# measures a viewport it no longer owns -- so it is served as itself and given
# the one thing a page reached by a shared link cannot supply for itself: the
# way back. Bottom left, because every explainer written so far already keeps a
# back-to-top control at bottom right.
BACK_LINK = """<a id="site-back" href="{href}">&larr; {label}</a>
<style>
#site-back{{position:fixed;left:14px;bottom:14px;z-index:190;padding:7px 12px;
  border-radius:999px;text-decoration:none;letter-spacing:.14em;
  font:600 11px/1 "IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;
  color:#f4f6f8;background:#15171b;border:1px solid rgba(255,255,255,.24);
  box-shadow:0 2px 10px rgba(0,0,0,.35);opacity:.7;
  transition:opacity .15s var(--ease,ease),transform .15s var(--ease,ease)}}
#site-back:hover{{opacity:1;transform:translateY(-1px)}}
@media print{{#site-back{{display:none}}}}
</style>
"""

BODY_TAG = re.compile(r"<body\b[^>]*>", re.I)


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


def read_meta(text, name):
    """Whatever a page says about itself in <head>, or ""."""
    pattern = re.compile(
        rf'<meta\s+name="{name}"\s+content="([^"]*)"', re.I | re.S)
    m = pattern.search(text)
    return html.unescape(m.group(1)).strip() if m else ""


def read_title(text):
    m = re.search(r"<title>(.*?)</title>", text, re.S | re.I)
    return html.unescape(re.sub(r"\s+", " ", m.group(1))).strip() if m else ""


def find_notes(notes_dir):
    """Every note, in the order the listing shows them.

    A note carries no paper id to be checked against, so the only thing that
    can be wrong with one is that it does not say what it is. A page with no
    <title> would list as a blank line, which is worth a word rather than a
    shrug.
    """
    found, orphans = [], []
    if not notes_dir.is_dir():
        return found, orphans
    for child in sorted(notes_dir.glob("*.html")):
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        text = child.read_text(encoding="utf-8")
        title = read_title(text)
        if not title:
            orphans.append(f"notes/{child.name}: no <title> to list it under")
            continue
        found.append({"slug": child.stem, "path": child, "title": title,
                      "blurb": read_meta(text, "description")})
    return found, orphans


def find_explainers(explainers_dir, known_ids):
    """Map paper id -> source file, for every explainer present.

    The same registration rule as demos, one directory level shallower: an
    explainer is a single self-contained page, so `explainers/<id>.html` is
    the whole artefact and a directory to hold one file would be ceremony.
    An id nobody publishes is named for the same reason a stray demo is.
    """
    found, orphans = {}, []
    if not explainers_dir.is_dir():
        return found, orphans
    for child in sorted(explainers_dir.glob("*.html")):
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        if child.stem not in known_ids:
            orphans.append(f"explainers/{child.name}: no paper with that id")
            continue
        found[child.stem] = child
    return found, orphans


# ----------------------------------------------------------------- rendering --

def render_readout(records, profiled, demos, explainers, years):
    cells = [
        (f"{len(records)}", "papers"),
        (f"{profiled}", "profiled"),
        (f"{min(years)}–{max(years)}", "span"),
    ]
    if demos:
        cells.append((f"{len(demos)}", "demos"))
    if explainers:
        cells.append((f"{len(explainers)}", "explainers"))
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
        empty = "" if n else " year--empty"
        out.append(
            f'        <div class="year{empty}" title="{n} paper(s) in {year}">'
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


def render_note_cards(notes):
    """The title is the link. A note's title is a sentence, not a code, so
    unlike a paper row there is no id in the margin to point at instead."""
    out = []
    for i, note in enumerate(notes):
        blurb = (f'\n        <p class="note-card__blurb">{esc(note["blurb"])}</p>'
                 if note["blurb"] else "")
        out.append(
            f'    <li class="note-card" style="--i:{i}">'
            f'\n      <a class="note-card__link" href="{esc(note["slug"])}.html">'
            f'\n        <h2 class="note-card__title">{esc(note["title"])}</h2>'
            f'{blurb}'
            f'\n      </a>\n    </li>')
    return "\n".join(out)


def render_flags(has_demo, has_explainer, n_code, n_profiled):
    flags = []
    if has_demo:
        flags.append(("demo", "DEMO"))
    if has_explainer:
        flags.append(("explainer", "EXPLAINER"))
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
        f'<a href="{esc(links[key])}"{NEW_TAB}>{label}</a>'
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


def search_blob(rec, by_key, has_demo=False, has_explainer=False):
    """One lowercased haystack per row. Tag codes go in too, so typing SYS
    finds the systems papers without reaching for the chip -- and so do the
    words for the sub-pages, including the Chinese one, because the explainers
    are written in Chinese and 解读 is what their reader would type."""
    parts = [rec["id"], rec.get("name") or "", rec["title"], venue_of(rec)]
    for key in rec.get("tags", []):
        parts.append(key)
        tag = by_key.get(key)
        if tag:
            parts.append(tag["code"])
    if has_demo:
        parts.append("demo")
    if has_explainer:
        parts.append("explainer 解读")
    return " ".join(parts).lower()


def render_row(rec, i, by_key, demo_ids, explainer_ids):
    links = rec.get("links") or {}
    id_key = id_link_key(rec)
    paper_url = links.get(id_key, "") if id_key else ""
    name = rec.get("name")
    has_demo = rec["id"] in demo_ids
    has_explainer = rec["id"] in explainer_ids

    ident = esc(rec["id"])
    id_cell = f'<a href="{esc(paper_url)}"{NEW_TAB}>{ident}</a>' if paper_url else ident

    # The title is the thing a reader points at, so the title is the link --
    # not just the id, which is a 10px string in the margin. The tags, the
    # other links and the profile toggle stay siblings of it: nesting them
    # inside the anchor would make every one of them un-clickable.
    label = ""
    if name:
        label += f'<span class="row__name">{esc(name)}</span>'
    label += esc(display_title(rec))
    title_html = (f'<a class="row__link" href="{esc(paper_url)}"{NEW_TAB}>{label}</a>'
                  if paper_url else label)

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
    if has_explainer:
        meta.append(f'<a class="explainer-badge" href="explainers/{ident}.html"'
                    f' title="Long-form read-through of this paper, written for'
                    f' this index (Chinese)">&#9776; EXPLAINER</a>')

    # Built outside the f-string: an escaped quote inside an f-string
    # expression is a syntax error before Python 3.12, and CI runs 3.11.
    flags = "".join(
        f' data-{name}="1"' for name, on in (
            ("demo", has_demo),
            ("explainer", has_explainer),
            ("code", bool(links.get("code"))),
            ("profiled", bool(rec.get("attrs"))),
        ) if on)

    return (
        f'    <li class="row" id="p-{ident}" style="--i:{i}"'
        f' data-search="{esc(search_blob(rec, by_key, has_demo, has_explainer))}"'
        f' data-tags="{esc(" ".join(rec.get("tags", [])))}"'
        f'{flags}>'
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

def build(out_dir, papers_path=None, tags_path=None, demos_dir=None,
          explainers_dir=None, notes_dir=None):
    papers = load_papers(papers_path or DATA / "papers.jsonl")
    tags = load_tags(tags_path or DATA / "tags.json")
    by_key = {t["key"]: t for t in tags}
    known_ids = {r["id"] for r in papers}

    demos, orphans = find_demos(demos_dir or DEMOS, known_ids)
    explainers, more = find_explainers(explainers_dir or EXPLAINERS, known_ids)
    notes, unnamed = find_notes(notes_dir or NOTES)
    for problem in orphans + more + unnamed:
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
    page = fill_block(page, "READOUT",
                      render_readout(records, profiled, demos, explainers, by_year))
    page = fill_block(page, "BARS", render_bars(tags, counts))
    page = fill_block(page, "YEARS", render_years(by_year))
    page = fill_block(page, "CHIPS", render_chips(tags, counts))
    page = fill_block(page, "FLAGS",
                      render_flags(bool(demos), bool(explainers), n_code, profiled))
    page = fill_block(page, "ROWS", "\n".join(
        render_row(rec, i, by_key, demos, explainers) for i, rec in enumerate(records)))
    page = fill_slot(page, "COUNT", len(records))
    page = fill_slot(page, "PROFILED", profiled)
    page = fill_slot(page, "BUILT", dt.date.today().isoformat())
    page = fill_block(page, "NOTELINK", render_note_link(notes))
    # Both entrances are conditional on the same thing. A hard-coded one in the
    # footer would be a dead link on any checkout with an empty notes/.
    page = fill_block(page, "NOTEFOOT",
                      ' ·\n    <a href="notes/">Notes</a>' if notes else "")

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

    if explainers:
        (out_dir / "explainers").mkdir(parents=True, exist_ok=True)
    for pid, source in explainers.items():
        build_explainer_page(out_dir, pid, source)

    if notes:
        build_notes(out_dir, notes)

    return {"papers": len(records), "profiled": profiled, "demos": len(demos),
            "explainers": len(explainers), "notes": len(notes), "out": out_dir}


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


def build_explainer_page(out_dir, pid, source):
    """An explainer belongs to one paper, so it goes back to that paper's row
    rather than to the top of a 458-row list."""
    write_with_back_link(source, out_dir / "explainers" / f"{pid}.html",
                         href=f"../index.html#p-{pid}", label="INDEX")


def render_note_link(notes):
    """The index only advertises the notes once there are some. An empty
    section behind a nav item is worse than no nav item."""
    if not notes:
        return ""
    plural = "" if len(notes) == 1 else "s"
    return ('    <p class="masthead__nav"><a href="notes/">'
            f'{len(notes)} cross-paper note{plural} &rarr;</a></p>')


def build_notes(out_dir, notes):
    """The listing, then every note behind it, each pointing back at the
    listing rather than at the paper index -- a note belongs to no row, so
    there is no row to return to."""
    dest = out_dir / "notes"
    dest.mkdir(parents=True, exist_ok=True)

    page = (WEB / "notes.template.html").read_text(encoding="utf-8")
    page = fill_block(page, "NOTES", render_note_cards(notes))
    page = fill_slot(page, "COUNT", len(notes))
    (dest / "index.html").write_text(page, encoding="utf-8")

    for note in notes:
        write_with_back_link(note["path"], dest / f'{note["slug"]}.html',
                             href="index.html", label="NOTES")


def write_with_back_link(source, target, href, label):
    """Copy the page verbatim but for one addition: the link home.

    Verbatim matters more here than anywhere else in the build. These pages
    are hand-written, self-contained and already themed; anything this script
    rewrote it would then have to keep rewriting correctly for every page
    written after it. So the only edit is one anchor and the rules that
    position it, inserted after <body> where it cannot land inside <head>.
    """
    text = source.read_text(encoding="utf-8")
    back = BACK_LINK.format(href=esc(href), label=label)
    page, n = BODY_TAG.subn(lambda m: f"{m.group(0)}\n{back}", text, count=1)
    if not n:
        print(f"[site] warning: {source.parent.name}/{source.name} has no "
              "<body>; published with no way back", file=sys.stderr)
    target.write_text(page, encoding="utf-8")


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
                  f"{stats['profiled']} profiled, {stats['demos']} demo(s), "
                  f"{stats['explainers']} explainer(s), {stats['notes']} note(s)")
        return

    stats = build(args.out)
    print(f"[site] {stats['papers']} papers, {stats['profiled']} profiled, "
          f"{stats['demos']} demo(s), {stats['explainers']} explainer(s), "
          f"{stats['notes']} note(s) -> {stats['out']}")


if __name__ == "__main__":
    main()
