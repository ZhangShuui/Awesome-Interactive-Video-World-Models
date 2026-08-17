#!/usr/bin/env python3
"""Check data/papers.jsonl before it reaches the README.

Errors fail the build. Warnings are review debt -- notably tags whose
`tags_source` is `rule`, meaning they came from a keyword guess and have never
been confirmed by a human. Provenance is per tag: a paper can be a system
because someone read it and carry `control` because a rule guessed.

Usage:
  python3 scripts/validate.py
  python3 scripts/validate.py --review        # list the unreviewed tags
  python3 scripts/validate.py --review memory # ... for one tag
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ("id", "title", "tags", "links")
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


def check(records, known_tags):
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

        tags = rec.get("tags")
        if not isinstance(tags, list):
            errors.append(f"{where}: tags must be a list")
        else:
            if len(set(tags)) != len(tags):
                errors.append(f"{where}: duplicate tag in {tags!r}")
            for tag in tags:
                if tag not in known_tags:
                    errors.append(f"{where}: unknown tag {tag!r}")
            source = rec.get("tags_source") or {}
            if not isinstance(source, dict):
                errors.append(f"{where}: tags_source must be an object keyed by tag")
            else:
                # A tag with no recorded provenance reads as confirmed, so an
                # unconfirmed one would quietly leave the review queue.
                for tag in tags:
                    if tag not in source:
                        errors.append(f"{where}: tag {tag!r} has no tags_source")
                for tag in source:
                    if tag not in tags:
                        errors.append(f"{where}: tags_source has {tag!r}, which is not a tag")

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
    ap.add_argument("--tags", type=Path, default=ROOT / "data" / "tags.json")
    ap.add_argument("--review", nargs="?", const="*", metavar="TAG",
                    help="list tags that were not settled by a human")
    args = ap.parse_args()

    unconfirmed = {"rule", "agent"}

    known_tags = {t["key"] for t in json.loads(args.tags.read_text(encoding="utf-8"))}
    records = load(args.papers)
    errors, warnings = check(records, known_tags)

    if args.review:
        pending = [(rec, tag) for _, rec in records
                   for tag, src in (rec.get("tags_source") or {}).items()
                   if src in unconfirmed
                   and (args.review == "*" or tag == args.review)]
        pending.sort(key=lambda p: (p[1], p[0].get("date") or ""), reverse=True)
        for rec, tag in pending:
            print(f"{rec['tags_source'][tag]:<6} {tag:<11} "
                  f"{rec['id']:<11} {rec['title'][:80]}")
        print(f"\n{len(pending)} tag{'' if len(pending) == 1 else 's'} "
              f"placed by a keyword rule or a review agent, not by a human.")
        return

    for warning in warnings:
        print(f"warning: {warning}")
    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        sys.exit(f"\n{len(errors)} error(s) in data/papers.jsonl")

    pending = sum(1 for _, r in records
                  for src in (r.get("tags_source") or {}).values()
                  if src in unconfirmed)
    assigned = sum(len(r.get("tags") or []) for _, r in records)
    print(f"[validate] {len(records)} records, {assigned} tag assignments across "
          f"{len(known_tags)} tags, no errors")
    if pending:
        print(f"[validate] {pending} tag(s) not yet confirmed by a human "
              f"(scripts/validate.py --review)")


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:  # piping --review into head is normal usage
        sys.stderr.close()
