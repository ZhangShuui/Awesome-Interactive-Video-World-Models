# arXiv candidate pipeline

A daily job proposes recent papers in a single GitHub Issue. Nothing enters the
list without a maintainer ticking a box.

## Why not just search titles for "world"

Because the systems that matter most are called Genie, Oasis, DIAMOND and
GameNGen. Title matching on one keyword misses them and drags in every
economics and climate paper that borrowed the phrase "world model".

So recall is phrase-based over title and abstract (see `QUERY_PHRASES` in
`scripts/arxiv_candidates.py`), and the narrowing happens afterwards:

1. arXiv category must be one of cs.CV, cs.LG, cs.AI, cs.RO, cs.GR, cs.MM, eess.IV.
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
worth two minutes of a maintainer's attention, nothing more. Measured over one
7-day window, the escape hatch costs about one extra candidate per day.

## How it runs

1. `.github/workflows/arxiv-candidates.yml` runs daily at 01:30 UTC, and on demand.
2. `scripts/arxiv_candidates.py` queries the arXiv API over the last N days.
3. Papers already in `data/papers.jsonl`, listed in `data/arxiv-ignore.txt`, or
   sitting in an open pipeline PR are skipped.
4. One Issue labeled `arxiv-candidates` is created or updated with the report.
   Refreshing preserves ticks and section corrections, so review in progress is
   never lost.
5. A maintainer comments `/create-pr`.
6. `.github/workflows/arxiv-candidates-create-pr.yml` runs
   `scripts/apply_issue_selections.py`, which appends the ticked papers to
   `data/papers.jsonl`, then regenerates `README.md` and `docs/comparison.md`
   and opens a PR.

Because the README is generated, this pipeline never edits markdown. The worst
a bad parse can do is add a row to a data file — reviewable in a diff, revertible
in one commit.

## Reviewing an inbox

1. Open the Issue labeled `arxiv-candidates`.
2. Tick the papers that belong.
3. The section in backticks is a keyword guess. Edit it in place if it is wrong;
   your edit wins over the guess.
4. Comment `/create-pr`.
5. Review the PR. Unticked candidates return in the next refresh.

Matches that keep coming back and never belong go in `data/arxiv-ignore.txt`,
one arXiv id per line, `#` for comments.

## Running it locally

```bash
python3 scripts/arxiv_candidates.py --days 7 --output -
```

Without a network, replay a saved Atom feed:

```bash
python3 scripts/arxiv_candidates.py --feed-file tests/data/sample-feed.xml --output -
```

## Tuning

- `QUERY_PHRASES` — recall. Add a phrase when a paper you expected never showed up.
- `CRITERIA` in `scripts/triage.py` — the three-criteria evidence patterns.
- `DECISIVE_TITLE_RULES` / `ABSTRACT_RULES` — which supporting section is suggested.
- `OFF_TOPIC_RE`, `VISUAL_GATE_RE` — precision.

These patterns are stems, not whole words. A trailing `\b` on a stem silently
disables it, which is why `tests/test_pipeline.py` pins the off-topic filter.

## Repository setting

The comment-triggered workflow pushes a branch and opens a PR with
`GITHUB_TOKEN`. Enable **Allow GitHub Actions to create and approve pull
requests** under **Settings → Actions → General → Workflow permissions**.

## arXiv API

This pipeline uses the public [arXiv API](https://info.arxiv.org/help/api/user-manual.html)
under its [Terms of Use](https://info.arxiv.org/help/api/tou.html), with at
least 3.1 seconds between paged requests. Thank you to arXiv for use of its open
access interoperability.
