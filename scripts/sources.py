#!/usr/bin/env python3
"""What every candidate source shares: the scope decision, identity, and the
inbox format.

Four things now propose papers -- arXiv, OpenReview, conference proceedings and
a blog watchlist -- and they must agree on what is in scope, or the list means
something different depending on which door a paper came through. So the
admission decision lives here exactly once and each source module contributes
only what it alone knows: a category for arXiv, a venue for OpenReview, a feed
for a blog.

The split that matters:

  scope      -- is this paper about generated video on one of the three axes?
                Identical for every source. `proposal()` below.
  provenance -- is this record worth trusting at all? Source-specific: cs.CV vs
                q-bio for arXiv, an accepted venue vs a withdrawn submission for
                OpenReview. Each source filters that before calling `proposal`.

Sources are told apart by an id prefix, and only arXiv gets to use a bare id:

  2608.07463              arXiv
  openreview:wAuawx6o2e   OpenReview
  proc:cvpr2025-a1b2c3d4  a conference proceedings page
  blog:genie-3            a hand-checked blog post or technical report
"""
import base64
import json
import re

import triage

# --- identity ----------------------------------------------------------------

BARE_ARXIV_RE = re.compile(r"^\d{4}\.\d{4,5}$")

SOURCE_LABELS = {
    "arxiv": "arXiv",
    "openreview": "OpenReview",
    "proc": "conference proceedings",
    "blog": "blog / technical report",
}


def source_of(pid):
    """-> 'arxiv' | 'openreview' | 'cvf' | 'blog'."""
    prefix, sep, _ = (pid or "").partition(":")
    if sep and prefix in SOURCE_LABELS:
        return prefix
    return "arxiv"


def url_for(pid, url=None):
    """The canonical link for a candidate.

    Non-arXiv ids carry their URL in the inbox payload because it cannot be
    derived: an OpenReview forum id maps to a URL, but a blog post's slug does
    not. `url` wins whenever it is present.
    """
    if url:
        return url
    if source_of(pid) == "openreview":
        return f"https://openreview.net/forum?id={pid.split(':', 1)[1]}"
    if BARE_ARXIV_RE.match(pid or ""):
        return f"https://arxiv.org/abs/{pid}"
    return ""


PUNCT_RE = re.compile(r"[^a-z0-9]+")


def norm_title(title):
    """Dedup key across sources.

    The same paper reaches this list as an arXiv id, an OpenReview forum id and
    a CVF page, so ids cannot deduplicate it -- titles have to. Punctuation,
    case and whitespace all differ between the three renderings of one title,
    and none of them carry meaning here.
    """
    return PUNCT_RE.sub("", (title or "").lower())


# --- vocabulary --------------------------------------------------------------

# The field's vocabulary, shared by every source that searches by keyword. One
# table, because two copies drift within a month.
#
# Keep phrases SHORT. A longer phrase is not a narrower version of a shorter
# one, it is a different phrase matched verbatim: "real-time video generation"
# does not match "real-time streaming audio-video generation". Five of the
# twelve phrases this list started with returned literally zero arXiv results
# over a seven-day window, while the papers they were written to catch --
# Ripple, Vorch-Streamer, DUET, EchoCache -- went unproposed. The scope was
# widened in ff3af77 to admit the efficiency substrate; these phrases are what
# makes that widening reach anything.
#
# Search engines stem, so "action-conditioned" and "action-conditional" return
# the same set on arXiv and only one is needed. Anything containing a shorter
# phrase is redundant: "long video generation" is covered by "video generation".
QUERY_PHRASES = [
    "world model",
    "world simulator",
    "interactive video",
    "interactive generation",
    "playable",
    "action-conditioned",
    "controllable video",
    "autoregressive video",
    "video game",
    "game engine",
    "video generation",
    "video diffusion",
    "video prediction",
    "frame prediction",
    # The field's plainest term, and the one that catches papers whose abstract
    # says "recent video models support generation, conditioning and editing"
    # without ever putting "video" next to "generation".
    "video model",
]


# --- scope -------------------------------------------------------------------

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


def proposal(title, abstract):
    """-> (propose, section, met, evidence). The one admission decision.

    Scoring is evidence of a criterion, not satisfaction of it: it decides what
    is worth two minutes of a reviewer's attention, nothing more. Surveys,
    benchmarks and the efficiency substrate are admitted at 0/3 because they
    have no reason to say "causal" or "streaming" anywhere and were being
    dropped while the realtime section already held a dozen of their genre.
    """
    blob = f"{title} {abstract or ''}"
    if OFF_TOPIC_RE.search(blob) or not VISUAL_GATE_RE.search(blob):
        return False, None, 0, {}
    section, met, evidence = triage.triage(title, abstract)
    if (met == 0 and section not in ("surveys", "benchmarks")
            and not triage.is_efficiency_substrate(title, abstract)):
        return False, section, met, evidence
    return True, section, met, evidence


# --- known state -------------------------------------------------------------

def _jsonl(path):
    if not path or not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            out.append(json.loads(line))
    return out


def known_ids(papers_path):
    return {r["id"] for r in _jsonl(papers_path)}


def known_titles(papers_path):
    """Normalised titles already in the list.

    An arXiv-id check cannot stop the OpenReview sweep from re-proposing a
    paper the list already holds under its arXiv id, so every non-arXiv source
    deduplicates on this instead.
    """
    return {norm_title(r.get("title")) for r in _jsonl(papers_path)} - {""}


def known_urls(papers_path):
    """Every link already recorded, normalised for comparison.

    The watchlist has no identifier to work with other than a URL, and the same
    post is reachable with and without a trailing slash or a `www.`.
    """
    out = set()
    for record in _jsonl(papers_path):
        for url in (record.get("links") or {}).values():
            if url:
                out.add(norm_url(url))
    return out


def norm_url(url):
    return re.sub(r"^https?://(?:www\.)?|/+$", "", (url or "").strip().lower())


def ignored_ids(path):
    ids = set()
    if path and path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            entry = line.split("#", 1)[0].strip()
            if entry:
                ids.add(entry)
    return ids


def rejected_ids(path):
    """Papers a review agent has already turned down. Kept out of the inbox so
    the same rejection is not re-litigated daily; reversible by deleting the
    line, unlike data/arxiv-ignore.txt which is meant to be permanent."""
    return {r["id"] for r in _jsonl(path)}


# --- inbox format ------------------------------------------------------------

# The visible line is editable -- the section in backticks is a guess and the
# maintainer's correction wins -- so the machine-readable copy rides along in an
# HTML comment. Nothing constrains the id, which is what lets a blog post and an
# arXiv preprint share one inbox.
CANDIDATE_RE = re.compile(
    r"^- \[(?P<checked>[ xX])\]\s+`(?P<section>[a-z-]+)`\s+.*?"
    r"<!-- candidate:(?P<payload>[A-Za-z0-9+/=]+) -->",
    re.M | re.S)

PAYLOAD_FIELDS = ("id", "name", "title", "date", "section", "url", "origin")


def encode(record):
    raw = json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return base64.b64encode(raw).decode("ascii")


def decode(payload):
    try:
        return json.loads(base64.b64decode(payload).decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None


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


TICKS = {True: "yes", False: "--"}


def render_candidates(candidates):
    """The checkbox lines for one source's candidates."""
    lines = []
    for cand in candidates:
        ev = cand.get("evidence") or {}
        marks = " · ".join(
            f"{key} {TICKS[bool(ev.get(key))]}" for key in ("action", "causal", "state"))
        payload = encode({k: cand[k] for k in PAYLOAD_FIELDS if cand.get(k)})
        lines.append(
            f"- [ ] `{cand['section']}` **{cand['id']}** — {cand['title']} "
            f"<!-- candidate:{payload} -->")
        detail = [url_for(cand["id"], cand.get("url")), cand.get("date") or "?"]
        if cand.get("origin"):
            detail.append(cand["origin"])
        detail.append(f"criteria {cand['met']}/3 ({marks})")
        lines.append("      " + " · ".join(d for d in detail if d))
    return lines


# --- refetch -----------------------------------------------------------------

# Imported lazily: each of these imports this module.
FETCHERS = {
    "arxiv": "arxiv_candidates",
    "openreview": "openreview_candidates",
    "proc": "venue_candidates",
    "blog": "blog_candidates",
}


def fill_abstracts(candidates):
    """Put an abstract back on every candidate that lost one.

    The inbox Issue carries no abstract -- it would double the body and GitHub
    caps it -- so the reviewer refetches. Each source knows how to find its own
    again, and they do not resemble each other: arXiv answers a batched id
    query, OpenReview has to be searched by exact title because its id endpoint
    is challenge-walled, a proceedings page is one fetch each, and a blog post
    only ever had the feed summary.
    """
    import importlib
    from collections import defaultdict

    grouped = defaultdict(list)
    for candidate in candidates:
        if not candidate.get("abstract"):
            grouped[source_of(candidate["id"])].append(candidate)
    for name, group in grouped.items():
        module = importlib.import_module(FETCHERS[name])
        module.fill_abstracts(group)
    return candidates


def retick(report, ticked):
    """Re-tick what the maintainer already ticked, so a refresh loses no work."""
    if not ticked:
        return report
    lines = report.splitlines(keepends=True)
    for i, line in enumerate(lines):
        m = CANDIDATE_RE.match(line)
        if m:
            payload = decode(m.group("payload"))
            if payload and payload["id"] in ticked:
                lines[i] = line.replace("- [ ]", "- [x]", 1)
    return "".join(lines)
