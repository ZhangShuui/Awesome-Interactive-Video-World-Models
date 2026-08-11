# Agent review

The tedious half of maintaining this list is reading four abstracts a day to
decide whether a paper is an interactive video world model. That half is
delegated to a local Claude Code agent. The half that decides what the list
says — merging — is not.

```
GitHub Action (daily, cloud)     arXiv + blog watchlist -> candidate Issue
        │
        ▼
scripts/agent_review.py (daily, your machine)
        ├─ screening calls, 8 papers each            title + abstract, no tools
        ├─ 1 attribute call per accepted `systems`   reads the paper, WebFetch only
        ├─ writes data/papers.jsonl, data/agent-rejected.jsonl
        └─ opens a pull request
        │
        ▼
you                              merge, or don't
```

The same script also drives the two sources that cannot be windowed by date and
so never reach the daily Issue — see [the pipeline](candidate-pipeline.md):

```bash
python3 scripts/agent_review.py --openreview      # ICLR / NeurIPS / ICML sweep
python3 scripts/agent_review.py --venue CVPR2025  # one conference's proceedings
```

Both are the same machinery pointed at a different door: sweep, screen, write,
open a PR. They deduplicate by normalised title, because a paper that reaches
this list from OpenReview and from arXiv shares no identifier at all.

Screening is batched (`--screen-batch`, default 8) so a slow or malformed
response costs one batch rather than the run; the papers in a failed batch stay
`unsure` and come back next time.

**The toolset is pinned on both passes.** Screening runs with every tool denied
so it answers from the prompt, and the attribute pass gets `WebFetch` and
nothing else.

This is not a detail. Left unrestricted the headless agent inherits the full
default toolset and goes exploring instead of answering. Measured on the same
5-paper screening prompt:

| | wall clock | turns | cost | outcome |
| --- | --- | --- | --- | --- |
| default toolset | 241s | **24** | $1.15 | `error_during_execution` |
| every tool denied | 148s | **2** | $0.49 | success |

Twenty-four turns to classify five abstracts that were already in the prompt,
and it still fell over. Note that passing an *empty* `--allowed-tools` is not a
restriction — it is the same as passing no flag at all, which is exactly how
this shipped broken the first time. The tools have to be named.

The agent never pushes to `main`, and the script aborts if the working tree is
dirty. Every entry it adds is marked `"section_source": "agent"`, so
`scripts/validate.py --review` always shows what has not been confirmed by a
human.

## Running it

```bash
python3 scripts/agent_review.py --dry-run     # judge and print, write nothing
python3 scripts/agent_review.py               # judge, commit, open a PR
python3 scripts/agent_review.py --local --days 7   # skip the Issue, query arXiv
python3 scripts/agent_review.py --openreview       # sweep OpenReview
python3 scripts/agent_review.py --venue ECCV2024   # sweep one proceedings
```

A sweep proposes far more at once than a morning's arXiv does — OpenReview held
103 unseen candidates the first time it ran — so `--max-papers` (default 25)
matters there. Anything over the cap is simply not judged this run; sweep again
after merging.

Daily, in the background:

```bash
./agent/install-timer.sh          # systemd user timer, 02:30 UTC
./agent/install-timer.sh --remove
journalctl --user -u awesome-ivwm-review -f
```

Requires `claude` and `gh` on PATH, both already logged in.

## What the agent decides

**In, out, or unsure**, plus a section, from the title and abstract. `unsure` is
a first-class verdict: those papers stay in the inbox and are listed in the PR
under "Left for you". The prompt pushes toward `unsure` rather than a guess,
because a wrong `in` quietly corrupts the list.

**Attributes**, for accepted papers going to `systems` only. Those are the rows
the comparison table renders; a paper in a supporting section never needs them.
The agent fetches the paper, extracts backbone, action space, frame rate,
horizon and memory mechanism, and records **where each number came from** —
section, table or figure. That evidence is stored on the record and rendered in
[comparison.md](comparison.md) under "Where these came from", so a claim in the
table can be checked without reading the paper again.

The prompt forbids inferring a number that is not reported. A missing field
means "not reported", which is information; an invented one is damage.

## Rejections are reversible

Rejected papers go to `data/agent-rejected.jsonl` with the reason and the model
that made the call:

```json
{"id": "2608.07463", "title": "...", "date": "2026-08-10", "reason": "mirror reflection generation, not an interactive world model", "model": "claude-sonnet-5"}
```

That file is read by `arxiv_candidates.py`, so a rejection is not re-litigated
every day. Delete a line to put the paper back in circulation on the next
refresh. Rejections arrive in the pull request diff, so they get reviewed at the
same moment as the additions — the point being that what an automated reviewer
*discards* deserves as much attention as what it keeps.

`data/arxiv-ignore.txt` remains the permanent list, for matches that will never
belong.

## Models and cost

Both passes default to Sonnet. The split is kept because the two jobs are not
equally hard, and reading papers is the one worth paying more for if the
comparison table starts drifting:

| Pass | Default | Why |
| --- | --- | --- |
| Screening | `claude-sonnet-5` | Batched. The decision is mostly "is this even about generated video". |
| Reading papers | `claude-sonnet-5` | One call per paper, full text. Matched the hand-read reference paper on every field; see [Accuracy](#accuracy) for where it and Opus disagree. |

Override with `--screen-model` / `--judge-model`.

Measured on a real run of 16 candidates: **$0.99** to screen them in two batches
of eight, and **$0.41** to read the one paper that reached `systems` — $1.39 for
the run. Reading a paper costs about **$0.45–0.50** either way; the two tiers
differ far less here than the model names suggest, because the cost is dominated
by pulling the paper into context.

Every `claude -p` is a fresh session that re-sends the whole Claude Code system
prompt, so there is a fixed cost of roughly **$0.13 per call** regardless of how
much you ask. That is the entire argument for batching: sixteen papers screened
one-per-call would have spent $2 on overhead alone before answering anything.

A normal day is a 3-day window and a handful of candidates — one screening batch
and at most a paper or two read, so about **$1**. Today's figures are inflated
because the inbox was backfilled over 14 days.

To spend less: raise `--screen-batch` (fewer calls, less overhead, but one
timeout costs more work), or lower `--max-attrs` — reading papers is the
expensive half, and `--max-attrs 0` skips it entirely. `--max-papers` (default
25) and `--max-attrs` (default 5) cap a single run; anything over the cap stays
in the inbox for next time.

The reported figure comes from `total_cost_usd` in the CLI's result envelope,
which prices the session's tokens at API rates. Whether that lands as a
per-token bill or against a subscription's limits depends on how your `claude`
is authenticated. A run that is killed mid-call reports nothing, so the number
is a floor, not an audit.

## Accuracy

Checked against a paper that had already been read by hand — Matrix-Game 2.0
([2508.13009](https://arxiv.org/abs/2508.13009)). Both Sonnet and Opus matched
the human values on every field: `causal-diffusion`, 25 FPS, `implicit-context`,
open-source, and the same action space and horizon, with Section 4.2 and Table 3
cited for the frame rate.

Run head to head on a second paper ([2607.26037](https://arxiv.org/abs/2607.26037)),
they agreed on `backbone`, `fps` and `open_source` and split on `memory`: Opus
read it as `hybrid:retrieval+implicit-context` (an always-retained sink chunk
plus top-k retrieval), Sonnet as `retrieval`. Opus is closer, but this is the
field where a reader should expect judgement rather than transcription, and it
is the reason `memory` disagreements are worth a look during review.

Two papers is a sanity check, not an evaluation. Spot-check the comparison-table
rows in a PR before merging; those are the numbers a reader is most likely to
quote.

## When it goes wrong

- **`working tree is dirty`** — the script refuses to run on top of uncommitted
  work. Commit or stash.
- **`model output was not JSON`** — retried once, then the run aborts without
  writing. Nothing is half-applied.
- **A screening verdict is missing for some candidate** — treated as `unsure`,
  never as `in`.
- **The full-text read disagrees with the screen** (`in_scope: false`) — the
  paper is still added, with empty attributes and the disagreement recorded in
  the PR body, so you decide rather than the second call silently overruling the
  first.
