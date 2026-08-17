#!/usr/bin/env python3
"""Render README.md and docs/comparison.md from data/.

data/papers.jsonl + data/tags.json + data/README.template.md -> README.md

There are no sections. One list, newest first, every paper once, each carrying
the one to three tags that say what it is. A paper is rarely about a single
thing and the reader is rarely after a single thing either; splitting the list
into buckets made both of those unsayable, and repeating a paper under every
bucket it belongs to just moved the problem. Find by tag with the browser's
find, not by scrolling to a heading.

The template owns all prose. This script only fills the marked blocks:

    <!-- BEGIN:TAGKEY -->  ... <!-- END:TAGKEY -->
    <!-- BEGIN:LIST -->    ... <!-- END:LIST -->
    <!-- BEGIN:TABLE -->   ... <!-- END:TABLE -->

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


def leading_token(value, vocabulary):
    """The controlled token a value starts with, ignoring whatever explanation
    follows it.

    These fields are supposed to hold one vocabulary token, but a contributor --
    human or agent -- reliably appends the reasoning: `retrieval — sparse
    attention over a growing KV-cache: ...`. Splitting on punctuation only works
    when the punctuation happens to come first, so match the vocabulary instead.
    The prose is not lost; comparison.md prints the field in full."""
    text = value.strip()
    for token in sorted(vocabulary, key=len, reverse=True):
        if text == token or re.match(rf"{re.escape(token)}\b", text):
            return token
    return re.split(r"\s+[-—–]\s+|[:(]", text)[0].strip()


def norm_backbone(value):
    head = leading_token(value, BACKBONE_LABELS).split("+")[0].strip()
    return BACKBONE_LABELS.get(head, head)


def _memory_atom(value):
    head = leading_token(value, MEMORY_LABELS)
    return MEMORY_LABELS.get(head, head)


def norm_memory(value):
    if value.startswith("hybrid"):
        rest = value.split(":", 1)[1] if ":" in value else ""
        # Stop at the first separator so an explanation after the pair does not
        # become a third "component".
        rest = re.split(r"\s+[-—–]\s+|[;.]", rest)[0]
        labels = [_memory_atom(p) for p in rest.split("+") if p.strip()]
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


def entry_line(rec, icons=None):
    """One bullet, ending in its tags. The tags are the only thing saying what
    the paper is about, so every one of them is on the line."""
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
    tags = rec.get("tags") or []
    if tags:
        icons = icons or {}
        parts.append("·")
        parts += [f"{icons.get(t, '')}`{t}`".strip() for t in tags]
    return " ".join(parts)


def render_list(records, icons=None):
    """Every paper once, newest first."""
    rows = sorted(records, key=lambda r: (r.get("date") or "", r["id"]), reverse=True)
    return "\n".join(entry_line(r, icons) for r in rows)


def render_tag_key(tags):
    """What each tag means, with the glyph that stands for it in the list.

    A key, not a table of contents -- there is nothing to jump to, because the
    list is not divided. The glyph earns its place by being searchable: every
    tag name is also an English word that appears in titles, so finding the
    control papers means searching for 🕹️, not for "control"."""
    return "\n".join(f"- {tag['icon']} **`{tag['key']}`** — {tag['blurb']}"
                     for tag in tags)


def _fps(rec):
    raw = str(rec["attrs"].get("fps") or "").strip()
    m = re.search(r"\d+(?:\.\d+)?", raw)
    return float(m.group()) if m else None


def table_rows(records, tags=("systems",), without=()):
    """Only the main list. A decoder or a scheduler also has a frame rate, but
    putting it in a column headed 'System' invites the reader to compare it
    against an interactive system's frame rate, which is not the same number.

    `without` exists because tags overlap: almost every system also carries a
    tech tag, so "everything that is not a system" has to be said by exclusion
    rather than by listing the other tags."""
    rows = [r for r in records
            if r["attrs"].get("backbone")
            and set(r.get("tags", [])) & set(tags)
            and not set(r.get("tags", [])) & set(without)]
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


def render_comparison_doc(records, tags):
    systems = table_rows(records)
    others = table_rows(records,
                        tuple(t["key"] for t in tags if t["key"] != "systems"),
                        without=("systems",))
    titles = {t["key"]: t["title"] for t in tags}

    out = ["# System comparison (full)", "",
           "Generated by `scripts/build_readme.py` from `data/papers.jsonl` — do not edit by hand.", "",
           "Every value is taken from the paper it describes, verbatim where the phrasing matters.",
           "A missing field means the paper does not report it, not that the value is zero. Frame",
           "rates are the numbers the authors claim, on the hardware they claim them on; they are",
           "not measured here and are not comparable across rows without reading the setups.", ""]

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
        evidence = rec.get("evidence") or {}
        if evidence:
            out.append("")
            out.append("<details><summary>Where these came from</summary>")
            out.append("")
            for key in ("fps", "horizon", "memory", "backbone", "action_space"):
                if evidence.get(key):
                    out.append(f"- **{key}:** {evidence[key]}")
            out.append("")
            out.append("</details>")
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
            note = " · ".join(titles.get(t, t) for t in rec.get("tags", []))
            block(rec, note=note or None)
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

    tags = json.loads((DATA / "tags.json").read_text(encoding="utf-8"))
    records = [json.loads(l) for l in (DATA / "papers.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    known = {t["key"] for t in tags}
    for rec in records:
        rec.setdefault("attrs", {})
        if not rec.get("tags"):
            sys.exit(f"{rec['id']}: no tags")
        for tag in rec["tags"]:
            if tag not in known:
                sys.exit(f"{rec['id']}: unknown tag {tag!r}")

    table, total_rows, shown_rows = render_table(
        records, args.table_limit or None)
    if total_rows > shown_rows:
        table += ("\n\n_Most recent systems only. Full table, with horizons and verbatim "
                  "action spaces: [docs/comparison.md](docs/comparison.md)._")

    readme = (DATA / "README.template.md").read_text(encoding="utf-8")
    icons = {t["key"]: t["icon"] for t in tags}
    readme = fill(readme, "TAGKEY", render_tag_key(tags))
    readme = fill(readme, "LIST", render_list(records, icons))
    readme = fill(readme, "TABLE", table)

    comparison = render_comparison_doc(records, tags)

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
