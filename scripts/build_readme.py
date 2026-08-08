#!/usr/bin/env python3
"""Render README.md and docs/comparison.md from data/.

data/papers.jsonl + data/sections.json + data/README.template.md -> README.md

The template owns all prose. This script only fills the marked blocks:

    <!-- BEGIN:CONTENTS -->  ... <!-- END:CONTENTS -->
    <!-- BEGIN:STATS -->     ... <!-- END:STATS -->
    <!-- BEGIN:LIST -->      ... <!-- END:LIST -->
    <!-- BEGIN:TABLE -->     ... <!-- END:TABLE -->

README.md is generated. Edit data/papers.jsonl, never the README.

Usage:
  python3 scripts/build_readme.py            # write README.md + docs/comparison.md
  python3 scripts/build_readme.py --check     # exit 1 if the files are stale
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

LINK_ORDER = [("paper", "Paper"), ("website", "Website"),
              ("code", "Code"), ("blog", "Blog")]

BACKBONE_LABELS = {
    "causal-diffusion": "causal diffusion",
    "bidirectional-diffusion": "bidir. diffusion",
    "hybrid-AR-diffusion": "AR + diffusion",
    "AR-transformer": "AR transformer",
    "SSM-hybrid": "SSM hybrid",
    "other": "other",
}

MEMORY_LABELS = {
    "none": "none",
    "implicit-context": "context",
    "explicit-spatial-reconstruction": "spatial (recon)",
    "explicit-spatial-storage": "spatial (store)",
    "retrieval": "retrieval",
    "compression-ssm": "compressive",
    "other": "other",
}

# Ordered: the first matching pattern that fires contributes its label.
ACTION_LABELS = [
    ("keyboard", r"keyboard|wasd|\bkeys?\b|button|gamepad|joystick"),
    ("mouse", r"\bmouse\b"),
    ("camera", r"camera|viewpoint|6-?dof|trajector|pose|navigat|orientation"),
    ("language", r"language|text|instruction|prompt|caption|narrat"),
    ("latent", r"latent action"),
    ("embodied", r"end-?effector|gripper|robot|hand |joint |manipulat"),
]


def norm_backbone(value):
    head = value.split(":")[0].split("+")[0].strip()
    return BACKBONE_LABELS.get(head, head)


def _memory_atom(value):
    head = re.split(r"[:(]", value)[0].strip()
    return MEMORY_LABELS.get(head, head)


def norm_memory(value):
    if value.startswith("hybrid"):
        parts = value.split(":", 1)[1] if ":" in value else ""
        labels = [_memory_atom(p) for p in parts.split("+") if p.strip()]
        return "hybrid: " + "+".join(labels) if labels else "hybrid"
    return _memory_atom(value)


def norm_action(value):
    if not value:
        return ""
    low = value.lower()
    hits = [label for label, pat in ACTION_LABELS if re.search(pat, low)]
    return " + ".join(hits[:3]) if hits else "other"


def venue_of(rec):
    """Real venues win. Inherited 'arxiv 2026.06' tags are not venues -- they
    are the posting month in someone else's formatting, so re-derive them from
    the date and get one house style instead of two."""
    venue = (rec.get("venue") or "").strip()
    if venue and not re.match(r"^arxiv\b", venue, re.I):
        return venue
    date = rec.get("date") or ""
    if re.match(r"\d{4}-\d{2}", date):
        return f"arXiv {date[:4]}.{date[5:7]}"
    return venue or None


def entry_line(rec):
    parts = ["*"]
    title = rec["title"].rstrip(". ")
    name = rec.get("name")
    if name:
        parts.append(f"**`{name}`**,")
        # The name tag already carries the prefix; repeating it reads as a stutter.
        if title.lower().startswith(f"{name.lower()}:"):
            title = title[len(name) + 1:].strip()
    parts.append(f"{title}.")
    venue = venue_of(rec)
    if venue:
        parts.append(f"**`{venue}`**")
    links = rec.get("links") or {}
    for key, label in LINK_ORDER:
        if links.get(key):
            parts.append(f"[[{label}]({links[key]})]")
    return " ".join(parts)


def anchor(title):
    """GitHub's heading slug. Punctuation is dropped *before* spaces become
    hyphens, so '&' leaves a gap behind: 'A & B' -> 'a--b'. Do not collapse."""
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    return re.sub(r"\s", "-", slug.strip())


def render_list(sections, by_section):
    out = []
    for sec in sections:
        recs = by_section.get(sec["key"], [])
        out.append(f"## {sec['title']}")
        out.append("")
        out.append(f"_{sec['blurb']}_ &nbsp;·&nbsp; **{len(recs)} entries**")
        out.append("")
        if not recs:
            out.append("_Nothing here yet — contributions welcome._")
            out.append("")
            continue
        out.extend(entry_line(r) for r in recs)
        out.append("")
    return "\n".join(out).rstrip()


def render_contents(sections, by_section):
    lines = []
    for sec in sections:
        n = len(by_section.get(sec["key"], []))
        lines.append(f"- [{sec['title']}](#{anchor(sec['title'])}) ({n})")
    lines.append("- [System Comparison](#system-comparison)")
    lines.append("- [Contributing](#contributing)")
    lines.append("- [Citation](#citation)")
    return "\n".join(lines)


def render_stats(records, sections):
    total = len(records)
    with_attrs = sum(1 for r in records if r["attrs"].get("backbone"))
    open_src = sum(1 for r in records if r["attrs"].get("open_source") is True)
    realtime = sum(1 for r in records
                   if _fps(r) is not None and _fps(r) >= 10)
    newest = max((r.get("date") or "") for r in records)
    return (f"**{total} papers** across {len(sections)} sections &nbsp;·&nbsp; "
            f"**{with_attrs}** read in depth and profiled in the comparison table "
            f"&nbsp;·&nbsp; **{open_src}** with released weights or code "
            f"&nbsp;·&nbsp; **{realtime}** reporting ≥10 FPS "
            f"&nbsp;·&nbsp; newest entry {newest}")


def _fps(rec):
    raw = str(rec["attrs"].get("fps") or "").strip()
    m = re.search(r"\d+(?:\.\d+)?", raw)
    return float(m.group()) if m else None


def table_rows(records, sections=("systems",)):
    """Only the main list. A decoder or a scheduler also has a frame rate, but
    putting it in a column headed 'System' invites the reader to compare it
    against an interactive system's frame rate, which is not the same number."""
    rows = [r for r in records
            if r["attrs"].get("backbone") and r["section"] in sections]
    rows.sort(key=lambda r: (r.get("date") or "", r["id"]), reverse=True)
    return rows


def short_label(rec, width=44):
    label = rec.get("name") or rec["title"].split(":")[0]
    return label if len(label) <= width else label[:width - 1].rstrip() + "…"


def cell(value):
    """A bare '|' inside a value silently eats the rest of the row."""
    return re.sub(r"\s+", " ", str(value)).replace("|", r"\|").strip()


def render_table(records, limit=None):
    rows = table_rows(records)
    shown = rows[:limit] if limit else rows
    out = ["| System | Date | Backbone | Action | FPS | Memory | Open |",
           "| --- | --- | --- | --- | --- | --- | --- |"]
    for r in shown:
        attrs = r["attrs"]
        label = cell(short_label(r))
        link = (r.get("links") or {}).get("paper")
        fps = _fps(r)
        out.append("| " + " | ".join([
            f"[{label}]({link})" if link else label,
            (r.get("date") or "")[:7],
            cell(norm_backbone(attrs["backbone"])),
            cell(norm_action(attrs.get("action_space", ""))) or "—",
            f"{fps:g}" if fps is not None else "—",
            cell(norm_memory(attrs.get("memory", ""))) or "—",
            "yes" if attrs.get("open_source") is True else "no",
        ]) + " |")
    return "\n".join(out), len(rows), len(shown)


def render_comparison_doc(records, sections):
    systems = table_rows(records)
    others = table_rows(records, tuple(s["key"] for s in sections if s["key"] != "systems"))
    titles = {s["key"]: s["title"] for s in sections}

    out = ["# System comparison (full)", "",
           "Generated by `scripts/build_readme.py` from `data/papers.jsonl` — do not edit by hand.", "",
           "Every value is taken from the paper it describes, verbatim where the phrasing matters.",
           "A missing field means the paper does not report it, not that the value is zero. Frame",
           "rates are the numbers the authors claim, on the hardware they claim them on; they are",
           "not measured here and are not comparable across rows without reading the setups.", "",
           f"{len(systems)} interactive systems, plus {len(others)} components and analyses profiled",
           "on the same axes.", ""]

    def block(rec, note=None):
        attrs = rec["attrs"]
        label = rec.get("name") or rec["title"]
        link = (rec.get("links") or {}).get("paper")
        out.append(f"### {label}" + (f" ([paper]({link}))" if link else ""))
        out.append("")
        line = f"_{rec['title']}_ — {rec.get('date') or 'n/a'}"
        out.append(line + (f" · {note}" if note else ""))
        out.append("")
        for key, name in (("backbone", "Backbone"), ("action_space", "Action space"),
                          ("fps", "Reported FPS"), ("horizon", "Horizon / context"),
                          ("memory", "Memory mechanism")):
            if attrs.get(key):
                out.append(f"- **{name}:** {attrs[key]}")
        if "open_source" in attrs:
            out.append(f"- **Open source:** {'yes' if attrs['open_source'] else 'no'}")
        out.append("")

    out.append("## Interactive systems")
    out.append("")
    for rec in systems:
        block(rec)

    if others:
        out.append("## Components and analyses")
        out.append("")
        out.append("Not interactive systems in their own right. Their numbers measure a part of "
                   "the stack and do not belong in the same column as an end-to-end frame rate.")
        out.append("")
        for rec in others:
            block(rec, note=titles.get(rec["section"], rec["section"]))
    return "\n".join(out)


def fill(template, block, body):
    pattern = re.compile(
        rf"<!-- BEGIN:{block} -->.*?<!-- END:{block} -->", re.S)
    if not pattern.search(template):
        sys.exit(f"template is missing the {block} block")
    replacement = f"<!-- BEGIN:{block} -->\n{body}\n<!-- END:{block} -->"
    return pattern.sub(lambda _: replacement, template)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify the generated files are current; write nothing")
    ap.add_argument("--table-limit", type=int, default=40,
                    help="rows kept in the README table (0 = all)")
    args = ap.parse_args()

    sections = json.loads((DATA / "sections.json").read_text(encoding="utf-8"))
    records = [json.loads(l) for l in (DATA / "papers.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    known = {s["key"] for s in sections}
    for rec in records:
        rec.setdefault("attrs", {})
        if rec["section"] not in known:
            sys.exit(f"{rec['id']}: unknown section {rec['section']!r}")

    by_section = {}
    for rec in records:
        by_section.setdefault(rec["section"], []).append(rec)
    for recs in by_section.values():
        recs.sort(key=lambda r: (r.get("date") or "", r["id"]), reverse=True)

    table, total_rows, shown_rows = render_table(
        records, args.table_limit or None)
    if total_rows > shown_rows:
        table += (f"\n\n_Showing the {shown_rows} most recent of {total_rows} profiled "
                  f"systems. Full table with horizons and verbatim action spaces: "
                  f"[docs/comparison.md](docs/comparison.md)._")

    readme = (DATA / "README.template.md").read_text(encoding="utf-8")
    readme = fill(readme, "CONTENTS", render_contents(sections, by_section))
    readme = fill(readme, "STATS", render_stats(records, sections))
    readme = fill(readme, "LIST", render_list(sections, by_section))
    readme = fill(readme, "TABLE", table)

    comparison = render_comparison_doc(records, sections)

    targets = [(ROOT / "README.md", readme),
               (ROOT / "docs" / "comparison.md", comparison)]
    if args.check:
        stale = [p.name for p, body in targets
                 if not p.exists() or p.read_text(encoding="utf-8") != body]
        if stale:
            sys.exit("stale, re-run scripts/build_readme.py: " + ", ".join(stale))
        print("[build] README.md and docs/comparison.md are current")
        return

    for path, body in targets:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    print(f"[build] {len(records)} entries -> README.md ({shown_rows}/{total_rows} table rows), "
          f"docs/comparison.md")


if __name__ == "__main__":
    main()
