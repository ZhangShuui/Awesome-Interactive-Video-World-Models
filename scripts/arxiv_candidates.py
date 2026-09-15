#!/usr/bin/env python3
"""Propose recent arXiv papers for review, as a checkbox inbox.

Recall is phrase-based, not title-based. The systems that matter most to this
list are named Genie, Oasis, DIAMOND -- searching titles for "world" misses all
of them, so the query set covers the vocabulary of the field and the three
scope criteria do the narrowing afterwards.

Output is one markdown report meant to live in a single GitHub Issue. Each
candidate carries its metadata base64-encoded in an HTML comment; the tags in
backticks on the visible line are editable and win.

Usage:
  python3 scripts/arxiv_candidates.py --days 7
  python3 scripts/arxiv_candidates.py --since 2026-08-14T04:31:00Z
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
# The announcement feed, and a different host from the API. The two are
# throttled separately and visibly so: export.arxiv.org refused this runner's
# subnet on four consecutive runs across 09-13..09-15 while rss.arxiv.org
# answered every request in under half a second. That split is the only reason
# a fallback is worth having -- if one host were down, so would the other be.
RSS_URL = "https://rss.arxiv.org/rss/{category}"
ABS_URL = "https://arxiv.org/abs/{paper_id}"
NS = {"a": "http://www.w3.org/2005/Atom"}
RSS_NS = {"arxiv": "http://arxiv.org/schemas/atom"}
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

# The API applies QUERY_PHRASES *as the query*, so everything reaching
# `sources.proposal` has already matched the field's vocabulary. RSS hands over
# the entire day's announcements instead -- 347 papers across five categories --
# and proposal() is a scope gate, not a topic gate: it was written assuming its
# input was phrase-recalled. Handed the raw day it admitted person re-identifi-
# cation, TinyML, 802.11 channel contention and maize leaf segmentation, 39
# candidates where six were real. So the recall layer is reapplied here, and it
# has to run before proposal(), not after.
PHRASE_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(p) for p in QUERY_PHRASES) + r")", re.I)

# "Announce Type: new" and the abstract that follows it, which is the only
# place the RSS item carries one.
RSS_ABSTRACT_RE = re.compile(
    r"^arXiv:\S+\s+Announce Type:\s*\S+\s*(?:Abstract:\s*)?", re.I)
SUBMITTED_RE = re.compile(r"Submitted on (\d{1,2} \w{3} \d{4})")

# The window a degraded run could not search, carried in its own report.
#
# `--since` is anchored to the last run that *succeeded*, and a run that falls
# back to RSS succeeds: it exits 0 and writes an inbox. That would quietly
# retire the guarantee the anchor exists for, because the window it never
# searched would stop being reachable the moment `--since` advanced past it.
# So the unsearched window start rides along in the report, is read back off
# the previous inbox on the next run, and only stops being carried when a run
# actually searches it.
UNSEARCHED_RE = re.compile(r"<!-- unsearched-since:\s*(\S+)\s*-->")


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
# gave up fifteen seconds into a limit measured in minutes -- and a lost run used
# to be a lost day of recall, silently, because the window opened at `now - days`
# no matter how long it had been since anything ran. `--since` makes the next run
# reach back over the outage, so a 429 now costs latency rather than papers; the
# backoff still matters, because reaching back only helps if something reaches.
#
# The first version of this budget waited 30/60/90/120s and still lost 08-13,
# 08-15 and 08-16: growing linearly spends most of the patience on the early
# attempts, and arXiv was flatly refusing six minutes in. Doubling reaches the
# ceiling in half the attempts and then sits there, which buys a quarter of an
# hour from seven. Each wait is jittered down by up to a quarter so that a
# runner subnet throttled in lockstep does not re-collide on the way back.
class RateLimited(SystemExit):
    """arXiv refused every attempt at the API.

    A SystemExit still, so a caller that has nothing better to do keeps dying
    exactly as it did and with the same message. But it is a different failure
    from a dead socket -- the service is up and declining to serve *us* -- and
    only that distinction makes a degraded answer the right response instead of
    a dishonest one.
    """


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
    last, failures, throttled, refused = None, 0, 0, False
    while True:
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code == 429:
                throttled += 1
                if throttled > RATE_LIMIT_RETRIES:
                    refused = True
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
    attempts = failures + throttled
    if refused:
        raise RateLimited(f"arXiv API request failed after {attempts} "
                          f"attempt(s): {last}")
    raise SystemExit(f"arXiv API request failed after {attempts} "
                     f"attempt(s): {last}")


# --- arXiv RSS, the degraded path ---------------------------------------------

def get(url, timeout, retries, retry_delay):
    """A plain GET with the ordinary retry budget and no rate-limit handling.

    RSS has never answered this job with a 429. If it starts to, the right
    response is to fail -- there is no third source to fall back to, and a
    fallback that silently returns nothing is worse than a run that says so.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last = exc
            if attempt < retries:
                time.sleep(retry_delay * (attempt + 1))
    raise SystemExit(f"{url} failed after {retries + 1} attempt(s): {last}")


def parse_rss(payload):
    """One category's daily announcement -> the shape parse_feed returns.

    Replacements are skipped. They are revisions of papers announced on some
    earlier day, so either the list already holds the paper or an earlier window
    already offered it and it was turned down; either way re-proposing it is
    noise. `new` and `cross` are the two that have never been seen before.

    The date here is the announcement date, not the submission date -- RSS does
    not carry the latter. `fill_submitted_dates` corrects it for the handful of
    papers that survive the gates, which is the only place the difference is
    ever written down.
    """
    root = ET.fromstring(payload)
    out = []
    for item in root.findall("./channel/item"):
        announce = item.findtext("arxiv:announce_type", "", RSS_NS).strip()
        if announce not in ("new", "cross"):
            continue
        link = (item.findtext("link", "") or "").strip()
        m = re.search(r"abs/(\d{4}\.\d{4,5})", link)
        if not m:
            continue
        description = item.findtext("description", "") or ""
        announced = item.findtext("pubDate", "") or ""
        try:
            date = parsedate_to_datetime(announced).date().isoformat()
        except (TypeError, ValueError):
            date = ""
        out.append({
            "id": m.group(1),
            "title": re.sub(r"\s+", " ", item.findtext("title", "") or "").strip(),
            "abstract": re.sub(
                r"\s+", " ", RSS_ABSTRACT_RE.sub("", description)).strip(),
            "date": date,
            "categories": sorted(
                {(c.text or "").strip() for c in item.findall("category")} - {""}),
        })
    return out


def fetch_rss(categories, timeout, retries, retry_delay):
    """Today's announcements across the categories this list reads.

    Deduplicated by id, because a paper cross-listed into three of them appears
    in three feeds, and phrase-filtered, because the API's own query did that
    job on the path this one replaces.
    """
    seen, papers = set(), []
    for category in sorted(categories):
        payload = get(RSS_URL.format(category=category), timeout, retries, retry_delay)
        for paper in parse_rss(payload):
            if paper["id"] in seen:
                continue
            seen.add(paper["id"])
            if not PHRASE_RE.search(f"{paper['title']} {paper['abstract']}"):
                continue
            papers.append(paper)
        time.sleep(MIN_DELAY_S)
    return papers


def fill_submitted_dates(candidates, timeout, retries, retry_delay):
    """Trade the announcement date for the real one, for candidates only.

    arXiv announces two to four days after submission, so an announcement date
    recorded as the paper's date is visibly wrong in a list sorted by date. The
    correct date is on the abstract page, which lives on arxiv.org -- a third
    host, and not the one refusing us. It is one request per candidate, which
    is affordable precisely because this runs after the gates rather than
    before: a day that announces 350 papers yields single digits here.

    Best effort. A candidate whose page will not load or will not parse keeps
    the announcement date rather than losing one.
    """
    for candidate in candidates:
        try:
            page = get(ABS_URL.format(paper_id=candidate["id"]),
                       timeout, retries, retry_delay)
        except SystemExit:
            continue
        found = SUBMITTED_RE.search(page.decode("utf-8", "replace"))
        if not found:
            continue
        try:
            when = datetime.strptime(found.group(1), "%d %b %Y")
        except ValueError:
            continue
        candidate["date"] = when.date().isoformat()
        time.sleep(MIN_DELAY_S)
    return candidates


TOTAL_RE = re.compile(r"<opensearch:totalResults[^>]*>(\d+)<")


def total_results(payload):
    """How many papers the window actually holds, as arXiv reports it."""
    match = TOTAL_RE.search(payload.decode("utf-8", "replace"))
    return int(match.group(1)) if match else None


def parse_since(raw):
    """An ISO-8601 instant, or None. Naive input is read as UTC."""
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        when = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        raise SystemExit(f"--since is not an ISO-8601 timestamp: {raw!r}")
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def window_start(end, days, since):
    """Where the search window opens.

    Two things set it, and taking whichever reaches further back is the whole
    point. `days` is the routine reach, and it has to be wider than the gap
    between runs because arXiv announces a submission days after it is
    submitted: 2608.14706 carries submittedDate 08-11 and an id from the 08-13
    batch, so a window that only reaches back to yesterday never sees it.

    `since` is when the last successful run started, and it covers the case
    `days` cannot: a run that never happened searched nothing, and the next
    run's `end - days` opens *after* the gap it was supposed to close. Three
    scheduled runs died on a 429 in August 2026; the run that followed opened
    its window 2h15m after 2608.14706 was submitted, and no later window can
    reach back for it, because every later window opens later still.
    """
    routine = end - timedelta(days=days)
    if since is None or since >= routine:
        return routine
    print(f"the last successful run was {since:%Y-%m-%d %H:%M}Z, further back "
          f"than the {days}-day window; searching from there instead",
          file=sys.stderr)
    return since


def fetch_papers(start_at, end, max_results, timeout, retries, retry_delay):
    """-> (papers, degraded). Degraded means the window was not searched.

    The API is the only source that can be asked about a date range, so when it
    refuses there is no way to honour `start_at` at all. The fallback answers a
    different question -- what was announced today -- and the caller has to say
    so rather than presenting one as the other.

    Nothing is lost by taking it, but not for free: this run exits 0 and so
    becomes the success `--since` anchors to, which would strand the window it
    never searched. `start_at` is written into the report and read back by the
    next run -- see `effective_since` -- so the reach survives a whole outage
    rather than one day of it.
    """
    try:
        return _fetch_window(start_at, end, max_results, timeout, retries,
                             retry_delay), False
    except RateLimited as exc:
        print(f"{exc}\nfalling back to the RSS announcement feeds, which are "
              f"served from a different host", file=sys.stderr)
    return fetch_rss(ALLOWED_CATEGORIES, timeout, retries, retry_delay), True


def _fetch_window(start_at, end, max_results, timeout, retries, retry_delay):
    query = build_query(start_at, end)
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
    # A routine window returns a couple of hundred papers and never comes near
    # the cap. A hand-run backfill over a month does, and so does a window that
    # `--since` has stretched across a long outage: the window silently lost its
    # oldest papers and the report looked complete. Say so.
    if total is not None and total > max_results:
        print(f"warning: the window from {start_at:%Y-%m-%d %H:%M}Z holds "
              f"{total} papers but --max-results is {max_results}; "
              f"{total - max_results} were not fetched. Re-run with "
              f"--max-results {total} or a shorter window.", file=sys.stderr)
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

def unsearched_since(issue_body):
    """The window start a previous degraded run left unsearched, if any."""
    found = UNSEARCHED_RE.search(issue_body or "")
    return parse_since(found.group(1)) if found else None


def effective_since(raw, issue_body):
    """How far back this run has to reach, over both kinds of gap.

    `raw` covers runs that never happened; the marker in `issue_body` covers
    runs that happened but could not search their window. Whichever reaches
    further back wins, and a run that searches its window writes no marker, so
    the chain ends on its own rather than growing forever.
    """
    since = parse_since(raw)
    stale = unsearched_since(issue_body)
    if stale and (since is None or stale < since):
        return stale
    return since


def render(candidates, days, tags, carried=0, degraded=False, unsearched=None):
    fresh = len(candidates) - carried
    if degraded:
        summary = (
            f"{len(candidates)} unreviewed paper(s), newest first — {fresh} from "
            f"today's arXiv announcement, {carried} still open from an earlier "
            f"window." if carried else
            f"{len(candidates)} unreviewed paper(s) from today's arXiv "
            f"announcement, newest first.")
        marker = (f"\n<!-- unsearched-since: {unsearched:%Y-%m-%dT%H:%M:%SZ} -->\n"
                  if unsearched else "")
        return _render(candidates, tags, summary, DEGRADED_NOTE) + marker
    summary = (
        f"{len(candidates)} unreviewed paper(s), newest first — {fresh} from the "
        f"last {days} day(s), {carried} still open from an earlier window."
        if carried else
        f"{len(candidates)} unreviewed paper(s) from the last {days} day(s), newest first.")
    return _render(candidates, tags, summary, "")


DEGRADED_NOTE = (
    "**The date window was not searched.** arXiv's API refused every attempt "
    "at it, so this inbox was built from the RSS announcement feeds for "
    "`cs.CV`, `cs.LG`, `cs.AI`, `cs.MM` and `eess.IV` instead — a different "
    "host, which was answering. RSS carries one day of announcements rather "
    "than a `submittedDate` range, so this covers today's batch and nothing "
    "earlier. Nothing is lost: the window of the next run that succeeds opens "
    "at the last successful run, so anything missed here comes back, and "
    "whatever you tick above is kept.")


def _render(candidates, tags, summary, note):
    lines = [
        "## Review recent arXiv candidates",
        "",
        summary,
        "",
    ] + ([note, ""] if note else []) + [
        "Two boxes each. Tick the **top** one to accept a paper; tick the nested "
        "**drop** box to say it should never be proposed again. Leaving both empty "
        "means not looked at yet, and it comes back tomorrow. The tags in "
        "backticks are a keyword guess — edit them in place if they are wrong, "
        "comma-separated, and add every one that applies: a paper is rarely "
        "about one thing.",
        "",
        "Comment `/create-pr` when you are done: accepted papers go to "
        "`data/papers.jsonl` and the README is regenerated, dropped ones go to "
        "`data/maintainer-rejected.jsonl`. Nothing is recorded until you do — "
        "both marks are safe to change until then.",
        "",
        f"Valid tags: {', '.join(f'`{t}`' for t in tags)}.",
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
    # Seven, not three. The window's job is no longer to cover the gap between
    # runs -- `--since` does that -- but to outlast arXiv's announcement lag,
    # which routinely runs to two or three days and is the reason a paper can
    # be submitted inside a window nobody was searching yet.
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--since", default="",
                    help="when the last successful run started (ISO-8601); the "
                         "window is widened to reach back at least this far")
    ap.add_argument("--max-results", type=int, default=400)
    ap.add_argument("--output", default="ARXIV_CANDIDATES.md",
                    help="'-' writes the report to stdout")
    ap.add_argument("--papers", type=Path, default=ROOT / "data" / "papers.jsonl")
    ap.add_argument("--tags", type=Path, default=ROOT / "data" / "tags.json")
    ap.add_argument("--ignore", type=Path, default=ROOT / "data" / "arxiv-ignore.txt")
    ap.add_argument("--rejected", type=Path,
                    default=ROOT / "data" / "agent-rejected.jsonl",
                    help="papers a review agent already turned down")
    ap.add_argument("--maintainer-rejected", type=Path,
                    default=ROOT / "data" / "maintainer-rejected.jsonl",
                    help="papers crossed out by hand in the inbox")
    ap.add_argument("--existing-issue-body", type=Path,
                    help="current inbox body; ticks and tag edits are preserved")
    ap.add_argument("--known-file", type=Path,
                    help="text whose arXiv links are already proposed (open PR bodies)")
    ap.add_argument("--feed-file", type=Path,
                    help="read a saved Atom feed instead of calling the API")
    ap.add_argument("--rss-file", type=Path,
                    help="read a saved RSS announcement feed; exercises the "
                         "degraded path the API's 429s trigger in production")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--retry-delay", type=float, default=5.0)
    return ap.parse_args()


def main():
    args = parse_args()
    tags = [t["key"] for t in json.loads(args.tags.read_text(encoding="utf-8"))]

    issue_body = (args.existing_issue_body.read_text(encoding="utf-8")
                  if args.existing_issue_body and args.existing_issue_body.exists() else "")

    days, degraded, unsearched = args.days, False, None
    if args.feed_file:
        papers = parse_feed(args.feed_file.read_bytes())
    elif args.rss_file:
        papers = [p for p in parse_rss(args.rss_file.read_bytes())
                  if PHRASE_RE.search(f"{p['title']} {p['abstract']}")]
        degraded = True
    else:
        end = datetime.now(timezone.utc)
        start_at = window_start(
            end, args.days, effective_since(args.since, issue_body))
        papers, degraded = fetch_papers(start_at, end, args.max_results,
                                        args.timeout, args.retries,
                                        args.retry_delay)
        # What the report claims to cover has to be what it covered, or a
        # stretched window reads as a routine one.
        days = max(1, round((end - start_at).total_seconds() / 86400))
        unsearched = start_at if degraded else None
    known = (sources.known_ids(args.papers) | sources.ignored_ids(args.ignore)
             | sources.rejected_ids(args.rejected)
             | sources.rejected_ids(args.maintainer_rejected))
    if args.known_file and args.known_file.exists():
        known |= ids_in_text(args.known_file.read_text(encoding="utf-8"))
    ticked = sources.checked_ids(issue_body)
    # Crossed but not yet committed: the entry stays, wearing its cross, so the
    # verdict is not lost between the click and the /create-pr that records it.
    crossed = sources.rejected_in_issue(issue_body)
    overrides = sources.edited_tags(issue_body)

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
        propose, tags_, met, evidence = sources.proposal(
            paper["title"], paper["abstract"])
        if not propose:
            continue
        candidates.append({
            "id": pid,
            "name": triage.extract_name(paper["title"]),
            "title": paper["title"],
            "date": paper["date"],
            "tags": overrides.get(pid, tags_),
            "met": met,
            "evidence": evidence,
        })

    # The fallback dated these by announcement because RSS carries nothing
    # else. Now that the gates have cut a day's 350 papers down to single
    # digits, the real submission dates are worth one request each.
    if degraded and candidates and not args.rss_file:
        fill_submitted_dates(candidates, args.timeout, args.retries,
                             args.retry_delay)

    # Everything above came out of this run's date window. Anything still open
    # from an earlier one has to be put back by hand, or the inbox forgets it
    # the first time the window slides past -- see sources.carried_candidates.
    carried = 0
    for candidate in sources.carried_candidates(issue_body):
        pid = candidate["id"]
        if sources.source_of(pid) != "arxiv" or pid in known or pid in seen:
            continue
        seen.add(pid)
        candidates.append(candidate)
        carried += 1

    candidates.sort(key=lambda c: (c["met"], c["date"], c["id"]), reverse=True)
    report = sources.recross(
        sources.retick(
            render(candidates, days, tags, carried, degraded, unsearched), ticked),
        crossed)

    if args.output == "-":
        sys.stdout.write(report)
        print(len(candidates), file=sys.stderr)
    else:
        Path(args.output).write_text(report, encoding="utf-8")
        print(len(candidates))


if __name__ == "__main__":
    main()
