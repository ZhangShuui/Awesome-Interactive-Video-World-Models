#!/usr/bin/env python3
"""Shared triage rules: does a paper belong here, and what is it about.

Used by the daily arXiv pipeline and by the offline importer. Keep every rule
in this file -- two copies of a keyword table drift within a month.

Papers carry tags, not a category. A paper is rarely about one thing, and the
old one-section-per-paper model had to throw the rest away: Incantation is both
an interactive world model and the paper on language as an action interface, and
filing it under `systems` made the control list read as though prompt-based
control did not exist. So the rules keep every tag that fires instead of
picking a winner.

The rules only ever *suggest*. Tags written into data/papers.jsonl by a human
are authoritative and nothing here overrides them.
"""
import re

# Ordered most specific claim first, which is also the order tags render in.
TECH_TAGS = ("datasets", "control", "memory", "realtime")

# High-precision patterns. A hit in the *title* earns the tag outright: a paper
# that is about caching says so in its title; a paper that merely uses a cache
# says so in its abstract.
DECISIVE_TITLE_RULES = {
    "datasets": [r"\bdatasets?\b", r"\bcorpus\b", r"\bdata engine\b"],
    "control": [
        r"\blatent[- ]action", r"\baction[- ]condition", r"\bcontrollab",
        r"\binstruction[- ]follow", r"\bcamera control\b", r"\baction space\b",
        r"\bkeyboard\b", r"\bmouse\b", r"\baction model\b",
        # The prompt is the control channel. Kept to titles that say so:
        # "text-guided" and "text-to-video" are not here, because a caption is
        # not an interface -- see LANGUAGE_ACTION.
        r"\baction interface\b", r"\blanguage[- ]guided\b", r"\bsemantic control\b",
        r"\btext conditioning\b", r"\btext[- ]grounded\b", r"\bmulti[- ]event\b",
        r"\bas[- ]prompt\b", r"\bgenerative control\b",
    ],
    "memory": [
        r"\bmemor(?:y|ies)\b", r"\bmem[A-Z]", r"\blong[- ]term\b",
        r"\blong[- ]horizon\b", r"\bpersisten", r"\bforget", r"\bout of sight\b",
        r"\brevisit", r"\bretriev", r"\bconsisten", r"\bdrift\b",
        r"\berror accumulation\b", r"\bextrapolat",
    ],
    "realtime": [
        r"\breal[- ]?time\b", r"\bstreaming\b", r"\bdistill", r"\bfew[- ]step\b",
        r"\bone[- ]step\b", r"\bacceler", r"\bcach(?:e|es|ing)\b", r"\blatency\b",
        r"\bthroughput\b", r"\binference engine\b", r"\bserving\b", r"\bspeed",
        r"\befficient (?:infer|serv|gener)",
    ],
}

# (weight, pattern) fallback, scored over the abstract only. Deliberately
# excludes generic tokens ("state", "3d", "control", "autoregressive") that
# appear in nearly every abstract in this field.
#
# "datasets" is deliberately absent: every method paper names the datasets it
# trained on, so an abstract hit says nothing. A dataset contribution announces
# itself in the title or it is not a dataset paper.
ABSTRACT_RULES = {
    "control": [(4, r"\blatent action"), (4, r"\baction[- ]condition"),
                (3, r"\bcontrollab"), (3, r"\binstruction[- ]follow"),
                (2, r"\bcamera control\b"), (2, r"\bkeyboard\b"), (2, r"\bmouse\b"),
                (2, r"\baction space\b"),
                (4, r"\baction interface\b"), (3, r"\bsemantic control\b"),
                (2, r"\blanguage[- ]guided\b"), (2, r"\btext intervention"),
                (2, r"\bprompt switch"), (2, r"\bstreaming prompt")],
    "memory": [(4, r"\bmemory\b"), (3, r"\blong[- ]term\b"), (3, r"\blong[- ]horizon\b"),
               (3, r"\bpersisten"), (2, r"\bconsisten"), (2, r"\brevisit"),
               (2, r"\bretriev"), (2, r"\bspatial memory\b"), (2, r"\bforget"),
               (2, r"\bscene reconstruction\b")],
    "realtime": [(4, r"\breal[- ]?time\b"), (4, r"\bstreaming\b"), (3, r"\bdistill"),
                 (3, r"\bfew[- ]step\b"), (3, r"\bacceler"), (2, r"\bcach"),
                 (2, r"\blatency\b"), (2, r"\bthroughput\b"), (2, r"\bfps\b"),
                 (2, r"\bsparse attention\b"), (2, r"\bquantiz")],
}

# "Memory-efficient" is about VRAM, not about remembering the world. Same trap
# for footprint/VRAM phrasing -- these belong under the latency budget, not
# under long-horizon memory.
MEMORY_FALSE_FRIENDS = re.compile(
    r"memory[- ](?:efficien|footprint|cost|overhead|bound|usage)|"
    r"\b(?:gpu|device|vram|kv[- ]cache) memory\b", re.I)

SURVEY_RE = re.compile(r"\bsurvey\b|\ba roadmap\b|\breview\b(?!er)", re.I)

# Checked only by triage(), not by suggest_tags(): a paper the screening
# already filed as a method should not be reclassified because it happens to
# ship a benchmark alongside.
BENCHMARK_RE = re.compile(
    r"\bbenchmark|\bevaluat(?:ion|ing)\b|\bmetrics?\b|\btest-?bed\b|\barena\b", re.I)

# An action expressed as words. The list holds a dozen systems you steer by
# typing at them -- Incantation, PAN, Pandora, LongLive, Yume-1.5,
# Hunyuan-GameCraft-2 -- and every one of them cleared the action criterion by
# accident, on a "playable" or an "interactive control" elsewhere in the
# abstract. A paper whose whole contribution is the language interface says
# none of those words, scored 0/3, and was dropped before the inbox.
#
# The scope section rules out "a single prompt supplied up front", so every
# pattern below requires the prompt to be doing per-step, per-entity or
# mid-rollout work. "text prompt", "text-to-video" and "text-guided" are
# deliberately absent: they match a caption written before generation starts,
# which is the whole of text-to-video and none of this list.
#
# Measured before keeping, on 1055 papers pulled by searching arXiv for prompt
# and language vocabulary -- a corpus far denser in text-to-video than a day's
# window is, so an upper bound on the noise. It admitted four papers that were
# being dropped, two of them wanted, and lost none. It also moves Incantation,
# Pandora, LongLive and ShotStream from a supporting section to `systems`,
# which is where a human had already filed them by hand.
LANGUAGE_ACTION = [
    r"\b(?:natural language|language|text|prompts?)\s+as\s+(?:an?|the)?\s*"
    r"(?:action|control|interface)",
    r"\baction interface\b", r"\bnatural language action",
    r"\b(?:per|each)[- ](?:step|frame|chunk|shot|entity|event)\s+"
    r"(?:text|prompt|instruction|caption)",
    r"\bprompt switch", r"\bswitching prompts\b", r"\bstreaming prompts?\b",
    r"\bmulti[- ]event prompt", r"\btext intervention", r"\bin[- ]video instruction",
    r"\btext[- ]controlled\b", r"\binstruction[- ]following (?:world|game|video|interactive)",
]

# Evidence for each of the three scope criteria. Presence is suggestive, not
# proof -- a human still reads the paper before it enters the main list.
CRITERIA = {
    "action": [
        r"\baction[- ]condition", r"\bper[- ](?:step|frame) action", r"\bkeyboard\b",
        r"\bmouse\b", r"\bcontrol signal", r"\buser (?:input|action|control)",
        r"\bagent action", r"\binteractive control", r"\bplayable\b",
        r"\bcamera (?:control|trajector)", r"\blatent action",
    ] + LANGUAGE_ACTION,
    "causal": [
        r"\bcausal\b", r"\bautoregressive\b", r"\bstreaming\b", r"\breal[- ]?time\b",
        r"\bframe[- ]by[- ]frame\b", r"\bon[- ]the[- ]fly\b", r"\bnext[- ]frame\b",
        r"\binteractive(?:ly)? generat", r"\bchunk[- ]wise\b",
    ],
    "state": [
        r"\bmemory\b", r"\bpersisten", r"\blong[- ](?:term|horizon)\b",
        r"\bconsisten", r"\brevisit", r"\bworld state\b", r"\bspatial memory\b",
        r"\bretriev", r"\bscene (?:memory|reconstruction)\b",
    ],
}

# Efficiency work on video diffusion is the substrate the real-time sections
# are built on, but a paper about quadratic attention cost has no reason to say
# "causal", "streaming" or "interactive" anywhere -- it scores 0/3 on the
# criteria above and would never reach the inbox. Requiring a video anchor
# alongside the efficiency vocabulary keeps image-only and LLM-only efficiency
# work out.
VIDEO_ANCHOR_RE = re.compile(r"\bvideo\b|\bframes?\b|\bvdits?\b|\bworld model", re.I)
EFFICIENCY_RE = re.compile(
    r"\bsparse attention\b|\bsparsit|\bkv[- ]?cache|\bquadratic\b|\bearly[- ]exit\b|"
    r"\bdistill|\bfew[- ]step\b|\bone[- ]step\b|\bquantiz|\bcaching\b|\bthroughput\b|"
    r"\bspeed-?up\b|\bacceler|\bflops\b|\btoken (?:prun|merg|reduc|select)|"
    r"\binference (?:cost|latency|efficien)|\befficient (?:infer|attention|generation)",
    re.I)


def is_efficiency_substrate(title, abstract):
    """True for video-generation efficiency papers that meet no scope criterion
    but still belong under Real-Time & Streaming Generation."""
    blob = f"{title} {abstract or ''}"
    return bool(VIDEO_ANCHOR_RE.search(blob) and EFFICIENCY_RE.search(blob))


NAME_STOPWORDS = {
    "a", "an", "the", "toward", "towards", "is", "can", "what", "how", "why",
    "from", "beyond", "learning", "understanding", "exploring", "rethinking",
    "scaling", "simulating", "adapting", "evaluating", "benchmarking", "on",
    "do", "does", "are", "when", "where", "in", "it", "we", "one", "two",
    "generative", "video", "world", "interactive", "efficient", "long",
}
NAMEY_RE = re.compile(r"[A-Z0-9].*[A-Z0-9]|\d|-")


def title_tags(title):
    """-> every tech tag the title claims outright, and nothing on a silence.

    Separate from suggest_tags because it is used to *enrich*: a survey about
    long-horizon memory is still a survey, and a fallback tag bolted onto it
    would be a guess wearing the same clothes as a claim.
    """
    low = title.lower()
    hits = {key: sum(bool(re.search(p, low)) for p in pats)
            for key, pats in DECISIVE_TITLE_RULES.items()}
    if MEMORY_FALSE_FRIENDS.search(title):
        hits["memory"] = 0
        hits["realtime"] += 1
    return [k for k in TECH_TAGS if hits[k]]


def suggest_tags(title, abstract):
    """-> every tech tag the paper earns, most specific first.

    A title that says three things gets three tags. This is the one place where
    tags differ from the sections they replaced, and it is the entire point:
    "Action-Conditioned Video World Models with Few-Step Distillation" is a
    control paper *and* a real-time paper, and picking one used to be a coin
    flip that silently emptied the other list.

    The abstract still only breaks a title-level silence, and still yields a
    single tag: an abstract mentions everything the work touches, so scoring it
    for multiple tags would give nearly every paper nearly every tag.
    """
    earned = title_tags(title)
    if earned:
        return earned

    low_abs = (abstract or "").lower()
    scores = {key: sum(w for w, p in pats if re.search(p, low_abs))
              for key, pats in ABSTRACT_RULES.items()}
    scores["datasets"] = 0
    if any(scores.values()):
        return [max(TECH_TAGS, key=lambda k: (scores[k], -TECH_TAGS.index(k)))]
    return ["realtime"]


def criteria_evidence(title, abstract):
    """-> {criterion: [matched phrases]} across title and abstract."""
    hay = f"{title} {abstract or ''}"
    found = {}
    for key, patterns in CRITERIA.items():
        hits = []
        for pat in patterns:
            m = re.search(pat, hay, re.I)
            if m:
                hits.append(m.group(0).lower())
        found[key] = sorted(set(hits))
    return found


def triage(title, abstract):
    """-> (tags, met_criteria_count, evidence).

    `systems` is earned only when all three criteria show evidence, and it does
    not stand alone: a system is also whatever its title says it is about, so
    "Action-Conditioned Video World Models with Few-Step Distillation" comes
    back as systems + control + realtime rather than as a choice between them.
    """
    evidence = criteria_evidence(title, abstract)
    met = sum(1 for hits in evidence.values() if hits)
    if SURVEY_RE.search(title):
        primary = "surveys"
    elif BENCHMARK_RE.search(title):
        primary = "benchmarks"
    elif met == 3:
        primary = "systems"
    else:
        return suggest_tags(title, abstract), met, evidence
    return [primary] + title_tags(title), met, evidence


def extract_name(title):
    """'Matrix-Game 2.0: An open-source...' -> 'Matrix-Game 2.0'; else None."""
    head, sep, _ = title.partition(":")
    if not sep:
        return None
    tokens = head.split()
    if not (1 <= len(tokens) <= 4):
        return None
    if tokens[0].lower() in NAME_STOPWORDS:
        return None
    if len(tokens) == 1:
        return head.strip() if head[:1].isupper() else None
    if any(NAMEY_RE.search(t) for t in tokens):
        return head.strip()
    return None
