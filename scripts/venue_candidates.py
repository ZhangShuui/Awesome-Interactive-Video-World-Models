#!/usr/bin/env python3
"""Backfill one conference's proceedings: CVPR, ICCV, WACV, ECCV, NeurIPS.

Not a daily job. A proceedings page changes once a year, so this runs by hand
after a conference publishes, and its whole purpose is the paper that never went
to arXiv -- most of what it finds is already in the list under an arXiv id and
gets dropped by title.

**Titles are filtered before abstracts are fetched.** CVPR 2025 alone is 2,871
papers and the listing carries no abstracts, so reading every abstract means
2,871 requests to answer a question a title mostly settles. The cost of that
trade is real and one-directional: a paper whose title says nothing topical --
"DUET: A Diversity-Quality Duet of Distillation Experts" would have survived,
but a bare codename would not -- is never seen. Widen `--title-re` when
sweeping a venue where that matters.

Usage:
  python3 scripts/venue_candidates.py --venue CVPR2025 --output -
  python3 scripts/venue_candidates.py --venue NeurIPS2024 --max-fetch 200
  python3 scripts/venue_candidates.py --venue ECCV2024 --title-re 'video|world'
"""
import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sources  # noqa: E402
import triage  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MIN_DELAY_S = 1.0
USER_AGENT = "awesome-interactive-video-world-models/1.0 (+https://github.com/)"

# Three proceedings sites, three markup dialects. ECVA writes its href
# unquoted and CVF puts the title on the same line; both are matched loosely
# on purpose, because a strict parser breaks the year these pages are restyled.
LISTINGS = {
    "cvf": {
        "match": re.compile(r"^(CVPR|ICCV|WACV)(\d{4})$", re.I),
        "url": "https://openaccess.thecvf.com/{venue}?day=all",
        "base": "https://openaccess.thecvf.com",
        "entry": re.compile(
            r'<dt class="ptitle">.*?<a\s+href=["\']?(?P<href>[^"\'>\s]+)["\']?\s*>'
            r'(?P<title>.*?)</a>', re.S | re.I),
        "abstract": re.compile(r'<div id="abstract"[^>]*>(?P<body>.*?)</div>', re.S | re.I),
    },
    "ecva": {
        "match": re.compile(r"^ECCV(\d{4})$", re.I),
        "url": "https://www.ecva.net/papers.php",
        "base": "https://www.ecva.net/",
        "entry": re.compile(
            r'<dt class="ptitle">.*?<a\s+href=["\']?(?P<href>[^"\'>\s]+)["\']?\s*>'
            r'(?P<title>.*?)</a>', re.S | re.I),
        "abstract": re.compile(r'<div id="abstract"[^>]*>(?P<body>.*?)</div>', re.S | re.I),
        # One page holds every ECCV since 2018; the year is only in the href.
        "href_year": "eccv_{year}",
    },
    "neurips": {
        "match": re.compile(r"^(?:NeurIPS|NIPS)(\d{4})$", re.I),
        "url": "https://proceedings.neurips.cc/paper_files/paper/{year}",
        "base": "https://proceedings.neurips.cc",
        "entry": re.compile(
            r'<a\s+title="paper title"\s+href="(?P<href>[^"]+)"\s*>(?P<title>.*?)</a>',
            re.S | re.I),
        "abstract": re.compile(
            r"<h4>Abstract</h4>\s*(?:<p>)?\s*(?P<body>.*?)(?:</p>)?\s*(?:<h4>|</div>)",
            re.S | re.I),
    },
}

# The cheap pre-filter over titles. Wider than the shared query vocabulary
# because it is the only chance a paper gets: nothing that fails here is ever
# read. Still far narrower than "video", which alone is a third of CVPR.
TITLE_PREFILTER = re.compile(
    r"world model|world simulat|interactive|playable|action[- ]condition|"
    r"controllable video|autoregressive video|video game|game engine|"
    r"video generat|video diffusion|video predict|frame predict|video synthes|"
    r"streaming|real[- ]?time|long video|neural (?:game|render)|simulator|"
    r"generative (?:game|world)", re.I)

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")


def clean(fragment):
    return SPACE_RE.sub(" ", html.unescape(TAG_RE.sub(" ", fragment or ""))).strip()


def dialect_for(venue):
    for kind, spec in LISTINGS.items():
        match = spec["match"].match(venue)
        if match:
            year = match.group(match.lastindex)
            return kind, spec, spec["url"].format(venue=venue, year=year), year
    raise SystemExit(
        f"unknown venue {venue!r}; expected one of CVPR/ICCV/WACV/ECCV/NeurIPS "
        f"followed by a year, e.g. CVPR2025")


def get(url, timeout, retries, retry_delay):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            if attempt < retries:
                time.sleep(retry_delay * (attempt + 1))
    raise SystemExit(f"{url} failed after {retries + 1} attempts: {last}")


def parse_listing(spec, page, venue, year=None):
    """-> [{'title', 'url'}], one per paper on the proceedings index."""
    want = spec.get("href_year", "").format(year=year) if year else ""
    out, seen = [], set()
    for match in spec["entry"].finditer(page):
        title = clean(match.group("title"))
        href = html.unescape(match.group("href").strip())
        if not title or not href or (want and want not in href):
            continue
        url = urllib.parse.urljoin(spec["base"] + "/", href)
        if url in seen:
            continue
        seen.add(url)
        out.append({"title": title, "url": url, "venue": venue})
    return out


def paper_id(venue, url):
    digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
    return f"proc:{venue.lower()}-{digest}"


def fill_abstracts(candidates, timeout=60.0, retries=2, retry_delay=5.0):
    """Refetch abstracts for inbox candidates, one proceedings page each."""
    for cand in candidates:
        url = cand.get("url")
        if not url or cand.get("abstract"):
            continue
        kind = "neurips" if "neurips" in url else ("ecva" if "ecva.net" in url else "cvf")
        page = get(url, timeout, retries, retry_delay)
        found = LISTINGS[kind]["abstract"].search(page)
        cand["abstract"] = clean(found.group("body")) if found else ""
        time.sleep(MIN_DELAY_S)
    return candidates


# --- report ------------------------------------------------------------------

def render(candidates, sections, venue, listed, examined):
    lines = [
        f"## Review {venue} proceedings candidates",
        "",
        f"{len(candidates)} paper(s) from {listed} in the proceedings, "
        f"{examined} of whose titles were topical enough to read.",
        "",
        "Everything already in the list under another identifier has been "
        "dropped by title, so what remains is mostly work that never went to "
        "arXiv. Tick what belongs; the section in backticks is a keyword guess "
        "and your edit wins. Comment `/create-pr` when done.",
        "",
        f"Valid sections: {', '.join(f'`{s}`' for s in sections)}.",
        "",
        "---",
        "",
    ]
    return "\n".join(lines + sources.render_candidates(candidates)) + "\n"


# --- main --------------------------------------------------------------------

def parse_args():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--venue", required=True,
                    help="CVPR2025, ICCV2025, WACV2025, ECCV2024, NeurIPS2024")
    ap.add_argument("--output", default="VENUE_CANDIDATES.md",
                    help="'-' writes the report to stdout")
    ap.add_argument("--title-re", default=None,
                    help="override the title pre-filter")
    ap.add_argument("--max-fetch", type=int, default=400,
                    help="most abstracts to read in one run")
    ap.add_argument("--papers", type=Path, default=ROOT / "data" / "papers.jsonl")
    ap.add_argument("--sections", type=Path, default=ROOT / "data" / "sections.json")
    ap.add_argument("--ignore", type=Path, default=ROOT / "data" / "arxiv-ignore.txt")
    ap.add_argument("--rejected", type=Path,
                    default=ROOT / "data" / "agent-rejected.jsonl")
    ap.add_argument("--existing-issue-body", type=Path,
                    help="current inbox body; ticks and section edits are preserved")
    ap.add_argument("--listing-file", type=Path,
                    help="read a saved proceedings index instead of fetching it")
    ap.add_argument("--timeout", type=float, default=90.0)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--retry-delay", type=float, default=5.0)
    return ap.parse_args()


def main():
    args = parse_args()
    sections = [s["key"] for s in json.loads(args.sections.read_text(encoding="utf-8"))]
    kind, spec, url, year = dialect_for(args.venue)
    title_re = re.compile(args.title_re, re.I) if args.title_re else TITLE_PREFILTER

    page = (args.listing_file.read_text(encoding="utf-8") if args.listing_file
            else get(url, args.timeout, args.retries, args.retry_delay))
    papers = parse_listing(spec, page, args.venue, year)
    if not papers:
        raise SystemExit(f"no papers parsed from {url}; the page markup may have changed")

    known_ids = (sources.known_ids(args.papers) | sources.ignored_ids(args.ignore)
                 | sources.rejected_ids(args.rejected))
    known_titles = sources.known_titles(args.papers)
    issue_body = (args.existing_issue_body.read_text(encoding="utf-8")
                  if args.existing_issue_body and args.existing_issue_body.exists() else "")
    overrides = sources.edited_sections(issue_body)

    shortlist = [p for p in papers
                 if title_re.search(p["title"])
                 and sources.norm_title(p["title"]) not in known_titles
                 and paper_id(args.venue, p["url"]) not in known_ids]
    if len(shortlist) > args.max_fetch:
        print(f"note: {len(shortlist)} titles matched but --max-fetch is "
              f"{args.max_fetch}; {len(shortlist) - args.max_fetch} were not read",
              file=sys.stderr)
        shortlist = shortlist[:args.max_fetch]

    candidates = []
    for index, paper in enumerate(shortlist, 1):
        print(f"  [{index}/{len(shortlist)}] {paper['title'][:70]}", file=sys.stderr)
        fill_abstracts([paper], args.timeout, args.retries, args.retry_delay)
        propose, section, met, evidence = sources.proposal(
            paper["title"], paper.get("abstract"))
        if not propose:
            continue
        pid = paper_id(args.venue, paper["url"])
        candidates.append({
            "id": pid,
            "name": triage.extract_name(paper["title"]),
            "title": paper["title"],
            "date": None,
            "section": overrides.get(pid, section),
            "met": met,
            "evidence": evidence,
            "url": paper["url"],
            "origin": args.venue,
        })

    candidates.sort(key=lambda c: (c["met"], c["title"]), reverse=True)
    report = sources.retick(
        render(candidates, sections, args.venue, len(papers), len(shortlist)),
        sources.checked_ids(issue_body))
    if args.output == "-":
        sys.stdout.write(report)
        print(len(candidates), file=sys.stderr)
    else:
        Path(args.output).write_text(report, encoding="utf-8")
        print(len(candidates))


if __name__ == "__main__":
    main()
