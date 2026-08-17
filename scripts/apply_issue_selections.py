#!/usr/bin/env python3
"""Turn the reviewed candidates in the inbox Issue into data files.

Two boxes, two destinations. Ticked papers become data/papers.jsonl records;
crossed ones become data/maintainer-rejected.jsonl lines so the pipeline stops
proposing them. Both have to be written here, in the one place the maintainer
reaches by commenting /create-pr, because the Issue body is rewritten daily and
is nobody's record of anything.

The README is generated, so nothing here edits markdown: new records are
appended to the data file and scripts/build_readme.py renders the result. That
is the whole reason this pipeline cannot corrupt the list -- the worst a bad
parse can do is add a row.

Prints the number of changes -- papers added plus papers rejected -- for the
workflow to branch on.

Usage:
  python3 scripts/apply_issue_selections.py --issue-body body.md \
      --summary-output summary.md
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sources import (CANDIDATE_RE, decode, parse_tags,  # noqa: E402
                     rejected_in_issue, source_of, url_for)

ROOT = Path(__file__).resolve().parent.parent


def parse_selections(issue_body, valid_tags, tag_order):
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
        # An unknown tag is dropped on its own rather than taking the whole
        # line with it: a maintainer adding `systems,contorl` should still get
        # the paper, with one complaint, not silence.
        typed = parse_tags(match.group("tags"))
        tags = [t for t in typed if t in valid_tags]
        for bad in [t for t in typed if t not in valid_tags]:
            warnings.append(f"{pid}: `{bad}` is not a known tag, dropped")
        if not tags:
            tags = [t for t in (payload.get("tags") or []) if t in valid_tags]
            if tags:
                warnings.append(f"{pid}: no usable tag typed, kept {','.join(tags)}")
        if not tags:
            warnings.append(f"{pid}: no usable tag, skipped")
            continue
        tags.sort(key=tag_order.index)
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
            "tags": tags,
            # Every tag on a ticked line was seen by the person who ticked it.
            "tags_source": {t: "curated" for t in tags},
            "links": {link_key: url},
            "attrs": {},
        })
    return records, warnings


def parse_rejections(issue_body, records):
    """-> ([{id, title, date}], warnings) for every crossed candidate.

    A paper both ticked and crossed is a contradiction only the maintainer can
    settle. Honouring the cross would throw away the tick, so the tick wins and
    the disagreement is reported instead of resolved quietly.
    """
    crossed = rejected_in_issue(issue_body)
    ticked = {r["id"] for r in records}
    out, warnings, seen = [], [], set()
    for match in CANDIDATE_RE.finditer(issue_body):
        payload = decode(match.group("payload"))
        if not payload or "id" not in payload:
            continue
        pid = payload["id"]
        if pid not in crossed or pid in seen:
            continue
        seen.add(pid)
        if pid in ticked:
            warnings.append(f"{pid}: ticked and crossed at once; kept the tick")
            continue
        out.append({"id": pid, "title": payload.get("title", "").strip(),
                    "date": payload.get("date")})
    return out, warnings


def write_summary(path, added, skipped, rejected, warnings):
    lines = [f"Added **{len(added)}** paper(s) from the review inbox.", ""]
    for rec in added:
        label = rec["name"] or rec["title"]
        link = next(iter(rec["links"].values()), "")
        lines.append(f"- {' '.join(f'`{t}`' for t in rec['tags'])} — [{label}]({link})")
    if rejected:
        lines += ["", f"Crossed out, and recorded in "
                      f"`data/maintainer-rejected.jsonl` so they stop coming back "
                      f"(**{len(rejected)}**):", ""]
        lines += [f"- `{r['id']}` — {r['title']}" for r in rejected]
    if skipped:
        lines += ["", f"Already in the list, skipped: {', '.join(sorted(skipped))}."]
    if warnings:
        lines += ["", "Warnings:"] + [f"- {w}" for w in warnings]
    lines += ["", "`README.md` and `docs/comparison.md` were regenerated from "
              "`data/papers.jsonl`. Attributes for the comparison table are added "
              "by hand after someone reads the paper."]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def append_rejections(path, rejected):
    """-> the ones that were not already recorded. Append-only and idempotent,
    so re-running /create-pr on the same body is a no-op rather than a pile of
    duplicate lines."""
    have = {r["id"] for r in _existing_rejections(path)}
    fresh = [r for r in rejected if r["id"] not in have]
    if fresh:
        with path.open("a", encoding="utf-8") as fh:
            for rec in fresh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return fresh


def _existing_rejections(path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.lstrip().startswith("#")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue-body", type=Path, required=True)
    ap.add_argument("--papers", type=Path, default=ROOT / "data" / "papers.jsonl")
    ap.add_argument("--tags", type=Path, default=ROOT / "data" / "tags.json")
    ap.add_argument("--maintainer-rejected", type=Path,
                    default=ROOT / "data" / "maintainer-rejected.jsonl")
    ap.add_argument("--summary-output", type=Path)
    args = ap.parse_args()

    order = [t["key"] for t in json.loads(args.tags.read_text(encoding="utf-8"))]
    body = args.issue_body.read_text(encoding="utf-8")
    selected, warnings = parse_selections(body, set(order), order)

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

    rejected, conflicts = parse_rejections(body, selected)
    warnings += conflicts
    rejected_new = append_rejections(args.maintainer_rejected, rejected)

    if args.summary_output:
        write_summary(args.summary_output, added, skipped, rejected_new, warnings)
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)
    print(len(added) + len(rejected_new))


if __name__ == "__main__":
    main()
