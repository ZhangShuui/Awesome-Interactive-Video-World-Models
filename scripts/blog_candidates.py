#!/usr/bin/env python3
"""Watch the labs that ship interactive world models without writing a paper.

Genie, Oasis, Sora, Marble, RTFM: the systems this list exists to track are
routinely announced in a blog post and never reach arXiv, which is why
`reports` is a tag at all. Until now that tag was applied entirely by
hand and grew six entries; the daily pipeline could not see a single one of
them. This polls the watchlist in data/sources.json instead.

Two kinds of source, and the difference is worth knowing:

  feed  an RSS or Atom feed. Titles, links and dates are what the publisher
        says they are, so these are reliable.
  page  a listing page scraped for links, used where a lab publishes no feed
        (World Labs, Decart, Runway). Titles come out of anchor text and are
        provisional -- good enough to notice a release, not good enough to
        record without looking.

Nothing here is auto-mergeable in spirit: the README promises that every URL in
`reports` has been checked by hand, and a scraped anchor is not a check. The
report says so on every candidate.

Usage:
  python3 scripts/blog_candidates.py --output -
  python3 scripts/blog_candidates.py --days 90 --output -
"""
import argparse
import html
import json
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
MIN_DELAY_S = 1.0
USER_AGENT = "awesome-interactive-video-world-models/1.0 (+https://github.com/)"

# Deliberately narrower than the shared query vocabulary. A lab blog is mostly
# funding rounds, hiring and product launches, and "video generation" appears in
# every one of them; matching it here would fill the inbox with press releases.
# What distinguishes an interactive world model in marketing prose is the claim
# to be a *world*, a *simulator*, or something you can *play*.
WATCH_RE = re.compile(
    r"world model|world simulator|generative world|interactive world|"
    r"playable|interactive video|real[- ]?time (?:video|frame|world|render)|"
    r"neural game engine|game generation|frame model|world api|"
    r"action[- ]condition|holodeck|generative game", re.I)

TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")
DATE_PREFIX_RE = re.compile(
    r"^\s*([A-Z][a-z]+ \d{1,2},? \d{4})\s*", re.I)
ANCHOR_RE = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', re.S | re.I)
SLUG_RE = re.compile(r"[^a-z0-9]+")


def clean(fragment):
    return SPACE_RE.sub(" ", html.unescape(TAG_RE.sub(" ", fragment or ""))).strip()


def get(url, timeout, retries, retry_delay):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            last = exc
            if attempt < retries:
                time.sleep(retry_delay * (attempt + 1))
    print(f"warning: {url} unreachable after {retries + 1} attempts: {last}",
          file=sys.stderr)
    return None


# --- parsing -----------------------------------------------------------------

def parse_date(raw):
    """RSS says 'Tue, 05 Aug 2025 09:00:00 GMT'; Atom says ISO 8601; a blog card
    says 'October 16, 2025' and neither parser will touch it."""
    if not raw:
        return None
    raw = raw.strip()
    try:
        return parsedate_to_datetime(raw).astimezone(timezone.utc).date().isoformat()
    except (TypeError, ValueError, IndexError):
        pass
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y", "%d %B %Y"):
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def strip_ns(tag):
    return tag.rsplit("}", 1)[-1].lower()


def parse_feed(payload):
    """-> [{'title', 'url', 'summary', 'date'}] from RSS 2.0 or Atom."""
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []
    items = []
    for node in root.iter():
        if strip_ns(node.tag) not in ("item", "entry"):
            continue
        fields = {"title": "", "url": "", "summary": "", "date": None}
        for child in node:
            name = strip_ns(child.tag)
            if name == "title":
                fields["title"] = clean(child.text or "")
            elif name == "link":
                # An Atom entry carries several: the post, its comment thread,
                # and the comment *feed*. Taking the last one proposed
                # ".../feed/" as though it were the announcement.
                rel = (child.get("rel") or "alternate").lower()
                if rel == "alternate" and not fields["url"]:
                    fields["url"] = (child.get("href") or child.text or "").strip()
            elif name in ("description", "summary", "content", "encoded"):
                if not fields["summary"]:
                    fields["summary"] = clean(child.text or "")
            elif name in ("pubdate", "published", "updated", "date"):
                fields["date"] = fields["date"] or parse_date(child.text)
        if fields["title"] and fields["url"]:
            items.append(fields)
    return items


HEADING_RE = re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.S | re.I)
IMG_ALT_RE = re.compile(r'<img[^>]+alt=["\']([^"\']{8,150})["\']', re.I)


def anchor_title(inner, flattened, strip=None):
    """The headline inside a blog card, in decreasing order of reliability.

    Flattened anchor text runs the title into the excerpt with no separator --
    "RTFM: A Real-Time Frame Model A research preview of RTFM, a new..." -- so
    the structure inside the anchor is worth looking at first. A card usually
    marks its title as a heading, or repeats it as the thumbnail's alt text.
    """
    for pattern in (HEADING_RE, IMG_ALT_RE):
        match = pattern.search(inner)
        if match:
            found = clean(match.group(1))
            if len(found) >= 8:
                return found
    headline = strip.sub("", flattened) if strip else flattened
    return DATE_PREFIX_RE.sub("", headline)[:110].strip()


def parse_page(payload, base, strip_re=None):
    """-> [{'title', 'url', 'summary', 'date'}] by scanning anchor text.

    Anchor text on a blog index is usually the whole card -- date, author,
    headline, excerpt, run together. The date comes off with a pattern; the
    author only comes off if the watchlist entry says how.
    """
    text = payload.decode("utf-8", "replace")
    strip = re.compile(strip_re, re.I) if strip_re else None
    items, seen = [], set()
    for href, body in ANCHOR_RE.findall(text):
        anchor = clean(body)
        if len(anchor) < 18:
            continue
        url = urllib.parse.urljoin(base, html.unescape(href.strip()))
        if url in seen:
            continue
        seen.add(url)
        date = None
        match = DATE_PREFIX_RE.match(anchor)
        if match:
            date = parse_date(match.group(1))
        items.append({"title": anchor_title(body, anchor, strip), "url": url,
                      "summary": anchor, "date": date})
    return items


# "feed" and friends are routing, not identity: ".../genie-3/feed/" must not
# become `blog:feed`, which would then collide with every other comment feed.
GENERIC_SEGMENTS = {"feed", "index", "amp", "home", "blog", "news", "post", "en"}


def slug_for(url):
    parsed = urllib.parse.urlparse(url)
    segments = [s for s in parsed.path.strip("/").split("/") if s]
    while segments and segments[-1].lower() in GENERIC_SEGMENTS:
        segments.pop()
    tail = segments[-1] if segments else parsed.netloc
    tail = SLUG_RE.sub("-", tail.lower()).strip("-")
    return (tail or "post")[:40]


# --- refetch -----------------------------------------------------------------

def fill_abstracts(candidates, watchlist=None, timeout=60.0, retries=2, retry_delay=5.0):
    """A blog post has no abstract; the feed summary is what screening gets.
    Re-poll the watchlist and match on URL."""
    wanted = {sources.norm_url(c.get("url")): c for c in candidates if c.get("url")}
    if not wanted:
        return candidates
    entries = watchlist if watchlist is not None else json.loads(
        (ROOT / "data" / "sources.json").read_text(encoding="utf-8"))
    for entry in entries:
        payload = get(entry["url"], timeout, retries, retry_delay)
        if not payload:
            continue
        items = (parse_feed(payload) if entry.get("kind") == "feed"
                 else parse_page(payload, entry["url"], entry.get("strip_re")))
        for item in items:
            cand = wanted.get(sources.norm_url(item["url"]))
            if cand and not cand.get("abstract"):
                cand["abstract"] = item.get("summary") or item.get("title") or ""
                cand.setdefault("date", item.get("date"))
        time.sleep(MIN_DELAY_S)
    for cand in candidates:
        cand.setdefault("abstract", "")
    return candidates


# --- report ------------------------------------------------------------------

def render(candidates, tags, polled, failed, carried=0):
    lines = [
        "## Review blog and technical-report candidates",
        "",
        f"{len(candidates) - carried} post(s) from {polled} watchlist source(s)"
        + (f", {failed} unreachable" if failed else "")
        + (f", plus {carried} still open from an earlier poll" if carried else "") + ".",
        "",
        "**Every one of these needs the link opened before it is merged.** The "
        "`reports` tag promises hand-checked URLs, and a keyword match on a "
        "feed summary is not that. Titles from `page` sources are scraped from "
        "anchor text and are provisional — fix them in place if they are wrong.",
        "",
        "Tick the top box for what belongs, the nested **drop** box for what "
        "should stop coming back. The tags in backticks default to `reports`; "
        "edit it if the post is really a dataset or a survey. Comment "
        "`/create-pr` when done.",
        "",
        f"Valid tags: {', '.join(f'`{t}`' for t in tags)}.",
        "",
        "Sources live in `data/sources.json` — add a lab there when it starts "
        "publishing work this list should track.",
        "",
        "---",
        "",
    ]
    return "\n".join(lines + sources.render_candidates(candidates)) + "\n"


# --- main --------------------------------------------------------------------

def parse_args():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--output", default="BLOG_CANDIDATES.md",
                    help="'-' writes the report to stdout")
    ap.add_argument("--days", type=int, default=120,
                    help="ignore posts older than this; posts with no date always pass")
    ap.add_argument("--watchlist", type=Path, default=ROOT / "data" / "sources.json")
    ap.add_argument("--papers", type=Path, default=ROOT / "data" / "papers.jsonl")
    ap.add_argument("--tags", type=Path, default=ROOT / "data" / "tags.json")
    ap.add_argument("--ignore", type=Path, default=ROOT / "data" / "arxiv-ignore.txt")
    ap.add_argument("--maintainer-rejected", type=Path,
                    default=ROOT / "data" / "maintainer-rejected.jsonl",
                    help="posts crossed out by hand in the inbox")
    ap.add_argument("--rejected", type=Path,
                    default=ROOT / "data" / "agent-rejected.jsonl")
    ap.add_argument("--existing-issue-body", type=Path,
                    help="current inbox body; ticks and tag edits are preserved")
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--retry-delay", type=float, default=5.0)
    return ap.parse_args()


def main():
    args = parse_args()
    tags = [t["key"] for t in json.loads(args.tags.read_text(encoding="utf-8"))]
    watchlist = json.loads(args.watchlist.read_text(encoding="utf-8"))

    known_ids = (sources.known_ids(args.papers) | sources.ignored_ids(args.ignore)
                 | sources.rejected_ids(args.rejected)
                 | sources.rejected_ids(args.maintainer_rejected))
    known_titles = sources.known_titles(args.papers)
    known_urls = sources.known_urls(args.papers)
    issue_body = (args.existing_issue_body.read_text(encoding="utf-8")
                  if args.existing_issue_body and args.existing_issue_body.exists() else "")
    overrides = sources.edited_tags(issue_body)
    crossed = sources.rejected_in_issue(issue_body)

    cutoff = (datetime.now(timezone.utc) - timedelta(days=args.days)).date().isoformat()
    candidates, seen, failed = [], set(), 0
    for entry in watchlist:
        payload = get(entry["url"], args.timeout, args.retries, args.retry_delay)
        if not payload:
            failed += 1
            continue
        items = (parse_feed(payload) if entry.get("kind") == "feed"
                 else parse_page(payload, entry["url"], entry.get("strip_re")))
        for item in items:
            blob = f"{item['title']} {item['summary']}"
            if not WATCH_RE.search(blob):
                continue
            # A post with no date is kept: `page` sources often have none, and
            # dropping them would silently disable half the watchlist.
            if item["date"] and item["date"] < cutoff:
                continue
            url = item["url"]
            key = sources.norm_url(url)
            if key in known_urls or key in seen:
                continue
            if sources.norm_title(item["title"]) in known_titles:
                continue
            pid = f"blog:{slug_for(url)}"
            if pid in known_ids:
                continue
            seen.add(key)
            _, _, met, evidence = sources.proposal(item["title"], item["summary"])
            candidates.append({
                "id": pid,
                "name": triage.extract_name(item["title"]),
                "title": item["title"],
                "date": item["date"],
                # Always `reports`: that tag is defined as the systems that
                # would be in the main list if they had a paper. The maintainer
                # moves it if the post turns out to be something else.
                "tags": overrides.get(pid, ["reports"]),
                "met": met,
                "evidence": evidence,
                "url": url,
                "origin": entry["name"],
            })
        time.sleep(MIN_DELAY_S)

    # A feed is incremental and a scraped listing page is short, so a post
    # falls off the end of both without ever being announced again. Carrying
    # the unjudged ones forward matters more here than it does for arXiv: a
    # single unreachable source already costs a poll, and this is what stops it
    # costing everything that source had proposed before.
    carried = 0
    for candidate in sources.carried_candidates(issue_body):
        pid = candidate["id"]
        if sources.source_of(pid) != "blog" or pid in known_ids:
            continue
        key = sources.norm_url(candidate.get("url") or "")
        if key in known_urls or key in seen:
            continue
        if sources.norm_title(candidate["title"]) in known_titles:
            continue
        seen.add(key)
        candidates.append(candidate)
        carried += 1

    candidates.sort(key=lambda c: (c["date"] or "", c["id"]), reverse=True)
    report = sources.recross(
        sources.retick(render(candidates, tags, len(watchlist), failed, carried),
                       sources.checked_ids(issue_body)),
        crossed)
    if args.output == "-":
        sys.stdout.write(report)
        print(len(candidates), file=sys.stderr)
    else:
        Path(args.output).write_text(report, encoding="utf-8")
        print(len(candidates))


if __name__ == "__main__":
    main()
