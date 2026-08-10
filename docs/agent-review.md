# Agent review

The tedious half of maintaining this list is reading four abstracts a day to
decide whether a paper is an interactive video world model. That half is
delegated to a local Claude Code agent. The half that decides what the list
says — merging — is not.

```
GitHub Action (daily, cloud)     arXiv -> candidate Issue
        │
        ▼
scripts/agent_review.py (daily, your machine)
        ├─ 1 screening call over all candidates      title + abstract
        ├─ 1 attribute call per accepted `systems`   reads the paper
        ├─ writes data/papers.jsonl, data/agent-rejected.jsonl
        └─ opens a pull request
        │
        ▼
you                              merge, or don't
```

The agent never pushes to `main`, and the script aborts if the working tree is
dirty. Every entry it adds is marked `"section_source": "agent"`, so
`scripts/validate.py --review` always shows what has not been confirmed by a
human.

## Running it

```bash
python3 scripts/agent_review.py --dry-run     # judge and print, write nothing
python3 scripts/agent_review.py               # judge, commit, open a PR
python3 scripts/agent_review.py --local --days 7   # skip the Issue, query arXiv
```

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

Two tiers, because the two jobs are not equally hard:

| Pass | Default | Why |
| --- | --- | --- |
| Screening | `claude-sonnet-5` | One batched call over all candidates. Cheap, and the decision is mostly "is this even about generated video". |
| Reading papers | `claude-opus-5` | One call per paper, full text, and the output goes into a comparison table people may rely on. |

Override with `--screen-model` / `--judge-model`.

Measured: about **$0.27** for a screening pass over a day's candidates, and
about **$0.55** per paper read. `--max-papers` (default 25) and `--max-attrs`
(default 5) cap a single run; anything over the cap stays in the inbox.

## Accuracy

Checked against a paper that had already been read by hand — Matrix-Game 2.0
([2508.13009](https://arxiv.org/abs/2508.13009)) — the agent matched the human
values on all five fields (`causal-diffusion`, 25 FPS, `implicit-context`,
open-source, and the same action space and horizon), and cited Section 4.2 and
Table 3 for the frame rate.

One paper is a sanity check, not an evaluation. Spot-check the comparison-table
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
