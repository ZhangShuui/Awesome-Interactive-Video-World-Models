#!/usr/bin/env python3
"""Check data/papers.jsonl before it reaches the README.

Errors fail the build. Warnings are review debt -- notably `section_source:
rule` entries, whose section came from a keyword guess and has never been
confirmed by a human.

Usage:
  python3 scripts/validate.py
  python3 scripts/validate.py --review        # list the unreviewed sections
  python3 scripts/validate.py --review memory # ... in one section
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ("id", "title", "section", "links")
ARXIV_ID_RE = re.compile(r"^\d{4}\.\d{4,5}$")
DATE_RE = re.compile(r"^\d{4}(-\d{2}-\d{2})?$")
URL_RE = re.compile(r"^https?://\S+$")
KNOWN_LINKS = {"paper", "website", "code", "blog"}


def load(path):
    records = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append((lineno, json.loads(line)))
        except json.JSONDecodeError as exc:
            sys.exit(f"data/papers.jsonl:{lineno}: not valid JSON — {exc}")
    return records


def check(records, sections):
    errors, warnings, seen = [], [], {}
    for lineno, rec in records:
        where = f"line {lineno}"
        missing = [f for f in REQUIRED if not rec.get(f)]
        if missing:
            errors.append(f"{where}: missing {', '.join(missing)}")
            continue
        pid = rec["id"]
        where = f"{pid} (line {lineno})"
        if pid in seen:
            errors.append(f"{where}: duplicate of line {seen[pid]}")
        seen[pid] = lineno

        if rec["section"] not in sections:
            errors.append(f"{where}: unknown section {rec['section']!r}")

        date = rec.get("date") or ""
        if date and not DATE_RE.match(date):
            errors.append(f"{where}: date {date!r} is not YYYY-MM-DD or YYYY")

        links = rec.get("links") or {}
        for key, url in links.items():
            if key not in KNOWN_LINKS:
                warnings.append(f"{where}: unusual link type {key!r}")
            if not URL_RE.match(str(url)):
                errors.append(f"{where}: {key} link is not a URL: {url!r}")

        if ARXIV_ID_RE.match(pid):
            paper = links.get("paper", "")
            if pid not in paper:
                errors.append(f"{where}: paper link {paper!r} does not point at {pid}")
        elif ":" not in pid:
            errors.append(f"{where}: non-arXiv ids need a prefix, e.g. 'blog:{pid}'")
        elif not links:
            errors.append(f"{where}: non-arXiv entries need at least one link")

        if "`" in (rec.get("name") or ""):
            errors.append(f"{where}: name contains a backtick, which breaks the entry")

        if not isinstance(rec.get("attrs", {}), dict):
            errors.append(f"{where}: attrs must be an object")
    return errors, warnings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--papers", type=Path, default=ROOT / "data" / "papers.jsonl")
    ap.add_argument("--sections", type=Path, default=ROOT / "data" / "sections.json")
    ap.add_argument("--review", nargs="?", const="*", metavar="SECTION",
                    help="list entries whose section is an unconfirmed keyword guess")
    args = ap.parse_args()

    sections = {s["key"] for s in json.loads(args.sections.read_text(encoding="utf-8"))}
    records = load(args.papers)
    errors, warnings = check(records, sections)

    if args.review:
        pending = [r for _, r in records
                   if r.get("section_source") == "rule"
                   and (args.review == "*" or r.get("section") == args.review)]
        pending.sort(key=lambda r: (r["section"], r.get("date") or ""), reverse=True)
        for rec in pending:
            print(f"{rec['section']:<11} {rec['id']:<11} {rec['title'][:88]}")
        print(f"\n{len(pending)} entr{'y' if len(pending) == 1 else 'ies'} "
              f"still on a keyword-suggested section.")
        return

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        sys.exit(f"\n{len(errors)} error(s) in data/papers.jsonl")

    unreviewed = sum(1 for _, r in records if r.get("section_source") == "rule")
    print(f"[validate] {len(records)} records, {len(sections)} sections, no errors")
    if unreviewed:
        print(f"[validate] {unreviewed} on a keyword-suggested section "
              f"(scripts/validate.py --review)")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:  # piping --review into head is normal usage
        sys.stderr.close()
