#!/usr/bin/env python3
"""Turn the ticked candidates in the inbox Issue into data/papers.jsonl records.

The README is generated, so nothing here edits markdown: new records are
appended to the data file and scripts/build_readme.py renders the result. That
is the whole reason this pipeline cannot corrupt the list -- the worst a bad
parse can do is add a row.

Prints the number of records added, for the workflow to branch on.

Usage:
  python3 scripts/apply_issue_selections.py --issue-body body.md \
      --summary-output summary.md
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sources import CANDIDATE_RE, decode, source_of, url_for  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def parse_selections(issue_body, valid_sections):
    """-> (records, warnings). Skips anything malformed rather than guessing."""
    records, warnings, seen = [], [], set()
    for match in CANDIDATE_RE.finditer(issue_body):
        if match.group("checked").lower() != "x":
            continue
        payload = decode(match.group("payload"))
        if not payload or "id" not in payload:
            warnings.append("skipped a ticked line with unreadable metadata")
            continue
        pid = payload["id"]
        if pid in seen:
            continue
        seen.add(pid)
        section = match.group("section")
        if section not in valid_sections:
            warnings.append(
                f"{pid}: `{section}` is not a known section, "
                f"fell back to `{payload.get('section')}`")
            section = payload.get("section")
        if section not in valid_sections:
            warnings.append(f"{pid}: no usable section, skipped")
            continue
        url = url_for(pid, payload.get("url"))
        if not url:
            warnings.append(f"{pid}: no usable link, skipped")
            continue
        # A blog post is not a paper, and the README renders the two under
        # different labels. `origin` carries the venue an inbox source knew
        # about -- "NeurIPS 2025 poster" -- which is exactly the field a
        # hand-added record would have had to be looked up by hand.
        link_key = "blog" if source_of(pid) == "blog" else "paper"
        records.append({
            "id": pid,
            "name": payload.get("name"),
            "title": payload.get("title", "").strip(),
            "venue": payload.get("origin"),
            "date": payload.get("date"),
            "section": section,
            "section_source": "curated",
            "links": {link_key: url},
            "attrs": {},
        })
    return records, warnings


def write_summary(path, added, skipped, warnings):
    lines = [f"Added **{len(added)}** paper(s) from the review inbox.", ""]
    for rec in added:
        label = rec["name"] or rec["title"]
        link = next(iter(rec["links"].values()), "")
        lines.append(f"- `{rec['section']}` — [{label}]({link})")
    if skipped:
        lines += ["", f"Already in the list, skipped: {', '.join(sorted(skipped))}."]
    if warnings:
        lines += ["", "Warnings:"] + [f"- {w}" for w in warnings]
    lines += ["", "`README.md` and `docs/comparison.md` were regenerated from "
              "`data/papers.jsonl`. Attributes for the comparison table are added "
              "by hand after someone reads the paper."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue-body", type=Path, required=True)
    ap.add_argument("--papers", type=Path, default=ROOT / "data" / "papers.jsonl")
    ap.add_argument("--sections", type=Path, default=ROOT / "data" / "sections.json")
    ap.add_argument("--summary-output", type=Path)
    args = ap.parse_args()

    valid = {s["key"] for s in json.loads(args.sections.read_text(encoding="utf-8"))}
    body = args.issue_body.read_text(encoding="utf-8")
    selected, warnings = parse_selections(body, valid)

    existing = []
    if args.papers.exists():
        existing = [json.loads(l) for l in args.papers.read_text(encoding="utf-8").splitlines() if l.strip()]
    have = {r["id"] for r in existing}

    added = [r for r in selected if r["id"] not in have]
    skipped = {r["id"] for r in selected if r["id"] in have}

    if added:
        merged = existing + added
        merged.sort(key=lambda r: (r.get("date") or "", r["id"]), reverse=True)
        args.papers.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in merged),
            encoding="utf-8")

    if args.summary_output:
        write_summary(args.summary_output, added, skipped, warnings)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(len(added))


if __name__ == "__main__":
    main()
