# Candidate pipeline

Four sources propose papers. Nothing enters the list without a maintainer
merging a pull request.

| Source | Cadence | Finds | Script |
| --- | --- | --- | --- |
| arXiv | daily, 01:30 UTC | preprints, which is most of the field | `arxiv_candidates.py` |
| Blog watchlist | daily, same job | Genie, Oasis, Marble — systems announced with no paper | `blog_candidates.py` |
| OpenReview | swept on demand | ICLR/NeurIPS/ICML papers, and the venue a paper was accepted to | `openreview_candidates.py` |
| Conference proceedings | swept per conference | CVPR/ICCV/ECCV/WACV/NeurIPS papers that never went to arXiv | `venue_candidates.py` |

The split is forced by what each source can answer. arXiv and RSS feeds can be
asked "what is new since Tuesday". OpenReview cannot — its searchable endpoint
ranks by relevance and ignores `sort` — and a proceedings page is published
once a year. So two sources tick daily and two are swept.

Every source applies the *same* scope rules, from `scripts/sources.py`. What
differs is the provenance filter each one owns: an arXiv category, an
OpenReview venue, a conference title match, a watchlist entry.

## Why not just search titles for "world"

Because the systems that matter most are called Genie, Oasis, DIAMOND and
GameNGen. Title matching on one keyword misses them and drags in every
economics and climate paper that borrowed the phrase "world model".

So recall is phrase-based over title and abstract (`QUERY_PHRASES` in
`scripts/sources.py`), and the narrowing happens afterwards:

1. Provenance. For arXiv, the paper must carry one of cs.CV, cs.LG, cs.AI,
   cs.MM, eess.IV — *any* of its categories will do, so this only excludes work
   that never cross-listed into vision or learning. cs.RO and cs.GR were
   removed: this list is about generated video you can act inside, not about
   robots or renderers, and the robot world models it does want cross-list
   cs.CV or cs.LG anyway.
2. Off-topic stems (protein, econom, climate, …) are dropped outright.
3. A **visual gate** requires the paper to be about pixels at all — an LLM's
   internal world model is out no matter how well it scores.
4. Each survivor is scored for evidence of the three scope criteria. A paper
   showing evidence for all three is proposed for `systems`; otherwise it is
   proposed for the supporting section its keywords fit. Scoring zero drops it.
5. **Except** for surveys, benchmarks, and the *efficiency substrate*: video
   diffusion work on sparse attention, KV caching, distillation, early exit and
   the like. Those papers have no reason to say "causal" or "streaming"
   anywhere, so they score 0/3 and were being dropped — while the `realtime`
   section already held a dozen of exactly their genre. `is_efficiency_substrate`
   in `scripts/triage.py` admits them, and requires a video anchor so that
   image-only and LLM-only efficiency work stays out.

Scoring is evidence of a criterion, not satisfaction of it. It decides what is
worth two minutes of a maintainer's attention, nothing more.

## Keep the query phrases short

A longer phrase is not a narrower version of a shorter one. It is a different
phrase, matched verbatim, and this cost the list real papers: `"real-time video
generation"` does not match *"real-time streaming audio-video generation"*, so
Ripple, Vorch-Streamer, DUET and EchoCache were never proposed. Measured over
one seven-day window, five of the twelve original phrases returned **zero**
results and two — `"world model"` and `"video diffusion"` — were carrying the
entire query.

Two rules keep that from coming back, both pinned in `tests/test_sources.py`:

- No phrase may contain another phrase. `"long video generation"` cannot match
  anything `"video generation"` misses, and keeping both hides which one works.
- Search backends stem, so `"action-conditioned"` and `"action-conditional"`
  return the same set. One is enough.

When you add a phrase, measure it: run the window before and after and count
what it actually adds. An extra phrase is free in API calls — they are OR'd
into one query — and costs only precision, which the review agent absorbs.

### What "forcing" cost, measured

Worth writing down, because the answer was not the obvious one and the next
person to notice the naming genre will want to add it again.

"X Forcing" is a naming convention in this field — Diffusion Forcing, Self
Forcing, Rolling Forcing, Memory Forcing, Causal Forcing — and the list holds 33
of them, so the phrase looks overdue. Measured over 30 days:

| | |
| --- | --- |
| the 33 papers already caught by the other phrases | **31** |
| `all:"forcing"` raw hits | 800+ (paging cap) |
| dropped by the category gate | 553 — `math.CO` zero forcing, `physics.flu-dyn` and `math.AP` baroclinic and tidal forcing, `cond-mat` |
| reaching the inbox | 45 |
| of those, new *and* relevant | **0** |

Papers in the genre say "video generation" or "autoregressive video" in their
abstracts as a matter of course, so the query already had them. What the phrase
adds instead is force: search stems `forcing` to `force`/`forced`, and
grasp-force, contact-force and force-torque papers discuss scenes and images, so
they clear the visual gate and land in the inbox. Restricting to `ti:` does not
help — titles are where zero forcing and tidal forcing live too.

It is in the list anyway, as a maintainer's call: the bet is that the genre
keeps growing and eventually produces a paper that drops the vocabulary the rest
of the query depends on. Narrowing the category gate at the same time took most
of the cost back. If the inbox starts filling with haptics, this is the phrase
to remove first.

## The daily job

1. `.github/workflows/arxiv-candidates.yml` runs at 01:30 UTC, and on demand.
2. `scripts/arxiv_candidates.py` queries arXiv over the last N days;
   `scripts/blog_candidates.py` polls the watchlist in `data/sources.json`.
3. Papers already in `data/papers.jsonl`, listed in `data/arxiv-ignore.txt`,
   already rejected, or sitting in an open pipeline PR are skipped.
4. One Issue labeled `arxiv-candidates` is created or updated with both
   reports. Refreshing preserves ticks and section corrections, so review in
   progress is never lost.
5. A maintainer comments `/create-pr`.
6. `.github/workflows/arxiv-candidates-create-pr.yml` runs
   `scripts/apply_issue_selections.py`, which appends the ticked papers to
   `data/papers.jsonl`, then regenerates `README.md` and `docs/comparison.md`
   and opens a PR.

Because the README is generated, this pipeline never edits markdown. The worst
a bad parse can do is add a row to a data file — reviewable in a diff, revertible
in one commit.

A local [review agent](agent-review.md) can do step 5's reading for you.

## The sweeps

Run these when a conference publishes, or every few months:

```bash
python3 scripts/agent_review.py --openreview        # judge and open a PR
python3 scripts/agent_review.py --venue CVPR2025

python3 scripts/openreview_candidates.py --output -  # or just look
python3 scripts/venue_candidates.py --venue NeurIPS2024 --output -
```

Both deduplicate against the list by **normalised title**, not by id — nearly
every hit is also on arXiv under a completely different identifier.

**OpenReview** is also the only source that knows a paper became a spotlight
rather than a preprint, and it records that venue on the entry. It skips
withdrawn, desk-rejected and under-review submissions by default
(`--include-submissions` to see them), and it ignores the re-indexed DBLP and
journal records its search returns alongside real venues.

**Proceedings** are filtered on title before any abstract is read: CVPR 2025 is
2,871 papers and the index carries no abstracts. That trade is one-directional
— a paper whose title says nothing topical is never seen — so widen
`--title-re` when sweeping a venue where it matters.

## The blog watchlist

`data/sources.json` lists the labs worth watching, each `feed` (an RSS or Atom
feed, reliable) or `page` (a listing page scraped for links, used where a lab
publishes none). Add an entry when a lab starts shipping work this list should
track.

Its filter is deliberately narrower than the shared vocabulary. A lab blog is
mostly funding rounds and product launches, and `"video generation"` appears in
all of them; what distinguishes an interactive world model in marketing prose
is the claim to be a *world*, a *simulator*, or something you can *play*.

Titles from `page` sources are scraped from anchor text and are provisional.
Nothing from this source should be merged without opening the link — the
`reports` section promises hand-checked URLs, and a keyword match on a feed
summary is not that.

## Reviewing an inbox

1. Open the Issue labeled `arxiv-candidates`.
2. Tick the papers that belong.
3. The section in backticks is a keyword guess. Edit it in place if it is wrong;
   your edit wins over the guess.
4. Comment `/create-pr`.
5. Review the PR. Unticked candidates return in the next refresh.

Matches that keep coming back and never belong go in `data/arxiv-ignore.txt`,
one id per line, `#` for comments.

## Running it locally

```bash
python3 scripts/arxiv_candidates.py --days 7 --output -
python3 scripts/blog_candidates.py --days 30 --output -
```

Without a network, replay a saved Atom feed:

```bash
python3 scripts/arxiv_candidates.py --feed-file tests/data/sample-feed.xml --output -
```

## Tuning

- `QUERY_PHRASES` in `scripts/sources.py` — recall, shared by every source.
  Add a phrase when a paper you expected never showed up, and read the rules
  above first.
- `proposal()` in `scripts/sources.py` — the one admission decision.
- `OFF_TOPIC_RE`, `VISUAL_GATE_RE` — precision.
- `CRITERIA` in `scripts/triage.py` — the three-criteria evidence patterns.
- `DECISIVE_TITLE_RULES` / `ABSTRACT_RULES` — which supporting section is suggested.
- `VENUE_RE`, `NOT_ACCEPTED_RE` in `scripts/openreview_candidates.py` — which
  venues count and which submissions are real.
- `TITLE_PREFILTER` in `scripts/venue_candidates.py` — what gets read at all.
- `WATCH_RE` in `scripts/blog_candidates.py` — release announcement vs press release.

These patterns are stems, not whole words. A trailing `\b` on a stem silently
disables it, which is why `tests/test_pipeline.py` pins the off-topic filter.

## Known gaps

- **A long outage loses papers.** The daily window is 3 days, so the job can
  fail twice and still catch up. Fail for four days and those papers are gone;
  there is no watermark. Re-run by hand with `--days`.
- **arXiv v1 only.** A paper cross-listed into cs.CV later, or rewritten in v2,
  is never reconsidered.
- **`--max-results` truncates.** A 3-day window returns a couple of dozen
  papers; a 30-day backfill returns hundreds and will hit the cap. It now warns
  on stderr instead of silently returning a short list.
- **SIGGRAPH and the ACM DL** are not covered by any source here.

## APIs and terms

This pipeline uses the public [arXiv API](https://info.arxiv.org/help/api/user-manual.html)
under its [Terms of Use](https://info.arxiv.org/help/api/tou.html), with at
least 3.1 seconds between paged requests. Thank you to arXiv for use of its open
access interoperability. OpenReview, CVF Open Access, ECVA and the NeurIPS
proceedings are read through their public endpoints at one request per second.

## Repository setting

The comment-triggered workflow pushes a branch and opens a PR with
`GITHUB_TOKEN`. Enable **Allow GitHub Actions to create and approve pull
requests** under **Settings → Actions → General → Workflow permissions**.
