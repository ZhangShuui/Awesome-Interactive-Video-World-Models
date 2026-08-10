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
import base64
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
API_URL = "https://export.arxiv.org/api/query"
NS = {"a": "http://www.w3.org/2005/Atom"}
PAGE_SIZE = 100
MIN_DELAY_S = 3.1
USER_AGENT = "awesome-interactive-video-world-models/1.0 (+https://github.com/)"

ALLOWED_CATEGORIES = {"cs.CV", "cs.LG", "cs.AI", "cs.RO", "cs.GR", "cs.MM", "eess.IV"}

QUERY_PHRASES = [
    "world model",
    "world simulator",
    "interactive video",
    "interactive generation",
    "playable",
    "action-conditioned video",
    "neural game engine",
    "game generation",
    "streaming video generation",
    "real-time video generation",
    "long video generation",
    "video diffusion",
]

# "World model" is popular vocabulary well outside vision. These never belong.
# Stems, not whole words -- a trailing \b here would silently disable every
# entry that is a prefix ("econom" would stop matching "Economic").
OFF_TOPIC_RE = re.compile(
    r"\b(?:protein|molecul|genomic|clinical|surgical|financ|econom|portfolio|"
    r"supply chain|digital twin|traffic forecast|weather|climate|seismic|"
    r"recommend(?:er|ation)|speech recognition)", re.I)

# The list is about generated *video*. A world model with no pixels in it --
# an LLM's internal world model, an agentic-RL dynamics model -- is out of
# scope no matter how many of the three criteria its abstract appears to meet.
VISUAL_GATE_RE = re.compile(
    r"\bvideo\b|\bframes?\b|\bvisual\b|\bpixel|\brender|\bimages?\b|"
    r"\bscene\b|\bview(?:point|s)?\b|\bdiffusion\b", re.I)

CANDIDATE_RE = re.compile(
    r"^- \[(?P<checked>[ xX])\]\s+`(?P<section>[a-z-]+)`\s+.*?"
    r"<!-- candidate:(?P<payload>[A-Za-z0-9+/=]+) -->",
    re.M | re.S)
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


def fetch_page(query, start, max_results, timeout, retries, retry_delay):
    params = urllib.parse.urlencode({
        "search_query": query, "start": start, "max_results": max_results,
        "sortBy": "submittedDate", "sortOrder": "descending",
    })
    request = urllib.request.Request(f"{API_URL}?{params}",
                                     headers={"User-Agent": USER_AGENT})
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError, ET.ParseError) as exc:
            last = exc
            if attempt < retries:
                time.sleep(retry_delay * (attempt + 1))
    raise SystemExit(f"arXiv API request failed after {retries + 1} attempts: {last}")


def fetch_papers(days, max_results, timeout, retries, retry_delay):
    end = datetime.now(timezone.utc)
    query = build_query(end - timedelta(days=days), end)
    papers, start = [], 0
    while start < max_results:
        page = fetch_page(query, start, min(PAGE_SIZE, max_results - start),
                          timeout, retries, retry_delay)
        batch = parse_feed(page)
        papers.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        start += PAGE_SIZE
        time.sleep(MIN_DELAY_S)
    return papers


# --- state -------------------------------------------------------------------

def known_ids(papers_path):
    ids = set()
    if papers_path.exists():
        for line in papers_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                ids.add(json.loads(line)["id"])
    return ids


def ignored_ids(path):
    ids = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            entry = line.split("#", 1)[0].strip()
            if entry:
                ids.add(entry)
    return ids


def ids_in_text(text):
    return set(ARXIV_ID_RE.findall(text or ""))


def checked_ids(issue_body):
    """Papers the maintainer already ticked survive an inbox refresh."""
    out = set()
    for m in CANDIDATE_RE.finditer(issue_body or ""):
        if m.group("checked").lower() == "x":
            payload = decode(m.group("payload"))
            if payload:
                out.add(payload["id"])
    return out


def edited_sections(issue_body):
    """Section corrections the maintainer typed survive an inbox refresh."""
    out = {}
    for m in CANDIDATE_RE.finditer(issue_body or ""):
        payload = decode(m.group("payload"))
        if payload and m.group("section") != payload.get("section"):
            out[payload["id"]] = m.group("section")
    return out


def encode(record):
    raw = json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def decode(payload):
    try:
        return json.loads(base64.b64decode(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None


# --- report ------------------------------------------------------------------

TICKS = {True: "yes", False: "--"}


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
    for cand in candidates:
        ev = cand["evidence"]
        marks = " · ".join(
            f"{key} {TICKS[bool(ev.get(key))]}" for key in ("action", "causal", "state"))
        payload = encode({k: cand[k] for k in ("id", "name", "title", "date", "section")})
        lines.append(
            f"- [ ] `{cand['section']}` **{cand['id']}** — {cand['title']} "
            f"<!-- candidate:{payload} -->")
        lines.append(f"      https://arxiv.org/abs/{cand['id']} · {cand['date']} · "
                     f"criteria {cand['met']}/3 ({marks})")
    return "\n".join(lines) + "\n"


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
    known = known_ids(args.papers) | ignored_ids(args.ignore)
    if args.known_file and args.known_file.exists():
        known |= ids_in_text(args.known_file.read_text(encoding="utf-8"))
    ticked = checked_ids(issue_body)
    overrides = edited_sections(issue_body)

    seen, candidates = set(), []
    for paper in papers:
        pid = paper["id"]
        if pid in known or pid in seen:
            continue
        seen.add(pid)
        if not set(paper["categories"]) & ALLOWED_CATEGORIES:
            continue
        blob = f"{paper['title']} {paper['abstract']}"
        if OFF_TOPIC_RE.search(blob) or not VISUAL_GATE_RE.search(blob):
            continue
        section, met, evidence = triage.triage(paper["title"], paper["abstract"])
        # Surveys, benchmarks and the efficiency substrate are worth a look even
        # when no criterion fires.
        if (met == 0 and section not in ("surveys", "benchmarks")
                and not triage.is_efficiency_substrate(paper["title"], paper["abstract"])):
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
    report = render(candidates, args.days, sections)

    # Re-tick what the maintainer already ticked, so a refresh loses no work.
    if ticked:
        lines = report.splitlines(keepends=True)
        for i, line in enumerate(lines):
            m = CANDIDATE_RE.match(line)
            if m:
                payload = decode(m.group("payload"))
                if payload and payload["id"] in ticked:
                    lines[i] = line.replace("- [ ]", "- [x]", 1)
        report = "".join(lines)

    if args.output == "-":
        sys.stdout.write(report)
        print(len(candidates), file=sys.stderr)
    else:
        Path(args.output).write_text(report, encoding="utf-8")
        print(len(candidates))


if __name__ == "__main__":
    main()
