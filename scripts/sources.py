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
    # "X Forcing" has become a naming genre here -- Diffusion Forcing, Self
    # Forcing, Rolling Forcing, Memory Forcing, Causal Forcing -- and the list
    # already holds 33 of them.
    #
    # Measured before adding, and the measurement argues against it: 31 of those
    # 33 were already caught by the phrases above, because a paper in this genre
    # says "video generation" or "autoregressive video" in its abstract as a
    # matter of course. Search stems forcing -> force/forced, so the phrase also
    # returns grasp-force, contact-force and force-torque work, which reads as
    # ~37 extra candidates a month and no extra papers. Kept anyway, as a
    # maintainer's call, on the bet that the genre keeps growing and a future
    # member of it drops the vocabulary the rest of the query depends on.
    # Narrowing the category gate takes most of the cost back.
    "forcing",
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

# The gate above states that intent and does not enforce it. It asks whether a
# visual word appears anywhere, which every paper in the field satisfies by
# accident: "diffusion" admits every diffusion-LLM serving paper, "visual"
# admits every VLA policy, "scene" admits every navigation stack. Measured over
# the 134 papers rejected by hand or by the review agent, 133 cleared it -- the
# gate was doing no work at all, and the maintainer was doing it instead, daily.
#
# So the decision is split in two. Below is the evidence that a paper actually
# *produces* pixels rather than merely consuming them; further down is the
# vocabulary of the two genres that keep arriving without any.
#
# "render" earns its own clause. On its own it matches "render exhaustive
# search infeasible" and "renders subsequent candidates ineffective" -- an
# ordinary English idiom that was letting LLM-serving papers in through a gate
# named after graphics. It counts only next to something visual.
VISUAL_OUTPUT_RE = re.compile(
    r"video (?:generation|generat\w+|synthesi[sz]\w*|diffusion|model|world model|rollout|frames?)|"
    r"generat\w+ (?:video|frames?|pixels?|images?)|synthesi[sz]\w* (?:video|frames?)|"
    r"diffusion world model|world model.{0,40}\bvideo\b|\bvideo\b.{0,40}world model|"
    r"visual (?:realism|fidelity|experience|generation|quality|content|world)|"
    r"world simulator|game engine|generative game|game generation|"
    r"\bplayable\b|interactive video|explorable|enterable|"
    r"text[- ]to[- ]video|image[- ]to[- ]video|\bt2v\b|\bi2v\b|pixel[- ]space|"
    r"\bfps\b|\b\d{3,4}p\b|"
    r"\brender\w*\b[^.]{0,60}?\b(?:videos?|frames?|images?|views?|scenes?|geometry|"
    r"appearance|artifacts?|pixels?|visual)\b|"
    r"\b(?:videos?|frames?|images?|views?|scenes?|neural|3d|gaussian|visual)\b"
    r"[^.]{0,40}?\brender\w*", re.I)

# The two genres that arrive every day and are turned down every day.
#
# The first stops at the latent: JEPA and the world-action models predict a
# feature, hand it to a planner and never decode it. They advertise the fact --
# "decoder-free", "beyond RGB", "latent futures" -- which is what makes them
# separable from the video world models they are named after. The second is the
# LLM stack: serving, speculative decoding, GUI and coding agents, which reach
# the query through "world model" as a figure of speech.
#
# Neither list is a rejection on its own. A paper matching them is dropped only
# when it cannot show visual output above, because the wanted half of this field
# says both things at once: DreamX-Phi is an action-conditioned world model for
# robotic manipulation, GeniWorld is a robot world model, and both generate
# video. Measured over the 429 already-listed papers that clear the current
# gate, this pair drops none of them and removes 44 of the 133 surviving
# rejections -- 34 world-action, 10 LLM, and nothing from any other genre.
#
# Surveys are exempt for the same reason they are admitted at 0/3: a survey of
# embodied world models is a survey first, and is wanted whatever it surveys.
NON_VISUAL_PURPOSE_RE = re.compile(
    # latent-only world models
    r"\bjepa\b|joint[- ]embedding predictive|latent world model|world[- ]action model|"
    r"\bwams?\b|decoder[- ]free|beyond rgb|feature forecasting|latent futures?\b|"
    r"without (?:generating|decoding|rendering) pixels|"
    # the LLM stack
    r"\bllms?\b|large language model|language model|\bmllms?\b|\bgui agent|coding agent|"
    r"mobile agent|tool[- ]augmented|speculative (?:sampling|decoding)|\bdllms?\b|"
    r"diffusion llm|"
    # a world model used only as a policy's simulator
    r"polic(?:y|ies)[- ](?:learning|evaluation|improvement|optimization)|"
    r"continuous[- ]control|visual control|model[- ]based rl\b|"
    r"downstream (?:planning|control)|(?:internal|learned) simulators?|"
    r"action[- ]chunks?|vision[- ]language[- ]action|\bvla\b|soft actor|\bmasac\b|"
    r"generalist polic", re.I)


def generates_video(title, abstract):
    """Does this paper produce pixels, or only consume them?

    True whenever there is evidence of visual output, and for surveys, which
    are judged by their subject rather than by their output.
    """
    blob = f"{title} {abstract or ''}"
    if triage.SURVEY_RE.search(title or ""):
        return True
    if VISUAL_OUTPUT_RE.search(blob):
        return True
    return not NON_VISUAL_PURPOSE_RE.search(blob)


def proposal(title, abstract):
    """-> (propose, tags, met, evidence). The one admission decision.

    Scoring is evidence of a criterion, not satisfaction of it: it decides what
    is worth two minutes of a reviewer's attention, nothing more. Surveys,
    benchmarks and the efficiency substrate are admitted at 0/3 because they
    have no reason to say "causal" or "streaming" anywhere and were being
    dropped while the realtime list already held a dozen of their genre.

    Three gates, cheapest first: the topic is not somebody else's field, a
    visual word appears at all, and -- see generates_video -- the paper makes
    pixels rather than only reading them.
    """
    blob = f"{title} {abstract or ''}"
    if OFF_TOPIC_RE.search(blob) or not VISUAL_GATE_RE.search(blob):
        return False, [], 0, {}
    if not generates_video(title, abstract):
        return False, [], 0, {}
    tags, met, evidence = triage.triage(title, abstract)
    if (met == 0 and not {"surveys", "benchmarks"} & set(tags)
            and not triage.is_efficiency_substrate(title, abstract)):
        return False, tags, met, evidence
    return True, tags, met, evidence


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

# The visible line is editable -- the tags in backticks are a guess and the
# maintainer's correction wins -- so the machine-readable copy rides along in an
# HTML comment. Nothing constrains the id, which is what lets a blog post and an
# arXiv preprint share one inbox.
#
# Tags are comma-separated, and editing them means typing a list: `systems` ->
# `systems,control`. A trailing comma or a space after one is accepted, because
# the field is edited by a human on a phone as often as not.
TAGS = r"[a-z-]+(?:\s*,\s*[a-z-]+)*,?"

CANDIDATE_RE = re.compile(
    rf"^- \[(?P<checked>[ xX])\]\s+`(?P<tags>{TAGS})`\s+.*?"
    r"<!-- candidate:(?P<payload>[A-Za-z0-9+/=]+) -->",
    re.M | re.S)

# The same entry plus the indented detail line under it, which is where the
# criteria marks live. They are not in the payload because they are derived,
# not identity -- but re-deriving them needs the abstract, and the inbox does
# not carry one, so a carried candidate reads them back off its own report.
CARRIED_RE = re.compile(
    rf"^- \[(?P<checked>[ xX])\]\s+`(?P<tags>{TAGS})`\s+.*?"
    r"<!-- candidate:(?P<payload>[A-Za-z0-9+/=]+) -->\n"
    r"[ ]+(?P<detail>\S.*)$",
    re.M)

CRITERIA_RE = re.compile(
    r"criteria (?P<met>\d)/3 \(action (?P<action>yes|--) · "
    r"causal (?P<causal>yes|--) · state (?P<state>yes|--)\)")

# The second box, on the indented detail line. Its id is in the clear rather
# than base64: the entry above already carries the payload, and this one only
# has to say which entry it belongs to.
REJECT_RE = re.compile(
    r"^\s+- \[(?P<checked>[ xX])\].*?<!-- reject:(?P<id>[^\s>]+) -->", re.M)

PAYLOAD_FIELDS = ("id", "name", "title", "date", "tags", "url", "origin")


def parse_tags(raw):
    """`systems, control,` -> ['systems', 'control']. Order is the maintainer's."""
    seen, out = set(), []
    for tag in (raw or "").split(","):
        tag = tag.strip()
        if tag and tag not in seen:
            seen.add(tag)
            out.append(tag)
    return out


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


def rejected_in_issue(issue_body):
    """Papers the maintainer crossed out in the inbox.

    A cross is not durable on its own -- it lives in an Issue body that the
    next refresh rewrites -- so it is honoured here and recorded for good in
    data/maintainer-rejected.jsonl when /create-pr runs. Until that happens the
    entry stays in the inbox wearing its cross, exactly as a ticked entry stays
    until a PR carries it off. Neither mark is allowed to be the only copy of
    itself.
    """
    return {m.group("id") for m in REJECT_RE.finditer(issue_body or "")
            if m.group("checked").lower() == "x"}


def edited_tags(issue_body):
    """Tag corrections the maintainer typed survive an inbox refresh."""
    out = {}
    for m in CANDIDATE_RE.finditer(issue_body or ""):
        payload = decode(m.group("payload"))
        if not payload:
            continue
        tags = parse_tags(m.group("tags"))
        if tags != (payload.get("tags") or []):
            out[payload["id"]] = tags
    return out


def carried_candidates(issue_body):
    """Every candidate already in the inbox, rebuilt well enough to re-render.

    Each source regenerates its report from its own window, so without this an
    entry that ages out of that window disappears before anyone has judged it
    -- silently, and for good, because nothing else remembers a candidate. The
    inbox is the only record between proposal and verdict, and the window has
    to be allowed to move: it is three days, the daily run has lost three of
    its last five, and a paper nobody had time to tick on Friday is not a
    paper anybody decided against.

    Carrying forward is not the same as never forgetting. The caller retires an
    entry the moment it is accounted for elsewhere -- merged, ignored, rejected,
    or sitting in an open PR -- which is what keeps the inbox from growing
    without bound.
    """
    out = []
    for m in CARRIED_RE.finditer(issue_body or ""):
        payload = decode(m.group("payload"))
        if not payload:
            continue
        criteria = CRITERIA_RE.search(m.group("detail"))
        candidate = dict(payload)
        # The visible tags are the maintainer's if they edited them, and the
        # payload's otherwise; either way the line is what to believe.
        candidate["tags"] = parse_tags(m.group("tags"))
        candidate["met"] = int(criteria.group("met")) if criteria else 0
        candidate["evidence"] = {
            key: bool(criteria and criteria.group(key) == "yes")
            for key in ("action", "causal", "state")}
        out.append(candidate)
    return out


TICKS = {True: "yes", False: "--"}


def render_candidates(candidates):
    """The checkbox lines for one source's candidates.

    Two boxes each, because a candidate has three fates and one box only spells
    two. Ticking the first accepts it; ticking the second says never propose
    this again; leaving both empty means nobody has looked yet, which is not
    the same as no. The second box is the detail line rather than a line of its
    own -- that line already existed and had nothing interactive on it, so the
    inbox gains a verdict without gaining any length.
    """
    lines = []
    for cand in candidates:
        ev = cand.get("evidence") or {}
        marks = " · ".join(
            f"{key} {TICKS[bool(ev.get(key))]}" for key in ("action", "causal", "state"))
        payload = encode({k: cand[k] for k in PAYLOAD_FIELDS if cand.get(k)})
        lines.append(
            f"- [ ] `{','.join(cand['tags'])}` **{cand['id']}** — {cand['title']} "
            f"<!-- candidate:{payload} -->")
        detail = [url_for(cand["id"], cand.get("url")), cand.get("date") or "?"]
        if cand.get("origin"):
            detail.append(cand["origin"])
        detail.append(f"criteria {cand['met']}/3 ({marks})")
        lines.append("  - [ ] **drop** · " + " · ".join(d for d in detail if d)
                     + f" <!-- reject:{cand['id']} -->")
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


def recross(report, rejected):
    """The same, for the drop box. A verdict survives a refresh either way."""
    if not rejected:
        return report
    lines = report.splitlines(keepends=True)
    for i, line in enumerate(lines):
        m = REJECT_RE.match(line)
        if m and m.group("id") in rejected:
            lines[i] = line.replace("- [ ]", "- [x]", 1)
    return "".join(lines)
