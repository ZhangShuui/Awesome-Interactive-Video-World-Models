#!/usr/bin/env python3
"""Run the daily review with a local Claude Code agent, then open a pull request.

The agent does what a maintainer does: read the candidates, judge each against
the three scope criteria, place it in a section, and for anything entering the
main list, read the paper and fill in the comparison-table row. It stops there.
Merging is a human's job and this script never pushes to the default branch.

    inbox Issue (or a local arXiv query)
      -> screening calls in small batches           (title + abstract, no tools)
      -> one attribute call per accepted `systems` paper (reads the paper)
      -> data/papers.jsonl + data/agent-rejected.jsonl
      -> branch, commit, `gh pr create`

Both passes run with the toolset pinned: screening gets no tools at all so it
answers from the prompt, and the attribute pass gets WebFetch and nothing else.

Rejections are written to data/agent-rejected.jsonl rather than dropped, so the
next inbox refresh does not propose them forever and so a human can see, in the
PR diff, exactly what the agent threw away.

Usage:
  python3 scripts/agent_review.py --dry-run          # judge and print, touch nothing
  python3 scripts/agent_review.py                    # judge, commit, open a PR
  python3 scripts/agent_review.py --local --days 7   # skip the Issue, query arXiv
"""
import argparse
import json
import re
import subprocess
import sys
import textwrap
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import triage  # noqa: E402
from arxiv_candidates import CANDIDATE_RE, decode  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "agent" / "prompts"
FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$")

# Screening judges text that is already in the prompt. Left unrestricted the
# headless agent inherits the full default toolset and goes looking -- fetching
# each arXiv page, reading the repo -- which turns a one-shot classification
# into a many-minute session. Naming the tools to deny is the only way to say
# "answer from what you were given"; an empty --allowed-tools is not a
# restriction, it is no flag at all.
DENY_ALL_TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep",
                  "WebFetch", "WebSearch", "Task", "NotebookEdit", "TodoWrite"]
SCREEN_TOOLS = {"disallowed": DENY_ALL_TOOLS}
ATTR_TOOLS = {"allowed": ["WebFetch"],
              "disallowed": [t for t in DENY_ALL_TOOLS if t != "WebFetch"]}


# --- claude headless ---------------------------------------------------------

class AgentError(RuntimeError):
    pass


def call_claude(prompt, model, tools, timeout):
    """-> (parsed_json, cost_usd). Raises AgentError on anything unusable."""
    cmd = ["claude", "-p", prompt, "--model", model, "--output-format", "json"]
    for flag, key in (("--allowed-tools", "allowed"), ("--disallowed-tools", "disallowed")):
        names = (tools or {}).get(key)
        if names:
            cmd += [flag, *names]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise AgentError(f"claude timed out after {timeout}s")
    if proc.returncode != 0:
        raise AgentError(f"claude exited {proc.returncode}: {proc.stderr.strip()[:300]}")
    try:
        envelope = json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise AgentError(f"claude did not return JSON: {proc.stdout[:300]}")
    if envelope.get("is_error") or envelope.get("subtype") != "success":
        raise AgentError(f"claude reported {envelope.get('subtype')}: "
                         f"{str(envelope.get('result'))[:300]}")
    cost = float(envelope.get("total_cost_usd") or 0.0)
    return extract_json(envelope.get("result") or ""), cost


def extract_json(result):
    """First complete JSON value in the model's reply.

    Told to return only JSON, the model still sometimes fences it, prefaces it,
    or appends a sentence of commentary. `json.loads` rejects all three and the
    retry costs a whole extra call, so parse the first value and ignore what
    surrounds it."""
    body = FENCE_RE.sub("", result.strip())
    start = min((i for i in (body.find("{"), body.find("[")) if i != -1), default=-1)
    if start == -1:
        raise AgentError(f"no JSON in model output: {body[:300]}")
    try:
        value, _ = json.JSONDecoder().raw_decode(body[start:])
    except json.JSONDecodeError as exc:
        raise AgentError(f"model output was not JSON ({exc}): {body[:300]}")
    return value


def call_with_retry(prompt, model, tools, timeout, attempts=2):
    last = None
    for attempt in range(attempts):
        try:
            return call_claude(prompt, model, tools, timeout)
        except AgentError as exc:
            last = exc
            if attempt + 1 < attempts:
                print(f"  retrying after: {exc}", file=sys.stderr)
                time.sleep(5)
    raise last


# --- prompt assembly ---------------------------------------------------------

def scope_text():
    """The Scope section of the README, so the prompt cannot drift from the
    published criteria."""
    template = (ROOT / "data" / "README.template.md").read_text(encoding="utf-8")
    match = re.search(r"^## Scope$.*?(?=^## )", template, re.M | re.S)
    if not match:
        raise SystemExit("could not find the Scope section in data/README.template.md")
    return match.group(0).strip()


def sections_text():
    sections = json.loads((ROOT / "data" / "sections.json").read_text(encoding="utf-8"))
    return "\n".join(f"- `{s['key']}` — {s['title']}. {s['blurb']}" for s in sections)


def render(template_name, **fields):
    text = (PROMPTS / template_name).read_text(encoding="utf-8")
    for key, value in fields.items():
        text = text.replace("{{" + key + "}}", value)
    leftover = re.findall(r"\{\{(\w+)\}\}", text)
    if leftover:
        raise SystemExit(f"{template_name}: unfilled placeholders {leftover}")
    return text


def candidates_block(candidates):
    out = []
    for i, cand in enumerate(candidates, 1):
        abstract = " ".join((cand.get("abstract") or "").split())
        out.append(textwrap.dedent(f"""\
            ### {i}. {cand['id']}
            Title: {cand['title']}
            Keyword suggestion (not authoritative): {cand.get('section') or '-'}
            Abstract: {abstract or '(not available — judge from the title and say unsure if you cannot)'}
            """))
    return "\n".join(out)


# --- candidate sources -------------------------------------------------------

def gh(*args, check=True):
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemExit(f"gh {' '.join(args)} failed: {proc.stderr.strip()[:300]}")
    return proc.stdout


BARE_ARXIV_ID_RE = re.compile(r"\b\d{4}\.\d{4,5}\b")


def ids_awaiting_merge():
    """Papers this agent has already judged but whose PR is still open.

    A run leaves the inbox untouched -- the Issue is the cloud workflow's to
    manage -- so without this a second run re-screens everything the first one
    decided, and pays for it twice. The PR body names every accepted id as a
    link and every rejected id in backticks, so scanning it covers both."""
    raw = gh("pr", "list", "--state", "open", "--limit", "50", "--json", "body",
             check=False)
    try:
        prs = json.loads(raw or "[]")
    except json.JSONDecodeError:
        return set()
    ids = set()
    for pr in prs:
        ids |= set(BARE_ARXIV_ID_RE.findall(pr.get("body") or ""))
    return ids


def candidates_from_issue():
    """-> (issue_number, [candidate]). Abstracts are not in the Issue body, so
    they are refetched from the arXiv API."""
    raw = gh("issue", "list", "--label", "arxiv-candidates", "--state", "open",
             "--limit", "1", "--json", "number,body")
    issues = json.loads(raw or "[]")
    if not issues:
        return None, []
    body = issues[0]["body"] or ""
    found = []
    for match in CANDIDATE_RE.finditer(body):
        payload = decode(match.group("payload"))
        if payload:
            payload["section"] = match.group("section")
            payload["checked"] = match.group("checked").lower() == "x"
            found.append(payload)

    import arxiv_candidates as ac
    handled = (ac.known_ids(ROOT / "data" / "papers.jsonl")
               | ac.ignored_ids(ROOT / "data" / "arxiv-ignore.txt")
               | rejected_ids()
               | ids_awaiting_merge())
    fresh = [c for c in found if not c["checked"] and c["id"] not in handled]
    skipped = len(found) - len(fresh) - sum(1 for c in found if c["checked"])
    if skipped:
        print(f"[agent] skipping {skipped} candidate(s) already in the list, "
              f"already rejected, or sitting in an open PR")
    return issues[0]["number"], fresh


def candidates_locally(days, max_results):
    import arxiv_candidates as ac
    papers = ac.fetch_papers(days, max_results, 60.0, 2, 5.0)
    known = ac.known_ids(ROOT / "data" / "papers.jsonl")
    known |= ac.ignored_ids(ROOT / "data" / "arxiv-ignore.txt")
    known |= rejected_ids()
    out = []
    for paper in papers:
        if paper["id"] in known:
            continue
        blob = f"{paper['title']} {paper['abstract']}"
        if not set(paper["categories"]) & ac.ALLOWED_CATEGORIES:
            continue
        if ac.OFF_TOPIC_RE.search(blob) or not ac.VISUAL_GATE_RE.search(blob):
            continue
        section, met, _ = triage.triage(paper["title"], paper["abstract"])
        if (met == 0 and section not in ("surveys", "benchmarks")
                and not triage.is_efficiency_substrate(paper["title"], paper["abstract"])):
            continue
        out.append({"id": paper["id"], "title": paper["title"],
                    "abstract": paper["abstract"], "date": paper["date"],
                    "section": section})
    return None, out


def candidates_from_rejections():
    """Re-open everything a past run turned down, to be judged against the
    scope as it reads today.

    A rejection is a decision made under one set of rules. Widen the scope and
    some of those decisions were right at the time and wrong now -- which is
    only recoverable because rejections are logged with their reasons instead of
    being dropped. Papers already in the list are not re-proposed."""
    import arxiv_candidates as ac
    rows = []
    if REJECTED.exists():
        for line in REJECTED.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#"):
                rows.append(json.loads(line))
    have = ac.known_ids(ROOT / "data" / "papers.jsonl")
    # Deliberately no `date`: the rejection row records when it was rejected,
    # not when the paper was published. fetch_abstracts fills the real one.
    return None, [{"id": r["id"], "title": r["title"], "section": None,
                   "prior_reason": r.get("reason", "")}
                  for r in rows if r["id"] not in have]


def drop_rejections(ids):
    """Remove recovered papers from the rejection log."""
    if not REJECTED.exists():
        return
    kept = []
    for line in REJECTED.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            kept.append(line)
            continue
        if json.loads(line)["id"] not in ids:
            kept.append(line)
    REJECTED.write_text("".join(l + "\n" for l in kept), encoding="utf-8")


def fetch_abstracts(candidates):
    """Issue bodies carry no abstract; screening without one is guesswork."""
    import arxiv_candidates as ac
    missing = [c for c in candidates if not c.get("abstract")]
    for batch_start in range(0, len(missing), 50):
        batch = missing[batch_start:batch_start + 50]
        query = " OR ".join(f"id:{c['id']}" for c in batch)
        raw = ac.fetch_page(query, 0, len(batch), 60.0, 2, 5.0)
        by_id = {p["id"]: p for p in ac.parse_feed(raw)}
        for cand in batch:
            paper = by_id.get(cand["id"])
            if paper:
                cand["abstract"] = paper["abstract"]
                cand.setdefault("date", paper["date"])
        if batch_start + 50 < len(missing):
            time.sleep(3.2)
    return candidates


# --- data files --------------------------------------------------------------

REJECTED = ROOT / "data" / "agent-rejected.jsonl"


def rejected_ids():
    if not REJECTED.exists():
        return set()
    out = set()
    for line in REJECTED.read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.lstrip().startswith("#"):
            out.add(json.loads(line)["id"])
    return out


def append_rejections(rows):
    with REJECTED.open("a", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def append_records(records):
    papers = ROOT / "data" / "papers.jsonl"
    existing = [json.loads(l) for l in papers.read_text(encoding="utf-8").splitlines() if l.strip()]
    have = {r["id"] for r in existing}
    fresh = [r for r in records if r["id"] not in have]
    merged = existing + fresh
    merged.sort(key=lambda r: (r.get("date") or "", r["id"]), reverse=True)
    papers.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in merged),
                      encoding="utf-8")
    return fresh


# --- git ---------------------------------------------------------------------

def git(*args, check=True):
    proc = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {proc.stderr.strip()[:300]}")
    return proc.stdout.strip()


def require_clean_tree():
    if git("status", "--porcelain"):
        raise SystemExit("working tree is dirty; commit or stash before an agent run")


# --- main --------------------------------------------------------------------

def screen(candidates, model, timeout, batch_size):
    """Batched so one slow or malformed response costs one batch, not the run.
    Anything without a verdict stays unsure, which keeps it in the inbox."""
    by_id, cost = {}, 0.0
    batches = [candidates[i:i + batch_size]
               for i in range(0, len(candidates), batch_size)]
    for n, chunk in enumerate(batches, 1):
        prompt = render("screen.md", SCOPE=scope_text(), SECTIONS=sections_text(),
                        CANDIDATES=candidates_block(chunk))
        print(f"  batch {n}/{len(batches)} ({len(chunk)} papers)", flush=True)
        try:
            verdicts, call_cost = call_with_retry(prompt, model, SCREEN_TOOLS, timeout)
        except AgentError as exc:
            print(f"  batch {n} failed, its papers stay unsure: {exc}", file=sys.stderr)
            continue
        cost += call_cost
        if not isinstance(verdicts, list):
            print(f"  batch {n} did not return an array, its papers stay unsure",
                  file=sys.stderr)
            continue
        for v in verdicts:
            if isinstance(v, dict) and v.get("id"):
                by_id[v["id"]] = v
    missing = [c["id"] for c in candidates if c["id"] not in by_id]
    if missing:
        print(f"  no verdict for {len(missing)} candidate(s); treating as unsure",
              file=sys.stderr)
    return by_id, cost


def read_attrs(candidate, model, timeout):
    prompt = render("attrs.md", ID=candidate["id"], TITLE=candidate["title"])
    return call_with_retry(prompt, model, ATTR_TOOLS, timeout)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--screen-model", default="claude-sonnet-5",
                    help="model for the bulk in/out pass (default: %(default)s)")
    ap.add_argument("--judge-model", default="claude-sonnet-5",
                    help="model for reading papers and filling attributes "
                         "(default: %(default)s)")
    ap.add_argument("--max-papers", type=int, default=25,
                    help="hard cap on candidates screened in one run")
    ap.add_argument("--max-attrs", type=int, default=5,
                    help="hard cap on full-text reads in one run; the rest are "
                         "added with empty attrs and picked up next time")
    ap.add_argument("--rejudge", action="store_true",
                    help="re-judge everything in data/agent-rejected.jsonl "
                         "against the scope as it reads today")
    ap.add_argument("--local", action="store_true",
                    help="query arXiv directly instead of reading the inbox Issue")
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--max-results", type=int, default=400)
    ap.add_argument("--screen-batch", type=int, default=8,
                    help="candidates per screening call (default: %(default)s)")
    ap.add_argument("--screen-timeout", type=float, default=600)
    ap.add_argument("--attr-timeout", type=float, default=600)
    ap.add_argument("--dry-run", action="store_true",
                    help="judge and report; write nothing, commit nothing")
    args = ap.parse_args()
    # Under systemd or a background shell stdout is block-buffered, so a run
    # that is working looks identical to one that is wedged. Progress is the
    # only thing you have while a call takes minutes.
    sys.stdout.reconfigure(line_buffering=True)

    if not args.dry_run:
        require_clean_tree()

    if args.rejudge:
        issue_number, candidates = candidates_from_rejections()
    elif args.local:
        issue_number, candidates = candidates_locally(args.days, args.max_results)
    else:
        issue_number, candidates = candidates_from_issue()
    if not candidates:
        print("[agent] nothing to review")
        return
    if len(candidates) > args.max_papers:
        print(f"[agent] {len(candidates)} candidates, capping at {args.max_papers}; "
              f"the rest stay in the inbox for the next run")
        candidates = candidates[:args.max_papers]
    fetch_abstracts(candidates)

    print(f"[agent] screening {len(candidates)} candidate(s) with {args.screen_model}")
    verdicts, cost = screen(candidates, args.screen_model, args.screen_timeout,
                            args.screen_batch)

    accepted, rejected, unsure = [], [], []
    valid = {s["key"] for s in json.loads((ROOT / "data" / "sections.json").read_text())}
    for cand in candidates:
        v = verdicts.get(cand["id"]) or {"verdict": "unsure", "reason": "no verdict returned"}
        verdict = v.get("verdict")
        if verdict == "in":
            section = v.get("section")
            if section not in valid:
                print(f"  warning: {cand['id']} -> invalid section {section!r}, "
                      f"falling back to the keyword suggestion", file=sys.stderr)
                section = cand.get("section") if cand.get("section") in valid else "realtime"
            accepted.append({**cand, "section": section, "reason": v.get("reason", ""),
                             "criteria": v.get("criteria") or {}})
        elif verdict == "out":
            rejected.append({**cand, "reason": v.get("reason", "")})
        else:
            unsure.append({**cand, "reason": v.get("reason", "")})

    print(f"[agent] in {len(accepted)} · out {len(rejected)} · unsure {len(unsure)} "
          f"· ${cost:.3f}")
    for row in accepted:
        print(f"    IN     {row['section']:<11} {row['id']}  {row['title'][:58]}")
    for row in unsure:
        print(f"    UNSURE {'':<11} {row['id']}  {row['title'][:58]}")
    for row in rejected:
        print(f"    OUT    {'':<11} {row['id']}  {row['title'][:58]}")

    # Attributes only matter for the main list -- the comparison table is the
    # only consumer, and it renders `systems` rows and nothing else.
    targets = [r for r in accepted if r["section"] == "systems"][:args.max_attrs]
    attrs_by_id, evidence_by_id, notes = {}, {}, {}
    for i, row in enumerate(targets, 1):
        print(f"[agent] reading {row['id']} ({i}/{len(targets)}) with {args.judge_model}")
        try:
            result, call_cost = read_attrs(row, args.judge_model, args.attr_timeout)
        except AgentError as exc:
            print(f"  attribute read failed, leaving attrs empty: {exc}", file=sys.stderr)
            continue
        cost += call_cost
        if result.get("in_scope") is False:
            print(f"  reader disagrees with the screen: {result.get('note')}")
            notes[row["id"]] = f"full-text read disagreed: {result.get('note', '')}"
            continue
        attrs = {k: v for k, v in (result.get("attrs") or {}).items()
                 if v not in (None, "", [])}
        attrs_by_id[row["id"]] = attrs
        # Kept so the number in the table can be checked against the paper
        # without reading the whole paper again.
        evidence_by_id[row["id"]] = {k: v for k, v in (result.get("evidence") or {}).items()
                                     if v not in (None, "", [])}
        notes[row["id"]] = result.get("note", "")
        print(f"    {json.dumps(attrs, ensure_ascii=False)[:150]}  (${call_cost:.3f})")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    records = [{
        "id": row["id"],
        "name": triage.extract_name(row["title"]),
        "title": row["title"],
        "venue": None,
        "date": row.get("date"),
        "section": row["section"],
        "section_source": "agent",
        "links": {"paper": f"https://arxiv.org/abs/{row['id']}"},
        "attrs": attrs_by_id.get(row["id"], {}),
        **({"evidence": evidence_by_id[row["id"]]}
           if evidence_by_id.get(row["id"]) else {}),
    } for row in accepted]
    # `rejected_on`, not `date`: this is when the call was made, not when the
    # paper was published. Conflating them once set every recovered paper to
    # the day it was re-judged.
    rejections = [{"id": row["id"], "title": row["title"], "rejected_on": stamp,
                   "reason": row["reason"], "model": args.screen_model}
                  for row in rejected]

    print(f"[agent] total ${cost:.3f}")
    if args.dry_run:
        print("[agent] dry run, nothing written")
        return
    if not records and not rejections:
        print("[agent] no decisions to commit")
        return

    added = append_records(records)
    if args.rejudge:
        # They are already in the log; only the recovered ones move.
        drop_rejections({r["id"] for r in added})
    else:
        append_rejections(rejections)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_readme.py")], check=True)

    branch = f"agent/review-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}"
    git("switch", "-c", branch)
    git("add", "data/papers.jsonl", "data/agent-rejected.jsonl",
        "README.md", "docs/comparison.md")
    git("commit", "-m", f"Agent review: +{len(added)} paper(s), {len(rejections)} rejected")
    git("push", "-u", "origin", branch)

    body = pr_body(added, attrs_by_id, notes, rejections, unsure, cost,
                   args.screen_model, args.judge_model, issue_number)
    url = gh("pr", "create", "--base", "main", "--head", branch,
             "--title", f"Agent review: {len(added)} paper(s) for the list",
             "--body", body).strip()
    print(f"[agent] {url}")
    if issue_number:
        gh("issue", "comment", str(issue_number), "--body",
           f"A local agent reviewed this inbox and opened {url}.\n\n"
           f"Accepted {len(added)}, rejected {len(rejections)}, "
           f"left {len(unsure)} unsure for you. Rejections are recorded in "
           f"`data/agent-rejected.jsonl` in that PR and will not be proposed again "
           f"unless you delete the line.", check=False)


def pr_body(added, attrs_by_id, notes, rejections, unsure, cost, screen_model,
            judge_model, issue_number):
    lines = [
        "Reviewed by a local Claude Code agent. **Nothing here has been read by a "
        "human yet — merging is that review.**", "",
        f"Screened with `{screen_model}`, papers read with `{judge_model}`. "
        f"Run cost ${cost:.2f}.",
    ]
    if issue_number:
        lines += ["", f"From inbox #{issue_number}."]
    if added:
        lines += ["", "## Accepted", "",
                  "| Paper | Section | Why | Attributes |", "| --- | --- | --- | --- |"]
        for rec in added:
            attrs = attrs_by_id.get(rec["id"])
            summary = ", ".join(f"{k}={v}" for k, v in list((attrs or {}).items())[:3])
            if attrs and len(attrs) > 3:
                summary += ", …"
            lines.append(
                f"| [{rec['name'] or rec['title'][:40]}]({rec['links']['paper']}) "
                f"| `{rec['section']}` | {notes.get(rec['id'], '') or '—'} "
                f"| {summary or '_not read_'} |")
    if unsure:
        lines += ["", "## Left for you", "",
                  "The agent could not decide these from the title and abstract. They "
                  "stay in the inbox.", ""]
        lines += [f"- [{r['id']}](https://arxiv.org/abs/{r['id']}) — {r['title']}"
                  for r in unsure]
    if rejections:
        lines += ["", "## Rejected", "",
                  "Recorded in `data/agent-rejected.jsonl`. Delete a line there to put "
                  "the paper back in circulation.", ""]
        lines += [f"- `{r['id']}` {r['title'][:70]} — {r['reason']}" for r in rejections]
    lines += ["", "---", "",
              "Frame rates and horizons are the papers' own claims, transcribed by the "
              "agent. Spot-check anything that will end up in the comparison table."]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
