#!/usr/bin/env python3
"""Propose recent arXiv papers for review, as a checkbox inbox.

Recall is phrase-based, not title-based. The systems that matter most to this
list are named Genie, Oasis, DIAMOND -- searching titles for "world" misses all
of them, so the query set covers the vocabulary of the field and the three
scope criteria do the narrowing afterwards.

Output is one markdown report meant to live in a single GitHub Issue. Each
candidate carries its metadata base64-encoded in an HTML comment; the section
in backticks on the visible line is editable and wins.

Usage:
  python3 scripts/arxiv_candidates.py --days 7
  python3 scripts/arxiv_candidates.py --feed-file tests/data/feed.xml --output -
"""
import argparse
import json
import random
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sources  # noqa: E402
import triage  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}
PAGE_SIZE = 100
MIN_DELAY_S = 3.1
USER_AGENT = "awesome-interactive-video-world-models/1.0 (+https://github.com/)"

# A paper passes on *any* of its categories, so this only excludes work that
# never cross-listed into vision or learning at all.
#
# cs.RO and cs.GR were dropped deliberately. This list is about generated video
# you can act inside, not about robots or renderers, and the two categories were
# paying their way in noise rather than papers: robotics contributes grasp-force,
# contact-force and force-torque work that talks about scenes and images and so
# clears the visual gate, and a pure-graphics paper with no vision cross-listing
# is a renderer, not a world model. Robotics world models that matter here are
# cross-listed cs.CV or cs.LG and still arrive.
ALLOWED_CATEGORIES = {"cs.CV", "cs.LG", "cs.AI", "cs.MM", "eess.IV"}

# The field's vocabulary lives in sources.py, shared with every other source.
# Every phrase is OR'd into one query here, so an extra phrase costs no extra
# API call -- only precision, which the gates and the review agent absorb.
QUERY_PHRASES = sources.QUERY_PHRASES

ARXIV_ID_RE = re.compile(r"arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})", re.I)


# --- arXiv API ---------------------------------------------------------------

def build_query(start, end):
    phrases = " OR ".join(f'all:"{p}"' for p in QUERY_PHRASES)
    window = f"submittedDate:[{start:%Y%m%d%H%M} TO {end:%Y%m%d%H%M}]"
    return f"({phrases}) AND {window}"


def parse_feed(payload):
    root = ET.fromstring(payload)
    out = []
    for entry in root.findall("a:entry", NS):
        raw_id = (entry.findtext("a:id", "", NS) or "").strip()
        m = re.search(r"abs/(\d{4}\.\d{4,5})", raw_id)
        if not m:
            continue
        out.append({
            "id": m.group(1),
            "title": re.sub(r"\s+", " ", entry.findtext("a:title", "", NS)).strip(),
            "abstract": re.sub(r"\s+", " ", entry.findtext("a:summary", "", NS)).strip(),
            "date": (entry.findtext("a:published", "", NS) or "")[:10],
            "categories": sorted({c.get("term") for c in entry.findall("a:category", NS)}),
        })
    return out


# Being rate-limited is not the same failure as a flaky socket and must not
# share its budget. arXiv limits by IP, and a GitHub Actions runner shares its
# address with everything else on that subnet, so the scheduled run collects
# 429s a laptop never sees. The 5s/10s backoff that covers a dropped connection
# gave up fifteen seconds into a limit measured in minutes -- and a lost run is
# a lost day of recall, silently, because the 3-day window only tolerates two.
#
# The first version of this budget waited 30/60/90/120s and still lost 08-13,
# 08-15 and 08-16: growing linearly spends most of the patience on the early
# attempts, and arXiv was flatly refusing six minutes in. Doubling reaches the
# ceiling in half the attempts and then sits there, which buys a quarter of an
# hour from seven. Each wait is jittered down by up to a quarter so that a
# runner subnet throttled in lockstep does not re-collide on the way back.
RATE_LIMIT_RETRIES = 7
RATE_LIMIT_BACKOFF_S = 30.0
RATE_LIMIT_MAX_WAIT_S = 300.0
RATE_LIMIT_JITTER = 0.25


def backoff_for(throttled):
    """The n-th rate-limit wait: exponential, capped, jittered downward."""
    base = min(RATE_LIMIT_BACKOFF_S * 2 ** (throttled - 1), RATE_LIMIT_MAX_WAIT_S)
    return base * (1.0 - RATE_LIMIT_JITTER * random.random())


def retry_after(exc):
    """How long the server asked us to wait, if it said. Seconds or HTTP-date."""
    headers = getattr(exc, "headers", None)
    raw = headers.get("Retry-After") if headers else None
    if not raw:
        return None
    raw = raw.strip()
    try:
        return min(float(raw), RATE_LIMIT_MAX_WAIT_S)
    except ValueError:
        pass
    try:
        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    delay = (when - datetime.now(when.tzinfo or timezone.utc)).total_seconds()
    return min(max(delay, 0.0), RATE_LIMIT_MAX_WAIT_S)


def fetch_page(query, start, max_results, timeout, retries, retry_delay):
    params = urllib.parse.urlencode({
        "search_query": query, "start": start, "max_results": max_results,
        "sortBy": "submittedDate", "sortOrder": "descending",
    })
    request = urllib.request.Request(f"{API_URL}?{params}",
                                     headers={"User-Agent": USER_AGENT})
    last, failures, throttled = None, 0, 0
    while True:
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code == 429:
                throttled += 1
                if throttled > RATE_LIMIT_RETRIES:
                    break
                wait = retry_after(exc) or backoff_for(throttled)
                print(f"arXiv rate-limited this request; waiting {wait:.0f}s "
                      f"({throttled}/{RATE_LIMIT_RETRIES})", file=sys.stderr)
                time.sleep(wait)
                continue
            failures += 1
            if failures > retries:
                break
            time.sleep(retry_delay * failures)
        except (urllib.error.URLError, TimeoutError, ET.ParseError) as exc:
            last = exc
            failures += 1
            if failures > retries:
                break
            time.sleep(retry_delay * failures)
    raise SystemExit(f"arXiv API request failed after {failures + throttled} "
                     f"attempt(s): {last}")


TOTAL_RE = re.compile(r"<opensearch:totalResults[^>]*>(\d+)<")


def total_results(payload):
    """How many papers the window actually holds, as arXiv reports it."""
    match = TOTAL_RE.search(payload.decode("utf-8", "replace"))
    return int(match.group(1)) if match else None


def fetch_papers(days, max_results, timeout, retries, retry_delay):
    end = datetime.now(timezone.utc)
    query = build_query(end - timedelta(days=days), end)
    papers, start, total = [], 0, None
    while start < max_results:
        page = fetch_page(query, start, min(PAGE_SIZE, max_results - start),
                          timeout, retries, retry_delay)
        if total is None:
            total = total_results(page)
        batch = parse_feed(page)
        papers.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE
        time.sleep(MIN_DELAY_S)
    # A daily 3-day window returns a couple of dozen papers and never comes near
    # the cap. A hand-run backfill over a month does: the window silently lost
    # its oldest papers and the report looked complete. Say so.
    if total is not None and total > max_results:
        print(f"warning: the {days}-day window holds {total} papers but "
              f"--max-results is {max_results}; {total - max_results} were not "
              f"fetched. Re-run with --max-results {total} or a shorter window.",
              file=sys.stderr)
    return papers


def fill_abstracts(candidates, timeout=60.0, retries=2, retry_delay=5.0):
    """Refetch abstracts for inbox candidates, 50 ids per request."""
    missing = [c for c in candidates if not c.get("abstract")]
    for start in range(0, len(missing), 50):
        batch = missing[start:start + 50]
        query = " OR ".join(f"id:{c['id']}" for c in batch)
        by_id = {p["id"]: p for p in parse_feed(
            fetch_page(query, 0, len(batch), timeout, retries, retry_delay))}
        for cand in batch:
            paper = by_id.get(cand["id"])
            if paper:
                cand["abstract"] = paper["abstract"]
                cand.setdefault("date", paper["date"])
        if start + 50 < len(missing):
            time.sleep(MIN_DELAY_S)
    return candidates


# --- state -------------------------------------------------------------------

def ids_in_text(text):
    return set(ARXIV_ID_RE.findall(text or ""))


# --- report ------------------------------------------------------------------

def render(candidates, days, sections):
    lines = [
        "## Review recent arXiv candidates",
        "",
        f"{len(candidates)} unreviewed paper(s) from the last {days} day(s), newest first.",
        "",
        "Tick the ones that belong. The section in backticks is a keyword guess — "
        "edit it in place if it is wrong. Comment `/create-pr` when you are done and "
        "a PR will add the ticked papers to `data/papers.jsonl` and regenerate the README.",
        "",
        f"Valid sections: {', '.join(f'`{s}`' for s in sections)}.",
        "",
        "`criteria` counts evidence for the three scope rules — per-step **action**, "
        "**causal** generation, persistent **state**. 3/3 suggests the main list; it is "
        "keyword evidence, not a reading of the paper.",
        "",
        "Unwanted matches that keep coming back belong in `data/arxiv-ignore.txt`.",
        "",
        "---",
        "",
    ]
    return "\n".join(lines + sources.render_candidates(candidates)) + "\n"


# --- main --------------------------------------------------------------------

def parse_args():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--max-results", type=int, default=400)
    ap.add_argument("--output", default="ARXIV_CANDIDATES.md",
                    help="'-' writes the report to stdout")
    ap.add_argument("--papers", type=Path, default=ROOT / "data" / "papers.jsonl")
    ap.add_argument("--sections", type=Path, default=ROOT / "data" / "sections.json")
    ap.add_argument("--ignore", type=Path, default=ROOT / "data" / "arxiv-ignore.txt")
    ap.add_argument("--rejected", type=Path,
                    default=ROOT / "data" / "agent-rejected.jsonl",
                    help="papers a review agent already turned down")
    ap.add_argument("--existing-issue-body", type=Path,
                    help="current inbox body; ticks and section edits are preserved")
    ap.add_argument("--known-file", type=Path,
                    help="text whose arXiv links are already proposed (open PR bodies)")
    ap.add_argument("--feed-file", type=Path,
                    help="read a saved Atom feed instead of calling the API")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--retry-delay", type=float, default=5.0)
    return ap.parse_args()


def main():
    args = parse_args()
    sections = [s["key"] for s in json.loads(args.sections.read_text(encoding="utf-8"))]

    if args.feed_file:
        papers = parse_feed(args.feed_file.read_bytes())
    else:
        papers = fetch_papers(args.days, args.max_results, args.timeout,
                              args.retries, args.retry_delay)

    issue_body = (args.existing_issue_body.read_text(encoding="utf-8")
                  if args.existing_issue_body and args.existing_issue_body.exists() else "")
    known = (sources.known_ids(args.papers) | sources.ignored_ids(args.ignore)
             | sources.rejected_ids(args.rejected))
    if args.known_file and args.known_file.exists():
        known |= ids_in_text(args.known_file.read_text(encoding="utf-8"))
    ticked = sources.checked_ids(issue_body)
    overrides = sources.edited_sections(issue_body)

    seen, candidates = set(), []
    for paper in papers:
        pid = paper["id"]
        if pid in known or pid in seen:
            continue
        seen.add(pid)
        # The only filter this source owns: everything else about scope is
        # shared with OpenReview, the proceedings backfill and the watchlist.
        if not set(paper["categories"]) & ALLOWED_CATEGORIES:
            continue
        propose, section, met, evidence = sources.proposal(
            paper["title"], paper["abstract"])
        if not propose:
            continue
        candidates.append({
            "id": pid,
            "name": triage.extract_name(paper["title"]),
            "title": paper["title"],
            "date": paper["date"],
            "section": overrides.get(pid, section),
            "met": met,
            "evidence": evidence,
        })

    candidates.sort(key=lambda c: (c["met"], c["date"], c["id"]), reverse=True)
    report = sources.retick(render(candidates, args.days, sections), ticked)

    if args.output == "-":
        sys.stdout.write(report)
        print(len(candidates), file=sys.stderr)
    else:
        Path(args.output).write_text(report, encoding="utf-8")
        print(len(candidates))


if __name__ == "__main__":
    main()
