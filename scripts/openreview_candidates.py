#!/usr/bin/env python3
"""Propose papers from OpenReview: ICLR, NeurIPS, ICML and their workshops.

This is a **sweep, not a daily tick**, and that is forced by the API rather than
chosen. `/notes?content.venueid=...` is behind a bot challenge, so the only
reachable endpoint is `/notes/search`, which ranks by relevance and ignores
`sort` -- there is no way to ask it for "everything since Tuesday". What it can
answer is "everything it knows about interactive video world models", which is
the right question to ask a few times a year rather than every morning.

What it finds that arXiv does not:

- Papers that were never posted to arXiv at all.
- The venue. arXiv knows a paper's id, not that it became an ICLR spotlight;
  285 of this list's 409 records carry no venue.
- Dedicated workshops. `ICLR 2026 Workshop World Models` and `CVPR 2026 Workshop
  VideoWorldModel` are this list's subject matter with a URL.

Deduplication is by **normalised title**, not id: nearly every hit here is also
on arXiv under a completely different identifier.

Usage:
  python3 scripts/openreview_candidates.py --output -
  python3 scripts/openreview_candidates.py --venue-re 'ICLR\\.cc/2026' --output -
  python3 scripts/openreview_candidates.py --include-submissions --limit 40
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sources  # noqa: E402
import triage  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEARCH_URL = "https://api2.openreview.net/notes/search"
PAGE_SIZE = 100
MIN_DELAY_S = 1.0
USER_AGENT = "awesome-interactive-video-world-models/1.0 (+https://github.com/)"

# The search index reaches past OpenReview's own venues into re-indexed DBLP
# records, journal entries and `OpenReview.net/Archive` uploads, whose metadata
# is thin and whose acceptance status is unknowable. Restrict to venues whose
# review process this list can actually name.
VENUE_RE = re.compile(
    r"^(?:ICLR\.cc|NeurIPS\.cc|ICML\.cc|robot-learning\.org|RLC\.cc|"
    r"thecvf\.com|eccv\.ecva\.net|SIGGRAPH\.org)/", re.I)

# `venue` is prose written by the venue itself: "ICLR 2026 Poster", "ICML 2026
# spotlight", "NeurIPS 2025 Workshop EWM Oral". These four phrasings mean the
# paper is not in the proceedings, and a curated list should not imply it is.
# An anonymous submission under review can also still be withdrawn.
NOT_ACCEPTED_RE = re.compile(
    r"submitted to|under review|withdrawn|desk reject|rejected", re.I)

# A workshop paper is worth proposing -- the World Models workshops are this
# list's subject -- but when the same title is present as both, the conference
# record is the one to keep.
WORKSHOP_RE = re.compile(r"workshop", re.I)


# --- API ---------------------------------------------------------------------

def search(query, offset, limit, timeout, retries, retry_delay):
    params = urllib.parse.urlencode({"query": query, "limit": limit, "offset": offset})
    request = urllib.request.Request(f"{SEARCH_URL}?{params}",
                                     headers={"User-Agent": USER_AGENT})
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return json.loads(resp.read())
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            last = exc
            if attempt < retries:
                time.sleep(retry_delay * (attempt + 1))
    raise SystemExit(f"OpenReview search failed after {retries + 1} attempts: {last}")


def value(note, key):
    """OpenReview API v2 wraps every content field as {"value": ...}."""
    field = (note.get("content") or {}).get(key)
    if isinstance(field, dict):
        return field.get("value")
    return field


def note_date(note):
    """-> YYYY-MM-DD. Publication date if the venue set one, else creation."""
    stamp = note.get("pdate") or note.get("cdate") or note.get("tcdate")
    if not stamp:
        return None
    return datetime.fromtimestamp(stamp / 1000, timezone.utc).strftime("%Y-%m-%d")


def fetch_notes(phrases, pages, timeout, retries, retry_delay):
    """-> {forum_id: note} across every phrase, deduplicated by forum."""
    notes = {}
    for phrase in phrases:
        for page in range(pages):
            payload = search(f'"{phrase}"', page * PAGE_SIZE, PAGE_SIZE,
                             timeout, retries, retry_delay)
            batch = payload.get("notes") or []
            for note in batch:
                notes.setdefault(note.get("forum") or note["id"], note)
            if len(batch) < PAGE_SIZE:
                break
            time.sleep(MIN_DELAY_S)
        time.sleep(MIN_DELAY_S)
    return notes


# --- refetch -----------------------------------------------------------------

def fill_abstracts(candidates):
    """Inbox bodies carry no abstract, and `/notes?id=` is challenge-walled, so
    the only way back to one is to search for the exact title."""
    for cand in candidates:
        title = cand.get("title") or ""
        if not title:
            continue
        payload = search(f'"{title}"', 0, 5, 60.0, 2, 5.0)
        want = cand["id"].split(":", 1)[-1]
        for note in payload.get("notes") or []:
            if (note.get("forum") or note.get("id")) == want or \
                    sources.norm_title(value(note, "title")) == sources.norm_title(title):
                cand["abstract"] = value(note, "abstract") or ""
                cand.setdefault("date", note_date(note))
                break
        time.sleep(MIN_DELAY_S)
    return candidates


# --- report ------------------------------------------------------------------

def render(candidates, sections, swept):
    lines = [
        "## Review OpenReview candidates",
        "",
        f"{len(candidates)} paper(s) from {swept} OpenReview record(s), "
        "strongest evidence first.",
        "",
        "These are matched against the list by **title**, not by id — a paper "
        "here may already be present under its arXiv id if the titles differ. "
        "Tick what belongs; the section in backticks is a keyword guess and your "
        "edit wins. Comment `/create-pr` when done.",
        "",
        f"Valid sections: {', '.join(f'`{s}`' for s in sections)}.",
        "",
        "The venue shown is what OpenReview reports, and it is recorded on the "
        "entry — this is the one source here that knows a paper became a "
        "spotlight rather than a preprint.",
        "",
        "---",
        "",
    ]
    return "\n".join(lines + sources.render_candidates(candidates)) + "\n"


# --- main --------------------------------------------------------------------

def parse_args():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", default="OPENREVIEW_CANDIDATES.md",
                    help="'-' writes the report to stdout")
    ap.add_argument("--pages", type=int, default=3,
                    help=f"pages of {PAGE_SIZE} to pull per phrase")
    ap.add_argument("--limit", type=int, default=60,
                    help="most candidates to propose in one sweep")
    ap.add_argument("--venue-re", default=None,
                    help="override the venue whitelist, e.g. 'ICLR\\.cc/2026'")
    ap.add_argument("--include-submissions", action="store_true",
                    help="also propose papers under review, which may be withdrawn "
                         "and carry no venue")
    ap.add_argument("--papers", type=Path, default=ROOT / "data" / "papers.jsonl")
    ap.add_argument("--sections", type=Path, default=ROOT / "data" / "sections.json")
    ap.add_argument("--ignore", type=Path, default=ROOT / "data" / "arxiv-ignore.txt")
    ap.add_argument("--rejected", type=Path,
                    default=ROOT / "data" / "agent-rejected.jsonl")
    ap.add_argument("--existing-issue-body", type=Path,
                    help="current inbox body; ticks and section edits are preserved")
    ap.add_argument("--notes-file", type=Path,
                    help="read a saved search response instead of calling the API")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--retry-delay", type=float, default=5.0)
    return ap.parse_args()


def collect(notes, known_ids, known_titles, overrides, venue_re, accepted_only):
    """-> [candidate], best evidence first, one per title."""
    by_title = {}
    for forum, note in notes.items():
        title, abstract = value(note, "title"), value(note, "abstract")
        venue, venueid = value(note, "venue") or "", value(note, "venueid") or ""
        # Reviews, comments and rebuttals are notes too; only submissions carry
        # both a title and an abstract.
        if not title or not abstract:
            continue
        if not venue_re.search(venueid):
            continue
        if accepted_only and NOT_ACCEPTED_RE.search(venue):
            continue
        pid = f"openreview:{forum}"
        key = sources.norm_title(title)
        if pid in known_ids or key in known_titles:
            continue
        propose, section, met, evidence = sources.proposal(title, abstract)
        if not propose:
            continue
        cand = {
            "id": pid,
            "name": triage.extract_name(title),
            "title": title,
            "date": note_date(note),
            "section": overrides.get(pid, section),
            "met": met,
            "evidence": evidence,
            "url": f"https://openreview.net/forum?id={forum}",
            "origin": venue or None,
        }
        # One title, one candidate: the same paper is routinely both a workshop
        # poster and a conference paper, and the conference record is the one
        # whose venue is worth recording.
        previous = by_title.get(key)
        if previous is None or (WORKSHOP_RE.search(previous.get("origin") or "")
                                and not WORKSHOP_RE.search(venue)):
            by_title[key] = cand
    return sorted(by_title.values(),
                  key=lambda c: (c["met"], c["date"] or "", c["id"]), reverse=True)


def main():
    args = parse_args()
    sections = [s["key"] for s in json.loads(args.sections.read_text(encoding="utf-8"))]
    venue_re = re.compile(args.venue_re, re.I) if args.venue_re else VENUE_RE

    if args.notes_file:
        payload = json.loads(args.notes_file.read_text(encoding="utf-8"))
        notes = {n.get("forum") or n["id"]: n for n in payload.get("notes", payload)}
    else:
        notes = fetch_notes(sources.QUERY_PHRASES, args.pages, args.timeout,
                            args.retries, args.retry_delay)

    issue_body = (args.existing_issue_body.read_text(encoding="utf-8")
                  if args.existing_issue_body and args.existing_issue_body.exists() else "")
    known_ids = (sources.known_ids(args.papers) | sources.ignored_ids(args.ignore)
                 | sources.rejected_ids(args.rejected))
    candidates = collect(notes, known_ids, sources.known_titles(args.papers),
                         sources.edited_sections(issue_body), venue_re,
                         not args.include_submissions)

    if len(candidates) > args.limit:
        print(f"note: {len(candidates)} candidates found, proposing the "
              f"{args.limit} with the strongest evidence; re-run after merging "
              f"to see the rest", file=sys.stderr)
        candidates = candidates[:args.limit]

    report = sources.retick(render(candidates, sections, len(notes)),
                            sources.checked_ids(issue_body))
    if args.output == "-":
        sys.stdout.write(report)
        print(len(candidates), file=sys.stderr)
    else:
        Path(args.output).write_text(report, encoding="utf-8")
        print(len(candidates))


if __name__ == "__main__":
    main()
